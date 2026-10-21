"""Separate diagnostic inputs; never changes original crops or HTR candidates."""
from pathlib import Path
from PIL import Image, ImageDraw
import json, hashlib, datetime

parser = __import__('argparse').ArgumentParser(description=__doc__)
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--out', type=Path, required=True)
args = parser.parse_args()
H = args.source.resolve()
OUT = args.out.resolve()
if OUT.exists(): raise SystemExit('Output must be a new directory')
if OUT.is_relative_to(H) or H.is_relative_to(OUT): raise SystemExit('Source/output must be disjoint')
OUT.mkdir(parents=True)
TARGETS = [('27v', 63), ('46v', 53), ('97v', 14), ('119v', 28), ('124v', 100)]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p, data): p.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

def main():
    manifest = {'expert_review': False, 'status': 'diagnostic_inputs', 'originals_modified': False,
                'method': 'Original polygon mask; per-column integer vertical translation to straighten recorded baseline; no scaling. Separate half-line trials overlap 120 pixels. White composite is a diagnostic layout, not a manuscript page.',
                'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'inputs': []}
    canvas = Image.new('RGB', (3000, 3000), 'white')
    slot = 0
    for folio, n in TARGETS:
        p = H/'pages'/folio
        comp = json.loads((p/'comparison.json').read_text('utf-8'))
        row = comp['lines'][n-1]
        source = p/row['image']
        assert sha(source) == row['image_sha256']
        im = Image.open(source).convert('RGB')
        x0,y0,x1,y1 = row['bbox_xyxy']
        mask = Image.new('L', im.size, 0)
        ImageDraw.Draw(mask).polygon([(x-x0,y-y0) for x,y in row['boundary']], fill=255)
        masked = Image.new('RGB', im.size, 'white'); masked.paste(im, (0,0), mask)
        baseline = row['baseline']
        def by(x):
            for a,b in zip(baseline, baseline[1:]):
                if a[0] <= x <= b[0]: return a[1]+(b[1]-a[1])*(x-a[0])/(b[0]-a[0])
            return baseline[0][1] if x < baseline[0][0] else baseline[-1][1]
        # Extra vertical space preserves every polygon pixel after integer shift.
        straight = Image.new('RGB', (im.width, im.height+200), 'white')
        shifts=[]
        for x in range(im.width):
            shift=150-round(by(x+x0)-y0); shifts.append(shift)
            straight.paste(masked.crop((x,0,x+1,im.height)), (x,shift))
        variants=[('straight',0,im.width)]
        if folio in ('97v','119v'):
            variants += [('left',0,im.width//2+60), ('right',im.width//2-60,im.width)]
        for name,left,right in variants:
            crop=straight.crop((left,0,right,straight.height))
            filename=f'{row["id"]}-{name}.png'; crop.save(OUT/filename)
            dest=[100, slot*300+20,100+crop.width,slot*300+20+crop.height]
            # Vertical whitespace slots are wider than visible ink; the saved crop includes padding.
            canvas.paste(crop, (dest[0],dest[1]))
            manifest['inputs'].append({'id':row['id']+'-'+name,'source_line_id':row['id'],
                'folio':folio,'segment':n,'file':filename,'sha256':sha(OUT/filename),
                'source_crop':str(source),'source_crop_sha256':sha(source),
                'source_bbox_xyxy':row['bbox_xyxy'],'source_boundary':row['boundary'],
                'source_baseline':baseline,'source_x_interval':[left,right],
                'column_vertical_shifts':shifts[left:right], 'composite_bbox_xyxy':dest})
            slot+=1
    canvas.save(OUT/'diagnostic-composite.png')
    manifest['composite_sha256']=sha(OUT/'diagnostic-composite.png')
    write(OUT/'input-manifest.json',manifest)
    print(json.dumps({'inputs':len(manifest['inputs']),'composite_sha256':manifest['composite_sha256']}))

if __name__=='__main__': main()
