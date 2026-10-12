"""Refresh frontend hashes, refusing to bless changes to existing research data."""
from pathlib import Path
import hashlib,json,sys
R=Path(__file__).resolve().parents[1];public=R/'web/public';p=R/'docs/web-source-manifest.json'
d=json.loads(p.read_text(encoding='utf8'))
protected=('web/public/data/','web/public/tei/','web/public/schemas/')
protected_files={'web/public/pilot-data.js','web/public/document.json','web/public/structure.json','web/public/summary.json'}
sha=lambda raw:hashlib.sha256(raw).hexdigest()
for item in d['files']:
 if item['path'].startswith(protected) or item['path'] in protected_files:
  raw=(R/item['path']).read_bytes()
  if sha(raw)!=item['sha256'] or len(raw)!=item['bytes']:raise SystemExit('Refusing research-data change: '+item['path'])
images={'.tif','.tiff','.png','.jpg','.jpeg','.webp','.gif','.bmp','.jp2','.avif','.svg','.ico'}
files=[]
for f in sorted(public.rglob('*')):
 if not f.is_file() or f.is_relative_to(public/'pagefind') or f.suffix.lower() in images:continue
 raw=f.read_bytes();files.append({'path':f.relative_to(R).as_posix(),'bytes':len(raw),'sha256':sha(raw)})
d['files']=files;d['frontend_revision']=sys.argv[1] if len(sys.argv)>1 else '20261012-1'
d['copy_policy']='Research snapshot hashes retained. Frontend changes and generated text assets recorded separately; image files and credentials excluded.'
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
print('Manifest updated; existing research hashes unchanged.')
