# Canonical data, exports and measurements

## Minimal JSON contract

See `../assets/demo.json` (ALL coordinates and text there are illustrative).

Required top-level: `schema`, `document_id`, `source`, `lines`. Optional `language`
(BCP 47, defaults to `la`).

- `source`: `image` (original filename), positive `width` and `height`, `folio`.
- each line: `id`, `bbox` `[x, y, width, height]` or `null`, `words`.
- each word: `id`, `bbox` or `null`, `diplomatic`, `expanded` (string or null),
  `status` (`proposed`, `reviewed`, `uncertain`), `change_type` (`none` or
  `abbreviation`), `evidence` (list), `alternatives`
  (list of alternatives, optional).
- The IDs must be unique and stable across revisions; never derive IDs by rounding
  coordinates or reusing mutable positions without a migration map.
- A `bbox` must be measured or copied from genuine image segmentation, never guessed.
  Coordinate origin is top-left of the same original image; unit pixels.
- Add `source_sha256`, HTR model/version, OCR raw output, review author/date and
  editorial policy to project metadata when actually known.

## TEI P5 4.12.0

Use namespace `http://www.tei-c.org/ns/1.0`.

- `teiHeader` documents sources, editor, transcription policy and uncertainty.
- `<facsimile>/<surface>/<graphic>/<zone>` anchors a page and physical text lines.
  A `<lb facs="#zone-id"/>` links transcription to a measured source region.
- Keep word IDs; `<choice><abbr>q̃litates</abbr><expan>qualitates</expan></choice>`
  represents different editorial representations of the same source word.
- Consider `<am>` and `<ex>` in a higher-fidelity edition for precise graphical
  abbreviation and editorial-supplement boundaries.
- Use `<unclear>`, `<gap>`, `<supplied>`, `<sic>/<corr>` only when justified.
- A derived expanded TXT must be generated from the same canonical data, not via a
  separate unaligned transcription.
- Parsing XML is **not** full TEI schema validation. Use TEI's official schema or
  custom ODD-derived Relax NG/Schema validation where available.

Official TEI Guidelines:
https://www.tei-c.org/release/doc/tei-p5-doc/en/html/PH.html

## ALTO 4.4

- Namespace `http://www.loc.gov/standards/alto/ns-v4#`.
- `Description` includes pixel measurement and original image filename;
  `Layout/Page/PrintSpace/TextBlock/TextLine/String` preserve layout.
- Main `CONTENT` is the diplomatic word or line transcription.
- If actual word boxes exist, export `String` per word and use
  `SUBS_TYPE="Abbreviation" SUBS_CONTENT="..."` for genuinely expanded forms.
- If only line boxes exist, produce **one line-level String** inside each TextLine,
  without fabricated token coordinates or misleading substitution metadata.
  Note word-level linking is unavailable in that fallback export.
- Absence of page or line coordinates blocks a trustworthy ALTO layout export;
  report it, keep TEI/JSON/TXT and request segmentation instead of inventing boxes.
- Check against the exact ALTO 4.4 XSD, and test Kramerius/NDK compatibility on the
  actual importer. ALTO schema validity does not guarantee application compatibility.

Official ALTO XSD repository: https://github.com/altoxml/schema

## Evaluation

- Keep a held-out, **manually reviewed reference** in the declared transcription
  convention. Never score an automatically reconstructed text as ground truth.
- Calculate diplomatic CER against diplomatic reference and expanded CER against
  expanded reference separately. Cite scope (folio/lines), normalization and sample
  size. CER = Levenshtein distance / reference-character count.
- Report word error rate (WER) separately; compare the same physical lines and
  exact reading order, ignoring neither missing lines nor segmentation errors.
- For evaluation alone, choose Unicode NFC or NFD consistently and document it;
  never strip abbreviation marks or silently replace long s, u/v, i/j if they are
  part of the defined diplomatic convention.
- Track percentages needing manual review and the mismatch categories: segmentation,
  character substitution, abbreviation expansion, line ordering and punctuation.

**Important:** `change_type="abbreviation"` is permitted only when the alternate
reading is truly an expansion of an attested abbreviation, never an OCR correction.
Other editorial correction types require a richer data model and a separate TEI
`<sic>/<corr>` representation; the bundled reference exporter rejects them.

## Offline profil pro tento projekt

Výchozí vydání exportéru je pevně TEI P5 4.12.0. Oficiální samostatné schéma TEI All je přibaleno v `schemas/tei-p5-4.12.0/tei_all.rng`; původ a SHA-256 obsahuje `sources.json`. Export používá TEI/@version="4.12.0" a relativní xml-model. Namespace se nemění. Skript `scripts/validate_tei.py` nebo přepínač exportéru `--validate-tei` kontroluje schéma lokálně pomocí lxml se zakázanou sítí. Ověřuje se Relax NG, nikoli vložená pravidla XPath 2 Schematron. ALTO schema validace i odborná revize zůstávají samostatné kroky.
