# Web Manuscripty

Dokumentace k 21. 10. 2026. Základní korpus z 19. 10. obsahuje **tři
rukopisy, 1 245 snímků**; 21. 10. přibyly samostatné četby a obrazové anotace
M I 259. [Produkce](https://rukopisy.digitalizaty.cz) běží
v Cloudflare Pages projektu `rukopisy-digitalizaty`; obrazy jsou v R2 a u vazby
M II 220 také v Pages. Aktuální výsledky a omezení: [stav výzkumu](../docs/research-status.md).

## Spuštění a ověření kopie

Potřebujete Python s lxml/Pillow a Node.js/npm. Z kořene repozitáře:

```sh
python -m pip install -r requirements-reference.txt
python web/validate_snapshot.py
python -m unittest discover -s medieval-manuscript-transcription/tests -v
cd web
npm ci
npm test
npm run test:overview
npm run test:theme
npm run test:publication
npm run build:pages
npm run test:search
```

`npm test` ověřuje návrhy oprav, souřadnice v1/v2, načítání dokumentů, statická
folia a odkazy všech tří rukopisů, workflow, návrh IIIF, adaptér M I 259
a dvě dodatečné četby (`test:readings`).
Samostatné testy přehledů a motivu ověřují jejich prezentační kontrakty.
Testy neprovádějí inference, překlad ani odbornou revizi.
`validate_snapshot.py` kontroluje chráněné hashe, JSON/XML, geometrii,
pokrytí interpretací a TEI indexy; neopakuje veškeré původní obrazové kontroly.

Lokální statický server z kořene:

```sh
python -m http.server 8000 --directory web/public
```

Otevřete `http://localhost:8000/`. Prostý server neumí čisté URL přepisy Pages;
lokálně používejte například `/rukopisy/vkol-m-i-259.html`,
`/rukopisy/vkol-m-i-259/119v.html` a `/rukopis.html?doc=vkol-m-i-259#119v`.
`file://` není vhodné kvůli fetch. Obrazy z R2 vyžadují síť; samotný clone
není úplná offline obrazová kopie.

## Média a ruční nasazení

Před každým Pages nasazením obnovte ignorovaný `public/binding-media/`
pro sedm snímků vazby M II 220:

```sh
cd web
npm run media:restore -- --check
npm run media:restore
npm run media:check
```

Obnova kontroluje 1 175 veřejných WebP (45 188 048 bajtů) přes SHA-256 a
velikost, bez klíče. M II 153 a M I 259 mají i vazbu v R2. Pokud veřejný zdroj
není dostupný, je nutné obnovit deriváty z archivních TIFF v pracovním prostoru.

Po kontrolách a přípravě nové verze:

```sh
npx wrangler login
npm run deploy
```

Deploy kontroluje vazební média, sestaví folia a hledání a nahraje `public/`
do existujícího projektu. GitHub sám Pages nenasazuje. Přihlášení, OAuth cache
a tokeny jsou místní; tyto příkazy nevytvářejí DNS ani bucket. Upload R2 je
samostatná správa úložiště s auditovaným prefixem a oprávněním.

`node verify_publication.mjs --plan` bez sítě vypíše soubory všech tří
dokumentů a přesměrování. `node verify_publication.mjs` je síťová kontrola
všech stránkových JSON a vybraných sdílených textů; přesměrování ověřuje zvlášť.
`npm run test:publication` kontroluje tento plán a chybové odpovědi synteticky.
`verify_public.mjs` zachovává starší podrobnou kontrolu M II 220 a vzorků
jeho obrazů. Nejde o úplnou kontrolu všech dnešních obrazových objektů.
Datované browserové/HTTP audity jsou v `docs/validation`.

## Folia a vyhledávání

`manuscripts.json` registruje M II 220 (677), M II 153 (197) a M I 259 (371).
Každý záznam má `id`, cestu manifestu v public a `default_model`.
`npm run build:pages` vytváří všech 1 245 statických folií, sitemap a ignorovaný
index `public/pagefind/`. Index se necommituje; sestavuje se při nasazení.
`npm run test:search` spouští skutečné Pagefind API/WASM nad místními soubory.

Folio má adresu `/rukopisy/{document_id}/{folio}`, řádek fragment například
`#f119v_l028`. Shodná jména folií různých dokumentů odděluje jmenný prostor.
Staré adresy shrnutí zachovává `_redirects` i malé HTML fallbacky pro prostý server.

Statické folio zobrazuje nezměněný přepis výchozího modelu z registru;
oba kandidáti jsou v dynamickém prohlížeči a downloadech. Nové `reading_addenda`
se uvádějí odděleně od starších interpretací. Poznámky k fragmentům a smíšeným
boxům jsou v řádkové analýze a u statického přepisu, s datem a stavem návrhu AI.
Jejich text se díky `data-pagefind-ignore` neindexuje jako rukopisný přepis.
[Datové vrstvy a klasifikace](../docs/data-contracts.md).

Nové návrhy M I 259 používají schéma v2 s identitou celého orientovaného PNG
a transformací do archivního TIFFu. Dva původní dokumenty zachovávají v1.
[Kontrakty a redakční postup](../docs/data-contracts.md).

## Publikační pipeline a chráněná data

[publication/README.md](publication/README.md) rozlišuje adaptéry M II 153,
M I 259 a sdílené generátory popisu, TEI, motivu a loga. Import výzkumných dat
není běžný frontend build. Vstupy, staging a reporty mají explicitní cesty.

`update_source_manifest.py` obnovuje inventář frontendu, ale odmítá změny
existujících výzkumných souborů. Plošný přepočet hashů nesmí tuto ochranu obejít.
Přijatá oprava potřebuje předchozí stav, provenienci a odpovídající nové exporty.
[Údržba a zachování artefaktů](../docs/maintenance.md).

Nové exporty se vytvářejí pouze pro skutečně dotčené vrstvy. Obrazové poznámky
nemění původní TXT/ALTO/TEI; dodatečné četby mají samostatné downloady.
`publish_reading_addenda.py` a `publish_neighbor_fragments.py` jsou jednorázové
importéry nad pevně určeným předchozím stavem. Nespouštějí se při běžném deploy
ani jako obecný krok obnovy. Základní `build_mi259.py` sám tyto pozdější vrstvy
nezachová; nový overlay nesmí jejich současná pole a downloady přepsat.
[Rozlišení builderů a importérů](publication/README.md).

`build_data.py`, `build_binding.py`, `build_document_identity.py` a
`build_extras.mjs` jsou původní generátory M II 220 závislé na obnoveném
pracovním prostoru. Nejsou univerzálním buildem tří rukopisů pro běžný clone.

## IIIF: neaktivní experiment

`npm run build:iiif` vytváří návrh Presentation API 3 pro M II 220 se 677
canvasy. `feature-config.js` ponechává `iiifManifest: false`; obrazové služby
manifestu nejsou publikované. `build_media.py --iiif` má syntetické testy,
nebyl proveden plošný TIFF build/upload IIIF. Před zapnutím chybí potvrzení práv,
obrazové objekty a jejich ověření včetně CORS. Statické adresy folií a vyhledávání
jsou již dokončené; starý požadavek na dokončení jejich fáze není aktuální TODO.
