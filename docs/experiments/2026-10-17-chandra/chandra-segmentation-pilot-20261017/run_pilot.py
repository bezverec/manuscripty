"""Small, non-destructive local layout comparison; raw responses retained."""
from pathlib import Path
import ast
import base64
import hashlib
import importlib.util
import io
import json
import platform
import subprocess
import time
import urllib.request
from datetime import datetime, timezone
from typing import Tuple

from PIL import Image
from lxml import html

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent
LOCAL_CHANDRA = Path('C:/temp/aindk/aiocr-proarc-gateway/chandra')
ENDPOINT = 'http://127.0.0.1:18086/v1'

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()

def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')

def http_json(url, payload=None, timeout=600):
    data = json.dumps(payload).encode('utf-8') if payload is not None else None
    request = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)

def load_prompt_and_scaler():
    # Read only the inspected upstream prompt constants and resize function.
    prompt_file = LOCAL_CHANDRA / 'prompts.py'
    spec = importlib.util.spec_from_file_location('pilot_chandra_prompts', prompt_file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    util_file = LOCAL_CHANDRA / 'model/util.py'
    tree = ast.parse(util_file.read_text(encoding='utf-8'))
    function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'scale_to_fit')
    namespace = {'Image': Image, 'Tuple': Tuple}
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(util_file), 'exec'), namespace)
    (OUT / 'prompt.txt').write_text(mod.OCR_LAYOUT_PROMPT, encoding='utf-8')
    (OUT / 'upstream-scale-to-fit.py.txt').write_text(ast.get_source_segment(util_file.read_text(encoding='utf-8'), function), encoding='utf-8')
    return mod.OCR_LAYOUT_PROMPT, namespace['scale_to_fit'], {
        'prompt_source': str(prompt_file), 'prompt_source_sha256': sha(prompt_file),
        'resize_source': str(util_file), 'resize_source_sha256': sha(util_file),
    }

SAMPLES = [
    dict(id='mii220-335v', manuscript='M II 220', folio='335v',
         image='htr-sixth-94-pages/pages/335v/image.png',
         original='EX/M_II_220____26LY4SCEX0335V.TIF',
         kraken='htr-sixth-94-pages/pages/335v/segmentation.json',
         provenance='htr-sixth-94-pages/pages/335v/catmus-run.json'),
    dict(id='mii220-20v', manuscript='M II 220', folio='20v',
         image='pilot-20r-21r/images/20v.png',
         original='EX/M_II_220____26LY4SCEX0020V.TIF',
         kraken='pilot-20r-21r/htr/20v.segmentation.json',
         provenance='pilot-20r-21r/manifest.json'),
    dict(id='mii153-5r', manuscript='M II 153', folio='5r',
         image='VKO___M_II_153____2Y2A3I8/full-htr-20261012/pages/5r/image.png',
         original='VKO___M_II_153____2Y2A3I8/EX/M_II_153____2Y2A3I8EX0005R.TIF',
         kraken='VKO___M_II_153____2Y2A3I8/full-htr-20261012/pages/5r/segmentation.json',
         provenance='VKO___M_II_153____2Y2A3I8/full-htr-20261012/pages/5r/catmus-run.json'),
    dict(id='mii220-335v-header-original', manuscript='M II 220', folio='335v',
         image='EX/M_II_220____26LY4SCEX0335V.TIF',
         original='EX/M_II_220____26LY4SCEX0335V.TIF',
         crop_xyxy=[900, 180, 4200, 700],
         comparison_scope='Diagnostic original crop, not identical to masked Kraken input'),
]

def main():
    OUT.mkdir(exist_ok=True)
    prompt, scale, source_versions = load_prompt_and_scaler()
    config = dict(started_utc=datetime.now(timezone.utc).isoformat(),
                  model='datalab-to/chandra-ocr-2', revision='af93b47dba1b47b6640c86ccf487ed2260ab9a09',
                  served_model='chandra', endpoint=ENDPOINT, temperature=0, top_p=0.1,
                  max_tokens=6000, python=platform.python_version(),
                  cuda_device='NVIDIA GeForce RTX 5070 / 12 GB',
                  inference='Existing local vLLM service; no paid API',
                  bbox_space='0..1000 normalized xyxy; mapped directly to corresponding input image dimensions',
                  comparison='Three same-working-image comparisons and one separate original-header diagnostic',
                  expert_review=False, **source_versions)
    config['server_models'] = http_json(ENDPOINT + '/models', timeout=10)
    dump(OUT / 'run-config.json', config)
    records = []
    for sample in SAMPLES:
        folder = OUT / sample['id']
        folder.mkdir(exist_ok=True)
        if (folder / 'result.json').exists():
            record = json.loads((folder / 'result.json').read_text(encoding='utf-8'))
            print('REUSE', sample['id'], flush=True)
            records.append(record)
            continue
        source = ROOT / sample['image']
        with Image.open(source) as opened:
            opened.seek(0)
            original_size = opened.size
            im = opened.convert('RGB')
        if 'crop_xyxy' in sample:
            im = im.crop(sample['crop_xyxy'])
        width, height = im.size
        preview = im.copy()
        preview.thumbnail((1500, 1800))
        preview.save(folder / 'preview.jpg', quality=92)
        if 'crop_xyxy' in sample:
            im.save(folder / 'crop.png')
        scaled = scale(im)
        scaled.save(folder / 'input.png')
        meta = dict(**sample, width=width, height=height, parent_size=list(original_size),
                    model_input_size=list(scaled.size), working_source_sha256=sha(source),
                    original_sha256=sha(ROOT / sample['original']),
                    model_input_sha256=sha(folder / 'input.png'))
        if 'kraken' in sample:
            kpath = ROOT / sample['kraken']
            k = json.loads(kpath.read_text(encoding='utf-8'))
            meta['kraken_segmentation_sha256'] = sha(kpath)
            meta['kraken_lines'] = len(k.get('lines', []))
            meta['kraken_regions'] = len(k.get('regions', {}))
            dump(folder / 'kraken.json', k)
        dump(folder / 'source.json', meta)
        content = [dict(type='image_url', image_url={'url':'data:image/png;base64,' + base64.b64encode((folder / 'input.png').read_bytes()).decode('ascii')}), dict(type='text', text=prompt)]
        payload = dict(model='chandra', messages=[dict(role='user', content=content)],
                       max_tokens=6000, temperature=0, top_p=0.1, seed=42)
        # Save a reference-based request manifest, not another copy of the base64 image.
        dump(folder / 'request.json', dict(model='chandra', prompt='../prompt.txt', image='input.png',
                                         max_tokens=6000, temperature=0, top_p=0.1, seed=42))
        print('START', sample['id'], list(scaled.size), flush=True)
        started = datetime.now(timezone.utc).isoformat()
        t0 = time.perf_counter()
        raw = http_json(ENDPOINT + '/chat/completions', payload)
        elapsed = time.perf_counter() - t0
        dump(folder / 'response.json', raw)
        text = raw['choices'][0]['message']['content'] or ''
        (folder / 'raw.html').write_text(text, encoding='utf-8')
        blocks = []
        doc = html.fragment_fromstring(text, create_parent=True)
        for i, element in enumerate(doc.xpath('//*[@data-bbox]'), 1):
            raw_box = element.get('data-bbox')
            try:
                coords = [float(v) for v in raw_box.replace(',', ' ').replace('[','').replace(']','').split()]
                valid = len(coords) == 4 and all(0 <= v <= 1000 for v in coords) and coords[0] < coords[2] and coords[1] < coords[3]
            except ValueError:
                coords, valid = [], False
            box = [coords[0]*width/1000, coords[1]*height/1000, coords[2]*width/1000, coords[3]*height/1000] if valid else None
            parent_box = None
            if valid and 'crop_xyxy' in sample:
                x, y = sample['crop_xyxy'][:2]
                parent_box = [box[0]+x, box[1]+y, box[2]+x, box[3]+y]
            blocks.append(dict(id=f'b{i:03}', label=element.get('data-label'),
                               bbox_raw=raw_box, bbox_normalized=coords, valid_bbox=valid,
                               bbox_pixels_xyxy=box, bbox_parent_pixels_xyxy=parent_box,
                               text=element.text_content(), html=html.tostring(element, encoding='unicode')))
        record = dict(**meta, started_utc=started, elapsed_seconds=elapsed,
                      finish_reason=raw['choices'][0]['finish_reason'], usage=raw.get('usage'),
                      blocks=blocks, block_count=len(blocks),
                      valid_block_count=sum(b['valid_bbox'] for b in blocks),
                      raw_sha256=sha(folder / 'raw.html'), expert_review=False,
                      recognition_not_scored=True)
        dump(folder / 'result.json', record)
        records.append(record)
        dump(OUT / 'results.json', records)
        print('DONE', sample['id'], round(elapsed, 2), 'seconds', len(blocks), 'blocks', record['finish_reason'], raw.get('usage'), flush=True)
    dump(OUT / 'results.json', records)

if __name__ == '__main__':
    main()
