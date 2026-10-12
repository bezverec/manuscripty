"""Synthetic images only. Never loads media-jobs or archive TIFF."""
import unittest,tempfile,json,hashlib
from pathlib import Path
from PIL import Image
from build_media import build_iiif_image

class StaticIIIFTest(unittest.TestCase):
 def test_partial_edges_and_all_advertised_requests(self):
  with tempfile.TemporaryDirectory() as folder:
   im=Image.new('RGB',(1031,777),'white')
   for y in range(im.height):
    for x in range(im.width):im.putpixel((x,y),((x//512)*70,(y//512)*90,120))
   original=hashlib.sha256(im.tobytes()).hexdigest()
   objects=build_iiif_image(im,'test',folder)
   info=json.loads((Path(folder)/'iiif/test/info.json').read_text())
   self.assertEqual(info['profile'],'level0');self.assertEqual(info['tiles'],[{'width':512,'scaleFactors':[1,2,4]}])
   self.assertEqual(hashlib.sha256(im.tobytes()).hexdigest(),original)
   for obj in objects:
    data=(Path(folder)/obj['key']).read_bytes();self.assertEqual(len(data),obj['bytes']);self.assertEqual(hashlib.sha256(data).hexdigest(),obj['sha256'])
   for scale in info['tiles'][0]['scaleFactors']:
    for y in range(0,777,512*scale):
     for x in range(0,1031,512*scale):
      rw,rh=min(512*scale,1031-x),min(512*scale,777-y)
      ow,oh=(rw+scale-1)//scale,(rh+scale-1)//scale
      for ext in ('webp','jpg'):
       with Image.open(Path(folder)/f'iiif/test/{x},{y},{rw},{rh}/{ow},{oh}/0/default.{ext}') as tile:
        self.assertEqual(tile.size,(ow,oh));self.assertLessEqual(tile.width,512);self.assertLessEqual(tile.height,512)
        # Allow Lanczos edge mixing and Q90 lossy compression, while detecting wrong tile origins.
        self.assertLess(abs(tile.getpixel((0,0))[0]-(x//512)*70),30)
   for size in info['sizes']:
    for ext in ('jpg','webp'):
     with Image.open(Path(folder)/f"iiif/test/full/{size['width']},{size['height']}/0/default.{ext}") as image:self.assertEqual(image.size,(size['width'],size['height']))
   with Image.open(Path(folder)/'iiif/test/full/max/0/default.jpg') as image:self.assertEqual(image.size,(1031,777))
 def test_namespace_and_path_safety(self):
  with tempfile.TemporaryDirectory() as folder:
   objects=build_iiif_image(Image.new('RGB',(3,5)),'1r',folder,namespace='second')
   self.assertTrue(all(o['key'].startswith('iiif/second/1r/') for o in objects))
   self.assertEqual(json.loads((Path(folder)/'iiif/second/1r/info.json').read_text())['id'],'https://rukopisy-data.digitalizaty.cz/iiif/second/1r')
   with self.assertRaises(ValueError):build_iiif_image(Image.new('RGB',(1,1)),'../bad',folder)

if __name__=='__main__':unittest.main()
