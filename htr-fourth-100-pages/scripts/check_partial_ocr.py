from pathlib import Path
import json,datetime
from lxml import etree as E
H=Path(__file__).resolve().parents[1]/'ocr-proarc';NS='http://www.loc.gov/standards/alto/ns-v3#';N={'a':NS}
class Resolver(E.Resolver):
 def resolve(self,url,public_id,context):
  if 'xlink.xsd' in url:return self.resolve_filename(str(H/'schemas/xlink-proarc.xsd'),context)
p=E.XMLParser(no_network=True);p.resolvers.add(Resolver());schema=E.XMLSchema(E.parse(str(H/'schemas/alto-3-0.xsd'),p))
m=json.loads((H/'manifest.json').read_text());checked=[]
for x in m['pages']:
 t=E.parse(str(H/x['ocr_xml']));schema.assertValid(t);lines=t.findall('.//a:TextLine',N)
 txt='\n'.join(''.join(c.get('CONTENT','') if E.QName(c).localname in ('String','HYP') else ' ' if E.QName(c).localname=='SP' else '' for c in ln) for ln in lines)+'\n'
 assert (H/x['ocr_txt']).read_bytes()==txt.encode('utf-8')
 for w in t.findall('.//a:String',N):assert float(w.get('WIDTH'))>0 and float(w.get('HEIGHT'))>0
 checked.append(x['folio'])
result={'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Early check of completed OCR pages only: XSD, TXT equality, positive word dimensions. Not final 100-page validation.','pages':checked,'all_checked_passed':True}
(H/'partial-validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'pages_checked':len(checked),'passed':True}),flush=True)
