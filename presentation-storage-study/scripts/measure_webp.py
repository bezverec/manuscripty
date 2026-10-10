from pathlib import Path
from PIL import Image,features
import io,json,math,time,datetime,collections
R=Path(__file__).resolve().parents[2];H=Path(__file__).resolve().parents[1]
files=sorted((R/'EX').glob('*.TIF'));sizes=collections.Counter();inventory=[]
for p in files:
 with Image.open(p) as im:
  sizes[im.size]+=1;inventory.append({'name':p.name,'dimensions':list(im.size),'frames':getattr(im,'n_frames',1),'bytes':p.stat().st_size})
(H/'inventory.json').write_text(json.dumps(inventory,indent=2)+'\n',encoding='utf-8')
def pyramid_geometry(w,h,tile=512):
 levels=[];top=math.ceil(math.log2(max(w,h)))
 for level in range(top+1):
  scale=2**(top-level);ww=math.ceil(w/scale);hh=math.ceil(h/scale)
  levels.append({'level':level,'width':ww,'height':hh,'tiles':math.ceil(ww/tile)*math.ceil(hh/tile)})
 return levels
out={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Presentation-size benchmark, no cloud upload. Whole TIFF frame0, not whitened HTR working image. No color-profile conversion applied in this size test.','pillow_version':Image.__version__,'libwebp_version':features.version('webp'),'tile_size':512,'tile_overlap':1,'webp_method':4,'file_count':len(files),'source_bytes':sum(x['bytes'] for x in inventory),'dimension_counts':[{ 'width':wh[0],'height':wh[1],'count':n} for wh,n in sizes.items()],'expected_tile_objects_all_files':sum(sum(x['tiles'] for x in pyramid_geometry(*wh))*n for wh,n in sizes.items()),'samples':[]}
for folio in ['25r','115r','295v']:
 p=R/'EX'/('M_II_220____26LY4SCEX'+folio[:-1].zfill(4)+folio[-1].upper()+'.TIF')
 with Image.open(p) as source:
  source.seek(0);im=source.convert('RGB')
 geom=pyramid_geometry(*im.size);sample={'folio':folio,'original':str(p.relative_to(R)),'dimensions':list(im.size),'levels':geom,'variants':[]}
 for quality in [80,90]:
  t=time.perf_counter();full=io.BytesIO();im.save(full,format='WEBP',quality=quality,method=4)
  tiles_bytes=0;tiles_count=0;level_data=[]
  for g in geom:
   level=im if im.size==(g['width'],g['height']) else im.resize((g['width'],g['height']),Image.Resampling.LANCZOS)
   nb=0;nc=0
   for y in range(0,level.height,512):
    for x in range(0,level.width,512):
     box=(max(0,x-1),max(0,y-1),min(level.width,x+513),min(level.height,y+513))
     tile=io.BytesIO();level.crop(box).save(tile,format='WEBP',quality=quality,method=4);nb+=len(tile.getbuffer());nc+=1
   level_data.append({**g,'bytes':nb});tiles_bytes+=nb;tiles_count+=nc
  variant={'quality':quality,'full_page_webp_bytes':len(full.getbuffer()),'pyramid_webp_bytes':tiles_bytes,'tiles':tiles_count,'levels':level_data,'seconds':time.perf_counter()-t}
  sample['variants'].append(variant);print(json.dumps({'folio':folio,**{k:v for k,v in variant.items() if k!='levels'}}),flush=True)
 out['samples'].append(sample);(H/'measurements.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
out['status']='complete';(H/'measurements.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print('MEASUREMENT_COMPLETE',flush=True)
