# Publikovaná prezentace

Dokumentace k 21. 10. 2026. Základní korpus byl publikován 19. 10., dodatečné
četby a anotace M I 259 nasazeny 21. 10. Web
[rukopisy.digitalizaty.cz](https://rukopisy.digitalizaty.cz) běží v Cloudflare
Pages projektu `rukopisy-digitalizaty`. Obsahuje M II 220, M II 153 a M I 259
z fondů Vědecké knihovny v Olomouci; celkem 1 245 snímků.
[Počty, stav a omezení](research-status.md).

HTML/CSS/JavaScript a veřejné JSON/TEI/TXT/ALTO jsou v Pages. OpenSeadragon
6.1.1 načítá WebP pyramidy DZI (512 px, překryv 1 px, Q90). Náhledy a skutečné
řádkové výřezy jsou samostatné deriváty. Archivní TIFF zůstávají místní.

| Obrazová sada | Umístění / prefix | Objekty | Bajty |
|---|---|---:|---:|
| M II 220, folia a výřezy | R2 `v1/` | 158 837 | 10 213 360 984 |
| M II 220, sedm snímků vazby | Pages `binding-media/` | 1 175 | 45 188 048 |
| M II 153, včetně vazby | R2 `v2/vkol-m-ii-153/` | 62 131 | 3 290 011 866 |
| M I 259, včetně vazby a doplňkových výřezů | R2 `v2/vkol-m-i-259/` | 66 119 | 3 898 255 624 |

Jde o vytvořené a dříve auditované deriváty, nikoli aktuální fakturační výkaz
či novou inventuru cloudového účtu. Sdílený bucket `rukopisy-mii220` má
[obrazovou doménu](https://rukopisy-data.digitalizaty.cz); jeho historický název
neomezuje obsah na první rukopis. Nové soubory mají vlastní namespace.

Frontend nabízí dokumenty, HTR, řádkové čtení, rekonstrukci a překlad,
pracovní strukturu, katalogový popis a odlišený výklad AI. Má noční režim,
šířku/skrytí panelů a jedno označení VISK 6 v přehledu. Statická folia jsou
čitelná bez JS, hledání Pagefind potřebuje JS/WASM. Staré adresy shrnutí
přesměrovávají na přehled dokumentu; doložené veřejné URL se při úklidu nemažou.

Statická folia zobrazují výchozí HTR model; dynamický prohlížeč a downloady
nabízejí oba původní kandidáty. Doplňkové četby s češtinou se odlišují od starší
interpretace a poznámky k sousedním listům od rukopisného textu. Poslední
nasazení těchto anotací má [samostatný záznam](validation/mi259-neighbor-survey-publication-20261021.json):
SHA všech 197 změněných veřejných JSON odpovídaly přijaté místní verzi.
To není nová inventura všech obrazů v R2.

Návrhy oprav zachovávají původní kandidáty a geometrii. UI stáhne JSON nebo
předvyplní GitHub issue; redakční přijetí a regenerace korpusu jsou samostatné.
Schéma v2 M I 259 identifikuje orientovaný souřadnicový obraz a transformaci
na TIFF. [Datové kontrakty](data-contracts.md).

Git neobsahuje obrazy rukopisů ani Pagefind index. Před Pages deploy je nutné
obnovit všech 1 175 ignorovaných vazebních WebP M II 220; jinak by další
nasazení tyto obrazy ztratilo. [Obnova, testy a nasazení](../web/README.md).
Publikace probíhá ručně přes Wrangler. Push do GitHubu sám nemění Pages,
DNS ani R2. Tokeny a lokální účtové cache se necommitují.

IIIF zůstává vypnutým návrhem manifestu M II 220 bez publikovaných obrazových
služeb. Před zapnutím vyžaduje vlastní přípravu, práva, upload a ověření.
Historické testy a výsledky jsou datované v `docs/validation`; nejsou
nepřetržitým monitoringem dnešního nasazení.
