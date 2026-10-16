"""Combine catalogue descriptions and distinctly labelled, source-linked AI synthesis.

Only two high-level summary JSONs may change; page readings and source links stay intact.
The supplier XML and the source snapshot guard remain authoritative and unchanged.
"""
import argparse
import copy
import hashlib
import html
import json
import re
from pathlib import Path
from lxml import etree
from supplier_descriptions import IDS, SHA as SOURCE_HASHES, PACKAGE
from markup import normalize_html
from digitization_support import decorate_record as support_record, install_assets as support_assets

REV = '20261014-2'
SUMMARY_PATHS = {IDS[0]: 'summary.json', IDS[1]: 'data/'+IDS[1]+'/summary.json'}
ALIASES = {IDS[0]: 'summary.html', IDS[1]: 'rukopisy/'+IDS[1]+'/shrnuti.html'}
ORIGIN = 'https://rukopisy.digitalizaty.cz'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding='utf8'))


def dump(obj):
    return (json.dumps(obj, ensure_ascii=False, indent=2)+'\n').encode('utf8')


def enriched_summary(public, ident):
    """Add catalogue-based synthesis without modifying any existing thematic reading."""
    old = load(public/SUMMARY_PATHS[ident])
    if old['document_id'] != ident or old['status'] != 'proposed' or old['expert_review'] is not False:
        raise ValueError('Unexpected summary identity/review status')
    context = load(PACKAGE/'overview_context.json')[ident]
    raw = (public/'metadata'/ident/'supplier.xml').read_bytes()
    if sha(raw) != SOURCE_HASHES[ident]:
        raise ValueError('Supplier context SHA mismatch')
    ms = etree.fromstring(raw).find('.//msDesc')
    for part in context['context']:
        for n in part['items']:
            if len(ms.xpath('msContents/msItem[@n=$n]', n=n)) != 1:
                raise ValueError('Unknown catalogue item: '+n)
        for name in part.get('header_paths', []):
            if ms.find(name) is None:
                raise ValueError('Missing catalogue header: '+name)
    updated = copy.deepcopy(old)
    updated['lead' if ident == IDS[0] else 'lead_cs'] = context['lead_cs']
    updated['updated_date'] = '2026-10-14'
    updated['catalogue_context'] = {
        'source_uri': '/metadata/'+ident+'/supplier.xml',
        'source_sha256': sha(raw), 'description_uri': '/metadata/'+ident+'/description.json',
        'method_cs': 'Syntéza dosavadních pracovních rekonstrukcí a úplného dodaného katalogového popisu. Nové katalogové podklady zpřesňují souhrnný výklad; nejde o novou obrazovou kontrolu nebo revizi řádkové četby.',
        'parts': context['context']
    }
    key = 'sections' if ident == IDS[0] else 'themes'
    assert old[key] == updated[key]  # includes original evidence URLs and source hashes
    return updated


def ai_article(record, ident):
    esc = html.escape
    themes = record.get('sections', record.get('themes'))
    text = '<article id="ai-shrnuti" class="ai-overview"><p class="evidence-label ai-label">Výklad AI · pracovní návrh · aktualizováno 14. 10. 2026</p><h2>Co rukopis obsahuje</h2><p class="summary-intro">'+esc(record.get('lead', record.get('lead_cs')) )+'</p>'
    text += '<p class="sample-notice">Bez odborné revize. Shrnutí vychází z dosavadních pracovních rekonstrukcí a překladů a z úplného katalogového popisu. Přebírá nejistoty četby; aktualizace podle katalogu není novým ověřením obrazu.</p><h3>Co doplňují nové podklady</h3>'
    for part in record['catalogue_context']['parts']:
        links = ', '.join('<a href="#catalogue-item-'+n.replace('.', '-')+'">'+esc(n)+'</a>' for n in part['items'])
        text += '<div class="context-pair"><h4>'+esc(part['title_cs'])+'</h4><p><strong>Podle katalogu:</strong> '+esc(part['catalogue_cs'])+'</p><p><strong>Interpretace AI:</strong> '+esc(part['interpretation_cs'])+'</p><p class="context-source">Podklad: katalogové položky '+links
        if part.get('header_paths'):
            text += ' a <a href="#zdrojovy-popis">fyzický popis a historie</a>'
        text += ' · <a href="'+record['catalogue_context']['source_uri']+'">původní XML</a></p></div>'
    text += '<h3>Témata s odkazy na pracovní četbu</h3><p>Rozbalte téma a porovnejte shrnutí s rekonstrukcí, překladem a obrazem uvedených folií.</p>'
    for theme in themes:
        text += '<details class="ai-theme" id="'+esc(theme['id'], quote=True)+'"><summary>'+esc(theme.get('title', theme.get('title_cs')))+'<span class="theme-kind">AI výklad</span></summary><div class="theme-body"><p>'+esc(theme.get('text', theme.get('summary_cs')) )+'</p>'
        text += '<div class="summary-sources" aria-label="Podklady pracovní četby">'
        for source in theme['sources']:
            url = source.get('uri', source.get('url'))
            if url.startswith('rukopis.html'):
                url = '/'+url.replace('rukopis.html', 'rukopis', 1)
            text += '<a href="'+esc(url, quote=True)+'">f. '+esc(source['folio'])+'</a>'
        text += '</div></div></details>'
    if record.get('scope_note_cs'):
        text += '<p class="sample-notice">'+esc(record['scope_note_cs'])+'</p>'
    text += '<p><a href="/'+SUMMARY_PATHS[ident]+'" download>Stáhnout shrnutí a jeho podklady (JSON)</a></p></article>'
    return text


def render(public, ident, summary):
    path = public/'rukopisy'/(ident+'.html')
    record = path.read_text(encoding='utf8')
    # Preserve old metadata, full supplier text, original citation scripts and search.
    record = re.sub(r'<article id="ai-shrnuti".*?</article>\s*', '', record, flags=re.S)
    record = record.replace('href="/summary"', 'href="#ai-shrnuti"')
    record = record.replace('href="/rukopisy/'+ident+'/shrnuti"', 'href="#ai-shrnuti"')
    record = record.replace('<p class="eyebrow">Popis a zdroje</p>', '<p class="eyebrow">Přehled rukopisu · popis, výklad a zdroje</p>')
    if '<main class="container section">' in record:
        record = record.replace('<main class="container section">', '<main class="section"><div class="container summary-layout">', 1).replace('</main>', '</div></main>', 1)
    if 'id="prehled-navigace"' not in record:
        nav = '<nav id="prehled-navigace" class="overview-nav" aria-label="Obsah přehledu"><a href="#ai-shrnuti">Výklad AI</a><a href="#zdrojovy-popis">Fyzický popis a historie</a><a href="#katalogovy-obsah">Katalogový obsah</a></nav>'
        marker = '<article>' if ident == IDS[0] else '<h2>Alternativní katalogové názvy a zdroje</h2>'
        if record.count(marker) < 1:
            raise ValueError('Missing overview insertion point')
        record = record.replace(marker, nav+'\n'+ai_article(summary, ident)+'\n'+marker, 1)
    else:
        record, count = re.subn(r'(<nav id="prehled-navigace".*?</nav>)', lambda m: m[1]+'\n'+ai_article(summary, ident), record, count=1, flags=re.S)
        if count != 1:
            raise ValueError('Missing overview navigation')
    # Internal navigation has replaced the formerly split summary actions.
    record = re.sub(r'<a class="btn" href="#ai-shrnuti">AI shrnutí</a>', '', record)
    record = record.replace('<a class="btn" href="#zdrojovy-popis">Fyzický popis a historie</a>', '')
    record = record.replace('<a class="btn" href="#katalogovy-obsah">Katalogový obsah</a>', '')
    record = record.replace('<p><a href="#ai-shrnuti">AI shrnutí rukopisu</a></p>', '')
    if ident == IDS[0]:
        record = record.replace('<article><h2>Katalogová identifikace a zdroje</h2>', '<article id="katalogove-upresneni"><h2>Katalogová identifikace a zdroje</h2>')
    # Mark source material at the start of each complete catalogue section.
    for anchor in ('zdrojovy-popis', 'katalogovy-obsah'):
        record = record.replace('<article id="'+anchor+'"><h2>', '<article id="'+anchor+'"><p class="evidence-label source-label">Katalogové údaje · převzato ze zdroje</p><h2>')
    record = re.sub(r'/catalogue\.css\?v=[\w-]+', '/catalogue.css?v='+REV, record)
    record = re.sub(r'<script src="/overview\.js.*?</script>', '', record)
    record = record.replace('</body>', '<script src="/overview.js?v='+REV+'" defer></script></body>')
    # Distinct IDs guarantee fragment compatibility with former summary URLs.
    tree = etree.HTML(record)
    ids = tree.xpath('//@id')
    if len(ids) != len(set(ids)) or len(tree.xpath('//article[@id="ai-shrnuti"]')) != 1:
        raise ValueError('Ambiguous overview IDs')
    return path, normalize_html(support_record(record)).encode('utf8')


def update(public, manifest_path=None, report_path=None):
    public = public.resolve()
    manifest = load(manifest_path) if manifest_path else None
    outputs = []; reports = []
    for ident in IDS:
        path = public/SUMMARY_PATHS[ident]; old = path.read_bytes()
        updated = enriched_summary(public, ident); raw = dump(updated)
        manifest_key = 'web/public/'+SUMMARY_PATHS[ident]
        if manifest:
            item = next(f for f in manifest['files'] if f['path'] == manifest_key)
            if item['sha256'] != sha(old) or item['bytes'] != len(old):
                raise ValueError('Unexpected prior summary hash: '+manifest_key)
            item.update(sha256=sha(raw), bytes=len(raw))
        outputs += [(path, raw), render(public, ident, updated)]
        url = '/rukopisy/'+ident
        alias = '<!doctype html><html lang="cs"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Shrnutí a popis rukopisu</title><link rel="canonical" href="'+ORIGIN+url+'"><link rel="stylesheet" href="/styles.css?v=20261012-6"></head><body><main class="container section"><h1>Shrnutí je součástí přehledu rukopisu</h1><p><a href="'+url+'#ai-shrnuti">Otevřít popis, výklad AI a zdroje</a></p></main></body></html>\n'
        outputs.append((public/ALIASES[ident], normalize_html(alias).encode('utf8')))
        reports.append({'document_id': ident, 'path': manifest_key, 'before_sha256': sha(old), 'after_sha256': sha(raw), 'supplier_sha256': updated['catalogue_context']['source_sha256'], 'thematic_readings_and_source_links_unchanged': True, 'expert_review': False})
    # Write only after BOTH identities, source SHAs, previous summary hashes and HTML pass.
    for path, raw in outputs:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    redirects = public/'_redirects'
    rules = redirects.read_text(encoding='utf8') if redirects.exists() else ''
    for ident in IDS:
        clean = '/'+ALIASES[ident][:-5]
        target = '/rukopisy/'+ident
        for alias in (clean, clean+'.html'):
            rule = alias+' '+target+' 301'
            if rule not in rules.splitlines():
                rules += rule+'\n'
    redirects.write_text(rules, encoding='utf8', newline='\n')
    (public/'overview.js').write_bytes((PACKAGE/'overview.js').read_bytes())
    support_assets(public)
    if manifest:
        manifest_path.write_bytes(dump(manifest))
    report = {'status': 'passed', 'scope': 'Only high-level AI summary JSON and presentation; original thematic readings, evidence links, supplier XML and page data preserved.', 'manuscripts': reports}
    if report_path:
        report_path.write_bytes(dump(report))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--public-root', type=Path, required=True)
    parser.add_argument('--manifest', type=Path)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    print(json.dumps(update(args.public_root, args.manifest, args.report), ensure_ascii=False))
