from pathlib import Path
import ast,json
H=Path(__file__).resolve().parents[1];files=sorted((H/'scripts').glob('*.py'))+sorted((H/'ocr-proarc/scripts').glob('*.py'))
for p in files:ast.parse(p.read_text(encoding='utf-8'),filename=str(p))
print(json.dumps({'syntax_valid_scripts':len(files)}),flush=True)
