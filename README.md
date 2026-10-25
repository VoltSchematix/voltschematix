# VoltSchematix

**NL** · [FR](#français) · [EN](#english)

**Versie 1.0.4** · Version 1.0.4

VoltSchematix is een gratis programma om de plannen van een elektrische installatie te maken: het **eendraadschema**, het **situatieplan**, de **lijst met kringen** en de **materiaallijst**. Alles samen maak je in één PDF, klaar om af te drukken of te bezorgen.

Het programma is één enkel bestand (`index.html`) dat in je browser werkt. Je hoeft niets te installeren en geen account aan te maken.

## Gebruiken

**Online:** open **https://voltschematix.github.io/voltschematix/**

**Offline:** open de link, open het menu van de browser (⋮ of …) en kies **Pagina opslaan als** (Chrome: onder *Opslaan en delen*; Edge: onder *Meer hulpprogramma's*). Kies **"Webpagina, alleen HTML"** en dubbelklik later op dat bestand. Je kunt ook hierboven `index.html` openen en op het downloadpijltje klikken. Alles werkt dan zonder internet, ook PDF maken, Excel en een PDF als achtergrond.

Werkt het best in **Chrome** of **Edge** op een computer. Firefox en Safari werken ook; daar komt een opgeslagen project in *Downloads*.

Op **gsm en tablet** (iPhone, iPad, Android) werkt het ook, met aanraken: tikken, knijpen om te zoomen, slepen om te schuiven. Opslaan gaat daar als download (iPhone/iPad: *Bewaar in Bestanden*, Android: *Downloads*). Tekenen gaat het vlotst op een tablet of computer.

## Programma voor Windows

Liever een echt programma? **[Downloaden voor Windows](https://github.com/VoltSchematix/voltschematix/releases/latest)** → klik bij *Assets* op *VoltSchematix_…_x64-setup.exe*, open het en installeer. Je krijgt een icoon in het startmenu, een eigen venster, en projecten (`.vsx`) openen met een dubbelklik. Windows kan bij de installatie waarschuwen dat de uitgever onbekend is: klik op *Meer informatie* → *Toch uitvoeren*. Projecten zijn uitwisselbaar met de online versie.

## Hoe begin je?

1. **Document:** vul de gegevens van de klant en van je firma in.
2. **Eendraadschema:** klik links op een zekering voor een nieuwe kring, en voeg stopcontacten, schakelaars en lampen toe.
3. **Situatieplan:** teken het grondplan, of leg een foto of PDF van het plan eronder, en plaats de symbolen.
4. **Materiaallijst:** kijk de lijst na en vul de kabellengtes in.
5. **Afdrukken:** maak één PDF of druk rechtstreeks af.

Druk tussendoor op **Ctrl+S** om je project als bestand op te slaan. Je projecten vind je terug op het tabblad **Mijn projecten**.

Een volledige handleiding, met woordenlijst en sneltoetsen, staat in het programma zelf (tabblad **Handleiding**, of de knop **?** rechtsboven).

## Je gegevens en veiligheid

- Alles wat je invult, blijft **op je eigen computer**, in je browser. Er wordt niets doorgestuurd.
- Het programma maakt **geen enkele internetverbinding**. Alle onderdelen zitten in het bestand zelf.
- Een strikte beveiligingsregel laat alleen de eigen code van het programma draaien. Projectbestanden worden bij het openen gecontroleerd en opgeschoond.
- Welke onderdelen van derden erin zitten (met versie en controlecode), staat in [THIRD-PARTY-LICENSES.txt](THIRD-PARTY-LICENSES.txt) en in de SBOM [sbom-web.cdx.json](sbom-web.cdx.json) (CycloneDX). Bij het Windows-programma staat ook een SBOM bij elke release.
- Haal het programma **alleen via de officiële link** hierboven. Een projectbestand (`.json`) kun je gerust openen; een HTML-bestand van iemand anders open je beter niet.
- Je project bewaar je als **bestand op je computer** (.json), in een map naar keuze: *Opslaan* (Ctrl+S) of *Opslaan als*. In Chrome en Edge verschijnt het gewone Windows-venster en bewaart *Opslaan* daarna telkens in hetzelfde bestand; in andere browsers komt het bestand in *Downloads*.
- Op het tabblad **Mijn projecten** vind je al je projectbestanden terug, met naam, klant en adres. Kies er een **projectmap** en alle projecten in die map verschijnen vanzelf.
- Het programma maakt daarnaast automatisch **reservekopieën** in je browser, als vangnet. Dat is geen veilige opslag: je project is pas echt veilig in het bestand.

## Oudere projecten

Projectbestanden van **elke vorige versie** openen in de nieuwste versie. Ze worden indien nodig automatisch omgezet, met eerst een reservekopie. Een bestand van een nieuwere versie geeft een waarschuwing.

Vorige versies van het programma vind je bij **Releases**.

## Talen

Nederlands, Français, English (keuze rechtsboven in het programma).

## Belangrijk

VoltSchematix is een hulpmiddel om plannen te tekenen. Het controleert niet of een installatie aan de geldende voorschriften voldoet. De gebruiker blijft zelf verantwoordelijk voor de juistheid van de plannen.

Gratis te gebruiken onder de [MIT-licentie](LICENSE), zonder enige garantie. Ingebouwde onderdelen van derden (jsPDF, PDF.js, SheetJS): zie [THIRD-PARTY-LICENSES.txt](THIRD-PARTY-LICENSES.txt).

---

## Français

VoltSchematix est un programme gratuit pour réaliser les plans d'une installation électrique : **schéma unifilaire**, **plan de situation**, **liste des circuits** et **liste de matériel**, réunis dans un seul PDF.

- **En ligne :** https://voltschematix.github.io/voltschematix/
- **Hors ligne :** ouvrez le lien, puis le menu du navigateur (⋮ ou …) → **Enregistrer la page sous** → **« Page Web, HTML uniquement »**. Ou ouvrez `index.html` ci-dessus et cliquez sur la flèche de téléchargement. Tout fonctionne ensuite sans internet, y compris le PDF, Excel et un PDF comme fond.
- Existe aussi comme programme pour Windows : **[Télécharger pour Windows](https://github.com/VoltSchematix/voltschematix/releases/latest)** (fichier *…setup.exe* sous *Assets*) ; les projets (`.vsx`, `.json`) fonctionnent dans les deux.
- Fonctionne au mieux dans Chrome ou Edge sur ordinateur. Fonctionne aussi sur smartphone et tablette (iPhone, iPad, Android), au toucher ; l'enregistrement s'y fait par téléchargement (iPhone/iPad : *Enregistrer dans Fichiers*).
- Vos données restent sur votre ordinateur ; le programme ne fait aucune connexion internet. Enregistrez votre projet comme fichier (.json) dans le dossier de votre choix (Chrome/Edge) ou dans Téléchargements. Téléchargez le programme uniquement via le lien officiel.
- L'onglet **Mes projets** affiche tous vos fichiers de projet (nom, client, adresse). Le programme fait aussi des copies de sauvegarde automatiques dans le navigateur, comme filet de sécurité temporaire.
- Composants tiers et versions : THIRD-PARTY-LICENSES.txt et la SBOM [sbom-web.cdx.json](sbom-web.cdx.json) (CycloneDX).
- Les fichiers de projet (`.json`) de toutes les versions précédentes s'ouvrent dans la dernière version.
- Le manuel complet se trouve dans le programme (onglet **Manuel** ou bouton **?**).

VoltSchematix est un outil de dessin. Il ne vérifie pas la conformité d'une installation aux prescriptions en vigueur ; l'utilisateur reste responsable de l'exactitude des plans. Licence MIT, sans garantie. Composants tiers : voir THIRD-PARTY-LICENSES.txt.

## English

VoltSchematix is a free program to draw the plans of an electrical installation: **single-line diagram**, **site plan**, **list of circuits** and **material list**, combined in one PDF.

- **Online:** https://voltschematix.github.io/voltschematix/
- **Offline:** open the link, then the browser menu (⋮ or …) → **Save page as** → **"Webpage, HTML Only"**. Or open `index.html` above and click the download arrow. Everything then works without internet, including PDF, Excel and a PDF as background.
- Also available as a program for Windows: **[Download for Windows](https://github.com/VoltSchematix/voltschematix/releases/latest)** (the *…setup.exe* file under *Assets*); projects (`.vsx`, `.json`) work in both.
- Works best in Chrome or Edge on a computer. Also works on phones and tablets (iPhone, iPad, Android) with touch; saving there is a download (iPhone/iPad: *Save to Files*).
- Your data stays on your computer; the program makes no internet connection at all. Save your project as a file (.json) in a folder of your choice (Chrome/Edge) or in Downloads. Only download the program from the official link.
- The **My projects** tab shows all your project files (name, client, address). The program also makes automatic backups in the browser, as a temporary safety net.
- Third-party components and versions: THIRD-PARTY-LICENSES.txt and the SBOM [sbom-web.cdx.json](sbom-web.cdx.json) (CycloneDX).
- Project files (`.json`) from every previous version open in the latest version.
- The full manual is inside the program (**Manual** tab or the **?** button).

VoltSchematix is a drawing tool. It does not check whether an installation complies with the applicable regulations; the user remains responsible for the correctness of the plans. MIT licence, no warranty. Third-party components: see THIRD-PARTY-LICENSES.txt.
