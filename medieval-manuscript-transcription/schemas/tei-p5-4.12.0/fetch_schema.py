from pathlib import Path
import urllib.request, json, hashlib, importlib.util
from html.parser import HTMLParser
HERE=Path(__file__).resolve().parent
class Links(HTMLParser):
    def __init__(self):super().__init__();self.links=[]
    def handle_starttag(self,tag,attrs):
        if tag=='a':self.links += [v for k,v in attrs if k=='href' and 'tei_all' in v]
base='https://tei-c.org/release/xml/tei/custom/schema/relaxng/'
p=Links();p.feed(urllib.request.urlopen(base,timeout=20).read().decode());print(p.links)
files=[]
for name in ['tei_all.rng']+[x for x in p.links if x.endswith(('.sch','.isosch'))]:
    data=urllib.request.urlopen(base+name,timeout=20).read()
    if name=='tei_all.rng':assert 'Version\u00a04.12.0' in data.decode('utf-8')[:1500]
    (HERE/name).write_bytes(data)
    files.append({'file':name,'url':base+name,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)})
(HERE/'sources.json').write_text(json.dumps({'tei_version':'4.12.0','release_url':'https://github.com/TEIC/TEI/releases/tag/P5_Release_4.12.0','retrieved_at':'2026-10-09','version_checked_in_rng_header':True,'files':files},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'schemas':files,'saxonche':bool(importlib.util.find_spec('saxonche')),'elementpath':bool(importlib.util.find_spec('elementpath'))}))
