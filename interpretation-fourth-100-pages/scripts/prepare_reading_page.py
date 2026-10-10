"""Prepare/re-register reading strips only for specified folios in the new batch."""
import argparse
from native_inputs import manifest_pages,prepare_reading
p=argparse.ArgumentParser();p.add_argument('folios',nargs='+');a=p.parse_args()
pages={s['folio']:s for s in manifest_pages()}
assert pages,'Raw manifest is not ready'
for f in a.folios:
 assert f in pages,'Folio not in this batch: '+f
 print('READING_TILES',f,prepare_reading(pages[f]),flush=True)
