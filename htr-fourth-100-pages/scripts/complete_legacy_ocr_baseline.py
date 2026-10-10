from pathlib import Path
import json,hashlib,time,datetime
H=Path(__file__).resolve().parents[1];R=H.parent
while not (H/'prior-outputs-final-check.json').exists():time.sleep(2)
a=H/'previous-artifacts-sha256.json';b=H/'prior-outputs-final-check.json';files=json.loads(a.read_text());meta=json.loads(b.read_text())
for p in sorted((R/'proarc-ocr-pilot-20-pages').rglob('*')):
 if p.is_file() and p.suffix.lower() in ['.json','.jsonl','.xml','.txt','.py','.zip','.md','.html','.rng','.xsd']:
  h=hashlib.sha256()
  with p.open('rb') as f:
   for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
  rel=p.relative_to(R).as_posix();assert rel not in files or files[rel]==h.hexdigest();files[rel]=h.hexdigest()
meta['files_sha256']=files
if 'proarc-ocr-pilot-20-pages' not in meta['source_folders']:meta['source_folders'].append('proarc-ocr-pilot-20-pages')
meta['legacy_ocr_inventory_recorded_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
for p,d in [(a,files),(b,meta)]:
 tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8');tmp.replace(p)
print('BASELINE_COMPLETE',len(files),meta['prior_raw_pages'],meta['prior_segments'],flush=True)
