# Stav rukopisu k 11. 10. 2026

| Ukazatel | Publikovaný stav |
|---|---:|
| Skeny celkem | 677 |
| Foliované snímky 1r–335v | 670 |
| Desky, přídeští, předsádky a hřbet | 7 |
| Strany s oběma hlavními HTR kandidáty a interpretací | 664 |
| Foliované strany bez hlavního textu ve vybraných oblastech | 6 |
| Segmenty ve veřejném UI | 50 297 |
| Segmenty před dvěma spojeními na 20v | 50 299 |
| Latinské rekonstrukce a české překlady po pasážích | 5 634 |
| Odborně revidovaná reference pro měření přesnosti | 0 |

Hlavní HTR tvoří CATMuS medieval 1.6.0 / Kraken a ENC-PSL/Medusa0.2Line-4B. Další checkpointy jsou pilotní experimenty, nikoli přepisy celého rukopisu. Rozpoznávání proběhlo lokálně, interpretace pomocí asistenta v chatu. Lokální tokeny Medusy nejsou tokeny Codexu. Historická pozorování spotřeby neumožňují zpětně odvodit přesnou izolovanou cenu celého projektu.

Všechny interpretace jsou návrhy bez nezávislé odborné kontroly, CER/WER nejsou stanoveny. Úplnost se týká hlavního textu ve vybraných oblastech; ne všech marginálií. Sedm snímků vazby má status not_transcribed. AI shrnutí a pracovní struktura rovněž nejsou katalogizací nebo odborně prokázanými hranicemi děl.

Veřejné rozhraní obsahuje řádkovou analýzu, souběžné HTR kandidáty, rekonstrukce, překlady, stahování textových vrstev, strukturu celého rukopisu, změnu šířky a skrytí panelů a návrhy oprav HTR i segmentace. Motto: „Rukopisy, snímek po snímku.“ Doprovodný text: „Přepis s pomocí AI. Opravy od uživatelů.“

Návrhy změn se exportují jako JSON nebo otevřou předvyplněný GitHub issue. Neodesílají se automaticky a nemění původní text, geometrii, obrazové výřezy ani exporty. Segmentační editor podporuje obdélníkové oblasti v souřadnicích originálu: změnu, rozdělení, spojení, přidání a odstranění. Editor může přijmout změnu a teprve následně řízeně přegenerovat odvozené vrstvy; tento schvalovací proces není automatizován.

TEI P5 4.12.0 obsahuje instituci a signaturu. Celorukopisový TEI je **popis a facsimilní index 677 snímků s odkazy na stranové TEI**, nikoli jeden sloučený kompletní přepis. ProArc větev produkuje TXT a ALTO 3.0; samostatná OCR dvojice není celý NDK PSP balíček.

Zdrojem počtů je publikovaný manifest, stranové JSON a veřejné kontroly v docs/validation. Historické měření po 430 skenech je zachováno v [záznamu k 10. 10.](research-snapshot-2026-10-10.json); není aktuálním výsledkem celého rukopisu. Nová kontrola repozitáře ověřuje shodu publikovaných souborů, referenční vazby, geometrii, pokrytí pasáží a úplný index TEI. Starší záznamy obrazové kontroly nejsou v této aktualizaci znovu prováděnou paleografickou revizí.
