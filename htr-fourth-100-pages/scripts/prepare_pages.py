from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib,time,shutil
HERE=Path(__file__).resolve().parents[1];ROOT=HERE.parent
sel=json.loads((HERE/'selection.json').read_text(encoding='utf-8'))
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(HERE/'pages').mkdir(exist_ok=True)
records=[]
for page in sel['pages']:
 folio=page['folio'];out=HERE/'pages'/folio;out.mkdir(exist_ok=True)
 num=int(folio[:-1]);side=folio[-1].upper();src=ROOT/'EX'/f'M_II_220____26LY4SCEX{num:04d}{side}.TIF'
 start=time.perf_counter();srcsha=sha(src)
 with Image.open(src) as img:
  frames=img.n_frames;img.seek(0);im=img.convert('RGB')
  assert im.size==(4500,5900)
  preview=im.copy();draw=ImageDraw.Draw(preview)
  for n,box in enumerate(page['regions'],1):draw.rectangle(box,outline='blue',width=12);draw.text((box[0]+20,box[1]+20),str(n),fill='blue',stroke_width=3)
  preview.thumbnail((1125,1475));preview.save(out/'selection-regions.jpg',quality=94)
  thumb=im.copy();thumb.thumbnail((1125,1475));thumb.save(out/'overview.jpg',quality=94)
  if page.get('reuse'):
   old=ROOT/'pilot-20r-21r'
   for target,source in [('image.png',old/'images/20v.png'),('segmentation.json',old/'htr/20v.segmentation.json')]:shutil.copyfile(source,out/target)
   (out/'crops').mkdir(exist_ok=True)
   for path in (old/'crops/20v').glob('*.png'):shutil.copyfile(path,out/'crops'/path.name)
  else:
   work=Image.new('RGB',im.size,'white')
   for box in page['regions']:work.paste(im.crop(box),box[:2])
   work.save(out/'image.png')
 rec={**page,'original':str(src.relative_to(ROOT)).replace(chr(92),'/'),'original_sha256':srcsha,'width':im.width,'height':im.height,'frame_used':0,'tiff_frames':frames,'working_image':f'pages/{folio}/image.png','working_image_sha256':sha(out/'image.png'),'preparation_seconds':time.perf_counter()-start,'selection_overview_inspected':True,'inspection_scope':'Reduced contact sheet used for main-column layout selection; not complete native-resolution reading.','pixel_operation':'Original-coordinate RGB frame 0; outside writing zones white, no scaling in working PNG.'}
 if page.get('reuse'):rec['pixel_operation']='Exact copy of previous 20v working PNG and original segmentation/crops; bytes unchanged.'
 records.append(rec);save(HERE/'manifest.json',{'document_id':'VKO_M_II_220','status':'prepared','pages':records,'selection':'selection.json','expert_review':False})
 print(json.dumps({'prepared':folio,'seconds':rec['preparation_seconds'],'source_sha256':srcsha}),flush=True)
print('PREPARATION_COMPLETE',flush=True)
