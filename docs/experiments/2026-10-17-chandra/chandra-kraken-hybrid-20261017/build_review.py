"""Local comparison of archival and hybrid segmentation; no ground-truth scoring."""
from pathlib import Path
from collections import Counter
import json
import html
import math
from PIL import Image, ImageDraw, ImageFont

OUT=Path(__file__).resolve().parent
ROOT=OUT.parent
PRIOR=ROOT/'chandra-segmentation-pilot-20261017'
COLORS={'original':'#009e73','tight':'#9b37ac','padding64':'#0072b2','chandra':'#d45b00'}

def dump(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')

def bbox(line):
    xs,ys=zip(*line['boundary'])
    return [min(xs),min(ys),max(xs),max(ys)]

def iou(a,b):
    x=max(0,min(a[2],b[2])-max(a[0],b[0])); y=max(0,min(a[3],b[3])-max(a[1],b[1]))
    inter=x*y
    area=(a[2]-a[0])*(a[3]-a[1])+(b[2]-b[0])*(b[3]-b[1])-inter
    return inter/area if area else 0

def smaller_overlap(a,b):
    inter=max(0,min(a[2],b[2])-max(a[0],b[0]))*max(0,min(a[3],b[3])-max(a[1],b[1]))
    area=min((a[2]-a[0])*(a[3]-a[1]),(b[2]-b[0])*(b[3]-b[1]))
    return inter/area if area else 0

def audit(result):
    lines=result['lines']; pairs=[]
    for n,a in enumerate(lines):
        for b in lines[n+1:]:
            if a['chandra_block_id']==b['chandra_block_id']:
                continue
            score=iou(a['bbox_xyxy'],b['bbox_xyxy'])
            overlap=smaller_overlap(a['bbox_xyxy'],b['bbox_xyxy'])
            delta=abs(a['baseline_anchor_xy'][1]-b['baseline_anchor_xy'][1])
            h=min(a['bbox_xyxy'][3]-a['bbox_xyxy'][1],b['bbox_xyxy'][3]-b['bbox_xyxy'][1])
            if score>=0.5 or (overlap>=0.8 and delta<=0.3*h+12):
                pairs.append(dict(a=a['id'],b=b['id'],bbox_iou=score,intersection_over_smaller_bbox_area=overlap,baseline_anchor_y_difference=delta,interpretation='Possible complete/partial duplicate, not verified against reference'))
    return dict(id=result['id'],variant=result['variant'],line_count=len(lines),
                small_fragments=[l['id'] for l in lines if l['bbox_xyxy'][2]-l['bbox_xyxy'][0]<150 or l['bbox_xyxy'][3]-l['bbox_xyxy'][1]<25],
                block_counts={b['chandra_id']:len(b['lines']) for b in result['blocks']},
                block_statuses={b['chandra_id']:b['status'] for b in result['blocks']},
                errors=result['errors'],
                anchors_outside_block=[l['id'] for l in lines if l['anchor_outside_original_chandra_bbox']],
                near_crop_edge=[l['id'] for l in lines if l['near_crop_edge']],
                possible_duplicate_pairs=pairs,
                elapsed_seconds=result['elapsed_seconds'])

def font(size):
    return ImageFont.truetype('C:/Windows/Fonts/arial.ttf',size)

def source_image(rec):
    return Image.open(PRIOR/rec['id']/'crop.png' if rec.get('crop_xyxy') else ROOT/rec['image']).convert('RGB')

def draw_comparison(rec,layers,crop=None,filename='comparison.png',title_overrides=None):
    im=source_image(rec)
    crop=crop or [0,0,*im.size]
    dx,dy=crop[:2]
    im=im.crop(crop)
    factor=min(720/im.width,1400/im.height)
    w,h=round(im.width*factor),round(im.height*factor)
    im=im.resize((w,h),Image.Resampling.LANCZOS)
    canvas=Image.new('RGB',(3*w+32,h+95),'#f8f5ee')
    draw=ImageDraw.Draw(canvas)
    titles={'original':'Původní Kraken','tight':'Chandra → Kraken: těsně','padding64':'Chandra → Kraken: +64 px'}
    if title_overrides:titles.update(title_overrides)
    for col,kind in enumerate(['original','tight','padding64']):
        panel=im.copy(); pd=ImageDraw.Draw(panel)
        for line in layers[kind]:
            points=[((x-dx)*factor,(y-dy)*factor) for x,y in line['boundary']]
            pd.line(points+points[:1],fill=COLORS[kind],width=2)
        x=col*(w+16)
        canvas.paste(panel,(x,52))
        title=titles[kind]+(f' ({len(layers[kind])})' if layers[kind] or kind!='original' else ' (bez srovnání)')
        draw.text((x+4,12),title,font=font(19),fill=COLORS[kind])
    draw.text((4,h+64),f'{rec["manuscript"]} · {rec["folio"]} | skutečné polygony Kraken; počty nejsou skóre správnosti | bez odborné revize',font=font(15),fill='#222')
    canvas.save(OUT/rec['id']/filename)

def main():
    records=json.loads((PRIOR/'results.json').read_text(encoding='utf-8'))
    notes=json.loads((OUT/'observations.json').read_text(encoding='utf-8')) if (OUT/'observations.json').exists() else {}
    sections=[]; audits=[]; table=[]
    for rec in records:
        folder=OUT/rec['id']
        if not all((folder/v/'result.json').exists() for v in ['tight','padding64']):
            continue
        results={v:json.loads((folder/v/'result.json').read_text(encoding='utf-8')) for v in ['tight','padding64']}
        if any(r['status']!='complete' for r in results.values()):
            continue
        original=json.loads((ROOT/rec['kraken']).read_text(encoding='utf-8'))['lines'] if rec.get('kraken') else []
        layers=dict(original=original,**{v:r['lines'] for v,r in results.items()})
        for r in results.values(): audits.append(audit(r))
        full_source=source_image(rec)
        preview=full_source.copy(); preview.thumbnail((1500,1800)); preview.save(folder/'preview.jpg',quality=92)
        draw_comparison(rec,layers)
        if rec['id']=='mii220-335v':
            draw_comparison(rec,layers,[900,220,4200,700],'header-comparison.png')
            draw_comparison(rec,layers,[500,250,4200,2550],'text-comparison.png')
            control_path=OUT/'scale-control-335v.json'
            if control_path.exists():
                control=json.loads(control_path.read_text(encoding='utf-8'))
                draw_comparison(rec,dict(original=original,tight=control['lines'],padding64=layers['padding64']),[900,220,4200,700],'header-scale-control.png',{'tight':'Kraken: kontrola měřítka'})
        objects=[]; crop_manifest=[]
        for kind,lines in layers.items():
            image=full_source
            crop_dir=folder/kind/'crops'
            crop_dir.mkdir(parents=True,exist_ok=True)
            for line in lines:
                pts=' '.join(f'{x},{y}' for x,y in line['boundary'])
                label=html.escape(line['id'])
                x0,y0,x1,y1=bbox(line)
                crop_box=[max(0,math.floor(x0)-12),max(0,math.floor(y0)-12),min(image.width,math.ceil(x1)+13),min(image.height,math.ceil(y1)+13)]
                crop_path=crop_dir/(line['id']+'.png')
                if not crop_path.exists(): image.crop(crop_box).save(crop_path)
                # Show the actual pixel support selected for this model block,
                # alongside a full-source display crop. A generated polygon may
                # extend into white canvas beyond the selected source rectangle.
                effective_relative=None
                if kind!='original':
                    block=next(b for b in results[kind]['blocks'] if b['chandra_id']==line['chandra_block_id'])
                    bx0,by0,bx1,by1=block['crop_xyxy']
                    effective=Image.new('RGB',(crop_box[2]-crop_box[0],crop_box[3]-crop_box[1]),'white')
                    ix0,iy0,ix1,iy1=max(bx0,crop_box[0]),max(by0,crop_box[1]),min(bx1,crop_box[2]),min(by1,crop_box[3])
                    if ix0<ix1 and iy0<iy1:
                        effective.paste(image.crop((ix0,iy0,ix1,iy1)),(ix0-crop_box[0],iy0-crop_box[1]))
                    effective_path=crop_dir/(line['id']+'.effective.png')
                    if not effective_path.exists(): effective.save(effective_path)
                    effective_relative=effective_path.relative_to(OUT).as_posix()
                relative=crop_path.relative_to(OUT).as_posix()
                crop_manifest.append(dict(id=line['id'],variant=kind,crop=relative,effective_crop=effective_relative,crop_xyxy=crop_box,source='Full source display crop plus effective model-pixel crop; both have 12 px display context'))
                objects.append(f'<a href="{effective_relative or relative}" target="_blank"><polygon class="layer-{kind}" points="{pts}" fill="none" stroke="{COLORS[kind]}" stroke-width="2" pointer-events="all" vector-effect="non-scaling-stroke"><title>{label} – otevřít skutečné vstupní pixely řádku</title></polygon></a>')
        dump(folder/'crop-manifest.json',crop_manifest)
        for block in rec['blocks']:
            x0,y0,x1,y1=block['bbox_pixels_xyxy']
            objects.append(f'<rect class="layer-chandra" x="{x0}" y="{y0}" width="{x1-x0}" height="{y1-y0}" fill="none" stroke="{COLORS["chandra"]}" stroke-width="2" stroke-dasharray="8 5" vector-effect="non-scaling-stroke"><title>Chandra {block["id"]}</title></rect>')
        rows=[]
        for block in rec['blocks']:
            b=[next(b for b in results[v]['blocks'] if b['chandra_id']==block['id']) for v in ['tight','padding64']]
            rows.append('<tr><td>'+block['id']+'</td><td>'+html.escape(block['label'] or '')+'</td>'+''.join(f'<td>{len(x["lines"])} ({x["status"]})</td>' for x in b)+'</tr>')
        n0=len(original) if rec.get('kraken') else '—'
        n1,n2=[results[v]['line_count'] for v in ['tight','padding64']]
        table.append(f'<tr><td><a href="#{rec["id"]}">{rec["manuscript"]} {rec["folio"]}{" – výřez" if rec.get("crop_xyxy") else ""}</a></td><td>{n0}</td><td>{n1}</td><td>{n2}</td></tr>')
        explanation=''.join('<p>'+html.escape(n)+'</p>' for n in notes.get(rec['id'],[]))
        if rec['id']=='mii220-335v' and (OUT/'scale-control-335v.json').exists():
            explanation+='<p><a href="mii220-335v/header-scale-control.png">Kontrola měřítka hlavičky bez oblastí Chandra</a> · <a href="scale-control-335v.json">Kontrolní segmentace JSON</a></p>'
        warning='<p>Samostatný výřez originálu; proti původnímu Kraken zde neprovádíme přímé srovnání.</p>' if rec.get('crop_xyxy') else ''
        sections.append(f'''<section id="{rec['id']}"><h2>{rec['manuscript']} · {rec['folio']}{' – původní hlavička' if rec.get('crop_xyxy') else ''}</h2>{warning}{explanation}
<p>Původní Kraken: {n0} · těsné bloky: {n1} · bloky s přesahem: {n2}</p>
<div class="canvas"><svg viewBox="0 0 {rec['width']} {rec['height']}" role="img" aria-label="Srovnání segmentace {rec['id']}"><image href="{rec['id']}/preview.jpg" width="{rec['width']}" height="{rec['height']}" preserveAspectRatio="none"/>{''.join(objects)}</svg></div>
<p><a href="{rec['id']}/comparison.png">Srovnání vedle sebe</a> · <a href="{rec['id']}/tight/result.json">Těsná varianta JSON</a> · <a href="{rec['id']}/padding64/result.json">Přesah 64 px JSON</a></p>
<details><summary>Počet a stav řádků v jednotlivých oblastech</summary><table><thead><tr><th>Blok Chandra</th><th>Typ</th><th>Těsně</th><th>+64 px</th></tr></thead><tbody>{''.join(rows)}</tbody></table></details></section>''')
    dump(OUT/'geometry-audit.json',audits)
    page='''<!doctype html><html lang="cs"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Chandra → Kraken: hybridní segmentace</title>
<style>:root{color-scheme:light dark}*{box-sizing:border-box}body{font:17px/1.6 system-ui;background:#f8f5ee;color:#242424;margin:0}main{max-width:1300px;margin:auto;padding:24px}header{max-width:980px}h1{font-size:2rem;line-height:1.2}a{color:#136098}section{background:#fffdf8;border:1px solid #bcb7ad;padding:22px;margin:30px 0}.toolbar{position:sticky;top:0;padding:12px;background:#e8e2d5;z-index:2;display:flex;gap:20px;flex-wrap:wrap;border:1px solid #bcb7ad}.canvas{overflow:auto;max-height:85vh;background:#ddd}.canvas svg{display:block;width:100%;height:auto}body.zoom .canvas svg{width:200%}body.hide-original .layer-original,body.hide-tight .layer-tight,body.hide-padding64 .layer-padding64,body.hide-chandra .layer-chandra{display:none}table{border-collapse:collapse;max-width:100%;font-variant-numeric:tabular-nums}th,td{border:1px solid #bcb7ad;padding:8px;text-align:left}footer{margin:24px 0}@media(prefers-color-scheme:dark){body{background:#181b1d;color:#eee}section{background:#222628}.toolbar{background:#303536}a{color:#8ecaff}}</style>
<main><header><h1>Chandra → Kraken</h1><p>Stejné tři pracovní strany a doplňkový výřez hlavičky jako v předchozím pilotu. Chandra vymezila oblasti, Kraken 7.1.1 s původním modelem blla nyní v každé oblasti znovu vyhledal řádky.</p>
<p>Dvě předem určené varianty: zaokrouhlená obálka Chandra a stejná obálka s přesahem 64 pixelů. Vybrané původní pixely jsou vloženy do bílého kontextu o výšce originálu, aby Kraken nezvětšoval drobné oblasti na výšku celé strany. Všechny skutečně detekované řádky jsou zachovány, včetně možných duplicit. Nebyly doplněny ruční baseline ani odvozené souřadnice z textu.</p><p>Kliknutím na polygon lze otevřít skutečné vstupní pixely jeho oblasti; obsah mimo vybranou oblast je bílý. Samotný polygon může do bílého okolí přesahovat. Vrstvy se přepínají níže; pro detail použijte zvětšení.</p>
<p><a href="report.md">Závěr a metodika</a> · <a href="summary.json">Průběh a výsledky</a> · <a href="engine.json">Verze segmentátoru</a> · <a href="geometry-audit.json">Geometrické příznaky</a> · <a href="../chandra-segmentation-pilot-20261017/index.html">Předchozí Chandra pilot</a></p>
<table><thead><tr><th>Vzorek</th><th>Původní Kraken</th><th>Těsná oblast</th><th>Přesah 64 px</th></tr></thead><tbody>'''+''.join(table)+'''</tbody></table><p>Počet řádkových segmentů není skóre správnosti; bez odborné referenční segmentace neměříme přesnost.</p></header>
<nav class="toolbar" aria-label="Vrstvy segmentace"><label style="color:#009e73"><input type="checkbox" checked data-layer="original"> Původní Kraken</label><label style="color:#9b37ac"><input type="checkbox" data-layer="tight"> Hybrid těsně</label><label style="color:#0072b2"><input type="checkbox" checked data-layer="padding64"> Hybrid +64 px</label><label style="color:#d45b00"><input type="checkbox" data-layer="chandra"> Oblasti Chandra</label><label><input type="checkbox" id="zoom"> Zvětšit</label></nav>'''+''.join(sections)+'''<footer>Experimentální návrh bez nezávislé odborné revize. Originály, starší segmentace ani veřejný web se nemění.</footer></main><script>document.querySelectorAll('[data-layer]').forEach(e=>{function update(){document.body.classList.toggle('hide-'+e.dataset.layer,!e.checked)}update();e.addEventListener('change',update)});document.getElementById('zoom').addEventListener('change',e=>document.body.classList.toggle('zoom',e.target.checked));</script></html>'''
    (OUT/'index.html').write_text(page,encoding='utf-8')
    print('Rendered',len(sections),'samples')

if __name__=='__main__': main()
