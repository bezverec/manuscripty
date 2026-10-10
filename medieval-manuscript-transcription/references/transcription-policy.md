# Transcription policy: medieval manuscripts

## Two independent but linked readings

**Diplomatic (diplomatic)**: what is materially attested on the leaf. Retain
letterforms or chosen scholarly grapheme mapping; keep tildes, abbreviation marks,
`ꝑ`, `ꝓ`, `ꝯ`, `⁊`, `ſ`, superscripts, punctuation and line breaks whenever legible.
Record all substitutions in an explicit transcription policy; do not indiscriminately
modernize spelling or expand an abbreviation in this layer.

**Expanded (expanded)**: editorial interpretation of the same material; expand only
abbreviations supported by the image, known scribal conventions, and syntactic context.
Preserve original lexeme/morphology as much as possible. An expansion is not a full
normalization, correction, translation, or reconstruction of a canonical quotation.

Both layers MUST be stored per document/line/word. Some abbreviations require
many-to-one or one-to-many alignment; preserve an explicit alignment note rather
than inserting imaginary token boundaries.

## Manual editorial decision procedure

1. Identify physical line and script (e.g. textualis / cursiva) cautiously.
2. Read unambiguous base letters before deciding abbreviation expansion.
3. Verify placement and shape of abbreviation mark; distinguish mark from scan
   noise and adjacent-line ascenders/descenders.
4. Inspect the same scribe's parallel forms on the current folio and nearby folios.
5. Generate alternatives; use grammar and subject matter as **secondary** evidence.
6. Consult Cappelli if available; cite the exact entry as dictionary evidence only.
7. Assign status: `reviewed` only after actual image verification and human/editorial
   review; `proposed` for defensible but not verified reading; `uncertain` when choice
   remains material. Never invent a numerical probability.
8. Record evidence and unresolved variants in JSON. Preserve the raw HTR string.

## Typical pitfalls

- `u/v`, `i/j`, `c/t`, `n/u/m`, `r`-rotunda and long `ſ` cause substitution errors.
- Diacritics may be stored as combining Unicode marks; NFC display and NFD storage
  can look alike but differ byte-for-byte. Preserve original data and state any
  normalized representation used for CER comparisons.
- HTR may confuse line endings and catchwords or merge the next column. Exclude
  marginal notes and foliations from the main text but encode them separately.
- A recognizable biblical or scholastic quote is not permission to replace what the
  copyist actually wrote.
- Use a physically justified space/word boundary, not arbitrary whitespace in HTR.
- For truly illegible stretches or lacunae, record `uncertain` and a transparent
  placeholder policy; do not invent letters.

## M II 220 / fol. 323r: hypothesis only

Earlier HTR for this manuscript contained:

`Sicut q̃litates elemētorꝭ in rebꝯ ...`

One reasonable **proposed** expanded reading:

`Sicut qualitates elementorum in rebus ...`

The proposed sequence is NOT a fully verified transcription, and the token positions
must be obtained from the original TIFF or its genuine PAGE/ALTO segmentation.
Do not label it validated ground truth.

## Human review checklist

- Can each proposed reading be pointed to on the exact image crop?
- Are expansions distinct from correction/normalization of the original spelling?
- Are editorial conjectures visibly marked and described?
- Are absent or hard-to-read glyphs marked uncertain, not resolved by guesswork?
- Are line breaks, text order, and page labels stable?
- Can the reviewer retrieve the candidate HTR strings and source image for a token?
