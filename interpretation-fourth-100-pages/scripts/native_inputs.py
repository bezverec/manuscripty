"""Local preparation helpers for the isolated fourth hundred-page interpretation batch."""
from pathlib import Path
import hashlib,json,re
from PIL import Image
I=Path(__file__).resolve().parents[1]; ROOT=I.parent
SOURCE_FOLDER='htr-fourth-100-pages'; TARGET=100
assert I.name=='interpretation-fourth-100-pages','Unexpected output directory'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def save(p,data):
 temp=p.with_name(p.name+'.tmp')
 temp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 temp.replace(p)
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as stream:
  for b in iter(lambda:stream.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def manifest_pages(require_complete=False):
 p=ROOT/SOURCE_FOLDER/'manifest.json'
 if not p.exists():return []
 pages=read(p)['pages']
 assert (len(pages)==TARGET if require_complete else 0<len(pages)<=TARGET),'Raw manifest page count outside this batch'
 assert len({p['folio'] for p in pages})==len(pages),'Duplicate raw folios'
 assert all(re.fullmatch(r'[1-9][0-9]*[rv]',p['folio']) for p in pages),'Unsafe folio path'
 return pages
def working_path(source):
 rel=Path(source['working_image'])
 assert not rel.is_absolute() and '..' not in rel.parts
 return ROOT/SOURCE_FOLDER/rel
def ready(source):
 keys=('original','original_sha256','working_image','working_image_sha256','width','height','regions')
 return all(k in source for k in keys) and working_path(source).is_file()
def prepare_inputs(source):
 f=source['folio'];out=I/f
 assert ready(source),f+' working image is not ready'
 for box in source['regions']:
  assert len(box)==4 and all(isinstance(n,int) for n in box)
  x0,y0,x1,y1=box
  assert 0<=x0<x1<=source['width'] and 0<=y0<y1<=source['height']
 assert source['regions'] or source.get('blank_main_text') is True,f+' empty selection is not marked blank'
 assert sha(working_path(source))==source['working_image_sha256'],f+' working image checksum changed'
 out.mkdir(exist_ok=True);(out/'tiles').mkdir(exist_ok=True)
 p=out/'inputs.json'
 if p.exists():
  inputs=read(p)
  assert inputs['folio']==f and inputs['source_folder']==SOURCE_FOLDER and inputs['source']==source,f+' existing inputs differ from manifest'
  return inputs
 inputs={'folio':f,'source_folder':SOURCE_FOLDER,'source':source,'tiles':[],
         'operation':'Native RGB selected-zone pixels; overlapping reading strips, no resizing. Preparing evidence does not assert it was opened.'}
 save(p,inputs)
 return inputs
def prepare_reading(source):
 inputs=prepare_inputs(source);out=I/source['folio'];images=[]
 existing=[t for t in inputs['tiles'] if t['image'].startswith('tiles/read-')]
 if existing:
  assert all((out/t['image']).is_file() for t in existing),'Existing registered reading strip is missing'
  return len(existing)
 with Image.open(working_path(source)) as im:
  assert im.size==(source['width'],source['height']) and im.mode=='RGB'
  for zi,(x0,y0,x1,y1) in enumerate(source['regions'],1):
   width=x1-x0
   columns=[(x0,x1)] if width<=2100 else [(x0,x0+width//2+80),(x0+width//2-80,x1)]
   for yi,y in enumerate(range(y0,y1,850),1):
    for xi,(x,ex) in enumerate(columns,1):
     box=[x,y,ex,min(y+950,y1)];name=f'tiles/read-z{zi}-y{yi}-x{xi}.png'
     p=out/name
     if not p.exists():im.crop(box).save(p)
     images.append({'image':name,'bbox_xyxy':box,'region_index':zi-1,'pixels_scaled':False,'source':'working_image'})
 old=inputs['tiles'];updated=[t for t in old if not t['image'].startswith('tiles/read-')]+images
 if updated!=old:inputs['tiles']=updated;save(out/'inputs.json',inputs)
 return len(images)
