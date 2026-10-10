from pathlib import Path
import json,hashlib
from PIL import Image
J=Path(r'D:/VKO___M_II_220____26LY4SC/interpretation-fourth-100-pages');R=J.parent/'htr-fourth-100-pages'
manifest=json.loads((R/'manifest.json').read_text(encoding='utf-8'))
checked=0;repaired=[]
for p in manifest['pages']:
 f=p['folio'];data=json.loads((J/f/'inputs.json').read_text(encoding='utf-8'))
 working=R/data['source']['working_image'];src=None
 for t in data['tiles']:
  tile=J/f/t['image'];box=t['bbox_xyxy'];bad=None
  try:
   with Image.open(tile) as im:
    im.load();assert im.mode=='RGB' and im.size==(box[2]-box[0],box[3]-box[1])
  except Exception as e:bad=str(e)
  if bad:
   if src is None:
    assert hashlib.sha256(working.read_bytes()).hexdigest()==data['source']['working_image_sha256']
    src=Image.open(working);src.load()
   assert t['source']=='working_image' and t['pixels_scaled'] is False
   fixed=src.crop(box);tmp=tile.with_suffix('.repair.tmp');fixed.save(tmp,format='PNG')
   with Image.open(tmp) as check:check.load();assert check.tobytes()==fixed.tobytes()
   tmp.replace(tile);repaired.append({'folio':f,'tile':t['image'],'error':bad})
   print('REPAIRED',f,t['image'],flush=True)
  checked+=1
 if src is not None:src.close()
result={'status':'passed','pages':len(manifest['pages']),'tiles_loaded':checked,'repaired':repaired,'operation':'PIL full decode; corrupted strips regenerated atomically from verified working-image native crop; valid strips and inputs untouched'}
(J/'native-decode-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result),flush=True)
