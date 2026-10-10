from pathlib import Path
from PIL import Image,ImageOps,ImageDraw
import json
R=Path('D:/VKO___M_II_220____26LY4SC');H=R/'htr-fourth-100-pages'
pages=json.loads((H/'candidate-selection.json').read_text())['pages'];out=H/'overviews';out.mkdir(exist_ok=True)
meta=[]
for start in range(0,len(pages),10):
 canvas=Image.new('RGB',(1800,1160),'#eee9df');draw=ImageDraw.Draw(canvas)
 for i,p in enumerate(pages[start:start+10]):
  with Image.open(R/p['original']) as im:
   im.seek(0);im=im.convert('RGB');w,h=im.size
   box=ImageOps.contain(im,(354,550));x=(i%5)*360+(360-box.width)//2;y=(i//5)*580+24
   canvas.paste(box,(x,y));draw.text(((i%5)*360+8,(i//5)*580+4),p['folio']+' '+str(w)+'x'+str(h),fill='black')
   meta.append(dict(p,width=w,height=h,frame_used=0,contact_sheet='overviews/contact-'+str(start//10+1).zfill(2)+'.png',sheet_bbox_xyxy=[x,y,x+box.width,y+box.height],overview_scaled=True))
 canvas.save(out/('contact-'+str(start//10+1).zfill(2)+'.png'))
 print('CONTACT',start//10+1,flush=True)
(H/'overview-inputs.json').write_text(json.dumps(meta,indent=2)+'\n')