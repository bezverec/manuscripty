from pathlib import Path
import json,time,datetime,html
H=Path(__file__).resolve().parents[1]
def read(p):
 try:return json.loads(p.read_text(encoding='utf-8'))
 except (FileNotFoundError,json.JSONDecodeError):return None
def atomic(p,s):
 tmp=p.with_name(p.name+'.tmp');tmp.write_text(s,encoding='utf-8');tmp.replace(p)
while True:
 s=read(H/'selection.json') or {'pages':[]};cat=read(H/'catmus-batch.json') or {};med=read(H/'medusa-batch.json') or {};ocr=read(H/'ocr-proarc/manifest.json') or {};v=read(H/'validation.json') or {};prior=read(H/'prior-outputs-final-check.json') or {}
 planned=len(s['pages']);extent=(s['pages'][0]['folio']+'–'+s['pages'][-1]['folio']) if planned else 'výběr se připravuje'
 progress={'recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'planned_pages':planned,'prior_raw_pages':prior.get('prior_raw_pages'),'target_all_raw_pages':prior.get('prior_raw_pages',0)+planned,'selected_folios':[p['folio'] for p in s['pages']],'catmus_status':cat.get('status','waiting'),'catmus_completed_pages':len(cat.get('pages',[])),'medusa_status':med.get('status','waiting'),'medusa_completed_pages':len(med.get('pages',[])),'ocr_status':ocr.get('status','waiting'),'ocr_completed_pages':len(ocr.get('pages',[])),'validation_status':v.get('status','pending'),'paid_api_calls':0}
 atomic(H/'progress.json',json.dumps(progress,indent=2)+'\n')
 if v.get('status')=='passed':break
 if not (H/'summary.json').exists():
  cards=[]
  for p in s['pages']:
   f=p['folio'];out=H/'pages'/f;cr=read(out/'catmus-run.json') or {};mr=read(out/'medusa-run.json') or {}
   link='pages/'+f+'/comparison.html' if (out/'comparison.html').exists() else ('pages/'+f+'/overview.jpg' if (out/'overview.jpg').exists() else '')
   label='<a href="'+html.escape(link)+'">'+html.escape(f)+'</a>' if link else html.escape(f)
   cells=[label,html.escape(str(cr.get('segments',''))),html.escape(str(cr.get('status','čeká'))),html.escape(str(mr.get('status','čeká'))),html.escape(str(mr.get('completed_segments','')))]
   cards.append('<tr>'+''.join('<td>'+x+'</td>' for x in cells)+'</tr>')
  links=['<a href="../pilot-index.html">Starší výsledky</a>','<a href="progress.json">Průběžná data</a>','<a href="selection.json">Výběr stran</a>']
  if (H/'README.md').exists():links.append('<a href="README.md">Metodika</a>')
  body=f'<!doctype html><html lang="cs"><meta charset="utf-8"><meta http-equiv="refresh" content="30"><title>HTR {planned} stran · průběh</title><style>body{{font:18px system-ui;margin:2em;background:#f5f2e9}}td,th{{padding:.4em;border:1px solid #ccc}}table{{border-collapse:collapse}}</style><h1>HTR nové dávky — průběh</h1><p>{planned} nových skenů {html.escape(extent)}. Lokální CATMuS a Medusa, bez placeného API. Surový HTR bez odborné korektury.</p><p>CATMuS {progress["catmus_completed_pages"]}/{planned} · Medusa {progress["medusa_completed_pages"]}/{planned} · TXT/ALTO {progress["ocr_completed_pages"]}/{planned}</p><p>'+ ' · '.join(links)+'<table><tr><th>Folio</th><th>Segmentů CAT</th><th>CATMuS</th><th>Medusa</th><th>Hotových segmentů MED</th></tr>'+''.join(cards)+'</table></html>'
  atomic(H/'index.html',body)
 if any(z.get('status')=='failed' for z in [cat,med,ocr]):print(json.dumps(progress),flush=True);break
 time.sleep(10)
print(json.dumps(progress),flush=True)
