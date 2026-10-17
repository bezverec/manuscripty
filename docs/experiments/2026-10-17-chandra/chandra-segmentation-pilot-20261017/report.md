# Chandra 2 proti stávající segmentaci Kraken

> Textový archiv pro GitHub. Obrazy a místní HTML prohlížeč se do Git neukládají. Záznam technické validace se vztahuje k původnímu místnímu běhu včetně obrazů.
> Pozdější hybridní pokus a kontrola měřítka přínos Chandry nepotvrdily; rozhodující je [souhrnný závěr](../README.md), nikoli izolované první pozorování hlavičky.

Malý místní experiment, 17. 10. 2026. [Souhrnný závěr pro GitHub](../README.md).

**Výsledek: Chandra je slibná pro návrhy textových oblastí a opravy problémových hlaviček. V tomto testu není přímou náhradou Kraken pro řádkové HTR.** Nejde o statistický benchmark ani o nezávisle odborně ověřené hodnocení.

## Co jsme skutečně provedli

Spustili jsme `datalab-to/chandra-ocr-2`, revize `af93b47dba1b47b6640c86ccf487ed2260ab9a09`, přes již běžící místní vLLM 0.17.0 na RTX 5070 s 12 GB paměti. Použit byl standardní prompt `ocr_layout`, temperature 0, top_p 0.1, seed 42, limit 6000 výstupních tokenů. Všechny čtyři odpovědi skončily `stop`, žádná dosažením tokenového limitu. Hlavičky nebyly při zpracování odpovědí odfiltrovány.

Tři celé **pracovní obrazy** jsou stejné soubory, z nichž pochází uložená segmentace Kraken. Ta byla znovu načtena, nikoli znovu spuštěna. Čtvrtý vstup je samostatný výřez původní hlavičky. Chandra automaticky zmenšuje vstup podle přiložené upstream funkce `scale_to_fit` na přibližně 6,3 Mpx; Kraken dříve pracoval v původním rozlišení a s ručními zónami. Souřadnice jsou převedeny zpět do pixelů příslušného vstupu. U výřezu je zaznamenán i posun do originálu.

| Vzorek | Stávající segmenty Kraken | Bloky Chandra | Místní požadavek |
| --- | ---: | ---: | ---: |
| M II 220, 335v | 27 | 6 | 116,4 s |
| M II 220, 20v | 84 | 2 | 34,3 s |
| M II 153, 5r | 80 | 2 | 39,8 s |
| 335v, samostatná původní hlavička | neporovnáváno | 3 | 4,5 s |

**Řádkový segment a textový blok nejsou stejná jednotka.** Tato čísla popisují výstup, nejsou skóre kvality. Kraken 7.1.1 používal výchozí segmentační model `blla.mlmodel`, SHA-256 `77a638a83c9e535620827a09e410ed36391e9e8e8126d5796a0f15b978186056`. CATMuS a Medusa jsou v našem dosavadním postupu rozpoznávače textu; v tomto experimentu nesrovnáváme jejich segmentaci.

## Co je vidět nad obrazem

**335v: konkrétní přínos u velké hlavičky.** Původní polygony `f335v_l002` a `f335v_l003` zachycují jen spodní pásy jedné fyzické řádky. Chandra vytvořila souvislý blok b002 s obálkou přibližně `[1489.5,318.6,3937.5,590.0]` v originálních souřadnicích a zahrnula podstatně větší část písmen. Oddělila také horní poznámku, hlavní odstavec a tři dolní odstavce. To může být užitečný návrh opravy oblasti. Některé sousední obálky se překrývají, takže nejde o hotové přesné výřezy pro všechny řádky.

Obrazový detail hlavičky zůstává v místním experimentu; Git archiv obsahuje skutečné geometrie v JSON..

**20v a 5r: dobré hrubé rozdělení na sloupce.** Na obou stranách Chandra našla dva velké bloky, levý před pravým. Kraken ale již má jednotlivé řádky. V pravidelném dvousloupcovém textu tento pokus neprokázal lepší řádkovou segmentaci Chandrou. Její standardní prompt ostatně žádá spojovat řádky do odstavců; značky `<br>` v odpovědi nejsou měřená řádková geometrie.

**Výřez originální hlavičky: rozložení užitečné, čtení nestabilní.** Na celostránkovém vstupu Chandra navrhla „Anno domini mcccclii. Nicolai archiepiscopi“, na samostatném výřezu „Annus dominici exiit xli. Scilicet ex nola“. Žádné z těchto čtení nepovažujeme za ověřené datum nebo jméno. Větší písmo a správně vymezený blok samy nezajišťují správnou transkripci.

## Omezení srovnání

- Kraken dostal ručně určené zóny, u dvousloupcových stran i rozdělení sloupců. Chandra dostala celý již maskovaný pracovní obraz, takže i ona získává nápovědu z bílých okrajů a mezisloupcové mezery. Zde není otestována plně automatická detekce všech oblastí z neupravených originálů.
- Na 335v začíná původní maska u y=290 a část drobné horní poznámky už chybí na vstupu obou postupů. Samostatný původní výřez tuto chybu ukazuje, ale kvůli změně vstupu se proti původnímu Kraken nepočítá.
- Chandra vrací generované obdélníkové obálky bloků; Kraken skutečné řádkové polygony a baseline. Nepřeváděli jsme odstavce na smyšlené řádkové souřadnice. Nezkoušeli jsme upravený prompt pro samostatné fyzické řádky ani další trénování.
- Nemáme odbornou referenční segmentaci. Nebylo měřeno IoU proti ground truth, F1, CER ani WER. Obrazové pozorování asistenta má stav návrhu, nikoli odborné revize. Tři vybrané strany nereprezentují celý fond.
- Časy měří celý místní požadavek Chandra včetně rozpoznávání textu. První požadavek zahrnul výraznou úvodní režii a nelze jej použít jako ustálenou rychlost. Původní Kraken běžel na CPU; jeho starší časy nejsou s tímto GPU během přímo srovnatelné.

## Spotřeba a další použití

Čtyři obrazové požadavky dohromady trvaly **194,9 s**, měly **22 369 vstupních a 3 659 výstupních tokenů** místního modelu. Nejde o tokeny účtu Codex. Cena placeného OCR API byla **0 Kč**; elektřina a spotřeba tohoto asistenta zde vyčísleny nejsou. Při diagnostice úvodního čekání byly odeslány také tři velmi malé čistě textové kontrolní požadavky; vypršel jejich klientský timeout a do výsledkové tabulky ani součtu čtyř obrazových požadavků nepatří.

Doporučeným dalším krokem je omezený pokus **Chandra navrhne oblasti → řádkový segmentátor zpracuje oblasti → obrazová kontrola problémových míst**. Na 335v lze velkou jednořádkovou hlavičku použít jako návrh nového výřezu pro Medusu. Funkčnost tohoto navazujícího řetězce zde ještě nebyla otestována. Plošná výměna segmentace obou rukopisů by z těchto výsledků nebyla podložená.

Originály, stávající přepisy a veřejný web zůstaly zachovány. Přesný prompt, vstupy modelu, nezměněné odpovědi, geometrie a kontrolní součty jsou v této složce. `local-run-validation.json` obsahuje závěrečnou kontrolu zdrojů, souřadnic a odkazů přehledu. Experiment lze znovu vykreslit pomocí `build_comparison.py`; `run_pilot.py` přeskočí již dokončené vzorky.

## Zdroje a provenance

- [Oficiální Chandra a popis výstupů](https://github.com/datalab-to/chandra).
- [Oficiální prompt – bloky, normalizace 0–1000 a spojování řádků](https://github.com/datalab-to/chandra/blob/master/chandra/prompts.py).
- [Přesná revize modelu](https://huggingface.co/datalab-to/chandra-ocr-2/tree/af93b47dba1b47b6640c86ccf487ed2260ab9a09).
- `run-config.json`, `results.json`, `observations.json`; pro každý vzorek `source.json`, `request.json`, `response.json`, `raw.html`, `result.json`, `input.png` a kopie původní segmentace `kraken.json`, kde je srovnání provedeno.
