from pathlib import Path
import hashlib,json,datetime,os
H=Path(__file__).resolve().parents[1];R=H.parent
FOLDERS=['pilot-ten-pages','pilot-next-ten-pages','pilot-third-ten-pages','htr-next-100-pages','htr-second-100-pages','htr-third-100-pages','interpretation-all-pages','interpretation-third-100-pages','pilot-20r-21r','proarc-ocr-pilot-20-pages']
OUT=H/'previous-artifacts-sha256.json'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
if OUT.exists():raise SystemExit('Baseline already exists; refusing to replace it')
files={}
for d in FOLDERS:
 for directory,dirs,names in os.walk(R/d):
  dirs[:]=[x for x in dirs if x not in ['crops','masked-crops','tiles','__pycache__']]
  for name in sorted(names):
   p=Path(directory)/name
   if not p.is_file() or p.suffix.lower() not in ['.json','.jsonl','.xml','.txt','.py','.zip','.md','.html','.rng','.xsd']:continue
   if any(x in ['crops','masked-crops','tiles','__pycache__'] for x in p.parts):continue
   files[p.relative_to(R).as_posix()]=sha(p)
raw=[json.loads((R/d/'manifest.json').read_text(encoding='utf-8')) for d in FOLDERS[:6]]
folios=[p['folio'] for m in raw for p in m['pages']]
assert len(folios)==len(set(folios)), 'Prior manifests contain duplicate folios'
OUT.write_text(json.dumps(files,indent=2)+'\n',encoding='utf-8')
(H/'prior-outputs-final-check.json').write_text(json.dumps({'recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Frozen completed prior raw, interpretation and original 20v text artifacts; master TIFF and derived PNG excluded; root pilot-index intentionally mutable','source_folders':FOLDERS,'prior_raw_pages':len(folios),'prior_segments':sum(int(p['segments']) for d in FOLDERS[:6] for p in json.loads((R/d/'summary.json').read_text(encoding='utf-8'))['pages']),'prior_folios':folios,'files_sha256':files},indent=2)+'\n',encoding='utf-8')
print('PRIOR_HASHES',len(files),'PRIOR_RAW_PAGES',len(folios),flush=True)
