// VoltSchematix - programma voor Windows.
// Het venster toont exact dezelfde code als de webversie (dist/index.html).
// Dit bestand voegt enkel toe wat een browser niet kan: de gewone Windows-vensters om een
// bestand te kiezen, en het lezen en schrijven van precies die bestanden (zie guard.rs).

#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod guard;

use guard::{ext_ok, percent_decode, write_atomic, Allow, MAX_READ, PROJECT_EXT, WRITE_EXT};
use serde::Serialize;
use std::fs;
use std::path::{Path, PathBuf};
use std::sync::Mutex;
use std::time::UNIX_EPOCH;
use tauri::Manager;
#[cfg(not(feature = "e2e"))]
use tauri_plugin_dialog::DialogExt;

/// Het bestand waarmee het programma gestart werd (dubbelklik op een .vsx-bestand).
struct Launch(Mutex<Option<String>>);

#[derive(Serialize)]
struct Stat {
    size: u64,
    mtime: f64,
}

fn denied() -> String {
    "geen toegang tot dit bestand".into()
}

#[tauri::command]
fn vs_stat(path: String, allow: tauri::State<'_, Allow>) -> Result<Stat, String> {
    let p = PathBuf::from(&path);
    if !allow.file_ok(&p) {
        return Err(denied());
    }
    let m = fs::metadata(&p).map_err(|e| e.to_string())?;
    if !m.is_file() {
        return Err("geen bestand".into());
    }
    let mtime = m
        .modified()
        .ok()
        .and_then(|t| t.duration_since(UNIX_EPOCH).ok())
        .map(|d| d.as_millis() as f64)
        .unwrap_or(0.0);
    Ok(Stat { size: m.len(), mtime })
}

#[tauri::command]
fn vs_read_text(path: String, allow: tauri::State<'_, Allow>) -> Result<String, String> {
    let p = PathBuf::from(&path);
    if !ext_ok(&p, &PROJECT_EXT) || !allow.file_ok(&p) {
        return Err(denied());
    }
    let m = fs::metadata(&p).map_err(|e| e.to_string())?;
    if m.len() > MAX_READ {
        return Err("bestand te groot".into());
    }
    fs::read_to_string(&p).map_err(|e| e.to_string())
}

/// Projectbestanden (.vsx en .json) in een gekozen projectmap, zonder submappen.
#[tauri::command]
fn vs_list(dir: String, allow: tauri::State<'_, Allow>) -> Result<Vec<String>, String> {
    let d = PathBuf::from(&dir);
    if !allow.dir_ok(&d) {
        return Err(denied());
    }
    let mut out: Vec<String> = Vec::new();
    for entry in fs::read_dir(&d).map_err(|e| e.to_string())?.flatten() {
        let p = entry.path();
        let is_file = entry.file_type().map(|t| t.is_file()).unwrap_or(false);
        if is_file && ext_ok(&p, &PROJECT_EXT) {
            if let Some(n) = p.file_name().and_then(|n| n.to_str()) {
                out.push(n.to_string());
            }
        }
    }
    out.sort_by_key(|s| s.to_lowercase());
    Ok(out)
}

/// Schrijft de inhoud (rechtstreeks als bytes doorgegeven) naar een gekozen bestand.
#[tauri::command]
fn vs_write_bytes(request: tauri::ipc::Request, allow: tauri::State<'_, Allow>) -> Result<(), String> {
    let path = request
        .headers()
        .get("x-path")
        .and_then(|v| v.to_str().ok())
        .map(percent_decode)
        .ok_or("geen bestandsnaam")?;
    let p = PathBuf::from(&path);
    if !ext_ok(&p, &WRITE_EXT) || !allow.file_ok(&p) {
        return Err(denied());
    }
    let data: &[u8] = match request.body() {
        tauri::ipc::InvokeBody::Raw(d) => d,
        _ => return Err("geen gegevens".into()),
    };
    write_atomic(&p, data)
}

/// Welke bestandstypes een Windows-venster toont.
fn filter_for(kind: &str) -> (&'static str, &'static [&'static str]) {
    match kind {
        "pdf" => ("PDF", &["pdf"]),
        "xlsx" => ("Excel", &["xlsx"]),
        _ => ("VoltSchematix-project", &["vsx", "json"]),
    }
}

/// Testversie (enkel voor de automatische eindtest bij het bouwen): de Windows-vensters worden
/// overgeslagen en de paden komen uit een lijst. Zit niet in het programma dat gebruikers krijgen.
#[cfg(feature = "e2e")]
fn e2e_next() -> Option<PathBuf> {
    let q = std::env::var("VS_E2E_QUEUE").ok()?;
    let text = fs::read_to_string(&q).ok()?;
    let mut lines: Vec<&str> = text.lines().filter(|l| !l.trim().is_empty()).collect();
    if lines.is_empty() {
        return None;
    }
    let first = lines.remove(0).trim().to_string();
    let _ = fs::write(&q, lines.join("\n"));
    if first == "-" {
        None
    } else {
        Some(PathBuf::from(first))
    }
}

#[cfg(not(feature = "e2e"))]
fn parent_of(app: &tauri::AppHandle) -> Option<tauri::WebviewWindow> {
    app.get_webview_window("main")
}

/// Windows-venster "Opslaan als". Het gekozen bestand mag daarna geschreven worden.
#[tauri::command]
async fn vs_pick_save(
    app: tauri::AppHandle,
    allow: tauri::State<'_, Allow>,
    name: String,
    dir: Option<String>,
    kind: String,
) -> Result<Option<String>, String> {
    let (label, exts) = filter_for(&kind);
    #[cfg(feature = "e2e")]
    let picked = {
        let _ = (&app, &name, &dir, label);
        e2e_next()
    };
    #[cfg(not(feature = "e2e"))]
    let picked = {
        let mut b = app.dialog().file().add_filter(label, exts).set_file_name(name);
        if let Some(d) = dir.map(PathBuf::from) {
            if d.is_dir() {
                b = b.set_directory(d);
            }
        }
        if let Some(w) = parent_of(&app) {
            b = b.set_parent(&w);
        }
        b.blocking_save_file().and_then(|f| f.into_path().ok())
    };
    let Some(mut p) = picked else { return Ok(None) };
    if !ext_ok(&p, exts) {
        let base = p.file_name().map(|n| n.to_string_lossy().into_owned()).unwrap_or_default();
        p.set_file_name(format!("{base}.{}", exts[0]));
    }
    allow.add_file(&p);
    Ok(Some(p.to_string_lossy().into_owned()))
}

/// Windows-venster "Openen". Het gekozen bestand mag daarna gelezen en bewaard worden.
#[tauri::command]
async fn vs_pick_open(
    app: tauri::AppHandle,
    allow: tauri::State<'_, Allow>,
    dir: Option<String>,
) -> Result<Option<String>, String> {
    #[cfg(feature = "e2e")]
    let picked = {
        let _ = (&app, &dir);
        e2e_next()
    };
    #[cfg(not(feature = "e2e"))]
    let picked = {
        let (label, exts) = filter_for("project");
        let mut b = app.dialog().file().add_filter(label, exts);
        if let Some(d) = dir.map(PathBuf::from) {
            if d.is_dir() {
                b = b.set_directory(d);
            }
        }
        if let Some(w) = parent_of(&app) {
            b = b.set_parent(&w);
        }
        b.blocking_pick_file().and_then(|f| f.into_path().ok())
    };
    let Some(p) = picked else { return Ok(None) };
    if !ext_ok(&p, &PROJECT_EXT) {
        return Err("geen projectbestand".into());
    }
    allow.add_file(&p);
    Ok(Some(p.to_string_lossy().into_owned()))
}

/// Windows-venster "Map kiezen" voor de projectmap.
#[tauri::command]
async fn vs_pick_dir(app: tauri::AppHandle, allow: tauri::State<'_, Allow>) -> Result<Option<String>, String> {
    #[cfg(feature = "e2e")]
    let picked = {
        let _ = &app;
        e2e_next()
    };
    #[cfg(not(feature = "e2e"))]
    let picked = {
        let mut b = app.dialog().file();
        if let Some(w) = parent_of(&app) {
            b = b.set_parent(&w);
        }
        b.blocking_pick_folder().and_then(|f| f.into_path().ok())
    };
    let Some(p) = picked else { return Ok(None) };
    allow.add_dir(&p);
    Ok(Some(p.to_string_lossy().into_owned()))
}

#[tauri::command]
fn launch_file(launch: tauri::State<'_, Launch>) -> Option<String> {
    let l: &Launch = &launch;
    l.0.lock().ok().and_then(|mut v| v.take())
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_opener::init())
        // het venster mag nooit naar een andere pagina gaan dan het programma zelf
        .plugin(
            tauri::plugin::Builder::<tauri::Wry>::new("vs-guard")
                .on_navigation(|_webview, url| {
                    url.host_str() == Some("tauri.localhost")
                        || (url.scheme() == "tauri" && url.host_str() == Some("localhost"))
                })
                .build(),
        )
        .setup(|app| {
            let store = app.path().app_data_dir().ok().map(|d| d.join("toegang.json"));
            let allow = Allow::load(store);
            let launched = std::env::args_os()
                .skip(1)
                .map(PathBuf::from)
                .find(|p| ext_ok(p, &PROJECT_EXT) && p.is_file());
            if let Some(p) = &launched {
                allow.add_file(Path::new(p));
            }
            app.manage(allow);
            app.manage(Launch(Mutex::new(
                launched.map(|p| p.to_string_lossy().into_owned()),
            )));
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            vs_stat,
            vs_read_text,
            vs_list,
            vs_write_bytes,
            vs_pick_save,
            vs_pick_open,
            vs_pick_dir,
            launch_file
        ])
        .run(tauri::generate_context!())
        .expect("VoltSchematix kon niet starten");
}
