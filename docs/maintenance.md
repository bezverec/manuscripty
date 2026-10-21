# Údržba repozitáře

Rozlišení aktivního webu a historických výzkumných dokladů k 21. 10. 2026.
Aktuální počet dokumentů a výsledků je v [research-status.md](research-status.md).

| Oblast | Význam a postup |
|---|---|
| `web/public`, `web/manuscripts.json` | Současný korpus a frontend; ověřují se manifestem, odkazy a testy všech tří dokumentů. |
| `web/publication` | Aktivní publikační adaptéry; M II 153 a M I 259 mají vlastní kontrakty. |
| `docs/web-source-manifest.json` | Inventář veřejných textových souborů; chráněné hashe se nepřepočítávají bez řízené opravy. |
| `docs/source-manifest.json` | Historický zdrojový snapshot z 10. 10.; není inventář dnešního repozitáře. |
| `docs/research-snapshot*.json`, `docs/repository-validation.json` | Datované historické výsledky, nikoli dnešní souhrn. |
| `htr-fourth-100-pages`, `interpretation-fourth-100-pages` | Referenční skripty konkrétní etapy M II 220, závislé na externím výzkumném prostoru. |
| `presentation-storage-study`, `docs/experiments` | Metody a evidence měření/pilotů; negativní výsledky mají výzkumnou hodnotu. |
| `docs/validation` | Datované kontroly a vybrané screenshoty; jejich rozsah se nesmí rozšířit změnou názvu či datace. |
| `public/pagefind`, `node_modules`, `.wrangler`, `.credentials`, obrazová média | Generované nebo místní soubory, ignorované Gitem; nesmějí se přidat plošným `git add -f`. |

## Co při kontrole nebylo smazáno

`web/sample-20v.json` je vstup původního `build_data.py`, není sirotek.
Kořenové `document.json`, `structure.json`, `summary.json` a `pilot-data.js`
obsluhují M II 220 a staré odkazy. HTML fallbacky starých shrnutí doplňují
Pages přesměrování na prostém statickém serveru. Stejné názvy folií různých
dokumentů nejsou duplicity určené ke smazání.

Kopie motivu, loga a prezentačních assetů v `publication/` jsou vstupy builderů;
kopie v `public/` jsou jejich nasaditelné výstupy. Původní a webové TEI mají
odlišné facsimilní URI a záměrně existují vedle sebe. Staré validace a negativní
modelové experimenty jsou doklady, i když se nespouštějí při každém deploy.

V této kontrole nebyl prokázán nepotřebný sledovaný soubor, jehož odstranění
by zachovalo všechny výše uvedené funkce a doklady. Úklid proto odstranil
zastaralá tvrzení a návody, nikoli výzkumné zdroje. Místní pracovní adresáře
mimo tento Git checkout nebyly součástí úklidu.

Kontrola odhalila šest nefunkčních odkazů v původním posouzení Frolatu:
odkazovaly do nepřibalené místní pracovní složky. Nahradilo je výslovné
vymezení zachované evidence. Nic se nevydává za dostupný soubor, který v Git není.

Proti původním 52 hashům `source-manifest.json` se liší dva již dříve upravené
soubory: referenční `scripts/export.py` a `tests/test_export.py` ve skillu.
Commit `e8741de02fbbfe0329563bd677aff11f2a3d1466` z 12. 10. přidal cache
Relax NG validátoru a testy její ekvivalence. Nynější údržba tyto soubory
nemění. Původní manifest zůstává pravdivým historickým dokladem, nové hashe
a vysvětlení rozdílu zaznamenává
[kontrola údržby](validation/repository-maintenance-20261021.json).

## Přijetí vědecké opravy

Zachovat předchozí kandidáty, parametry, obrazovou identitu a SHA-256. Nová
četba asistenta není nový raw výstup Medusy. Výstup nad maskovaným, rozděleným
či narovnaným výřezem musí mít novou provenienci a vazbu na původní segment.
Tokenový limit původního pokusu se tím zpětně nemaže.

Řízený import musí ověřit očekávané předchozí hashe a povolený rozsah změny,
znovu vytvořit dotčené TXT/TEI/ALTO/JSON a zkontrolovat konzistenci. Teprve pak
se aktualizuje chráněný inventář. `update_source_manifest.py` není nástroj pro
plošné schválení změněných dat. Nová obrazová média potřebují nové verze klíčů;
existující R2 objekty s immutable cache se nepřepisují jinými pixely.

## Kontroly při údržbě

Použít [webový návod](../web/README.md). U dokumentace zkontrolovat místní
Markdown odkazy a soulad počtů s registrem. U frontendů spustit příslušné testy,
před deploy ověřit média a sestavit Pagefind. Sirotka odstraňovat až po kontrole
odkazů, importů, testů, builderů a veřejných URL; samotná absence textové
reference není důkaz, že historický příkaz nebo citovaný soubor nemá význam.

Změna Git repozitáře sama nenasazuje web. Nový audit musí mít vlastní datum,
rozsah a omezení; historický úspěšný scan secrets nepotvrzuje nový obsah.
Připravené změny této údržby prošly lokálním Gitleaks 8.30.1 bez nálezu;
[přesný rozsah kontroly](validation/maintenance-secrets-20261021.json).
Nejde o nový úplný scan historie ani o kontrolu všech místních credential souborů.
