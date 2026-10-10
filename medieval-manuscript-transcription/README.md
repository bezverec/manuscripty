# Medieval Manuscript Transcription – Codex Skill

This is a *ready-to-install Codex Skill*, not an OCR model and not a fine-tuned LLM.
Its goal is critically reviewed dual-layer manuscript transcription and well-structured
image-linked exports.

## Installation

**In a repository**: unpack `medieval-manuscript-transcription/` to
`<repo>/.agents/skills/medieval-manuscript-transcription/`.

**For all your projects**: unpack the directory to
`~/.codex/skills/medieval-manuscript-transcription/`.

Invoke Codex with an instruction such as:

> Use $medieval-manuscript-transcription. Analyze the manuscript TIFF and the
> Kraken/TRIDIS HTR results. Create diplomatic and expanded Latin transcriptions,
> mark uncertain readings, then export aligned TEI P5 and ALTO XML.

The skill can guide Codex through tools available in its own execution environment.
It does not grant image viewing, OCR inference, web lookup or internet access by itself.

## Demo of the included XML exporter

From the skill directory:

```bash
python scripts/export.py --input assets/demo.json --out-dir ./demo-output
python -m unittest discover -s tests -v
```

The bundled demo is **synthetic**. Its example word boxes have no relation to any real
manuscript; do not repurpose them for archival data.

The reference exporter generates two TXT files, TEI, ALTO and review notes from
supplied aligned JSON. It requires genuine measured **line coordinates** for ALTO,
falls back to line-level ALTO if word coordinates are missing, and does not perform OCR.
Additional TEI RNG and ALTO XSD validation must be run in your target environment.

## Sources

- OpenAI Codex Agent Skills: https://developers.openai.com/api/docs/guides/tools-skills
- Ad fontes Cappelli data: https://adfontes.uzh.ch/en/ressourcen/abkuerzungen/cappelli-daten-zum-download
- TEI Guidelines: https://www.tei-c.org/release/doc/tei-p5-doc/en/html/PH.html
- ALTO XSD: https://github.com/altoxml/schema

## TEI 4.12.0 offline

Exporty nyní používají TEI P5 4.12.0 a místní kopii oficiálního schématu. Validace vyžaduje Python s balíčkem lxml; při běhu nepotřebuje internet.

```bash
python scripts/export.py --input assets/demo.json --out-dir ./demo-output --validate-tei
python scripts/validate_tei.py ./demo-output/edition.tei.xml --report ./demo-output/tei-validation.json
```

Výsledek znamená shodu se schématem Relax NG 4.12.0, nikoli ověření pravidel Schematron, ALTO XSD nebo správnosti přepisu. Podrobnosti a licence jsou v [popisu přibaleného schématu](schemas/tei-p5-4.12.0/README.md).
