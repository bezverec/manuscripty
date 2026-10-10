from pathlib import Path
import json,time,runpy,datetime
H=Path(__file__).resolve().parents[1]
def rd(p):return json.loads(p.read_text(encoding='utf-8'))
while True:
 try:
  selected=[p['folio'] for p in rd(H/'selection.json')['pages']]
  cat=rd(H/'catmus-batch.json');med=rd(H/'medusa-batch.json');ocr=rd(H/'ocr-proarc/manifest.json');ov=rd(H/'ocr-proarc/validation.json');zp=rd(H/'ocr-proarc/package-check.json')
  for name,data in [('CATMuS',cat),('Medusa',med),('OCR',ocr)]:
   if data.get('status')=='failed':raise RuntimeError(name+' failed: '+data.get('error',''))
  if all(x.get('status')=='success' and [p['folio'] for p in x['pages']]==selected for x in [cat,med,ocr]) and ov.get('all_checks_passed') and [p['folio'] for p in ov['pages']]==selected and zp.get('zip_crc_and_file_hashes_valid'):break
 except (FileNotFoundError,json.JSONDecodeError):pass
 time.sleep(5)
(H/'validation.json').write_text(json.dumps({'status':'running','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'expert_reference':False})+'\n',encoding='utf-8')
for name in ['build_comparison.py','build_report.py']:runpy.run_path(str(H/'scripts'/name),run_name='__main__')
J=H.parent/'interpretation-fourth-100-pages'
while not (J/'index.html').is_file():time.sleep(10)
runpy.run_path(str(H/'scripts/validate_outputs.py'),run_name='__main__')
print('FINALIZATION_COMPLETE',flush=True)
