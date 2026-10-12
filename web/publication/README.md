# Přenositelné sestavení M II153

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
