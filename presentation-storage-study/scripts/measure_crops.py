from pathlib import Path
from PIL import Image,features
import io,json,time,datetime,collections
R=Path(__file__).resolve().parents[2];H=Path(__file__).resolve().parents[1]
inventory=json.loads((H/'crop-inventory.json').read_text(encoding='utf-8'))
output={'status':'running','recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Presentation-only crop encoding, no source mutation or cloud upload','sampling':inventory['sampling'],'pilot_pages':inventory['pages'],'pilot_crops':inventory['crops'],'pilot_png_bytes':inventory['png_total_bytes'],'pillow_version':Image.__version__,'libwebp_version':features.version('webp'),'webp_method':4,'samples':[]}
for i,item in enumerate(inventory['samples'],1):
 with Image.open(R/item['path']) as src:im=src.convert('RGB')
 row={**item,'width':im.width,'height':im.height,'variants':[]}
 for q in [80,90]:
  t=time.perf_counter();buf=io.BytesIO();im.save(buf,format='WEBP',quality=q,method=4)
  row['variants'].append({'quality':q,'bytes':len(buf.getbuffer()),'seconds':time.perf_counter()-t})
 output['samples'].append(row)
 if i%25==0:
  (H/'crop-measurements.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8');print(json.dumps({'completed':i,'total':len(inventory['samples'])}),flush=True)
output['status']='complete';output['completed_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
(H/'crop-measurements.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8')
print('CROP_MEASUREMENT_COMPLETE',flush=True)
