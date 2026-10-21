"""Check the published text snapshot; no inference or paleographic validation."""
from pathlib import Path
import hashlib
import json
import re
from lxml import etree

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / 'web/public'
NS = {'t': 'http://www.tei-c.org/ns/1.0'}
parser = etree.XMLParser(resolve_entities=False, no_network=True)

def load(path):
    return json.loads(path.read_text(encoding='utf8'))

def require(condition, message):
    if not condition:
        raise ValueError(message)

def public_file(relative):
    # Public hrefs may be root-relative; filesystem resolution stays in public/.
    target = (PUBLIC / relative.lstrip('/')).resolve()
    require(target.is_relative_to(PUBLIC.resolve()), 'Path escapes public/: ' + relative)
    require(target.is_file(), 'Missing public text file: ' + relative)
    return target

record = load(ROOT / 'docs/web-source-manifest.json')
syntax = {'json': 0, 'xml': 0}
for item in record['files']:
    target = (ROOT / item['path']).resolve()
    require(target.is_relative_to(PUBLIC.resolve()), 'Invalid source manifest path')
    raw = target.read_bytes()
    require(len(raw) == item['bytes'] and hashlib.sha256(raw).hexdigest() == item['sha256'], 'Snapshot changed: ' + item['path'])
    if target.suffix == '.json':
        json.loads(raw)
        syntax['json'] += 1
    elif target.suffix in ('.xml', '.rng'):
        etree.fromstring(raw, parser)
        syntax['xml'] += 1

image_extensions = {'.tif', '.tiff', '.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp', '.jp2', '.avif', '.svg', '.ico'}
actual_text = {p.relative_to(ROOT).as_posix() for p in PUBLIC.rglob('*') if p.is_file() and not p.is_relative_to(PUBLIC / 'pagefind') and p.suffix.lower() not in image_extensions}
require(actual_text == {r['path'] for r in record['files']}, 'Unrecorded or missing public text files')
text = (PUBLIC / 'pilot-data.js').read_text(encoding='utf8')
manifest = json.loads(text.split('=', 1)[1].strip().rstrip(';'))
expected = {'pages': 677, 'folios': 670, 'binding': 7, 'text_pages': 664, 'lines': 50297, 'passages': 5634, 'blank': 6}
require(manifest['counts'] == expected, 'Unexpected public counts')
folios = {str(i) + side for i in range(1, 336) for side in ('r', 'v')}
bindings = {'FC', 'FS', 'F001r', 'F001v', 'BS', 'BC', 'SP'}
require({p['folio'] for p in manifest['pages']} == folios | bindings and len(manifest['pages']) == 677, 'Scan coverage or duplicate scan')
counts = dict.fromkeys(expected, 0)
counts['pages'] = len(manifest['pages'])
pages = {}
for entry in manifest['pages']:
    p = load(public_file(entry['data']))
    f = entry['folio']
    pages[f] = p
    require(p['folio'] == f and p['document_id'] == 'vkol-m-ii-220', 'Wrong page identity: ' + f)
    require(p['document_uri'] == manifest['document']['uri'] and p['repository']['name'] == 'Vědecká knihovna v Olomouci', 'Wrong holding institution: ' + f)
    require(p['expert_review'] is False and re.fullmatch('[a-f0-9]{64}', p['source_sha256']), 'Wrong provenance/review state: ' + f)
    if f in bindings:
        counts['binding'] += 1
        require(p['transcription_status'] == 'not_transcribed' and not p['lines'] and not p['passages'], 'Binding scan claims transcription')
    else:
        counts['folios'] += 1
        if p['blank']:
            counts['blank'] += 1
            require(not p['lines'] and not p['passages'], 'Blank main text has content')
        else:
            counts['text_pages'] += 1
            require(p['lines'] and p['passages'], 'Text page incomplete: ' + f)
    ids = {line['id'] for line in p['lines']}
    require(len(ids) == len(p['lines']), 'Duplicate line IDs: ' + f)
    for line in p['lines']:
        x, y, w, h = line['bbox']
        require(all(isinstance(v, int) and not isinstance(v, bool) for v in (x, y, w, h)) and x >= 0 and y >= 0 and w > 0 and h > 0 and x + w <= p['width'] and y + h <= p['height'], 'Out-of-bounds geometry: ' + line['id'])
        require(all(isinstance(line['raw_htr'].get(model), str) for model in ('catmus', 'medusa')), 'Missing HTR candidate: ' + line['id'])
    coverage = set()
    for passage in p['passages']:
        require(passage['latin'] and passage['czech'] and passage['line_ids'] and set(passage['line_ids']) <= ids, 'Invalid passage linkage: ' + f)
        coverage.update(passage['line_ids'])
    require(coverage == ids, 'Uncovered text segments: ' + f)
    for download in p['downloads']:
        public_file(download['href'])
    counts['lines'] += len(p['lines'])
    counts['passages'] += len(p['passages'])
require(counts == expected, 'Actual data counts disagree with manifest')
structure = load(PUBLIC / 'structure.json')
leaves = [p for g in structure['groups'] for p in g['pages']]
require(len(leaves) == 677 and {p['folio'] for p in leaves} == folios | bindings, 'Incomplete working structure')
require(sum(len(p['passages']) for p in leaves) == 5634, 'Incomplete structure passages')
rng = etree.RelaxNG(etree.parse(str(PUBLIC / 'schemas/tei-p5-4.12.0/tei_all.rng'), parser))
tei = etree.parse(str(PUBLIC / 'tei/vkol-m-ii-220.xml'), parser)
rng.assertValid(tei)
require(len(tei.findall('.//t:facsimile/t:surface', NS)) == 677, 'Incomplete whole-document TEI index')

# Keep the legacy acceptance checks above intact and check the second manuscript
# independently: its selected binding writing is part of the text-page count.
registry = load(ROOT / 'web/manuscripts.json')
require(registry['schema'] == 'manuscripty-static-registry-v1', 'Unexpected manuscript registry schema')
registered = registry['manuscripts']
require(len(registered) == 3 and {m['id'] for m in registered} == {'vkol-m-ii-220', 'vkol-m-ii-153', 'vkol-m-i-259'}, 'Expected exactly three registered manuscripts')
registry_by_id = {m['id']: m for m in registered}
require(all(m['default_model'] == 'catmus' for m in registered), 'Unexpected default HTR model')
require(registry_by_id['vkol-m-ii-220']['manifest'].lstrip('/') == 'pilot-data.js', 'Changed legacy registry manifest')
require(registry_by_id['vkol-m-ii-153']['manifest'].lstrip('/') == 'data/vkol-m-ii-153/manifest.json', 'Wrong M II 153 registry manifest')

manifest153 = load(public_file(registry_by_id['vkol-m-ii-153']['manifest']))
expected153 = {'pages': 197, 'lines': 15013, 'blank': 8, 'text_pages': 189}
require(manifest153['schema'] == 'manuscripty-public-v1' and manifest153['publication_ready'] is True, 'M II 153 is not a complete publication snapshot')
require(all(manifest153['counts'].get(k) == v for k, v in expected153.items()), 'Unexpected M II 153 public counts')
require(isinstance(manifest153['counts'].get('passages'), int) and not isinstance(manifest153['counts']['passages'], bool) and manifest153['counts']['passages'] > 0, 'Missing final M II 153 passage count')
folios153 = {str(i) + side for i in range(1, 97) for side in ('r', 'v')}
bindings153 = {'FC', 'FS', 'BC', 'BS', 'SP'}
scans153 = folios153 | bindings153
entries153 = manifest153['pages']
require(len(entries153) == 197 and {p['folio'] for p in entries153} == scans153, 'M II 153 scan coverage or duplicate scan')
document153 = manifest153['document']
require(document153['id'] == 'vkol-m-ii-153' and document153['repository']['name'] == 'Vědecká knihovna v Olomouci', 'Wrong M II 153 document identity/institution')
actual153 = {**dict.fromkeys(expected153, 0), 'passages': 0}
actual153['pages'] = len(entries153)
pages153 = {}
for entry in entries153:
    f = entry['folio']
    p = load(public_file(entry['data']))
    pages153[f] = p
    require(p['folio'] == f and p['document_id'] == 'vkol-m-ii-153', 'Wrong M II 153 page identity: ' + f)
    require(p['document_uri'] == document153['uri'] and p['repository']['name'] == 'Vědecká knihovna v Olomouci', 'Wrong M II 153 holding institution: ' + f)
    require(p['expert_review'] is False and re.fullmatch('[a-f0-9]{64}', p['source_sha256']), 'Wrong M II 153 provenance/review state: ' + f)
    require(isinstance(p['blank'], bool) and entry['blank'] == p['blank'], 'M II 153 blank state mismatch: ' + f)
    if p['blank']:
        actual153['blank'] += 1
        require(not p['lines'] and not p['passages'], 'M II 153 blank selected text has content: ' + f)
    else:
        actual153['text_pages'] += 1
        require(p['lines'] and p['passages'], 'M II 153 selected text incomplete: ' + f)
        reconstruction = load(public_file('data/vkol-m-ii-153/' + f + '/reconstruction.json'))
        require(reconstruction['status'] == 'proposed' and reconstruction['expert_review'] is False, 'M II 153 interpretation claims reviewed/final status: ' + f)
    ids = {line['id'] for line in p['lines']}
    require(len(ids) == len(p['lines']), 'Duplicate M II 153 line IDs: ' + f)
    for line in p['lines']:
        x, y, w, h = line['bbox']
        require(all(isinstance(v, int) and not isinstance(v, bool) for v in (x, y, w, h)) and x >= 0 and y >= 0 and w > 0 and h > 0 and x + w <= p['width'] and y + h <= p['height'], 'Out-of-bounds M II 153 geometry: ' + line['id'])
        require(all(isinstance(line['raw_htr'].get(model), str) for model in ('catmus', 'medusa')), 'Missing M II 153 HTR candidate: ' + line['id'])
    coverage = set()
    passage_ids = set()
    for passage in p['passages']:
        require(passage['id'] not in passage_ids, 'Duplicate M II 153 passage ID: ' + f)
        passage_ids.add(passage['id'])
        require(passage['latin'] and passage['czech'] and passage['line_ids'] and set(passage['line_ids']) <= ids, 'Invalid M II 153 passage linkage: ' + f)
        coverage.update(passage['line_ids'])
    require(coverage == ids, 'Uncovered M II 153 text segments: ' + f)
    require(entry['segments'] == len(p['lines']) and entry['passages'] == len(p['passages']), 'M II 153 header/data count mismatch: ' + f)
    require(p['downloads'], 'Missing M II 153 downloads: ' + f)
    download_paths = {d['href'].lstrip('/') for d in p['downloads']}
    for download in p['downloads']:
        public_file(download['href'])
    if p['lines']:
        prefix = 'data/vkol-m-ii-153/' + f + '/'
        require({prefix + n for n in ('comparison.json', 'catmus.raw.txt', 'medusa.raw.txt', 'reconstruction.json', 'reconstruction.la.txt', 'translation.cs.txt')} <= download_paths, 'Missing M II 153 source/interpretation download: ' + f)
    actual153['lines'] += len(p['lines'])
    actual153['passages'] += len(p['passages'])
require(all(actual153[k] == v for k, v in expected153.items()) and actual153['passages'] == manifest153['counts']['passages'], 'Actual M II 153 data counts disagree with final manifest')
structure153 = load(public_file(manifest153['structure_url']))
require(structure153['status'] == 'proposed' and structure153['expert_review'] is False, 'M II 153 structure claims reviewed/final status')
require(structure153['counts'] == manifest153['counts'], 'M II 153 structure/manifest counts differ')
leaves153 = [p for g in structure153['groups'] for p in g['pages']]
require(len(leaves153) == 197 and {p['folio'] for p in leaves153} == scans153, 'Incomplete M II 153 working structure')
require(sum(len(p['passages']) for p in leaves153) == actual153['passages'], 'Incomplete M II 153 structure passages')
for leaf in leaves153:
    p = pages153[leaf['folio']]
    require(leaf['blank'] == p['blank'] and leaf['source_sha256'] == p['source_sha256'], 'M II 153 structure/page provenance mismatch: ' + p['folio'])
    require({v['id'] for v in leaf['passages']} == {v['id'] for v in p['passages']} and len(leaf['passages']) == len(p['passages']), 'M II 153 structure/page passage mismatch: ' + p['folio'])
    require(all(v['line_id'] in {line['id'] for line in p['lines']} for v in leaf['passages']), 'Invalid M II 153 structure line link: ' + p['folio'])
tei153 = etree.parse(str(public_file('tei/vkol-m-ii-153.xml')), parser)
rng.assertValid(tei153)
scan_divs153 = tei153.findall('.//t:text/t:body/t:div[@type="scan"]', NS)
require(len(scan_divs153) == 197 and {div.get('n') for div in scan_divs153} == scans153, 'Incomplete M II 153 whole-document TEI scan index')


# M I 259 has an independent acceptance corpus. Its scan IDs are physical
# inventory identifiers, including the two additional scans, not proved foliation.
require(registry_by_id['vkol-m-i-259']['manifest'].lstrip('/') == 'data/vkol-m-i-259/manifest.json', 'Wrong M I 259 registry manifest')
order259 = ['FC', 'FS', 'F001R', 'F001V']
for n in range(1, 181):
    for side in ('r', 'v'):
        f = str(n) + side
        order259.append(f)
        if f in ('83v', '84r'):
            order259.append('extra-' + f)
order259 += ['B001R', 'B001V', 'BS', 'BC', 'SP']
manifest259 = load(public_file(registry_by_id['vkol-m-i-259']['manifest']))
require(manifest259['schema'] == 'manuscripty-public-v1' and manifest259['publication_ready'] is True, 'M I 259 is not a complete publication snapshot')
entries259 = manifest259['pages']
require(len(entries259) == 371 and [p['folio'] for p in entries259] == order259, 'M I 259 scan order/coverage or duplicate scan')
document259 = manifest259['document']
require(document259['id'] == 'vkol-m-i-259' and document259['repository']['name'] == 'Vědecká knihovna v Olomouci', 'Wrong M I 259 document identity/institution')
actual259 = dict.fromkeys(('pages', 'lines', 'passages', 'blank', 'text_pages', 'supplemental_readings'), 0)
actual259['pages'] = len(entries259)
pages259 = {}
masked259 = set()
rotation259 = {'FS': 90, 'B001R': 90, 'BS': 90, 'B001V': 270}
coordinate_ids259 = set()
for entry in entries259:
    f = entry['folio']
    prefix = 'data/vkol-m-i-259/' + f + '/'
    require(entry['data'].lstrip('/') == prefix + 'page.json', 'Wrong M I 259 page URL: ' + f)
    p = load(public_file(entry['data']))
    pages259[f] = p
    require(p['folio'] == f and p['document_id'] == 'vkol-m-i-259' and p['document_uri'] == document259['uri'], 'Wrong M I 259 page identity: ' + f)
    require(p['repository'] == document259['repository'], 'Wrong M I 259 holding institution: ' + f)
    require(p['expert_review'] is False and isinstance(p['source_sha256'], str) and re.fullmatch('[a-f0-9]{64}', p['source_sha256']), 'Wrong M I 259 provenance/review state: ' + f)
    require(isinstance(p['source_original'], str) and re.fullmatch(r'EX/[^/\\]+\.[Tt][Ii][Ff][Ff]?', p['source_original']), 'Missing M I 259 archival TIFF identity: ' + f)
    require(all(isinstance(p[k], int) and not isinstance(p[k], bool) and p[k] > 0 for k in ('width', 'height')), 'Invalid M I 259 raster dimensions: ' + f)
    c = p['coordinate_source']
    require(c['id'] not in coordinate_ids259 and c['id'] == 'vkol-m-i-259_' + f + '_coordinate', 'Duplicate/missing M I 259 coordinate raster ID: ' + f)
    coordinate_ids259.add(c['id'])
    require(c['derived_from_sha256'] == p['source_sha256'] and re.fullmatch('[a-f0-9]{64}', c['sha256']), 'M I 259 coordinate/TIFF hash mismatch: ' + f)
    require((c['width'], c['height']) == (p['width'], p['height']) and c['frame'] == 0 and c['original_tiff_frame'] == 0 and c['bbox_format'] == 'xywh' and c['origin'] == 'top-left', 'Wrong M I 259 coordinate space: ' + f)
    rotation = rotation259.get(f, 0)
    affine = {0: [[1, 0, 0], [0, 1, 0], [0, 0, 1]], 90: [[0, 1, 0], [-1, 0, c['height']], [0, 0, 1]], 180: [[-1, 0, c['width']], [0, -1, c['height']], [0, 0, 1]], 270: [[0, -1, c['width']], [1, 0, 0], [0, 0, 1]]}
    require(c['rotation_ccw_degrees'] == rotation and c['source_to_coordinate_pixel_edge_affine'] == affine[rotation], 'Wrong M I 259 TIFF-to-coordinate pixel-edge affine: ' + f)
    require('model_input' not in c, 'M I 259 coordinate raster conflates model input: ' + f)
    model_input = p['model_input']
    require(isinstance(model_input, dict) and re.fullmatch('[a-f0-9]{64}', model_input['sha256']) and isinstance(model_input['masked_pilot'], bool), 'Missing M I 259 separate model-input provenance: ' + f)
    require(isinstance(model_input['operation'], str) and model_input['operation'], 'Missing M I 259 model-input operation: ' + f)
    mx, my, mx1, my1 = model_input['reading_zone_xyxy']
    require(all(isinstance(v, int) and not isinstance(v, bool) for v in (mx, my, mx1, my1)) and 0 <= mx < mx1 <= p['width'] and 0 <= my < my1 <= p['height'], 'Invalid M I 259 model-input reading zone: ' + f)
    if model_input['masked_pilot']:
        masked259.add(f)
        require(model_input['sha256'] != c['sha256'], 'M I 259 mask hash used as full coordinate raster: ' + f)
    else:
        require(model_input['sha256'] == c['sha256'] and model_input['reading_zone_xyxy'] == [0, 0, p['width'], p['height']], 'M I 259 full model input differs from coordinate raster: ' + f)
    require(isinstance(p['blank'], bool) and entry['blank'] == p['blank'] and p['blank'] == (not p['lines']), 'M I 259 blank state mismatch: ' + f)
    actual259['blank' if p['blank'] else 'text_pages'] += 1
    comparison = load(public_file(prefix + 'comparison.json'))
    reconstruction = load(public_file(prefix + 'reconstruction.json'))
    evidence = load(public_file(prefix + 'evidence.json'))
    require(comparison['folio'] == f and comparison['expert_review'] is False and comparison['coordinate_source'] == c and comparison['source_original'] == p['source_original'] and comparison['source_sha256'] == p['source_sha256'], 'M I 259 comparison provenance mismatch: ' + f)
    require(reconstruction['folio'] == f and reconstruction['status'] == 'proposed' and reconstruction['expert_review'] is False and evidence['folio'] == f and evidence['status'] == 'proposed' and evidence['expert_review'] is False, 'M I 259 interpretation/evidence identity or review state: ' + f)
    fingerprint = hashlib.sha256(json.dumps([[r['bbox_xyxy'], r['boundary'], r['baseline']] for r in comparison['lines']], sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    require(comparison['geometry_fingerprint'] == reconstruction['geometry_fingerprint'] == evidence['geometry_fingerprint'] == fingerprint, 'M I 259 geometry/evidence fingerprint mismatch: ' + f)
    require(all(re.fullmatch('[a-f0-9]{64}', evidence[k]) for k in ('author_sha256', 'inspection_sha256')), 'Missing M I 259 author/inspection evidence hash: ' + f)
    line_order = [line['id'] for line in p['lines']]
    ids = set(line_order)
    require(len(ids) == len(line_order) and [r['id'] for r in comparison['lines']] == line_order, 'M I 259 duplicate/mismatched line IDs: ' + f)
    if p.get('reading_addenda'):
        appendix = load(public_file(prefix + 'reading-addenda.json'))
        require(appendix['schema'] == 'manuscripty-reading-addenda-v1' and appendix['document_id'] == 'vkol-m-i-259' and appendix['folio'] == f and appendix['status'] == 'proposed' and appendix['expert_review'] is False, 'Invalid addendum identity/review state: ' + f)
        require(appendix['readings'] == p['reading_addenda'] and len(appendix['readings']) == 1, 'Addendum download/page mismatch: ' + f)
        reading = appendix['readings'][0]
        require(reading['status'] == 'proposed' and reading['expert_review'] is False and reading['line_ids'] and set(reading['line_ids']) <= ids and set(reading['target_line_ids']) <= set(reading['line_ids']), 'Invalid addendum line/review linkage: ' + f)
        require(reading['source_review_sha256'] == hashlib.sha256((ROOT / 'docs/experiments/2026-10-21-medusa-five/report.json').read_bytes()).hexdigest(), 'Addendum evidence changed: ' + f)
        require(reading['source_image_sha256'] == next(r['image_sha256'] for r in comparison['lines'] if r['id'] == reading['target_line_ids'][0]), 'Addendum source crop identity changed: ' + f)
        appendix_tei = etree.parse(str(public_file(prefix + 'reading-addenda.tei.xml')), parser)
        rng.assertValid(appendix_tei)
        require(appendix_tei.getroot().get('version') == '4.12.0' and appendix_tei.xpath('//t:supplied[@reason="conjecture"][@cert="low"]', namespaces=NS), 'Addendum TEI must mark conjecture: ' + f)
        for kind, value in [('reconstruction', reading['reconstruction']), ('translation', reading['translation_cs'])]:
            element = appendix_tei.xpath('//t:div[@type="reading_addendum"]/t:ab[@type="' + kind + '"]', namespaces=NS)
            require(len(element) == 1 and ''.join(element[0].itertext()) == value, 'Addendum TEI text differs: ' + f)
        require({prefix + n for n in ('reading-addenda.json', 'reading-addenda.tei.xml', 'reading-addenda.reconstruction.txt', 'reading-addenda.translation.cs.txt')} <= {d['href'].lstrip('/') for d in p['downloads']}, 'Addendum downloads missing: ' + f)
    for line, raw in zip(p['lines'], comparison['lines']):
        if 'neighboring_leaf_fragment' in line.get('flags', []):
            annotation = line['editorial_annotation']
            require(annotation['classification'] == 'partial_neighboring_leaf' and annotation['status'] == 'proposed' and annotation['expert_review'] is False, 'Invalid neighboring-leaf classification/review state: ' + line['id'])
            review_path = ROOT / 'docs/experiments/2026-10-21-medusa-five/report.json'
            require(annotation['evidence_review_sha256'] == hashlib.sha256(review_path.read_bytes()).hexdigest() and annotation['source_crop_sha256'] == raw['image_sha256'], 'Changed neighboring-leaf evidence: ' + line['id'])
            require(any(row['id'] == line['id'] and row['classification'] == 'partial_neighboring_leaf' for row in load(review_path)['rows']), 'Classification lacks source review: ' + line['id'])
        x, y, w, h = line['bbox']
        require(all(isinstance(v, int) and not isinstance(v, bool) for v in (x, y, w, h)) and x >= 0 and y >= 0 and w > 0 and h > 0 and x + w <= p['width'] and y + h <= p['height'], 'Out-of-bounds M I 259 geometry: ' + line['id'])
        require(raw['bbox_xyxy'] == [x, y, x + w, y + h] and line['source_segment_ids'] == [line['id']], 'Changed M I 259 source segment geometry/identity: ' + line['id'])
        require(set(line['raw_htr']) == {'catmus', 'medusa'} and all(isinstance(line['raw_htr'][model], str) and line['raw_htr'][model] == raw['candidates'][model]['raw'] for model in ('catmus', 'medusa')), 'Changed M I 259 HTR candidate Unicode: ' + line['id'])
    require(len({v['id'] for v in p['passages']}) == len(p['passages']), 'Duplicate M I 259 passage ID: ' + f)
    coverage = []
    require(len(p['passages']) == len(reconstruction['units']), 'M I 259 interpretation unit count mismatch: ' + f)
    unit_indices = []
    for passage, unit in zip(p['passages'], reconstruction['units']):
        require(passage['latin'] and passage['czech'] and passage['line_ids'] and set(passage['line_ids']) <= ids, 'Invalid M I 259 passage linkage: ' + f)
        require(passage['line_ids'] == line_order[unit['start'] - 1:unit['end']] and passage['latin'] == unit['reconstruction'] and passage['czech'] == unit['translation_cs'], 'Changed M I 259 interpretation range/text: ' + f)
        coverage.extend(passage['line_ids'])
        unit_indices.extend(range(unit['start'], unit['end'] + 1))
    require(coverage == line_order and unit_indices == list(range(1, len(line_order) + 1)), 'Uncovered, overlapping or reordered M I 259 text segments: ' + f)
    supplemental = p['supplemental_readings']
    require(len({v['id'] for v in supplemental}) == len(supplemental) and not ({v['id'] for v in supplemental} & ids), 'M I 259 supplemental/HTR ID collision: ' + f)
    original_supplemental = reconstruction.get('supplemental_readings', [])
    require(len(supplemental) == len(original_supplemental), 'M I 259 supplemental count mismatch: ' + f)
    for reading, original in zip(supplemental, original_supplemental):
        require(reading['status'] == 'proposed' and reading['expert_review'] is False and 'raw_htr' not in reading and 'line_ids' not in reading, 'M I 259 supplemental reading claims HTR/review: ' + f)
        require(all(reading[k] == original[k] for k in ('id', 'source_region_xyxy', 'crop_rotation_ccw_degrees', 'reconstruction', 'translation_cs', 'note_cs')), 'Changed M I 259 supplemental reading: ' + f)
        x, y, x1, y1 = reading['source_region_xyxy']
        require(all(isinstance(v, int) and not isinstance(v, bool) for v in (x, y, x1, y1)) and 0 <= x < x1 <= p['width'] and 0 <= y < y1 <= p['height'] and reading['crop_rotation_ccw_degrees'] in (0, 90, 180, 270), 'Invalid M I 259 supplemental geometry: ' + f)
    require(entry['segments'] == len(p['lines']) and entry['passages'] == len(p['passages']) and entry['supplemental_readings'] == len(supplemental), 'M I 259 header/data count mismatch: ' + f)
    required_downloads = {prefix + name for name in ('comparison.json', 'catmus.raw.txt', 'medusa.raw.txt', 'catmus.alto.xml', 'medusa.alto.xml', 'edition.tei.xml', 'edition.web.tei.xml', 'reconstruction.json', 'reconstruction.txt', 'translation.cs.txt', 'evidence.json')}
    require(required_downloads <= {d['href'].lstrip('/') for d in p['downloads']}, 'Missing M I 259 source/interpretation download: ' + f)
    for download in p['downloads']:
        public_file(download['href'])
    for model in ('catmus', 'medusa'):
        require(public_file(prefix + model + '.raw.txt').read_bytes().decode('utf8') == '\n'.join(line['raw_htr'][model] for line in p['lines']), 'M I 259 raw TXT identity differs: ' + f + '/' + model)
    actual259['lines'] += len(p['lines'])
    actual259['passages'] += len(p['passages'])
    actual259['supplemental_readings'] += len(supplemental)
require(actual259 == manifest259['counts'] == document259['counts'] and actual259['supplemental_readings'] == 3, 'Actual M I 259 counts disagree with complete manifest')
require(masked259 == {'1r', '14r', '18r', '25r', '46r', '62r', '88r', '100r', '135r', '145r'}, 'Wrong M I 259 masked-pilot inventory')
structure259 = load(public_file(manifest259['structure_url']))
require(structure259['status'] == 'proposed' and structure259['expert_review'] is False and structure259['counts'] == actual259, 'Wrong M I 259 structure state/counts')
leaves259 = [p for g in structure259['groups'] for p in g['pages']]
require([p['folio'] for p in leaves259] == order259, 'Incomplete/reordered M I 259 working structure')
for leaf in leaves259:
    p = pages259[leaf['folio']]
    require(leaf['blank'] == p['blank'] and leaf['source_sha256'] == p['source_sha256'], 'M I 259 structure/page provenance mismatch: ' + p['folio'])
    require([v['id'] for v in leaf['passages']] == [v['id'] for v in p['passages']] and [v['line_id'] for v in leaf['passages']] == [v['line_ids'][0] for v in p['passages']], 'M I 259 structure/page passage linkage mismatch: ' + p['folio'])
tei259 = etree.parse(str(public_file('tei/vkol-m-i-259.xml')), parser)
require(tei259.getroot().get('version') == '4.12.0', 'Wrong M I 259 whole-document TEI version')
rng.assertValid(tei259)
surfaces259 = tei259.findall('.//t:facsimile/t:surface', NS)
require(len(surfaces259) == 371 and [surface.get('n') for surface in surfaces259] == order259, 'Incomplete/reordered M I 259 whole-document TEI surface index')

report = {'status': 'passed', 'copied_files_sha256_verified': len(record['files']), 'bytes': sum(f['bytes'] for f in record['files']), 'syntax': syntax,
          'counts': counts, 'bbox_checked': counts['lines'], 'whole_document_tei_relaxng': 'passed', 'expert_review': False,
          'registry_manuscripts': len(registered),
          'manuscripts': {'vkol-m-ii-220': {'counts': counts, 'bbox_checked': counts['lines'], 'whole_document_tei_relaxng': 'passed', 'tei_surface_count': 677},
                          'vkol-m-ii-153': {'counts': actual153, 'folios': len(folios153), 'binding_scans': len(bindings153), 'bbox_checked': actual153['lines'], 'whole_document_tei_relaxng': 'passed', 'tei_scan_div_count': len(scan_divs153), 'interpretation_status': 'proposed'},
                          'vkol-m-i-259': {'counts': actual259, 'bbox_checked': actual259['lines'], 'raw_candidate_unicode_and_txt': 'passed', 'coordinate_source_and_affine': 'passed', 'masked_pilot_pages': len(masked259), 'supplemental_readings_separate': actual259['supplemental_readings'], 'whole_document_tei_relaxng': 'passed', 'tei_surface_count': len(surfaces259), 'interpretation_status': 'proposed'}},
          'scope': 'Text snapshot integrity, syntax, page/download/passage links, geometry and whole-document TEI index. Not new image inspection or full schema revalidation of every existing edition.'}
(ROOT / 'docs/validation/repository-snapshot-validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf8', newline='\n')
print(json.dumps(report, ensure_ascii=False))
