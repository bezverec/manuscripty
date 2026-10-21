# Manuscripty

Výzkumný systém pro lokální HTR středověkých rukopisů, obrazově kontrolované návrhy rekonstrukce v jazyce předlohy a českého překladu a jejich veřejné přezkoumání. Dokumentace aktualizována **21. října 2026**. Základní HTR korpus byl zveřejněn **19. října**; **21. října** přibyly samostatné návrhy čtení a anotace sousedních listů M I 259.

Rukopis **M II 220 z fondů Vědecké knihovny v Olomouci** je dostupný na [rukopisy.digitalizaty.cz](https://rukopisy.digitalizaty.cz). [Záznam celého dokumentu](https://rukopisy.digitalizaty.cz/rukopisy/vkol-m-ii-220) používá projektový identifikátor vkol-m-ii-220; nejde o knihovnou přidělené PID.

Společná knihovna nyní zahrnuje také [M II 153](https://rukopisy.digitalizaty.cz/rukopisy/vkol-m-ii-153)
ze stejné instituce: 197 snímků (192 folií a 5 snímků vazby), oba původní HTR
kandidáty na 15 013 segmentech, 3 531 pracovních interpretačních úseků s českým
překladem a zdrojové AI shrnutí.
Osm snímků nemá hlavní text ve vybraných oblastech. Celkem je zaregistrováno
874 snímků v prvních dvou dokumentech. Oba kodexy mají souhrnný katalogový název **Textus varii**;
samostatná díla a jejich atribuce mají vlastní zdroje v popisu.

Třetím dokumentem je [M I 259 · Textus varii](https://rukopisy.digitalizaty.cz/rukopisy/vkol-m-i-259):
371 snímků včetně vazby, předsádek a dvou dodatečných záběrů, latinské a německé texty,
původní kandidáti CATMuS a Medusa, pracovní rekonstrukce a český překlad. Knihovna tak
obsahuje **1 245 snímků ve třech rukopisech**. [Metodika M I 259](docs/mi259-processing.md)
vysvětluje meze segmentace, rozdíly mezi názvy skenů a psanou foliací i samostatné
ruční výřezy. Nové návrhy oprav odkazují na přesně identifikovaný orientovaný
souřadnicový obraz; původní archivní TIFF zůstává samostatně identifikován.

U M I 259 jsou nově oddělené dvě dodatečné obrazové četby s českým překladem
a označení **4 025 fragmentů sousedních listů a jednoho smíšeného výřezu na
197 snímcích**. Tato pracovní posouzení AI nemění původní HTR, segmentové ID
ani starší exporty. [Rozsah obrazové kontroly a omezení](docs/experiments/2026-10-21-mi259-neighbor-survey/README.md).

U **M II 220** je publikováno **677 skenů**: 670 foliovaných snímků (1r–335v) a 7 snímků vazby a předsádky. Na 664 textových stranách jsou kandidáti CATMuS a Medusa 4B a celkem **5 634 návrhů rekonstrukce a českého překladu**. UI zobrazuje **50 297 segmentů**, původní datové vrstvy mají 50 299 segmentů; dvě dvojice fragmentů na 20v jsou v UI spojené. Šest foliovaných stran nemá hlavní text ve vybraných oblastech. Vazba a předsádky jsou označené jako dosud nepřepsané.

Výsledky mají stav **proposed**, bez nezávislé odborné revize. CER/WER nebyly změřeny. Dokončení vybraného hlavního textu neznamená odborně ověřenou edici všech marginálií a zápisů.

## Orientace

- [Současná architektura](docs/architecture.md)
- [Historická publikace prvních dvou rukopisů a katalogové zdroje](docs/TWO-MANUSCRIPT-PUBLICATION.md)
- [M I 259: zpracování a publikace třetího rukopisu](docs/mi259-processing.md)
- [Použité HTR technologie, modely, odkazy a revize](docs/htr-technologies.md)
- [Aktuální stav a hranice výsledků](docs/research-status.md)
- [Údržba repozitáře a zachování historických dokladů](docs/maintenance.md)
- [Segmentační pilot Chandra / Kraken: přínos Chandry neprokázán](docs/experiments/2026-10-17-chandra/README.md)
- [Veřejná prezentace, úložiště a opravy](docs/presentation.md)
- [Web: spuštění, obnova obrazů a nasazení](web/README.md)
- [Dávková reprodukce](docs/reproduction.md) a [datové vrstvy](docs/data-contracts.md)
- [Kontrolní součty publikované textové části](docs/web-source-manifest.json)
- [Pravidla transkripce](medieval-manuscript-transcription/SKILL.md)

## Obsah repozitáře

| Adresář | Obsah |
|---|---|
| web/public | Aktuální statický frontend a veřejné JSON, TXT, TEI; bez obrazových souborů |
| web | Publikační a obrazové buildery, testy návrhů oprav, ověřování webu, konfigurace Pages |
| docs/htr-evidence | Záznamy použitých checkpointů a pilotních posouzení; bez vah |
| docs/validation | Zachované výsledky kontrol veřejné verze a nové kontroly tohoto snapshotu |
| htr-fourth-100-pages | Reprezentativní inference a ProArc export ze snapshotu 10. 10. |
| interpretation-fourth-100-pages | Reprezentativní obrazová příprava a exporty ze snapshotu 10. 10. |
| medieval-manuscript-transcription | Skill, referenční exporter, syntetická ukázka, testy, offline TEI P5 4.12.0 |
| presentation-storage-study | Původní měřicí skripty pro WebP a výřezy |

Starší dávkové zdroje zůstávají historickým referenčním snapshotem; původ a SHA-256 jsou v [source-manifest.json](docs/source-manifest.json). Veřejný textový korpus je v `web/public`. Obrazové deriváty M II 153 a M I 259 a folia M II 220 jsou v R2; sedm snímků vazby M II 220 používá Pages. Archivní TIFF, obrazové výřezy, modely, lokální cache, přístupové údaje a node_modules do Git nepatří. Git obsahuje pouze výslovně vybrané screenshoty UI a logo jako obrazové výjimky. Celá původní pracovní data a souhrnné balíčky OCR pro ProArc nejsou součástí webového snapshotu.

## Ověření

~~~sh
python -m pip install -r requirements-reference.txt
python web/validate_snapshot.py
python -m unittest discover -s medieval-manuscript-transcription/tests -v
cd web
npm test
~~~

Testy neprovádějí inference ani překlad. Web lze prohlížet přes místní HTTP server; podrobnosti a obnova sedmi obrazových snímků jsou ve web/README.md.

## Licence a původ

Původní LICENSE (GNU GPL v3) je zachován. TEI, ALTO a OpenSeadragon mají vlastní zachovaná licenční oznámení. HTR modely mají vlastní licence a stahují se samostatně. Repozitář neobsahuje obrazy rukopisu ani nepředstavuje publikaci odborně schválené edice.
