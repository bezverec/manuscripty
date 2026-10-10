# Manuscripty

Výzkumný systém pro porovnání lokálního HTR středověkých rukopisů s obrazově kontrolovanými návrhy latinské rekonstrukce a českého překladu. Tento repozitář zachycuje používanou architekturu pilotu rukopisu VKO M II 220 k 10. 10. 2026.

Pilot zahrnuje **430 skenů a 31 528 segmentů**. Na 427 stranách s textem existují návrhy rekonstrukce a překladu; další tři záznamy zachycují absenci hlavního textu ve zvolených oblastech. Interpretace jsou označeny **proposed**, bez odborné revize. Bez referenčního přepisu nejsou stanoveny CER ani WER.

## Orientace

- [Architektura a tok dat](docs/architecture.md)
- [Prostředí, spuštění a omezení reprodukce](docs/reproduction.md)
- [Datové vrstvy a validační pravidla](docs/data-contracts.md)
- [Stav pilotu a měření spotřeby](docs/research-status.md)
- [Návrh webové prezentace](docs/presentation.md)
- [Původ a kontrolní součty zdrojů](docs/source-manifest.json)
- [Pravidla přepisu a práce s nejistotou](medieval-manuscript-transcription/SKILL.md)

## Součásti

| Adresář | Úloha |
|---|---|
| htr-fourth-100-pages/scripts | Příprava TIFF, segmentace Kraken, CATMuS, Medusa, checkpointy, porovnání a audit |
| htr-fourth-100-pages/selection.json | Skutečný výběr a geometrie poslední dávky 100 skenů |
| htr-fourth-100-pages/ocr-proarc | Export TXT a ALTO 3.0, XSD kontrola a ZIP pro import do ProArcu |
| interpretation-fourth-100-pages/scripts | Příprava obrazů pro čtení, export návrhů, TEI, kontrola a souhrn pilotu |
| medieval-manuscript-transcription | Skill, syntetická ukázka, referenční exporter, testy a offline TEI 4.12.0 |
| presentation-storage-study/scripts | Měření velikosti WebP dlaždic a výřezů |

Zdrojové soubory uvedené v manifestu jsou převzaty beze změny. Dávkové skripty jsou konkrétní implementace poslední stovky a mají pevné názvy složek, počty stran a vazby na předchozí etapy. Repozitář obsahuje zdroje a schémata; výzkumná data, TIFF, PNG, modelové váhy, checkpointy a celé výsledné přepisy se spravují v odděleném pracovním úložišti. Git clone sám nenahradí původní datové prostředí.

## Rychlé ověření referenčního exporteru

Python s lxml; přesné použité verze základních knihoven jsou v requirements-reference.txt.

~~~sh
python -m unittest discover -s medieval-manuscript-transcription/tests -v
python medieval-manuscript-transcription/scripts/export.py --input medieval-manuscript-transcription/assets/demo.json --out-dir demo-output --validate-tei
~~~

Ukázka je syntetická. Tyto příkazy neprovádějí HTR ani nevytvářejí překlad. Detailní provozní postup je v návodu k reprodukci.

## Licence a původ

Původní soubor LICENSE připraveného repozitáře (GNU GPL v3) je zachován. Přibalená schémata TEI a ALTO mají vlastní zachovaná oznámení a původ. Modely se stahují samostatně podle svých licencí. Archivní obrazy ani ediční výstupy se tímto repozitářem nezpřístupňují.
