# Přenosné kontroly webového overlay

Oba skripty vyžadují explicitní `--source`, `--base-public`, `--staged`,
`--build-report` a `--report-dir`. Čtou výzkumné vstupy, stávající web a nový
overlay; píší pouze JSON zprávu do report-dir. Nepublikují, nekopírují obrazy,
nevyžadují přístupové údaje a nekontaktují obrazový server.

Po úplném builderu doplňte navazující souhrn a statické folio stránky podle
zvolené pipeline. Audit řeší odkazy ve vrstveném stromu: nový soubor má přednost,
nezměněné sdílené soubory se hledají v base-public.

```text
python audit_web.py --source /research/full-htr --base-public /site/public \
  --staged /staging/new-overlay --build-report /staging/reports/build-report.json \
  --report-dir /staging/reports
node test_frontend.mjs --source /research/full-htr --base-public /site/public \
  --staged /staging/new-overlay --build-report /staging/reports/build-report.json \
  --report-dir /staging/reports
```

Na Windows nahraďte cesty vlastními absolutními cestami a použijte syntax
pokračování příkazu pro PowerShell, nebo příkazy zapište na jeden řádek.

`audit-report.json` ověřuje obě původní HTR a bbox pro každý segment, přesné
zdrojové ID a pokrytí rekonstrukce/češtiny, zdrojovou SHA identifikaci snímků,
jmenné prostory náhledů/dlaždic/výřezů, dostupné downloads a byte SHA původních
exportů. Úplný publikovatelný M II 153 má 197 snímků a 15013 segmentů. U textové
strany musí být všech 14 deklarovaných downloadů. Kontrola nepozměněných 677
snímků M II 220 zahrnuje manifest, počty, textovou část TEI a zákaz přepsání
původních podkladových data/TXT/ALTO/TEI souborů v overlay. Zpráva zaznamenává
souhrnnou SHA inventury těchto podkladů a ověřuje SHA baseline souborů uvedených
builderem. Neřeší obsahovou správnost nových katalogových údajů.

Kontrola souborů odmítne rastrová média, váhy modelů, soubory klíčů a `.env`,
soubor větší než limit Pages a známé formáty přístupových klíčů v textových
souborech. Při nálezu uvádí cestu, ne nalezený tajný obsah. Tato kontrola
vybraných signatur nenahrazuje audit celého Git historie nástrojem gitleaks.

`frontend-test-report.json` testuje v Node VM routování a manifest loader,
uzavřený výběr dokumentu, zpětnou kompatibilitu, identifikaci a Unicode návrhů
HTR/segmentace, zachování původní geometrie, jazyky interpretačních pasáží,
odkazy katalogu a přítomnost ovládacích prvků. Není testem renderování,
obrazové dostupnosti, klávesnicové přístupnosti ani paleografické správnosti.

Osm malých syntetických testů ověřuje i chybové případy auditu:

```text
python -m unittest test_audit_web -v
```

Mění jednotlivé původní HTR, bbox, coverage, download a baseline, zkouší chybný
namespace/cestu, podkladová legacy data, chybějící odkaz a zakázaný soubor nebo
syntetickou signaturu klíče. Testy používají dočasné vlastní soubory, nikoli skeny.
