//! Wat het programma mag lezen en schrijven.
//!
//! Het venster kan enkel bestanden lezen of schrijven die de gebruiker zelf gekozen heeft
//! in een venster van Windows of macOS (Opslaan, Openen, Projectmap kiezen) of waarmee het programma
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

/// Vaste schrijfwijze van een pad. Enkel volledige paden zonder ".." worden aanvaard.
/// Windows maakt geen onderscheid tussen hoofd- en kleine letters; op een Mac blijft het pad
/// letterlijk (een Mac-schijf kan hoofdlettergevoelig zijn: "Plan.vsx" en "plan.vsx" zijn dan twee bestanden).
pub fn key(p: &Path) -> Option<String> {
    if !p.is_absolute() {
        return None;
    }
    if p.components().any(|c| matches!(c, Component::ParentDir | Component::CurDir)) {
        return None;
    }
    #[cfg(windows)]
    {
        let s = p.to_string_lossy().replace('/', "\\");
        let s = s.trim_end_matches('\\');
        if s.is_empty() {
            return None;
        }
        Some(s.to_lowercase())
    }
    #[cfg(not(windows))]
    {
        let s = p.to_string_lossy();
        let s = s.trim_end_matches('/');
        if s.is_empty() {
            return None;
        }
        Some(s.to_string())
    }
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
        // in een projectmap nooit via een snelkoppeling (symlink) naar een bestand elders
        if is_link(p) {
            return false;
        }
        match p.parent() {
            Some(parent) => ext_ok(p, &PROJECT_EXT) && self.dir_ok(parent),
            None => false,
        }
    }
}

/// Is dit pad een snelkoppeling (symbolische link of junction)?
pub fn is_link(p: &Path) -> bool {
    fs::symlink_metadata(p)
        .map(|m| m.file_type().is_symlink())
        .unwrap_or(false)
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
    // een achtergebleven tijdelijk bestand (of een snelkoppeling met die naam) eerst weg, zodat er nooit via een link elders geschreven wordt
    if tmp.exists() || is_link(&tmp) {
        let _ = fs::remove_file(&tmp);
    }
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
        // Windows: hoofdletters maken niet uit; Mac: een ander geschreven naam is een ander bestand
        #[cfg(windows)]
        assert!(a.file_ok(&PathBuf::from(f.to_string_lossy().to_uppercase())));
        #[cfg(not(windows))]
        assert!(!a.file_ok(&d.join("WONING.vsx")));
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

    #[cfg(unix)]
    #[test]
    fn no_links() {
        let d = tmpdir("links");
        let a = Allow::load(None);
        a.add_dir(&d);
        let target = std::env::temp_dir().join(format!("vs-geheim-{}.json", std::process::id()));
        fs::write(&target, b"geheim").unwrap();
        let link = d.join("link.json");
        std::os::unix::fs::symlink(&target, &link).unwrap();
        assert!(!a.file_ok(&link));
        // tijdelijk bestand als link: schrijven gaat niet naar het doel van de link
        let f = d.join("p.json");
        std::os::unix::fs::symlink(&target, d.join("p.json.tmp")).unwrap();
        write_atomic(&f, b"nieuw").unwrap();
        assert_eq!(fs::read(&target).unwrap(), b"geheim");
        assert_eq!(fs::read(&f).unwrap(), b"nieuw");
        let _ = fs::remove_file(&target);
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
