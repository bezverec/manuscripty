# Ověřený stav pilotu k 10. 10. 2026

Jde o souhrn lokálních dokončených výstupů, které se ukládají mimo tento repozitář. Zdrojové kontrolní součty souhrnů jsou v research-snapshot.json. Přesnost přepisu nebyla vyhodnocena proti odborné referenci.

| Ukazatel | Stav |
|---|---:|
| Unikátní zpracované skeny | 430 |
| Segmenty hlavních textových oblastí | 31 528 |
| Strany s návrhem latiny a češtiny | 427 |
| Záznamy bez hlavního textu ve vybraných oblastech | 3 |
| Poslední dávka | 100 skenů, 184r–235r |
| Segmenty poslední dávky | 7 626 |
| Návrhové pasáže poslední dávky | 818 |
| Skutečně otevřené nativní obrazové pruhy této dávky | 1 228 |
| Kontrolované předchozí artefakty, SHA-256 beze změny | 7 331 |
| Kontrolované odkazy finálního přehledu | 983 |

Sedm HTR etap: pilot-ten-pages (10), pilot-next-ten-pages (10), pilot-third-ten-pages (10), htr-next-100-pages (100), htr-second-100-pages (100), htr-third-100-pages (100), htr-fourth-100-pages (100). Poslední dávka vynechává již dříve zpracovaná folia 200r, 210v a 225r. Prázdné hlavní oblasti jsou u 97v, 108r a 108v. Záznamy takových stran nejsou chybějící rekonstrukce.

V poslední dávce jsou auditovány náhradní postupy polygonizace na sedmi stranách: 206v, 207r, 208r, 219r, 221r, 233r a 234v. Medusa dosáhla limitu bez EOS u segmentů f195r_l004, f199v_l036 a f203r_l026. U deseti slov OCR používá označenou řádkovou obálku místo slovní geometrie. Poškozený nativní PNG vstup 215r byl znovu vytvořen a ověřen před čtením. Tyto případy omezují interpretaci technicky úspěšného průchodu.

## Spotřeba poslední stovky

| Operace | Zaznamenaná hodnota |
|---|---:|
| CATMuS segmentace CPU | 4 394,888 s |
| Bezztrátové výřezy | 1 122,007 s |
| CATMuS rozpoznávání CPU | 1 390,086 s |
| Medusa uložený GPU čas všech relací | 3 963,068 s |
| CTC zarovnání a OCR export CPU | 1 600,503 s |
| Lokální Medusa vstupní tokeny | 2 317 908 |
| Lokální Medusa výstupní tokeny | 174 677 |
| Placená modelová API | 0 volání |
| Sdílený týdenní limit účtu při zahájení a na konci | 83 % → 94 % |

Časy různých větví se překrývají. Zachované checkpointy se započítávají jednou; neuložený výpočet při přerušení není změřen. Rozdíl 11 procentních bodů sdíleného účtového okna je orientační pozorování, ne přesný tokenový účet této dávky. Lokální tokeny Medusy nejsou tokeny Codexu. Příkon, cena elektřiny, lidská práce a izolovaná peněžní cena použití předplatného nebyly měřeny. Přímé API výdaje 0 proto nejsou celkové ekonomické náklady projektu.

Technické dokončení zahrnuje oba HTR kandidáty, navrženou latinu a češtinu, TEI Relax NG, ProArc OCR XSD a ZIP, čtení exportů zpět, odkazy a uchování starších výsledků. Všechny interpretace stále mají status proposed, human_reviewed false, expert_reference false, CER/ WER null.
