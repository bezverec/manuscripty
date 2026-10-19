"""Stage only M I 259 text data after complete local audits; never deploy or copy media."""
from __future__ import annotations
import argparse
import copy
import hashlib
import html
import json
import re
import shutil
from pathlib import Path, PureWindowsPath
from lxml import etree as E

DOC = 'vkol-m-i-259'
SITE = 'https://rukopisy.digitalizaty.cz'
URI = SITE + '/rukopisy/' + DOC
READER = SITE + '/rukopis?doc=' + DOC
MEDIA = 'https://rukopisy-data.digitalizaty.cz/v2/' + DOC
TEI = 'http://www.tei-c.org/ns/1.0'
NS = {'t': TEI}
XMLID = '{http://www.w3.org/XML/1998/namespace}id'
SUPPLIER = 'M_I_259_____09Z2NI6_CS.XML'
SUPPLIER_SHA = '896eee4a9a3b80a60bebcd2e409eceede8374807fdd8441efa7cb98472f931b3'
COORD_FIELDS = ('id','sha256','width','height','frame','derived_from_sha256','original_tiff_frame','rotation_ccw_degrees','source_to_coordinate_pixel_edge_affine','bbox_format','origin')
NOTICE = 'Pracovní HTR, rekonstrukce a české překlady bez odborné revize. Identifikátory snímků nejsou ověřenou původní foliací.'

def read(path): return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def require(condition, message):
    if not condition: raise ValueError(message)
def dump(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')
def parse(path): return E.parse(str(path), E.XMLParser(resolve_entities=False, no_network=True))
def q(name): return '{'+TEI+'}'+name
def safe(value):
    require(isinstance(value,str) and re.fullmatch(r'[A-Za-z0-9_-]+',value), 'Unsafe identifier: '+str(value)); return value
def basename(value): return PureWindowsPath(value).name
def label(folio):
    return {'FC':'Přední deska','FS':'Přední přídeští','F001R':'Přední předsádka · recto','F001V':'Přední předsádka · verso','B001R':'Zadní předsádka · recto','B001V':'Zadní předsádka · verso','BS':'Zadní přídeští','BC':'Zadní deska','SP':'Hřbet','extra-83v':'Dodatečný snímek extra-83v','extra-84r':'Dodatečný snímek extra-84r'}.get(folio,'Snímek '+folio)
def physical_ids():
    out=['FC','FS','F001R','F001V']
    for n in range(1,181):
        for s in ('r','v'):
            f=f'{n}{s}';out.append(f)
            if f=='83v':out.append('extra-83v')
            if f=='84r':out.append('extra-84r')
    return out+['B001R','B001V','BS','BC','SP']

def publication_gate(source):
    manifest=read(source/'manifest.json'); entries={p['folio']:p for p in manifest['pages']}; ids=set(physical_ids())
    require(len(manifest['pages'])==371 and set(entries)==ids,'Expected the complete 371-scan inventory')
    progress=read(source/'progress.json')
    require(progress['status'] in ('complete','complete_with_review'),'Processing is not complete')
    require(all(progress.get(k)==371 for k in ('total_scans','both_models','author_drafts','interpretation_exported')),'Incomplete progress counts')
    require(len(progress['pages'])==371 and set(p['folio'] for p in progress['pages'])==ids and all(p.get('both_models') and p.get('author_draft_available') and p.get('interpretation_exported') for p in progress['pages']),'Incomplete page progress')
    reports={}
    for name,count in [('full-output-validation.json','validated_pages'),('final-source-validation.json','validated_sources')]:
        audit=read(source/name)
        require(audit.get('status')=='passed' and not audit.get('errors') and audit.get(count)==371 and len(audit['pages'])==371 and {p['folio'] for p in audit['pages']}==ids,'Final audit not passed: '+name)
        reports[name]=sha(source/name)
    audit=read(source/'interpretation-validation.json'); pilot=read(source/'pilot-evidence-validation.json')
    reused={f for f,p in entries.items() if p.get('reused_pilot')}
    require(len(reused)==10 and pilot.get('status')=='passed' and len(pilot['pages'])==10 and {p['folio'] for p in pilot['pages']}==reused,'Ten original pilot records must be validated')
    require(not audit.get('errors') and audit.get('validated_drafts')==361 and len(audit['pages'])==361 and {p['folio'] for p in audit['pages']}==ids-reused,'All 361 new interpretation drafts must be audited')
    for item in audit['pages']:
        require(sha(source/'interpretation'/(item['folio']+'.author.json'))==item['author_sha256'],'Author draft changed after audit: '+item['folio'])
    coordinates=read(source/'publication-coordinate-sources/index.json')
    require(coordinates.get('status')=='passed' and set(coordinates['pages'])==ids,'Coordinate raster inventory incomplete')
    for f in ids:
        require((source/'interpretation'/(f+'.author.json')).is_file() and (source/'pages'/f/'comparison.json').is_file(),'Missing author/comparison: '+f)
    for name in ['interpretation-validation.json','pilot-evidence-validation.json','publication-coordinate-sources/index.json','progress.json','manifest.json']:
        reports[name]=sha(source/name)
    return manifest,entries,coordinates['pages'],reports

def coordinate_source(record,entry):
    c={k:copy.deepcopy(record[k]) for k in COORD_FIELDS}
    require(c['derived_from_sha256']==entry['original_sha256'] and (c['width'],c['height'])==(entry['width'],entry['height']),'Coordinate/TIFF identity mismatch')
    require(c['origin']=='top-left' and c['bbox_format']=='xywh' and c['frame']==0,'Invalid coordinate system')
    require(all(re.fullmatch('[a-f0-9]{64}',c[k]) for k in ('sha256','derived_from_sha256')),'Invalid coordinate hash')
    expected={0:[[1,0,0],[0,1,0],[0,0,1]],90:[[0,1,0],[-1,0,c['height']],[0,0,1]],180:[[-1,0,c['width']],[0,-1,c['height']],[0,0,1]],270:[[0,-1,c['width']],[1,0,0],[0,0,1]]}
    require(c['source_to_coordinate_pixel_edge_affine']==expected.get(c['rotation_ccw_degrees']),'Wrong pixel-edge affine')
    return c

def page_data(entry, comparison, interpretation, coordinate):
    f=safe(entry['folio']); lines=[]; ids=[]
    for row in comparison['lines']:
        rid=safe(row['id']); require(rid not in ids,'Duplicate line ID');ids.append(rid)
        x,y,x1,y1=row['bbox_xyxy'];require(all(isinstance(v,int) for v in (x,y,x1,y1)) and 0<=x<x1<=entry['width'] and 0<=y<y1<=entry['height'],'Invalid box '+rid)
        candidates=row['candidates'];require(set(candidates)=={'catmus','medusa'} and all(isinstance(v['raw'],str) for v in candidates.values()),'Both original HTR candidates required')
        medusa=candidates['medusa'];flags=list(row.get('review_flags',[])); notes=[]
        if medusa.get('hit_token_limit'):flags.append('medusa_token_limit');notes.append('Medusa dosáhla limitu generování; výstup může být nedokončený.')
        if medusa.get('decoding_recovery'):flags.append('medusa_changed_decoding_unreviewed');notes.append('Obnovovací běh Medusy se změněným dekódováním (repetition_penalty 1,08); původní předchozí výstup je zachován ve výzkumných datech. Není odborně ověřeno.')
        lines.append({'id':rid,'source_segment_ids':[rid],'bbox':[x,y,x1-x,y1-y],'image':f'{MEDIA}/crops/{f}/{rid}.webp','raw_htr':{k:v['raw'] for k,v in candidates.items()},'words':[],'flags':list(dict.fromkeys(flags)),'note':' '.join(notes) or None,'hit_token_limit':bool(medusa.get('hit_token_limit')),'decoding_recovery':copy.deepcopy(medusa.get('decoding_recovery',False))})
    units=interpretation['units']; require([i for u in units for i in range(u['start'],u['end']+1)]==list(range(1,len(lines)+1)),'Interpretation index coverage differs: '+f)
    passages=[]
    for i,u in enumerate(units,1):
        require(u['reconstruction'] and u['translation_cs'],'Empty interpretation unit')
        passages.append({'id':safe(u.get('id',f'u_{f}_{i:03}')),'title':u.get('title',f'Úsek {i}'),'line_ids':ids[u['start']-1:u['end']],'latin':u['reconstruction'],'czech':u['translation_cs'],'notes':u.get('note_cs',''),'operations':[],'language':u.get('language',interpretation.get('language','la'))})
    supplemental=[]
    for v in interpretation.get('supplemental_readings',[]):
        sid=safe(v['id']);supplemental.append({k:copy.deepcopy(v[k]) for k in ('id','source_region_xyxy','crop_rotation_ccw_degrees','reconstruction','translation_cs','note_cs')})
        supplemental[-1].update(image=f'{MEDIA}/supplemental/{f}/{sid}.webp',status='proposed',expert_review=False)
    blank=not lines
    return {'folio':f,'label':label(f),'kind':'segments','width':entry['width'],'height':entry['height'],'models':{'catmus':'CATMuS medieval 1.6.0','medusa':'Medusa 0.2Line-4B'} if lines else {},'source_original':'EX/'+basename(entry['source']),'source_sha256':entry['original_sha256'],'coordinate_source':coordinate,'language':interpretation.get('language',entry.get('language','und')),'analysis_scope':'Oba původní HTR kandidáti po stejných segmentech. Samostatné doplňkové obrazové čtení není HTR. '+NOTICE,'notes':NOTICE,'lines':lines,'passages':passages,'supplemental_readings':supplemental,'preview':f'{MEDIA}/previews/{f}.webp','tiles':{'type':'dzi','width':entry['width'],'height':entry['height'],'tileSize':512,'tileOverlap':1,'tilesUrl':f'{MEDIA}/tiles/{f}/','fileFormat':'webp'},'blank':blank,'expert_review':False,'downloads':[],'document_id':DOC,'document_uri':URI,'repository':{'name':'Vědecká knihovna v Olomouci','uri':'https://www.vkol.cz/','settlement':'Olomouc','country':'Česko'}}

def web_tei(path,dest,folio,coordinate,validator,document=False):
    tree=parse(path); root=tree.getroot(); ms=root.find('.//'+q('msDesc')); before=E.tostring(ms,method='c14n') if document else None
    original_text=E.tostring(root.find(q('text')),method='c14n') if not document else None
    for g in root.xpath('//t:facsimile//t:graphic',namespaces=NS):
        parent=g.getparent(); scan=parent.get('n') if document else folio
        g.set('url',READER+'#'+scan)
    if not document:
        for d in root.xpath('//t:msDesc[@corresp]',namespaces=NS):d.set('corresp',SITE+'/tei/'+DOC+'.xml#ms-'+DOC)
    header=root.find(q('teiHeader')); enc=header.find(q('encodingDesc'))
    if enc is None:
        enc=E.Element(q('encodingDesc'));header.insert(1,enc)
    p=E.SubElement(enc,q('p'));p.text='Web derivative. Graphic URI resolves to the tiled viewer, not a standalone bitmap or the archival TIFF. Geometry uses pixels of the full unmasked oriented coordinate PNG, identified with its SHA256 and TIFF-to-coordinate pixel-edge affine in the corresponding page.json. Model input masks are recorded separately. Source readings and zones are unchanged. This document is an index and working data, not a complete scholarly edition.'
    if coordinate:
        p=E.SubElement(enc,q('p'));p.text='Coordinate raster '+coordinate['id']+'; PNG SHA256 '+coordinate['sha256']+'; archival TIFF SHA256 '+coordinate['derived_from_sha256']+'; TIFF frame '+str(coordinate['original_tiff_frame'])+'; counterclockwise rotation '+str(coordinate['rotation_ccw_degrees'])+' degrees; TIFF-to-coordinate pixel-edge homogeneous matrix '+json.dumps(coordinate['source_to_coordinate_pixel_edge_affine'])+'. These are not the coordinates of the unrotated TIFF; archival ALTO remains in TIFF coordinates.'
    if document:
        facsimile=root.find(q('facsimile'));order={f:i for i,f in enumerate(physical_ids())}
        if facsimile is not None:
            surfaces=list(facsimile);require(all(s.tag==q('surface') and s.get('n') in order for s in surfaces),'Unknown document surface')
            facsimile[:]=sorted(surfaces,key=lambda s:order[s.get('n')])
        pub=root.find(q('teiHeader')+'/'+q('fileDesc')+'/'+q('publicationStmt')); pp=pub.find(q('p'))
        E.SubElement(pp,q('ref'),target=URI).text='Veřejný záznam rukopisu'
        body=root.find(q('text')+'/'+q('body'));body.clear();E.SubElement(body,q('p')).text='Úplný převzatý katalogový popis a index 371 snímků. Nejde o úplnou odbornou edici. '+NOTICE
        for f in physical_ids():E.SubElement(E.SubElement(body,q('p')),q('ref'),target=READER+'#'+f).text=label(f)
        require(E.tostring(ms,method='c14n')==before,'msDesc changed during publication')
    else:require(E.tostring(root.find(q('text')),method='c14n')==original_text,'TEI readings changed during publication')
    validator.assertValid(tree);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_bytes(b'<?xml version="1.0" encoding="UTF-8"?>\n<?xml-model href="/schemas/tei-p5-4.12.0/tei_all.rng" type="application/xml" schematypens="http://relaxng.org/ns/structure/1.0"?>\n'+E.tostring(tree,encoding='utf-8'))

def catalogue_html(source):
    import supplier_descriptions as sd
    sd.LABELS['handDesc']='Písmo a písařské ruce';sd.CONTAINERS.add('handDesc')
    root=parse(source).getroot();require(not root.getroottree().docinfo.doctype,'Supplier DTD forbidden')
    ms=root.find('.//msDesc');require(ms is not None,'Missing supplied msDesc')
    block,item=sd.renderer(DOC,set());contents=ms.find('msContents')
    catalogue='<article id="katalogovy-obsah"><h2>Katalogový obsah kodexu</h2><p>Původní katalogové rozsahy jsou zachovány; jejich přiřazení k identifikátorům skenů není úplně ověřeno.</p>'+''.join(item(n) for n in contents.findall('msItem'))+'</article>'
    description='<article id="zdrojovy-popis"><h2>Úplný popis podle dodaného XML</h2><p>Převzato z podkladů Vědecké knihovny v Olomouci, včetně fyzického popisu, vazby, historie a poznámek. Nejde o nezávislou odbornou revizi.</p><p><a href="/metadata/'+DOC+'/supplier.xml">Původní XML</a> · <a href="/metadata/'+DOC+'/description.json">Strukturovaný popis JSON</a></p>'+''.join(block(n) for n in ms if n.tag!='msContents')+'</article>'
    classifications=root.findall('.//catDesc')
    if classifications:description=description.replace('</article>','<section><h3>Klasifikace zdrojového popisu</h3>'+''.join('<p>'+html.escape(''.join(n.itertext()))+'</p>' for n in classifications)+'</section></article>')
    return catalogue,description,{'schema':'manuscripty-supplier-description-v1','document_id':DOC,'source_sha256':SUPPLIER_SHA,'source':'/metadata/'+DOC+'/supplier.xml','description':sd.tree(ms)}

def summary_data(research,pages,source):
    by={p['folio']:p for p in pages};sections=[]
    for i,s in enumerate(research['sections'],1):
        evidence=[]
        for ev in s['evidence']:
            f=ev['scan_id'];require(f in by,'Summary scan ID unknown')
            require(sha(source/ev['author_record'])==ev['author_sha256'] and sha(source/ev['inspection_record'])==ev['inspection_sha256'],'Summary evidence changed: '+f)
            evidence.append({'folio':f,'url':READER+'&vrstva=vyklad#'+f,'source_sha256':by[f]['source_sha256'],'author_sha256':ev['author_sha256'],'inspection_sha256':ev['inspection_sha256'],'evidence_url':'/data/'+DOC+'/'+f+'/evidence.json'})
        sections.append({'id':'ai-section-'+str(i),'title':s['title'],'text_cs':s['text_cs'],'sources':evidence})
    return {'schema':'manuscripty-ai-summary-v1','document_id':DOC,'status':'proposed','expert_review':False,'description_cs':'Obrazově podložený výklad AI; odlišen od převzatých katalogových údajů.','sections':sections,'limits_cs':research['limits_cs'],'foliation_review_url':'/data/'+DOC+'/foliation-review.json'}

def render_record(doc,summary,catalogue,description):
    e=html.escape
    ai='<article id="ai-shrnuti"><h2>Výklad AI</h2><p class="sample-notice">'+e(NOTICE)+'</p>'
    for s in summary['sections']:
        ai+='<section id="'+s['id']+'"><h3>'+e(s['title'])+'</h3><p>'+e(s['text_cs'])+'</p><p>Obrazové podklady: '+', '.join('<a href="'+e(v['url'],quote=True)+'">'+e(label(v['folio']))+'</a>' for v in s['sources'])+'</p></section>'
    limits=summary['limits_cs'];ai+='<h3>Meze výkladu</h3>'+(''.join('<p>'+e(x)+'</p>' for x in limits) if isinstance(limits,list) else '<p>'+e(limits)+'</p>')+'</article>'
    record='<!DOCTYPE html><html lang="cs"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>'+e(doc['title'])+'</title><link rel="canonical" href="'+URI+'"><link rel="stylesheet" href="/styles.css"><link rel="stylesheet" href="/catalogue.css"></head><body><header class="site-header"><div class="container"><a class="brand" href="/">Rukopisy, snímek po snímku.</a></div></header><main class="container section"><h1>'+e(doc['title'])+'</h1><p>Vědecká knihovna v Olomouci · M I 259 · 1. polovina 15. století (katalogový údaj)</p><div class="hero-actions"><a class="btn btn--primary" href="'+e(READER,quote=True)+'">Otevřít celý rukopis</a><a class="btn" href="#ai-shrnuti">Výklad AI</a><a class="btn" href="#zdrojovy-popis">Popis a zdroje</a><a class="btn" href="/tei/'+DOC+'.xml">TEI P5 4.12.0</a></div><p class="sample-notice">'+e(NOTICE)+'</p>'+ai+description+catalogue+'<article id="foliace"><h2>Číslování a identifikátory</h2><p>Identifikátory zachovávají názvy skenů. Katalog upozorňuje na nerozřezaný dvojlist 83/84; na několika pozdějších listech je psané číslo o jedno vyšší. Souvislý posun není úplně ověřen. Dodatečné snímky extra-83v a extra-84r jsou samostatné, bez ztotožnění se standardními snímky.</p><a href="/data/'+DOC+'/foliation-review.json">Doklady a pracovní závěry k foliaci</a></article><article><h2>Zpracování a zdroje</h2><p>Segmentace <a href="https://kraken.re/main/index.html">Kraken</a>, HTR <a href="https://zenodo.org/records/15030337">CATMuS medieval 1.6.0</a> a <a href="https://huggingface.co/ENC-PSL/Medusa0.2Line-4B">Medusa 0.2Line-4B</a>. Původní výstupy jsou oddělené od návrhů rekonstrukce a českého překladu.</p><p>Plný orientovaný nemaskovaný obraz určuje souřadnice ve webu. Deset pilotních modelových vstupů má bílé masky; jejich identita je vedena zvlášť. ALTO ke stažení používá souřadnice původního TIFF. Změněné dekódování a limity Medusy jsou označeny u příslušných segmentů.</p></article></main></body></html>'
    from digitization_support import decorate_record
    from color_theme import decorate
    return decorate(decorate_record(record))

def build(args):
    source=args.source.resolve();base=args.base_public.resolve();out=args.out.resolve();reports=args.report_dir.resolve()
    require(source.is_dir() and base.is_dir(),'Source and base-public must exist')
    require(not out.exists() and not reports.exists(),'Output and report directories must be new')
    for target in (out,reports):
        require(not target.is_relative_to(source) and not target.is_relative_to(base) and not source.is_relative_to(target) and not base.is_relative_to(target),'Output must be disjoint from research and base-public')
    require(not out.is_relative_to(reports) and not reports.is_relative_to(out),'Output and reports must be disjoint')
    manifest,entries,coords,audits=publication_gate(source)
    require(sha(source/SUPPLIER)==SUPPLIER_SHA,'Supplied metadata changed')
    validator=E.RelaxNG(parse(args.rng));validator.assertValid(parse(source/'exports/document-metadata.tei.xml'))
    out.mkdir(parents=True);reports.mkdir(parents=True)
    pages=[];headers=[]
    for f in physical_ids():
        entry=entries[f];comparison=read(source/'pages'/f/'comparison.json');interpretation=read(source/'interpretation'/(f+'.json'))
        own=read(source/'interpretation'/(f+'.author.json'));reused=bool(entry.get('reused_pilot'))
        require(own.get('status','proposed' if reused else None)=='proposed' and own.get('expert_review',False if reused else None) is False,'Unexpected author status')
        fp=hashlib.sha256(json.dumps([[r['bbox_xyxy'],r['boundary'],r['baseline']] for r in comparison['lines']],sort_keys=True,separators=(',',':')).encode()).hexdigest()
        require(interpretation['geometry_fingerprint']==fp and own.get('geometry_fingerprint',fp if reused else None)==fp,'Interpretation geometry changed')
        require([u['reconstruction'] for u in interpretation['units']]==[u['reconstruction'] for u in own['units']] and [u['translation_cs'] for u in interpretation['units']]==[u['translation_cs'] for u in own['units']],'Canonical/author reading mismatch')
        coordinate=coordinate_source(coords[f],entry);page=page_data(entry,comparison,interpretation,coordinate)
        page['model_input']=copy.deepcopy(coords[f]['model_input']);dest=out/'data'/DOC/f;dest.mkdir(parents=True)
        prefix='/data/'+DOC+'/'+f+'/'
        def copy_file(path,name,title):
            require(path.is_file(),'Missing publication source: '+str(path));shutil.copyfile(path,dest/name)
            require(sha(path)==sha(dest/name),'Copied bytes changed');page['downloads'].append({'name':title,'href':prefix+name})
        # Public comparison exposes original strings/geometries, without machine paths.
        public_comparison={'folio':f,'source_original':page['source_original'],'source_sha256':page['source_sha256'],'coordinate_source':coordinate,'geometry_fingerprint':interpretation['geometry_fingerprint'],'lines':[{k:copy.deepcopy(r[k]) for k in ('id','bbox_xyxy','boundary','baseline','image_sha256','candidates') if k in r} for r in comparison['lines']],'expert_review':False}
        dump(dest/'comparison.json',public_comparison);page['downloads'].append({'name':'Neupravené HTR a geometrie JSON','href':prefix+'comparison.json'})
        for model in ('catmus','medusa'):
            copy_file(source/'exports'/f'{f}-{model}.txt',model+'.raw.txt',model+' · původní TXT')
            require((dest/(model+'.raw.txt')).read_bytes().decode('utf-8')=='\n'.join(l['raw_htr'][model] for l in page['lines']),'Raw TXT identity differs')
            copy_file(source/'exports'/f'{f}-{model}.alto.xml',model+'.alto.xml',model+' · ALTO (souřadnice původního TIFF)')
        copy_file(source/'exports'/f'{f}.tei.xml','edition.tei.xml','Oba HTR a interpretace · původní místní TEI P5 4.12.0')
        web_tei(source/'exports'/f'{f}.tei.xml',dest/'edition.web.tei.xml',f,coordinate,validator)
        page['downloads'].append({'name':'Oba HTR a interpretace · TEI s webovými odkazy','href':prefix+'edition.web.tei.xml'})
        public_interpretation={k:copy.deepcopy(interpretation[k]) for k in ('folio','language','status','expert_review','geometry_fingerprint','units','supplemental_readings') if k in interpretation}
        dump(dest/'reconstruction.json',public_interpretation);page['downloads'].append({'name':'Rekonstrukce a překlad JSON (původní jednotky)','href':prefix+'reconstruction.json'})
        for suffix,name,title in [('reconstruction.txt','reconstruction.txt','Rekonstrukce TXT'),('translation.cs.txt','translation.cs.txt','Český překlad TXT')]:copy_file(source/'interpretation'/f'{f}.{suffix}',name,title)
        if reused:
            inspection_path=source/'pilot-inspection-record.json'
            historical=next(v for v in read(inspection_path)['pages'] if v['folio']==f)
            pilot_validation_path=source/'pilot-evidence-validation.json'
            retained=next(v for v in read(pilot_validation_path)['pages'] if v['folio']==f)
            images=retained['images']
            recorded=historical['image_sheets_opened_by_assistant']+historical['additional_individual_crops_opened_by_assistant']
            require(set(recorded)=={v['path'] for v in images},'Reused pilot evidence inventory differs: '+f)
        else:
            inspection_path=source/'interpretation'/f'{f}.inspection.json'
            inspection=read(inspection_path);images=inspection.get('images_actually_opened',inspection.get('images',inspection.get('opened_images',inspection.get('images_opened',[]))))
        evidence={'folio':f,'status':'proposed','expert_review':False,'author_sha256':sha(source/'interpretation'/f'{f}.author.json'),'inspection_sha256':sha(inspection_path),'geometry_fingerprint':interpretation['geometry_fingerprint'],'images_recorded':[{'artifact':v.get('path',v.get('image','')) if not re.match(r'^[A-Za-z]:',v.get('path',v.get('image',''))) else basename(v.get('path',v.get('image',''))),'sha256':v['sha256']} for v in images],'scope':'Public evidence index of the retained local inspection record. No new image inspection or expert validation is asserted by this publication.'}
        if reused:evidence.update(inspection_record_type='reused_pilot_global_record',artifact_identity_validation_sha256=sha(pilot_validation_path),hashes_recorded_at_original_reading_time=False)
        dump(dest/'evidence.json',evidence);page['downloads'].append({'name':'Doklady obrazové kontroly JSON','href':prefix+'evidence.json'})
        dump(dest/'page.json',page);pages.append(page)
        headers.append({k:page[k] for k in ('folio','label','kind','preview','blank')}|{'data':prefix+'page.json','segments':len(page['lines']),'passages':len(page['passages']),'supplemental_readings':len(page['supplemental_readings'])})
    counts={'pages':371,'lines':sum(len(p['lines']) for p in pages),'passages':sum(len(p['passages']) for p in pages),'blank':sum(p['blank'] for p in pages),'text_pages':sum(bool(p['lines']) for p in pages),'supplemental_readings':sum(len(p['supplemental_readings']) for p in pages)}
    doc={'schema':'manuscripty-document-v1','id':DOC,'uri':URI,'reader':READER,'title':'M I 259 · Textus varii','shelfmark':'M I 259','repository':pages[0]['repository'],'catalogue_title':'Textus varii','old_shelfmarks':['2 VI 17','II f 17'],'dating':{'notBefore':1400,'notAfter':1450,'source':'Dodaný katalogový popis; nikoli nezávislé paleografické datování'},'language':['la','de'],'title_note_cs':'Sbírka různých textů podle dodaného XML. Katalogová tvrzení jsou oddělena od výkladu AI.','tei_version':'4.12.0','tei':SITE+'/tei/'+DOC+'.xml','identifier_authority':'Projektový identifikátor Manuscripty, nikoli PID přidělené knihovnou','editorial_status':'Working research results without expert review','source_metadata':{'sha256':SUPPLIER_SHA,'xml':'/metadata/'+DOC+'/supplier.xml','json':'/metadata/'+DOC+'/description.json'},'counts':counts,'foliation_review':'/data/'+DOC+'/foliation-review.json'}
    data={'schema':'manuscripty-public-v1','title':doc['title'],'scope':NOTICE,'description_cs':'371 snímků rukopisu z fondů Vědecké knihovny v Olomouci. '+NOTICE,'processing_note':'Kraken pro segmentaci; CATMuS medieval 1.6.0 a Medusa 0.2Line-4B po stejných segmentech. Doprovodná čtení jsou samostatná obrazová interpretace.','pages':headers,'counts':counts,'document':doc,'structure_url':'/data/'+DOC+'/structure.json','summary_url':'/rukopisy/'+DOC+'#ai-shrnuti','publication_ready':True}
    target=out/'data'/DOC;dump(target/'document.json',doc)
    groups=[{'id':'scans_'+str(i+1),'label':pages[i]['label']+' – '+pages[min(i+19,370)]['label'],'pages':[{'folio':p['folio'],'label':p['label'],'kind':p['kind'],'blank':p['blank'],'source_sha256':p['source_sha256'],'passages':[{'id':v['id'],'title':v['title'],'line_id':v['line_ids'][0]} for v in p['passages']]} for p in pages[i:i+20]]} for i in range(0,371,20)]
    catalogue,description,structured=catalogue_html(source/SUPPLIER)
    dump(target/'structure.json',{'schema':'manuscripty-structure-v1','status':'proposed','expert_review':False,'counts':counts,'groups':groups,'catalogue_items':[],'catalogue_mapping_note_cs':'Katalogové rozsahy jsou v úplném popisu; nejsou považovány za ověřené odkazy na stabilní ID skenů.','catalogue_items_unmapped':read(source/'catalogue-items.json')})
    dump(target/'foliation-review.json',read(source/'foliation-review.json'))
    summary=summary_data(read(source/'research-summary.json'),pages,source);dump(target/'summary.json',summary)
    metadata=out/'metadata'/DOC;metadata.mkdir(parents=True);shutil.copyfile(source/SUPPLIER,metadata/'supplier.xml');dump(metadata/'description.json',structured)
    web_tei(source/'exports/document-metadata.tei.xml',out/'tei'/f'{DOC}.xml',None,None,validator,document=True)
    record=out/'rukopisy'/f'{DOC}.html';record.parent.mkdir();record.write_text(render_record(doc,summary,catalogue,description),encoding='utf-8',newline='\n')
    # A failing late TEI/evidence check must never leave a ready public manifest.
    dump(target/'manifest.json',data)
    inventory=[]
    for p in sorted(out.rglob('*')):
        if not p.is_file():continue
        require(p.suffix in ('.json','.txt','.xml','.html'),'Unexpected non-text output')
        require(p.stat().st_size<25*1024*1024,'Cloudflare Pages file limit exceeded')
        inventory.append({'path':p.relative_to(out).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)})
    report={'status':'passed','publication_ready':True,'document_id':DOC,'counts':counts,'final_input_audits_sha256':audits,'source_metadata_sha256':SUPPLIER_SHA,'media_copied':False,'legacy_manuscripts_modified':False,'tei_relaxng_valid':True,'expert_review':False,'files':inventory}
    dump(reports/'build-mi259.json',report);return report

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('source','base-public','out','report-dir','rng'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();result=build(args);print(json.dumps({k:result[k] for k in ('status','publication_ready','counts','media_copied')},ensure_ascii=False))
