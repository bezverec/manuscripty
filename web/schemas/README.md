# Pinned IIIF Presentation 3 validation schema

Unmodified `schema/iiif_3_0.json` from the official IIIF validator repository:
https://github.com/IIIF/presentation-validator/blob/3891f47ce7dbaa896027a5fab5f63a109de4bd70/schema/iiif_3_0.json

Retrieved 2026-10-12. SHA-256:
`14dd7ee8aee25d959be4b12feddb4179c726909fc85b925f6707f4ab3bfe2ad6`.
The schema is tested offline with Ajv (draft 7 and URI formats). The normative
specification remains https://iiif.io/api/presentation/3.0/.

Validation covers JSON structure/types and additional local canvas, range, link and
feature-flag invariants. It does not establish complete IIIF conformance, JSON-LD
expansion, HTTP availability/CORS or compatibility with a remote viewer. Image API
requests are separately tested on a synthetic image against the tile algorithm at
https://iiif.io/api/image/3.0/implementation/. No source TIFF was processed.

TODO: the pinned upstream repository has no LICENSE file or GitHub license metadata.
The schema is preserved with its source and hash; clarify upstream redistribution
terms before further redistribution. No manuscript license is inferred from it.
