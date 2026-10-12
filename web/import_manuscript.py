"""Import a validated publication overlay, preserving existing research layers.

Requires the reviewed phase-5 public baseline and the explicit complete build
report. Never removes files, copies media, or silently accepts legacy text edits.
"""
from pathlib import Path
import argparse, hashlib, json, re, shutil
from lxml import etree

ROOT=Path(__file__).resolve().parents[1]
PUBLIC=ROOT/'web/public'
ALLOW={'web/public/pilot-data.js','web/public/document.json','web/public/tei/vkol-m-ii-220.xml'}
PROTECTED=('web/public/data/','web/public/tei/','web/public/schemas/')
PROTECTED_FILES={'web/public/pilot-data.js','web/public/document.json','web/public/structure.json','web/public/summary.json'}
def load(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pilot(p):
 m=re.fullmatch(r'window\.PILOT_DATA\s*=\s*(\{.*\});\s*',p.read_text(encoding='utf8'),re.S)
 if not m:raise ValueError('Invalid pilot manifest')
 return json.loads(m.group(1))

def run(staged,build_report,audit_report):
 staged=staged.resolve()
 if staged==PUBLIC.resolve() or staged.is_relative_to(PUBLIC.resolve()) or PUBLIC.resolve().is_relative_to(staged):raise ValueError('Staging and public must be disjoint')
 report=load(build_report)
 if not report['publication_ready'] or report['required_missing'] or report['counts']['pages']!=197 or report['counts']['lines']!=15013:raise ValueError('Incomplete publication overlay')
 second=load(staged/'data/vkol-m-ii-153/manifest.json')
 if not second['publication_ready'] or second['document']['id']!='vkol-m-ii-153':raise ValueError('Invalid new document')
 for relative,expected in report['base_files_sha256'].items():
  if sha(PUBLIC/relative)!=expected:raise ValueError('Reviewed frontend baseline changed: '+relative)
 old=pilot(PUBLIC/'pilot-data.js');new=pilot(staged/'pilot-data.js')
 if old['pages']!=new['pages'] or old['counts']!=new['counts']:raise ValueError('Legacy page entries changed')
 before=load(PUBLIC/'document.json');after=load(staged/'document.json')
 for key in ('id','uri','reader','counts'):
  if before[key]!=after[key]:raise ValueError('Legacy identity/count changed: '+key)
 ns={'t':'http://www.tei-c.org/ns/1.0'}
 parser=etree.XMLParser(resolve_entities=False,no_network=True)
 oldtei=etree.parse(str(PUBLIC/'tei/vkol-m-ii-220.xml'),parser)
 newtei=etree.parse(str(staged/'tei/vkol-m-ii-220.xml'),parser)
 if etree.tostring(oldtei.find('t:text',ns),method='c14n')!=etree.tostring(newtei.find('t:text',ns),method='c14n'):raise ValueError('Legacy TEI text changed')
 inventory=load(ROOT/'docs/web-source-manifest.json')
 checked=0
 for item in inventory['files']:
  path=item['path'];current=ROOT/path
  if current.stat().st_size!=item['bytes'] or sha(current)!=item['sha256']:
   if path.startswith(PROTECTED) or path in PROTECTED_FILES:raise ValueError('Legacy research baseline changed before import: '+path)
  candidate=staged/Path(path).relative_to('web/public')
  if candidate.is_file() and (path.startswith(PROTECTED) or path in PROTECTED_FILES):
   if path not in ALLOW and sha(candidate)!=item['sha256']:raise ValueError('Overlay would modify research layer: '+path)
   checked+=1
 files=[]
 for p in sorted(staged.rglob('*')):
  if not p.is_file():continue
  relative=p.relative_to(staged)
  if p.suffix.lower() in {'.png','.jpg','.jpeg','.webp','.tif','.tiff','.safetensors','.mlmodel','.env','.ico'}:raise ValueError('Media or credentials forbidden: '+str(relative))
  if '.credentials' in relative.parts or 'node_modules' in relative.parts or 'pagefind' in relative.parts:raise ValueError('Private/generated directory in overlay')
  if p.stat().st_size>=25*1024*1024:raise ValueError('Cloudflare Pages file limit exceeded')
  if p.suffix.lower()=='.svg' and relative.as_posix()!='favicon.svg':raise ValueError('Only authored favicon SVG allowed')
  files.append((p,PUBLIC/relative))
 for source,target in files:
  target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
 # Update only the three deliberately approved identification hashes. The usual
 # manifest updater still refuses every other research change before inventory.
 approved=[]
 for item in inventory['files']:
  if item['path'] in ALLOW:
   p=ROOT/item['path'];approved.append({'path':item['path'],'before_sha256':item['sha256'],'after_sha256':sha(p)})
   item['bytes']=p.stat().st_size;item['sha256']=sha(p)
 manifest=ROOT/'docs/web-source-manifest.json'
 manifest.write_text(json.dumps(inventory,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
 result={'status':'passed','copied_text_files':len(files),'checked_legacy_research_files':checked,'legacy_pages_unchanged':677,'legacy_counts_unchanged':True,'legacy_tei_text_c14n_unchanged':True,'approved_identification_changes':approved,'new_document':second['document']['id'],'new_counts':second['counts'],'media_copied':False}
 audit_report.parent.mkdir(parents=True,exist_ok=True);audit_report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n');print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--staged',type=Path,required=True);p.add_argument('--build-report',type=Path,required=True);p.add_argument('--audit-report',type=Path,required=True);a=p.parse_args();run(a.staged,a.build_report,a.audit_report)
