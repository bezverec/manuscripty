"""Convert supplied msDesc to pinned TEI P5, preserving existing edition/index nodes."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
from lxml import etree as ET
from supplier_descriptions import IDS, SHA, SOURCE_FILES, normalized

TEI='http://www.tei-c.org/ns/1.0'
XML='http://www.w3.org/XML/1998/namespace'
NS={'t':TEI}
SCHEMA_SHA='b0f115095ead2ccc6933aa3365c6f4a82cba3b2ec7eee7f76bb616d7a63b7e48'
Q=lambda tag:'{'+TEI+'}'+tag
digest=lambda raw:hashlib.sha256(raw).hexdigest()
parser=lambda:ET.XMLParser(resolve_entities=False,no_network=True)


def qualify(node):
    result=ET.Element(Q(node.tag))
    result.attrib.update(node.attrib);result.text=node.text;result.tail=node.tail
    for child in node:
        if isinstance(child.tag,str):result.append(qualify(child))
    return result


def canonical(node):
    return ET.tostring(node,method='c14n') if node is not None else None


def convert(public, manifest_path=None, report_path=None, schema_path=None, validator=None):
    schema_path=schema_path or public/'schemas/tei-p5-4.12.0/tei_all.rng'
    if digest(schema_path.read_bytes())!=SCHEMA_SHA:raise ValueError('Pinned schema changed')
    rng=validator if validator is not None else ET.RelaxNG(ET.parse(str(schema_path),parser()))
    manifest=json.loads(manifest_path.read_text(encoding='utf8')) if manifest_path else None
    candidates=[];reports=[]
    for ident in IDS:
        path=public/'tei'/(ident+'.xml');before=path.read_bytes()
        root=ET.fromstring(before,parser())
        if root.get('version')!='4.12.0':raise ValueError('Unexpected TEI version')
        preserved={name:canonical(root.find(Q(name))) for name in ('text','facsimile')}
        supplied=(public/'metadata'/ident/'supplier.xml').read_bytes()
        if digest(supplied)!=SHA[ident]:raise ValueError('Supplier source mismatch')
        source=ET.fromstring(supplied,parser()).find('.//msDesc')
        old=root.find('.//t:sourceDesc/t:msDesc',NS)
        if source is None or old is None:raise ValueError('Missing msDesc')
        ms=qualify(source)
        source_pairs=list(zip((n for n in source.iter() if isinstance(n.tag,str)),ms.iter()))
        ms.set('{'+XML+'}id',old.get('{'+XML+'}id') or 'ms-'+ident)
        ms.set('corresp','https://rukopisy.digitalizaty.cz/metadata/'+ident+'/supplier.xml')
        # Retain project URI, identifiers and repository references alongside
        # the complete original identification, including former shelfmarks.
        identifier=ms.find(Q('msIdentifier'))
        for previous in old.find(Q('msIdentifier')):
            matches=[n for n in identifier if n.tag==previous.tag and normalized(''.join(n.itertext()))==normalized(''.join(previous.itertext()))]
            if matches:
                for key,value in previous.attrib.items():matches[0].set(key,value)
            elif previous.tag==Q('idno'):
                position=next((i for i,n in enumerate(identifier) if n.tag==Q('altIdentifier')),len(identifier))
                identifier.insert(position,copy.deepcopy(previous))
            else:identifier.append(copy.deepcopy(previous))
        summary=old.find('t:msContents/t:summary',NS)
        if summary is not None:ms.find(Q('msContents')).insert(0,copy.deepcopy(summary))
        reader='https://rukopisy.digitalizaty.cz/rukopis'+('?doc='+ident if ident==IDS[1] else '')
        mappings=[]
        for locus in ms.findall('.//'+Q('locus')):
            targets=[]
            for attr in ('from','to'):
                value=locus.get(attr)
                if not value:continue
                folio=value
                if value=='#IDf001v':
                    folio='F001v';replacement='#surface_F001v'
                    if root.find('.//t:surface[@xml:id="surface_F001v"]',{**NS,'xml':XML}) is None:raise ValueError('Missing referenced surface')
                    locus.set(attr,replacement)
                    mappings.append({'attribute':attr,'source':value,'tei':replacement})
                targets.append(reader+'#'+folio)
            if targets:locus.set('target',' '.join(dict.fromkeys(targets)))
        old.getparent().replace(old,ms)
        attributes_checked=0
        for source_node,converted_node in source_pairs:
            for key,value in source_node.attrib.items():
                if source_node is source and key=='{'+XML+'}id':continue
                expected='#surface_F001v' if key in ('from','to') and value=='#IDf001v' else value
                if converted_node.get(key)!=expected:raise ValueError('Changed source attribute: '+key)
                attributes_checked+=1
        fd=root.find('t:teiHeader/t:fileDesc',NS)
        notes=fd.find(Q('notesStmt'))
        if notes is None:
            notes=ET.Element(Q('notesStmt'));fd.insert(list(fd).index(fd.find(Q('sourceDesc'))),notes)
        marker='supplier-msdesc-'+ident
        if notes.find('t:note[@xml:id="'+marker+'"]',{**NS,'xml':XML}) is None:
            note=ET.SubElement(notes,Q('note'),type='metadata-source',corresp='urn:sha256:'+SHA[ident])
            note.set('{'+XML+'}id',marker)
            note.text='Úplný katalogový popis převzat z '+SOURCE_FILES[ident]+'. Obsahuje fyzický popis, vazbu, historii, bibliografii a poznámky ke všem dílům. Údaje jsou tvrzení dodaného popisu, nikoli nové obrazové nebo odborné ověření. Původní XML se zachovává samostatně beze změny.'
        editorial=root.find('t:teiHeader/t:encodingDesc/t:editorialDecl',NS)
        if editorial is None:raise ValueError('Missing editorial declaration')
        classification=ET.fromstring(supplied,parser()).find('teiHeader/encodingDesc/classDecl')
        if classification is not None:
            encoding=editorial.getparent();existing=encoding.find(Q('classDecl'))
            converted_classification=qualify(classification)
            if existing is None:encoding.append(converted_classification)
            else:encoding.replace(existing,converted_classification)
        policy='supplier-msdesc-conversion-'+ident
        if editorial.find('t:p[@xml:id="'+policy+'"]',{**NS,'xml':XML}) is None:
            p=ET.SubElement(editorial,Q('p'));p.set('{'+XML+'}id',policy)
            p.text='Popis msDesc je převeden do jmenného prostoru TEI P5 4.12.0. Zachováno je původní znění, vnořené položky, bibliografie, datace i míry jistoty; projektové identifikátory a původní ediční poznámky zůstávají oddělené. Odkazy locus míří na příslušná folia prohlížeče; původní #IDf001v se mapuje na existující #surface_F001v tam, kde je tento odkaz použit. Původní text a facsimile projektu se nemění.'
        # Reparse the final tree so libxml2's ID table reflects the replaced
        # msDesc, rather than the detached node with the same project xml:id.
        root=ET.fromstring(ET.tostring(root),parser())
        if not rng.validate(root):raise ValueError(ident+' TEI invalid: '+str(rng.error_log))
        for name,value in preserved.items():
            if canonical(root.find(Q(name)))!=value:raise ValueError('Changed protected '+name)
        ids={n.get('{'+XML+'}id') for n in root.iter() if n.get('{'+XML+'}id')}
        for node in root.iter():
            for attr in ('target','facs','corresp','from','to'):
                for value in node.get(attr,'').split():
                    if value.startswith('#') and value[1:] not in ids:raise ValueError('Unresolved local TEI pointer: '+value)
        text=normalized(''.join(ms.itertext()));checked=0
        for node in source.iter():
            for value in (node.text,node.tail):
                phrase=normalized(value or '')
                if phrase:
                    if phrase not in text:raise ValueError('Omitted catalogue text: '+phrase[:100])
                    checked+=1
        raw=b'<?xml version="1.0" encoding="UTF-8"?>\n<?xml-model href="../schemas/tei-p5-4.12.0/tei_all.rng" type="application/xml" schematypens="http://relaxng.org/ns/structure/1.0"?>\n'+ET.tostring(root,encoding='UTF-8',pretty_print=True)
        if manifest is not None:
            name='web/public/tei/'+ident+'.xml'
            record=next(r for r in manifest['files'] if r['path']==name)
            if record['sha256']!=digest(before) or record['bytes']!=len(before):raise ValueError('Unrecorded prior TEI change')
            record.update(sha256=digest(raw),bytes=len(raw))
        candidates.append((path,raw))
        reports.append({'id':ident,'before_sha256':digest(before),'after_sha256':digest(raw),'source_sha256':SHA[ident],'source_text_nodes_checked':checked,'source_attributes_verified':attributes_checked,'source_classification_preserved':classification is not None,'msItems':len(ms.findall('.//'+Q('msItem'))),'text_c14n_unchanged':True,'facsimile_c14n_unchanged':True,'local_pointers_verified':True,'relaxng':'passed','pointer_mappings':mappings})
    for path,raw in candidates:path.write_bytes(raw)
    if manifest_path:manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
    report={'status':'passed','tei_version':'4.12.0','schema_sha256':SCHEMA_SHA,'scope':'Explicitly authorized metadata-only update of two whole-document TEI descriptions; preserved edition/index text and facsimile','manuscripts':reports}
    if report_path:report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--public-root',required=True,type=Path);p.add_argument('--manifest',type=Path);p.add_argument('--report',type=Path)
    a=p.parse_args();print(json.dumps(convert(a.public_root.resolve(),a.manifest,a.report),ensure_ascii=False))
