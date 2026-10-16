"""Small, source-preserving Ministry of Culture credit for digitized manuscripts."""
import argparse
import hashlib
import re
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent
LOGO_SHA = '4a56caf133530ed276a94a4d57280c0fb888235bc23a70f8719144030ff0facf'
REV = '20261016-1'
CREDIT = '<aside class="digitization-support" aria-label="Podpora digitalizace"><p>Zdigitalizováno ve VISK 6</p><a href="https://www.mk.gov.cz/" aria-label="Ministerstvo kultury"><img src="/brand/logo-mk.svg" alt="Ministerstvo kultury" width="150" height="86" decoding="async"></a></aside>'


def install_assets(public):
    raw = (PACKAGE/'assets/logo-mk.svg').read_bytes()
    if hashlib.sha256(raw).hexdigest() != LOGO_SHA:
        raise ValueError('Changed official Ministry logo')
    (public/'brand').mkdir(parents=True, exist_ok=True)
    (public/'brand/logo-mk.svg').write_bytes(raw)
    (public/'support.css').write_bytes((PACKAGE/'support.css').read_bytes())


def stylesheet(text):
    text = re.sub(r'<link rel="stylesheet" href="/support\.css[^\"]*">', '', text)
    return text.replace('</head>', '<link rel="stylesheet" href="/support.css?v='+REV+'"></head>', 1)


def decorate_record(text):
    text = re.sub(r'<aside class="digitization-support".*?</aside>', '', text, flags=re.S)
    text, count = re.subn(r'(<div class="hero-actions">.*?</div>)', lambda m: m[1]+CREDIT, text, count=1, flags=re.S)
    if count != 1:
        raise ValueError('Missing manuscript overview actions')
    return stylesheet(text)


def decorate_viewer(text):
    text = re.sub(r'<aside class="digitization-support".*?</aside>', '', text, flags=re.S)
    text, count = re.subn(r'(<section class="tabpanel stack" id="panel-popis".*?)(</section>)', lambda m: m[1]+CREDIT+m[2], text, count=1, flags=re.S)
    if count != 1:
        raise ValueError('Missing viewer description panel')
    return stylesheet(text)


def update(public):
    public = public.resolve()
    candidates = []
    for ident in ('vkol-m-ii-220', 'vkol-m-ii-153'):
        path = public/'rukopisy'/(ident+'.html')
        candidates.append((path, decorate_record(path.read_text(encoding='utf8'))))
    path = public/'rukopis.html'
    candidates.append((path, decorate_viewer(path.read_text(encoding='utf8'))))
    install_assets(public)
    for path, text in candidates:
        path.write_text(text, encoding='utf8', newline='\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--public-root', type=Path, required=True)
    update(parser.parse_args().public_root)
    print('Official logo installed; two overviews and the shared viewer updated.')
