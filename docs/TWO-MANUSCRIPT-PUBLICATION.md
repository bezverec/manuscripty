# Publikace dvou rukopisů

Oba kodexy pocházejí z fondů Vědecké knihovny v Olomouci. Jejich souhrnný název
v dodaných digitalizačních XML je **Textus varii**. Názvy dílčích děl, atribuce,
datace a provenience mají vlastní zdroje a nejistoty v popisu dokumentu; datum
jednoho textu nebo explicit nejsou automaticky datem celého kodexu.

| Dokument | Snímky | Zdroj identifikací | Stálý záznam |
|---|---:|---|---|
| M II 220 | 677 | [Manuscripta.cz](https://manuscripta.cz/manuscript/VKOL_M_II_220/), dodané XML | https://rukopisy.digitalizaty.cz/rukopisy/vkol-m-ii-220 |
| M II 153 | 197 | [Manuscripta.cz](https://manuscripta.cz/manuscript/VKOL_M_II_153/), dodané XML | https://rukopisy.digitalizaty.cz/rukopisy/vkol-m-ii-153 |

Původní výzkumná data M II 220 zůstávají zachována. Identifikační doplnění mění
hlavičku dokumentu, popis a hlavičku jeho TEI indexu; obsah `<text>` indexu a všech
677 původních stránkových záznamů zůstává stejný. Import ověřuje původní SHA,
identitu, počty a kanonický XML obsah před zápisem. Přehled změněných
identifikačních hashů je v `validation/two-manuscript-import.json`.

M II 153 má oba původní HTR kandidáty na stejných 15 013 segmentech, samostatnou
pracovní rekonstrukci, český překlad v 3 531 úsecích, vazby pasáží na řádky a obrazovou evidenci.
Stavy jsou `proposed`, `expert_review: false`. Prázdné hlavní textové plochy se
nezaměňují s nepřepsanými okrajovými přípisy. Značky nejistot a přeškrtnutí jsou
součástí ediční vrstvy. Smíšené latinské a německé doplňky 96v mají vlastní
jazykové značky. Žádná hodnota CER/WER se netvrdí bez odborné referenční transkripce.

## Web a identifikátory

Úvod obsahuje dva skutečné katalogové záznamy, společné hledání a odkazy na celé
rukopisy. Prohlížeč načítá explicitní povolený registr; `?doc=vkol-m-ii-153`
vybírá druhý rukopis. Původní odkazy bez `doc`, přípony `.html`, všech sedm hodnot
`vrstva` a fragmenty řádků zůstávají funkční pro M II 220.

Registr `web/manuscripts.json` řídí generování 874 statických stránek a Pagefind.
AI shrnutí má samostatné zdrojové odkazy; do indexu folií se přidávají jen
zaregistrované snímky. IIIF zůstává přípravou: manifest je návrh, přepínač vypnutý,
obrazová IIIF média nebyla nahrána. Licence snímků není vydávána za CC0.

## Reprodukce a úložiště

Explicitní publikační buildery jsou v `web/publication/`. Vyžadují lokální
výzkumné vstupy a parametry cest; soukromá pracovní data ani váhy nejsou v Git.
Dokončení, obrazovou evidenci, původní HTR a geometrii ověřují před publikací.
`web/import_manuscript.py` přijímá ověřený dokončený textový overlay, odmítá média,
přístupové údaje, přepis odlišných původních výzkumných souborů a překryv vstupu/výstupu.

Obrazy M II 153 jsou WebP dlaždice, náhledy a řádkové výřezy v R2 pod
`v2/vkol-m-ii-153/`: 62 131 souborů, 3 290 011 866 bajtů. Lokální kontrola ověřila
SHA všech souborů a jejich zdroje; vzdálená inventura ověřila ETag/MD5 všech
objektů a veřejné SHA/CORS vybraných vzorků. Archivní TIFF ani obrazové soubory
nepatří do repozitáře. Omezený dočasný upload token byl po použití zneplatněn;
ověření odmítnutí starého klíče a odstranění místní kopie je zaznamenáno bez klíče.

GitHub Actions dostaly výslovně schválenou možnost vytvářet PR. Výchozí oprávnění
zůstává `read`; indexační workflow má konkrétní zápisová oprávnění pouze pro
generovaný přehled návrhů. Neslučuje ani neschvaluje PR a nemění kanonické HTR.
Nasazování na Cloudflare Pages zůstává ruční.
