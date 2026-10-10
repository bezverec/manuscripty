"""Re-extract CATMuS CTC positions; export ProArc OCR pairs in ALTO 3.0.
Only stored image, segmentation and raw candidates are read; no pilot is modified.
"""
from pathlib import Path
import json, re, math, hashlib, time, datetime, importlib.metadata
from itertools import groupby
import torch
from PIL import Image
from kraken import rpred
from kraken.containers import Segmentation
from kraken.lib import models, ctc_decoder
from lxml import etree as E
HERE=Path(__file__).resolve().parents[1]; ROOT=HERE.parents[1]
NS='http://www.loc.gov/standards/alto/ns-v3#'; XSI='http://www.w3.org/2001/XMLSchema-instance'
MODEL=Path('/models/catmus-medieval-1.6.0.mlmodel')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def save(p,obj): p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def el(p,n,**kw):return E.SubElement(p,'{'+NS+'}'+n,**{k:str(v) for k,v in kw.items()})
def val(p,n,s):el(p,n).text=s

def rect(points):
 pts=list(points); assert pts
 x0=math.floor(min(p[0] for p in pts)); y0=math.floor(min(p[1] for p in pts))
 x1=math.ceil(max(p[0] for p in pts)); y1=math.ceil(max(p[1] for p in pts))
 return [x0,y0,x1,y1]
def union(boxes):return [min(b[0] for b in boxes),min(b[1] for b in boxes),max(b[2] for b in boxes),max(b[3] for b in boxes)]
def attrs(b):return dict(HPOS=b[0],VPOS=b[1],WIDTH=b[2]-b[0],HEIGHT=b[3]-b[1])
def processing(parent,name,date,description,creator,software,version,settings=None):
 s=el(parent,name); val(s,'processingDateTime',date)
 val(s,'processingAgency','Local manuscript pilot M II 220; institutional producer not specified')
 val(s,'processingStepDescription',description)
 if settings:val(s,'processingStepSettings',settings)
 sw=el(s,'processingSoftware'); val(sw,'softwareCreator',creator); val(sw,'softwareName',software); val(sw,'softwareVersion',version)
 return s

items=[]
for folder in ['htr-fourth-100-pages']:
 manifest=json.loads((ROOT/folder/'manifest.json').read_text(encoding='utf-8'))
 items.extend((folder,p) for p in manifest['pages'])
items.sort(key=lambda item:(int(item[1]['folio'][:-1]),item[1]['folio'][-1]))
assert len(items)==100 and len(set(p['folio'] for _,p in items))==100
(HERE/'import').mkdir(exist_ok=True); (HERE/'provenance').mkdir(exist_ok=True)
started=time.perf_counter(); torch.set_num_threads(4)
assert sha(MODEL)=='227d10f15a936c2492105b7796a6152647c742f248af117856f417008eadbc9c'
net=models.load_any(str(MODEL),device='cpu')
# greedy_decoder start/end are inclusive frame indexes. Spatial cuts are
# boundaries, so end+1 preserves the actual full decoded frame interval.
# This does not change predicted labels, confidence, or word grouping.
def half_open_greedy(outputs, seq_lens=None):
 return [[(label,start,end+1,confidence) for label,start,end,confidence in sequence]
         for sequence in ctc_decoder.greedy_decoder(outputs,seq_lens)]
net.decoder=half_open_greedy
report={'created_utc':utc(),'status':'running','engine':{'kraken':importlib.metadata.version('kraken'),'torch':torch.__version__,'device':'cpu','threads':4,'ctc_endpoints':'inclusive to half-open: end+1 before spatial transform','model_sha256':sha(MODEL)},'schema_version':'3.0','namespace':NS,'physical_img_nr_scope':'1..100 in this sorted pilot subset, not asserted full-manuscript scan order','pages':[]}
for ordinal,(folder,pg) in enumerate(items,1):
 folio=pg['folio']; p=ROOT/folder/'pages'/folio
 while True:
  try:
   ready=json.loads((p/'catmus-run.json').read_text())
   if ready['status']=='success':break
  except (FileNotFoundError,json.JSONDecodeError):pass
  time.sleep(1)
 t=time.perf_counter()
 files=[p/'segmentation.json',p/'image.png',p/'catmus.candidates.json',p/'catmus.raw.txt']
 before={str(f.relative_to(ROOT)):sha(f) for f in files}
 assert sha(ROOT/pg['original'])==pg['original_sha256']
 assert sha(p/'image.png')==pg['working_image_sha256']
 candidates=json.loads((p/'catmus.candidates.json').read_text(encoding='utf-8'))['lines']
 seg=Segmentation(**json.loads((p/'segmentation.json').read_text(encoding='utf-8')))
 seg.imagename=str(p/'image.png'); im=Image.open(p/'image.png'); assert im.size==(pg['width'],pg['height'])
 predictions=list(rpred.rpred(net,im,seg)) if candidates else [];  assert len(predictions)==len(candidates)
 diffs=[{'id':c['id'],'previous':c['raw'],'rerun':r.prediction} for c,r in zip(candidates,predictions) if c['raw']!=r.prediction]
 if diffs:
  save(HERE/'provenance'/f'{folio}.differences.json',diffs)
  raise RuntimeError(f'Raw text differs on {folio}; no silent replacement permitted')
 rows=[]; blanks=[]; ws_changes=[]; hyphens=[]
 for c,r in zip(candidates,predictions):
  assert c['id']==r.id and len(r.cuts)==len(r.prediction)==len(r.confidences)
  tokens=[]
  for m in re.finditer(r'\S+|\s+',r.prediction):
   text,poly,conf=r[m.start():m.end()]; b=rect(poly)
   assert 0<=b[0]<=b[2]<=pg['width'] and 0<=b[1]<=b[3]<=pg['height'],(folio,r.id,b)
   tokens.append({'text':text,'start':m.start(),'end':m.end(),'polygon':[list(q) for q in poly],'bbox_xyxy':b,'confidence_mean':float(conf),'space':text.isspace()})
  for token in tokens:
   if not token['space'] and (token['bbox_xyxy'][0]==token['bbox_xyxy'][2] or token['bbox_xyxy'][1]==token['bbox_xyxy'][3]):
    token['ctc_polygon_original']=token['polygon'];token['ctc_bbox_original']=token['bbox_xyxy']
    token['polygon']=[list(q) for q in r.boundary];token['bbox_xyxy']=rect(r.boundary)
    token['geometry_method']='detected_line_envelope_fallback_unlocalized_word'
  words=[x for x in tokens if not x['space']]
  canonical=' '.join(x['text'] for x in words)
  if canonical!=r.prediction:ws_changes.append({'id':r.id,'raw':r.prediction,'export':canonical})
  row={'id':r.id,'region_index':c['region_index'],'raw':r.prediction,'export':canonical,'boundary':r.boundary,'baseline':r.baseline,'tokens':tokens,'char_polygons':r.cuts,'char_confidences':[float(x) for x in r.confidences],'bbox_xyxy':union([rect(r.boundary)]+[x['bbox_xyxy'] for x in tokens])}
  if not words:blanks.append(r.id)
  rows.append(row)
 # Mechanically join only explicit terminal hyphen markers with the next line's first token in the same block.
 for j,row in enumerate(rows[:-1]):
  ww=[x for x in row['tokens'] if not x['space']]
  nxt=rows[j+1]; nw=[x for x in nxt['tokens'] if not x['space']]
  if ww and nw and row['region_index']==nxt['region_index'] and re.search(r'[-¬⸗]$',ww[-1]['text']) and len(ww[-1]['text'])>1:
   first=ww[-1]; second=nw[0]; combined=first['text'][:-1]+second['text']
   first['subs_type']='HypPart1'; second['subs_type']='HypPart2'
   first['subs_content']=second['subs_content']=combined
   r=predictions[j]; start,end=first['start'],first['end']
   text,poly,conf=r[start:end-1]; first['string_content']=text; first['string_polygon']=[list(q) for q in poly]
   first['string_bbox_xyxy']=rect(poly); first['string_confidence_mean']=float(conf)
   htext,hpoly,hconf=r[end-1:end]; first['hyp']={'content':htext,'polygon':[list(q) for q in hpoly],'bbox_xyxy':rect(hpoly)}
   hyphens.append({'part1_line':row['id'],'part2_line':nxt['id'],'raw_parts':[first['text'],second['text']],'subs_content':combined,'status':'mechanical_unreviewed'})
 stem=Path(pg['original']).stem; a=E.Element('{'+NS+'}alto',nsmap={None:NS,'xsi':XSI},SCHEMAVERSION='3.0')
 a.set('{'+XSI+'}schemaLocation',NS+' https://www.loc.gov/standards/alto/v3/alto-3-0.xsd')
 a.append(E.Comment('Unreviewed CATMuS HTR. CTC-derived word polygons; see manifest.json and README.md.'))
 desc=el(a,'Description'); val(desc,'MeasurementUnit','pixel')
 src=el(desc,'sourceImageInformation'); val(src,'fileName',Path(pg['original']).name)
 op=el(desc,'OCRProcessing',ID=f'f{folio}_OCR')
 processing(op,'preProcessingStep',report['created_utc'],'Reuse existing baseline segmentation and native-size RGB frame 0 with white outside pilot writing zones. No scaling, rotation or deskew.','Local pilot scripts','Stored pilot segmentation','1.0',f'image SHA256={sha(p/"image.png")}; segmentation SHA256={sha(p/"segmentation.json")}')
 processing(op,'ocrProcessingStep',utc(),'Rerun CATMuS on stored lines to obtain CTC character positions. Inclusive decoder end converted to exclusive end+1 before spatial transform. Exact code-point equality with existing raw HTR verified.','Kraken contributors','Kraken',report['engine']['kraken'],f'CATMuS medieval 1.6.0; model SHA256={sha(MODEL)}; CPU; torch threads=4')
 processing(op,'postProcessingStep',utc(),'Group CTC spans by whitespace; retain Unicode; normalize whitespace; omit empty predictions; encode explicit terminal hyphens mechanically. TXT extracted from ALTO, LF line endings.','Local pilot scripts','ProArc pilot OCR exporter','1.0')
 styles=el(a,'Styles'); el(styles,'ParagraphStyle',ID=f'f{folio}_PS_Left',ALIGN='Left')
 if any(t.get('geometry_method') for row in rows for t in row['tokens']):
  tags=el(a,'Tags');el(tags,'OtherTag',ID=f'f{folio}_UnlocalizedWord',LABEL='unlocalized_word_line_envelope',DESCRIPTION='Degenerate CTC position: detected text-line envelope used; no word-level localization available.')
 page=el(el(a,'Layout'),'Page',ID=f'f{folio}',WIDTH=pg['width'],HEIGHT=pg['height'],PHYSICAL_IMG_NR=ordinal,PROCESSING=f'f{folio}_OCR')
 nonempty=[r for r in rows if r['export']]; printrect=union([r['bbox_xyxy'] for r in nonempty]) if nonempty else [0,0,im.width,im.height]; x,y,x1,y1=printrect; W,H=im.size
 for name,b in [('TopMargin',[0,0,W,y]),('LeftMargin',[0,y,x,y1]),('RightMargin',[x1,y,W,y1]),('BottomMargin',[0,y1,W,H])]:el(page,name,ID=f'f{folio}_{name}',**attrs(b))
 ps=el(page,'PrintSpace',ID=f'f{folio}_PrintSpace',**attrs(printrect)); wc=0; sc=0; groups=[]
 for gi,(region,rs) in enumerate(groupby(rows,key=lambda r:r['region_index']),1):
  rr=[r for r in rs if r['export']]
  if not rr:continue
  block=el(ps,'TextBlock',ID=f'f{folio}_B{gi:03}',LANG='la',STYLEREFS=f'f{folio}_PS_Left',**attrs(union([r['bbox_xyxy'] for r in rr])))
  groups.append({'id':block.get('ID'),'region_index':region,'line_ids':[r['id'] for r in rr]})
  for row in rr:
   ln=el(block,'TextLine',ID=row['id'],LANG='la',STYLEREFS=f'f{folio}_PS_Left',CS='false',**attrs(row['bbox_xyxy']))
   tok=row['tokens']; words=[(i,t) for i,t in enumerate(tok) if not t['space']]
   for wi,(idx,tokword) in enumerate(words):
    wc+=1; s=el(ln,'String',ID=f'f{folio}_W{wc:05}',CONTENT=tokword.get('string_content',tokword['text']),WC=f"{tokword.get('string_confidence_mean',tokword['confidence_mean']):.6f}",**attrs(tokword.get('string_bbox_xyxy',tokword['bbox_xyxy'])))
    if tokword.get('geometry_method'):s.set('TAGREFS',f'f{folio}_UnlocalizedWord')
    if 'subs_type' in tokword:s.set('SUBS_TYPE',tokword['subs_type']);s.set('SUBS_CONTENT',tokword['subs_content'])
    if wi<len(words)-1:
     between=[t for t in tok[idx+1:words[wi+1][0]] if t['space']]; assert between
     sc+=1; el(ln,'SP',ID=f'f{folio}_SP{sc:05}',**attrs(union([t['bbox_xyxy'] for t in between])))
    if 'hyp' in tokword:el(ln,'HYP',CONTENT=tokword['hyp']['content'],**attrs(tokword['hyp']['bbox_xyxy']))
 xml=E.tostring(a,encoding='UTF-8',xml_declaration=True,pretty_print=True)
 (HERE/'import'/f'{stem}.ocr.xml').write_bytes(xml)
 # Read serialized XML, rather than using raw candidates as TXT source.
 parsed=E.fromstring(xml); textlines=[]
 for ln in parsed.findall('.//{'+NS+'}TextLine'):
  textlines.append(''.join(ch.get('CONTENT','') if E.QName(ch).localname in ('String','HYP') else ' ' if E.QName(ch).localname=='SP' else '' for ch in ln))
 expected=[r['export'] for r in rows if r['export']];assert textlines==expected
 txt='\n'.join(textlines)+'\n'; (HERE/'import'/f'{stem}.ocr.txt').write_bytes(txt.encode('utf-8'))
 provenance={'folio':folio,'source_pilot':folder,'source_hashes_before':before,'rows':rows,'empty_predictions_omitted':blanks,'whitespace_changes':ws_changes,'hyphenation_pairs':hyphens,'blocks':groups}
 save(HERE/'provenance'/f'{folio}.alignment.json',provenance)
 assert before=={str(f.relative_to(ROOT)):sha(f) for f in files}
 result={'folio':folio,'sequence_in_export':ordinal,'original':pg['original'],'original_sha256':pg['original_sha256'],'source_pilot':folder,'source_raw_txt':str((p/'catmus.raw.txt').relative_to(ROOT)),'source_raw_txt_sha256':sha(p/'catmus.raw.txt'),'source_candidates_sha256':sha(p/'catmus.candidates.json'),'working_image_sha256':sha(p/'image.png'),'segmentation_sha256':sha(p/'segmentation.json'),'width':W,'height':H,'frame':0,'ocr_xml':f'import/{stem}.ocr.xml','ocr_txt':f'import/{stem}.ocr.txt','ocr_xml_sha256':sha(HERE/'import'/f'{stem}.ocr.xml'),'ocr_txt_sha256':sha(HERE/'import'/f'{stem}.ocr.txt'),'provenance':f'provenance/{folio}.alignment.json','source_segments':len(rows),'exported_textlines':len(textlines),'words':wc,'spaces':sc,'empty_predictions_omitted':blanks,'whitespace_changed_lines':len(ws_changes),'hyphenation_pairs':len(hyphens),'raw_rerun_differences':0,'unlocalized_words_line_envelope':sum(bool(t.get('geometry_method')) for row in rows for t in row['tokens']),'seconds':round(time.perf_counter()-t,3)}
 report['pages'].append(result);save(HERE/'manifest.json',report)
 print(json.dumps({k:result[k] for k in ['folio','source_segments','exported_textlines','words','raw_rerun_differences','seconds']}),flush=True)
report['status']='success';report['completed_utc']=utc();report['seconds']=round(time.perf_counter()-started,3)
report['totals']={key:sum(p[key] for p in report['pages']) for key in ['source_segments','exported_textlines','words','spaces','whitespace_changed_lines','hyphenation_pairs','raw_rerun_differences','unlocalized_words_line_envelope']}
save(HERE/'manifest.json',report)
print(json.dumps(report['totals']),flush=True)
