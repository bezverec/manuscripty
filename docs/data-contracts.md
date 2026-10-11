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

## Veřejný snapshot a návrhy změn (11. 10. 2026)

web/public/data/{folio}/page.json je prezentační adaptér: spojuje raw_htr.catmus/medusa, původní source_segment_ids, bbox, obrazové URL, pracovní pasáže a odkazy na původní textové exporty. Nejde o nahrazení kanonického výzkumného JSON. document.json určuje instituci, signaturu a projektový URI. pilot-data.js obsahuje globální pořadí 677 snímků, structure.json pracovní navigaci odvozenou z pasáží.

HTR a segmentační návrhy uchovávají původní text či geometrii, ID a SHA-256 zdroje, URL místa a důvod. Segmentační schéma manuscripty-segmentation-proposal-v1 používá operace resize/split/merge/add/remove; nové obdélníky mají pořadí a souřadnice [x,y,width,height] v původních pixelech od levého horního rohu. Stav zůstává proposed a expert_review false. Validace hranic nebo modelová shoda nemění stav odborné revize.

Přijetí změny musí být samostatně zaznamenáno a řízeně promítnuto do závislých výřezů, HTR a exportů. UI pouze stáhne návrh nebo předvyplní GitHub issue; nezapisuje do kanonického korpusu.
