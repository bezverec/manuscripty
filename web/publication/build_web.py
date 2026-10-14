"""Stage multi-manuscript frontend and M II 153 data; never modify the live public tree.

The output is a merge overlay, not a standalone copy of the existing website.
Use --require-complete for a publication candidate. Without it a pilot preview is
explicitly partial. TIFF/PNG/model files are never copied into the Pages payload.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import shutil
from pathlib import Path
from lxml import etree as ET

DOC = "vkol-m-ii-153"
ORIGIN = "https://rukopisy.digitalizaty.cz"
MEDIA = "https://rukopisy-data.digitalizaty.cz/v2/" + DOC
REV = "20261012-6"
TEI = "http://www.tei-c.org/ns/1.0"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, content):
    path = Path(path)
    if path.suffix == '.html':
        from markup import normalize_html
        content = normalize_html(content)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def dump(path, content):
    write(path, json.dumps(content, ensure_ascii=False, indent=2) + "\n")


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError("Frontend baseline changed; expected one occurrence: " + old[:90])
    return text.replace(old, new, 1)


def patch_frontend(base, out, legacy_doc):
    from frontend_multi import patch_frontend as integrate
    return integrate(base, out, legacy_doc)


def stage_legacy_metadata(base, out, overlay, validator):
    """Update identification only; leave the 677 page entries and text layers intact."""
    doc = read(overlay / 'document.json')
    if doc['id'] != 'vkol-m-ii-220' or doc['reader'] != ORIGIN + '/rukopis':
        raise ValueError('Unexpected legacy identity or reader URI')
    data_path = base / 'pilot-data.js'
    code = data_path.read_text(encoding='utf-8')
    match = re.fullmatch(r'window\.PILOT_DATA\s*=\s*(\{.*\});\s*', code, re.S)
    if not match:
        raise ValueError('Unexpected legacy manifest format')
    data = json.loads(match.group(1))
    old_pages = json.dumps(data['pages'], sort_keys=True)
    old_counts = data['counts']
    if doc['counts'] != old_counts:
        raise ValueError('Legacy metadata count mismatch')
    data['document'] = doc
    data['title'] = doc['display_title_cs'] + ' / ' + doc['descriptive_title_cs']
    data['description_cs'] = doc['title_note_cs']
    assert json.dumps(data['pages'], sort_keys=True) == old_pages
    write(out / 'pilot-data.js', 'window.PILOT_DATA = ' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';\n')
    dump(out / 'document.json', doc)
    tei = ET.parse(str(overlay / 'tei/vkol-m-ii-220.xml'), ET.XMLParser(resolve_entities=False, no_network=True))
    if not validator.validate(tei):
        raise ValueError('Legacy metadata TEI invalid: ' + str(validator.error_log))
    previous = ET.parse(str(base / 'tei/vkol-m-ii-220.xml'), ET.XMLParser(resolve_entities=False, no_network=True))
    ns = {'t': TEI}
    assert ET.tostring(tei.find('t:text', ns), method='c14n') == ET.tostring(previous.find('t:text', ns), method='c14n')
    (out / 'tei').mkdir(exist_ok=True)
    shutil.copy2(overlay / 'tei/vkol-m-ii-220.xml', out / 'tei/vkol-m-ii-220.xml')
    record = (base / 'rukopisy/vkol-m-ii-220.html').read_text(encoding='utf-8')
    record = record.replace('Záznam celého dokumentu', 'Popis a zdroje').replace('Rukopisy · výzkumný pilot</a>', 'Rukopisy, snímek po snímku.</a>').replace('v záložce „O zpracování“', 'v záložce „O rukopisu“')
    record = replace_once(record, '<title>M II 220 · Vědecká knihovna v Olomouci</title>', '<title>' + html.escape(data['title']) + '</title>')
    record = replace_once(record, '<h1>Rukopis M II 220</h1>', '<h1>' + html.escape(data['title']) + '</h1>')
    notes = '<article><h2>Katalogová identifikace a zdroje</h2><p>' + html.escape(doc['title_note_cs']) + '</p>'
    notes += '<p>Staré signatury: ' + html.escape(', '.join(doc.get('old_shelfmarks', []))) + '.</p>'
    for catalogue in doc.get('external_catalogues', []):
        notes += '<p>Alternativní název podle <a href="' + html.escape(catalogue['url'], quote=True) + '">Manuscripta.cz</a>: ' + html.escape(catalogue['title_verbatim']) + '</p><p>Datace: ' + html.escape(catalogue['dating_verbatim']) + '. Jde o katalogový údaj; přesný rok není nezávisle potvrzen pro všechny části kodexu.</p><p>' + html.escape(catalogue['catalogue_reference_verbatim'] + '. ' + catalogue['catalogue_reference_note_cs']) + '</p>'
    for claim in doc.get('provenance_claims', []):
        notes += '<p>' + html.escape(claim['claim_cs'] + ' Zdroj: ' + claim['source']) + '</p>'
    for discrepancy in doc.get('catalogue_location_discrepancies', []):
        notes += '<p class="notice">' + html.escape(discrepancy['conclusion_cs']) + '</p>'
    from catalogue_records import legacy_catalogue_section
    notes += '</article>' + legacy_catalogue_section(doc)
    record = record.replace('<a class="btn" href="/summary">AI shrnutí</a></div>', '<a class="btn" href="/summary">AI shrnutí</a><a class="btn" href="#katalogovy-obsah">Katalogový obsah</a></div>', 1)
    record = replace_once(record, '<article><h2>TEI a podklady</h2>', notes + '<article><h2>TEI a podklady</h2>')
    from frontend_multi import decorate_record
    write(out / 'rukopisy/vkol-m-ii-220.html', decorate_record(record,{**doc,'title':data['title']},doc['title_note_cs']))
    return doc, {name: digest(base / name) for name in ('pilot-data.js', 'document.json', 'tei/vkol-m-ii-220.xml', 'rukopisy/vkol-m-ii-220.html')}


def latin_join(strings):
    """Only undo alphabetic word wraps; never remove uncertainty brackets."""
    text = "\n".join(strings)
    return re.sub(r"(?<=[A-Za-zÀ-ž])-\n(?=[a-zà-ž])", "", text).replace("\n", " ")


def passage_language(rows, fallback="la"):
    languages = {row.get("language", fallback) for row in rows}
    return next(iter(languages)) if len(languages) == 1 else "mul"


def adapt_interpretation(obj, lines):
    ids = [line["id"] for line in lines]
    if "passages" in obj:
        passages = obj["passages"]
        covered = {i for p in passages for i in p["line_ids"]}
    else:
        interpreted = {line["id"]: line for line in obj["lines"]}
        if set(interpreted) != set(ids):
            raise ValueError("Interpretation/source segment ID mismatch")
        passages = []
        for unit in obj["translation_units"]:
            units = [interpreted[i] for i in unit["line_ids"]]
            notes = [n for v in units for n in v.get("editorial_notes", [])]
            reading = [v["reconstruction_la"] for v in units if v.get("include_in_main_text", True)]
            if not reading:
                reading = [v["reconstruction_la"] for v in units]
            passages.append({"id": unit["id"], "title": unit.get("title", "Úsek " + str(len(passages) + 1)), "line_ids": unit["line_ids"], "latin": latin_join(reading), "czech": unit["translation_cs"], "notes": " · ".join(dict.fromkeys(notes)), "operations": [], "language": passage_language(units, obj.get("language", "la"))})
        # Preserve commentary-only fragments as explicit entries in the reader.
        covered = {i for p in passages for i in p["line_ids"]}
        for i in ids:
            if i not in covered and interpreted[i].get("include_in_main_text") is False:
                v = interpreted[i]
                passages.append({"id": "fragment_" + i, "title": "Fragment / poznámka", "line_ids": [i], "latin": v["reconstruction_la"], "czech": "Samostatný fragment bez souvislého překladu.", "notes": " · ".join(v.get("editorial_notes", [])), "operations": [], "language": v.get("language", obj.get("language", "la"))})
                covered.add(i)
    if covered != set(ids):
        raise ValueError("Interpretation does not cover source segments exactly")
    result = []
    for p in passages:
        if not p["line_ids"] or any(i not in ids for i in p["line_ids"]) or not p["latin"] or not p["czech"]:
            raise ValueError("Invalid or empty interpretation passage")
        language_map = obj.get("languages", {})
        languages = {language_map.get(i, language_map.get(str(ids.index(i) + 1), obj.get("language", "la"))) for i in p["line_ids"]}
        language = p.get("language", next(iter(languages)) if len(languages) == 1 else "mul")
        result.append({**p, "language": language, "notes": p.get("notes", ""), "operations": p.get("operations", [])})
    return result


def catalogue_items(path):
    root = ET.parse(str(path), ET.XMLParser(resolve_entities=False, no_network=True))
    items = []
    for item in root.xpath("//*[local-name()='msContents']/*[local-name()='msItem']"):
        locus = item.find("locus")
        title = item.find("title")
        if locus is not None and title is not None:
            items.append({"id": "catalogue_" + item.get("n", str(len(items) + 1)), "from": locus.get("from"), "to": locus.get("to"), "title": " ".join(title.itertext()).strip()})
    return items


def make_document_tei(out, doc, manifest, items, validator):
    q = lambda name: "{" + TEI + "}" + name
    root = ET.Element(q("TEI"), nsmap={None: TEI})
    root.set("{http://www.w3.org/XML/1998/namespace}id", DOC)
    root.set("version", "4.12.0")

    def el(parent, name, text=None, **attrs):
        node = ET.SubElement(parent, q(name), **attrs)
        if text is not None:
            node.text = str(text)
        return node

    header = el(root, "teiHeader")
    fd = el(header, "fileDesc")
    titles = el(fd, "titleStmt")
    el(titles, "title", doc["title"])
    for title in doc.get("alternative_titles", []):
        if isinstance(title, dict):
            el(titles, "title", title["title"], type="alternative")
    ps = el(fd, "publicationStmt")
    el(ps, "publisher", "Manuscripty — výzkumná prezentace")
    el(ps, "idno", doc["uri"], type="URI")
    el(el(ps, "availability"), "p", "Pracovní návrhy AI bez odborné revize. Licence zdrojového rukopisu nebyla v pilotu určena.")
    notes = el(fd, "notesStmt")
    for alternative in doc.get("alternative_titles", []):
        note = el(notes, "note", alternative["title"] + ": " + str(alternative.get("source", "")))
        if alternative.get("uri"):
            el(note, "ref", "Katalogový záznam", target=alternative["uri"])
    el(notes, "note", doc.get("catalogue_reference_discrepancy_cs", "Katalogové názvy označují různé složky kodexu."))
    sd = el(fd, "sourceDesc")
    ms = el(sd, "msDesc")
    mi = el(ms, "msIdentifier")
    for key, value in (("country", "Česko"), ("settlement", "Olomouc"), ("repository", "Vědecká knihovna v Olomouci"), ("idno", "M II 153")):
        el(mi, key, value)
    el(mi, "idno", "vkol000759929", type="catalogue")
    for former in ("2 IV 25", "II d 25"):
        el(el(mi, "altIdentifier", type="former"), "idno", former)
    el(el(mi, "altIdentifier", type="project"), "idno", DOC)
    contents = el(ms, "msContents")
    el(contents, "summary", doc["title_note_cs"])
    for item in items:
        m = el(contents, "msItem", n=item["id"].removeprefix("catalogue_"))
        el(m, "locus", item["from"] + "–" + item["to"], **{"from": item["from"], "to": item["to"]})
        el(m, "title", item["title"])
    history = el(ms, "history")
    origin = el(history, "origin")
    el(origin, "origDate", "2. polovina 14. století; podle dodaného digitalizačního popisu", notBefore="1350", notAfter="1400")
    if doc.get("provenance_note_cs"):
        el(history, "provenance", doc["provenance_note_cs"])
    ed = el(header, "encodingDesc")
    el(el(ed, "editorialDecl"), "p", "Tento TEI obsahuje doloženou identifikaci, katalogový soupis děl a seznam digitalizovaných snímků. Přepisy a interpretace jsou dostupné v jednotlivých navázaných souborech. Validita XML nepotvrzuje správnost četby.")
    body = el(el(root, "text"), "body")
    for page in manifest:
        div = el(body, "div", type="scan", n=page["folio"])
        el(div, "head", page["label"])
        p = el(div, "p")
        el(p, "ref", "Obraz a textové vrstvy", target=doc["reader"] + "#" + page["folio"])
    if not validator.validate(root):
        raise ValueError("Document TEI invalid: " + str(validator.error_log))
    xml = ET.tostring(root, encoding="UTF-8", xml_declaration=True, pretty_print=True)
    path = out / "tei" / (DOC + ".xml")
    path.parent.mkdir(parents=True, exist_ok=True)
    prefix = b'<?xml version="1.0" encoding="UTF-8"?>\n<?xml-model href="/schemas/tei-p5-4.12.0/tei_all.rng" type="application/xml" schematypens="http://relaxng.org/ns/structure/1.0"?>\n'
    path.write_bytes(prefix + ET.tostring(root, encoding="UTF-8", pretty_print=True))


def make_web_tei(source, dest, reader, validator):
    """Create a derivative web export without changing raw readings or geometry.

    The facsimile URI explicitly points to a tiled viewer, not to an original TIFF
    or a single bitmap. Retain the source-relative URI in the encoding description.
    """
    root = ET.parse(str(source), ET.XMLParser(resolve_entities=False, no_network=True)).getroot()
    ns = {"t": TEI}
    original_text = ET.tostring(root.find("{" + TEI + "}text"))
    image_refs = []
    for graphic in root.xpath("//t:facsimile//t:graphic", namespaces=ns):
        image_refs.append(graphic.get("url", ""))
        graphic.set("url", reader)
    encoding = root.find("{" + TEI + "}teiHeader/{" + TEI + "}encodingDesc")
    if encoding is None:
        raise ValueError("Missing encoding description in " + str(source))
    note = ET.SubElement(encoding, "{" + TEI + "}p")
    note.text = "Web presentation derivative. Facsimile graphic URI resolves to the public tiled manuscript viewer, not to a standalone bitmap or the archival TIFF. Coordinates remain original image pixels; the viewer renders them through Deep Zoom WebP tiles. Original relative graphic URI(s): " + "; ".join(image_refs) + ". Source readings and measured zones remain unchanged."
    assert ET.tostring(root.find("{" + TEI + "}text")) == original_text
    if not validator.validate(root):
        raise ValueError("Web TEI invalid: " + str(validator.error_log))
    prefix = '<?xml version="1.0" encoding="UTF-8"?>\n<?xml-model href="/schemas/tei-p5-4.12.0/tei_all.rng" type="application/xml" schematypens="http://relaxng.org/ns/structure/1.0"?>\n'
    write(dest, prefix + ET.tostring(root, encoding="unicode"))


def build(args):
    source = args.source.resolve()
    base = args.base_public.resolve()
    out = args.out.resolve()
    validate_paths(args)
    report_dir = args.report_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    validator = ET.RelaxNG(ET.parse(str(args.rng)))
    web_tei_count = 0
    manifest = read(source / "manifest.json")["pages"]
    if len({p["folio"] for p in manifest}) != len(manifest):
        raise ValueError("Duplicate page IDs")
    if args.require_complete and len(manifest) != 197:
        raise ValueError("Publication requires all 197 scans")
    if args.require_complete:
        from audit_interpretation import audit as audit_interpretation
        interpretation_audit = audit_interpretation(source, args.rng, pilot_source=args.pilot_source)
        dump(report_dir / 'interpretation-provenance-audit.json', interpretation_audit)
    legacy_doc, legacy_originals = stage_legacy_metadata(base, out, args.legacy_metadata.resolve(), validator)
    originals = patch_frontend(base, out, legacy_doc)
    originals.update(legacy_originals)
    metadata_path = args.supplier_metadata.resolve()
    items = catalogue_items(metadata_path)
    doc = {"schema": "manuscripty-document-v1", "id": DOC, "uri": ORIGIN + "/rukopisy/" + DOC, "title": "M II 153 · Stimulus amoris / Textus varii", "shelfmark": "M II 153", "repository": {"name": "Vědecká knihovna v Olomouci", "uri": "https://www.vkol.cz/", "settlement": "Olomouc", "country": "Česko"}, "catalogue": {"record_id": "vkol000759929", "agency": "CZ-OlVK", "reference": "Boháček 283", "former_shelfmarks": ["2 IV 25", "II d 25"], "source": "Katalogový záznam dodaný uživatelem 2026-10-12"}, "catalogue_title": "Stimulus amoris", "digitization_title": "Textus varii", "title_note_cs": "Katalogový název Stimulus amoris identifikuje záznam rukopisu; digitalizační popis Textus varii označuje širší obsah kodexu. Stimulus amoris je v popisu uveden na ff. 1r–36r.", "dating": {"notBefore": 1350, "notAfter": 1400, "source": "Dodaný digitalizační popis; nejde o nezávislé paleografické datování"}, "tei_version": "4.12.0", "tei": ORIGIN + "/tei/" + DOC + ".xml", "reader": ORIGIN + "/rukopis?doc=" + DOC, "identifier_authority": "Projektový identifikátor Manuscripty, nikoli PID přidělené knihovnou", "editorial_status": "Working research results without expert review", "metadata_source_sha256": digest(metadata_path)}
    identification_path = source / "document.json"
    identification = read(identification_path)
    doc["title"] = identification.get("display_title_cs", "M II 153 — Textus varii") + " / " + identification.get("descriptive_title_cs", "Sbírka různých textů")
    doc["title_note_cs"] = identification.get("title_note_cs", "Kodex obsahuje více děl; Textus varii je souhrnný název z digitalizačního XML, Stimulus amoris označuje jednu složku.")
    doc["alternative_titles"] = [{**t, "uri": t.get("source") if str(t.get("source", "")).startswith("https://") else None} for t in identification.get("alternative_catalogue_titles", [{"title": "Stimulus amoris", "source": "Katalogový záznam dodaný uživatelem", "record_id": "vkol000759929"}])]
    doc["external_catalogues"] = identification.get("external_catalogues", [])
    doc["provenance_claims"] = identification.get("provenance_claims", [])
    doc["provenance_note_cs"] = " ".join(c["claim_cs"] + "; podle " + c["source"] + ". Jde o katalogové tvrzení bez nezávislého ověření." for c in doc["provenance_claims"])
    doc["catalogue_reference_discrepancy_cs"] = identification.get("catalogue_reference_discrepancy_cs", "")
    doc["source_identification"] = identification
    if identification_path.exists():
        doc["identification_source_sha256"] = digest(identification_path)
    headers = []
    pages = []
    required_missing = []
    for entry in manifest:
        folio = entry["folio"]
        if entry.get('layout_correction_pending'):
            required_missing.append(folio + ': layout correction pending')
        if not re.fullmatch(r"[A-Za-z0-9_]+", folio):
            raise ValueError("Unsafe scan identifier: " + folio)
        src = source / "pages" / folio
        dest = out / "data" / DOC / folio
        dest.mkdir(parents=True, exist_ok=True)
        prefix = "/data/" + DOC + "/" + folio + "/"
        blank = bool(entry.get("blank_main_text", False))
        cp = src / "comparison.json"
        comparison = read(cp) if cp.exists() else {"lines": []}
        if not cp.exists() and not blank:
            required_missing.append(folio + ": comparison")
        lines = []
        for l in comparison["lines"]:
            candidates = l.get("candidates", l.get("htr_candidates", {}))
            if set(candidates) != {"catmus", "medusa"}:
                raise ValueError("Both models required for " + l["id"])
            lines.append({"id": l["id"], "source_segment_ids": [l["id"]], "bbox": l["bbox"], "image": MEDIA + "/crops/" + folio + "/" + l["id"] + ".webp", "raw_htr": {k: v["raw"] for k, v in candidates.items()}, "words": [], "flags": l.get("review_flags", []), "note": None, "hit_token_limit": candidates["medusa"].get("hit_token_limit", False)})
        if not lines and not blank:
            required_missing.append(folio + ": empty HTR without explicit no-main-text classification")
        ip = source / "interpretation" / (folio + ".json")
        if ip.exists():
            interpreted = read(ip)
            passages = adapt_interpretation(interpreted, lines)
        else:
            passages = []
            if lines:
                required_missing.append(folio + ": interpretation")
        downloads = []

        def copy_file(path, name, title, required=False):
            if path.exists():
                shutil.copy2(path, dest / name)
                if digest(path) != digest(dest / name):
                    raise ValueError("Copied source bytes changed: " + str(path))
                downloads.append({"name": title, "href": prefix + name})
            elif required:
                required_missing.append(folio + ": " + name)

        if cp.exists():
            copy_file(cp, "comparison.json", "Neupravené HTR a geometrie JSON")
        for model in ("catmus", "medusa"):
            copy_file(src / (model + ".raw.txt"), model + ".raw.txt", "Původní " + model + " TXT", bool(lines))
            for extension, label in (("tei.xml", "TEI P5 4.12.0"), ("alto.xml", "ALTO XML")):
                copy_file(source / "exports" / (folio + "-" + model + "." + extension), model + "." + extension, model + " · " + label + " (původní lokální export)", bool(lines))
                if extension == "tei.xml" and (dest / (model + ".tei.xml")).exists():
                    name = model + ".web.tei.xml"
                    make_web_tei(dest / (model + ".tei.xml"), dest / name, doc["reader"] + "#" + folio, validator)
                    web_tei_count += 1
                    downloads.append({"name": model + " · TEI s odkazy na webový prohlížeč", "href": prefix + name})
        if ip.exists():
            copy_file(ip, "reconstruction.json", "Rekonstrukce a překlad JSON")
            for suffix, name, label in (("tei.xml", "reconstruction.tei.xml", "Rekonstrukce a překlad TEI P5 4.12.0"), ("reconstruction.la.txt", "reconstruction.la.txt", "Rekonstrukce (jazyk předlohy) TXT"), ("translation.cs.txt", "translation.cs.txt", "Český překlad TXT")):
                copy_file(ip.with_name(folio + "." + suffix), name, label + (" (původní lokální export)" if suffix == "tei.xml" else ""), bool(lines))
                if suffix == "tei.xml" and (dest / name).exists():
                    make_web_tei(dest / name, dest / "reconstruction.web.tei.xml", doc["reader"] + "#" + folio, validator)
                    web_tei_count += 1
                    downloads.append({"name": "Rekonstrukce a překlad · TEI s odkazy na webový prohlížeč", "href": prefix + "reconstruction.web.tei.xml"})
        label = entry.get("label") or ({"FC":"Přední deska", "FS":"Přední přídeští", "BS":"Zadní přídeští", "BC":"Zadní deska", "SP":"Hřbet"}.get(folio) or ("f. " + folio if re.fullmatch(r"\d+[rv]", folio) else "Snímek " + folio))
        page = {"folio": folio, "label": label, "kind": "segments" if lines else "binding" if not re.fullmatch(r"\d+[rv]", folio) else "segments", "width": entry["width"], "height": entry["height"], "models": {"catmus": "CATMuS medieval 1.6.0", "medusa": "Medusa 0.2Line-4B"} if lines else {}, "source_sha256": entry["original_sha256"], "source_original": entry["original"], "source_fixity_md5_verified": entry.get("source_fixity_md5_verified", False), "source_integrity_note": entry.get("source_integrity_note"), "analysis_scope": "Původní HTR obou modelů po segmentech; samostatná slovní geometrie nebyla určena. Rekonstrukce a překlad jsou návrhy AI po smyslových úsecích.", "notes": interpreted.get("editorial_policy", {}).get("description_cs", "Pracovní návrhy bez odborné revize.") if ip.exists() else "Interpretace zatím není dostupná.", "lines": lines, "passages": passages, "preview": MEDIA + "/previews/" + folio + ".webp", "tiles": {"type": "dzi", "width": entry["width"], "height": entry["height"], "tileSize": 512, "tileOverlap": 1, "tilesUrl": MEDIA + "/tiles/" + folio + "/", "fileFormat": "webp"}, "blank": blank, "expert_review": False, "downloads": downloads, "document_id": DOC, "document_uri": doc["uri"], "repository": doc["repository"]}
        page["language"] = interpreted.get("language", "la") if ip.exists() else entry.get("language", "und")
        dump(dest / "page.json", page)
        pages.append(page)
        headers.append({"folio": folio, "label": label, "kind": page["kind"], "preview": page["preview"], "data": prefix + "page.json", "blank": blank, "segments": len(lines), "passages": len(passages)})
    if args.require_complete and required_missing:
        raise ValueError("Incomplete publication data: " + "; ".join(required_missing[:20]))
    counts = {"pages": len(pages), "lines": sum(len(p["lines"]) for p in pages), "passages": sum(len(p["passages"]) for p in pages), "blank": sum(p["blank"] for p in pages), "text_pages": sum(bool(p["lines"]) for p in pages)}
    doc["counts"] = counts
    description = str(counts["pages"]) + " snímků rukopisu M II 153. " + doc["title_note_cs"] + " Datace 1350–1400 pochází z dodaného popisu; Manuscripta.cz uvádí druhou polovinu 14. století. Původní HTR, rekonstrukce a český překlad jsou pracovní návrhy bez odborné revize."
    data = {"schema": "manuscripty-public-v1", "title": doc["title"], "scope": description, "description_cs": description, "processing_note": "Srovnání CATMuS medieval 1.6.0 a Medusa 0.2Line-4B po stejných fyzických segmentech; obrazové předzpracování se mezi modely liší. Vlastní rekonstrukce rozvádí zkratky a upravuje interpunkci; není diplomatickým přepisem. Český překlad používá smyslové úseky s odkazy na zdrojové řádky. Nevyřešená místa zůstávají označená.", "pages": headers, "counts": counts, "document": doc, "structure_url": "/data/" + DOC + "/structure.json", "summary_url": "/rukopisy/" + DOC + "/shrnuti", "publication_ready": bool(args.require_complete and not required_missing and len(pages) == 197)}
    dump(out / "data" / DOC / "manifest.json", data)
    dump(out / "data" / DOC / "document.json", doc)
    groups = []
    # Pages are partitioned into simple folio ranges; catalogue work boundaries
    # overlap and must not masquerade as an exclusive segmentation of the codex.
    for start in range(0, len(pages), 20):
        group = pages[start:start + 20]
        groups.append({"id": "scans_" + str(start + 1), "label": group[0]["label"] + " – " + group[-1]["label"], "pages": [{"folio": p["folio"], "label": p["label"], "kind": p["kind"], "blank": p["blank"], "source_sha256": p["source_sha256"], "passages": [{"id": v["id"], "title": v["title"], "line_id": v["line_ids"][0]} for v in p["passages"]]} for p in group]})
    dump(out / "data" / DOC / "structure.json", {"schema": "manuscripty-structure-v1", "status": "proposed", "expert_review": False, "basis": "Digitization catalogue ranges and AI passage titles", "counts": counts, "groups": groups, "catalogue_items": items})
    make_document_tei(out, doc, headers, items, validator)
    rows = "".join('<li><a href="/rukopis?doc=' + DOC + '#' + html.escape(i["from"]) + '">' + html.escape(i["title"]) + '</a> · ' + html.escape(i["from"] + "–" + i["to"]) + '</li>' for i in items)
    record = '<!doctype html><html lang="cs"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>' + html.escape(doc["title"]) + '</title><link rel="stylesheet" href="/styles.css?v=20261012-6"><link rel="canonical" href="' + doc["uri"] + '"></head><body><header class="site-header"><div class="container"><a class="brand" href="/">Rukopisy, snímek po snímku.</a></div></header><main class="container section"><h1>' + html.escape(doc["title"]) + '</h1><p>Rukopis z fondů <a href="https://www.vkol.cz/">Vědecké knihovny v Olomouci</a>.</p><p>' + html.escape(doc["title_note_cs"]) + '</p><p>Datace 1350–1400 podle dodaného digitalizačního popisu. Katalogový záznam vkol000759929 (CZ-OlVK); Boháček 283. Starší signatury: 2 IV 25, II d 25.</p><p class="sample-notice">Pracovní čtení, rekonstrukce a překlad jsou návrhy AI bez odborné revize. Shoda modelů ani validita XML nepotvrzují správnost četby.</p><div class="hero-actions"><a class="btn btn--primary" href="/rukopis?doc=' + DOC + '">Otevřít rukopis</a><a class="btn" href="/tei/' + DOC + '.xml">TEI P5 4.12.0 · popis a soupis snímků</a><a class="btn" href="/data/' + DOC + '/document.json">Metadata JSON</a></div><h2>Katalogový obsah kodexu</h2><p>Rozsahy pocházejí z dodaného digitalizačního XML; některá díla sdílejí stejné folio.</p><ol>' + rows + '</ol><p class="layer-id">Projektový stálý odkaz: ' + doc["uri"] + '</p></main></body></html>'
    title_sources = "".join('<li><strong>' + html.escape(t["title"]) + '</strong> — ' + ('<a href="' + html.escape(t["uri"], quote=True) + '">Manuscripta.cz</a>' if t.get("uri") else html.escape(str(t["source"]))) + '</li>' for t in doc["alternative_titles"])
    catalogue_notes = '<h2>Alternativní katalogové názvy a zdroje</h2><ul>' + title_sources + '</ul><p>' + html.escape(doc["catalogue_reference_discrepancy_cs"]) + '</p>'
    for catalogue in doc["external_catalogues"]:
        catalogue_notes += '<p>Katalogový odkaz uvedený na Manuscripta.cz: ' + html.escape(catalogue.get("catalogue_reference_verbatim", "")) + '. ' + html.escape(catalogue.get("catalogue_reference_note_cs", "")) + '</p>'
    if doc["provenance_note_cs"]:
        catalogue_notes += '<p>' + html.escape(doc["provenance_note_cs"]) + '</p>'
    record = record.replace('<h2>Katalogový obsah kodexu</h2>', catalogue_notes + '<h2>Katalogový obsah kodexu</h2>')
    from frontend_multi import decorate_record
    record=record.replace('u pilotních skenů','u všech 197 zdrojových TIFF')
    record=record.replace('<h2>Katalogový obsah kodexu</h2>','<p><a href="/rukopisy/'+DOC+'/shrnuti">AI shrnutí rukopisu</a></p><h2>Katalogový obsah kodexu</h2>')
    write(out / "rukopisy" / (DOC + ".html"), decorate_record(record,doc,description))
    homepage = (out / "index.html").read_text(encoding="utf-8").replace("{COUNT}", str(len(pages))).replace("{DOCUMENT_TITLE}", html.escape(doc["title"]))
    write(out / "index.html", homepage)
    from supplier_descriptions import update_descriptions
    update_descriptions(out)
    dump(report_dir / "build-report.json", {"status": "passed", "scope": "staged overlay only", "source": str(source), "output": str(out), "counts": counts, "publication_ready": data["publication_ready"], "required_missing": required_missing, "base_files_sha256": originals, "tei": {"version": "4.12.0", "validation": "Relax NG passed", "validated_web_documents": web_tei_count + 2, "schema_sha256": digest(args.rng), "web_facsimile_uri_semantics": "Public tiled viewer URI, not direct image resource; explained in encodingDesc"}, "images_in_pages_payload": False, "uploaded": False, "committed": False})
    print(json.dumps({"status": "passed", "counts": counts, "publication_ready": data["publication_ready"], "output": str(out)}))


def validate_paths(args):
    """Refuse destructive aliases/overlaps; nothing is deleted by this builder."""
    source, base, out, report = (p.resolve() for p in (args.source, args.base_public, args.out, args.report_dir))
    protected_dirs = [source, base, args.legacy_metadata.resolve()]
    if args.pilot_source is not None:
        protected_dirs.append(args.pilot_source.resolve())
    protected_files = [args.rng.resolve(), args.supplier_metadata.resolve()]
    for path in protected_dirs:
        if not path.is_dir():
            raise ValueError("Input directory does not exist: " + str(path))
    for path in protected_files:
        if not path.is_file():
            raise ValueError("Input file does not exist: " + str(path))
    for target in (out, report):
        if target == Path(target.anchor):
            raise ValueError("Output/report may not be a filesystem root")
        for original in protected_dirs:
            if target.is_relative_to(original) or original.is_relative_to(target):
                raise ValueError("Output/report overlaps a protected input directory: " + str(target))
        for original in protected_files:
            if original.is_relative_to(target) or target == original:
                raise ValueError("Output/report contains or aliases a protected input file")
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise ValueError("Output must be a new or empty directory; stale files are never deleted")
    if report.exists() and not report.is_dir():
        raise ValueError("Report destination must be a directory")


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("source", "base-public", "out", "rng", "supplier-metadata", "legacy-metadata", "report-dir"):
        p.add_argument("--" + name, type=Path, required=True)
    p.add_argument("--pilot-source", type=Path, help="Explicit original pilot root; required for inherited pilot provenance")
    p.add_argument("--require-complete", action="store_true", help="Require197scans, complete current interpretation provenance and all exports")
    return p


if __name__ == "__main__":
    build(parser().parse_args())
