# Publikovaná webová verze

Snapshot 11. 10. 2026, revize 20261011-7, [produkce](https://rukopisy.digitalizaty.cz). public/ obsahuje statický frontend a veřejné textové exporty, zkopírované byte-for-byte. Obrazy jsou v samostatném úložišti; jejich kontrolní součty nejsou obrazové soubory.

## Lokální prohlížení

Z kořene repozitáře:

~~~sh
python -m http.server 8000 --directory web/public
~~~

Otevřete http://localhost:8000/ a http://localhost:8000/rukopis.html. Python server neprovádí Cloudflare přepis čistých URL; detail dokumentu lokálně otevřete jako /rukopisy/vkol-m-ii-220.html. JavaScript používá fetch, proto soubory neotvírejte přímo přes file://. Folia a řádkové výřezy vyžadují dostupnost veřejné R2 domény; bez sítě je nutná samostatná místní kopie obrazových derivátů a úprava jejich URL.

Sedm snímků vazby používá public/binding-media/, které Git neobsahuje. Před nasazením je obnovte z existujícího veřejného webu podle manifestu:

~~~sh
cd web
npm run media:restore -- --check
npm run media:restore
npm run media:check
npm test
~~~

První příkaz pouze ověří manifest bez stahování. Obnova přenese 1 175 veřejných WebP objektů (45 188 048 bajtů), ověří velikost i SHA-256 a uloží je pouze do ignorovaného public/binding-media/. Nepotřebuje žádný klíč. media:check nic nestahuje a vyžaduje všechna média. Pokud veřejný zdroj nebude dostupný, vytvořte deriváty z archivních TIFF pomocí build_binding.py v obnoveném pracovním prostoru.

## Kontroly a nasazení

~~~sh
# Z kořene repozitáře:
python web/validate_snapshot.py
python -m unittest discover -s medieval-manuscript-transcription/tests -v
# Z web/:
npm test
# Volitelně síťová kontrola existující produkce:
node verify_public.mjs
npm install
npm run media:check
npx wrangler login
npm run deploy
~~~

Wrangler je pevně uvedený v package-lock.json. Deploy ověřuje obrazové snímky vazby a nahrává public/ do existujícího projektu rukopisy-digitalizaty. Nasazení vyžaduje vlastní přihlášení a oprávnění; tokeny ani OAuth cache nejsou v Git. Cloudflare DNS/R2 jsou existující služby, nevytvářejí se těmito příkazy. Není nastavené automatické nasazování z GitHubu.

Při Python validaci se kontrolují kopírované SHA-256, JSON/XML syntaxe, referenční vazby, rozměry a geometrie, dostupnost obou HTR kandidátů a pokrytí interpretacemi; úplný TEI index prochází offline Relax NG. Jde o kontrolu datového snapshotu, nikoli novou odbornou revizi nebo opakovanou celkovou validaci všech původních edic. npm test spouští 11 HTR a 12 segmentačních kontrol. Původní browserové a veřejné HTTP kontroly jsou v ../docs/validation.

## Regenerace z výzkumných vstupů

Buildery vyžadují původní pracovní prostor: archiv EX/, všechna HTR porovnání, reconstruction.json, dokončovací manifest a vzorky. Nastavte MANUSCRIPT_WORKSPACE na jeho kořen. Následující kroky vytvářejí nové lokální deriváty a mění public/; jsou určeny pro přípravu nové verze, ne pro ověření kopie:

~~~sh
python build_data.py
python build_binding.py
node build_extras.mjs
python build_document_identity.py
~~~

build_data.py vytvoří media-jobs.json; build_media.py pak lokálně vytváří folia v r2-media/ (ignorováno). Obnova uvedená výše řeší pouze sedm snímků vazby, ne 158 837 objektů v R2. Přenos folií do R2 je samostatná autorizovaná správa úložiště a není součástí tohoto zdrojového snapshotu. Po regeneraci je potřeba obnovit manifest SHA-256 pro novou verzi; původní kopie je v docs/web-source-manifest.json.

Návrhy oprav se pouze exportují nebo předvyplňují GitHub issue. Přijetí a přegenerování HTR, TEI a OCR je samostatný redakční krok. Segmentační editor podporuje obdélníky, ne polygony nebo baselines.

Při přípravě repozitáře byl ověřen manifest a místní kopie všech 1 175 obrazových souborů vazby. Samotná hromadná obnova HTTP v tomto kroku nebyla znovu spouštěna. Síťová kontrola používá devět kontrolních R2 objektů a 14 objektů vazby; metadata vzorků jsou přibalená, obrazové soubory v Git nejsou.

## Statické stránky folií a vyhledávání (fáze 3)

Po `npm ci` spusťte `npm run build:pages`. Offline Node generátor vytvoří 677 stránek
`public/rukopisy/vkol-m-ii-220/<folio>.html` a sitemap; následně Pagefind 1.4.0
vytvoří ignorovaný `public/pagefind/` s vyhledávacím indexem. Verze Pagefind i
HTML validatoru jsou pevné v package.json a lockfile. Index necommitujte; nasazovací
skript jej vždy sestaví před nahráním. V této fázi nebylo nic nasazeno ani nahráno
na R2 a nebylo změněno DNS/Cloudflare.

Folia jsou čitelná bez JavaScriptu; zobrazují CATMuS, rekonstrukci a český překlad,
poznámky a odkazy na zdrojové řádky, předchozí/další snímek, prohlížeč, citaci a
podklady ke stažení. Snímky vazby uvádějí zatím nepřepsáno. Čistá adresa folia je
`/rukopisy/vkol-m-ii-220/20v`, řádková citace končí `#f20v_l001`. Původní stavové
odkazy prohlížeče zůstávají funkční. Lokálně použijte příponu `.html`; Python
HTTP server nepřesměruje čisté URL. Hledání je místní Pagefind/WASM, pole na úvodu
hledá ve všech zaregistrovaných rukopisech, pole na záznamu pouze v daném rukopisu.
Výsledky vedou na statická folia; JavaScript je nutný pouze pro hledání.

`manuscripts.json` je rozšiřitelný registr. Každý záznam má `id`, `manifest`
(relativní cesta uvnitř public, JS pilot-data nebo JSON manifest) a `default_model`.
Nový manifest musí mít shodné `document.id`, URI/reader a vlastní stránková data.
Tato fáze registruje pouze M II 220 a žádná nová katalogová metadata ani M II 153
nezveřejňuje. URI prohlížeče s parametrem doc generátor zachová.

Kontroly:

~~~sh
npm test
npm run test:search
# Z kořene:
python web/validate_snapshot.py
python -m unittest discover -s medieval-manuscript-transcription/tests -v
~~~

`npm test` vyžaduje vygenerované stránky přítomné ve snapshotu a validuje všech 677
pomocí html-validate 10.0.0 (doporučená pravidla), odkazy a identifikátory.
`npm run test:search` vyžaduje sestavený index a spouští skutečné Pagefind browser
API a WASM s místním fetch; slovo glosa z neupraveného CATMuS 20v musí najít 20v.
Snapshot validátor vynechává pouze generovaný public/pagefind při inventuře;
SHA všech 677 zdrojových stran, jejich TXT/JSON/TEI nadále kontroluje.
`docs/web-source-manifest.json` zahrnuje nové HTML, sitemap a změněné frontend
soubory; výzkumné texty, geometrie, ID a zdrojové SHA se nemění.

Otevřené otázky: TODO licence a práva; datace/katalogová identifikace nejsou
součástí této fáze. Vygenerované HTML má metadata pouze z existujícího snapshotu.

Volitelná obrazová kontrola: `node test-folio-browser.cjs` vyžaduje nainstalovaný Playwright (nebo `PLAYWRIGHT_MODULE` s cestou k balíčku) a místní Chrome. Ukládá ověřovací screenshoty do `docs/validation/phase3-screenshots/`; ověřuje šířky 1440 a 390 px, text bez JS a hledání v prohlížeči. Úzká gitignore výjimka dovoluje pouze tyto ověřovací screenshoty v PR; zdrojové skeny a jiná obrazová data zůstávají vyloučena.
