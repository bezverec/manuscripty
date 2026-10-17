"""Render actual model geometry; never infer physical lines from generated prose."""
from pathlib import Path
import json
import html
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent
ROOT = OUT.parent
GREEN = '#009e73'
ORANGE = '#d45b00'

def font(size):
    return ImageFont.truetype('C:/Windows/Fonts/arial.ttf', size)

def boxes(record, kraken):
    items = []
    for line in kraken.get('lines', []):
        boundary = line.get('boundary')
        if boundary:
            items.append(dict(id=line['id'], points=boundary, kind='kraken'))
    for block in record['blocks']:
        b = block['bbox_pixels_xyxy']
        if b:
            items.append(dict(id=block['id'], points=[[b[0],b[1]],[b[2],b[1]],[b[2],b[3]],[b[0],b[3]]], kind='chandra', label=block['label']))
    return items

def render_panels(record, kraken, crop=None, name='comparison.png'):
    folder = OUT / record['id']
    if record.get('crop_xyxy'):
        source = folder / 'crop.png'
    else:
        source = ROOT / record['image']
    im = Image.open(source).convert('RGB')
    if crop is None:
        crop = [0,0,*im.size]
    dx,dy = crop[:2]
    im = im.crop(crop)
    scale = min(700/im.width, 1400/im.height)
    w,h = round(im.width*scale), round(im.height*scale)
    im = im.resize((w,h), Image.Resampling.LANCZOS)
    result = Image.new('RGB',(3*w+40,h+90),'#faf7ef')
    draw = ImageDraw.Draw(result)
    items = boxes(record,kraken)
    labels = ['Vstup', f'Kraken: {len(kraken.get("lines", []))} segmentů' if kraken else 'Kraken: neporovnáváno', f'Chandra: {record["block_count"]} bloků']
    for column, kind in enumerate([None,'kraken','chandra']):
        panel = im.copy()
        pd = ImageDraw.Draw(panel)
        if kind:
            for obj in items:
                if obj['kind'] != kind:
                    continue
                points = [((x-dx)*scale,(y-dy)*scale) for x,y in obj['points']]
                color = GREEN if kind=='kraken' else ORANGE
                pd.line(points + points[:1],fill=color,width=2)
                if kind=='chandra':
                    x,y=points[0]
                    if 0 <= x < w and 0 <= y < h:
                        pd.text((x+3,y+3),obj['id'],font=font(16),fill=color,stroke_width=1,stroke_fill='white')
        x=column*(w+20)
        result.paste(panel,(x,48))
        draw.text((x+4,12),labels[column],font=font(20),fill='#202020')
    draw.text((4,h+60),f'{record["manuscript"]}, {record["folio"]} | zelená: polygony řádků; oranžová: obálky bloků | bez odborné revize',font=font(15),fill='#303030')
    result.save(folder / name)

def main():
    records = json.loads((OUT / 'results.json').read_text(encoding='utf-8'))
    notes_path = OUT / 'observations.json'
    notes = json.loads(notes_path.read_text(encoding='utf-8')) if notes_path.exists() else {}
    cards = []
    for r in records:
        folder = OUT / r['id']
        kraken = json.loads((folder/'kraken.json').read_text(encoding='utf-8')) if (folder/'kraken.json').exists() else {}
        render_panels(r,kraken)
        if r['id']=='mii220-335v':
            render_panels(r,kraken,crop=[900,220,4200,700],name='header-comparison.png')
        geometry = boxes(r,kraken)
        polygons = []
        for obj in geometry:
            kind=obj['kind']
            color=GREEN if kind=='kraken' else ORANGE
            pts=' '.join(f'{x},{y}' for x,y in obj['points'])
            tip=html.escape(obj['id']+' '+obj.get('label',''))
            polygons.append(f'<polygon class="{kind}" points="{pts}" fill="none" stroke="{color}" stroke-width="2" vector-effect="non-scaling-stroke"><title>{tip}</title></polygon>')
            if kind=='chandra':
                x,y=obj['points'][0]
                polygons.append(f'<text class="chandra" x="{x+10}" y="{y+65}" fill="{color}" font-size="55" stroke="white" stroke-width="8" paint-order="stroke">{obj["id"]}</text>')
        rows=''.join(f'<tr><td>{b["id"]}</td><td>{html.escape(b["label"] or "")}</td><td>{html.escape(str(b["bbox_raw"]))}</td><td>{html.escape(b["text"])}</td></tr>' for b in r['blocks'])
        warning='' if r['finish_reason']=='stop' else f'<p class="warning">Výstup skončil: {html.escape(r["finish_reason"])}</p>'
        note=''.join('<p>'+html.escape(n)+'</p>' for n in notes.get(r['id'],[]))
        sid=html.escape(r['id'])
        diagnostic='<p class="warning">Samostatný výřez originálu; nejde o shodný vstup s původní segmentací Kraken.</p>' if r.get('crop_xyxy') else ''
        cards.append(f'''<section id="{sid}"><h2>{r['manuscript']} · {r['folio']}{' · původní hlavička' if r.get('crop_xyxy') else ''}</h2>
<p>Kraken: {len(kraken.get('lines',[])) if kraken else '—'} řádkových segmentů · Chandra: {r['block_count']} bloků · {r['elapsed_seconds']:.1f} s · {r['usage']['completion_tokens']} výstupních tokenů · {r['finish_reason']}</p>{diagnostic}{warning}{note}
<div class="canvas"><svg viewBox="0 0 {r['width']} {r['height']}" aria-label="Srovnání skutečné geometrie {sid}" role="img"><image href="{sid}/preview.jpg" width="{r['width']}" height="{r['height']}" preserveAspectRatio="none"/>{''.join(polygons)}</svg></div>
<p><a href="{sid}/comparison.png">Srovnání vedle sebe (PNG)</a> · <a href="{sid}/result.json">Výsledek a souřadnice</a> · <a href="{sid}/response.json">Nezměněná odpověď</a> · <a href="{sid}/input.png">Skutečný vstup modelu</a></p>
<details><summary>Bloky a surový přepis Chandra – bez ověření správnosti textu</summary><table><thead><tr><th>ID</th><th>Typ</th><th>Obálka 0–1000</th><th>Text</th></tr></thead><tbody>{rows}</tbody></table></details></section>''')
    page='''<!doctype html><html lang="cs"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Chandra 2 × Kraken – segmentační pilot</title>
<style>:root{color-scheme:light dark}*{box-sizing:border-box}body{font:17px/1.6 system-ui;margin:0;background:#f7f4ec;color:#242522}main{max-width:1250px;margin:auto;padding:24px}a{color:#136098}h1{font-size:2rem;line-height:1.2}h2{margin-top:0}header{max-width:900px}.toolbar{position:sticky;top:0;background:#ece7db;padding:12px;z-index:2;border:1px solid #bcb8ad;display:flex;gap:24px;flex-wrap:wrap}section{margin:30px 0;padding:22px;border:1px solid #bcb8ad;background:#fffdf7}.canvas{overflow:auto;max-height:85vh;background:#ddd}.canvas svg{display:block;width:100%;height:auto}body.zoom .canvas svg{width:180%}body.no-kraken .kraken,body.no-chandra .chandra{display:none}table{border-collapse:collapse;width:100%}td,th{border:1px solid #bcb8ad;padding:8px;vertical-align:top}td:nth-child(4){white-space:pre-wrap}details{overflow:auto}.warning{border-left:4px solid #bd6c00;padding-left:12px}footer{padding:20px 0}@media(prefers-color-scheme:dark){body{background:#191b1c;color:#eee}.toolbar{background:#2d3031}section{background:#222526}a{color:#8bcaff}}</style>
<main><header><h1>Chandra 2 × Kraken</h1><p>Malý místní test segmentace obou olomouckých rukopisů · 17. 10. 2026.</p>
<p>Tři celé pracovní obrazy a jeden diagnostický výřez. Zeleně jsou skutečné polygony řádků Kraken, oranžově modelové obálky bloků Chandra. Počty bloků a řádků nejsou skóre přesnosti. Běžný prompt Chandra spojuje řádky do odstavců.</p>
<p>Kraken 7.1.1 / výchozí blla; Chandra OCR 2, revize af93b47dba1b47b6640c86ccf487ed2260ab9a09, lokálně na RTX 5070. Bez odborné referenční segmentace, CER a WER nebyly měřeny.</p>
<p><a href="report.md">Závěr a metodika</a> · <a href="run-config.json">Konfigurace</a> · <a href="results.json">Data</a> · <a href="prompt.txt">Přesný prompt</a></p></header>
<nav class="toolbar" aria-label="Vrstvy geometrie"><label><input type="checkbox" checked data-layer="kraken"> Kraken – řádky</label><label><input type="checkbox" checked data-layer="chandra"> Chandra – bloky</label><label><input type="checkbox" id="zoom"> Zvětšit obraz</label></nav>'''+''.join(cards)+'''<footer>Výzkumný návrh bez nezávislé odborné revize. Originály ani publikované přepisy se tímto experimentem nemění.</footer></main><script>document.querySelectorAll('[data-layer]').forEach(e=>e.addEventListener('change',()=>document.body.classList.toggle('no-'+e.dataset.layer,!e.checked)));document.getElementById('zoom').addEventListener('change',e=>document.body.classList.toggle('zoom',e.target.checked));</script></html>'''
    (OUT/'index.html').write_text(page,encoding='utf-8')
    print('Rendered',len(records),'samples')

if __name__=='__main__':
    main()
