# Současná architektura

Systém je lokální dávkový výzkumný postup: souborové manifesty a Python skripty propojují Docker inference, obrazové čtení asistenta a offline publikační exporty. Nemá centrální databázi; publikační větev je statický veřejný web v Cloudflare Pages s obrazovými deriváty v R2 a Pages. Aktuální stav k 11. 10. 2026 je popsán v research-status.md; dávkové příklady níže zůstávají konkrétním snapshotem čtvrté stovky.

~~~mermaid
flowchart TD
  A[Archivní TIFF + SHA-256] --> B[Výběr frame 0 a hlavních textových oblastí]
  B --> C[RGB pracovní obraz v původních souřadnicích]
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

Archivní TIFF jsou v EX/. Jejich SHA-256, rozměry, zvolený frame a geometrie oblastí vstupují do manifestu. Poslední dávka používá frame 0, RGB, 4500 × 5900 pixelů. prepare_pages.py zachovává rozlišení a pixely uvnitř zvolených oblastí, okolí v pracovním obrazu vyplní bíle. Změna pracovní vrstvy se nedotýká archivního TIFF.

Výběr oblastí vzniká po skutečném otevření přehledových obrazů. Automaticky zapsaný příznak v přípravném skriptu sám není důkazem této kontroly; součástí datového auditu jsou záznamy skutečného čtení. Hlavní textové zóny nemusí zahrnovat všechny marginálie.

## 2. Dvě lokální HTR větve

Kraken 7.1.1 s modelem CATMuS medieval 1.6.0 poskytuje segmentaci a rozpoznání na CPU. Dva pevné shardy po 50 stranách používají čtyři CPU vlákna každý. Polygony, baselines, pořadí a ID segmentů se zachovávají v původních obrazových souřadnicích. Opravy geometrie a náhradní postup polygonizace mají explicitní auditní záznam a vyžadují obrazovou kontrolu.

ENC-PSL/Medusa0.2Line-4B používá GPU a stejné bezztrátové řádkové výřezy s vlastní interní předúpravou. Shodný vstupní výřez tedy neznamená shodný tensor obou modelů. Medusa dostává nezávislý prompt pro každý řádek, bez předchozí transkripce, s vypnutým thinking a sampling. Výstup se ukládá bez strip a Unicode normalizace. Chybějící EOS při dosažení limitu se označuje jako možné zkrácení.

Řádkové checkpointy Medusy a stranové checkpointy CATMuS umožňují pokračovat po přerušení. Obnovení kontroluje kontrolní součty vstupů a modelů; uložený výsledek se nemá přičítat k časům či tokenům podruhé. Scheduling čerpá z rozdělení folii mezi čtenáře, konečná prezentace zůstává v pořadí rukopisu.

## 3. Rekonstrukce a překlad

native_inputs.py a prepare_tiles.py připravují pruhy v nativním rozlišení s překryvem a známými souřadnicemi. Příprava obrázku neznamená jeho otevření. Asistent v chatu skutečně čte obraz, porovnává HTR kandidáty a zapisuje oddělené interpretace s vazbou na segmenty a otevřené obrazy. Při povoleném souběžném zpracování dostávají asistenti disjunktní folia; sjednocení a validace probíhají nad jedním manifestem.

Interpretace není automatická volba lepšího HTR řádku. Doplnění, rozvedení zkratek, nejisté čtení a překlad musí zůstat rozlišitelné od surového rozpoznání. Současné exportery pouze zpracují již vytvořené návrhy; žádný přibalený skript sám nevolá frontier API ani negeneruje český překlad.

## 4. Exporty a souhrn

export_interpretation.py vytváří TEI P5 4.12.0, JSON, TXT a HTML s odkazy na obrazy. Místní RNG schéma se kontroluje offline. build_final_report.py spojuje výsledky sedmi HTR etap, obnovuje pilot-index.html a souhrnné TXT, dokládá nezměněnost předchozích výsledků. Pracuje proto i s daty starších etap mimo tento zdrojový snapshot.

ProArc větev používá CATMuS CTC zarovnání. Surový řádkový text musí odpovídat uloženému rozpoznání. Souřadnice slov pocházejí z měřených CTC pozic a geometrie; případný řádkový fallback je výslovně označen. TXT/ALTO obsahuje surové OCR, rekonstrukce a český překlad jsou samostatné vrstvy. Export není kompletní NDK PSP balíček a úspěšná XSD kontrola není ověřený import do živého ProArcu.

## Provozní hranice

Soubory jsou zdrojem pravdy pro checkpointy, provenienci a přezkoumání. Docker odděluje CPU Kraken a CUDA Medusu; hostitelský Python připravuje obrazy a exporty. Offline HTML umožňuje přezkoumat kandidáty a návrhy. Veřejný web a WebP/R2 jsou nasazené; frontend a textový korpus jsou v web/public, provoz v presentation.md a web/README.md.
