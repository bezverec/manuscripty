"""Presentation helpers for catalogue descriptions; research data stay untouched."""
import argparse
import html
import json
import re
from pathlib import Path


def without_fixity_notice(record):
    return re.sub(r'<p\b[^>]*>(?:(?!</p>).)*fixity\.md5(?:(?!</p>).)*</p>', '', record, flags=re.I | re.S)


def legacy_catalogue_section(doc):
    catalogue = json.loads(Path(__file__).with_name('mii220-catalogue.json').read_text(encoding='utf8'))
    if catalogue['source_sha256'] != doc['source_metadata']['sha256']:
        raise ValueError('Catalogue source differs from manuscript metadata')

    def rows(items, is_nested=False):
        result = []
        for item in items:
            start, end = item['from'], item['to']
            if not all(re.fullmatch(r'\d+[rv]', value) for value in (start, end)):
                raise ValueError('Unexpected catalogue folio')
            label = start if start == end else start + '–' + end
            nested = '<ol>' + rows(item['children'], True) + '</ol>' if item['children'] else ''
            title = item['title'] or ('Pododdíl ' if is_nested else 'Katalogová položka ') + item['number']
            result.append('<li><a href="/rukopis#' + start + '">' + html.escape(title) + '</a> · ' + label + nested + '</li>')
        return ''.join(result)

    return '<article id="katalogovy-obsah"><h2>Katalogový obsah kodexu</h2><p>Soubor obsahuje 57 hlavních katalogových položek, 64 včetně vnořených. Názvy a rozsahy pocházejí z dodaného digitalizačního XML; některé texty sdílejí stejné folio. Odkazy otevírají příslušnou stranu rukopisu.</p><ol>' + rows(catalogue['items']) + '</ol></article>'


def update_records(public):
    target = public / 'rukopisy/vkol-m-ii-220.html'
    doc = json.loads((public / 'document.json').read_text(encoding='utf8'))
    record = target.read_text(encoding='utf8')
    section = legacy_catalogue_section(doc)
    if 'id="katalogovy-obsah"' in record:
        record, count = re.subn(r'<article id="katalogovy-obsah">.*?</article>', lambda _: section, record, flags=re.S)
        if count != 1:
            raise ValueError('Ambiguous catalogue section')
    else:
        anchor = '<article><h2>TEI a podklady</h2>'
        if record.count(anchor) != 1:
            raise ValueError('Missing catalogue insertion point')
        record = record.replace(anchor, section + anchor, 1)
    record = record.replace('Záznam celého dokumentu', 'Popis a zdroje')
    record = record.replace('Rukopisy · výzkumný pilot</a>', 'Rukopisy, snímek po snímku.</a>')
    record = record.replace('v záložce „O zpracování“', 'v záložce „O rukopisu“')
    link = '<a class="btn" href="#katalogovy-obsah">Katalogový obsah</a>'
    if 'href="#katalogovy-obsah"' not in record:
        record = record.replace('<a class="btn" href="/summary">AI shrnutí</a></div>', '<a class="btn" href="/summary">AI shrnutí</a>' + link + '</div>', 1)
    target.write_text(without_fixity_notice(record), encoding='utf8', newline='\n')
    second = public / 'rukopisy/vkol-m-ii-153.html'
    second.write_text(without_fixity_notice(second.read_text(encoding='utf8')), encoding='utf8', newline='\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--public-root', type=Path, required=True)
    update_records(parser.parse_args().public_root.resolve())
