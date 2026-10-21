# Současná architektura

Systém je lokální dávkový výzkumný postup: souborové manifesty a Python skripty propojují Docker inference, obrazové čtení asistenta a offline publikační exporty. Nemá centrální databázi; publikační větev je statický web v Cloudflare Pages s obrazy v R2 a Pages. K 21. 10. 2026 zahrnuje tři rukopisy a 1 245 snímků; [aktuální stav](research-status.md). Přibalené skripty čtvrté stovky jsou historický příklad M II 220, nikoli jednotný orchestrátor dnešní knihovny.

~~~mermaid
flowchart TD
  A[Archivní TIFF + SHA-256] --> B[Evidovaný frame, orientace a případná hlavní zóna]
  B --> C[RGB pracovní obraz + souřadnicový pramen]
  C --> D[Kraken blla: řádky, baselines a polygony]
  D --> E[Bezztrátové řádkové výřezy]
  D --> F[CATMuS: surové HTR na CPU]
  E --> G[Medusa 4B: surové HTR na GPU]
  F --> H[Porovnání podle segment ID]
  G --> H
  C --> I[Nativní obrazové pruhy pro čtení]
  H --> J[Asistent: návrh latinské rekonstrukce a češtiny]
  I --> J
  J --> K[JSON proposed + nejistoty + obrazová provenience]
  K --> L[TEI 4.12.0 + TXT + HTML review]
  F --> M[CTC zarovnání + TXT + ALTO 3.0]
  M --> N[XSD a kontrolovaný ZIP pro ProArc]
  L --> O[Offline prohlížeč pilotu]
  H --> O
  L --> P[Statický web Cloudflare Pages]
  H --> P
  A --> Q[WebP deriváty: R2 a Pages]
  P --> Q
  P --> S[Návrhy oprav JSON / GitHub issue]
~~~

## 1. Archivní a pracovní obrazy

Archivní TIFF jsou v EX/. SHA-256, rozměry, frame, orientace a případné oblasti vstupují do manifestu. Historická dávka M II 220 používá frame 0, RGB, 4500 × 5900 pixelů a bílé okolí hlavních oblastí. M I 259 má zpravidla 3900 × 5600 pixelů, u dvou dodatečných záběrů frame 1 a u čtyř vazebních snímků bezztrátové otočení. Nových 361 stran má úplný nemaskovaný modelový vstup; deset převzatých pilotů zachovává maskování. [Výjimky a transformace](mi259-processing.md). Archivní TIFF se nemění.

Výběr oblastí vzniká po skutečném otevření přehledových obrazů. Automaticky zapsaný příznak v přípravném skriptu sám není důkazem této kontroly; součástí datového auditu jsou záznamy skutečného čtení. Hlavní textové zóny nemusí zahrnovat všechny marginálie.

## 2. Dvě lokální HTR větve

Kraken 7.1.1 s modelem CATMuS medieval 1.6.0 poskytuje segmentaci a rozpoznání na CPU. Shardy jsou vlastností konkrétní dávky; čtvrtá stovka používá dva shardy po 50 stranách se čtyřmi vlákny. Polygony, baselines, pořadí a ID zůstávají v evidovaném pracovním souřadnicovém systému. Opravy geometrie a náhradní polygonizace mají vlastní audit a vyžadují obrazovou kontrolu.

ENC-PSL/Medusa0.2Line-4B používá GPU a obdélníkové bezztrátové výřezy přiřazené ke stejné segmentové geometrii. CATMuS používá polygon/baseline, Medusa vlastní předúpravu; shoda segmentu neznamená totožné vstupní pixely/tensory obou větví. Medusa má nezávislý prompt bez přepisu druhého enginu a deterministické generování. Požadavek `enable_thinking=False` se ověřuje ve skutečně vykreslené šabloně. Raw Unicode se nenormalizuje. Chybějící EOS při dosažení limitu zůstává označený; změna dekódování má samostatnou provenienci.

Řádkové checkpointy Medusy a stranové checkpointy CATMuS umožňují pokračovat po přerušení. Obnovení kontroluje kontrolní součty vstupů a modelů; uložený výsledek se nemá přičítat k časům či tokenům podruhé. Scheduling čerpá z rozdělení folii mezi čtenáře, konečná prezentace zůstává v pořadí rukopisu.

## 3. Rekonstrukce a překlad

native_inputs.py a prepare_tiles.py připravují pruhy v nativním rozlišení s překryvem a známými souřadnicemi. Příprava obrázku neznamená jeho otevření. Asistent v chatu skutečně čte obraz, porovnává HTR kandidáty a zapisuje oddělené interpretace s vazbou na segmenty a otevřené obrazy. Při povoleném souběžném zpracování dostávají asistenti disjunktní folia; sjednocení a validace probíhají nad jedním manifestem.

Interpretace není automatická volba lepšího HTR řádku. Doplnění, rozvedení zkratek, nejisté čtení a překlad musí zůstat rozlišitelné od surového rozpoznání. Současné exportery pouze zpracují již vytvořené návrhy; žádný přibalený skript sám nevolá frontier API ani negeneruje český překlad.

## 4. Exporty a souhrn

export_interpretation.py vytváří TEI P5 4.12.0, JSON, TXT a HTML s odkazy na obrazy. Místní RNG schéma se kontroluje offline. build_final_report.py spojuje výsledky sedmi HTR etap, obnovuje pilot-index.html a souhrnné TXT, dokládá nezměněnost předchozích výsledků. Pracuje proto i s daty starších etap mimo tento zdrojový snapshot.

ProArc větev používá CATMuS CTC zarovnání. Surový řádkový text musí odpovídat uloženému rozpoznání. Souřadnice slov pocházejí z měřených CTC pozic a geometrie; případný řádkový fallback je výslovně označen. TXT/ALTO obsahuje surové OCR, rekonstrukce a český překlad jsou samostatné vrstvy. Export není kompletní NDK PSP balíček a úspěšná XSD kontrola není ověřený import do živého ProArcu.

## Provozní hranice

Publikační adaptéry jsou oddělené podle rukopisu: původní generátory M II 220,
`web/publication/build_web.py` pro M II 153 a `build_mi259.py` pro M I 259.
Společný registr řídí statická folia a Pagefind. M I 259 má zvlášť identifikovaný
nemaskovaný souřadnicový obraz a transformační matici; návrhy v2 jej nezaměňují
s archivním TIFFem. První dva dokumenty zachovávají v1. [Datové kontrakty](data-contracts.md).

CTC slovní zarovnání popsané výše se týká původní ProArc větve M II 220;
stránkové ALTO M I 259 používá doloženou řádkovou geometrii, bez vymyšlených
slovních obdélníků. [Přenosné publikační kroky](../web/publication/README.md).

Soubory jsou zdrojem pravdy pro checkpointy, provenienci a přezkoumání. Docker odděluje CPU Kraken a CUDA Medusu; hostitelský Python připravuje obrazy a exporty. Offline HTML umožňuje přezkoumat kandidáty a návrhy. Veřejný web a WebP/R2 jsou nasazené; frontend a textový korpus jsou v web/public, provoz v presentation.md a web/README.md.
