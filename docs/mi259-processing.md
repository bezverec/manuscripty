# M I 259: metoda zpracování a meze interpretace

Třetí rukopis projektu je **M I 259 – Textus varii** z fondů
[Vědecké knihovny v Olomouci](https://www.vkol.cz/). Tento dokument popisuje
postup a význam jednotlivých vrstev. Publikace byla dokončena 19. 10. 2026
v [PR #17](https://github.com/bezverec/manuscripty/pull/17); dokument není
výsledkem odborné revize ani závěrečným vyúčtováním spotřeby.

## Prameny, popis a identifikátory

Obrazovým pramenem jsou místní archivní TIFFy dodané pro digitalizaci.
Katalogovým pramenem je dodané XML `M_I_259_____09Z2NI6_CS.XML` z metadatové
části dávky; do výzkumního adresáře bylo převzato beze změny. Jeho SHA-256 je
`896eee4a9a3b80a60bebcd2e409eceede8374807fdd8441efa7cb98472f931b3`.
Název *Textus varii*, datování, fyzický popis, vazba, historie, bibliografie
a další poznámky jsou převzatá katalogová tvrzení. Nejsou novým datováním
nebo kodikologickým posudkem AI. Úplný `msDesc` se zachovává v TEI;
interpretační výklad AI tvoří samostatnou, označenou vrstvu.

Digitální inventář obsahuje 371 snímků: běžná souborová označení `1r–180v`,
vazební části a dva dodatečné snímky `extra-83v` a `extra-84r`.
**ID snímku není ověřená původní foliace.** Katalog upozorňuje na nerozřezaný
dvojlist 83/84. Na kontrolovaných pozdějších listech je psané číslo o jedno
vyšší než souborové označení, například snímek `133r` nese číslo 134.
Souvislé mapování celého zbytku nebylo takto ověřeno. Workflow proto soubory
nepřejmenovává, neslévá dodatečné snímky s běžnými ID a nepřepisuje katalogová
čísla rozsahů podle odhadu. Doklady a míra nejistoty jsou ve
`foliation-review.json` výzkumné dávky.

Kontrolní součet vlastního vstupního souboru dokládá identitu daného
souboru mezi kroky zpracování. Sám o sobě nepotvrzuje shodu s historickým
stavem u dodavatele. Dodaný seznam MD5 a současné TIFFy vykazují rozpory;
jejich příčina není vysvětlena. Vlastní výchozí SHA-256/MD5 evidence a
dodavatelský seznam zůstávají oddělené. Tento rozpor se automaticky
neopravuje ani nepředkládá jako ověřená dodavatelská fixity.

## Obraz, souřadnice a odvozeniny

Archivní TIFFy zůstávají nezměněné. Pro práci vzniká nativní RGB PNG
z evidovaného snímku TIFFu. Pokud je nutná orientace, použije se bezztrátové
přeskládání pixelů bez převzorkování. V aktuálním manifestu je zaznamenáno
otočení proti směru hodinových ručiček: `FS`, `B001R` a `BS` o 90°,
`B001V` o 270°. Ostatní uvedené snímky takto otočené nejsou.

Webové souřadnice vycházejí z **celého orientovaného nemaskovaného PNG**,
nikoli automaticky z původního neotočeného TIFFu. Každý souřadnicový pramen
má vlastní ID, SHA-256, rozměry, číslo snímku, odkaz na SHA-256 původního
TIFFu, úhel a transformační matici. Počátek je vlevo nahoře, obdélník má
tvar `xywh`. Matice násobí sloupcový vektor `[x,y,1]` v souřadnicích hran
pixelů; nejde o souřadnice jejich středů. Bez příslušné transformace nelze
obdélník z orientovaného obrazu přenést na TIFF.

Deset převzatých pilotních stran (`1r`, `14r`, `18r`, `25r`, `46r`, `62r`,
`88r`, `100r`, `135r`, `145r`) používá původní modelový vstup s bílým
maskováním mimo vybranou hlavní zónu. Jeho hash a operace jsou vedeny jako
`model_input` zvlášť od plného souřadnicového obrazu. Obdélníky zůstávají
v témže systému rozměrů, ale hash maskovaného vstupu není hashem celého
nemaskovaného PNG. Pilot proto nevypovídá o schopnosti zachytit veškeré
marginálie celého listu.

WebP náhledy, dlaždice a řádkové výřezy jsou publikační deriváty; ztrátové
WebP se nevydává za archivní obrazový master. Celé souřadnicové PNG
zůstává místním bezztrátovým základem. Doplňkové ruční výřezy mají
samostatnou oblast a případnou vlastní rotaci; nejsou dalšími automaticky
rozpoznanými řádky.

Exportované ALTO pro archivní TIFF používá **souřadnice původního TIFFu**.
Webové návrhy změn segmentace naproti tomu musí být vztaženy ke konkrétnímu
orientovanému souřadnicovému prameni. Záměna těchto dvou prostorů by
posunula nebo otočila návrh opravy. Publikační adaptér proto přenáší
identitu a transformaci explicitně:
[build_mi259.py](../web/publication/build_mi259.py).

## Segmentace a dva HTR kandidáti

| Součást | Skutečná úloha | Verze nebo pramen |
|---|---|---|
| Kraken | Řádková segmentace BLLA, práce s polygony/baselines a CPU rozpoznávání | 7.1.1; [dokumentace](https://kraken.re/main/index.html), [kód](https://github.com/mittagessen/kraken) |
| CATMuS medieval | Původní grafematický kandidát bez automatického nahrazení rozvedenou ediční vrstvou | 1.6.0; [checkpoint na Zenodo](https://zenodo.org/records/15030337), [transkripční pravidla](https://catmus-guidelines.github.io/) |
| Medusa | Druhý řádkový VLM kandidát nad uloženými segmenty | [ENC-PSL/Medusa0.2Line-4B](https://huggingface.co/ENC-PSL/Medusa0.2Line-4B), [použitá revize](https://huggingface.co/ENC-PSL/Medusa0.2Line-4B/tree/2e891246c709976eb8fd90274932d1f08debcb15) |

CATMuS checkpoint má SHA-256
`227d10f15a936c2492105b7796a6152647c742f248af117856f417008eadbc9c`.
Medusa používá `model.safetensors` s SHA-256
`930f97e19686a94e2a9967014e437162153bb884121aa3923a1e25422d4e708b`.
Váhy nejsou součástí webového repozitáře. Přehled dalších dřívějších pokusů
je v [HTR technologiích](htr-technologies.md); jejich vyzkoušení na jiném
rukopisu neznamená použití pro M I 259. Chandra není součástí tohoto
produkčního řetězce.

CATMuS běží v místním CPU Dockeru. Medusa nejprve využívala místní službu;
pro hlavní dávku následovalo uživatelem schválené oddělené GPU okno s jedním
načtením modelu. Warm runner používá RTX 5070, NF4 double quantization,
BF16 výpočet, SDPA, deterministické generování, batch 8 a základní limit
128 nových tokenů. Parametr `enable_thinking=False` je požadovaný parametr
šablony; jeho skutečné vykreslení se kontroluje odděleně, nikoli pouhou
přítomností v kódu. Model nedostává přepis druhého enginu ani ediční návrh.
Prompt zní:

```text
Transcribe the handwritten text in this line image.
Output ONLY the transcription.
```

Zaznamenané warm prostředí: PyTorch `2.10.0+cu129`, torchvision
`0.25.0+cu129`, Transformers `5.2.0`, bitsandbytes `0.49.2`,
Accelerate `1.13.0`, Pillow `12.1.1`. CPU evidence uvádí PyTorch
`2.9.0+cpu`. Konkrétní soubory běhu jsou rozhodující pro dílčí inference.

Oba kandidáti sdílejí identitu fyzického segmentu a geometrii. **Nedostávají
nutně totožné vstupní tenzory:** Kraken/CATMuS pracuje s polygonem a baseline,
Medusa s hashovaným obdélníkovým výřezem a vlastní interní předúpravou.
Geometrický fingerprint je SHA-256 kanonicky serializovaného seznamu
`[bbox_xyxy, boundary, baseline]` všech řádků. Změna segmentace tedy vyžaduje
nové ověření návaznosti kandidátů a interpretace, ne pouhé zachování indexů.

## Opakování generování a původní raw

Zásah tokenového limitu může znamenat nedokončený řádek nebo repetitivní
smyčku. Nejprve se opakuje stejný výřez jednotlivě se stejným limitem.
Další recovery je **samostatný experiment se změněným dekódováním**:
batch 1, `max_new_tokens=256`, `repetition_penalty=1.08`,
`do_sample=False`. První pokus, retry, stav před recovery i nová kandidatura
se uchovávají odděleně. Zvolený raw může odkazovat na recovery; není to
potichu přepsaný původní výstup se stejnými parametry.

Ukončení EOS, nezasažení limitu a neprázdný výstup jsou technická kritéria,
nikoli ověření správnosti. I krátký řádek může být chybný a dva shodné
kandidáty může spojovat stejná chyba. Počet přetrvávajících limitů a
výsledky kontrol patří až do datovaného závěrečného reportu.

## Rekonstrukce, český překlad a obrazové doklady

Původní raw HTR, návrh rekonstrukce původního jazyka a český překlad jsou
tři oddělené vrstvy. Rekonstrukce může rozvádět zkratky a spojovat více
segmentů do odstavce. Nejde tím o diplomatický přepis každého znaku ani
o nové automatické rozpoznávání. Překlad je překlad skutečně navrženého
rozsahu; mezery v četbě nemají být skryty souvislým shrnutím.

Asistenti pracují s celostránkovými náhledy a skutečně otevřenými nativními
bezztrátovými pásy či výřezy. Záznam inspekce uvádí konkrétní soubor,
SHA-256 a rozsah kontroly. Připravení PNG ani záznam HTR úlohy samo
o sobě inspekci nedokládá. Převzaté piloty mají vlastní evidenci původu;
nemají být vydávány za nově provedené čtení celé strany.

Návrhy jsou `proposed`, `expert_review=false`. Nejistoty označují hranaté
závorky, otazníky a poznámky. Chybějící slova se nedoplňují automaticky
podle Vulgáty, právního kánonu nebo katalogového očekávání. Zejména nejasná
negace či podmínka může změnit význam celého právního výroku. Nezávislá
odborná reference není k dispozici; neuvádí se proto CER/WER jako naměřená
přesnost tohoto rukopisu. Ani vyhledání paralely nebo slovníkové zkratky
není důkazem, že takový znak je na daném listu skutečně napsán.

Automatické segmenty mohou zahrnout cizí text protějšího listu ve žlábku,
rozdělit konec věty nebo zaměnit otvor za písmeno. U listu označeného
`no_continuous_main_text` mohou stále existovat foliace, linkování,
prosvítání a materiálové stopy. Prázdný seznam řádků není sám o sobě
důkazem nepsaného listu. Doplňkové obrazové čtení vynechané oblasti se
označuje samostatně a nenahrazuje nezměněný raw HTR.

## Exporty, kontrola a provozní náklady

TEI cílí na [P5 4.12.0](https://github.com/TEIC/TEI/releases/tag/P5_Release_4.12.0)
s připnutým místním Relax NG. ALTO pro ProArc cílí na
[ALTO 3.0](https://www.loc.gov/standards/alto/). Při pouze řádkové geometrii
se nevymýšlejí souřadnice jednotlivých slov. XML parsování, validace RNG/XSD,
shoda raw TXT/XML, rozsahy souřadnic, lokální odkazy a obrazové hashe jsou
různé kontroly; žádná z nich nepotvrzuje správnost paleografické četby.
Schematron, skutečný import do ProArcu a kontrola vzhledu v prohlížeči
musí mít vlastní výslovný záznam, mají-li být prohlášeny za provedené.

Publikační adaptér vyžaduje zvlášť evidované kontroly inventáře, obrazových
pramenů, interpretací, pilotů a souřadnicových PNG. Tato metodická stránka
nepřebírá průběžný počet hotových stran jako výsledek finálního auditu.

Lokální HTR inference není spotřeba frontier asistenta. Metadata spotřeby
jednotlivých úloh, smíšené provozní úkoly rootu, předchozí piloty a práce na
jiném projektu je nutné oddělit. Cached input je podmnožina input tokenů,
reasoning podmnožina output tokenů. Týdenní ukazatel sdíleného účtu není
měřením nákladů tohoto rukopisu. Elektřina ani amortizace nebyly tímto
postupem měřeny; nelze je zaměnit za nulové náklady. Konečné součty ani
přepočet na cenu API zde nejsou uváděny.

Cloudflare Pages/R2 a OpenSeadragon slouží publikaci a prohlížení, nikoli
rozpoznávání. Přístupové údaje, účtové cache, původní TIFFy a modelové váhy
nepatří do veřejného repozitáře. Kontrola secrets má vlastní datovaný
rozsah a omezení; starší úspěšný scan není kontrolou nově připravené dávky.

## Ověřený publikační balíček z 19. října 2026

Balíček obsahuje 371 snímků, 17 414 automatických segmentů, 2 739 pracovních
interpretačních úseků a tři samostatná doplňková obrazová čtení. U 41 snímků
nebyl vymezen souvislý hlavní text; nejde o tvrzení, že na celém obrazu není
žádná stopa písma. Deset stran zachovává maskované modelové vstupy původního
pilotu, jejich veřejné obrazy jsou úplné.

Pět zachovaných kandidátů Medusy stále dosahuje tokenového limitu:
snímek 27v / segment 63, 46v / 53, 97v / 14, 119v / 28 a 124v / 100.
Jsou označené v datech i UI. Samostatný pokus s pozměněným dekódováním
má vlastní příznak a zachované předchozí výstupy; ukončení generování
nepotvrzuje správnost přečteného textu.

Úplné místní kontroly prošly pro všechny stránkové TEI (Relax NG P5 4.12.0),
ALTO (XSD 3.0), textovou identitu, geometrii, odkazy a zachování současných
zdrojových TIFFů. Převzatý katalogový msDesc zůstal textově zachován.
Veřejný balíček prošel nezávislou kontrolou všech tří dokumentů, statických
stran, návrhů oprav a vyhledávacího indexu 1 245 snímků. Tyto technické
kontroly nejsou odbornou paleografickou revizí.

Obrazy představují 66 119 WebP souborů (3 898 255 624 bajtů), včetně náhledů,
dlaždic a skutečných výřezů. Nahrání bylo 19. 10. zkontrolováno pro všechny
objekty přes velikost a ETag/MD5; produkční prohlížeč byl ověřen výběrově.
Dočasný token byl zneplatněn a jeho místní soubor odstraněn.
[Veřejný dokument](https://rukopisy.digitalizaty.cz/rukopisy/vkol-m-i-259).

## Následná kontrola pěti kandidátů (21. 10. 2026)

Všech pět původních výřezů a širší obrazový kontext bylo znovu otevřeno.
27v/63, 46v/53 a 124v/100 jsou úzké neúplné útržky sousedního listu,
97v/14 a 119v/28 skutečné řádky hlavního textu. Experiment s polygonovou
maskou, narovnáním baseline a dvěma překrývajícími se polovinami hlavních
řádků vytvořil devět diagnostických vstupů. Běžná místní služba je znovu
segmentovala na 15 částí. Žádný nový výstup nenarazil na tokenový limit,
ale technické ukončení neznamenalo úplnou či správnou četbu; nové raw nejsou
přijaty jako náhrada původních kandidátů.

Samostatný návrh četby a češtiny zpřesňuje dva hlavní řádky. U 97v je
pracovní interpretace „dřevo z posvěceného kostela“ podpořena právní paralelou,
nikoli vydávána za jistou diplomatickou četbu. U okrajových útržků se
chybějící slova nevymýšlejí. [Výsledek, kandidáti a provenience](experiments/2026-10-21-medusa-five/README.md).
Publikovaný korpus a jeho původních pět limitových příznaků zůstaly beze změny.

## Samostatný publikační doplněk z 21. 10. 2026

Po schválení uživatelem se obě zpřesněné četby publikují v nové vrstvě
`reading_addenda`, nikoli přepsáním původních pasáží či raw kandidátů.
Rozhraní je uvádí před starším výkladem s datem a nejistotami; u 97v odděluje
pokračování v segmentu 15. Stejný návrh je ve statickém foliu i v nových
JSON/TXT/TEI downloadech. Doplněk byl validován proti TEI P5 4.12.0.
Původní `edition.tei.xml`, `edition.web.tei.xml`, rekonstrukce, překlad,
oba raw TXT, ALTO i geometrie zůstávají beze změny.

Jednorázový importér `web/publication/publish_reading_addenda.py` přijímá
pouze připnutý výzkumný záznam a dvě původní SHA stranových adaptérů;
ověřuje jejich dřívější pole a mění pouze novou vrstvu a čtyři downloady.
[Audit importu](validation/reading-addenda-import-20261021.json).
Opakování nad již doplněnými daty záměrně odmítne.

Doplněk byl 21. 10. nasazen na veřejný web. Obě statická folia byla ověřena
v produkčním prohlížeči; u 119v také původní Medusa a její varování vedle nového
návrhu v řádkové analýze a překladové záložce.
[Záznam nasazení a rozsah ověření](validation/reading-addenda-publication-20261021.json).
