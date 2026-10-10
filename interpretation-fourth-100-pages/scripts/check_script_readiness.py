"""Focused local smoke checks; temporary synthetic pixels are not manuscript evidence."""
import ast,importlib.util,tempfile,json
from pathlib import Path
from html.parser import HTMLParser
from lxml import etree as E
from PIL import Image,ImageChops,ImageDraw
S=Path(__file__).resolve().parent
# Import preparation normally, then exercise it in an isolated temporary batch.
spec=importlib.util.spec_from_file_location('native_inputs_check',S/'native_inputs.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
test_base=(S/'readiness-temp').resolve()
assert test_base.is_relative_to(S.resolve()),'Unsafe synthetic check directory'
test_base.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(prefix='mii220-script-check-',dir=str(test_base)) as temp:
 assert Path(temp).resolve().is_relative_to(test_base),'Unsafe synthetic fixture path'
 root=Path(temp);out=root/'interpretation-fourth-100-pages';out.mkdir()
 raw=root/'htr-fourth-100-pages';(raw/'pages/184r').mkdir(parents=True)
 image=raw/'pages/184r/image.png';Image.new('RGB',(2300,1800),(27,83,149)).save(image)
 source={'folio':'184r','regions':[[100,50,2200,1750]],'width':2300,'height':1800,
 'original':'synthetic-unused.tif','original_sha256':'synthetic-unused','working_image':'pages/184r/image.png','working_image_sha256':m.sha(image)}
 (raw/'manifest.json').write_text(json.dumps({'pages':[source]}),encoding='utf-8')
 m.I=out;m.ROOT=root
 assert m.manifest_pages()==[source]
 try:m.manifest_pages(require_complete=True)
 except AssertionError:pass
 else:raise AssertionError('Incomplete manifest was accepted as complete')
 assert m.prepare_reading(source)==2
 inputs=m.read(out/'184r/inputs.json');mask=Image.new('1',(2300,1800),0);draw=ImageDraw.Draw(mask)
 with Image.open(image) as expected:
  for t in inputs['tiles']:
   b=t['bbox_xyxy'];draw.rectangle((b[0],b[1],b[2]-1,b[3]-1),fill=1)
   with Image.open(out/'184r'/t['image']) as actual:
    assert ImageChops.difference(actual,expected.crop(b)).getbbox() is None
 assert mask.crop(source['regions'][0]).getextrema()==(1,1)
 assert m.prepare_reading(source)==2 and len(m.read(out/'184r/inputs.json')['tiles'])==2
 bad={**source,'working_image_sha256':'wrong'}
 try:m.prepare_inputs(bad)
 except AssertionError:pass
 else:raise AssertionError('Bad image checksum accepted')
 # Extract only pure exporter helpers: do not execute the actual batch export.
 tree=ast.parse((S/'export_interpretation.py').read_text(encoding='utf-8'))
 names={'relative_opened_tiles','LocalLinks','parsed_html'}
 module=ast.Module(body=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in names],type_ignores=[])
 scope={'Path':Path,'HTMLParser':HTMLParser,'I':out,'parser_cache':{}}
 exec(compile(module,'exporter-helpers','exec'),scope)
 fn=scope['relative_opened_tiles']
 assert fn({'image_inspection':{'tiles':['tiles/read-z1-y1-x1.png']}},'184r')==['tiles/read-z1-y1-x1.png']
 assert fn({'image_inspection':{'tiles':['D:/VKO___M_II_220____26LY4SC/interpretation-fourth-100-pages/184r/tiles/read-z1-y1-x1.png']}},'184r')==['tiles/read-z1-y1-x1.png']
 assert fn({'image_inspection':{'tiles':[str(out/'184r/tiles/read-z1-y1-x1.png')]}},'184r')==['tiles/read-z1-y1-x1.png']
 for bad in ['tiles/../wrong.png','D:/VKO___M_II_220____26LY4SC/interpretation-all-pages/184r/tiles/read-z1-y1-x1.png','D:/VKO___M_II_220____26LY4SC/interpretation-third-100-pages/184r/tiles/read-z1-y1-x1.png']:
  try:fn({'image_inspection':{'tiles':[bad]}},'184r')
  except AssertionError:pass
  else:raise AssertionError('Unsafe/old evidence path accepted')
 hp=out/'fixture.html';hp.write_text('<html><a id="anchor" href="#anchor">x</a></html>',encoding='utf-8')
 parse=scope['parsed_html'];one=parse(hp);two=parse(hp)
 assert one is two and 'anchor' in two.ids and 'absent' not in two.ids and len(scope['parser_cache'])==1
 try:parse(out/'missing.html')
 except AssertionError:pass
 else:raise AssertionError('Missing HTML accepted')
print('SCRIPT_READINESS_PASSED: manifest isolation, native pixel/coverage/SHA, idempotence, evidence paths, HTML parser cache/anchors/existence')
