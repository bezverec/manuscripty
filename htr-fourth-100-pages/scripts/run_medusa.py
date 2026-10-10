"""Resumable local Medusa batch; sixteen independent line crops per GPU call."""
from pathlib import Path
import json,time,datetime,hashlib,os,importlib.metadata,traceback
os.environ['HF_DEACTIVATE_ASYNC_LOAD']='1'
import torch
from PIL import Image
from transformers import AutoProcessor,AutoModelForImageTextToText,BitsAndBytesConfig
from transformers.utils.logging import disable_progress_bar
disable_progress_bar()
H=Path(__file__).resolve().parents[1];MD=Path('/opt/medusa-model');BATCH_SIZE=16
REV='2e891246c709976eb8fd90274932d1f08debcb15'
PROMPT='Transcribe the handwritten text in this line image.\nOutput ONLY the transcription.'
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def save(p,x):
 tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');tmp.replace(p)
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
while True:
 try:
  manifest=json.loads((H/'manifest.json').read_text())
  if len(manifest['pages'])==100:break
 except (FileNotFoundError,json.JSONDecodeError):pass
 time.sleep(1)
torch.set_num_threads(4);torch.manual_seed(0)
modelsha=sha(MD/'model.safetensors');assert modelsha=='930f97e19686a94e2a9967014e437162153bb884121aa3923a1e25422d4e708b'
batch={'status':'loading','started_utc':utc(),'model_id':'ENC-PSL/Medusa0.2Line-4B','revision':REV,'model_sha256':modelsha,'precision':'bitsandbytes NF4 4-bit weights, double quantization, BF16 compute','prompt':PROMPT,'enable_thinking':False,'batch_size':BATCH_SIZE,'max_new_tokens':128,'do_sample':False,'min_pixels':65536,'max_pixels':401408,'gpu':torch.cuda.get_device_name(),'versions':{v:importlib.metadata.version(v) for v in ['torch','transformers','bitsandbytes','accelerate','huggingface-hub','Pillow']},'paid_api_calls':0,'expert_reference':False,'cer':None,'wer':None,'pages':[],'scheduling':'Round-robin parent,b,c,a author assignments; within group first ready folio in assignment order; skip unavailable groups. Independent crop prompts; presentation sorted by manuscript order.','waiting_for_catmus_seconds':0,'prior_sessions_provenance':'medusa-session-history.json','current_session_recognition_seconds':0,'timing_note':'Up to sixteen independent crops in a padded GPU batch. Batched tensor arithmetic may differ numerically from previous batch-size-one runs. Shared generation time recorded, not independent latency.'}
save(H/'medusa-batch.json',batch);t0=time.perf_counter()
try:
 proc=AutoProcessor.from_pretrained(MD,local_files_only=True,trust_remote_code=False,min_pixels=65536,max_pixels=401408)
 proc.tokenizer.padding_side='left'
 quant=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_quant_type='nf4',bnb_4bit_use_double_quant=True,bnb_4bit_compute_dtype=torch.bfloat16)
 model=AutoModelForImageTextToText.from_pretrained(MD,local_files_only=True,trust_remote_code=False,quantization_config=quant,device_map={'':'cuda:0'},dtype=torch.bfloat16,attn_implementation='sdpa').eval()
 torch.cuda.synchronize();batch['model_load_seconds']=time.perf_counter()-t0;batch['parameter_devices']=sorted(set(str(p.device) for p in model.parameters()));assert batch['parameter_devices']==['cuda:0']
 me=model.generation_config.eos_token_id;stop=sorted(set(([me] if isinstance(me,int) else (me or []))+[proc.tokenizer.eos_token_id]));batch['eos_token_ids']=stop;batch['status']='running';save(H/'medusa-batch.json',batch)
 print(json.dumps({'loaded_seconds':batch['model_load_seconds'],'gpu_batch_size':BATCH_SIZE}),flush=True)
 author_root=H.parent/'interpretation-fourth-100-pages'/'assignments'
 author_groups=[json.loads((author_root/(name+'.json')).read_text())['folios'] for name in ['parent','b','c','a']]
 assigned=[f for group in author_groups for f in group]
 assert len(assigned)==100 and set(assigned)==set(p['folio'] for p in manifest['pages']) and len(set(assigned))==100,'Author scheduler coverage mismatch'
 def ready_pages():
  todo={p['folio']:p for p in manifest['pages']};cursor=0
  while todo:
   selected=None
   for offset in range(len(author_groups)):
    gi=(cursor+offset)%len(author_groups)
    for folio in author_groups[gi]:
     if folio not in todo:continue
     try:ready=json.loads((H/'pages'/folio/'catmus-run.json').read_text())
     except (FileNotFoundError,json.JSONDecodeError):continue
     if ready['status']=='success':selected=folio;cursor=(gi+1)%len(author_groups);break
    if selected is not None:break
   if selected is not None:yield todo.pop(selected)
   else:
    t_wait=time.perf_counter();time.sleep(1);batch['waiting_for_catmus_seconds']+=time.perf_counter()-t_wait
 for page in ready_pages():
  folio=page['folio'];out=H/'pages'/folio;wait=time.perf_counter()
  while True:
   try:
    catrun=json.loads((out/'catmus-run.json').read_text())
    if catrun['status']=='success':break
    if catrun['status']=='failed':raise RuntimeError('CATMuS failed '+folio)
   except (FileNotFoundError,json.JSONDecodeError):pass
   time.sleep(1)
  batch['waiting_for_catmus_seconds']+=time.perf_counter()-wait
  cat=json.loads((out/'catmus.candidates.json').read_text());lines=[];rp=out/'medusa-run.json';jp=out/'medusa.results.jsonl'
  if jp.exists():
   data=jp.read_bytes();offset=0
   for rawline in data.splitlines(keepends=True):
    try:row=json.loads(rawline)
    except json.JSONDecodeError:
     assert offset+len(rawline)==len(data),'Nonterminal damaged checkpoint';(out/('interrupted-jsonl-tail-'+str(time.time_ns())+'.bin')).write_bytes(rawline);jp.write_bytes(data[:offset]);break
    expected=cat['lines'][len(lines)];assert row['id']==expected['id'] and row['image_sha256']==expected['image_sha256'] and row['bbox']==expected['bbox'];lines.append(row);offset+=len(rawline)
  if rp.exists():
   prior=json.loads(rp.read_text());assert prior['revision']==REV and prior['model_sha256']==modelsha and prior['image_sha256']==sha(out/'image.png') and prior['segmentation_sha256']==sha(out/'segmentation.json')
   if prior['status']=='success':
    assert len(lines)==len(cat['lines']);batch['pages'].append(prior);save(H/'medusa-batch.json',batch);print('RESUME_EXISTING '+folio,flush=True);continue
  run={'folio':folio,'status':'running','started_utc':utc(),'model_id':batch['model_id'],'revision':REV,'model_sha256':modelsha,'image_sha256':sha(out/'image.png'),'segmentation_sha256':sha(out/'segmentation.json'),'catmus_candidates_sha256':sha(out/'catmus.candidates.json'),'input':'Same original-coordinate lossless crops as CATMuS, RGB. Independent prompts, no prior transcription.','prompt':PROMPT,'precision':batch['precision'],'batch_size':BATCH_SIZE,'min_pixels':65536,'max_pixels':401408,'max_new_tokens':128,'eos_token_ids':stop,'postprocessing':'decode skip_special_tokens=True; no strip or Unicode normalization','expert_reference':False,'cer':None,'wer':None,'resumed_segments':len(lines),'rendered_non_thinking_prefix_verified':True}
  if not cat['lines']:jp.touch(exist_ok=True);run.update(blank_main_text=True,model_inference_performed=False,rendered_non_thinking_prefix_verified=None)
  save(rp,run);torch.cuda.reset_peak_memory_stats();startpage=time.perf_counter()
  for startidx in range(len(lines),len(cat['lines']),BATCH_SIZE):
   chunk=cat['lines'][startidx:startidx+BATCH_SIZE];messages=[];sizes=[];tline=time.perf_counter()
   for line in chunk:
    path=out/line['image'];assert sha(path)==line['image_sha256'];img=Image.open(path).convert('RGB');sizes.append(list(img.size));messages.append([{'role':'user','content':[{'type':'text','text':PROMPT},{'type':'image','image':img}]}])
   inp=proc.apply_chat_template(messages,tokenize=True,add_generation_prompt=True,return_dict=True,enable_thinking=False,return_tensors='pt',padding=True).to('cuda:0')
   for seq in inp['input_ids']:assert proc.tokenizer.decode(seq[-25:],skip_special_tokens=False).endswith('<think>\n\n</think>\n\n')
   torch.cuda.synchronize();tg=time.perf_counter()
   with torch.inference_mode():ids=model.generate(**inp,max_new_tokens=128,do_sample=False,eos_token_id=stop)
   torch.cuda.synchronize();gensec=time.perf_counter()-tg;batch['current_session_recognition_seconds']+=time.perf_counter()-tline
   for j,line in enumerate(chunk):
    generated=ids[j][inp['input_ids'].shape[1]:];eos=[i for i,v in enumerate(generated.tolist()) if v in stop]
    if eos:generated=generated[:eos[0]+1]
    row={k:line[k] for k in ['id','bbox','boundary','baseline','region_index','image','image_sha256','review_flags']}
    row.update(image_size=sizes[j],raw=proc.decode(generated,skip_special_tokens=True),decoded_with_special_tokens=proc.decode(generated,skip_special_tokens=False),input_tokens=int(inp['attention_mask'][j].sum()),padded_input_tokens=int(inp['input_ids'].shape[1]),output_tokens=len(generated),image_grid_thw=[inp['image_grid_thw'][j].tolist()],ended_with_eos=bool(eos),hit_token_limit=len(generated)>=128 and not eos,generation_seconds=gensec/len(chunk),generation_batch_seconds=gensec,generation_batch_size=len(chunk),generation_batch_ids=[v['id'] for v in chunk],total_line_seconds=(time.perf_counter()-tline)/len(chunk))
    with open(jp,'a',encoding='utf-8') as f:f.write(json.dumps(row,ensure_ascii=False)+'\n');f.flush();os.fsync(f.fileno())
    lines.append(row)
   save(out/'medusa.candidates.json',{'folio':folio,'model':batch['model_id'],'status':'raw_unreviewed','lines':lines});run['completed_segments']=len(lines);save(rp,run)
   print(json.dumps({'folio':folio,'progress':f'{len(lines)}/{len(cat["lines"])}','batch_seconds':round(gensec,3),'truncated_in_batch':sum(x['hit_token_limit'] for x in lines[-len(chunk):])}),flush=True)
   del inp,ids,generated
  run.update(status='success',recognition_seconds=sum(x['total_line_seconds'] for x in lines),this_session_page_seconds=time.perf_counter()-startpage,segments=len(lines),gpu_peak_allocated_bytes=torch.cuda.max_memory_allocated(),gpu_peak_reserved_bytes=torch.cuda.max_memory_reserved(),finished_utc=utc(),nonempty=sum(bool(x['raw'].strip()) for x in lines),truncated_lines=[x['id'] for x in lines if x['hit_token_limit']],total_input_tokens=sum(x['input_tokens'] for x in lines),total_output_tokens=sum(x['output_tokens'] for x in lines))
  save(out/'medusa.candidates.json',{'folio':folio,'model':batch['model_id'],'status':'raw_unreviewed','lines':lines});(out/'medusa.raw.txt').write_text('\n'.join(x['raw'] for x in lines)+'\n',encoding='utf-8');save(rp,run);batch['pages'].append(run);batch['pages'].sort(key=lambda p:(int(p['folio'][:-1]),p['folio'][-1]));save(H/'medusa-batch.json',batch);print(json.dumps({'done':folio,'segments':len(lines),'recognition_seconds':run['recognition_seconds'],'truncated':run['truncated_lines']}),flush=True)
 batch.update(status='success',finished_utc=utc(),total_seconds=time.perf_counter()-t0,new_recognition_seconds=batch['current_session_recognition_seconds'],checkpointed_recognition_seconds_all_sessions=sum(x['recognition_seconds'] for x in batch['pages']),total_seconds_scope='Current resumed session from model loading; prior wall time, durable tokens and unknown interrupted generation documented separately in medusa-session-history.json');save(H/'medusa-batch.json',batch);print('MEDUSA_BATCH_COMPLETE',flush=True)
except Exception as e:
 batch.update(status='failed',error=str(e),finished_utc=utc());save(H/'medusa-batch.json',batch);traceback.print_exc();raise
