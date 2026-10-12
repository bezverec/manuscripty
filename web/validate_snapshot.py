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
require(len(registered) == 2 and {m['id'] for m in registered} == {'vkol-m-ii-220', 'vkol-m-ii-153'}, 'Expected exactly two registered manuscripts')
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

report = {'status': 'passed', 'copied_files_sha256_verified': len(record['files']), 'bytes': sum(f['bytes'] for f in record['files']), 'syntax': syntax,
          'counts': counts, 'bbox_checked': counts['lines'], 'whole_document_tei_relaxng': 'passed', 'expert_review': False,
          'registry_manuscripts': len(registered),
          'manuscripts': {'vkol-m-ii-220': {'counts': counts, 'bbox_checked': counts['lines'], 'whole_document_tei_relaxng': 'passed', 'tei_surface_count': 677},
                          'vkol-m-ii-153': {'counts': actual153, 'folios': len(folios153), 'binding_scans': len(bindings153), 'bbox_checked': actual153['lines'], 'whole_document_tei_relaxng': 'passed', 'tei_scan_div_count': len(scan_divs153), 'interpretation_status': 'proposed'}},
          'scope': 'Text snapshot integrity, syntax, page/download/passage links, geometry and whole-document TEI index. Not new image inspection or full schema revalidation of every existing edition.'}
(ROOT / 'docs/validation/repository-snapshot-validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf8', newline='\n')
print(json.dumps(report, ensure_ascii=False))
