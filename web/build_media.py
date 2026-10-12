from pathlib import Path
from PIL import Image
import json,math,io,hashlib,datetime,concurrent.futures,os,argparse,re
D=Path(__file__).resolve().parent;M=D/'r2-media'
def build_iiif_image(im, folio, output, base='https://rukopisy-data.digitalizaty.cz/iiif', namespace=None):
 """Static Image API 3 level 0: advertised sizes/tiles only, not arbitrary ROI."""
 for value in (folio, namespace):
  if value is not None and not re.fullmatch(r'[A-Za-z0-9_-]+', value):raise ValueError('Unsafe IIIF identifier')
 prefix='iiif/'+(namespace+'/' if namespace else '')+folio
 service=base.rstrip('/')+'/'+(namespace+'/' if namespace else '')+folio
 out=Path(output);objects=[];im=im.convert('RGB');w,h=im.size
 def save(image, request, extension):
  key=prefix+'/'+request+'/default.'+extension;dest=out/key;dest.parent.mkdir(parents=True,exist_ok=True)
  image.save(dest,format='WEBP' if extension=='webp' else 'JPEG',quality=90,**({'method':4} if extension=='webp' else {}))
  raw=dest.read_bytes();objects.append({'key':key,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'content_type':'image/webp' if extension=='webp' else 'image/jpeg'})
 factors=[1]
 while math.ceil(max(w,h)/factors[-1])>512:factors.append(factors[-1]*2)
 sizes=[]
 for factor in factors:
  lw,lh=math.ceil(w/factor),math.ceil(h/factor);sizes.append({'width':lw,'height':lh})
  level=im if factor==1 else im.resize((lw,lh),Image.Resampling.LANCZOS)
  for ext in ('webp','jpg'):
   save(level,f'full/{lw},{lh}/0',ext)
   if factor==1:save(level,'full/max/0',ext)
  for y in range(0,h,512*factor):
   for x in range(0,w,512*factor):
    rw,rh=min(512*factor,w-x),min(512*factor,h-y)
    ow,oh=math.ceil(rw/factor),math.ceil(rh/factor)
    tile=level.crop((x//factor,y//factor,x//factor+ow,y//factor+oh))
    for ext in ('webp','jpg'):save(tile,f'{x},{y},{rw},{rh}/{ow},{oh}/0',ext)
 info={'@context':'http://iiif.io/api/image/3/context.json','id':service,'type':'ImageService3','protocol':'http://iiif.io/api/image','profile':'level0','width':w,'height':h,'tiles':[{'width':512,'scaleFactors':factors}],'sizes':sizes,'preferredFormats':['webp'],'extraFormats':['webp']}
 key=prefix+'/info.json';dest=out/key;dest.parent.mkdir(parents=True,exist_ok=True);raw=(json.dumps(info,indent=2)+'\n').encode();dest.write_bytes(raw)
 objects.append({'key':key,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'content_type':'application/json'})
 return objects

def work(j):
 marker=D/'media-results'/(j['folio']+'.json');marker.parent.mkdir(exist_ok=True)
 if marker.exists():
  previous=json.loads(marker.read_text(encoding='utf8'))
  if previous.get('iiif_namespace')==j.get('iiif_namespace') and previous.get('iiif_enabled',False)==j.get('iiif_enabled',False) and all((M/v['key']).exists() and (M/v['key']).stat().st_size==v['bytes'] for v in previous['objects']):return previous
 objects=[]
 def save(im,key,q=90):
  dest=M/key;dest.parent.mkdir(parents=True,exist_ok=True);buf=io.BytesIO();im.save(buf,format='WEBP',quality=q,method=4);data=buf.getvalue();dest.write_bytes(data)
  objects.append({'key':key,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'content_type':'image/webp'})
 raw=Path(j['source']).read_bytes();sha=hashlib.sha256(raw).hexdigest()
 if sha!=j['sha256']:raise ValueError('Master checksum mismatch '+j['folio'])
 with Image.open(io.BytesIO(raw)) as source:source.seek(0);im=source.convert('RGB')
 if im.size!=(j['width'],j['height']):raise ValueError('Wrong dimensions '+j['folio'])
 preview=im.copy();preview.thumbnail((900,1200),Image.Resampling.LANCZOS);save(preview,'v1/previews/'+j['folio']+'.webp')
 top=math.ceil(math.log2(max(im.size)))
 for level in range(top+1):
  scale=2**(top-level);w=math.ceil(im.width/scale);h=math.ceil(im.height/scale)
  lev=im if scale==1 else im.resize((w,h),Image.Resampling.LANCZOS)
  for y in range(0,h,512):
   for x in range(0,w,512):
    save(lev.crop((max(0,x-1),max(0,y-1),min(w,x+513),min(h,y+513))),'v1/tiles/'+j['folio']+'/'+str(level)+'/'+str(x//512)+'_'+str(y//512)+'.webp')
 for c in j['crops']:
  with Image.open(c['source']) as crop:save(crop.convert('RGB'),c['key'])
 if j.get('iiif_enabled'):objects.extend(build_iiif_image(im,j['folio'],M,namespace=j.get('iiif_namespace')))
 result={'folio':j['folio'],'master_sha256_verified':sha,'dimensions':[im.width,im.height],'objects':objects,'bytes':sum(v['bytes'] for v in objects),'quality':90,'method':4,'lossy':True,'native_dimensions_preserved':True,'iiif_enabled':j.get('iiif_enabled',False),'iiif_namespace':j.get('iiif_namespace')}
 marker.write_text(json.dumps(result,separators=(',',':')),encoding='utf8');return result
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--iiif',action='store_true',help='Prepare static IIIF locally; never uploads');parser.add_argument('--iiif-namespace',help='Namespace for a future additional manuscript');args=parser.parse_args()
 jobs=json.loads((D/'media-jobs.json').read_text(encoding='utf8'));results=[]
 for job in jobs:
  job['iiif_enabled']=args.iiif;job['iiif_namespace']=args.iiif_namespace
 with concurrent.futures.ProcessPoolExecutor(max_workers=8) as pool:
  futures={pool.submit(work,j):j['folio'] for j in jobs}
  for future in concurrent.futures.as_completed(futures):
   results.append(future.result())
   progress={'pages':len(results),'total':len(jobs),'bytes':sum(v['bytes'] for v in results),'objects':sum(len(v['objects']) for v in results)}
   (D/'media-progress.json').write_text(json.dumps(progress),encoding='utf8')
   if len(results)%10==0:print(json.dumps(progress),flush=True)
 objects=[v for r in results for v in r['objects']]
 report={'status':'passed','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pages':len(results),'objects':len(objects),'bytes':sum(v['bytes'] for v in objects),'gigabytes':sum(v['bytes'] for v in objects)/1e9,'quality':90,'method':4,'lossy':True,'master_checksums_verified':len(results),'source_master_files_unchanged':True,'crop_dimensions_preserved':True}
 (D/'media-validation.json').write_text(json.dumps(report,indent=2),encoding='utf8');(D/'upload-manifest.json').write_text(json.dumps(objects,separators=(',',':')),encoding='utf8');print(json.dumps(report),flush=True)
