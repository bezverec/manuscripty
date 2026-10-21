"""One-time, evidence-pinned annotation import. Never changes recognition/export data."""
from pathlib import Path
import argparse
import copy
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[2]
REVIEW = 'docs/experiments/2026-10-21-mi259-neighbor-survey/report.json'
NOTE = ('Útržek sousedního listu: tento výřez podle obrazové kontroly AI zachycuje '
        'pouze neúplný fragment sousední stránky při okraji snímku, nikoli úplný '
        'řádek hlavního textu. Chybějící části nelze spolehlivě doplnit. Původní '
        'HTR zůstává zachované; označení je pracovní posouzení bez odborné revize '
        '(21. 10. 2026).')
MIXED_NOTE = ('Přesah do sousedního listu: tento výřez podle obrazové kontroly AI '
              'obsahuje konec řádku hlavního listu i neúplný útržek textu sousední '
              'stránky za přehybem. Nelze jej celý považovat za jediný souvislý '
              'řádek hlavního textu. Původní HTR i segmentace zůstávají zachované; '
              'označení je pracovní posouzení bez odborné revize (21. 10. 2026).')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load(path):
    return json.loads(path.read_text('utf8'))

def require(condition, message):
    if not condition:
        raise ValueError(message)

def encoded(document, before_bytes):
    text = json.dumps(document, ensure_ascii=False, indent=2) + '\n'
    return text.replace('\n', '\r\n' if b'\r\n' in before_bytes else '\n').encode('utf8')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--review-sha256', required=True,
                        help='Explicit SHA-256 of the accepted frozen visual survey')
    parser.add_argument('--apply', action='store_true', help='Write checked annotations; default is dry run')
    args = parser.parse_args()
    review_path = ROOT / REVIEW
    require(re.fullmatch('[a-f0-9]{64}', args.review_sha256) and sha(review_path) == args.review_sha256,
            'Review hash differs from the explicitly accepted evidence')
    review = load(review_path)
    require(review['document_id'] == 'vkol-m-i-259' and review['expert_review'] is False
            and review['counts']['scans'] == 371, 'Wrong review identity/scope')
    ids = [r['id'] for r in review['rows']]
    require(len(ids) == len(set(ids)), 'Duplicate reviewed line identity')
    manifest_path = ROOT / 'docs/web-source-manifest.json'
    manifest = load(manifest_path)
    inventory = {r['path']: r for r in manifest['files']}
    page_reviews = {p['folio']: p for p in review['pages']}
    by_page = {}
    for row in review['rows']:
        require(re.fullmatch(r'\d+[rv]', row['folio']) and row['id'].startswith('f' + row['folio'] + '_l'),
                'Invalid folio/line identity')
        require(row['status'] == 'proposed' and row['expert_review'] is False, 'Invalid review state')
        by_page.setdefault(row['folio'], []).append(row)
    pending = []
    changes = []
    # Validate every affected page before any writes. Reapplication is rejected by the baseline SHA.
    for folio, rows in by_page.items():
        relative = f'web/public/data/vkol-m-i-259/{folio}/page.json'
        path = ROOT / relative
        expected = page_reviews[folio]['before_page_sha256']
        require(sha(path) == expected == inventory[relative]['sha256'], 'Page baseline changed: ' + folio)
        original = load(path)
        changed = copy.deepcopy(original)
        comparison = load(path.parent / 'comparison.json')
        raw_by_id = {r['id']: r for r in comparison['lines']}
        line_by_id = {r['id']: r for r in changed['lines']}
        undo = []
        for row in rows:
            line = line_by_id[row['id']]
            raw = raw_by_id[row['id']]
            require(row['original_crop_sha256'] == raw['image_sha256'] and row['bbox_xyxy'] == raw['bbox_xyxy'],
                    'Changed source crop/geometry: ' + row['id'])
            require(all(line['raw_htr'][m] == raw['candidates'][m]['raw'] for m in ('catmus', 'medusa')),
                    'Changed original HTR: ' + row['id'])
            if row['already_annotated']:
                require('neighboring_leaf_fragment' in line['flags'], 'Missing previous annotation')
                continue
            require('editorial_annotation' not in line, 'Existing editorial annotation would be overwritten')
            mixed = row['classification'] == 'mixed_main_and_neighboring_leaf'
            require(mixed or row['classification'] == 'partial_neighboring_leaf', 'Unknown classification')
            flag = 'neighboring_leaf_overlap' if mixed else 'neighboring_leaf_fragment'
            require(flag not in line['flags'], 'Annotation already present')
            undo.append((row['id'], line['note'], line['flags'][:]))
            line['note'] = (MIXED_NOTE if mixed else NOTE) + (' ' + line['note'] if line['note'] else '')
            line['flags'].append(flag)
            line['editorial_annotation'] = {
                'classification': row['classification'], 'date': '2026-10-21', 'status': 'proposed',
                'expert_review': False, 'evidence_review_path': REVIEW,
                'evidence_review_sha256': args.review_sha256, 'source_crop_sha256': row['original_crop_sha256']}
        if not undo:
            continue
        restored = copy.deepcopy(changed)
        restored_by_id = {r['id']: r for r in restored['lines']}
        for line_id, note, flags in undo:
            line = restored_by_id[line_id]
            line['note'], line['flags'] = note, flags
            line.pop('editorial_annotation')
        require(restored == original, 'Unexpected change beyond notes/flags/annotation: ' + folio)
        content = encoded(changed, path.read_bytes())
        digest = hashlib.sha256(content).hexdigest()
        pending.append((path, content))
        inventory[relative].update(sha256=digest, bytes=len(content))
        changes.append({'path': relative, 'before_page_sha256': expected, 'after_page_sha256': digest,
                        'annotated_ids': [u[0] for u in undo], 'previous_notes_and_flags':
                        [{'id': i, 'note': n, 'flags': f} for i, n, f in undo],
                        'all_other_page_fields_unchanged': True})
    count = sum(len(c['annotated_ids']) for c in changes)
    require(count == review['counts']['new_annotations'], 'Annotation count differs from review')
    audit = {'date': '2026-10-21', 'status': 'passed', 'review_path': REVIEW,
             'source_review_sha256': args.review_sha256, 'new_annotations': count,
             'changed_pages': len(changes), 'changes': changes,
             'original_raw_geometry_passages_downloads_and_token_flags_preserved': True,
             'original_txt_alto_tei_and_interpretation_files_modified': False,
             'new_htr_inference': False, 'expert_review': False}
    if args.apply:
        for path, content in pending:
            path.write_bytes(content)
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf8', newline='\n')
        (ROOT / 'docs/validation/mi259-neighbor-survey-import-20261021.json').write_text(
            json.dumps(audit, ensure_ascii=False, indent=2) + '\n', encoding='utf8', newline='\n')
    print(json.dumps({'mode': 'applied' if args.apply else 'dry-run', 'new_annotations': count,
                      'changed_pages': len(changes), 'originals_preserved': True}))

if __name__ == '__main__':
    main()
