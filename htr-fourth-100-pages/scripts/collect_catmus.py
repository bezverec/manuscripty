from pathlib import Path
import json,time,datetime
H=Path(__file__).resolve().parents[1]
def rd(p):
 try:return json.loads(p.read_text())
 except (FileNotFoundError,json.JSONDecodeError):return None
while True:
 m=rd(H/'manifest.json');parts=[rd(H/f'catmus-batch-part{i}.json') for i in [1,2]];pages=[]
 for p in m['pages']:
  r=rd(H/'pages'/p['folio']/'catmus-run.json')
  if r and r['status']=='success':pages.append(r)
 status='success' if len(pages)==100 and all(x and x['status']=='success' for x in parts) else 'failed' if any(x and x['status']=='failed' for x in parts) else 'running'
 result={'status':status,'parallel_cpu_workers':2,'threads_per_worker':4,'engine':rd(H/'catmus-engine-part1.json') or rd(H/'catmus-engine-part2.json'),'pages':pages,'collected_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 if status=='failed':result['error']='; '.join(x.get('error','') for x in parts if x and x['status']=='failed')
 tmp=H/'catmus-batch.json.tmp';tmp.write_text(json.dumps(result,ensure_ascii=False,indent=2));tmp.replace(H/'catmus-batch.json')
 if status!='running':print(json.dumps({'status':status,'completed':len(pages),'error':result.get('error')}),flush=True);break
 time.sleep(2)
