from pathlib import Path
import json,time,runpy
H=Path(__file__).resolve().parents[1]
while True:
 try:
  s=json.loads((H/'manifest.json').read_text())
  if len(s['pages'])==100:break
 except (FileNotFoundError,json.JSONDecodeError):pass
 time.sleep(1)
for name in ['export_proarc_ocr.py','validate_export.py','package_export.py']:runpy.run_path(str(H/'ocr-proarc/scripts'/name),run_name='__main__')
