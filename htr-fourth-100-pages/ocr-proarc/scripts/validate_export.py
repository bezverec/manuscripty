"""Offline ALTO XSD + selected NDK OCR structural checks, not a full PSP validator."""
from pathlib import Path
import json, hashlib, math, datetime
from lxml import etree as E
HERE=Path(__file__).resolve().parents[1];ROOT=HERE.parents[1]
NS='http://www.loc.gov/standards/alto/ns-v3#'; N={'a':NS}
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def box(e):
 x,y,w,h=[float(e.get(k)) for k in ['HPOS','VPOS','WIDTH','HEIGHT']]
 return [x,y,x+w,y+h]
class Resolver(E.Resolver):
 def resolve(self,url,public_id,context):
  if url in ['http://www.loc.gov/standards/xlink/xlink.xsd','https://www.loc.gov/standards/xlink/xlink.xsd']:
   return self.resolve_filename(str(HERE/'schemas/xlink-proarc.xsd'),context)
parser=E.XMLParser(no_network=True);parser.resolvers.add(Resolver())
schema=E.XMLSchema(E.parse(str(HERE/'schemas/alto-3-0.xsd'),parser))
m=json.loads((HERE/'manifest.json').read_text()); assert m['status']=='success' and len(m['pages'])==100
out={'validated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'ALTO 3.0 XSD, selected NDK OCR required fields, text equality, geometry, hashes. Not full NDK PSP validation or live ProArc import.','pages':[],'full_psp_validated':False,'live_proarc_import_tested':False}
for p in m['pages']:
 xp=HERE/p['ocr_xml'];tp=HERE/p['ocr_txt'];t=E.parse(str(xp));a=t.getroot()
 page=t.find('.//a:Page',N)
 assert page.get('PRINTED_IMG_NR') is None
 schema.assertValid(t)
 assert a.get('SCHEMAVERSION')=='3.0' and E.QName(a).namespace==NS
 assert t.findtext('a:Description/a:MeasurementUnit',namespaces=N)=='pixel'
 assert t.findtext('a:Description/a:sourceImageInformation/a:fileName',namespaces=N)==Path(p['original']).name
 assert page.get('ID')=='f'+p['folio'] and int(page.get('PHYSICAL_IMG_NR'))==p['sequence_in_export']
 assert float(page.get('WIDTH'))==p['width'] and float(page.get('HEIGHT'))==p['height']
 ids=[e.get('ID') for e in t.iter() if e.get('ID')];assert len(ids)==len(set(ids))
 for e in t.iter():
  for k in ['STYLEREFS','PROCESSING','TAGREFS']:
   if e.get(k):assert all(x in ids for x in e.get(k).split())
 for step in t.findall('.//a:OCRProcessing/*',N):
  for name in ['processingDateTime','processingAgency','processingStepDescription','processingSoftware/softwareCreator','processingSoftware/softwareName','processingSoftware/softwareVersion']:
   assert step.findtext('/'.join('a:'+x for x in name.split('/')),namespaces=N)
 for name in ['TopMargin','LeftMargin','RightMargin','BottomMargin','PrintSpace']:
  e=page.find('a:'+name,N);assert e is not None and e.get('ID');box(e)
 ps=page.find('a:PrintSpace',N)
 for block in ps.findall('a:TextBlock',N):
  assert block.get('ID') and block.get('LANG')=='la' and block.get('STYLEREFS') and block.findall('a:TextLine',N)
  for line in block.findall('a:TextLine',N):
   assert line.get('ID') and line.get('STYLEREFS') and line.findall('a:String',N)
   for word in line.findall('a:String',N):assert word.get('ID') and word.get('CONTENT') and not any(c.isspace() for c in word.get('CONTENT')) and 0<=float(word.get('WC'))<=1 and float(word.get('WIDTH'))>0 and float(word.get('HEIGHT'))>0
   for sp in line.findall('a:SP',N):assert sp.get('ID')
 for e in t.iter():
  if e.get('HPOS') is not None:
   b=box(e);assert 0<=b[0]<=b[2]<=p['width'] and 0<=b[1]<=b[3]<=p['height']
   if E.QName(e).localname in ['TextBlock','TextLine','String','SP','HYP']:
    par=e.getparent();parentbox=box(par)
    assert parentbox[0]<=b[0]<=b[2]<=parentbox[2] and parentbox[1]<=b[1]<=b[3]<=parentbox[3],(p['folio'],e.get('ID'),b,parentbox)
 txt=tp.read_bytes();assert not txt.startswith(b'\xef\xbb\xbf') and b'\r' not in txt
 lines=t.findall('.//a:TextLine',N)
 extracted=[''.join(ch.get('CONTENT','') if E.QName(ch).localname in ['String','HYP'] else ' ' if E.QName(ch).localname=='SP' else '' for ch in ln) for ln in lines]
 assert txt.decode('utf-8')=='\n'.join(extracted)+'\n'
 prov=json.loads((HERE/p['provenance']).read_text());rows=[r for r in prov['rows'] if r['export']]
 assert extracted==[r['export'] for r in rows] and [ln.get('ID') for ln in lines]==[r['id'] for r in rows]
 for ln,r in zip(lines,rows):
  assert box(ln)==r['bbox_xyxy']
  ww=[w for w in r['tokens'] if not w['space']]
  for se,w in zip(ln.findall('a:String',N),ww):
   assert se.get('CONTENT')==w.get('string_content',w['text'])
   assert box(se)==w.get('string_bbox_xyxy',w['bbox_xyxy'])
   if w.get('geometry_method'):
    assert w['geometry_method']=='detected_line_envelope_fallback_unlocalized_word' and se.get('TAGREFS')=='f'+p['folio']+'_UnlocalizedWord'
    assert w['polygon']==r['boundary'] and (w['ctc_bbox_original'][0]==w['ctc_bbox_original'][2] or w['ctc_bbox_original'][1]==w['ctc_bbox_original'][3])
   points=w.get('string_polygon',w['polygon'])
   assert box(se)==[math.floor(min(q[0] for q in points)),math.floor(min(q[1] for q in points)),math.ceil(max(q[0] for q in points)),math.ceil(max(q[1] for q in points))]
 # Hyphen pairs: two reciprocal substitutions with identical content; preserve raw delimiter in HYP.
 h1=t.findall('.//a:String[@SUBS_TYPE="HypPart1"]',N);h2=t.findall('.//a:String[@SUBS_TYPE="HypPart2"]',N)
 assert len(h1)==len(h2)==p['hyphenation_pairs']==len(t.findall('.//a:HYP',N))
 assert [h.get('SUBS_CONTENT') for h in h1]==[h.get('SUBS_CONTENT') for h in h2]
 assert all(x.get('SUBS_CONTENT') for x in h1+h2)
 assert len(lines)==p['exported_textlines'] and len(t.findall('.//a:String',N))==p['words']
 for rel,h in prov['source_hashes_before'].items():assert sha(ROOT/rel)==h
 assert sha(ROOT/p['original'])==p['original_sha256']
 p['ocr_xml_sha256']=sha(xp);p['ocr_txt_sha256']=sha(tp);p['provenance_sha256']=sha(HERE/p['provenance'])
 p['zero_width_words']=len([w for w in t.findall('.//a:String',N) if float(w.get('WIDTH'))==0])
 out['pages'].append({'folio':p['folio'],'xsd_valid':True,'ndk_selected_required_fields_valid':True,'txt_exactly_derived_from_alto':True,'geometry_matches_documented_ctc_or_detected_line_envelope':True,'unlocalized_words_line_envelope':p['unlocalized_words_line_envelope'],'coordinates_within_image_and_parent':True,'source_files_unchanged':True,'zero_width_words':p['zero_width_words'],'word_count':p['words']})
out['all_checks_passed']=True;out['totals']=m['totals'];out['schema_sources']=[{'path':'schemas/alto-3-0.xsd','url':'https://www.loc.gov/standards/alto/v3/alto-3-0.xsd','sha256':sha(HERE/'schemas/alto-3-0.xsd')},{'path':'schemas/xlink-proarc.xsd','url':'https://raw.githubusercontent.com/proarc/proarc/21119617e17fbcdfdcfd5d5c653a820ad537567d/proarc-mods/src/main/resources/cz/cas/lib/proarc/mods/xlink.xsd','sha256':sha(HERE/'schemas/xlink-proarc.xsd')}]
(HERE/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(HERE/'validation.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'all_checks_passed':True,'pages':len(out['pages']),'totals':out['totals'],'zero_width_words':sum(p['zero_width_words'] for p in out['pages'])}),flush=True)
