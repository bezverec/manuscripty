from pathlib import Path
import json,hashlib,datetime,zipfile,functools
from PIL import Image,ImageChops
from lxml import etree as E
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
H=Path(__file__).resolve().parents[1];R=H.parent
def read(p):return json.loads(p.read_text(encoding='utf-8'))
@functools.lru_cache(maxsize=None)
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
class Links(HTMLParser):
 def __init__(self):super().__init__();self.links=[];self.ids=set()
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  for k in ['href','src']:
   if k in a:self.links.append(a[k])
  if 'id' in a:assert a['id'] not in self.ids;self.ids.add(a['id'])
m=read(H/'manifest.json');cb=read(H/'catmus-batch.json');mb=read(H/'medusa-batch.json')
selection=read(H/'selection.json');folios=[p['folio'] for p in m['pages']]
assert folios==[p['folio'] for p in selection['pages']] and len(folios)==len(set(folios))
assert cb['status']==mb['status']=='success' and [p['folio'] for p in cb['pages']]==[p['folio'] for p in mb['pages']]==folios
prior=read(H/'prior-outputs-final-check.json');assert not set(folios)&set(prior['prior_folios'])
checks=[];totals=0
for p in m['pages']:
 o=H/'pages'/p['folio'];c=read(o/'catmus.candidates.json')['lines'];d=read(o/'medusa.candidates.json')['lines'];x=read(o/'comparison.json')['lines'];s=read(o/'segmentation.json')['lines'];jl=[json.loads(l) for l in (o/'medusa.results.jsonl').read_text(encoding='utf-8').splitlines() if l]
 cr=read(o/'catmus-run.json');mr=read(o/'medusa-run.json');ids=[l['id'] for l in c]
 assert len(ids)==len(set(ids)) and len(ids)==cr['segments']==mr['segments']
 assert ids==[l['id'] for l in d]==[l['id'] for l in x]==[l['id'] for l in s]==[l['id'] for l in jl]
 assert sha(R/p['original'])==p['original_sha256']
 assert sha(o/'image.png')==p['working_image_sha256']==cr['image_sha256']==mr['image_sha256']
 assert sha(o/'segmentation.json')==cr['segmentation_sha256']==mr['segmentation_sha256']
 assert mr['model_sha256']==mb['model_sha256'] and mr['max_new_tokens']==mb['max_new_tokens']
 im=Image.open(o/'image.png').convert('RGB'); assert list(im.size)==[p['width'],p['height']]
 with Image.open(R/p['original']) as oi:
  assert p['frame_used']==0;oi.seek(p['frame_used']);original=oi.convert('RGB');assert original.size==im.size
  expected_work=Image.new('RGB',original.size,'white')
  for b in p['regions']:
   assert len(b)==4 and 0<=b[0]<b[2]<=im.width and 0<=b[1]<b[3]<=im.height
   expected_work.paste(original.crop(b),b[:2])
  assert ImageChops.difference(im,expected_work).getbbox() is None
 for a,b,cmp,j,seg in zip(c,d,x,jl,s):
  assert a['image_sha256']==b['image_sha256']==cmp['image_sha256']==sha(o/a['image'])
  assert a['bbox']==b['bbox']==cmp['bbox'] and a['boundary']==b['boundary']==seg['boundary']
  assert a['baseline']==b['baseline']==seg['baseline']
  assert a['raw']==cmp['candidates']['catmus'] and b['raw']==cmp['candidates']['medusa']==j['raw']
  assert len(a['boundary'])>=3 and len(a['baseline'])>=2
  assert all(0<=q[0]<=im.width and 0<=q[1]<=im.height for q in a['boundary']+a['baseline'])
  bb=a['crop_xyxy'];assert len(bb)==4 and 0<=bb[0]<bb[2]<=im.width and 0<=bb[1]<bb[3]<=im.height
  xs=[q[0] for q in a['boundary']];ys=[q[1] for q in a['boundary']]
  assert a['bbox']==[min(xs),min(ys),max(xs)-min(xs),max(ys)-min(ys)]
  crop=Image.open(o/a['image']).convert('RGB');expected=im.crop(a['crop_xyxy'])
  assert crop.size==expected.size and list(crop.size)==b['image_size'] and ImageChops.difference(crop,expected).getbbox() is None
  assert b['ended_with_eos'] or b['hit_token_limit']
  assert b['hit_token_limit']==cmp['medusa_hit_token_limit']
  assert b['image']==a['image'] and isinstance(a['raw'],str) and isinstance(b['raw'],str)
 assert (o/'catmus.raw.txt').read_text(encoding='utf-8')=='\n'.join(a['raw'] for a in c)+'\n'
 assert (o/'medusa.raw.txt').read_text(encoding='utf-8')=='\n'.join(a['raw'] for a in d)+'\n'
 checks.append({'folio':p['folio'],'segments':len(c),'same_source_segment_geometry_and_documented_crops':True,'preprocessing_note':'CATMuS: Kraken rpred internal line extraction and rectification. Medusa: stored rectangular PNG plus processor. No assertion of identical model input tensors.','original_sha256_matches':True,'raw_unicode_json_jsonl_txt_equal':True,'working_zones_pixel_equal_to_master_frame0':True,'line_crops_pixel_equal_to_working_image':True,'medusa_truncated_ids':[a['id'] for a in d if a['hit_token_limit']]});totals+=len(c)
 print(p['folio']+' VALID',flush=True)
# Independently recheck the new OCR XML using bundled ALTO/XLink schemas.
class Resolver(E.Resolver):
 def resolve(self,url,public_id,context):
  if url in ['http://www.loc.gov/standards/xlink/xlink.xsd','https://www.loc.gov/standards/xlink/xlink.xsd']:
   return self.resolve_filename(str(H/'ocr-proarc/schemas/xlink-proarc.xsd'),context)
xp=E.XMLParser(no_network=True);xp.resolvers.add(Resolver())
xsd=E.XMLSchema(E.parse(str(H/'ocr-proarc/schemas/alto-3-0.xsd'),xp))
ocr=read(H/'ocr-proarc/manifest.json');ov=read(H/'ocr-proarc/validation.json');package=read(H/'ocr-proarc/package-check.json')
assert ocr['status']=='success' and [p['folio'] for p in ocr['pages']]==folios
assert ov['all_checks_passed'] and [p['folio'] for p in ov['pages']]==folios and all(p['xsd_valid'] for p in ov['pages']) and package['zip_crc_and_file_hashes_valid']
for p in ocr['pages']:
 xsd.assertValid(E.parse(str(H/'ocr-proarc'/p['ocr_xml']),xp))
 for path,key in [('ocr_xml','ocr_xml_sha256'),('ocr_txt','ocr_txt_sha256'),('provenance','provenance_sha256')]:assert sha(H/'ocr-proarc'/p[path])==p[key]
zip_path=H/'ocr-proarc/proarc-ocr-next-100-pages.zip'
with zipfile.ZipFile(zip_path) as archive:
 assert archive.testzip() is None
 sums=archive.read('SHA256SUMS.txt').decode('utf-8').splitlines()
 for line in sums:
  digest,member=line.split(None,1);member=member.lstrip('*')
  assert hashlib.sha256(archive.read(member)).hexdigest()==digest
zip_members_checked=len(sums)
old=read(H/'previous-artifacts-sha256.json')
previous_inventory=read(R/'htr-third-100-pages/previous-artifacts-sha256.json')
assert all(old.get(rel)==checksum for rel,checksum in previous_inventory.items())
assert all(sha(R/rel)==checksum for rel,checksum in old.items())
expanded=read(H/'prior-outputs-final-check.json');assert all(sha(R/rel)==checksum for rel,checksum in expanded['files_sha256'].items())
html_cache={}
def parsed(p):
 p=p.resolve()
 if p not in html_cache:
  parser=Links();parser.feed(p.read_text(encoding='utf-8'));html_cache[p]=parser
 return html_cache[p]
assert (R/'interpretation-fourth-100-pages/index.html').is_file()
linkcount=0
for fp in [H/'index.html',R/'pilot-index.html']+list((H/'pages').glob('*/comparison.html')):
 parser=parsed(fp)
 for link in parser.links:
  u=urlsplit(link)
  if u.scheme:continue
  target=(fp.parent/unquote(u.path)).resolve() if u.path else fp;assert target.exists(),str(target)
  if u.fragment:
   fparser=parsed(target);assert unquote(u.fragment) in fparser.ids
  linkcount+=1
result={'status':'passed','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pages':checks,'total_segments':totals,'page_count':len(folios),'prior_raw_pages':prior['prior_raw_pages'],'all_raw_pages':prior['prior_raw_pages']+len(folios),'new_ocr_alto_xsd_rechecked':True,'ocr_zip_crc_and_member_sha256_rechecked':True,'ocr_zip_member_hashes_checked':zip_members_checked,'local_html_links_checked':linkcount,'local_html_documents_parsed':len(html_cache),'previous_artifacts_checked':len(old),'previous_inventory_continuity_entries_checked':len(previous_inventory),'previous_artifacts_unchanged':True,'expanded_prior_inventory_checked':len(expanded['files_sha256']),'expanded_inventory_recorded_utc':expanded['recorded_utc'],'expert_reference':False,'cer':None,'wer':None,'does_not_establish_paleographic_correctness':True,'scripts_sha256':{str(p.relative_to(H)):sha(p) for p in sorted((H/'scripts').glob('*.py'))}}
(H/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('ALL_VALID',flush=True)
