"""Integrity and exact coordinate-transform checks, not an accuracy benchmark."""
from pathlib import Path
from functools import lru_cache
import hashlib
import json
import math
from datetime import datetime,timezone
from urllib.parse import urlparse,unquote
from lxml import html

OUT=Path(__file__).resolve().parent
ROOT=OUT.parent
PRIOR=ROOT/'chandra-segmentation-pilot-20261017'

@lru_cache(None)
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for data in iter(lambda:f.read(1024*1024),b''):h.update(data)
    return h.hexdigest()

def load(path):return json.loads(path.read_text(encoding='utf-8'))
def translated(points,dx,dy):return [[int(x)+dx,int(y)+dy] for x,y in points]

def main():
    records=load(PRIOR/'results.json')
    summary=load(OUT/'summary.json')
    engine=load(OUT/'engine.json')
    checks=[]; out_of_view=[]; expected_polygons=0; elapsed=0
    for rec in records:
        source=PRIOR/rec['id']/'crop.png' if rec.get('crop_xyxy') else ROOT/rec['image']
        original=ROOT/rec['original']
        check=dict(id=rec['id'],original_unchanged=sha(original)==rec['original_sha256'],
                   prior_chandra_raw_unchanged=sha(PRIOR/rec['id']/'raw.html')==rec['raw_sha256'])
        if rec.get('kraken'):
            check['old_kraken_unchanged']=sha(ROOT/rec['kraken'])==rec['kraken_segmentation_sha256']
            check['working_image_unchanged']=sha(source)==rec['working_source_sha256']
            expected_polygons+=len(load(ROOT/rec['kraken'])['lines'])
        for variant,padding in [('tight',0),('padding64',64)]:
            folder=OUT/rec['id']/variant
            r=load(folder/'result.json')
            assert r['status']=='complete' and not r['errors']
            assert r['source_image_sha256']==sha(source)
            assert r['chandra_result_sha256']==sha(PRIOR/rec['id']/'result.json')
            assert r['line_count']==len(r['lines'])
            assert len(r['lines'])==sum(len(b['lines']) for b in r['blocks'])
            assert len({l['id'] for l in r['lines']})==len(r['lines'])
            by_id={l['id']:l for l in r['lines']}
            for block in r['blocks']:
                source_block=next(b for b in rec['blocks'] if b['id']==block['chandra_id'])
                b=source_block['bbox_pixels_xyxy']
                expected_crop=[max(0,math.floor(b[0])-padding),max(0,math.floor(b[1])-padding),min(rec['width'],math.ceil(b[2])+padding),min(rec['height'],math.ceil(b[3])+padding)]
                assert block['crop_xyxy']==expected_crop
                assert block['network_canvas_size']==[expected_crop[2]-expected_crop[0],rec['parent_size'][1]]
                dx,dy=block['canvas_to_source_translation_xy']
                assert dx==expected_crop[0] and dy==-(rec.get('crop_xyxy') or [0,0])[1]
                local=load(folder/(block['chandra_id']+'.local-segmentation.json'))
                assert len(local['lines'])==len(block['lines'])
                for key,local_line in zip(block['lines'],local['lines']):
                    line=by_id[key]
                    assert line['local_line_id']==local_line['id']
                    assert line['boundary']==translated(local_line['boundary'],dx,dy)
                    assert line['baseline']==translated(local_line['baseline'],dx,dy)
                    assert len(line['boundary'])>=3 and len(line['baseline'])>=2
                    if rec.get('crop_xyxy'):
                        px,py=rec['crop_xyxy'][:2]
                        assert line['boundary_parent']==translated(line['boundary'],px,py)
                        assert line['baseline_parent']==translated(line['baseline'],px,py)
                    if any(x<0 or y<0 or x>rec['width'] or y>rec['height'] for x,y in line['boundary']+line['baseline']):
                        out_of_view.append(dict(id=line['id'],note='Genuine polygon may extend into white context outside diagnostic crop; not altered'))
            expected_polygons+=r['line_count']
            elapsed+=r['elapsed_seconds']
            check[variant+'_geometry_exact']=True
        checks.append(check)
    doc=html.fromstring((OUT/'index.html').read_text(encoding='utf-8'))
    links=[]
    for element in doc.xpath('//*[@href or @src]'):
        target=element.get('href') or element.get('src')
        parsed=urlparse(target)
        if parsed.scheme or not parsed.path:continue
        links.append(dict(target=target,exists=(OUT/unquote(parsed.path)).resolve().is_file()))
    rendered=len(doc.xpath('//polygon'))
    assert rendered==expected_polygons
    assert len(summary['pages'])==8 and summary['status']=='complete'
    assert sha(PRIOR/'results.json')==summary['chandra_results_sha256']
    assert engine['segmentation_model_sha256']=='77a638a83c9e535620827a09e410ed36391e9e8e8126d5796a0f15b978186056'
    assert all(v for c in checks for k,v in c.items() if k!='id')
    assert all(l['exists'] for l in links)
    control=load(OUT/'scale-control-335v.json')
    control_local=load(OUT/'scale-control-335v.local-segmentation.json')
    assert control['status']=='complete' and control['model_sha256']==engine['segmentation_model_sha256']
    assert control['original_manual_zone']==[500,290,4200,2550]
    assert control['source_sha256']==sha(ROOT/'htr-sixth-94-pages/pages/335v/image.png')
    assert control['line_count']==len(control['lines'])==len(control_local['lines'])
    for line,local in zip(control['lines'],control_local['lines']):
        assert line['baseline']==translated(local['baseline'],500,0)
        assert line['boundary']==translated(local['boundary'],500,0)
    result=dict(passed=True,validated_utc=datetime.now(timezone.utc).isoformat(),
                completed_samples=8,checks=checks,local_links=links,
                rendered_line_polygons=rendered,expected_line_polygons=expected_polygons,
                polygons_outside_diagnostic_view=out_of_view,
                completed_segmentation_seconds=elapsed,
                scale_control_seconds=control['elapsed_seconds'],scale_control_geometry_exact=True,
                recognition_run=False,accuracy_scored=False,independent_expert_review=False,
                note='Checks prove provenance and faithful coordinate transforms, not scientific correctness of segmentation.')
    (OUT/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ['checks','local_links','polygons_outside_diagnostic_view']},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
