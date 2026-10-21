# Fáze 4 — návrhy oprav na GitHubu

Původní workflow nyní obsluhuje tři dokumenty. Dva první zachovávají v1,
M I 259 má v2 s identitou orientovaného souřadnicového PNG a transformační
maticí k TIFFu. [Aktuální kontrakty](data-contracts.md). Historické doklady
níže patří ke své původní fázi; nejsou novým browserovým testem tří rukopisů.

Formuláře HTR a segmentace mají ID polí shodná s exporty prohlížeče. URL předvyplňuje `template` a tato ID; parametr `labels` se nepoužívá. Nad limitem 7 500 znaků zůstává export JSON. Jeho celý obsah patří do pole `proposal_json`; pouhá příloha ani externí URL se automaticky nestahuje.

Oba workflow čtou pouze důvěryhodný kód výchozí větve. Text hlášení se zpracovává jako data, nikdy se nevkládá do shellu, `eval` ani programu. Kontrola ověřuje schema, dokument, folio, SHA původního skenu, ID, původní HTR a geometrii; neposuzuje paleografickou správnost. Neplatný návrh dostane jeden průběžně aktualizovaný komentář a `needs-info`. Index obsahuje pouze otevřené validní návrhy; uzavřená hlášení a PR se vyloučí.

`proposals.json` zachovává původní tvar `{folio: {line_id: [issue_number]}}` pro M II 220 a přidává `documents[document_id][folio][line_id]`. Chybějící oblast má klíč `*` a objeví se jako návrh související s celou stranou. Další rukopisy používají `data/<document_id>/<folio>/page.json` (podporuje se také `rukopisy/<document_id>/data/<folio>/page.json`); legacy M II 220 má původní `data/<folio>/page.json`.

Přehledové workflow vytvoří nebo aktualizuje jedinou větev `automation/open-proposals` a PR měnící `web/public/proposals.json` a jeho SHA/velikost ve zdrojovém manifestu. Nasazení zůstává ruční. Automatický deploy lze navrhnout samostatně po schválení provozního postupu.

## Ověření a otevřené kroky

- `npm test` zahrnuje formuláře, dlouhé URL, Unicode, přesnou identitu, namespace isolation, JSON fallback, neplatné návrhy, uzavřená hlášení a opakované komentáře.
- Volitelný browser test: `npm run test:proposals:ui`, s `MANUSCRIPT_PLAYWRIGHT` (nainstalovaný Playwright modul) a `MANUSCRIPT_TEST_MEDIA` (lokální kořen existujících obrazů obsahující v1/). Fixture #101 nenavštěvuje GitHub.
- `python web/validate_snapshot.py` nad aktualizovaným frontendovým manifestem kontroluje neměnnost celého výzkumného snapshotu.
- Pro společnou publikaci byly vytvořeny skutečné štítky `htr-oprava`, `segmentace-oprava`, `needs-info`.
- Po výslovném souhlasu správce je v repozitáři povolená tvorba PR z Actions; výchozí oprávnění zůstalo `read`. Samotný workflow PR neschvaluje ani neslučuje.
- Kontrolní `workflow_dispatch` po sloučení [12. 10. 2026](https://github.com/bezverec/manuscripty/actions/runs/38304633347) úspěšně potvrdil shodu indexu s otevřenými validovanými návrhy. Žádné nové hlášení ani návrhový PR nevznikl. Úplný živý cyklus nového zkušebního issue a zpětného komentáře zatím neproběhl; parsing, PR a idempotence jsou pokryty místními kontraktními testy a fixture.
- Prohlížeč byl ověřen v Chrome s fixture #101: odkaz v seznamu HTR i řádkové analýze, předvyplnění identity a absence browser pageerrors. Desktop 1440×900 a mobilní panel 390×844 jsou lokálně v docs/validation/phase-4-screenshots; snímky nepatří do výzkumných dat ani source manifestu. Žádné skutečné issue nevzniklo.

Dokumentace: [URL parametrů GitHub Issues](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/creating-an-issue#creating-an-issue-from-a-url-query), [schema formulářů](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-githubs-form-schema).

Manifest `docs/web-source-manifest.json` se mění pouze pro frontendové soubory a nový prázdný přehled. Výzkumné texty a zdrojové otisky se nemění.
