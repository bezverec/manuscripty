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
    target = (PUBLIC / relative).resolve()
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
actual_text = {p.relative_to(ROOT).as_posix() for p in PUBLIC.rglob('*') if p.is_file() and p.suffix.lower() not in image_extensions}
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
report = {'status': 'passed', 'copied_files_sha256_verified': len(record['files']), 'bytes': sum(f['bytes'] for f in record['files']), 'syntax': syntax,
          'counts': counts, 'bbox_checked': counts['lines'], 'whole_document_tei_relaxng': 'passed', 'expert_review': False,
          'scope': 'Text snapshot integrity, syntax, page/download/passage links, geometry and whole-document TEI index. Not new image inspection or full schema revalidation of every existing edition.'}
(ROOT / 'docs/validation/repository-snapshot-validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
print(json.dumps(report, ensure_ascii=False))
