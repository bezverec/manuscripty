"""335v ablation: original manual zone with the hybrid's white-canvas scale."""
from pathlib import Path
import dataclasses
import importlib.resources
import json
import time
import torch
from PIL import Image
from kraken import blla
from kraken.lib import vgsl
from run_hybrid import sha,dump,move_points,line_box,utc,MODEL_SHA

ROOT=Path('/workspace'); OUT=Path('/output')
source=ROOT/'htr-sixth-94-pages/pages/335v/image.png'
prior=json.loads((ROOT/'htr-sixth-94-pages/pages/335v/catmus-run.json').read_text(encoding='utf-8'))
assert prior['reading_zones']==[[500,290,4200,2550]]
assert sha(source)==prior['image_sha256']
torch.set_num_threads(4)
mp=Path(str(importlib.resources.files('kraken').joinpath('blla.mlmodel')))
assert sha(mp)==MODEL_SHA
model=vgsl.TorchVGSLModel.load_model(mp)
im=Image.open(source).convert('RGB')
box=prior['reading_zones'][0]
canvas=Image.new('RGB',(box[2]-box[0],im.height),'white')
canvas.paste(im.crop(box),(0,box[1]))
t=time.perf_counter()
print('START SCALE_CONTROL_335V',flush=True)
seg=blla.segment(canvas,model=model,device='cpu',raise_on_error=True)
elapsed=time.perf_counter()-t
dump(OUT/'scale-control-335v.local-segmentation.json',dataclasses.asdict(seg))
lines=[]
for n,line in enumerate(seg.lines,1):
    row=dict(id=f'mii220-335v_scale_control_l{n:03}',local_line_id=line.id,
             boundary=move_points(line.boundary,box[0],0),baseline=move_points(line.baseline,box[0],0))
    row['bbox_xyxy']=line_box(row)
    lines.append(row)
dump(OUT/'scale-control-335v.json',dict(status='complete',finished_utc=utc(),
    source=str(source),source_sha256=sha(source),original_manual_zone=box,
    network_canvas_size=list(canvas.size),model_sha256=sha(mp),elapsed_seconds=elapsed,
    lines=lines,line_count=len(lines),expert_review=False,recognition_run=False,
    purpose='Isolate white-canvas/page-height normalization from Chandra block proposals on 335v'))
print('DONE SCALE_CONTROL_335V',len(lines),round(elapsed,2),flush=True)
