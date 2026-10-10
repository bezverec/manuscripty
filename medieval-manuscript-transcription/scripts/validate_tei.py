#!/usr/bin/env python3
"""Validate supplied TEI files offline against bundled TEI P5 4.12.0 Relax NG."""
from pathlib import Path
import argparse, importlib.util, json
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('tei_export',HERE/'export.py')
core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('files',type=Path,nargs='+')
    parser.add_argument('--report',type=Path)
    args=parser.parse_args()
    results=[]
    for path in args.files:
        try:result={'file':str(path),'valid':True,**core.validate_tei_file(path)}
        except Exception as error:result={'file':str(path),'valid':False,'error':str(error)}
        results.append(result)
        print(str(path)+': '+('VALID (Relax NG 4.12.0, offline)' if result['valid'] else result['error']))
    if args.report:args.report.write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return 0 if all(r['valid'] for r in results) else 1
if __name__=='__main__':raise SystemExit(main())
