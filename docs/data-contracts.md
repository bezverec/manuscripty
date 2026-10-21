# Datové vrstvy a validační pravidla

## Vrstvy

| Vrstva | Příklady souborů ve výzkumných datech | Pravidlo |
|---|---|---|
| Archivní zdroj | EX/*.TIF | SHA-256, rozměry a frame; původní obraz zachovat |
| Výběr a příprava | selection.json, manifest.json, image.png | Oblasti, pořadí sloupců a původní pixelové souřadnice |
| Segmentace | segmentation.json, řádkové PNG | Stabilní ID, baseline, polygon, bbox a vazba na zdroj |
| Surové HTR | catmus.candidates.json, medusa.candidates.json, *.raw.txt | raw_unreviewed; původní Unicode a nezávislé kandidáty |
| Obrazové podklady | inputs.json, tiles/, inspection log | Souřadnice, SHA-256 a evidence skutečného otevření |
| Interpretace | reconstruction.json | proposed; samostatná latina, čeština, nejistoty a ID segmentů |
| Přezkoumání | review.html, reconstruction.tei.xml, *.txt | Klikatelné obrazy a zachované rozlišení vrstev |
| OCR pro import | TXT, ALTO XML, ZIP | Surový CATMuS text, skutečná geometrie a samostatná validace |

Konkrétní interpretační JSON obsahuje schema, document_id, folio, source_original, source_sha256, source_folder, author, created_utc, image_inspection a passages. Pasáž má id, source_segment_ids, latin_reconstruction, czech_translation, notes_cs, status, human_reviewed a uncertainty_notation. Kompletní pravidla referenčního exporteru jsou v [formats-and-evaluation.md](../medieval-manuscript-transcription/references/formats-and-evaluation.md); produkční pasážový JSON je jiný vstupní formát. Syntetický demo.json se přímo nepředává produkčnímu export_interpretation.py.

## Nejistota a status

Obrazové čtení asistenta není odborná revize člověkem. human_reviewed a expert_reference zůstávají false, dokud příslušná revize skutečně neproběhne. CER a WER jsou null bez nezávislého referenčního přepisu.

Produkční TEI převádí nejistotu značenou ⟦…⟧ na unclear s nízkou jistotou, konjekturální doplnění […] na supplied reason=conjecture a nerozřešené úseky na gap reason=unresolved. Neurčitost není automaticky fyzické poškození pergamenu. Zkratky a běžné textové opravy rozlišuje referenční exporter. Latinská plynulost není důkaz správného čtení.

## Technické kontroly

- Výběr, manifest a všechny modelové výstupy musí mít stejné jedinečné folio a segmenty; pořadí a členství se ověřují.
- Geometrie je v mezích obrazu; nativní pruhy odpovídají pracovním a archivním pixelům uvnitř zón. Vytvořený soubor není důkaz jeho prohlédnutí.
- Checkpoint může být obnoven jen při shodě vstupních a modelových SHA-256. Kandidát se nepřepisuje normalizovanou či rekonstruovanou latinou.
- TEI P5 4.12.0 se ověřuje místním oficiálním Relax NG přes lxml bez sítě. Vložený XPath 2 Schematron nebyl spuštěn; RNG nehodnotí filologickou správnost.
- Produkční ALTO 3.0 prochází místním XSD včetně importů; kontroluje se TXT, XML a geometrie. Referenční skill generuje výchozí ALTO 4.4, které není produkčním ProArc profilem.
- CTC inkluzivní koncová pozice se převádí na polootevřený interval end + 1. Tam, kde slovní geometrie chybí, se řádkový fallback označuje; odhadované slovní obdélníky se nevydávají za měření.
- ZIP kontroluje CRC, přítomnost souborů a shodu SHA-256 členů. Technická kontrola tohoto OCR balíčku není kompletní validace NDK PSP ani ověřený import do živé instance ProArcu.
- Dokončení etapy vyžaduje také načtení uložených exportů zpět z disku, ověření HTML odkazů a nezměněnost starších artefaktů.

## Auditní omezení

Rozdíl dvou HTR výstupů není chybovost vůči pravdě. Náhradní polygonizace a dosažení generačního limitu musí být přiznány v provenienci. Časy souběžných CPU/GPU větví se nesčítají jako délka projektu. Tokeny lokální Medusy nelze zaměnit za spotřebu frontier asistenta ani přepočítat na procenta předplatného.

## Veřejný korpus a návrhy změn (21. 10. 2026)

`web/public/data/{folio}/page.json` je původní namespace M II 220.
M II 153 a M I 259 používají `data/{document_id}/{folio}/page.json` a vlastní
JSON manifesty. `web/manuscripts.json` vybírá manifesty tří dokumentů;
`pilot-data.js` zůstává záměrně původním manifestem 677 snímků M II 220.
Každý stránkový adaptér spojuje raw kandidáty, ID, bbox, obrazy, pasáže a
downloady; nenahrazuje kanonický výzkumný JSON. Celkem jde o 1 245 snímků.
Vlastní `document.json` a `structure.json` nových dokumentů jsou uvnitř jejich
namespace; kořenové soubory zachovávají zpětnou kompatibilitu M II 220.

Návrhy uchovávají původní text/geometrii, ID, SHA-256, URL a důvod.
Segmentační operace jsou resize/split/merge/add/remove; obdélníky mají tvar
`[x,y,width,height]`, počátek vlevo nahoře. První dva dokumenty zachovávají v1.
M I 259 používá `manuscripty-htr-proposal-v2` a
`manuscripty-segmentation-proposal-v2`: `coordinate_source` má vlastní ID,
SHA-256, rozměry a transformaci do původního TIFFu. V2 souřadnice jsou v celém
orientovaném nemaskovaném PNG, nikoli automaticky v neotočeném TIFFu.
`model_input` se vede samostatně; deset pilotů M I 259 má maskování, čtyři
vazební snímky mají rotaci. Matice násobí sloupcový vektor `[x,y,1]` v prostoru
hran pixelů. [Podrobnosti](mi259-processing.md). Stav zůstává `proposed`,
`expert_review=false`; validace hranic nebo shoda modelů není odbornou revizí.

Přijetí změny musí být samostatně zaznamenáno a řízeně promítnuto do závislých výřezů, HTR a exportů. UI pouze stáhne návrh nebo předvyplní GitHub issue; nezapisuje do kanonického korpusu.

## Dodatečné návrhy čtení

Volitelné `page.json.reading_addenda` uchovává novější rozvedenou četbu AI
odděleně od původních `lines.raw_htr`, `passages` a jejich exportů.
Každý návrh má datum, stav `proposed`, `expert_review=false`, zdrojové
`line_ids`, hlavní `target_line_ids`, rekonstrukci, český překlad, nejistoty
a SHA původního obrazového výřezu i výzkumného záznamu. Pokračování z dalšího
řádku má samostatné pole a vlastní řádkovou vazbu. `supersedes_passage_ids`
označuje starší výklad, který návrh zpřesňuje; nemaže jej ani nemění jeho text.

První dvě taková čtení patří M I 259, 97v/14 (+ kontext 15) a 119v/28.
Samostatné `reading-addenda.json`, TXT a TEI P5 4.12.0 jsou nové downloady;
původní TXT, ALTO, TEI a tokenové příznaky Medusy zůstávají stejné.
Konjektury jsou v doplňkovém TEI označené `supplied reason="conjecture"
cert="low"`; zachovávají také viditelné závorky s otazníkem. Návrh se zobrazuje
v řádkové analýze, interpretační záložce i statickém foliu. Test:
`cd web && npm run test:readings`.

## Redakční anotace sousedních listů

Volitelné `lines[].editorial_annotation` klasifikuje obrazový obsah původního
segmentu; není opravou rozpoznaného textu ani novou segmentací.

| Příznak v `flags` | `classification` | Význam |
|---|---|---|
| `neighboring_leaf_fragment` | `partial_neighboring_leaf` | Samostatný neúplný text sousedního listu v okrajovém pruhu snímku. |
| `neighboring_leaf_overlap` | `mixed_main_and_neighboring_leaf` | Box zachycuje také část hlavního řádku; nelze jej celý považovat za cizí text. |

Anotace obsahuje datum, `status: proposed`, `expert_review: false`,
`evidence_review_sha256` a `source_crop_sha256`. Rozšířená kontrola uvádí také
`evidence_review_path`; tři původní poznámky bez tohoto pole odkazují na pevně
určený záznam kontroly pěti řádků. `validate_snapshot.py` přijímá pouze výslovně
povolené záznamy a ověřuje jejich SHA, ID řádku, klasifikaci, bbox a SHA výřezu
proti původnímu `comparison.json`. Podklady nejsou načítány z libovolné cesty
zadané v datech. Všechny přijaté anotace musí zůstat přítomné.

Lidsky čitelná `note` doplňuje předchozí poznámku; původní příznaky včetně
`medusa_token_limit` se zachovávají. `raw_htr`, souřadnice, identifikátory,
pasáže a starší TXT/ALTO/TEI se nemění. Samostatná poznámka proto nevyžaduje
nový OCR export. Na 197 snímcích M I 259 je 4 025 fragmentů a jeden smíšený
box; celkový počet segmentů zůstává 17 414. „Fragment“ neoznačuje automaticky
fyzické poškození listu ani kvalitu přepisu.

Poznámky jsou v řádkové analýze u obou kandidátů a ve výchozím HTR statického
folia. V HTML mají `data-pagefind-ignore`, aby se nezaměňovaly za rukopisný
text ve vyhledávání. Podrobnosti: [obrazový průzkum](experiments/2026-10-21-mi259-neighbor-survey/README.md).
