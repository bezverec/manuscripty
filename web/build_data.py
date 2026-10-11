import os
from pathlib import Path
import json,shutil
from PIL import Image
R=Path(os.environ.get("MANUSCRIPT_WORKSPACE",Path(__file__).resolve().parents[2]));D=Path(__file__).resolve().parent;P=D/'public'
C=json.loads((R/'interpretation-final-46-pages/completion-validation.json').read_text(encoding='utf8'))
BASE='https://rukopisy-data.digitalizaty.cz/v1'
manifest={'schema':'manuscripty-public-v1','title':'M II 220','scope':'Celý rukopis, vybraný hlavní text; pracovní výsledky bez odborné revize.','pages':[]}
jobs=[];counts={'pages':0,'lines':0,'passages':0,'blank':0};errors=[]
for m in sorted(C['pages'],key=lambda x:(int(x['folio'][:-1]),x['folio'][-1]=='v')):
 f=m['folio']; rawpath=R/m['raw_comparison'].replace('.html','.json'); rd=rawpath.parent; ip=R/m['review'].replace('review.html','reconstruction.json'); ide=ip.parent
 raw=json.loads(rawpath.read_text(encoding='utf8'));rec=json.loads(ip.read_text(encoding='utf8'));out=P/'data'/f;out.mkdir(parents=True,exist_ok=True)
 with Image.open(R/m['source_original']) as im:w,h=im.size
 if f=='20v':
  page=json.loads((D/'sample-20v.json').read_text(encoding='utf8'))
  page['models']['medusa']='Medusa 0.2Line-4B'
  raw_by_id={l['id']:l for l in raw['lines']}
  for line in page['lines']:
   source_rows=[raw_by_id[sid] for sid in line['source_segment_ids']]
   line['raw_htr']['medusa']='\n'.join(v['candidates']['medusa'] for v in source_rows)
   line['medusa_source_segments']=[{'id':v['id'],'raw':v['candidates']['medusa']} for v in source_rows]
   line['medusa_joined_segments']=len(source_rows)>1
   line['hit_token_limit']=any(v.get('medusa_hit_token_limit',False) for v in source_rows)
  for l in page['lines']:
   l['_source_image']=str(R/'design-proposals/knihovna-rukopisu-v2-analyza'/l['image']);l['image']=BASE+'/crops/'+f+'/'+l['id']+'.webp'
 else:
  page={'folio':f,'kind':'segments','width':w,'height':h,'models':{'catmus':'CATMuS medieval 1.6.0','medusa':'Medusa 0.2Line-4B'},'source_sha256':m['source_sha256'],'notes':rec.get('notes_cs',''),'analysis_scope':'Původní HTR po segmentech, geometrie a příznaky; pracovní rekonstrukce a český překlad po pasážích. Samostatná slovní analýza nebyla vytvořena.','lines':[],'passages':[]}
  for l in raw.get('lines',[]):
   page['lines'].append({'id':l['id'],'source_segment_ids':[l['id']],'bbox':l['bbox'],'image':BASE+'/crops/'+f+'/'+l['id']+'.webp','raw_htr':l['candidates'],'words':[],'flags':l.get('review_flags',[]),'note':l.get('visual_review_note_cs'),'hit_token_limit':l.get('medusa_hit_token_limit',False),'_source_image':str(rd/l['image'])})
  for v in rec.get('passages',[]):
   page['passages'].append({'id':v['id'],'title':v['title_cs'],'line_ids':v['source_segment_ids'],'latin':v['latin_reconstruction'],'czech':v['czech_translation'],'notes':v.get('notes_cs',''),'operations':[]})
 page['width']=w;page['height']=h;page['preview']=BASE+'/previews/'+f+'.webp';page['tiles']={'type':'dzi','width':w,'height':h,'tileSize':512,'tileOverlap':1,'tilesUrl':BASE+'/tiles/'+f+'/', 'fileFormat':'webp'}
 page['blank']=m['blank_selected_text'];page['source_original']=m['source_original'];page['expert_review']=False
 downloads=[]
 for fname,src,label in [('comparison.json',rawpath,'Neupravené HTR a geometrie JSON'),('reconstruction.json',ip,'Rekonstrukce a překlad JSON'),('reconstruction.tei.xml',ide/'reconstruction.tei.xml','TEI P5 4.12.0')]:
  if src.exists():shutil.copyfile(src,out/fname);downloads.append({'name':label,'href':'data/'+f+'/'+fname})
 for fname,key,label in [('reconstruction.la.txt','latin','Latinská rekonstrukce TXT'),('translation.cs.txt','czech','Český překlad TXT')]:
  (out/fname).write_text('\n\n'.join(v[key] for v in page['passages'])+'\n',encoding='utf8');downloads.append({'name':label,'href':'data/'+f+'/'+fname})
 if f=='20v':
  for fname in ['transcription.json','edition.tei.xml','diplomatic.txt','expanded.txt']:
   src=R/'design-proposals/knihovna-rukopisu-v2-analyza/data/20v'/fname
   if src.exists():shutil.copyfile(src,out/fname);downloads.append({'name':fname,'href':'data/'+f+'/'+fname})
 page['downloads']=downloads
 ids={l['id'] for l in page['lines']};coverage=set()
 for v in page['passages']:
  if not v['latin'] or not v['czech']:errors.append([f,v['id'],'missing text'])
  if not set(v['line_ids'])<=ids:errors.append([f,v['id'],'unknown line'])
  coverage.update(v['line_ids'])
 if not page['blank'] and coverage!=ids:errors.append([f,'uncovered',list(ids-coverage)])
 crops=[{'source':l.pop('_source_image'),'key':'v1/crops/'+f+'/'+l['id']+'.webp'} for l in page['lines']]
 jobs.append({'folio':f,'source':str(R/m['source_original']),'sha256':m['source_sha256'],'width':w,'height':h,'crops':crops})
 (out/'page.json').write_text(json.dumps(page,ensure_ascii=False,separators=(',',':')),encoding='utf8')
 manifest['pages'].append({'folio':f,'preview':page['preview'],'data':'data/'+f+'/page.json','blank':page['blank'],'segments':len(page['lines']),'passages':len(page['passages'])})
 counts['pages']+=1;counts['lines']+=len(page['lines']);counts['passages']+=len(page['passages']);counts['blank']+=page['blank']
manifest['counts']=counts
(P/'pilot-data.js').write_text('window.PILOT_DATA = '+json.dumps(manifest,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf8')
(D/'media-jobs.json').write_text(json.dumps(jobs,ensure_ascii=False),encoding='utf8')
(D/'data-validation.json').write_text(json.dumps({'status':'passed' if not errors else 'failed','counts':counts,'errors':errors,'master_files_not_modified':True},ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'counts':counts,'errors':errors}),flush=True)
if errors:raise SystemExit(1)
