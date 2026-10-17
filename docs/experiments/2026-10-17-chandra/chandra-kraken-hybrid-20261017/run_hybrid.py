"""CPU-only Kraken on previously generated Chandra blocks, in an isolated container.

No recognition, manual lines, deduplication, or changes to archival data.
Run with /workspace mounted read-only, this folder at /output read-write.
"""
from pathlib import Path
import dataclasses
import datetime
import hashlib
import importlib.metadata
import importlib.resources
import json
import math
import time
import traceback

import torch
from PIL import Image
from kraken import blla
from kraken.lib import vgsl

ROOT = Path('/workspace')
OUT = Path('/output')
PRIOR = ROOT / 'chandra-segmentation-pilot-20261017'
VARIANTS = [('tight', 0), ('padding64', 64)]
MODEL_SHA = '77a638a83c9e535620827a09e410ed36391e9e8e8126d5796a0f15b978186056'

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()

def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str), encoding='utf-8')

def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def move_points(points, dx, dy):
    return [[int(x)+dx, int(y)+dy] for x,y in points] if points else []

def line_box(line):
    xs,ys=zip(*line['boundary'])
    return [min(xs),min(ys),max(xs),max(ys)]

def main():
    torch.set_num_threads(4)
    model_path=Path(str(importlib.resources.files('kraken').joinpath('blla.mlmodel')))
    assert sha(model_path)==MODEL_SHA
    t0=time.perf_counter()
    model=vgsl.TorchVGSLModel.load_model(model_path)
    dump(OUT/'engine.json',dict(kraken=importlib.metadata.version('kraken'), torch=torch.__version__,
         device='cpu',threads=4,segmentation_model=str(model_path),segmentation_model_sha256=sha(model_path),
         model_input=list(model.input),model_spec=model.spec,
         model_load_seconds=time.perf_counter()-t0,network='none',recognition_run=False,
         polygonizer_fallback=False,manual_line_fallback=False))
    records=json.loads((PRIOR/'results.json').read_text(encoding='utf-8'))
    summary=dict(started_utc=utc(), status='running', variants=VARIANTS,
                 chandra_reused=True, chandra_results_sha256=sha(PRIOR/'results.json'),
                 source_policy='Same working PNGs as preceding pilot, plus its separate original-header crop',
                 coordinate_policy='Outward-rounded Chandra bbox; fixed crop padding; selected source pixels placed on white canvas at original TIFF height to preserve network scale; genuine Kraken points translated without additional scaling',
                 canvas_policy='Native source pixels only; crop width, original TIFF height. Pixels outside selected bbox are white. No physical-line geometry is supplied.',
                 reading_order='Chandra block sequence, then Kraken native line order inside each block',
                 deduplication=False,manual_line_fallback=False,expert_review=False,pages=[])
    dump(OUT/'summary.json',summary)
    for rec in records:
        page_dir=OUT/rec['id']
        page_dir.mkdir(exist_ok=True)
        src=PRIOR/rec['id']/'crop.png' if rec.get('crop_xyxy') else ROOT/rec['image']
        with Image.open(src) as opened:
            opened.seek(0)
            im=opened.convert('RGB')
        assert im.size==(rec['width'],rec['height'])
        if not rec.get('crop_xyxy'):
            assert sha(src)==rec['working_source_sha256']
        meta={k:rec.get(k) for k in ['id','manuscript','folio','image','original','width','height','crop_xyxy','working_source_sha256','original_sha256','kraken','kraken_lines']}
        meta.update(chandra_result_sha256=sha(PRIOR/rec['id']/'result.json'),
                    source_image_sha256=sha(src),source_image=str(src),expert_review=False)
        dump(page_dir/'source.json',meta)
        for variant,padding in VARIANTS:
            destination=page_dir/variant
            destination.mkdir(exist_ok=True)
            result_path=destination/'result.json'
            if result_path.exists():
                existing=json.loads(result_path.read_text(encoding='utf-8'))
                if existing.get('status')=='complete':
                    print('REUSE',rec['id'],variant,flush=True)
                    summary['pages'].append(existing)
                    continue
            result=dict(**meta,variant=variant,padding_pixels=padding,status='running',
                        started_utc=utc(),blocks=[],lines=[],errors=[])
            p0=time.perf_counter()
            for block in rec['blocks']:
                if not block['valid_bbox']:
                    result['errors'].append(dict(block_id=block['id'],error='Invalid Chandra bbox'))
                    continue
                box=block['bbox_pixels_xyxy']
                crop=[max(0,math.floor(box[0])-padding),max(0,math.floor(box[1])-padding),
                      min(im.width,math.ceil(box[2])+padding),min(im.height,math.ceil(box[3])+padding)]
                assert crop[0]<crop[2] and crop[1]<crop[3]
                block_record=dict(chandra_id=block['id'],label=block['label'],
                                  chandra_bbox_xyxy=box,crop_xyxy=crop,lines=[],status='running')
                print('START',rec['id'],variant,block['id'],crop,flush=True)
                b0=time.perf_counter()
                try:
                    # blla fixes its input height to 1800. A 90 px-high direct
                    # crop would enlarge letters by 20x. Neutral white context
                    # keeps the page-height normalization consistent instead.
                    parent_height=rec['parent_size'][1]
                    parent_y=rec.get('crop_xyxy',[0,0])[1]
                    canvas=Image.new('RGB',(crop[2]-crop[0],parent_height),'white')
                    canvas.paste(im.crop(crop),(0,crop[1]+parent_y))
                    block_record['network_canvas_size']=list(canvas.size)
                    block_record['canvas_paste_xy']=[0,crop[1]+parent_y]
                    block_record['canvas_to_source_translation_xy']=[crop[0],-parent_y]
                    seg=blla.segment(canvas,model=model,device='cpu',raise_on_error=True)
                    dump(destination/(block['id']+'.local-segmentation.json'),dataclasses.asdict(seg))
                    for n,line in enumerate(seg.lines,1):
                        item=dict(id=f'{rec["id"]}_{variant}_{block["id"]}_l{n:03}',
                                  chandra_block_id=block['id'],local_line_id=line.id,
                                  baseline=move_points(line.baseline,crop[0],-parent_y),
                                  boundary=move_points(line.boundary,crop[0],-parent_y),
                                  source='kraken_blla_in_chandra_crop',review_status='proposed')
                        item['bbox_xyxy']=line_box(item)
                        baseline=item['baseline']
                        cx=sum(p[0] for p in baseline)/len(baseline)
                        cy=sum(p[1] for p in baseline)/len(baseline)
                        item['baseline_anchor_xy']=[cx,cy]
                        item['anchor_outside_original_chandra_bbox']=not(box[0]<=cx<=box[2] and box[1]<=cy<=box[3])
                        item['near_crop_edge']=any([item['bbox_xyxy'][0]-crop[0]<12,item['bbox_xyxy'][1]-crop[1]<12,crop[2]-item['bbox_xyxy'][2]<12,crop[3]-item['bbox_xyxy'][3]<12])
                        if rec.get('crop_xyxy'):
                            dx,dy=rec['crop_xyxy'][:2]
                            item['boundary_parent']=move_points(item['boundary'],dx,dy)
                            item['baseline_parent']=move_points(item['baseline'],dx,dy)
                        result['lines'].append(item)
                        block_record['lines'].append(item['id'])
                    block_record['status']='success' if seg.lines else 'no_lines'
                except Exception as error:
                    block_record.update(status='error',error_type=type(error).__name__,error=str(error),traceback=traceback.format_exc())
                    result['errors'].append(dict(block_id=block['id'],error_type=type(error).__name__,error=str(error)))
                block_record['elapsed_seconds']=time.perf_counter()-b0
                result['blocks'].append(block_record)
                dump(result_path,result)
                print('DONE',rec['id'],variant,block['id'],block_record['status'],len(block_record['lines']),round(block_record['elapsed_seconds'],2),flush=True)
            result.update(status='complete',finished_utc=utc(),elapsed_seconds=time.perf_counter()-p0,
                          line_count=len(result['lines']),zero_line_blocks=sum(b['status']=='no_lines' for b in result['blocks']),
                          error_blocks=sum(b['status']=='error' for b in result['blocks']))
            dump(result_path,result)
            summary['pages'].append(result)
            dump(OUT/'summary.json',summary)
    summary.update(status='complete',finished_utc=utc())
    dump(OUT/'summary.json',summary)
    print('HYBRID_COMPLETE',flush=True)

if __name__=='__main__':
    main()
