"""Verify complete, current interpretation provenance; no new reading is claimed."""
from pathlib import Path
import argparse, hashlib, json
from lxml import etree

def read(p): return json.loads(p.read_text(encoding='utf8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def audit(source, rng, require_complete=True, pilot_source=None):
    source=Path(source).resolve(); cache={}; missing=[]; checked=0; sheets=0; exports=0
    def local(relative):
        p=(source/relative).resolve()
        if not p.is_relative_to(source) or not p.is_file(): raise ValueError('Invalid provenance file: '+str(relative))
        return p
    def checkfile(relative, expected):
        p=local(relative)
        if p not in cache: cache[p]=sha(p)
        if cache[p]!=expected: raise ValueError('Stale provenance SHA: '+str(relative))
    def image_records(obj):
        if isinstance(obj,dict):
            if 'file' in obj and 'sha256' in obj: checkfile(obj['file'],obj['sha256'])
            for value in obj.values(): image_records(value)
        elif isinstance(obj,list):
            for value in obj: image_records(value)
    validator=etree.RelaxNG(etree.parse(str(rng)))
    manifest=read(source/'manifest.json')
    if len(manifest['pages'])!=197 or manifest.get('status')!='prepared': raise ValueError('HTR manifest is not complete')
    for page in manifest['pages']:
        fol=page['folio']; ip=source/'interpretation'/(fol+'.json'); vp=ip.with_name(fol+'.validation.json')
        if not ip.exists() or not vp.exists(): missing.append(fol); continue
        comparison=read(local('pages/'+fol+'/comparison.json')); data=read(ip); val=read(vp)
        if data['expert_review'] is not False or val['expert_review'] is not False: raise ValueError('Incorrect review state: '+fol)
        if data['source']['original_sha256']!=page['original_sha256']: raise ValueError('Wrong original source: '+fol)
        if [x['id'] for x in data['lines']]!=[x['id'] for x in comparison['lines']]: raise ValueError('Source IDs changed: '+fol)
        for a,b in zip(data['lines'],comparison['lines']):
            if a['bbox']!=b['bbox'] or a['htr_candidates']!=b['candidates']: raise ValueError('Raw model/geometry change: '+a['id'])
        ids={x['id'] for x in comparison['lines']}
        if {i for u in data['translation_units'] for i in u['line_ids']}!=ids: raise ValueError('Incomplete translation: '+fol)
        for record in data.get('htr_source_files',[]): checkfile(record['file'],record['sha256'])
        logpath=data['inspection_record']; checkfile(logpath,val['inspection_record_sha256']); log=read(local(logpath)); image_records(log)
        opened={i for s in log.get('opened_sheets',[]) for i in s.get('line_ids',[])}
        sheets+=len(log.get('opened_sheets',[]))
        authorpath=source/'interpretation'/(fol+'.author.json')
        if 'inherited_interpretation' in data:
            if pilot_source is None: raise ValueError('Inherited pilot requires explicit --pilot-source')
            pilot=Path(pilot_source).resolve()/'interpretation'/(fol+'.json')
            if sha(pilot)!=data['inherited_interpretation']['sha256']: raise ValueError('Inherited pilot changed: '+fol)
            old=read(pilot)
            if [x['reconstruction_la'] for x in old['lines']]!=[x['reconstruction_la'] for x in data['lines']] or old['translation_units']!=data['translation_units']: raise ValueError('Pilot reading changed: '+fol)
        else:
            if not authorpath.exists() or sha(authorpath)!=val.get('author_sha256'): raise ValueError('Author changed after export: '+fol)
            author=read(authorpath)
            if author['latin']!=[x['reconstruction_la'] for x in data['lines']]: raise ValueError('Canonical reading differs: '+fol)
            if [u[2] for u in author['units']]!=[u['translation_cs'] for u in data['translation_units']]: raise ValueError('Canonical translation differs: '+fol)
            if ids and (set(author['_provenance']['inspected_line_ids'])!=ids or not ids<=opened): raise ValueError('Missing image-inspection IDs: '+fol)
        if ids:
            if val['tei'].get('relaxng_valid') is not True: raise ValueError('Missing schema validation: '+fol)
            xml=local('interpretation/'+fol+'.tei.xml'); validator.assertValid(etree.parse(str(xml))); exports+=1
            for suffix in ('.reconstruction.la.txt','.translation.cs.txt'): local('interpretation/'+fol+suffix)
        elif not page.get('blank_main_text'): raise ValueError('Empty text without explicit blank classification: '+fol)
        checked+=1
    if missing and require_complete: raise ValueError('Missing interpretation: '+', '.join(missing))
    return {'status':'passed' if not missing else 'partial','pages':checked,'expected_pages':197,'missing':missing,'complete':not missing,'verified_provenance_files':len(cache),'opened_sheet_records':sheets,'tei_relaxng_validated':exports,'expert_review':False,'scope':'SHA provenance, current author/export agreement, preserved models/geometry, exact translation coverage and TEI Relax NG. No claim that machine validation proves paleographic correctness.'}

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--source',type=Path,required=True);p.add_argument('--rng',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--allow-partial',action='store_true');p.add_argument('--pilot-source',type=Path);a=p.parse_args()
    result=audit(a.source,a.rng,not a.allow_partial,pilot_source=a.pilot_source);a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps(result,ensure_ascii=False))
