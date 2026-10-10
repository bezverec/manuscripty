from pathlib import Path
import json,time,runpy
H=Path(__file__).resolve().parents[1]
while True:
 try:
  m=json.loads((H/'manifest.json').read_text())
  if len(m['pages'])==100:break
 except (FileNotFoundError,json.JSONDecodeError):pass
 time.sleep(1)
runpy.run_path(str(H/'scripts/run_catmus.py'),run_name='__main__')
