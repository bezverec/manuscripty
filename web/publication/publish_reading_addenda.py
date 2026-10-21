"""Publish exactly two approved AI addenda; preserve every original research layer.

Only the two pinned page adapters and their manifest entries may be changed.
The source review and all other existing protected files must match their hashes.
"""
from pathlib import Path
import hashlib, json, re
from lxml import etree as E

R = Path(__file__).resolve().parents[2]
PUBLIC = R/'web/public'
REVIEW = R/'docs/experiments/2026-10-21-medusa-five/report.json'
REVIEW_SHA = '7f97d67890615c511bb18e62b40b6a3a4d202b26e20327a0bb3aae3cfebcfeaa'
EXPECTED = {'97v':'81d1fb0f9aa16c05d3808b0d75df274a80b9ce816abfa4cb1c0bedd8f10e3e44',
            '119v':'4f4b8ddf6f13c205bd4e59c77beec36e8a828cd6bcb510974bd91ae9ac99af55'}
DOC='vkol-m-i-259'
T='http://www.tei-c.org/ns/1.0'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p): return json.loads(p.read_text(encoding='utf8'))
def dump(p,d): p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
def add(parent,tag,text=None,**attrs):
    node=E.SubElement(parent,'{'+T+'}'+tag,**attrs)
    node.text=text
    return node
def marked(parent,text):
    """Preserve visible uncertainty markers, also encode conjectures explicitly."""
    cursor=0;last=None
    for match in re.finditer(r'\[[^\]]*\?\]',text):
        prefix=text[cursor:match.start()]
        if last is None: parent.text=(parent.text or '')+prefix
        else: last.tail=(last.tail or '')+prefix
        last=add(parent,'supplied',match.group(),reason='conjecture',cert='low')
        cursor=match.end()
    tail=text[cursor:]
    if last is None: parent.text=(parent.text or '')+tail
    else: last.tail=(last.tail or '')+tail

def tei(reading,folio,validator):
    root=E.Element('{'+T+'}TEI',nsmap={None:T},version='4.12.0')
    header=add(root,'teiHeader');desc=add(header,'fileDesc')
    stmt=add(desc,'titleStmt');add(stmt,'title','M I 259 · '+folio+' · zpřesněná četba AI z 21. 10. 2026')
    pub=add(desc,'publicationStmt');add(pub,'p','Návrh AI bez odborné revize. Původní HTR a původní edice zůstávají zachované.')
    source=add(desc,'sourceDesc');p=add(source,'p','Vědecká knihovna v Olomouci, M I 259, snímek '+folio+'. ')
    add(p,'ref','Původní stranová edice',target=f'https://rukopisy.digitalizaty.cz/data/{DOC}/{folio}/edition.web.tei.xml')
    encoding=add(header,'encodingDesc');add(encoding,'p','Samostatné rozvedené čtení, nikoli diplomatická reference či nový raw Medusy. Text v hranatých závorkách s otazníkem je konjektura; značky zůstávají i v obsahu supplied. Nevyřešené právní odkazy a elipsy se zachovávají. Bez nových obrazových nebo slovních souřadnic.')
    revision=add(header,'revisionDesc');add(revision,'change','Publikace odděleného návrhu s nejistotami; původní raw neměněn.',when=reading['date'])
    body=add(add(root,'text'),'body');div=add(body,'div',type='reading_addendum',subtype='AI_proposed')
    div.set('corresp',' '.join(f'https://rukopisy.digitalizaty.cz/rukopisy/{DOC}/{folio}#{i}' for i in reading['line_ids']))
    for kind,lang,value in [('reconstruction','la',reading['reconstruction']),('context_continuation','la',reading.get('context_continuation')),('translation','cs',reading['translation_cs'])]:
        if value:
            p=add(div,'ab',type=kind);p.set('{http://www.w3.org/XML/1998/namespace}lang',lang);marked(p,value)
    add(div,'note',reading['note_cs'],type='uncertainty')
    validator.assertValid(root)
    return E.tostring(root,encoding='utf8',xml_declaration=True,pretty_print=True)

def main():
    assert sha(REVIEW)==REVIEW_SHA,'Approved review changed'
    review=load(REVIEW);manifest_path=R/'docs/web-source-manifest.json';manifest=load(manifest_path)
    inventory={v['path']:v for v in manifest['files']}
    for item in manifest['files']:
        if item['path'].startswith(('web/public/data/','web/public/tei/','web/public/schemas/')):
            assert sha(R/item['path'])==item['sha256'],'Existing protected data changed: '+item['path']
    validator=E.RelaxNG(E.parse(str(PUBLIC/'schemas/tei-p5-4.12.0/tei_all.rng'),E.XMLParser(no_network=True)))
    changes=[];new_files=[]
    for folio,expected in EXPECTED.items():
        folder=PUBLIC/'data'/DOC/folio;p=folder/'page.json';assert sha(p)==expected,'Page differs from approved baseline: '+folio
        page=load(p);row=next(r for r in review['rows'] if r['folio']==folio)
        reading={k:row[k] for k in ('reconstruction','translation_cs','note_cs')}
        ids=[row['id']]+(['f97v_l015'] if folio=='97v' else [])
        reading.update(id='addendum_'+folio+'_20261021',date='2026-10-21',status='proposed',expert_review=False,line_ids=ids,target_line_ids=[row['id']],
                       source_review_sha256=REVIEW_SHA,source_image_sha256=row['original_crop_sha256'],original_page_sha256=expected,
                       supersedes_passage_ids=[u['id'] for u in page['passages'] if row['id'] in u['line_ids']],
                       sources=[{'label':'Obrazový podklad a původní HTR','url':f'https://rukopisy.digitalizaty.cz/rukopis?doc={DOC}&vrstva=radky#{folio}-{row["id"]}'},
                                {'label':'Záznam kontroly a nového pokusu','url':'https://github.com/bezverec/manuscripty/blob/7c41e54a1cfc35a714eea43063fefcd33c14c0a7/docs/experiments/2026-10-21-medusa-five/README.md'}])
        if folio=='97v':
            reading['context_continuation']=row['context_continuation']
            reading['sources'].append({'label':'Právní paralela: interpretační opora, nikoli důkaz písmenného znění','url':review['parallel_source']['url']+'#page=14'})
        assert set(ids)<={l['id'] for l in page['lines']}
        original_line=next(l for l in page['lines'] if l['id']==row['id'])
        assert original_line['raw_htr']['medusa']==row['original_medusa_raw'] and original_line['hit_token_limit']
        output={'schema':'manuscripty-reading-addenda-v1','document_id':DOC,'folio':folio,'status':'proposed','expert_review':False,'readings':[reading]}
        payloads={'reading-addenda.json':json.dumps(output,ensure_ascii=False,indent=2).encode()+b'\n',
                  'reading-addenda.tei.xml':tei(reading,folio,validator),
                  'reading-addenda.reconstruction.txt':(reading['reconstruction']+'\n'+(reading.get('context_continuation','')+'\n' if reading.get('context_continuation') else '')+'\n'+reading['note_cs']+'\n').encode(),
                  'reading-addenda.translation.cs.txt':(reading['translation_cs']+'\n\n'+reading['note_cs']+'\n').encode()}
        assert all(not (folder/name).exists() for name in payloads),'Refuse overwrite of existing addendum'
        for name,content in payloads.items(): (folder/name).write_bytes(content);new_files.append((folder/name).relative_to(R).as_posix())
        page['reading_addenda']=[reading]
        titles=['Zpřesněná četba AI a překlad JSON','Zpřesněná četba AI TEI P5 4.12.0','Zpřesněná četba AI TXT','Zpřesněný český překlad TXT']
        page['downloads'] += [{'name':title,'href':f'/data/{DOC}/{folio}/{name}'} for name,title in zip(payloads,titles)]
        dump(p,page)
        restored=load(p);restored.pop('reading_addenda');restored['downloads']=restored['downloads'][:-4]
        assert restored==json.loads(__import__('subprocess').check_output(['git','show','HEAD:'+p.relative_to(R).as_posix()])),'Original page fields changed'
        item=inventory[p.relative_to(R).as_posix()];assert item['sha256']==expected
        item.update(sha256=sha(p),bytes=p.stat().st_size)
        changes.append({'path':item['path'],'before_sha256':expected,'after_sha256':item['sha256'],'only_added_fields':['reading_addenda','four download links']})
    for name in new_files:
        p=R/name;manifest['files'].append({'path':name,'bytes':p.stat().st_size,'sha256':sha(p)})
    manifest['files'].sort(key=lambda v:v['path']);dump(manifest_path,manifest)
    dump(R/'docs/validation/reading-addenda-import-20261021.json',{'status':'passed','approved_review_sha256':REVIEW_SHA,'changes':changes,'new_files':new_files,'previous_page_fields_unchanged':True,'raw_htr_and_original_exports_changed':False,'standalone_tei_relaxng':'passed','expert_review':False})
    print('Imported exactly two addenda; original page fields/HTR/editions preserved; TEI validated.')
if __name__=='__main__':main()
