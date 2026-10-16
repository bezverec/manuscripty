"""Install the shared theme on presentation HTML only; never touch research data."""
import argparse
import re
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent
REV = '20261016-3'


def decorate(text):
    text = re.sub(r'<script src="/theme\.js[^\"]*"></script>', '', text)
    text = re.sub(r'<link rel="stylesheet" href="/theme\.css[^\"]*">', '', text)
    text, count = re.subn(r'(<meta charset="utf-8">)', lambda m: m[1]+'<script src="/theme.js?v='+REV+'"></script>', text, count=1, flags=re.I)
    if count != 1 or '</head>' not in text:
        raise ValueError('Missing HTML encoding/head for theme bootstrap')
    return text.replace('</head>', '<link rel="stylesheet" href="/theme.css?v='+REV+'"></head>', 1)


def install_assets(public):
    for name in ('theme.js', 'theme.css'):
        (public/name).write_bytes((PACKAGE/name).read_bytes())


def update(public):
    public = public.resolve()
    # Public data/ can contain edition HTML: only site and folio presentation are selected.
    targets = [public/name for name in ('index.html','rukopis.html','404.html','summary.html')]
    targets += sorted((public/'rukopisy').rglob('*.html'))
    candidates = [(p, decorate(p.read_text(encoding='utf8'))) for p in targets if p.exists()]
    install_assets(public)
    for path, text in candidates:
        path.write_text(text, encoding='utf8', newline='\n')
    return len(candidates)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--public-root', type=Path, required=True)
    args = parser.parse_args()
    print('Theme installed on', update(args.public_root), 'presentation pages.')
