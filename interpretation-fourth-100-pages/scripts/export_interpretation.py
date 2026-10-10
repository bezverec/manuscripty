"""Export the 100 new proposed interpretations; write only inside this batch directory."""
from pathlib import Path
import json,html,hashlib,re,datetime
from urllib.parse import urlsplit,unquote
from html.parser import HTMLParser
from zoneinfo import ZoneInfo
from lxml import etree as E
from PIL import Image,ImageChops,ImageDraw
I=Path(__file__).resolve().parents[1]; ROOT=I.parent; HERE=I
assert I.name=='interpretation-fourth-100-pages','Unexpected output directory'
SOURCE_FOLDER='htr-fourth-100-pages'; TARGET=100; PREVIOUS=330; TOTAL=430
WORK_DATE=datetime.datetime.now(ZoneInfo('Europe/Prague')).date().isoformat()
NS='http://www.tei-c.org/ns/1.0'; XML='http://www.w3.org/XML/1998/namespace'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def relative_opened_tiles(d,f):
 """Normalize host-specific evidence paths only in the export view; preserve author JSON."""
 result=[]
 prefixes=['D:/VKO___M_II_220____26LY4SC/interpretation-fourth-100-pages/'+f+'/',str(I/f).replace('\\','/')+'/']
 for value in d['image_inspection']['tiles']:
  s=value.replace('\\','/')
  if not s.startswith('tiles/'):
   prefix=next((p for p in prefixes if s.startswith(p)),None)
   assert prefix is not None,f+' unknown image evidence root: '+s
   s=s[len(prefix):]
  assert s.startswith('tiles/') and '..' not in Path(s).parts
  result.append(s)
 assert len(result)==len(set(result)),f+' duplicate opened tile'
 return result

def el(parent,tag,text=None,**attrs):
 n=E.SubElement(parent,'{'+NS+'}'+tag,**attrs)
 if text is not None:n.text=text
 return n
def appendtext(parent,t):
 if len(parent):parent[-1].tail=(parent[-1].tail or '')+t
 else:parent.text=(parent.text or '')+t
def notation(parent,text):
 """Balanced uncertainty markers. Gaps denote unresolved reading, never asserted physical damage."""
 pos=0
 while pos<len(text):
  if text[pos] not in '⟦[':
   end=pos+1
   while end<len(text) and text[end] not in '⟦[':end+=1
   appendtext(parent,text[pos:end]);pos=end;continue
  op=text[pos];close='⟧' if op=='⟦' else ']';depth=1;j=pos+1
  while j<len(text) and depth:
   if text[j]==op:depth+=1
   elif text[j]==close:depth-=1
   j+=1
  if depth:appendtext(parent,text[pos:]);break
  content=text[pos+1:j-1]
  if content.strip() in ('…','...'):el(parent,'gap',reason='unresolved',extent='unknown')
  else:
   n=el(parent,'supplied' if op=='[' else 'unclear',cert='low',**({'reason':'conjecture'} if op=='[' else {}))
   notation(n,content)
  pos=j

CSS="""body{margin:0;background:#f5f2e9;color:#25221d;font:17px/1.65 system-ui,sans-serif}main{max-width:1280px;margin:auto;padding:28px}h1{line-height:1.25}a{color:#245d80}.badge{color:#863f21;font-weight:650}.lead{max-width:1000px}.passage{background:white;border:1px solid #d8d0bf;border-radius:8px;margin:24px 0;padding:24px}.texts{display:grid;grid-template-columns:1fr 1fr;gap:28px}.reading{white-space:pre-wrap;font:20px/1.7 Georgia,serif;overflow-wrap:anywhere}.sources img{max-width:100%;height:auto;border:1px solid #ddd}.sources figure{margin:16px 0}.notes{background:#f2eee3;padding:12px}details{margin:14px 0}.toolbar{position:sticky;top:0;background:#e7e1d5;padding:12px;z-index:1}input,button{font:inherit;padding:6px}table{border-collapse:collapse;width:100%;background:white}td,th{border:1px solid #d8d0bf;padding:10px;text-align:left}.overview{max-width:100%;max-height:460px}code{overflow-wrap:anywhere}nav{margin:16px 0}footer{padding:24px 0;color:#635b50}@media(max-width:760px){.texts{grid-template-columns:1fr}main{padding:14px}.passage{padding:16px}table{font-size:14px}}"""
def page(title,body):
 return '<!doctype html><html lang="cs"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+html.escape(title)+'</title><style>'+CSS+'</style></head><body><main>'+body+'</main></body></html>'
esc=html.escape
method="""Pracovní návrh frontier asistenta po obrazové četbě. Latinský text obsahuje rozvedené zkratky, redakční interpunkci a místy domněnky; není diplomatickým přepisem ani konzervativní expanzí. Český překlad vychází z tohoto návrhu. ⟦text?⟧ označuje nejisté čtení, [text?] domnělé doplnění a ⟦…⟧ nerozřešenou sekvenci, nikoli automaticky fyzickou ztrátu. Také neoznačená slova zůstávají návrhem. Bez odborné lidské kontroly a referenčního přepisu; CER/WER se nepočítá."""
manifest=read(ROOT/SOURCE_FOLDER/'manifest.json')
sourcepages=manifest['pages']
assert len(sourcepages)==TARGET,'Raw manifest must contain exactly 100 pages'
assert len({p['folio'] for p in sourcepages})==TARGET,'Duplicate raw folios'
assert all(re.fullmatch(r'[1-9][0-9]*[rv]',p['folio']) for p in sourcepages),'Unsafe folio path'
allpages=[{**p,'source_folder':SOURCE_FOLDER} for p in sourcepages if (I/p['folio']/'reconstruction.json').exists()]
assert len(allpages)==TARGET,'Final export requires all 100 definitive reconstruction JSON files'
schema=ROOT/'medieval-manuscript-transcription/schemas/tei-p5-4.12.0/tei_all.rng'
rng=E.RelaxNG(E.parse(str(schema),E.XMLParser(no_network=True,resolve_entities=False)));checks=[];records=[];htmlfiles=[]
save(I/'validation.json',{'status':'running','expert_reference':False})
for src in allpages:
 f=src['folio']; HERE=ROOT/src['source_folder']
 out=I/f;d=read(out/'reconstruction.json');cat=read(HERE/'pages'/f/'catmus.candidates.json')['lines'];med=read(HERE/'pages'/f/'medusa.candidates.json')['lines'];inp=read(out/'inputs.json')
 d['image_inspection']['tiles']=relative_opened_tiles(d,f)
 # Authors may use a string or a list of notes; normalize only the export view.
 def note_text(value):
  if isinstance(value,list):return '\n'.join(note_text(x) for x in value)
  assert isinstance(value,str),'notes_cs must be a string or list of strings'
  return value
 d['notes_cs']=note_text(d['notes_cs'])
 for passage in d['passages']:passage['notes_cs']=note_text(passage['notes_cs'])
 ids=[x['id'] for x in cat];coverage=[s for p in d['passages'] for s in p['source_segment_ids']]
 assert ids==coverage and len(ids)==len(set(ids))
 assert len(cat)==len(med) and [x['id'] for x in med]==ids
 assert d['expert_reference'] is False and d['cer'] is None and d['wer'] is None and not d['cappelli_consulted']
 assert d['folio']==f and d['language']=='la' and d['translator_language']=='cs'
 assert d.get('status','proposed')=='proposed' and d.get('human_reviewed',False) is False
 assert d['source_original']==src['original'] and d['source_folder']==SOURCE_FOLDER
 assert inp['folio']==f and inp['source_folder']==SOURCE_FOLDER and inp['source']=={k:v for k,v in src.items() if k!='source_folder'}
 inspection=d['image_inspection']
 assert inspection['native_pixels'] is True and inspection['original_htr_compared'] is True and inspection['original_medusa_compared'] is True and inspection['masked_htr_compared'] is False
 if src['regions']:
  assert inspection['selected_zones_covered'] is True and inspection['all_selected_zones_opened'] is True
 else:
  assert src.get('blank_main_text') is True and not cat and not med and not d['passages']
  assert inspection['tiles'],'Blank pages require actual native image evidence'
 assert d['source_sha256']==src['original_sha256']==sha(ROOT/src['original'])
 assert sha(HERE/'pages'/f/'image.png')==src['working_image_sha256']
 byid={x['id']:x for x in cat};md=['# Folio '+f+' — pracovní rekonstrukce a český překlad','',method,'',d['notes_cs'],'']
 lat=[];cz=[];sections=[];toc=[]
 for p in d['passages']:
  assert p['latin_reconstruction'].strip() and p['czech_translation'].strip() and p['status']=='proposed' and p['human_reviewed'] is False
  pid=p['id'];ss=p['source_segment_ids'];title=p['title_cs'];toc.append('<a href="#'+pid+'">'+esc(title)+'</a>')
  md.extend(['## '+title,'','Identifikátor: '+pid+'; obrazové segmenty: '+', '.join(ss),'','**Latinský návrh**','',p['latin_reconstruction'],'','**Český překlad**','',p['czech_translation'],'','**Poznámky:** '+p['notes_cs'],''])
  lat.extend([title,p['latin_reconstruction'],'']);cz.extend([title,p['czech_translation'],''])
  sourcehtml=[]
  for sid in ss:
   c=byid[sid];ix=ids.index(sid);url='../../'+src['source_folder']+'/pages/'+f+'/'+c['image']
   raw='<p>CATMuS (původní): <span lang="la">'+esc(c['raw'])+'</span></p><p>Medusa (původní): <span lang="la">'+esc(med[ix]['raw'])+'</span></p>'
   sourcehtml.append('<figure><figcaption>'+esc(sid)+'</figcaption><a href="'+url+'"><img loading="lazy" src="'+url+'" alt="Původní výřez '+esc(sid)+'"></a><details><summary>Neupravené výstupy HTR</summary>'+raw+'</details></figure>')
  sections.append('<article class="passage" id="'+pid+'"><h2>'+esc(title)+'</h2><p class="badge">Návrh · bez odborné kontroly</p><div class="texts"><section><h3>Latinská rekonstrukce</h3><p class="reading" lang="la">'+esc(p['latin_reconstruction'])+'</p></section><section><h3>Český překlad</h3><p class="reading">'+esc(p['czech_translation'])+'</p></section></div>'+('<p class="notes">'+esc(p['notes_cs'])+'</p>' if p['notes_cs'] else '')+'<details class="sources"><summary>Obrazové podklady a HTR ('+str(len(ss))+' segmentů)</summary>'+''.join(sourcehtml)+'</details></article>')
 (out/'reading.md').write_text('\n'.join(md),encoding='utf-8')
 (out/'reconstruction.la.txt').write_text('\n'.join(lat),encoding='utf-8')
 (out/'translation.cs.txt').write_text('\n'.join(cz),encoding='utf-8')
 view='<nav><a href="../index.html">Všechny výkladové návrhy</a> · <a href="../../htr-fourth-100-pages/index.html">Srovnání HTR této etapy</a> · <a href="reading.md">Markdown</a> · <a href="reconstruction.la.txt">Latina TXT</a> · <a href="translation.cs.txt">Čeština TXT</a> · <a href="reconstruction.tei.xml">TEI P5 4.12.0</a> · <a href="reconstruction.json">JSON a evidence četby</a></nav><h1>Folio '+f+'</h1><p class="lead">'+esc(method)+'</p><p>'+esc(d['notes_cs'])+'</p><details><summary>Přehled stránky a nativní výřezy celé vybrané oblasti</summary><a href="../../'+src['source_folder']+'/pages/'+f+'/image.png"><img class="overview" src="../../'+src['source_folder']+'/pages/'+f+'/overview.jpg" alt="Přehled folia '+f+'"></a><ul>'+''.join('<li><a href="'+esc(t)+'">'+esc(t)+'</a></li>' for t in d['image_inspection']['tiles'])+'</ul></details><nav>'+ ' · '.join(toc)+'</nav><div class="toolbar"><label>Hledat v návrhu a překladu <input id="filter" type="search"></label> <button id="all">Zobrazit vše</button></div>'+''.join(sections)+"""<script>const filter=document.getElementById('filter');filter.addEventListener('input',()=>{const q=filter.value.toLocaleLowerCase('cs');document.querySelectorAll('.passage').forEach(p=>p.hidden=!p.querySelector('.texts').textContent.toLocaleLowerCase('cs').includes(q)&&!p.querySelector('h2').textContent.toLocaleLowerCase('cs').includes(q));});document.getElementById('all').addEventListener('click',()=>{filter.value='';filter.dispatchEvent(new Event('input'));});</script>"""+'<footer>Exportováno místně '+WORK_DATE+'. Při další revizi uchovat původní HTR a evidovat opravy.</footer>'
 (out/'review.html').write_text(page('M II 220 · '+f+' · rekonstrukce a překlad',view),encoding='utf-8');htmlfiles.append(out/'review.html')
 tei=E.Element('{'+NS+'}TEI',nsmap={None:NS},attrib={'{'+XML+'}lang':'cs','version':'4.12.0'})
 header=el(tei,'teiHeader');fd=el(header,'fileDesc');ts=el(fd,'titleStmt');el(ts,'title','M II 220, folio '+f+': pracovní latinská rekonstrukce a český překlad')
 resp=el(ts,'respStmt',**{'{'+XML+'}id':'frontier'});el(resp,'resp','Obrazová četba, návrh rekonstrukce a překlad; bez odborné lidské kontroly');el(resp,'name',d['author'])
 ed=el(fd,'editionStmt');el(ed,'edition','Pracovní návrh; export TEI P5 4.12.0, RNG tei_all.rng')
 pub=el(fd,'publicationStmt');el(pub,'p','Místní neveřejný výzkumný pilot, '+WORK_DATE+'. Všechny četby a překlady jsou návrhy.')
 source=el(fd,'sourceDesc');el(source,'p','Digitalizovaný rukopis M II 220; '+d['source_original']+'; SHA-256 '+d['source_sha256']+'. HTR a souřadnice: CATMuS medieval 1.6.0 / Kraken; další podklad: Medusa0.2Line-4B. Původní znění kandidátů se uchovává samostatně.')
 enc=el(header,'encodingDesc');ep=el(enc,'editorialDecl');el(ep,'p',method+' Odstavcové facs ukazuje skutečné polygonové segmenty HTR v pořadí, nikoli ověřené zarovnání jednotlivých slov. unclear má cert=low; supplied reason=conjecture je domněnka; gap reason=unresolved označuje nevyřešenou četbu.')
 prof=el(header,'profileDesc');lu=el(prof,'langUsage');el(lu,'language','Latina',ident='la');el(lu,'language','Čeština',ident='cs')
 rev=el(header,'revisionDesc');el(rev,'change','První výkladový návrh; CER/WER bez reference nestanoveno.',when=WORK_DATE,who='#frontier')
 fac=el(tei,'facsimile');surface=el(fac,'surface',**{'{'+XML+'}id':'f'+f+'_surface','ulx':'0','uly':'0','lrx':str(src['width']),'lry':str(src['height'])})
 el(surface,'graphic',url='../../'+src['source_folder']+'/pages/'+f+'/image.png',width=str(src['width'])+'px',height=str(src['height'])+'px')
 for c in cat:
  pts=' '.join(str(int(x))+','+str(int(y)) for x,y in c['boundary']);x,y,w,h=c['bbox']
  z=el(surface,'zone',**{'{'+XML+'}id':c['id']+'_zone','type':'htr-segment','points':pts,'ulx':str(x),'uly':str(y),'lrx':str(x+w),'lry':str(y+h)})
 text=el(tei,'text');body=el(text,'body');la=el(body,'div',type='reconstruction',**{'{'+XML+'}lang':'la'});el(la,'head','Pracovní latinský návrh')
 for p in d['passages']:
  pp=el(la,'p',**{'{'+XML+'}id':p['id'],'facs':' '.join('#'+x+'_zone' for x in p['source_segment_ids']),'resp':'#frontier'});notation(pp,p['latin_reconstruction'])
 cs=el(body,'div',type='translation',**{'{'+XML+'}lang':'cs'});el(cs,'head','Pracovní český překlad')
 for p in d['passages']:
  pp=el(cs,'p',corresp='#'+p['id'],resp='#frontier');notation(pp,p['czech_translation'])
  if p['notes_cs']:el(cs,'note',p['title_cs']+': '+p['notes_cs'],target='#'+p['id'])
 E.ElementTree(tei).write(str(out/'reconstruction.tei.xml'),encoding='utf-8',xml_declaration=True,pretty_print=True)
 assert rng.validate(tei),str(rng.error_log)
 rec={'folio':f,'status':'proposed','passages':len(d['passages']),'segments':len(cat),'review':f+'/review.html','original_sha256':src['original_sha256'],'reconstruction_sha256':sha(out/'reconstruction.json'),'original_catmus_sha256':sha(HERE/'pages'/f/'catmus.candidates.json'),'original_medusa_sha256':sha(HERE/'pages'/f/'medusa.candidates.json'),'inspected_native_tiles':len(d['image_inspection']['tiles']),'exports_sha256':{n:sha(out/n) for n in ['reading.md','reconstruction.la.txt','translation.cs.txt','review.html','reconstruction.tei.xml']}}
 records.append(rec);checks.append({'folio':f,'segments':len(cat),'passages':len(d['passages']),'all_segments_covered_once_in_order':True,'tei_rng_valid':True,'expert_reference':False,'native_zone_coverage_verified':False})
 if len(records)%25==0:print('INTERPRETATION_EXPORT',len(records),'/',len(allpages),flush=True)

# Verify the pixels of actually opened tiles and their stated coverage.
for check_index,c in enumerate(checks,1):
 f=c['folio'];out=I/f;src=next(x for x in allpages if x['folio']==f);d=read(out/'reconstruction.json');inp=read(out/'inputs.json');HERE=ROOT/src['source_folder']
 d['image_inspection']['tiles']=relative_opened_tiles(d,f)
 assert set(d['image_inspection']['tiles'])<=set(t['image'] for t in inp['tiles']),f+' unknown opened tile'
 with Image.open(HERE/'pages'/f/'image.png') as full:
  mask=Image.new('1',full.size,0);draw=ImageDraw.Draw(mask)
  for t in inp['tiles']:
   if t['image'] not in d['image_inspection']['tiles']:continue
   b=t['bbox_xyxy']
   assert len(b)==4 and all(isinstance(v,int) for v in b),f+' invalid native coordinates'
   assert 0<=b[0]<b[2]<=full.width and 0<=b[1]<b[3]<=full.height,f+' native tile outside source image'
   assert t['pixels_scaled'] is False,f+' scaled tile evidence'
   assert t.get('source','working_image') in ('working_image','original_frame0'),f+' unknown tile source'
   draw.rectangle([b[0],b[1],b[2]-1,b[3]-1],fill=1)
   with Image.open(out/t['image']) as actual:
    if t.get('source')=='original_frame0':
     with Image.open(ROOT/src['original']) as original:
      original.seek(0);expected=original.convert('RGB').crop(b)
    else:expected=full.crop(b)
    assert actual.size==expected.size and actual.mode==expected.mode and ImageChops.difference(actual,expected).getbbox() is None
  if d['image_inspection']['selected_zones_covered']:
   for roi in src['regions']:assert mask.crop(roi).getextrema()==(1,1)
   c['native_zone_coverage_verified']=True
 c['opened_native_tiles_pixel_verified']=True
 if check_index%25==0:print('PIXEL_VALIDATION',check_index,'/',len(checks),flush=True)
summary={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'complete' if len(records)==TARGET else 'in_progress','new_interpretations_completed':len(records),'new_interpretations_target':TARGET,'previous_interpretations':PREVIOUS,'total_interpretations_target':TOTAL,'total_interpretations_completed':PREVIOUS+len(records),'source_folder':SOURCE_FOLDER,'expert_reference':False,'tei_version':'4.12.0','rng_sha256':sha(schema),'pages':records}
save(I/'manifest.json',summary)
body='<h1>M II 220 · čtvrtá stovka rekonstrukcí a českých překladů</h1><p>'+esc(method)+'</p><p>Dokončených návrhů této etapy: '+str(len(records))+' / '+str(TARGET)+'. Předchozích 330 stran zůstává v dřívějších etapách.</p><nav><a href="../htr-fourth-100-pages/index.html">HTR této etapy</a> · <a href="manifest.json">Provenience</a> · <a href="validation.json">Technická validace</a></nav><table><thead><tr><th>Folio</th><th>Návrh</th><th>Pasáže</th><th>Segmenty</th></tr></thead><tbody>'
for rec in sorted(records,key=lambda p:(int(p['folio'][:-1]),p['folio'][-1])):
 body+='<tr><td>'+rec['folio']+'</td><td><a href="'+rec['review']+'">Rekonstrukce a překlad</a></td><td>'+str(rec['passages'])+'</td><td>'+str(rec['segments'])+'</td></tr>'
body+='</tbody></table>'
(I/'index.html').write_text(page('M II 220 · čtvrtá stovka výkladových návrhů',body),encoding='utf-8')
class LocalLinks(HTMLParser):
 def __init__(self):super().__init__();self.links=[];self.ids=set()
 def handle_starttag(self,tag,attrs):
  attrs=dict(attrs)
  if 'id' in attrs:self.ids.add(attrs['id'])
  for k in ('href','src'):
   if k in attrs:self.links.append(attrs[k])
# Read each HTML file at most once while retaining target and fragment checks.
parser_cache={}
def parsed_html(path):
 path=path.resolve()
 if path not in parser_cache:
  assert path.is_file(),str(path)+' missing HTML target'
  parser=LocalLinks();parser.feed(path.read_text(encoding='utf-8'));parser.close()
  parser_cache[path]=parser
 return parser_cache[path]
link_count=0
for hp in [I/'index.html',*htmlfiles]:
 parser=parsed_html(hp)
 for href in parser.links:
  url=urlsplit(href)
  if url.scheme or url.netloc:continue
  target=(hp.parent/unquote(url.path)).resolve() if url.path else hp
  assert target.is_file(),str(hp)+' missing '+href
  if url.fragment and target.suffix.lower() in ('.html','.htm'):
   tp=parsed_html(target);assert unquote(url.fragment) in tp.ids,str(hp)+' missing anchor '+href
  link_count+=1
save(I/'validation.json',{'status':'passed' if len(records)==TARGET else 'passed_for_completed_subset','completed_pages':len(records),'local_html_links_checked':link_count,'local_html_links_valid':True,'local_html_documents_parsed':len(parser_cache),'checks':checks,'tei_rng_version':'4.12.0','tei_rng_valid_files':len(records),'schematron_run':False,'expert_reference':False,'does_not_establish_paleographic_or_translation_correctness':True})
print('INTERPRETATIONS_EXPORTED',len(records),flush=True)
