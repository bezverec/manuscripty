# Stav výzkumu a publikace k 21. 10. 2026

Veřejná knihovna obsahuje **tři rukopisy z fondů Vědecké knihovny v Olomouci,
1 245 snímků**. Níže je stav publikovaného korpusu z 19. 10. 2026, nikoli nová
odborná revize. Počty vycházejí z registru `web/manuscripts.json` a stranových dat.

| Dokument | Snímky | Segmenty v UI | Interpretační úseky s českým překladem |
|---|---:|---:|---:|
| [M II 220](https://rukopisy.digitalizaty.cz/rukopisy/vkol-m-ii-220) | 677 | 50 297 | 5 634 |
| [M II 153](https://rukopisy.digitalizaty.cz/rukopisy/vkol-m-ii-153) | 197 | 15 013 | 3 531 |
| [M I 259](https://rukopisy.digitalizaty.cz/rukopisy/vkol-m-i-259) | 371 | 17 414 | 2 739 |
| Celkem | **1 245** | **82 724** | **11 904** |

Segmenty nejsou počty správně přečtených fyzických řádků. Segmentace může řádek
rozdělit nebo zahrnout sousední list. Zdrojové vrstvy M II 220 mají 50 299
segmentů; dvě dvojice na 20v jsou v UI spojené. Interpretační úseky zahrnují
výslovně označené nečitelné fragmenty, nikoli jen úplné souvislé věty.

M II 220 má 670 foliovaných a sedm vazebních snímků; šest foliovaných stran
nemá hlavní text ve vybraných oblastech, vazba je nepřepsaná. M II 153 má 192
foliovaných a pět vazebních snímků; osm snímků nemá hlavní text ve vybraných
oblastech. M I 259 má `1r–180v`, devět vazebních/předsádkových snímků a dva
zvláštní záběry. U 41 snímků nebyl vymezen souvislý hlavní text. Navíc obsahuje
tři samostatná doplňková obrazová čtení mimo automatické segmenty.

## Hranice výsledků

Hlavní HTR větve používají Kraken 7.1.1 / CATMuS medieval 1.6.0 a
ENC-PSL/Medusa0.2Line-4B. Kandidáti, rekonstrukce původního jazyka a český
překlad jsou oddělené vrstvy. Interpretace jsou `proposed`,
`expert_review=false`; nezávislá odborná reference a měření CER/WER chybějí.
[Modely a revize](htr-technologies.md).

Publikovaná původní Medusa vrstva M I 259 má pět tokenově omezených kandidátů:
`27v/63`, `46v/53`, `97v/14`, `119v/28`, `124v/100`. Jsou označené v datech a
řádkové analýze. Nová četba nebo inference nad upraveným výřezem se uchovává
zvlášť. [Metodika a následná kontrola](mi259-processing.md).

M I 259 má rozdíly mezi souborovými ID a psanou foliací. Globální renumerace
neproběhla; `extra-83v` a `extra-84r` zůstávají samostatné. Deset převzatých
pilotů má maskovaný modelový vstup, ale veřejný souřadnicový obraz je úplný.

Pilot Chandra → Kraken ze 17. 10. **neprokázal přínos přidání Chandry**.
Výrazný vliv mělo měřítko vstupu; větší hlavičku 335v lépe zachytil i samotný
Kraken po vhodné přípravě. Plošná změna segmentace ani měření vůči odborné
referenci neproběhly. [Experiment](experiments/2026-10-17-chandra/README.md).

## Web, návrhy oprav a exporty

Společný prohlížeč nabízí tři dokumenty, HTR, řádkovou analýzu, rekonstrukci,
překlad, strukturu, katalogové údaje a odlišený výklad AI. Podporuje skrytí a
šířku panelů, noční režim a jediné označení „Zdigitalizováno ve VISK 6“
v přehledu. Statická folia lze číst bez JavaScriptu, hledání používá Pagefind.
Pracovní struktura není odborně ověřené vymezení děl.

Návrhy HTR/segmentace se stahují jako JSON nebo předvyplní GitHub issue.
Nevstupují automaticky do korpusu. M I 259 používá v2 s identitou celého
orientovaného souřadnicového obrazu a maticí k TIFFu; první dva dokumenty
zachovávají v1. [Kontrakty](data-contracts.md).

TEI P5 4.12.0 obsahuje katalogové `msDesc`, instituci, fyzický popis, historii
a poznámky. Celorukopisové TEI jsou popisy a facsimilní indexy s odkazy na
stranové edice. OCR TXT/ALTO 3.0 nejsou celé NDK PSP. RNG/XSD validace není
import do ProArcu ani odborná kontrola. IIIF je vypnutý návrh pro M II 220.

## Evidence a náklady

Publikace M I 259 proběhla 19. 10. 2026 v PR #17. Tehdy byla doložena kontrola
všech 66 119 nahraných WebP a výběrová kontrola produkčního UI. Dočasný upload
token byl zneplatněn a místní soubor odstraněn. Datované audity
v `docs/validation` dokládají svůj tehdejší rozsah, nikoli pozdější změny.

Lokální tokeny Medusy nejsou spotřeba Codexu. Sdílený týdenní limit a souběžná
práce na jiném projektu neizolují cenu tohoto výzkumu. Záznamy z 10. a 11. 10.
jsou historické snapshoty, ne současný součet. [Pravidla údržby](maintenance.md).
