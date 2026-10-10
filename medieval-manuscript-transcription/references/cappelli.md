# Cappelli / Ad fontes: controlled use

Primary lookup and information:

- https://www.adfontes.uzh.ch/en/ressourcen/abkuerzungen/cappelli-online
- https://adfontes.uzh.ch/en/ressourcen/abkuerzungen/cappelli-daten-zum-download
- https://centerfordigitalhumanities.github.io/cappelli/index.mini.html

The University of Zurich / Ad fontes offers a structured, crowdsourced transcription
of Cappelli's *Lexicon abbreviaturarum*, including the corresponding abbreviation
images, IDs and pages. Ad fontes states that those dictionary images and information
are in the public domain; some dataset errors may remain. The downloadable zip
contains an Excel file and matching image IDs. Verify current download/access before
claiming an archive has been downloaded.

## Lookup procedure

1. First read the target abbreviation from the manuscript image. Describe shape,
   superscript/overline position, base letters, and likely abbreviation class.
2. Search candidate expansions by characters, language, category and abbreviation
   image in Ad fontes, or in a locally imported copy of the dataset.
3. Compare the *visual form* and script context; do not identify a dictionary entry
   using expanded Latin alone.
4. Record: `source="cappelli"`, `record_id`, `page`, `abbreviation`, `expansion`,
   `url`, match notes, lookup timestamp if actually retrieved. If unavailable, record
   only `source="unverified_dictionary_hypothesis"` and do not fabricate IDs.
5. Prefer repeated evidence from the same scribal hand over mere dictionary match.
6. Do not silently import dataset content into the published edition; store a short
   provenance note and use direct source URLs or page citations as appropriate.

## Common classes to investigate

- Suspension (ending omitted)
- Contraction (middle of word omitted)
- Superscript letters and overlines
- Special signs for common Latin units (per, pro, qui/quod, et, -us, -rum...)

The same visual sign can have multiple expansions by period, region, language,
script and grammatical case. Cappelli is a reference dictionary, not a universal
OCR decoding function. Never substitute dictionary text for visual assessment.

## Optional future implementation

When a user supplies the downloaded XLSX+images archive, implement a small **offline**
read-only lookup index (SQLite FTS, with optional thumbnail search), keyed by the real
Cappelli record ID; include provenance, script, language, image name and page. Support
multiple candidate expansions and manually confirmed mapping to the local manuscript
hand. Do not invent column names until inspecting the actual workbook.
