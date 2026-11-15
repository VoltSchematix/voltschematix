# Veiligheid · Sécurité · Security

## Nederlands

**Een veiligheidsprobleem melden.** Ga naar het tabblad **Security** van dit project en klik op **Report a vulnerability**. De melding is privé: alleen de beheerder van VoltSchematix kan ze lezen. Zet een veiligheidsprobleem niet in een openbare discussie.

Vermeld als het kan: de versie (staat naast de naam, bv. v1.0.8), of het gaat om de website, het HTML-bestand, Windows of Mac, en de stappen om het probleem te tonen. Een voorbeeldbestand helpt, maar gebruik geen echte klantgegevens.

**Welke versie krijgt herstellingen?** Alleen de nieuwste versie. Een herstelling komt altijd uit als een nieuwe versie met een hoger nummer; bestanden van een uitgebrachte versie worden nooit vervangen.

**Hoe VoltSchematix gebouwd is.**
- Het programma werkt volledig op je eigen toestel. Je projecten worden nergens naartoe gestuurd. Het programma maakt geen verbinding met internet, behalve als je het toelaat om bij het opstarten online te controleren of er een update beschikbaar is: dan wordt enkel een versienummer opgehaald van één vast adres op de website van VoltSchematix.
- De programma's voor Windows en Mac worden door GitHub gebouwd uit de openbare broncode, met vastgelegde versies van alle onderdelen (`Cargo.lock`, `package-lock.json`).
- Bij elke release staan controlecodes (`SHA256SUMS.txt`, `SHA256SUMS-mac.txt`), een lijst van alle onderdelen (SBOM) en, vanaf versie 1.0.9, een bouwbewijs. Het bouwbewijs nakijken kan met de GitHub CLI:
  `gh attestation verify VoltSchematix_x.y.z_x64-setup.exe --repo VoltSchematix/voltschematix`
- De programma's zijn niet ondertekend met een betaald certificaat. Windows en macOS tonen daarom een waarschuwing bij de eerste installatie. Download alleen via deze pagina of via https://voltschematix.github.io/voltschematix/.

## Français

**Signaler un problème de sécurité.** Ouvrez l'onglet **Security** de ce projet et cliquez sur **Report a vulnerability**. Le signalement est privé : seul le gestionnaire de VoltSchematix peut le lire. Ne publiez pas un problème de sécurité dans une discussion publique.

Indiquez si possible : la version (à côté du nom, p. ex. v1.0.8), s'il s'agit du site web, du fichier HTML, de Windows ou de Mac, et les étapes pour reproduire le problème. Un fichier d'exemple aide, mais n'utilisez pas de données réelles de clients.

**Quelle version reçoit des corrections ?** Uniquement la dernière version. Une correction sort toujours comme une nouvelle version avec un numéro plus élevé ; les fichiers d'une version publiée ne sont jamais remplacés.

**Comment VoltSchematix est construit.**
- Le programme fonctionne entièrement sur votre appareil. Vos projets ne sont envoyés nulle part. Le programme n'établit aucune connexion à internet, sauf si vous l'autorisez à vérifier en ligne, au démarrage, si une mise à jour est disponible : seul un numéro de version est alors récupéré à une adresse fixe du site web de VoltSchematix.
- Les programmes pour Windows et Mac sont construits par GitHub à partir du code source public, avec des versions figées de tous les composants (`Cargo.lock`, `package-lock.json`).
- Chaque version publiée contient des sommes de contrôle (`SHA256SUMS.txt`, `SHA256SUMS-mac.txt`), la liste de tous les composants (SBOM) et, à partir de la version 1.0.9, une attestation de construction. Pour vérifier l'attestation avec la GitHub CLI :
  `gh attestation verify VoltSchematix_x.y.z_x64-setup.exe --repo VoltSchematix/voltschematix`
- Les programmes ne sont pas signés avec un certificat payant. Windows et macOS affichent donc un avertissement lors de la première installation. Téléchargez uniquement via cette page ou via https://voltschematix.github.io/voltschematix/.

## English

**Reporting a security issue.** Open the **Security** tab of this project and click **Report a vulnerability**. The report is private: only the VoltSchematix maintainer can read it. Please do not post a security issue in a public discussion.

If possible, include: the version (next to the name, e.g. v1.0.8), whether it concerns the website, the HTML file, Windows or Mac, and the steps to reproduce. A sample file helps, but do not use real customer data.

**Which version gets fixes?** Only the latest version. A fix is always released as a new version with a higher number; the files of a published version are never replaced.

**How VoltSchematix is built.**
- The program runs entirely on your own device. Your projects are not sent anywhere. The program makes no connection to the internet, unless you allow it to check online at start-up whether an update is available: in that case only a version number is fetched from one fixed address on the VoltSchematix website.
- The Windows and Mac programs are built by GitHub from the public source code, with pinned versions of all components (`Cargo.lock`, `package-lock.json`).
- Every release includes checksums (`SHA256SUMS.txt`, `SHA256SUMS-mac.txt`), a list of all components (SBOM) and, from version 1.0.9 on, a build attestation. To verify the attestation with the GitHub CLI:
  `gh attestation verify VoltSchematix_x.y.z_x64-setup.exe --repo VoltSchematix/voltschematix`
- The programs are not signed with a paid certificate. Windows and macOS therefore show a warning on first installation. Only download from this page or from https://voltschematix.github.io/voltschematix/.
