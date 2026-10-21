# M I 259: útržky sousedních listů, 21. 10. 2026

Kontrola obrazových přehledů všech **371 snímků** a polohy původních **17 414
segmentů** potvrdila, že dřívější tři případy nejsou ojedinělé. Při skenování
se často zachytil úzký pruh protější stránky a Kraken jej dále rozřádkoval.
„Útržek“ zde znamená neúplně zachycený text ve výřezu, nikoli tvrzení, že je
samotný list fyzicky utržený.

Nově se označuje **4 022 samostatných fragmentů** a **jeden smíšený výřez**.
Spolu se třemi dřívějšími poznámkami je to **4 025 fragmentů a jeden přesah
na 197 snímcích**. Jde o počet automatických segmentů, nikoli počet listů,
nezávislých textů či chyb rozpoznávání. Součet segmentů korpusu se nemění.

## Co bylo skutečně prohlédnuto

- 16 přehledových tabulí všech snímků včetně vazby a prázdných stran.
- 27 tabulí s okrajovým kontextem 216 stran, odvozeným z původních pixelů
  úplného souřadnicového obrazu; náhled je zmenšen na 28 %.
- Čtyři detailní tabule 46 hraničních kandidátů a osm dalších výřezů
  v nativním rozlišení pro vyjasnění jednotlivých případů.

Rozhodující je fyzický přehyb mezi listy, návaznost písma a poloha konkrétního
segmentu. Krátké okrajové boxy sloužily k výběru kandidátů; samotné souřadnice
ani nesmyslný HTR výstup nebyly přijaty jako důkaz. Prvotní geometrický výběr
byl upraven po obrazové kontrole. Například `f134v_l019`, `f103v_l027`,
`f41v_l008` a `f44v_l032` patří hlavnímu listu; `f91v_l082` zachycuje poškození
a `f56r_l002` stopu inkoustu. Nejsou nově označené. Popisky diagramu na 87r
rovněž zůstávají bez tohoto příznaku.

`f25v_l055` zahrnuje konec řádku hlavního listu i text za přehybem.
Má proto odlišnou klasifikaci `mixed_main_and_neighboring_leaf`, příznak
`neighboring_leaf_overlap` a poznámku „Přesah do sousedního listu“.
Celý tento výřez nelze označit za cizí text. Samostatné fragmenty používají
dosavadní `partial_neighboring_leaf` / `neighboring_leaf_fragment`.

Vše je **pracovní obrazové posouzení AI (`proposed`, `expert_review: false`)**.
Nejde o novou paleografickou revizi každého znaku ani záruku, že byly nalezeny
všechny smíšené boxy a dosud nesegmentované stopy. Snímky bez nově označeného
segmentu tím nejsou prohlášeny za snímky bez cizího textu. Předchozí rekonstrukce
a překlady zůstávají původními návrhy; anotace jejich obsah nově nepotvrzuje.

## Zachování dat a reprodukce importu

[Zmrazený přehled](report.json) obsahuje přesné identifikátory, geometrii,
SHA původních výřezů, zdrojových souřadnicových obrazů a výchozích `page.json`,
rozpis kontroly všech stran i SHA skutečně prohlédnutých obrazových tabulí.
Obrazové tabule zůstávají v místním adresáři
`deployment/neighbor-leaf-survey-20261021/`; do Git ani na web se nově nenahrávají.
Původní veřejné výřezy jsou v záznamu propojené jednotlivě.

Jednorázový importér mění pouze poznámku, nový příznak a novou
`editorial_annotation` u uvedených řádků. Před zápisem ověří všechny výchozí
SHA a při změně výchozího stavu nebo opakování odmítne pokračovat. Původní tři
anotace nepřepisuje. Odebráním nových polí a obnovením předchozí poznámky
a příznaků se musí získat přesně původní struktura každé strany.

```powershell
python web/publication/publish_neighbor_fragments.py --review-sha256 6faad8b22157551b3c8e8cc4b6371b8e06677ac32741b7f53c84f9f1b91bb2c0
# Pouze nad původním snapshotem; zápis vyžaduje navíc --apply.
```

Oba raw kandidáti, všechna dřívější varování Medusy, ID a geometrie,
interpretace, TXT, ALTO a TEI zůstávají zachované. Nebyla spuštěna nová HTR
inference ani placené API. Nové poznámky jsou v řádkové analýze vedle obou HTR
kandidátů a u výchozího přepisu statických folií; nevstupují do vyhledávacího
indexu jako rukopisný text.

[Audit přesně omezeného importu](../../validation/mi259-neighbor-survey-import-20261021.json).

Technická kontrola prošla pro všech 1 245 statických folií a 191 833 místních
odkazů. Úplný snapshot ověřil 12 721 veřejných textových souborů včetně shody
raw kandidátů s původními porovnáními, TXT, geometrie a indexu TEI. Všech
4 094 ostatních datových souborů M I 259 má původní záznam v kontrolním
manifestu. Neplatný hash podkladů a opakování importu byly skutečně odmítnuty
bez zápisu. [Kontroly zachování](../../validation/mi259-neighbor-survey-preservation-20261021.json)
a [celkový záznam technického ověření](../../validation/mi259-neighbor-survey-validation-20261021.json).

Nová verze byla 21. 10. nasazena na veřejný web. U všech 197 změněných
`page.json` byla poté ověřena shoda celého těla odpovědi se SHA místní přijaté
verze, tedy všech 4 023 nových anotací. V produkčním prohlížeči byly otevřeny
oba typy poznámek vedle původních kandidátů a smíšený případ také ve statickém
foliu. [Nasazení a přesný rozsah kontroly](../../validation/mi259-neighbor-survey-publication-20261021.json).
