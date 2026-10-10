#!/usr/bin/env python3
"""Export a *provided* annotated transcription to TEI P5 / ALTO 4.4 / TXT.

No OCR, Cappelli matching, image inspection, or XML schema validation is performed.
Never use the bundled demo coordinates as measurements of a real manuscript.
"""
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from xml.etree import ElementTree as ET

TEI = "http://www.tei-c.org/ns/1.0"
TEI_VERSION = "4.12.0"
TEI_SCHEMA = Path(__file__).resolve().parents[1] / "schemas" / ("tei-p5-" + TEI_VERSION) / "tei_all.rng"
ALTO = "http://www.loc.gov/standards/alto/ns-v4#"
XML = "http://www.w3.org/XML/1998/namespace"
ID_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.-]*$")
STATUSES = {"proposed", "reviewed", "uncertain"}


def add(parent, tag, text=None, attrs=None, ns=TEI):
    node = ET.SubElement(parent, f"{{{ns}}}{tag}", attrs or {})
    if text is not None:
        node.text = text
    return node


def check_box(box, width, height, name):
    if box is None:
        return
    if not isinstance(box, list) or len(box) != 4:
        raise ValueError(f"{name}: bbox must be [x,y,width,height] or null")
    if any(isinstance(x, bool) or not isinstance(x, (float, int)) for x in box):
        raise ValueError(f"{name}: bbox coordinates must be numbers")
    x, y, w, h = box
    if x < 0 or y < 0 or w <= 0 or h <= 0 or x + w > width or y + h > height:
        raise ValueError(f"{name}: bbox out of bounds: {box}")


def validate(doc):
    if doc.get("schema") != "medieval-htr-v1":
        raise ValueError("schema must be medieval-htr-v1")
    if not doc.get("document_id") or not isinstance(doc["document_id"], str):
        raise ValueError("document_id required")
    src = doc.get("source", {})
    for k in ("width", "height"):
        if not isinstance(src.get(k), int) or isinstance(src[k], bool) or src[k] <= 0:
            raise ValueError(f"source.{k} must be positive integer")
    if not isinstance(doc.get("language", "la"), str) or not doc.get("language", "la"):
        raise ValueError("language must be a nonempty BCP 47 code")
    for k in ("image", "folio"):
        if not isinstance(src.get(k), str) or not src[k]:
            raise ValueError(f"source.{k} is required")
    if not isinstance(doc.get("lines"), list) or not doc["lines"]:
        raise ValueError("nonempty lines list required")
    ids = set()
    for line in doc["lines"]:
        name = line.get("id")
        if not isinstance(name, str) or not ID_RE.fullmatch(name) or name in ids:
            raise ValueError(f"invalid or duplicate line ID: {name}")
        ids.add(name)
        check_box(line.get("bbox"), src["width"], src["height"], name)
        if not isinstance(line.get("words"), list) or not line["words"]:
            raise ValueError(f"{name}: at least one word required")
        for word in line["words"]:
            wid = word.get("id")
            if not isinstance(wid, str) or not ID_RE.fullmatch(wid) or wid in ids:
                raise ValueError(f"invalid or duplicate word ID: {wid}")
            ids.add(wid)
            if word.get("status") not in STATUSES:
                raise ValueError(f"{wid}: unknown status")
            for key in ("diplomatic", "expanded"):
                val = word.get(key)
                if key == "diplomatic" and (not isinstance(val, str) or not val.strip()):
                    raise ValueError(f"{wid}: nonempty diplomatic reading required")
                if key == "expanded" and val is not None and not isinstance(val, str):
                    raise ValueError(f"{wid}: expanded must be text or null")
            if word.get("expanded") is not None and not word["expanded"].strip():
                raise ValueError(f"{wid}: expanded cannot be empty")
            ctype = word.get("change_type")
            if ctype not in {"none", "abbreviation"}:
                raise ValueError(f"{wid}: change_type must be none or abbreviation")
            altered = word.get("expanded") is not None and word["expanded"] != word["diplomatic"]
            if altered and ctype != "abbreviation":
                raise ValueError(f"{wid}: changed reading requires explicit abbreviation classification")
            if not altered and ctype == "abbreviation":
                raise ValueError(f"{wid}: abbreviation classification but no expansion supplied")
            if not isinstance(word.get("evidence", []), list):
                raise ValueError(f"{wid}: evidence must be a list")
            check_box(word.get("bbox"), src["width"], src["height"], wid)
    return doc


def attrs_box(box):
    x, y, w, h = box
    return dict(HPOS=str(x), VPOS=str(y), WIDTH=str(w), HEIGHT=str(h))


def make_tei(doc):
    ET.register_namespace("", TEI)
    root = ET.Element(f"{{{TEI}}}TEI", {f"{{{XML}}}lang": doc.get("language", "la"), "version": TEI_VERSION})
    header = add(root, "teiHeader")
    fd = add(header, "fileDesc")
    ts = add(fd, "titleStmt")
    add(ts, "title", f"{doc['document_id']}, {doc['source']['folio']}: working transcription")
    pub = add(fd, "publicationStmt")
    add(pub, "p", "Working output; verify all proposed readings against the manuscript.")
    sd = add(fd, "sourceDesc")
    add(sd, "p", f"Digitized source image: {doc['source']['image']}")
    ed = add(header, "encodingDesc")
    ep = add(ed, "editorialDecl")
    add(ep, "p", "Diplomatic readings preserve abbreviations; expansions are proposed "
        "editorial readings. Word @type denotes reviewed, proposed or uncertain status.")

    fac = add(root, "facsimile")
    src = doc["source"]
    surface_id = "s_" + doc["lines"][0]["id"].split("_l")[0]
    surface = add(fac, "surface", attrs={f"{{{XML}}}id": surface_id,
          "n": src["folio"], "ulx": "0", "uly": "0",
          "lrx": str(src["width"]), "lry": str(src["height"])})
    add(surface, "graphic", attrs={"url": src["image"]})
    for line in doc["lines"]:
        if line.get("bbox") is None:
            continue
        x, y, w, h = line["bbox"]
        add(surface, "zone", attrs={f"{{{XML}}}id": "z_" + line["id"],
            "ulx": str(x), "uly": str(y), "lrx": str(x+w), "lry": str(y+h)})

    text = add(root, "text")
    body = add(text, "body")
    division = add(body, "div", attrs={"type": "transcription"})
    add(division, "pb", attrs={"n": src["folio"], "facs": f"#{surface_id}"})
    ab = add(division, "ab")
    for n, line in enumerate(doc["lines"], start=1):
        lb_attrs = {"n": str(n)}
        if line.get("bbox") is not None:
            lb_attrs["facs"] = "#z_" + line["id"]
        add(ab, "lb", attrs=lb_attrs)
        for word in line["words"]:
            w = add(ab, "w", attrs={f"{{{XML}}}id": word["id"], "type": word["status"]})
            dip = word["diplomatic"]
            exp = word.get("expanded")
            if exp is not None and exp != dip:
                c = add(w, "choice")
                abbr = add(c, "abbr")
                if word["status"] == "uncertain":
                    add(abbr, "unclear", dip)
                else:
                    abbr.text = dip
                add(c, "expan", exp)
            elif word["status"] == "uncertain":
                add(w, "unclear", dip)
            else:
                w.text = dip
            w.tail = " "
    return ET.ElementTree(root)


def write_tei(tree, destination):
    """Write a versioned TEI document with an offline xml-model schema reference.

    This serializer does not itself validate. Use scripts/validate_tei.py.
    The namespace is the stable TEI namespace, not a release-specific namespace.
    """
    destination = Path(destination)
    if not TEI_SCHEMA.is_file():
        raise FileNotFoundError(f"Offline TEI schema missing: {TEI_SCHEMA}")
    try:
        href = Path(os.path.relpath(TEI_SCHEMA, destination.resolve().parent)).as_posix()
    except ValueError:  # Windows: destination and bundled schema on different drives.
        href = TEI_SCHEMA.as_uri()
    href = href.replace('&', '&amp;').replace('"', '&quot;')
    tree.getroot().set("version", TEI_VERSION)
    ET.register_namespace("", TEI)
    prefix = ('<?xml version="1.0" encoding="UTF-8"?>\n'
              '<?xml-model href="' + href + '" type="application/xml" '
              'schematypens="http://relaxng.org/ns/structure/1.0"?>\n')
    destination.write_bytes(prefix.encode("utf-8") + ET.tostring(tree.getroot(), encoding="utf-8"))


def validate_tei_file(source):
    """Offline Relax NG validation against the bundled, checksummed TEI release.

    Requires lxml. Embedded XPath 2 Schematron constraints are not executed.
    """
    import hashlib
    from lxml import etree
    source = Path(source).resolve()
    manifest = json.loads((TEI_SCHEMA.parent / "sources.json").read_text(encoding="utf-8"))
    expected = next(f["sha256"] for f in manifest["files"] if f["file"] == TEI_SCHEMA.name)
    if hashlib.sha256(TEI_SCHEMA.read_bytes()).hexdigest() != expected:
        raise ValueError("Bundled TEI schema checksum mismatch")
    parser = etree.XMLParser(no_network=True, resolve_entities=False, load_dtd=False)
    schema_tree = etree.parse(str(TEI_SCHEMA), parser)
    if schema_tree.xpath("//rng:include | //rng:externalRef", namespaces={"rng": "http://relaxng.org/ns/structure/1.0"}):
        raise ValueError("Bundled schema must be self-contained for offline validation")
    document = etree.parse(str(source), parser)
    if document.getroot().get("version") != TEI_VERSION:
        raise ValueError("TEI root does not declare version " + TEI_VERSION)
    if document.docinfo.doctype:
        raise ValueError("External DTDs are not used by this offline TEI export")
    models = document.xpath('/processing-instruction("xml-model")')
    hrefs = [re.search(r'href="([^"]+)"', model.text) for model in models]
    if not any(h and (source.parent / h.group(1)).resolve() == TEI_SCHEMA.resolve() for h in hrefs):
        # For exports on another Windows drive, write_tei uses an absolute file URI.
        if not any(h and h.group(1) == TEI_SCHEMA.as_uri() for h in hrefs):
            raise ValueError("Missing or incorrect offline xml-model schema reference")
    validator = etree.RelaxNG(schema_tree)
    if not validator.validate(document):
        raise ValueError(str(validator.error_log))
    ids = document.xpath('//@xml:id', namespaces={"xml": XML})
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate xml:id")
    facs = document.xpath('//@facs')
    if any(ref[1:] not in ids for value in facs for ref in value.split() if ref.startswith('#')):
        raise ValueError("Unresolved local facsimile reference")
    return {"tei_version": TEI_VERSION, "schema": str(TEI_SCHEMA), "schema_sha256": expected,
            "relaxng_valid": True, "schematron_checked": False, "offline": True,
            "local_facsimile_references_valid": True, "lxml_version": '.'.join(map(str, etree.LXML_VERSION)),
            "note": "Relax NG validity only; embedded XPath 2 Schematron and scholarly correctness are not validated."}


def make_alto(doc, word_level):
    ET.register_namespace("", ALTO)
    root = ET.Element(f"{{{ALTO}}}alto", {"SCHEMAVERSION": "4.4"})
    src = doc["source"]
    desc = add(root, "Description", ns=ALTO)
    add(desc, "MeasurementUnit", "pixel", ns=ALTO)
    si = add(desc, "sourceImageInformation", ns=ALTO)
    add(si, "fileName", src["image"], ns=ALTO)
    layout = add(root, "Layout", ns=ALTO)
    page = add(layout, "Page", ns=ALTO, attrs={
        "ID": "page_1", "PHYSICAL_IMG_NR": "1",
        "PRINTED_IMG_NR": src["folio"], "LANG": doc.get("language", "la"),
        "WIDTH": str(src["width"]), "HEIGHT": str(src["height"])
    })
    # Bound the actual, measured line rectangles; do not pretend the entire
    # image is a measured printspace or text block.
    boxes = [ln["bbox"] for ln in doc["lines"]]
    left = min(b[0] for b in boxes)
    top = min(b[1] for b in boxes)
    right = max(b[0] + b[2] for b in boxes)
    bottom = max(b[1] + b[3] for b in boxes)
    actual_bounds = attrs_box([left, top, right-left, bottom-top])
    printspace = add(page, "PrintSpace", ns=ALTO, attrs=actual_bounds)
    block = add(printspace, "TextBlock", ns=ALTO,
                attrs={"ID": "block_1", **actual_bounds})
    for line in doc["lines"]:
        if line.get("bbox") is None:
            raise ValueError(f"Cannot export ALTO without authentic line bbox: {line['id']}")
        tline = add(block, "TextLine", ns=ALTO,
                    attrs={"ID": line["id"], **attrs_box(line["bbox"])})
        if word_level:
            for word in line["words"]:
                if word.get("bbox") is None:
                    raise ValueError(f"Word-level ALTO needs authentic word bbox: {word['id']}")
                sa = {"ID": word["id"], "CONTENT": word["diplomatic"],
                      **attrs_box(word["bbox"])}
                exp = word.get("expanded")
                if exp is not None and exp != word["diplomatic"]:
                    sa["SUBS_TYPE"] = "Abbreviation"
                    sa["SUBS_CONTENT"] = exp
                add(tline, "String", ns=ALTO, attrs=sa)
        else:
            text = " ".join(w["diplomatic"] for w in line["words"])
            add(tline, "String", ns=ALTO,
                attrs={"ID": "line_string_" + line["id"], "CONTENT": text,
                       **attrs_box(line["bbox"])})
    return ET.ElementTree(root)


def export(doc, out_dir):
    validate(doc)
    out_dir = Path(out_dir)
    # Pre-check boxes to avoid half-written output in case of missing segmentation.
    if any(line.get("bbox") is None for line in doc["lines"]):
        raise ValueError("Cannot export layout without a line bbox. Use genuine PAGE/ALTO segmentation.")
    word_level = all(w.get("bbox") is not None for ln in doc["lines"] for w in ln["words"])
    out_dir.mkdir(parents=True, exist_ok=True)
    write_tei(make_tei(doc), out_dir / "edition.tei.xml")
    make_alto(doc, word_level).write(out_dir / "diplomatic.alto.xml", encoding="utf-8", xml_declaration=True)
    for key in ("diplomatic", "expanded"):
        lines = [" ".join((w.get(key) or w["diplomatic"]) for w in ln["words"])
                 for ln in doc["lines"]]
        (out_dir / (key + ".txt")).write_text("\n".join(lines) + "\n", encoding="utf-8")
    open_items = [(ln["id"], w["id"], w["diplomatic"], w.get("expanded"))
                  for ln in doc["lines"] for w in ln["words"]
                  if w["status"] != "reviewed"]
    notes = ["# Readings needing review", "",
             f"ALTO granularity: {'word' if word_level else 'line'}.", ""]
    for lid, wid, dip, exp in open_items:
        notes.append(f"- {lid} / {wid}: `{dip}` => `{exp or '[not expanded]'}`")
    (out_dir / "review-needed.md").write_text("\n".join(notes) + "\n", encoding="utf-8")
    return word_level, len(open_items)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--validate-tei", action="store_true", help="Validate offline against bundled TEI 4.12.0 Relax NG; requires lxml")
    args = parser.parse_args()
    doc = json.loads(args.input.read_text(encoding="utf-8"))
    granularity, pending = export(doc, args.out_dir)
    print(f"Export complete: {args.out_dir} | ALTO={'word' if granularity else 'line'} "
          f"| pending review={pending}")
    if args.validate_tei:
        result = validate_tei_file(args.out_dir / "edition.tei.xml")
        (args.out_dir / "tei-validation.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print("TEI 4.12.0 Relax NG: valid (offline). Schematron and ALTO XSD not checked.")
    else:
        print("NOTE: Only structural checks performed. TEI/ALTO schema validation not performed.")


if __name__ == "__main__":
    main()
