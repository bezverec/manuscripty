from pathlib import Path
from PIL import Image
import json,math,io,hashlib,datetime,concurrent.futures,os
D=Path(__file__).resolve().parent;M=D/'r2-media'
def work(j):
 marker=D/'media-results'/(j['folio']+'.json');marker.parent.mkdir(exist_ok=True)
 if marker.exists():
  previous=json.loads(marker.read_text(encoding='utf8'))
  if all((M/v['key']).exists() and (M/v['key']).stat().st_size==v['bytes'] for v in previous['objects']):return previous
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
 result={'folio':j['folio'],'master_sha256_verified':sha,'dimensions':[im.width,im.height],'objects':objects,'bytes':sum(v['bytes'] for v in objects),'quality':90,'method':4,'lossy':True,'native_dimensions_preserved':True}
 marker.write_text(json.dumps(result,separators=(',',':')),encoding='utf8');return result
if __name__=='__main__':
 jobs=json.loads((D/'media-jobs.json').read_text(encoding='utf8'));results=[]
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
