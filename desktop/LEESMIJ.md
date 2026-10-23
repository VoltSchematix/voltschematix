# VoltSchematix – programma voor Windows

Deze map bevat het programma voor Windows. Het gebruikt exact dezelfde code als de online versie
(`dist/index.html`) en verpakt die met [Tauri](https://tauri.app) tot een echt Windows-programma.

- `dist/index.html` – het programma zelf (gebouwd uit dezelfde bron als de website)
- `src-tauri/` – de verpakking: venster, Windows-vensters voor Opslaan/Openen, bestandstype `.vsx`, icoon
- `tests/` – de eindtest die bij elke bouw automatisch op Windows draait
- Bouwen gebeurt automatisch op GitHub: tabblad **Actions** → **Programma voor Windows** → **Run workflow**.
  Eerst worden alle tests uitgevoerd; pas als die slagen, wordt het installatieprogramma gebouwd en
  als concept bij **Releases** gezet, samen met `SHA256SUMS.txt` (controlecodes).

## Veiligheid

- Het programma maakt zelf geen internetverbinding en kan niet naar een andere pagina wegnavigeren.
- Het kan enkel bestanden lezen en schrijven die de gebruiker zelf in een Windows-venster gekozen heeft
  (of projectbestanden in de gekozen projectmap). Die controle gebeurt in het programma zelf (`src-tauri/src/guard.rs`),
  niet in de webpagina.
- Alle onderdelen staan vast op een exacte versie; de bouwstappen op GitHub staan vast op een exacte commit.
- Projecten (`.vsx`) zijn gewone JSON-bestanden en volledig uitwisselbaar met de online versie (`.json`).
