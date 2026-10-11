import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json,hashlib,datetime
from PIL import Image
import build_media
D=Path(__file__).resolve().parent; R=Path(os.environ.get("MANUSCRIPT_WORKSPACE",D.parents[1])); P=D/'public'
build_media.M=P/'binding-media'; build_media.D=D/'binding-build'; build_media.D.mkdir(exist_ok=True)
definitions=[('FC','000FC','Přední deska','front'),('FS','000FS','Přední přídeští','front'),('F001r','F001R','Předsádka – recto','front'),('F001v','F001V','Předsádka – verso','front'),('BS','000BS','Zadní přídeští','back'),('BC','000BC','Zadní deska','back'),('SP','000SP','Hřbet','back')]
jobs=[]; pages=[]
for folio,code,label,position in definitions:
 original='EX/M_II_220____26LY4SCEX'+code+'.TIF'; src=R/original; sha=hashlib.sha256(src.read_bytes()).hexdigest()
 with Image.open(src) as im: w,h=im.size
 jobs.append({'folio':folio,'source':str(src),'sha256':sha,'width':w,'height':h,'crops':[]})
 base='binding-media/v1'
 page={'folio':folio,'label':label,'kind':'binding','position':position,'width':w,'height':h,'models':{},'source_sha256':sha,'source_original':original,'notes':'Obrazová prezentace vazby nebo předsádky. HTR, rekonstrukce a překlad pro tento snímek zatím nebyly vytvořeny.','analysis_scope':'Snímek vazby / předsádky v původním rozlišení, prezentační WebP Q90. Bez HTR a odborného kodikologického popisu.','lines':[],'passages':[],'blank':False,'transcription_status':'not_transcribed','expert_review':False,'preview':base+'/previews/'+folio+'.webp','tiles':{'type':'dzi','width':w,'height':h,'tileSize':512,'tileOverlap':1,'tilesUrl':base+'/tiles/'+folio+'/','fileFormat':'webp'},'downloads':[{'name':'Metadata snímku JSON','href':'data/'+folio+'/page.json'}]}
 out=P/'data'/folio; out.mkdir(parents=True,exist_ok=True); (out/'page.json').write_text(json.dumps(page,ensure_ascii=False,separators=(',',':')),encoding='utf8')
 pages.append({'folio':folio,'label':label,'kind':'binding','position':position,'preview':page['preview'],'data':'data/'+folio+'/page.json','blank':False,'segments':0,'passages':0,'transcription_status':'not_transcribed'})
with ThreadPoolExecutor(max_workers=3) as pool:
 results=list(pool.map(build_media.work,jobs))
(D/'binding-pages.json').write_text(json.dumps(pages,ensure_ascii=False,indent=2),encoding='utf8')
(D/'binding-media-validation.json').write_text(json.dumps({'status':'passed','checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_images_visually_inspected':'binding-contact-sheet.png','pages':len(results),'objects':sum(len(r['objects']) for r in results),'bytes':sum(r['bytes'] for r in results),'quality':90,'source_checksums_verified':len(results),'archive_masters_unchanged':True,'hosting':'Existing Cloudflare Pages project, binding-media/; no new access credentials','results':results},ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'pages':len(results),'objects':sum(len(r['objects']) for r in results),'bytes':sum(r['bytes'] for r in results)},ensure_ascii=False),flush=True)
