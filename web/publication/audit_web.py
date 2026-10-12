"""Read-only data, namespace, download, link and baseline audit of a web overlay.

All input roots are explicit. This does not contact live media, deploy, or certify
paleographic accuracy. Failure reports contain paths/messages, never secret text.
"""
import argparse
import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, unquote
from lxml import etree as ET

DOC = 'vkol-m-ii-153'
MEDIA = 'https://rukopisy-data.digitalizaty.cz/v2/' + DOC + '/'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def member(root, relative):
    result = (root / relative).resolve()
    require(result.is_relative_to(root), 'Path escapes its declared root')
    return result


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []
        self.ids = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        for key in ('href', 'src'):
            if key in attrs:
                self.urls.append(attrs[key])


def report_path(report_dir, source, base, staged):
    report_dir = report_dir.resolve()
    for root in (source, base, staged):
        require(not report_dir.is_relative_to(root) and not root.is_relative_to(report_dir),
                'Report directory overlaps a read-only input root')
    report_dir.mkdir(parents=True, exist_ok=True)
    return report_dir / 'audit-report.json'


def audit(source, base, staged, build_report):
    source, base, staged, build_report = [Path(p).resolve() for p in (source, base, staged, build_report)]
    for root in (source, base, staged):
        require(root.is_dir(), 'Missing input directory: ' + str(root))
    build = read(build_report)
    require(build['status'] == 'passed', 'Build report did not pass')
    require(Path(build['source']).resolve() == source and Path(build['output']).resolve() == staged,
            'Build report belongs to different declared input/output')
    hashes = build['base_files_sha256']
    require(bool(hashes), 'Empty baseline SHA inventory')
    for name, expected in hashes.items():
        require(sha(member(base, name)) == expected, 'Baseline changed: ' + name)

    manifest = read(staged / ('data/' + DOC + '/manifest.json'))
    source_manifest = read(source / 'manifest.json')['pages']
    require([p['folio'] for p in manifest['pages']] == [p['folio'] for p in source_manifest],
            'Missing, reordered or additional source pages')
    require(len({p['folio'] for p in manifest['pages']}) == len(source_manifest), 'Duplicate page IDs')
    require(manifest['document']['id'] == DOC, 'Incorrect document ID')
    require(build['publication_ready'] == manifest['publication_ready'], 'Publication readiness mismatch')
    if manifest['publication_ready']:
        require(len(source_manifest) == 197 and not build['required_missing'], 'Incomplete publication')

    examined = downloads = interpreted_pages = 0
    required_names = {'comparison.json', 'catmus.raw.txt', 'medusa.raw.txt',
                      'catmus.tei.xml', 'medusa.tei.xml', 'catmus.alto.xml', 'medusa.alto.xml',
                      'catmus.web.tei.xml', 'medusa.web.tei.xml', 'reconstruction.json',
                      'reconstruction.tei.xml', 'reconstruction.web.tei.xml',
                      'reconstruction.la.txt', 'translation.cs.txt'}
    copy_pairs = [('catmus.raw.txt', 'catmus.raw.txt', 'page'), ('medusa.raw.txt', 'medusa.raw.txt', 'page'),
                  ('comparison.json', 'comparison.json', 'page')]
    for header, source_entry in zip(manifest['pages'], source_manifest):
        folio = header['folio']
        require(re.fullmatch(r'[A-Za-z0-9_]+', folio), 'Unsafe folio identifier')
        prefix = '/data/' + DOC + '/' + folio + '/'
        require(header['data'] == prefix + 'page.json', 'Incorrect page namespace: ' + folio)
        page = read(member(staged, header['data'].lstrip('/')))
        cp = source / 'pages' / folio / 'comparison.json'
        raw = read(cp) if cp.exists() else {'lines': []}
        require(len(raw['lines']) == len(page['lines']) == header['segments'], 'Segment count mismatch: ' + folio)
        require(page['document_id'] == DOC and page['folio'] == folio, 'Page identity mismatch: ' + folio)
        require(page['source_sha256'] == source_entry['original_sha256'], 'Source SHA mismatch: ' + folio)
        require(page['width'] == source_entry['width'] and page['height'] == source_entry['height'], 'Source dimensions changed: ' + folio)
        require(page['preview'] == MEDIA + 'previews/' + folio + '.webp', 'Preview namespace mismatch: ' + folio)
        require(page['tiles']['tilesUrl'] == MEDIA + 'tiles/' + folio + '/', 'Tiles namespace mismatch: ' + folio)
        ids = [line['id'] for line in raw['lines']]
        require(len(set(ids)) == len(ids), 'Duplicate source segment IDs: ' + folio)
        for before, after in zip(raw['lines'], page['lines']):
            label = folio + '/' + before['id']
            require(before['id'] == after['id'], 'Segment ID changed: ' + label)
            require(before['bbox'] == after['bbox'], 'Bounding box changed: ' + label)
            require(after['source_segment_ids'] == [before['id']], 'Source ID linkage changed: ' + label)
            candidates = before.get('candidates', before.get('htr_candidates', {}))
            require(set(candidates) == set(after['raw_htr']) == {'catmus', 'medusa'}, 'Both model outputs required: ' + label)
            for model in ('catmus', 'medusa'):
                require(candidates[model]['raw'] == after['raw_htr'][model], 'Raw HTR changed: ' + label + '/' + model)
            require(after['image'] == MEDIA + 'crops/' + folio + '/' + before['id'] + '.webp', 'Crop namespace mismatch: ' + label)
            examined += 1
        covered = {i for passage in page['passages'] for i in passage['line_ids']}
        require(covered == set(ids), 'Interpretation does not cover exact source ID set: ' + folio)
        for passage in page['passages']:
            require(bool(passage['line_ids']), 'Passage without source IDs: ' + folio)
            require(bool(passage.get('czech', '').strip()), 'Missing Czech translation: ' + folio)
            require(bool(passage.get('latin', '').strip()), 'Missing reconstruction: ' + folio)
        interpreted_pages += bool(ids and page['passages'])
        names = set()
        for download in page['downloads']:
            href = download['href']
            require(href.startswith(prefix), 'Download namespace mismatch: ' + folio)
            require(member(staged, href.lstrip('/')).is_file(), 'Missing download: ' + href)
            require(Path(href).name not in names, 'Duplicate download name: ' + href)
            names.add(Path(href).name)
            downloads += 1
        if ids and manifest['publication_ready']:
            require(required_names <= names, 'Required downloads missing: ' + folio)
        for src_name, dst_name, _ in copy_pairs:
            src = source / 'pages' / folio / src_name
            dst = staged / ('data/' + DOC) / folio / dst_name
            if src.exists():
                require(dst.is_file() and sha(src) == sha(dst), 'Copied raw source bytes changed: ' + folio + '/' + src_name)
        for model in ('catmus', 'medusa'):
            for extension in ('tei.xml', 'alto.xml'):
                src = source / 'exports' / (folio + '-' + model + '.' + extension)
                dst = staged / ('data/' + DOC) / folio / (model + '.' + extension)
                if src.exists():
                    require(dst.is_file() and sha(src) == sha(dst), 'Copied model export bytes changed: ' + folio + '/' + model + '.' + extension)
        for suffix, name in [('.json', 'reconstruction.json'), ('.tei.xml', 'reconstruction.tei.xml'),
                             ('.reconstruction.la.txt', 'reconstruction.la.txt'), ('.translation.cs.txt', 'translation.cs.txt')]:
            src = source / 'interpretation' / (folio + suffix)
            dst = staged / ('data/' + DOC) / folio / name
            if src.exists():
                require(dst.is_file() and sha(src) == sha(dst), 'Copied interpretation bytes changed: ' + folio + '/' + name)
    require(examined == manifest['counts']['lines'] == build['counts']['lines'], 'Total segment count mismatch')
    if manifest['publication_ready']:
        require(examined == 15013, 'Expected final M II 153 source count is 15013')

    # Underlying legacy data/exports must stay untouched in the new overlay.
    legacy_code = (base / 'pilot-data.js').read_text(encoding='utf8')
    staged_code = (staged / 'pilot-data.js').read_text(encoding='utf8')
    def legacy_data(code):
        match = re.fullmatch(r'window\.PILOT_DATA\s*=\s*(\{.*\});\s*', code, re.S)
        require(match is not None, 'Unexpected legacy manifest syntax')
        return json.loads(match.group(1))
    old, new = legacy_data(legacy_code), legacy_data(staged_code)
    require(old['pages'] == new['pages'] and old['counts'] == new['counts'], 'Legacy pages/counts changed')
    require(len(new['pages']) == 677, 'Legacy page inventory changed')
    parser = ET.XMLParser(resolve_entities=False, no_network=True)
    old_tei = ET.parse(str(base / 'tei/vkol-m-ii-220.xml'), parser)
    new_tei = ET.parse(str(staged / 'tei/vkol-m-ii-220.xml'), parser)
    ns = {'t': 'http://www.tei-c.org/ns/1.0'}
    require(ET.tostring(old_tei.find('t:text', ns), method='c14n') ==
            ET.tostring(new_tei.find('t:text', ns), method='c14n'), 'Legacy TEI text changed')
    legacy_files = 0
    legacy_digest = hashlib.sha256()
    for root_name in ('data', 'txt', 'alto', 'tei'):
        directory = base / root_name
        if not directory.exists():
            continue
        for file in sorted(directory.rglob('*')):
            if not file.is_file():
                continue
            relative = file.relative_to(base).as_posix()
            digest = sha(file)
            legacy_digest.update((relative + '\0' + digest + '\n').encode('utf8'))
            overlay_file = staged / relative
            if overlay_file.exists() and relative != 'tei/vkol-m-ii-220.xml':
                require(sha(overlay_file) == digest, 'Legacy underlying data overwritten: ' + relative)
            legacy_files += 1

    links = 0
    for file in staged.rglob('*.html'):
        parser = Links()
        parser.feed(file.read_text(encoding='utf-8'))
        require(len(parser.ids) == len(set(parser.ids)), 'Duplicate HTML IDs: ' + str(file.relative_to(staged)))
        for href in parser.urls:
            url = urlparse(href)
            if url.scheme or url.netloc or not url.path:
                continue
            relative = Path(unquote(url.path).lstrip('/')) if url.path.startswith('/') else file.relative_to(staged).parent / unquote(url.path)
            candidates = []
            for root in (staged, base):
                target = member(root, relative)
                candidates.extend([target, Path(str(target) + '.html'), target / 'index.html'])
            require(any(p.is_file() for p in candidates), 'Missing local link: ' + str(file.relative_to(staged)) + ' -> ' + href)
            links += 1

    forbidden = []
    credential = re.compile(r'(?:AKIA[0-9A-Z]{16}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|gh[pousr]_[A-Za-z0-9_]{30,}|github_pat_[A-Za-z0-9_]{40,}|sk-proj-[A-Za-z0-9_-]{30,})')
    scanned = 0
    for file in staged.rglob('*'):
        if not file.is_file():
            continue
        rel = file.relative_to(staged).as_posix()
        name = file.name.lower()
        if file.suffix.lower() in ('.tif', '.tiff', '.png', '.jpg', '.jpeg', '.webp', '.safetensors', '.mlmodel', '.pem', '.key', '.p12') or name == '.env' or name.startswith('.env.'):
            forbidden.append(rel)
        require(file.stat().st_size < 25 * 1024 * 1024, 'Pages file exceeds 25 MiB: ' + rel)
        if file.suffix.lower() in ('.json', '.js', '.mjs', '.html', '.txt', '.xml', '.css', '.yml', '.yaml', '.toml'):
            scanned += 1
            require(credential.search(file.read_text(encoding='utf8')) is None, 'Credential signature found in: ' + rel)
    require(not forbidden, 'Forbidden media/model/credential files: ' + ', '.join(forbidden[:10]))
    return {'status': 'passed', 'source_segments_unchanged': examined, 'both_raw_htr_and_bbox_unchanged': True,
            'source_pages': len(source_manifest), 'interpreted_text_pages': interpreted_pages, 'downloads_checked': downloads,
            'resolved_html_links': links, 'base_sha256_unchanged': True, 'baseline_files_checked': len(hashes),
            'legacy_pages_unchanged': 677, 'legacy_underlying_files_checked': legacy_files,
            'legacy_inventory_sha256': legacy_digest.hexdigest(), 'forbidden_media_or_secret_files': forbidden,
            'credential_signature_text_files_checked': scanned, 'publication_ready': manifest['publication_ready'],
            'browser_visual_test': False, 'scope': 'Static overlay/source audit; no deployment, image-availability or paleographic accuracy assertion'}


def main():
    parser = argparse.ArgumentParser()
    for name in ('source', 'base-public', 'staged', 'build-report', 'report-dir'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    destination = report_path(args.report_dir, args.source.resolve(), args.base_public.resolve(), args.staged.resolve())
    result = audit(args.source, args.base_public, args.staged, args.build_report)
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
