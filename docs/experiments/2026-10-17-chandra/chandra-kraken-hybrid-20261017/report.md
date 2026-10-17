# Hybridní segmentace Chandra → Kraken

> Textový archiv pro GitHub. Obrazy a místní HTML prohlížeč se do Git neukládají. Záznam technické validace se vztahuje k původnímu místnímu běhu včetně obrazů.

17. 10. 2026 · [Souhrnný závěr pro GitHub](../README.md) · [Kontrolní geometrie bez Chandry](scale-control-335v.json).

**Přínos přidání Chandry nebyl v tomto pilotu prokázán. Řetězec funguje, ale test neprokázal obecnou převahu nad správně nastaveným Kraken. Podstatným zjištěním je vliv měřítka: hlavičku 335v dokázal výrazně zlepšit i samotný Kraken, když dostal vhodně připravený vstup.** Chandra zůstává možným nástrojem pro návrhy oblastí; plošné nahrazení dosavadní segmentace z tohoto vzorku nevyplývá.

## Provedený experiment

Použili jsme stejné tři pracovní obrazy jako v předchozím pilotu: M II 220, 20v a 335v; M II 153, 5r. Navíc jsme zopakovali doplňkový původní výřez hlavičky 335v. Chandra neběžela znovu: převzaty byly její skutečné obálky a pořadí bloků z `../chandra-segmentation-pilot-20261017/results.json`, se zaznamenanými SHA-256.

Uvnitř každého bloku jsme nově spustili Kraken 7.1.1 / výchozí `blla.mlmodel`, stejný segmentační model jako dříve, SHA-256 `77a638a83c9e535620827a09e410ed36391e9e8e8126d5796a0f15b978186056`. Běžel na CPU, čtyři vlákna, v izolovaném kontejneru bez sítě. Původní data byla připojena jen pro čtení. Neproběhlo HTR, rozvíjení zkratek, překlad ani změna veřejného webu.

Dvě jednotné varianty pro všechny oblasti:

- **Těsně:** obálka Chandra zaokrouhlená směrem ven na celé pixely.
- **Přesah 64 px:** stejná obálka rozšířená o 64 původních pixelů na každé straně, omezená hranicí vstupního obrazu.

Všechny detekované baseline a polygony jsou zachovány. Nedoplňovali jsme ruční řádky, nevytvářeli souřadnice z textu ani automaticky neodstraňovali duplicity. Čtení postupuje podle bloků Chandra a následně podle pořadí Kraken uvnitř bloku.

## Proč je důležité měřítko

Nejprve jsme zkusili předat oblasti přímo jako malé výřezy. Výchozí model Kraken však normalizuje **výšku na 1800 pixelů**. U první drobné poznámky měl výřez pouze 869 × 89 px: takový vstup neúměrně zvětšuje písmo i šířku obrazu. Pokus byl zastaven před dokončením první oblasti; je zaznamenán v `initial-crop-attempt.json`.

Dokončené varianty proto používají **bílé plátno o výšce původního TIFF** a šířce vybrané oblasti. Vybrané pixely zůstávají v nativním rozlišení a na původní svislé pozici, okolí je bílé. Žádná baseline se modelu neposkytuje. Kraken pak všechny bloky dané strany normalizuje při stejném svislém měřítku. U původního výřezu hlavičky je navíc přesně zaznamenán posun do rodičovské strany.

Polygon může přesahovat i do bílého okolí. Proto přehled po kliknutí otevírá řádkový výřez se **skutečně poskytnutými pixely**. Vedle něj je uložen i odpovídající výřez z úplného pracovního obrazu, aby bylo možné zkontrolovat vynechané části. Samotná větší obálka nad originálem nesmí být zaměněna za důkaz, že model dostal všechny tyto pixely.

## Výsledky

| Vzorek | Původní Kraken | Hybrid těsně | Hybrid +64 px |
| --- | ---: | ---: | ---: |
| M II 220, 335v | 27 | 23 | 28 |
| M II 220, 20v | 84 | 82 | 86 |
| M II 153, 5r | 80 | 80 | 80 |
| Samostatný původní výřez hlavičky | bez přímého srovnání | 5 | 5 |

Jde o **počty výstupních segmentů, nikoli skóre kvality ani ověřené počty fyzických řádků**.

**335v:** původní segmentace zachytila hlavní velký nápis jen jako dva nízké pásy. Těsný hybrid má dvě vyšší obálky, ale stále neúplný začátek. Varianta s přesahem zachytila hlavní nápis jednou širokou baseline. Současně přibrala část horní poznámky a jiné sousední řádky: geometrická kontrola označila pět možných úplných či částečných duplicitních párů mezi bloky. Některé nové obálky jsou příliš volné. Je to použitelný návrh opravy, nikoli hotová segmentace k vydání.

**20v:** těsný hybrid má 82 segmentů bez malých fragmentů podle jednotného geometrického příznaku. Původních 84 obsahovalo dva dříve označené malé fragmenty. S přesahem vzniklo 86 segmentů včetně čtyř malých fragmentů; rozšířená oblast zasahuje k sousednímu sloupci. Geometrická kontrola označila čtyři možné duplicitní páry. Nižší počet sám nezaručuje správnost všech řádků ani lepší rozpoznávání textu.

**5r:** obě varianty mají stejných 80 segmentů jako původní Kraken, bez malých fragmentů. Na této pravidelné dvousloupcové straně nebylo samotným počtem doloženo zlepšení. Přesná kvalita všech ořezů a následného HTR nebyla měřena.

**Kontrolní běh 335v bez Chandry:** původní ručně vymezenou zónu `[500,290,4200,2550]` jsme zpracovali samotným Kraken se stejným bílým kontextem o výšce 5900 px. Vzniklo 20 segmentů a hlavní hlavička byla také zachycena jednou souvislou baseline s podstatně vyšším polygonem než původně. Významná část předchozí chyby tedy souvisela s normalizací nízkého ořezu. Počet 20 opět není ověřený počet fyzických řádků; tato kontrola izoluje jediný konkrétní faktor na jediné straně.

## Omezení a doporučení

Nemáme nezávisle odborně zkontrolovanou referenční segmentaci. Nebylo měřeno F1, IoU proti ground truth, CER ani WER. Značení možných duplicit je jen geometrický příznak: mezi různými bloky používá IoU obdélníkových obálek alespoň 0,5, nebo pokrytí alespoň 80 % menší obálky se srovnatelnou svislou pozicí baseline. Není to automatické rozhodnutí, že jde o stejný fyzický řádek. „Malý fragment“ zde znamená šířku pod 150 px nebo výšku pod 25 px; ani tento příznak sám neprokazuje chybu.

Původní Kraken používal ruční zóny a u dvou stran také ruční dělení sloupců. Chandra dostala pracovní obrazy, na kterých je okolí těchto zón již bílé. Výsledky proto neověřují plně automatické zpracování neupravených originálů. U hlavního hybridu se navíc mění geometrie oblastí i měřítko vůči starému postupu. Kontrolní běh pomáhá odlišit vliv měřítka na 335v, ale není úplnou ablační studií všech stran a nastavení.

**Praktický další krok:** nejprve upravit a ověřit normalizaci vstupu Kraken. Chandra může navrhovat sloupce, hlavičky a problémové oblasti. Přesah má být omezen sousedními oblastmi a následovat má kontrola duplicit, nepokrytého textu a řádkových ořezů. Velkou hlavičku lze použít jako návrh nového výřezu pro Medusu, teprve tím by se ověřil dopad na čtení. Plošné nahrazení segmentace rukopisů by nyní bylo předčasné.

## Čas a uchování

Osm dokončených variant dohromady spotřebovalo **241,0 s měřeného běhu** včetně souvisejícího ukládání uvnitř variant. Dodatečný kontrolní segmentační běh trval **23,5 s**. Tyto součty nezahrnují start kontejnerů, úvodní přerušený pokus, přípravu a vykreslení přehledu. Nové tokeny Chandry se nespotřebovaly, protože byly použity její uložené výsledky; placené OCR API použito nebylo. Spotřeba tohoto asistenta a elektřina vyčísleny nejsou.

Původní obrazy, starší segmentace a předchozí výstupy Chandry jsou zachovány. `local-run-validation.json` kontroluje jejich SHA-256, shodu modelu, přesné převody skutečných souřadnic Kraken z každého plátna a místní odkazy přehledu. Toto technické ověření neznamená odborné potvrzení správnosti řádků.

Reprodukce: `run_hybrid.py` uvnitř obrazu `proarc5-kraken:7.1.1` s kořenem pracovního prostoru na `/workspace` jen pro čtení a touto složkou na `/output`; stejně `run_scale_control.py`. Přehled vytváří místní `build_review.py`, technickou kontrolu provádí `validate.py`. Konfiguraci, časování a surovou lokální geometrii obsahují `engine.json`, `summary.json` a `*.local-segmentation.json`. Nikde nebyla původní geometrie potichu přepsána opravenými odhady.
