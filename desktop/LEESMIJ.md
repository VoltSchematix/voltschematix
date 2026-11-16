# VoltSchematix – programma voor Windows en Mac

Deze map bevat het programma voor Windows en voor Mac. Het gebruikt exact dezelfde code als de online versie
(`dist/index.html`) en verpakt die met [Tauri](https://tauri.app) tot een echt programma.

- `dist/index.html` – het programma zelf (gebouwd uit dezelfde bron als de website)
- `src-tauri/` – de verpakking: venster, de vensters voor Opslaan/Openen, bestandstype `.vsx`, icoon
  - `tauri.conf.json` – gemeenschappelijke instellingen en Windows (installatieprogramma)
  - `tauri.macos.conf.json` – extra instellingen voor de Mac (`.app` en `.dmg`, Mac-icoon, macOS 11 of nieuwer)
- `tests/` – de eindtest die bij elke bouw automatisch op Windows draait
- Bouwen gebeurt automatisch op GitHub, tabblad **Actions**:
  - **Programma voor Windows** → **Run workflow**
  - **Programma voor Mac** → **Run workflow** (één programma voor Macs met Apple-chip en met Intel)

  Eerst worden alle tests uitgevoerd; pas als die slagen, wordt het programma gebouwd en bij **Releases**
  gezet (dezelfde versie, dezelfde release), samen met controlecodes (`SHA256SUMS.txt`, `SHA256SUMS-mac.txt`)
  en een SBOM.

## Veiligheid

- Op Windows is het venster zo aangemaakt dat het doorzichtig kan zijn (`tauri.windows.conf.json`, `transparent`). Dat wordt enkel gebruikt door **Doorkijk** op het situatieplan: het tekenvlak wordt dan een gat waar je doorheen kijkt. Het programma kan niet lezen wat erachter staat. De enige extra venstertoelating is `core:window:allow-set-always-on-top` (venster bovenaan houden). Op de Mac is het venster gewoon en bestaat Doorkijk niet.
- Het programma maakt geen internetverbinding en kan niet naar een andere pagina wegnavigeren. Enige uitzondering, enkel na jouw toestemming: bij het opstarten (hoogstens één keer per dag) het nieuwste versienummer ophalen van één vast adres (`versie.txt` op de website). Het antwoord telt enkel als het precies een versienummer is.
- Het kan enkel bestanden lezen en schrijven die de gebruiker zelf in een venster van Windows of macOS gekozen heeft
  of waarmee het programma geopend werd (dubbelklik). Mappen die in een oudere versie als projectmap gekozen waren, blijven toegelaten.
  Die controle gebeurt in het programma zelf (`src-tauri/src/guard.rs`), niet in de webpagina, en is dezelfde op Windows en Mac.
- Op de Mac houdt de controle rekening met hoofdlettergevoelige schijven: een bestand met een anders geschreven naam is een ander bestand.
- Alle onderdelen staan vast op een exacte versie; de bouwstappen op GitHub staan vast op een exacte commit.
- Projecten (`.vsx`) zijn gewone JSON-bestanden en volledig uitwisselbaar tussen Windows, Mac en de online versie (`.json`).
- Het Mac-programma is ad hoc ondertekend, niet met een betaald Apple-ontwikkelaarsaccount. macOS vraagt daarom
  de eerste keer om toestemming (*Systeeminstellingen* → *Privacy en beveiliging* → *Toch openen*).
