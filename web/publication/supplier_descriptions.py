"""Publish complete supplied descriptions; preserve their text and source bytes."""
import argparse
import hashlib
import html
import json
import re
from pathlib import Path
from lxml import etree as ET

PACKAGE = Path(__file__).resolve().parent
IDS = ('vkol-m-ii-220', 'vkol-m-ii-153')
SOURCE_FILES = dict(zip(IDS, ('M_II_220____26LY4SC_CS.XML','M_II_153____2Y2A3I8_CS.XML')))
SHA = dict(zip(IDS, ('7151f2795ae2cf8d301ccd4aeb815d980604f58c513b525f961cc7a2941e3632', 'cc8d4487c0e784e1dfb3dbbf102f4a546338e4430330d5be74e1950e790148d8')))
LABELS = {
    'msIdentifier':'Identifikace ve zdrojovém popisu', 'head':'Název a datace',
    'physDesc':'Fyzický popis', 'objectDesc':'Podoba dokumentu',
    'supportDesc':'Psací látka, rozsah a skladba', 'bindingDesc':'Vazba',
    'binding':'Popis vazby', 'history':'Vznik a historie',
    'additional':'Další informace a bibliografie', 'adminInfo':'Historie popisu',
    'recordHist':'Vznik katalogového záznamu', 'listBibl':'Bibliografie',
    'country':'Země', 'settlement':'Místo uložení', 'institution':'Instituce',
    'repository':'Uložení', 'idno':'Signatura', 'altIdentifier':'Stará signatura',
    'title':'Název', 'origDate':'Datace', 'origin':'Vznik', 'provenance':'Provenience',
    'support':'Psací látka', 'extent':'Rozsah a rozměry', 'collation':'Skladba složek',
    'author':'Autor podle katalogu', 'locus':'Rozsah', 'incipit':'Incipit',
    'explicit':'Explicit', 'rubric':'Rubrika', 'finalRubric':'Závěrečná rubrika',
    'colophon':'Kolofon', 'note':'Poznámka', 'textLang':'Jazyk', 'bibl':'Bibliografický odkaz',
}
CONTAINERS = {'msIdentifier','head','physDesc','objectDesc','supportDesc','bindingDesc','binding','history','additional','adminInfo','recordHist','listBibl'}
INLINE = {'locus','persName','placeName','orgName','q','term','dimensions','height','width'}


def normalized(text):
    return ' '.join(text.split())


def tree(node):
    return {'tag':node.tag,'attributes':dict(node.attrib),'text':node.text,
            'tail':node.tail,'children':[tree(c) for c in node if isinstance(c.tag,str)]}


def renderer(doc_id, valid_folia):
    reader = '/rukopis' + ('?doc=' + doc_id if doc_id != IDS[0] else '')

    def folio(value):
        if value.startswith('#ID'):
            value = value[3:]
            if re.fullmatch(r'f\d+[rv]',value):
                value = 'F' + value[1:]
            elif re.fullmatch(r'0*\d+[rv]',value):
                value = str(int(value[:-1])) + value[-1]
        return value if value in valid_folia else None

    def inline(node):
        result = html.escape(node.text or '')
        for child in node:
            result += inline(child) + html.escape(child.tail or '')
        if node.tag == 'locus':
            start = folio(node.get('from',''))
            if not normalized(''.join(node.itertext())):
                first,last=node.get('from',''),node.get('to','')
                result=html.escape(first if first==last else first+'–'+last)
            if start:
                result = '<a href="' + reader + '#' + start + '">' + result + '</a>'
        elif node.tag == 'author' and node.get('ref','').startswith(('https://','http://')):
            result += ' <a href="' + html.escape(node.get('ref'),quote=True) + '">Autoritní záznam</a>'
        elif node.tag == 'dimensions':
            height, width, unit = node.findtext('height'), node.findtext('width'), node.get('unit','')
            result = 'Rozměry listu: výška ' + html.escape(height or '') + ' ' + html.escape(unit) + ', šířka ' + html.escape(width or '') + ' ' + html.escape(unit) + '.'
        elif node.tag in ('origDate','origin'):
            if node.get('notBefore') or node.get('notAfter'):
                result += ' <span class="source-qualifier">(katalogové rozmezí: ' + html.escape(node.get('notBefore','?')) + '–' + html.escape(node.get('notAfter','?')) + ')</span>'
        elif node.tag == 'persName' and node.get('type') == 'scribe':
            result += ' <span class="source-qualifier">(písař podle popisu)</span>'
        elif node.tag == 'orgName' and node.get('type') == 'owner':
            result += ' <span class="source-qualifier">(dřívější vlastník podle popisu)</span>'
        elif node.tag == 'placeName':
            if node.get('cert'):
                confidence = {'medium':'střední'}.get(node.get('cert'),node.get('cert'))
                result += ' <span class="source-qualifier">(jistota v popisu: ' + html.escape(confidence) + ')</span>'
            if node.get('key'):
                result += ' <span class="source-qualifier">(identifikátor místa ve zdroji: ' + html.escape(node.get('key')) + ')</span>'
        elif node.tag == 'textLang':
            codes = ' '.join(filter(None,[node.get('mainLang'),node.get('otherLangs')]))
            if codes:
                result += ' <span class="source-qualifier">(jazykové kódy: ' + html.escape(codes) + ')</span>'
        return result

    def field(node):
        if node.tag == 'p':
            return '<p>' + inline(node) + '</p>'
        if node.tag not in LABELS:
            raise ValueError('Unmapped description field: ' + node.tag)
        return '<dl class="source-fields"><dt>' + LABELS[node.tag] + '</dt><dd>' + inline(node) + '</dd></dl>'

    def block(node, level=3):
        if node.tag in CONTAINERS:
            heading = min(level,6)
            content = html.escape(node.text or '')
            for child in node:
                content += block(child,level+1) + html.escape(child.tail or '')
            return '<section><h' + str(heading) + '>' + LABELS[node.tag] + '</h' + str(heading) + '>' + content + '</section>'
        return field(node)

    def item(node, nested=False):
        number = node.get('n','')
        title = normalized(node.findtext('title') or ('Pododdíl ' if nested else 'Katalogová položka ') + number)
        locus = node.find('locus')
        interval = normalized(''.join(locus.itertext())) if locus is not None else ''
        summary = number + '. ' + title + (' · ' + interval if interval else '')
        body = html.escape(node.text or '')
        for child in node:
            body += (item(child,True) if child.tag == 'msItem' else field(child)) + html.escape(child.tail or '')
        anchor = 'catalogue-item-' + number.replace('.', '-')
        return '<details class="source-entry" id="' + html.escape(anchor,quote=True) + '"><summary>' + html.escape(summary) + '</summary><div class="source-prose">' + body + '</div></details>'

    return block,item


def update_descriptions(public):
    reports=[]
    for doc_id in IDS:
        source = PACKAGE / 'source-metadata' / (doc_id + '.xml')
        raw=source.read_bytes()
        digest=hashlib.sha256(raw).hexdigest()
        if digest != SHA[doc_id]:
            raise ValueError('Changed supplier XML: ' + doc_id)
        root=ET.fromstring(raw,ET.XMLParser(resolve_entities=False,no_network=True))
        if root.getroottree().docinfo.doctype:
            raise ValueError('Supplier XML may not contain DTDs')
        doc_path=public/'document.json' if doc_id==IDS[0] else public/'data'/doc_id/'document.json'
        doc=json.loads(doc_path.read_text(encoding='utf8'))
        expected=doc.get('source_metadata',{}).get('sha256') or doc.get('metadata_source_sha256')
        if expected != digest:
            raise ValueError('Supplier XML does not match document identity')
        manifest_code=(public/'pilot-data.js').read_text(encoding='utf8') if doc_id==IDS[0] else None
        manifest=json.loads(re.fullmatch(r'window\.PILOT_DATA\s*=\s*(\{.*\});\s*',manifest_code,re.S).group(1)) if manifest_code else json.loads((public/'data'/doc_id/'manifest.json').read_text(encoding='utf8'))
        block,item=renderer(doc_id,{p['folio'] for p in manifest['pages']})
        ms=root.find('.//msDesc'); header=root.find('teiHeader')
        if ms is None or header is None:
            raise ValueError('Missing manuscript description')
        contents=ms.find('msContents')
        if contents is None:
            raise ValueError('Missing catalogue contents')
        count=len(contents.findall('msItem')); total=len(contents.findall('.//msItem'))
        catalogue='<article id="katalogovy-obsah"><h2>Katalogový obsah kodexu</h2><p>Podle dodaného XML: ' + str(count) + ' hlavních položek, ' + str(total) + ' včetně pododdílů. Rozbalte položku pro její úplný katalogový popis. Názvy, atribuce, rozsahy a poznámky zachováváme podle zdroje; nejde o novou odbornou revizi.</p>' + ''.join(item(n) for n in contents.findall('msItem')) + '</article>'
        source_url='/metadata/'+doc_id+'/supplier.xml'
        json_url='/metadata/'+doc_id+'/description.json'
        full='<article id="zdrojovy-popis"><h2>Úplný popis podle dodaného XML</h2><p class="sample-notice">Převzato z katalogového popisu podle podkladů Vědecké knihovny v Olomouci. Znění údajů a poznámek včetně původních nejistot zůstává zachované. Nejde o nezávislé ověření rukopisu.</p><div class="hero-actions"><a class="btn" href="'+source_url+'" download="'+SOURCE_FILES[doc_id]+'">Původní popis XML</a><a class="btn" href="'+json_url+'" download>Úplný katalogový popis JSON</a></div>'
        full+= ''.join(block(n) for n in ms if n.tag!='msContents')
        classifications=[n for n in header.findall('.//catDesc') if normalized(''.join(n.itertext()))]
        if classifications:
            full+='<section><h3>Klasifikace zdrojového popisu</h3>'+''.join('<p>'+html.escape(normalized(''.join(n.itertext())))+'</p>' for n in classifications)+'</section>'
        full+='</article>'
        record_path=public/'rukopisy'/(doc_id+'.html')
        record=record_path.read_text(encoding='utf8')
        if 'id="zdrojovy-popis"' in record:
            record,n=re.subn(r'<article id="zdrojovy-popis">.*?</article>',lambda _:full,record,flags=re.S)
            if n!=1:raise ValueError('Ambiguous complete description')
            prefix=''
        else:
            prefix=full
        if 'id="katalogovy-obsah"' in record:
            record,n=re.subn(r'<article id="katalogovy-obsah">.*?</article>',lambda _:prefix+catalogue,record,flags=re.S)
        else:
            record,n=re.subn(r'<h2>Katalogový obsah kodexu</h2>.*?</ol>',lambda _:prefix+catalogue,record,flags=re.S)
        if n!=1:raise ValueError('Ambiguous catalogue insertion')
        if '/catalogue.css' not in record:
            record=record.replace('</head>','<link rel="stylesheet" href="/catalogue.css?v=20261014-1"></head>')
        if 'href="#zdrojovy-popis"' not in record:
            record=record.replace('<div class="hero-actions">','<div class="hero-actions"><a class="btn" href="#zdrojovy-popis">Fyzický popis a historie</a>',1)
        # Check every meaningful source text node and tail in the full msDesc,
        # independently of our field mapping, including collapsed item details.
        rendered=ET.HTML(full+catalogue)
        visible=normalized(''.join(rendered.itertext()))
        checked=0
        for node in ms.iter():
            for value in (node.text,node.tail):
                phrase=normalized(value or '')
                if phrase:
                    if phrase not in visible:
                        raise ValueError('Omitted source text in '+doc_id+': '+phrase[:100])
                    checked+=1
        # Browser whitespace is presentation only; archival XML/JSON stay exact.
        record=re.sub(r'[ \t]+\n','\n',record)
        record_path.write_text(record,encoding='utf8',newline='\n')
        metadata=public/'metadata'/doc_id
        metadata.mkdir(parents=True,exist_ok=True)
        (metadata/'supplier.xml').write_bytes(raw)
        (metadata/'description.json').write_text(json.dumps({'document_id':doc_id,'source_filename':SOURCE_FILES[doc_id],'source_sha256':digest,'scope':'Complete supplied teiHeader, with original attributes and text; source format, not a new TEI P5 edition','header':tree(header)},ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
        reports.append({'id':doc_id,'source_sha256':digest,'source_xml_bytes':len(raw),'main_items':count,'total_items':total,'description_text_nodes_checked':checked,'source_xml_exact_bytes':True,'original_header_attributes_retained':True})
    (public/'catalogue.css').write_bytes((PACKAGE/'catalogue.css').read_bytes())
    return reports


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--public-root',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps({'status':'passed','manuscripts':update_descriptions(args.public_root.resolve())},ensure_ascii=False))
