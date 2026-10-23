//! Wat het programma mag lezen en schrijven.
//!
//! Het venster kan enkel bestanden lezen of schrijven die de gebruiker zelf gekozen heeft
//! in een Windows-venster (Opslaan, Openen, Projectmap kiezen) of waarmee het programma
//! gestart werd (dubbelklik). Die lijst wordt onthouden, zodat Mijn projecten na het herstarten
//! blijft werken. Al de rest van de computer blijft onbereikbaar, ook als er ooit kwaadaardige
//! code in het venster zou geraken.

use serde::{Deserialize, Serialize};
use std::collections::HashSet;
use std::fs;
use std::path::{Component, Path, PathBuf};
use std::sync::Mutex;

/// Projectbestanden.
pub const PROJECT_EXT: [&str; 2] = ["vsx", "json"];
/// Wat geschreven mag worden.
pub const WRITE_EXT: [&str; 4] = ["vsx", "json", "pdf", "xlsx"];
/// Een projectbestand is nooit groter dan dit.
pub const MAX_READ: u64 = 100 * 1024 * 1024;
/// Hoeveel gekozen bestanden onthouden worden.
const MAX_FILES: usize = 2000;

pub fn ext_ok(p: &Path, allowed: &[&str]) -> bool {
    p.extension()
        .and_then(|e| e.to_str())
        .map(|e| allowed.iter().any(|a| a.eq_ignore_ascii_case(e)))
        .unwrap_or(false)
}

/// Vaste schrijfwijze van een pad (Windows maakt geen onderscheid tussen hoofd- en kleine letters).
/// Enkel volledige paden zonder ".." worden aanvaard.
pub fn key(p: &Path) -> Option<String> {
    if !p.is_absolute() {
        return None;
    }
    if p.components().any(|c| matches!(c, Component::ParentDir | Component::CurDir)) {
        return None;
    }
    let s = p.to_string_lossy().replace('/', "\\");
    let s = s.trim_end_matches('\\');
    if s.is_empty() {
        return None;
    }
    Some(s.to_lowercase())
}

#[derive(Default, Serialize, Deserialize)]
struct Saved {
    files: Vec<String>,
    dirs: Vec<String>,
}

pub struct Allow {
    store: Option<PathBuf>,
    files: Mutex<Vec<String>>,
    dirs: Mutex<HashSet<String>>,
}

impl Allow {
    pub fn load(store: Option<PathBuf>) -> Self {
        let saved: Saved = store
            .as_ref()
            .and_then(|p| fs::read_to_string(p).ok())
            .and_then(|t| serde_json::from_str(&t).ok())
            .unwrap_or_default();
        Allow {
            store,
            files: Mutex::new(saved.files),
            dirs: Mutex::new(saved.dirs.into_iter().collect()),
        }
    }

    fn save(&self) {
        let Some(store) = &self.store else { return };
        let saved = Saved {
            files: self.files.lock().map(|f| f.clone()).unwrap_or_default(),
            dirs: self
                .dirs
                .lock()
                .map(|d| d.iter().cloned().collect())
                .unwrap_or_default(),
        };
        if let Some(dir) = store.parent() {
            let _ = fs::create_dir_all(dir);
        }
        if let Ok(t) = serde_json::to_string(&saved) {
            let _ = fs::write(store, t);
        }
    }

    pub fn add_file(&self, p: &Path) {
        let Some(k) = key(p) else { return };
        if let Ok(mut f) = self.files.lock() {
            f.retain(|x| x != &k);
            f.push(k);
            let n = f.len();
            if n > MAX_FILES {
                f.drain(0..n - MAX_FILES);
            }
        }
        self.save();
    }

    pub fn add_dir(&self, p: &Path) {
        let Some(k) = key(p) else { return };
        if let Ok(mut d) = self.dirs.lock() {
            d.insert(k);
        }
        self.save();
    }

    pub fn dir_ok(&self, p: &Path) -> bool {
        key(p)
            .map(|k| self.dirs.lock().map(|d| d.contains(&k)).unwrap_or(false))
            .unwrap_or(false)
    }

    /// Een bestand mag als de gebruiker het zelf gekozen heeft, of als het rechtstreeks
    /// in een gekozen projectmap staat (geen submappen).
    pub fn file_ok(&self, p: &Path) -> bool {
        let Some(k) = key(p) else { return false };
        if self.files.lock().map(|f| f.contains(&k)).unwrap_or(false) {
            return true;
        }
        match p.parent() {
            Some(parent) => ext_ok(p, &PROJECT_EXT) && self.dir_ok(parent),
            None => false,
        }
    }
}

pub fn percent_decode(s: &str) -> String {
    let b = s.as_bytes();
    let hexval = |c: u8| -> Option<u8> {
        match c {
            b'0'..=b'9' => Some(c - b'0'),
            b'a'..=b'f' => Some(c - b'a' + 10),
            b'A'..=b'F' => Some(c - b'A' + 10),
            _ => None,
        }
    };
    let mut out: Vec<u8> = Vec::with_capacity(b.len());
    let mut i = 0;
    while i < b.len() {
        if b[i] == b'%' && i + 2 < b.len() {
            if let (Some(h), Some(l)) = (hexval(b[i + 1]), hexval(b[i + 2])) {
                out.push(h * 16 + l);
                i += 3;
                continue;
            }
        }
        out.push(b[i]);
        i += 1;
    }
    String::from_utf8_lossy(&out).into_owned()
}

/// Eerst naar een tijdelijk bestand ernaast schrijven, daarna vervangen:
/// zo raakt een bestand nooit half bewaard.
pub fn write_atomic(p: &Path, data: &[u8]) -> Result<(), String> {
    let ext = p.extension().and_then(|e| e.to_str()).unwrap_or("bestand");
    let tmp = p.with_extension(format!("{ext}.tmp"));
    fs::write(&tmp, data).map_err(|e| e.to_string())?;
    if let Err(e) = fs::rename(&tmp, p) {
        let _ = fs::remove_file(&tmp);
        fs::write(p, data).map_err(|_| e.to_string())?;
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn tmpdir(name: &str) -> PathBuf {
        let d = std::env::temp_dir().join(format!("vs-test-{name}-{}", std::process::id()));
        let _ = fs::remove_dir_all(&d);
        fs::create_dir_all(&d).unwrap();
        d
    }

    #[test]
    fn decode() {
        assert_eq!(percent_decode("C%3A%5CUsers%5CJan%20%C3%A9.vsx"), "C:\\Users\\Jan é.vsx");
        assert_eq!(percent_decode("a%2"), "a%2");
        assert_eq!(percent_decode("a%zz"), "a%zz");
    }

    #[test]
    fn extensions() {
        assert!(ext_ok(Path::new("a.VSX"), &PROJECT_EXT));
        assert!(ext_ok(Path::new("a.json"), &PROJECT_EXT));
        assert!(!ext_ok(Path::new("a.exe"), &WRITE_EXT));
        assert!(!ext_ok(Path::new("a"), &WRITE_EXT));
        assert!(!ext_ok(Path::new("a.json.exe"), &WRITE_EXT));
    }

    #[test]
    fn only_chosen_files() {
        let d = tmpdir("allow");
        let store = d.join("toegang.json");
        let a = Allow::load(Some(store.clone()));
        let f = d.join("Woning.vsx");
        assert!(!a.file_ok(&f));
        a.add_file(&f);
        assert!(a.file_ok(&f));
        // hoofdletters maken niet uit
        assert!(a.file_ok(&PathBuf::from(f.to_string_lossy().to_uppercase())));
        // een ander bestand in dezelfde map: niet, tot de map gekozen is
        let g = d.join("Ander.json");
        assert!(!a.file_ok(&g));
        a.add_dir(&d);
        assert!(a.file_ok(&g));
        // in de projectmap enkel projectbestanden, geen submappen
        assert!(!a.file_ok(&d.join("geheim.txt")));
        assert!(!a.file_ok(&d.join("sub").join("x.vsx")));
        // ".." en relatieve paden nooit
        assert!(!a.file_ok(&d.join("..").join("x.vsx")));
        assert!(!a.file_ok(Path::new("x.vsx")));
        // onthouden na herstarten
        let b = Allow::load(Some(store));
        assert!(b.file_ok(&f) && b.file_ok(&g) && b.dir_ok(&d));
        let _ = fs::remove_dir_all(&d);
    }

    #[test]
    fn atomic_write() {
        let d = tmpdir("write");
        let f = d.join("p.vsx");
        write_atomic(&f, b"een").unwrap();
        write_atomic(&f, b"twee").unwrap();
        assert_eq!(fs::read(&f).unwrap(), b"twee");
        assert!(!d.join("p.vsx.tmp").exists());
        let _ = fs::remove_dir_all(&d);
    }
}
