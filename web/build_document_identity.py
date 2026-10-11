import os
"""Public manuscript identity and TEI catalogue; source editions remain unchanged."""
from pathlib import Path
import json, re, hashlib, shutil
from copy import deepcopy
from lxml import etree as E
D=Path(__file__).resolve().parent; P=D/'public'; R=Path(os.environ.get("MANUSCRIPT_WORKSPACE",D.parent.parent))
NS='http://www.tei-c.org/ns/1.0'; XML='http://www.w3.org/XML/1998/namespace'; N={'t':NS}
ID='vkol-m-ii-220'; BASE='https://rukopisy.digitalizaty.cz'; URI=BASE+'/rukopisy/'+ID
LIB='Vědecká knihovna v Olomouci'; LIBURI='https://www.vkol.cz/'
SCHEMA=D.parent/'medieval-manuscript-transcription/schemas/tei-p5-4.12.0/tei_all.rng'
backup=D/'pre-document-identity-update-20261011/tei'; backup.mkdir(parents=True,exist_ok=True)
parser=E.XMLParser(resolve_entities=False,no_network=True)
rng=E.RelaxNG(E.parse(str(SCHEMA),parser))
schemaout=P/'schemas/tei-p5-4.12.0/tei_all.rng';schemaout.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(SCHEMA,schemaout)
s=(P/'pilot-data.js').read_text(encoding='utf8'); manifest=json.loads(s.split('=',1)[1].strip().rstrip(';'))
meta={'schema':'manuscripty-document-v1','id':ID,'uri':URI,'title':'M II 220','shelfmark':'M II 220','repository':{'name':LIB,'uri':LIBURI,'settlement':'Olomouc','country':'Česko'},'tei_version':'4.12.0','tei':BASE+'/tei/'+ID+'.xml','reader':BASE+'/rukopis','counts':manifest['counts'],'identifier_authority':'Project Manuscripty; not a library-assigned persistent identifier','editorial_status':'Working research results without expert review','sources':[{'claim':'Repository and shelfmark','evidence':'Explicit user statement, checked against Manuscripta.cz catalogue search','url':'https://manuscripta.cz/search/?page=131'}]}
manifest['document']=meta;(P/'pilot-data.js').write_text('window.PILOT_DATA = '+json.dumps(manifest,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf8')
(P/'document.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def el(parent,tag,text=None,**attrs):
 e=E.SubElement(parent,'{'+NS+'}'+tag,**attrs)
 if text is not None:e.text=text
 return e
def identifier(parent):
 ms=el(parent,'msDesc'); ms.set('{'+XML+'}id',ID)
 mi=el(ms,'msIdentifier');el(mi,'country','Česko');el(mi,'settlement','Olomouc');el(mi,'repository',LIB,ref=LIBURI);el(mi,'idno','M II 220',type='shelfmark');el(mi,'idno',URI,type='URI')
 return ms
checks=[]; pages=[]
for p in manifest['pages']:
 path=P/p['data']; data=json.loads(path.read_text(encoding='utf8'));data.update(document_id=ID,document_uri=URI,repository=meta['repository']);path.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf8');pages.append((p,data))
 for link in data.get('downloads',[]):
  if not link['href'].endswith('.tei.xml'):continue
  xp=P/link['href']; tree=E.parse(str(xp),parser); root=tree.getroot(); text_before=E.tostring(root.find('t:text',N)); facs_before=E.tostring(root.find('t:facsimile',N))
  root.set('{'+XML+'}id','tei-'+ID+'-'+p['folio']);fd=root.find('t:teiHeader/t:fileDesc',N);sd=fd.find('t:sourceDesc',N)
  ms=sd.find('t:msDesc',N)
  if ms is None:ms=identifier(sd)
  original_notes=sd.findall('t:p',N)
  if original_notes:
   additional=el(ms,'additional'); bibliography=el(additional,'listBibl')
   for note in original_notes:
    b=el(bibliography,'bibl');b.text=note.text
    for child in list(note):b.append(child)
    sd.remove(note)
  pub=fd.find('t:publicationStmt',N)
  for child in list(pub):pub.remove(child)
  el(pub,'publisher','Výzkumný pilot Manuscripty');el(pub,'idno',BASE+'/'+link['href'],type='URI');av=el(pub,'availability');el(av,'p','Veřejná prezentace pracovního návrhu bez odborné revize. Knihovna je institucí uchovávající rukopis; není zde označena za vydavatele AI přepisu.')
  # Serialize a corrected offline schema reference without changing body/facsimile.
  out=b'<?xml version="1.0" encoding="UTF-8"?>\n<?xml-model href="../../schemas/tei-p5-4.12.0/tei_all.rng" type="application/xml" schematypens="http://relaxng.org/ns/structure/1.0"?>\n'+E.tostring(root,encoding='UTF-8',pretty_print=True)
  target=backup/link['href'];target.parent.mkdir(parents=True,exist_ok=True)
  if not target.exists():shutil.copyfile(xp,target)
  xp.write_bytes(out)
  probe=E.Element('{'+NS+'}TEI',nsmap={None:NS},version='4.12.0');probe.append(deepcopy(root.find('t:teiHeader',N)));el(el(el(probe,'text'),'body'),'p','Header validation')
  valid=rng.validate(probe);unchanged=text_before==E.tostring(root.find('t:text',N)) and facs_before==E.tostring(root.find('t:facsimile',N))
  if not valid or not unchanged:raise RuntimeError(str(xp)+' '+str(rng.error_log)+' body unchanged='+str(unchanged))
  checks.append({'file':link['href'],'relax_ng_header':True,'text_and_facsimile_unchanged':unchanged})
root=E.Element('{'+NS+'}TEI',nsmap={None:NS},version='4.12.0');root.set('{'+XML+'}id','tei-'+ID);root.set('{'+XML+'}lang','cs')
header=el(root,'teiHeader');fd=el(header,'fileDesc');ts=el(fd,'titleStmt');el(ts,'title','M II 220: popis rukopisu a soupis digitálních snímků');ps=el(fd,'publicationStmt');el(ps,'publisher','Výzkumný pilot Manuscripty');el(ps,'idno',URI,type='URI');av=el(ps,'availability');el(av,'p','Pracovní výzkumná prezentace bez odborné revize. Tento soubor obsahuje identifikaci a odkazy, nikoli souvislý přepis celého rukopisu.')
sd=el(fd,'sourceDesc');identifier(sd);ed=el(header,'encodingDesc');decl=el(ed,'editorialDecl');el(decl,'p','Stálý identifikátor a URI přiděluje tento výzkumný projekt. Signatura M II 220 pochází od instituce uchovávající rukopis. Názvy pasáží a výsledky AI nejsou odborně potvrzeným katalogem. Sedm snímků vazby a předsádky zatím nemá HTR.')
facs=el(root,'facsimile');body=el(el(root,'text'),'body');el(body,'head','Soupis 677 digitálních snímků');listing=el(body,'list')
for p,data in pages:
 sid='surface_'+p['folio'];sf=el(facs,'surface',n=p.get('label',p['folio']),ulx='0',uly='0',lrx=str(data['width']),lry=str(data['height']));sf.set('{'+XML+'}id',sid)
 preview=data['preview'];preview=preview if preview.startswith('https://') else BASE+'/'+preview
 el(sf,'graphic',url=preview,mimeType='image/webp')
 item=el(listing,'item',facs='#'+sid);el(item,'ref',p.get('label',p['folio']),target=BASE+'/rukopis#'+p['folio'])
 if data['lines']:el(item,'note','Pracovní HTR a interpretace bez odborné revize.')
 else:el(item,'note','Zatím bez HTR.' if p.get('kind')=='binding' else 'Bez vybraného hlavního textu.')
 for link in data.get('downloads',[]):
  if link['href'].endswith('.tei.xml'):el(item,'ref','TEI příslušné strany',target=BASE+'/'+link['href'])
if not rng.validate(root):raise RuntimeError(str(rng.error_log))
(P/'tei').mkdir(exist_ok=True);(P/'tei'/f'{ID}.xml').write_bytes(b'<?xml version="1.0" encoding="UTF-8"?>\n<?xml-model href="../schemas/tei-p5-4.12.0/tei_all.rng" type="application/xml" schematypens="http://relaxng.org/ns/structure/1.0"?>\n'+E.tostring(root,encoding='UTF-8',pretty_print=True))
report={'status':'passed','document_id':ID,'document_uri':URI,'tei_version':'4.12.0','schema_sha256':hashlib.sha256(SCHEMA.read_bytes()).hexdigest(),'validation':'Offline Relax NG: complete manuscript description/index plus all modified page headers in TEI wrappers. Existing text and facsimile preserved byte-for-byte in subtree serialization; no XPath 2 Schematron or paleographic validation','pages':len(pages),'whole_document_surfaces':len(facs),'whole_document_is_transcription':False,'public_page_tei_updated':len(checks),'source_editions_unchanged':True,'checks':checks}
(D/'document-identity-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({k:v for k,v in report.items() if k!='checks'},ensure_ascii=False))
