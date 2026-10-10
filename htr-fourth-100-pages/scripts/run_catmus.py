from pathlib import Path
import json,hashlib,time,dataclasses,importlib.metadata,importlib.resources,datetime,traceback
import os
import torch
from PIL import Image,ImageDraw
from kraken import blla,rpred
from kraken.containers import BaselineLine
from kraken.lib import models,vgsl
import kraken.lib.segmentation as kseg
from shapely import make_valid
from shapely.errors import GEOSException
HERE=Path(__file__).resolve().parents[1];ROOT=HERE.parent
manifest=json.loads((HERE/'manifest.json').read_text())
SHARD=int(os.environ.get('CATMUS_SHARD','0'))
if SHARD:manifest['pages']=manifest['pages'][(SHARD-1)*50:SHARD*50]
# Preserve shard membership; interleave author assignments to avoid starvation.
shard_pages={p['folio']:p for p in manifest['pages']}
author_groups=[json.loads((ROOT/'interpretation-fourth-100-pages'/'assignments'/f'{name}.json').read_text())['folios'] for name in ['parent','b','c','a']]
ordered=[f for row in __import__('itertools').zip_longest(*author_groups) for f in row if f in shard_pages]
assert len(ordered)==len(shard_pages) and len(set(ordered))==len(ordered)
manifest['pages']=[shard_pages[f] for f in ordered]
BATCH_FILE=HERE/('catmus-batch.json' if not SHARD else f'catmus-batch-part{SHARD}.json')
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf-8')
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
torch.set_num_threads(4)
segpath=importlib.resources.files('kraken').joinpath('blla.mlmodel');mp=Path('/models/catmus-medieval-1.6.0.mlmodel')
assert sha(mp)=='227d10f15a936c2492105b7796a6152647c742f248af117856f417008eadbc9c'
assert sha(Path(str(segpath)))=='77a638a83c9e535620827a09e410ed36391e9e8e8126d5796a0f15b978186056'
started=time.perf_counter();segmodel=vgsl.TorchVGSLModel.load_model(segpath);net=models.load_any(str(mp),device='cpu')
engine={'kraken':importlib.metadata.version('kraken'),'torch':torch.__version__,'device':'cpu','threads':4,'segmentation_model_sha256':sha(Path(str(segpath))),'catmus_model_sha256':sha(mp),'model_load_seconds':time.perf_counter()-started}
save(HERE/('catmus-engine.json' if not SHARD else f'catmus-engine-part{SHARD}.json'),engine)
summary={'status':'running','started_utc':utc(),'engine':engine,'scheduling':'Fixed 50-page shard membership; author assignment round-robin parent,b,c,a. Successful page checkpoints resumed unchanged; manifest preserved.','prior_sessions_provenance':'catmus-session-history.json','pages':[]}
save(BATCH_FILE,summary)
original_union=kseg.unary_union
def polygon_parts(g):
 if g.geom_type=='Polygon':return [g]
 return [p for child in getattr(g,'geoms',[]) for p in polygon_parts(child)]
def audited_union(geoms):
 try:return original_union(geoms)
 except GEOSException as e:
  if 'TopologyException' not in str(e):raise
  repaired=[make_valid(g) if not g.is_valid else g for g in geoms]
  polygons=[p for g in repaired for p in polygon_parts(g)]
  result=original_union(polygons)
  assert result.is_valid and not result.is_empty
  polygonizer_events.append({'error':str(e),'fallback':'GEOS make_valid on invalid detected envelope polygons; retain polygon components, omit zero-area line components; no text or baseline alteration. Visual review required.','input_wkt':[g.wkt for g in geoms],'repaired_wkt':[g.wkt for g in repaired],'union_wkt':result.wkt})
  return result
kseg.unary_union=audited_union
original_polygonizer=blla.calculate_polygonal_environment
polygonizer_events=[]
def audited_polygonizer(**kwargs):
 try:return original_polygonizer(**kwargs)
 except Exception as e:
  if isinstance(e, NotImplementedError) and 'multi-part geometries do not' in str(e):
   retry=dict(kwargs);retry['topline']=None
   result=original_polygonizer(**retry)
   polygonizer_events.append({'error':str(e),'scaled_baselines':[list(map(list,bl)) for bl in kwargs['baselines']],'fallback':'Retry polygonization with original supplementary constraints and topline=None after multi-part parallel offset error. No eight-pixel baseline offset; detected baseline unchanged; visual review required.'})
   return result
  if not any(k in str(e) for k in ['No intersection with boundaries','TopologyException','is out of bounds for axis 0 with size 0']):raise
  event={'error':str(e),'scaled_baselines':[list(map(list,bl)) for bl in kwargs['baselines']],'fallback':'Retry polygonization of same detected baseline without supplementary neighbour/region constraints; visual review required.'}
  retry=dict(kwargs);retry['suppl_obj']=[]
  try:result=original_polygonizer(**retry)
  except IndexError as retry_error:
   if 'is out of bounds for axis 0 with size 0' not in str(retry_error):raise
   event['retry_error']=str(retry_error)
   event['fallback']='Retry polygonization with original supplementary constraints and topline=None (no eight-pixel baseline offset). Detected baseline unchanged; visual review required.'
   retry=dict(kwargs);retry['topline']=None
   result=original_polygonizer(**retry)
  polygonizer_events.append(event)
  return result
for page in manifest['pages']:
 folio=page['folio'];out=HERE/'pages'/folio
 if (out/'catmus.candidates.json').exists() and (out/'catmus-run.json').exists() and json.loads((out/'catmus-run.json').read_text()).get('status')=='success':
  prior=json.loads((out/'catmus-run.json').read_text());assert prior['status']=='success' and prior['image_sha256']==sha(out/'image.png') and prior['segmentation_sha256']==sha(out/'segmentation.json')
  summary['pages'].append(prior);save(BATCH_FILE,summary);print('RESUME_EXISTING '+folio,flush=True);continue
 run={'folio':folio,'status':'running','started_utc':utc(),'image_sha256':sha(out/'image.png'),'original_sha256':page['original_sha256'],'reading_zones':page['regions'],'reading_order_policy':'Each manually defined zone top-to-bottom, then zone order. Table column relations are not reconstructed.','expert_reference':False,'cer':None,'wer':None};save(out/'catmus-run.json',run)
 t0=time.perf_counter()
 try:
  im=Image.open(out/'image.png')
  if page.get('blank_main_text'):
   assert not page['regions']
   lines=[]
   save(out/'segmentation.json',{'type':'baselines','imagename':str(out/'image.png'),'text_direction':'horizontal-lr','script_detection':False,'lines':[],'regions':{},'line_orders':None,'language':None})
   (out/'crops').mkdir(exist_ok=True)
   run.update(status='success',segmentation_seconds=0,crop_seconds=0,recognition_seconds=0,polygonizer_fallback_events=[],blank_main_text=True,model_inference_performed=False)
  elif page.get('reuse'):
   old=json.loads((ROOT/'pilot-20r-21r/htr/20v.candidates.json').read_text())
   segjson=json.loads((out/'segmentation.json').read_text())
   lines=[]
   for item in old['lines']:
    crop=out/'crops'/f"{item['id']}.png"
    lines.append({'id':item['id'],'bbox':item['bbox'],'boundary':item['boundary'],'baseline':item['baseline'],'region_index':0 if item['bbox'][0]<2400 else 1,'image':'crops/'+crop.name,'image_sha256':sha(crop),'raw':item['candidates']['catmus']['raw'],'review_flags':['original_fragment'] if item['id'] in ['f20v_l013','f20v_l058'] else []})
   run.update(status='reused',source='../pilot-20r-21r/htr/20v.candidates.json',source_sha256=sha(ROOT/'pilot-20r-21r/htr/20v.candidates.json'),recognition_seconds=None,segmentation_seconds=None,crop_seconds=None,reused_segments=len(lines),timing_note='No recognition rerun; no original CATMuS per-page timing was captured.')
  else:
   ts=time.perf_counter();pieces=[];polygonizer_events.clear();blla.calculate_polygonal_environment=audited_polygonizer
   for zi,box in enumerate(page['regions']):
    print(json.dumps({'stage':'segmentation','folio':folio,'zone':zi}),flush=True)
    event_start=len(polygonizer_events)
    s=blla.segment(im.crop(box),model=segmodel,device='cpu',raise_on_error=True)
    for event in polygonizer_events[event_start:]:event['zone']=zi
    if not s.lines:
     manual=HERE/'inspection/manual-segmentation.json'
     entries=json.loads(manual.read_text())['lines'] if manual.exists() else []
     matches=[e for e in entries if e['folio']==folio and e['region_index']==zi]
     if not matches:raise RuntimeError(f'No lines detected in text zone {zi}, {folio}')
     s.lines=[BaselineLine(id='manual-heading',baseline=[(x-box[0],y-box[1]) for x,y in e['baseline']],boundary=[(x-box[0],y-box[1]) for x,y in e['boundary']]) for e in matches]
     run.setdefault('manual_segmentation_events',[]).extend(matches)
    for line in s.lines:
     line.baseline=[(int(x)+box[0],int(y)+box[1]) for x,y in line.baseline]
     line.boundary=[(int(x)+box[0],int(y)+box[1]) for x,y in line.boundary]
    s.lines.sort(key=lambda ln:min(p[1] for p in ln.baseline))
    pieces.append(s)
   seg=pieces[0];all_lines=[];zones=[]
   for zi,piece in enumerate(pieces):all_lines.extend(piece.lines);zones.extend([zi]*len(piece.lines))
   seg.lines=all_lines;seg.regions={};seg.imagename=str(out/'image.png')
   for n,line in enumerate(seg.lines,1):line.id=f'f{folio}_l{n:03d}'
   run['segmentation_seconds']=time.perf_counter()-ts
   run['polygonizer_fallback_events']=list(polygonizer_events)
   save(out/'segmentation.json',dataclasses.asdict(seg))
   ts=time.perf_counter();(out/'crops').mkdir(exist_ok=True);overview=im.convert('RGB');draw=ImageDraw.Draw(overview);lines=[]
   for line,zi in zip(seg.lines,zones):
    xs=[int(p[0]) for p in line.boundary];ys=[int(p[1]) for p in line.boundary]
    bbox=[min(xs),min(ys),max(xs)-min(xs),max(ys)-min(ys)];box=page['regions'][zi]
    xy=(max(0,min(xs)-12),max(0,min(ys)-12),min(im.width,max(xs)+13),min(im.height,max(ys)+13))
    cp=out/'crops'/f'{line.id}.png';im.crop(xy).save(cp)
    flags=[]
    if any(e['region_index']==zi for e in run.get('manual_segmentation_events',[])):flags.append('manual_segmentation')
    if any(e['zone']==zi for e in polygonizer_events):flags.append('polygonizer_fallback_in_zone')
    if bbox[2]<150 or bbox[3]<25:flags.append('small_fragment')
    if bbox[3]>300:flags.append('tall_segment')
    if min(xs)-box[0]<12 or box[2]-max(xs)<12 or min(ys)-box[1]<12 or box[3]-max(ys)<12:flags.append('near_zone_edge')
    lines.append({'id':line.id,'bbox':bbox,'boundary':line.boundary,'baseline':line.baseline,'region_index':zi,'image':'crops/'+cp.name,'image_sha256':sha(cp),'crop_xyxy':list(xy),'review_flags':flags})
    draw.line(line.boundary+[line.boundary[0]],fill='red',width=4);draw.text((xy[0],xy[1]),line.id,fill='blue',stroke_width=1)
   overview.thumbnail((1350,1770));overview.save(out/'segmentation-preview.jpg',quality=94)
   run['crop_seconds']=time.perf_counter()-ts
   ts=time.perf_counter();preds=list(rpred.rpred(net,im,seg));run['recognition_seconds']=time.perf_counter()-ts
   assert len(preds)==len(lines)
   for item,pred in zip(lines,preds):item['raw']=pred.prediction
   run['status']='success'
  save(out/'catmus.candidates.json',{'folio':folio,'model':'CATMuS medieval 1.6.0','status':'raw_unreviewed','lines':lines})
  (out/'catmus.raw.txt').write_text('\n'.join(x['raw'] for x in lines)+'\n',encoding='utf-8')
  run.update(finished_utc=utc(),total_seconds=time.perf_counter()-t0,segments=len(lines),nonempty=sum(bool(x['raw'].strip()) for x in lines),segmentation_sha256=sha(out/'segmentation.json'))
  save(out/'catmus-run.json',run);summary['pages'].append(run);save(BATCH_FILE,summary)
  print(json.dumps({'done':folio,'segments':len(lines),'segmentation_seconds':run['segmentation_seconds'],'recognition_seconds':run['recognition_seconds'],'total_seconds':run['total_seconds']}),flush=True)
 except Exception as e:
  run.update(status='failed',error=str(e),finished_utc=utc());save(out/'catmus-run.json',run);summary.update(status='failed',error=str(e));save(BATCH_FILE,summary);traceback.print_exc();raise
summary.update(status='success',finished_utc=utc());save(BATCH_FILE,summary);print('CATMUS_BATCH_COMPLETE',flush=True)
