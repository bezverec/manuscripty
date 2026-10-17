# Chandra a hybridní segmentace: přínos v pilotu neprokázán

Výzkumný záznam z 17. 10. 2026, rukopisy M II 220 a M II 153 z fondů Vědecké knihovny v Olomouci.

**Na těchto vzorcích se neprokázal přínos přidání Chandry oproti správně připravenému vstupu Kraken.** První pozorování lepšího vymezení hlavičky Chandrou nebylo důkazem lepší řádkové segmentace. Následný kontrolní běh ukázal, že podstatné zlepšení hlavičky zvládne i samotný Kraken při zachování měřítka původní strany. Nejde o důkaz, že Chandra nemůže pomoci na jiném materiálu.

## Co bylo porovnáno

1. Chandra OCR 2 na stejných třech pracovních obrazech jako původní Kraken: M II 220, **20v a 335v**; M II 153, **5r**. Navíc samostatný původní výřez hlavičky 335v.
2. Hybrid: uložené obálky Chandry → nová řádková segmentace Kraken. Těsné obálky a jednotný přesah 64 původních pixelů.
3. Kontrola měřítka na 335v: původní ručně vymezená oblast → Kraken s bílým kontextem o výšce celé strany, **bez oblastí navržených Chandrou**.

| Strana | Původní Kraken | Hybrid těsně | Hybrid +64 px |
|---|---:|---:|---:|
| M II 220, 335v | 27 | 23 | 28 |
| M II 220, 20v | 84 | 82 | 86 |
| M II 153, 5r | 80 | 80 | 80 |

Počty jsou výstupní segmenty, nikoli skóre přesnosti nebo odborně ověřené počty fyzických řádků. Doplňkový výřez hlavičky měl v obou hybridních variantách pět segmentů, ale nemá přímé srovnání s původní segmentací celé pracovní strany.

## Zjištění a rozhodnutí

- **335v:** hybrid s přesahem zachytil hlavní hlavičku jedním širokým řádkem, ale vytvářel duplicity a volné obálky. Kontrola bez oblastí Chandry zachytila hlavičku rovněž jedním řádkem. Jejích 20 segmentů se neprohlašuje za odbornou referenci.
- **20v:** těsná varianta měla 82 segmentů bez malých fragmentů podle geometrického příznaku; původních 84 obsahovalo dva již dříve označené fragmenty. Přesah vytvořil čtyři malé fragmenty a možné duplicity u sousedního sloupce.
- **5r:** v obou variantách 80 segmentů, bez doloženého zlepšení proti stávajícímu postupu.
- **Rozpoznávání textu:** přepis Chandry v hlavičce se při změně výřezu výrazně měnil. Nový hybridní běh žádné HTR neprováděl, takže neměří dopad segmentace na Medusu nebo CATMuS.

Výchozí `blla.mlmodel` normalizuje výšku vstupu na 1800 pixelů. Nízký výřez tak může neúměrně zvětšit písmo. Dokončený hybrid zachovává nativní pixely oblasti na bílém plátně o výšce originálního TIFF; kontrolní běh stejný postup použil s původní ruční zónou. **Prioritou je ověřit a upravit přípravu vstupů Kraken. Plošné zařazení Chandry ani jednotného přesahu tento pilot nepodporuje.** Publikované přepisy a geometrie se experimentem nenahrazují.

Jde o tři vybrané pracovní obrazy s již maskovaným okolím, nikoli plně automatický benchmark neupravených originálů. Původní Kraken měl ruční zóny a dělení sloupců. Chybí nezávisle odborně ověřená referenční segmentace; nebylo měřeno F1, IoU proti ground truth, CER ani WER. Výsledek je omezený negativní výsledek tohoto pilotu, ne univerzální žebříček modelů.

## Výsledky a reprodukce

- [První Chandra pilot – metodika a dobová pozorování](chandra-segmentation-pilot-20261017/report.md), [souhrnná data](chandra-segmentation-pilot-20261017/results.json), [přesný prompt](chandra-segmentation-pilot-20261017/prompt.txt).
- [Hybrid a kontrolní běh – podrobný závěr](chandra-kraken-hybrid-20261017/report.md), [všechny dokončené varianty](chandra-kraken-hybrid-20261017/summary.json), [kontrola bez Chandry](chandra-kraken-hybrid-20261017/scale-control-335v.json).
- [Geometrické příznaky překryvů](chandra-kraken-hybrid-20261017/geometry-audit.json), [ověření původního místního běhu](chandra-kraken-hybrid-20261017/local-run-validation.json), [manifest archivovaných souborů a SHA-256](publication-manifest.json).

Archiv zachovává surové odpovědi Chandry, skutečné baseline a polygony Kraken, verze, časování a skripty. **Neobsahuje obrazy, modelové váhy, přístupové údaje ani HTML prohlížeče závislé na místních obrazech.** Záznamy `local-run-validation.json` dokumentují místní běhy včetně jejich obrazových souborů; nejsou tvrzením, že tyto obrazy existují v Git. Aktuální technickou kontrolu textového archivu obsahuje [archive-validation.json](archive-validation.json).

Samotný textový archiv lze ověřit bez obrazů příkazem `python docs/experiments/2026-10-17-chandra/verify_archive.py` z kořene repozitáře. Používá pouze standardní knihovnu Pythonu; kontroluje publikované SHA-256, JSON, syntaxi skriptů, místní odkazy a doložené počty variant. Neprovádí OCR ani odborné posouzení.

Skripty jsou zachovány ve svém původním pracovním uspořádání. Pro reprodukci je nutné umístit obě složky experimentů vedle původních zdrojových složek rukopisů a historických HTR dávek; požadované soubory a jejich SHA-256 uvádějí `source.json`, `result.json` a manifesty. Nejde o samostatný balíček obsahující zdrojové skeny. `run_pilot.py` předpokládá původní místní instalaci a endpoint Chandry; `run_hybrid.py` a `run_scale_control.py` CPU obraz `proarc5-kraken:7.1.1`, čtecí připojení pracovního prostoru na `/workspace` a zápis této experimentální složky na `/output`. `build_review.py` / `build_comparison.py` po obnově obrazů znovu sestaví místní přehledy. Původní `validate.py` ověřují tyto úplné místní experimenty, nikoli samotný textový Git archiv.

Chandra: [`datalab-to/chandra-ocr-2`](https://huggingface.co/datalab-to/chandra-ocr-2/tree/af93b47dba1b47b6640c86ccf487ed2260ab9a09), revize `af93b47dba1b47b6640c86ccf487ed2260ab9a09`, místní vLLM 0.17.0, RTX 5070 12 GB. Kraken: 7.1.1, PyTorch 2.9.0+cpu, čtyři vlákna; checkpoint a jeho SHA-256 v [engine.json](chandra-kraken-hybrid-20261017/engine.json).

Čtyři původní obrazové požadavky Chandry: 194,9 s, 22 369 vstupních a 3 659 výstupních tokenů místního modelu. Osm hybridních variant: 241,0 s; kontrolní segmentace: 23,5 s. Časy nezahrnují veškerou přípravu, start kontejnerů a přerušený úvodní pokus. Hybrid znovu použil uloženou Chandru. Placené OCR API nebylo použito; spotřeba asistenta ani elektřina nejsou vyčísleny.

## Původ přiloženého kódu

Prompt a fragment `scale_to_fit` pocházejí z [datalab-to/chandra](https://github.com/datalab-to/chandra), Apache-2.0; zachována je [licence](LICENSE.chandra-code.txt) a kontrolní součty skutečně použitého místního kódu. Skript pilotu pouze načítá tento prompt a extrahuje funkci změny měřítka. Váhy Chandry mají samostatné podmínky u [konkrétní revize modelu](https://huggingface.co/datalab-to/chandra-ocr-2/tree/af93b47dba1b47b6640c86ccf487ed2260ab9a09), nevztahuje se na ně licence kódu a nejsou distribuovány. Vlastní skripty a autorské zprávy spadají pod licenci tohoto výzkumného projektu. Surové modelové výstupy mají zachovaný původ a nejsou odborně schválenou edicí.
