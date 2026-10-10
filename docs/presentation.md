# Návrh budoucí prezentace

Aktuální prezentace je offline HTML s odkazy na místní TIFF deriváty, řádkové výřezy a nativní čtecí pruhy. GitHub zde uchovává architekturu a zdroje. Veřejný web, R2 bucket ani DNS nebyly v rámci pilotu nasazeny.

Navržený web může spojit statické HTML, JSON, TXT a TEI na webovém hostingu s předem vytvořenými WebP pyramidami a výřezy na Cloudflare R2. Uvažované adresy jsou rukopisy.digitalizaty.cz pro web a rukopisy-data.digitalizaty.cz pro obrazy. Doménu, DNS, CORS, cache a oprávnění k veřejnému zpřístupnění je nutné řešit při skutečném nasazení.

~~~mermaid
flowchart LR
  A[Lokální archiv TIFF] --> B[Lokální WebP encoding]
  B --> C[R2: verzované dlaždice a výřezy]
  D[HTR + interpretace + metadata] --> E[Statický web]
  E --> C
~~~

Lokální studie měřila tři celé obrazy a 150 řádkových výřezů z 30 stran. Pro celý inventář 677 snímků, z toho 670 číslovaných stran, odhadla WebP Q90 dlaždice na 5,87 GB a řádkové výřezy na 4,29 GB, celkem 10,16 GB bez rezervy. Pro plánování byla navržena kapacita 12–15 GB. Q80 vycházelo celkem na 6,05 GB. Zhruba 161 tisíc obrazových objektů je extrapolace, nikoli vytvořený a nahraný korpus.

Jde o záměrný vzorek a historický odhad k 10. 10. 2026. Nezahrnuje archivní TIFF, samostatné plné WebP ke stažení ani automaticky všechny marginálie. CATMuS a Medusa sdílejí řádkové výřezy, které se nezapočítávají dvakrát. Při posouzení úložiště je potřeba zvlášť započítat pruhy pro nativní čtení, pokud se mají také zveřejnit.

Výpočty vznikají ve skriptech measure_webp.py a measure_crops.py. Ty mají vazby na lokální původní inventář a pilotní adresáře. Před rozhodnutím o nasazení je vhodné měření rozšířit na větší vzorek a znovu ověřit aktuální podmínky [Cloudflare R2](https://developers.cloudflare.com/r2/pricing/) a [GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits). Tento snapshot automaticky nevytváří veřejný bucket ani GitHub Pages.
