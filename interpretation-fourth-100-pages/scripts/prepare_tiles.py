"""Prepare native selected-zone reading strips from the sole raw manifest.
Run once for currently ready pages, or --watch to wait for the complete prepared manifest.
No reconstruction or image-inspection claims are generated.
"""
import argparse,time,json
from native_inputs import manifest_pages,ready,prepare_reading,TARGET
p=argparse.ArgumentParser();p.add_argument('folios',nargs='*');p.add_argument('--watch',action='store_true');p.add_argument('--poll-seconds',type=float,default=30)
a=p.parse_args();assert a.poll_seconds>0
assert len(a.folios)==len(set(a.folios)),'Duplicate requested folios'
reported=set()
while True:
 try:pages=manifest_pages()
 except json.JSONDecodeError:
  if not a.watch:raise
  pages=[] # The raw producer may be replacing its live manifest.
 if len(pages)==TARGET and a.folios:
  unknown=set(a.folios)-{s['folio'] for s in pages}
  assert not unknown,'Folios not in this batch: '+str(sorted(unknown))
 selected=[s for s in pages if not a.folios or s['folio'] in a.folios]
 for s in selected:
  f=s['folio']
  if f in reported or not ready(s):continue
  count=prepare_reading(s);reported.add(f);print('READING_TILES',f,count,flush=True)
 expected=len(a.folios) if a.folios else TARGET
 if len(reported)==expected:print('ALL_NATIVE_INPUTS_PREPARED',len(reported),flush=True);break
 if not a.watch:
  print('PREPARED_READY_PAGES',len(reported),'EXPECTED',expected,flush=True);break
 time.sleep(a.poll_seconds)
