# Přenositelné sestavení M II153

`digitization_support.py --public-root /site/public` přidá malé označení
„Zdigitalizováno ve VISK 6“ a původní logo Ministerstva kultury k oběma
přehledům a do části Popis společného prohlížeče.
V přehledech se označení opakuje také na začátku sekce `#ai-shrnuti`, aby
bylo vidět při otevření přímého odkazu na shrnutí.
Zdrojové SVG v `assets/` je připnuté SHA, kopíruje se beze změny a nevyžaduje síť při sestavení.
Generátory přehledů i společného prohlížeče zachovávají stejné označení.
Podpora se vztahuje k digitalizaci rukopisů; nejde o označení výkladů AI.

Popis M II 220 používá také `mii220-catalogue.json`: 57 hlavních položek a sedm
pododdílů opsaných z dodaného XML. Jeho zdrojový SHA se kontroluje proti metadatům
rukopisu. Samostatnou aktualizaci veřejných popisů lze provést příkazem
`python catalogue_records.py --public-root /site/public`; přidá katalogový obsah
M II 220 a odstraní oznámení o fixity z obou popisů.

`supplier_descriptions.py --public-root /site/public` doplní úplné dodané
popisy obou rukopisů: fyzické vlastnosti, historii, bibliografii i rozbalovací
podrobnosti všech děl. Archivní kopie v `source-metadata/` se kontrolují přes
SHA proti metadatům dokumentu. Veřejné původní XML zůstává bajtově stejné,
JSON uchovává celou hlavičku včetně všech atributů a původního textu.
Kontrola hlídá převzetí každého neprázdného textového uzlu popisu; neznámá
popisná pole musí dostat výslovné mapování. Výzkumné přepisy se nemění.
Původní XML je dodaný formát, nikoli nově vytvořený TEI P5 4.12.0 export.

`manuscript_overview.py --public-root /site/public` slučuje katalogový popis
a AI shrnutí do jediné kanonické stránky `/rukopisy/{id}`. Témata zůstávají
rozbalovací a odkazy na původní četbu zachované. Staré adresy shrnutí dostávají
HTTP 301 bez cílového fragmentu, takže zůstávají funkční také tematické kotvy.
AI syntéza a převzaté katalogové informace mají odlišné štítky; doplnění
podle `overview_context.json` neznamená novou obrazovou kontrolu. Skript mění
pouze dva souhrnné JSONy, nikoli řádkové přepisy, překlady nebo TEI. Volitelný
`--manifest` kontroluje jejich předchozí SHA a aktualizuje jen tyto dvě položky;
`--report` uchová audit. Obecnou kontrolu ostatních dat tento postup neobchází.
Po opakované aktualizaci dodaných popisů spusťte přehled znovu. Navazující
`build_summary.py` jej již volá po sestavení tematických dokladů M II 153.

`enrich_document_tei.py --public-root /site/public` převádí celý dodaný `msDesc`
také do hlavních TEI popisů. Používá připnuté Relax NG schéma P5 4.12.0;
kontroluje všechny textové části zdroje, lokální odkazy a neměnnost `text`
i `facsimile` přes C14N. Zachovává projektové identifikátory a dřívější ediční
poznámky. Argument `--manifest` smí zaznamenat pouze tyto dva ověřené zásahy
do hlaviček; předchozí SHA musí souhlasit. Obecná ochrana výzkumných souborů
zůstává v `update_source_manifest.py` beze změny. `--report` uloží podrobný audit.

Python3.10+ a lxml. Tento adresář neobsahuje rukopisné obrazy, výzkumné výsledky,
secrets ani síťové/deployment příkazy. Výstup je merge overlay stávajícího webu,
nikoli kompletní samostatný web. Výzkumné vstupy a stávající public strom se pouze čtou.

Všechny hlavní cesty jsou povinné a explicitní:

```text
python build_web.py --source /research/full-htr --base-public /site/public \
  --out /staging/new-overlay --rng /schemas/tei-p5-4.12.0/tei_all.rng \
  --supplier-metadata /metadata/supplier.xml --legacy-metadata /metadata/legacy-overlay \
  --report-dir /staging/reports --pilot-source /research/original-pilot --require-complete
```

Na Windows použijte vlastní absolutní cesty a běžné PowerShell pokračování příkazu.
`--pilot-source` je nutný pro dochované tři pilotní interpretace; jejich původní
četba a překlad se kontrolují proti výslovně vybranému původnímu pilotu.
Žádná implicitní cesta ke workspace se nehledá. `source/document.json` je součást
kontraktu explicitně vybraných dat; supplier XML a legacy overlay jsou samostatné vstupy.
Relax NG může potřebovat své lokální include soubory; předejte úplný balík P5 4.12.0.

Výstup musí být nový nebo prázdný adresář. Nesmí překrývat source, base-public,
pilot-source ani legacy-metadata, nesmí obsahovat vstupní XML/schema. Totéž platí
pro report-dir. Skripty nic nemažou. Po přerušeném běhu zvolte nový výstup nebo
předchozí staging ručně zkontrolujte. Při změně očekávaných frontend kotev se build zastaví.

`--require-complete` vyžaduje197skenů, aktuální SHAprovenance, autorskou četbu,
pokrytí všech zdrojových IDs, oba původní HTR, shodnou geometrii, původní pilotní
rozhodnutí a TEIvalidované proti dodanému RNG. `publication_ready` může být true
jen po tomto úplném auditu. Bez přepínače je výstup pouze částečný náhled.
Reporty ukládá výhradně report-dir. To neověřuje paleografickou správnost, licenci,
živé HTTPobrazů, XPath2Schematron ani renderování v prohlížeči.

M II153 má samostatný namespace `/data/vkol-m-ii-153/` a média ve `v2`.
M II220 má nadále původní IDs a v1. Textová část jeho TEI se kontroluje C14N,
677položek a počty se zachovávají. Dodané lokální exporty se kopírují po bytech;
webové TEI přesměrují facsimile URI na prohlížeč a tuto odlišnost vysvětlují.
Souhrnný TEI má explicitně version4.12.0 a xml-modelPI s veřejnou schemaURI.
Jazyky interpretačních pasáží se odvozují ze skutečných canonical lines;
německé doplňky96v nejsou označeny jako latinské. Nečitelné fragmenty mají und,
smíšené jednotky mul. IDvazby se nemění, fallback názvy desek/přídeští jsou české.

Frontend kopie obsahuje stejné schválené změny jako místní builder, včetně vypnuté
IIIFfeatureflag. AIshrnutí, statické folio stránky a vyhledávací indexy sestavuje
navazující pipeline odděleně; tento overlay je sám nevytváří. Build nic nepublikuje.

Spustit lokální testy:

```text
python -m unittest discover -s . -p test_portable.py -v
```
