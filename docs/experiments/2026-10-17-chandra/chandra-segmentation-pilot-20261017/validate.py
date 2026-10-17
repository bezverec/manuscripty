"""Verify provenance and generated comparison integrity, without OCR quality scores."""
from pathlib import Path
import json
from datetime import datetime, timezone
from urllib.parse import urlparse, unquote
from lxml import html
from run_pilot import sha, dump

OUT = Path(__file__).resolve().parent
ROOT = OUT.parent

def main():
    records = json.loads((OUT/'results.json').read_text(encoding='utf-8'))
    checks=[]
    for record in records:
        folder=OUT/record['id']
        check=dict(id=record['id'],
                   source_unchanged=sha(ROOT/record['image'])==record['working_source_sha256'],
                   original_unchanged=sha(ROOT/record['original'])==record['original_sha256'],
                   input_unchanged=sha(folder/'input.png')==record['model_input_sha256'],
                   raw_unchanged=sha(folder/'raw.html')==record['raw_sha256'],
                   all_bboxes_valid=all(b['valid_bbox'] for b in record['blocks']),
                   not_truncated=record['finish_reason']=='stop')
        if 'kraken' in record:
            check['kraken_unchanged']=sha(ROOT/record['kraken'])==record['kraken_segmentation_sha256']
            # JSON pretty printing need not preserve source whitespace/bytes.
            check['kraken_copy_semantically_identical']=json.loads((folder/'kraken.json').read_text(encoding='utf-8'))==json.loads((ROOT/record['kraken']).read_text(encoding='utf-8'))
        checks.append(check)
    doc=html.fromstring((OUT/'index.html').read_text(encoding='utf-8'))
    links=[]
    for e in doc.xpath('//*[@href or @src]'):
        target=e.get('href') or e.get('src')
        p=urlparse(target)
        if p.scheme or not p.path:
            continue
        resolved=(OUT/unquote(p.path)).resolve()
        links.append(dict(target=target, exists=resolved.is_file()))
    expected_chandra=sum(r['block_count'] for r in records)
    expected_kraken=sum(r.get('kraken_lines',0) for r in records)
    geometry=dict(expected_chandra=expected_chandra,
                  rendered_chandra=len(doc.xpath('//polygon[@class="chandra"]')),
                  expected_kraken=expected_kraken,
                  rendered_kraken=len(doc.xpath('//polygon[@class="kraken"]')))
    passed=all(all(v for k,v in c.items() if k!='id') for c in checks)
    passed=passed and all(l['exists'] for l in links)
    passed=passed and geometry['rendered_chandra']==expected_chandra and geometry['rendered_kraken']==expected_kraken
    result=dict(validated_utc=datetime.now(timezone.utc).isoformat(), passed=passed,
                checks=checks,local_links=links,geometry=geometry,
                seconds=sum(r['elapsed_seconds'] for r in records),
                prompt_tokens=sum(r['usage']['prompt_tokens'] for r in records),
                completion_tokens=sum(r['usage']['completion_tokens'] for r in records),
                recognition_scored=False, segmentation_ground_truth_scored=False,
                independent_expert_review=False)
    dump(OUT/'validation.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('local_links','checks')},ensure_ascii=False,indent=2))
    if not passed:
        raise SystemExit('Validation failed: see validation.json')

if __name__=='__main__':
    main()
