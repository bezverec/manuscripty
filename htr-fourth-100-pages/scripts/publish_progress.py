from pathlib import Path
import json,time,runpy
H=Path(__file__).resolve().parents[1];last=-1
def rd(p):return json.loads(p.read_text(encoding='utf-8'))
while True:
 try:
  selected=rd(H/'selection.json')['pages'];m=rd(H/'medusa-batch.json');n=len(m['pages'])
  v=rd(H/'validation.json') if (H/'validation.json').exists() else {}
  if v.get('status')=='passed' or m.get('status') in ['success','failed']:break
  assert all(p['folio'] in {s['folio'] for s in selected} for p in m['pages'])
  if n>=1 and n!=last and (last<0 or n%5==0):runpy.run_path(str(H/'scripts/build_comparison.py'),run_name='__main__');last=n
 except (FileNotFoundError,json.JSONDecodeError):pass
 time.sleep(10)
