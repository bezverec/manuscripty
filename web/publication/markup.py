"""Normalize authored presentation markup without changing research text."""
import argparse, re
from pathlib import Path

def normalize_html(text):
    text = re.sub(r'<!doctype html>', '<!DOCTYPE html>', text, count=1, flags=re.I)
    text = text.replace('<label for="folio-search-query">', '<label>')
    return text.replace('<div class="summary-sources" aria-label=', '<div class="summary-sources" role="group" aria-label=')

if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--staged',type=Path,required=True)
    root=parser.parse_args().staged.resolve()
    for name in ('index.html','summary.html','rukopisy/vkol-m-ii-153.html','rukopisy/vkol-m-ii-220.html','rukopisy/vkol-m-ii-153/shrnuti.html'):
        target=root/name
        text=target.read_text(encoding='utf8')
        target.write_text(normalize_html(text),encoding='utf8',newline='\n')
