/** Verify registered page JSON and selected shared assets; redirects are checked separately. */
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath, pathToFileURL} from 'node:url';

const here=path.dirname(fileURLToPath(import.meta.url));
const digest=b=>crypto.createHash('sha256').update(b).digest('hex');
export async function publicationPlan(root=path.join(here,'public'),registryFile=path.join(here,'manuscripts.json')) {
  const registry=JSON.parse(await fs.readFile(registryFile,'utf8'));
  const redirects=(await fs.readFile(path.join(root,'_redirects'),'utf8')).split(/\r?\n/)
    .filter(line=>line.trim()&&!line.trim().startsWith('#')).map(line=>{
      const [from,to,status]=line.trim().split(/\s+/);
      if(!from?.startsWith('/')||!to?.startsWith('/')||status!=='301')throw Error('Unsupported redirect: '+line);
      return {from,to,status:301};
    });
  const redirected=new Set(redirects.map(r=>r.from));
  const files=new Set(['index.html','pilot-data.js','document.json','rukopis.html','rukopis.js',
    'document-loader.js','coordinate-core.mjs','theme.js','theme.css','styles.css','sitemap.xml']);
  const documents=[];
  for(const item of registry.manuscripts){
    const source=await fs.readFile(path.join(root,item.manifest),'utf8');
    const manifest=JSON.parse(item.manifest.endsWith('.js')?source.slice(source.indexOf('=')+1).trim().replace(/;$/,''):source);
    if(manifest.document.id!==item.id||!manifest.pages.length)throw Error('Invalid registered manifest: '+item.id);
    if(!item.manifest.endsWith('.js')&&!manifest.publication_ready)throw Error('Incomplete registered publication: '+item.id);
    files.add(item.manifest);files.add('tei/'+item.id+'.xml');files.add('rukopisy/'+item.id+'.html');
    files.add(item.id==='vkol-m-ii-220'?'summary.json':'data/'+item.id+'/summary.json');
    for(const page of manifest.pages)files.add(page.data.replace(/^\//,''));
    documents.push({id:item.id,pages:manifest.pages.length});
  }
  const entries=[];
  for(const file of [...files].sort()){
    const resolved=path.resolve(root,file);
    if(!resolved.startsWith(path.resolve(root)+path.sep))throw Error('Public path escapes root: '+file);
    const urlPath=file==='index.html'?'/':'/'+file.replace(/\.html$/,'');
    if(redirected.has(urlPath)||redirected.has('/'+file))throw Error('Redirect must not be byte-compared: '+file);
    entries.push({path:file,url_path:urlPath});
  }
  return {documents,files:entries,redirects};
}
export async function verifyRedirect(rule,origin,fetcher=fetch){
  const response=await fetcher(new URL(rule.from,origin),{redirect:'manual',signal:AbortSignal.timeout(45000)});
  const actual=new URL(response.headers.get('location')||rule.from,origin).href;
  const expected=new URL(rule.to,origin).href;
  if(response.status!==rule.status||actual!==expected)throw Error('Redirect mismatch: '+rule.from+' HTTP '+response.status);
  return {path:rule.from,status:response.status,location:actual};
}
async function main(){
  const args=process.argv.slice(2),planOnly=args.includes('--plan');
  const destination=args.find(x=>x!=='--plan')||path.resolve(here,'../docs/validation/publication-http-validation.json');
  const plan=await publicationPlan();
  if(planOnly){console.log(JSON.stringify(plan,null,2));return;}
  const origin='https://rukopisy.digitalizaty.cz',results=[],redirects=[];let cursor=0;
  await Promise.all(Array.from({length:12},async()=>{
    while(cursor<plan.files.length){
      const item=plan.files[cursor++];
      const response=await fetch(new URL(item.url_path,origin),{redirect:'manual',signal:AbortSignal.timeout(45000)});
      const actual=Buffer.from(await response.arrayBuffer()),expected=await fs.readFile(path.join(here,'public',item.path));
      if(response.status!==200||digest(actual)!==digest(expected))throw Error('Published snapshot mismatch: '+item.path+' HTTP '+response.status);
      results.push({path:item.path,status:response.status,sha256:digest(actual)});
    }
  }));
  for(const rule of plan.redirects)redirects.push(await verifyRedirect(rule,origin));
  const missing=await fetch(origin+'/missing-publication-proof-20261021',{redirect:'manual',signal:AbortSignal.timeout(45000)});
  if(missing.status!==404)throw Error('Missing URL must return 404');
  const report={status:'passed',origin,checked:new Date().toISOString(),documents:plan.documents,
    text_files_sha256_verified:results.length,not_found_status:missing.status,redirects,
    results:results.sort((a,b)=>a.path.localeCompare(b.path)),
    scope:'All registered page JSON, manifests, document TEI, overviews and selected shared text assets. Legacy redirect responses checked without following. Images, complete raw exports and visual rendering have separate audits.'};
  await fs.writeFile(destination,JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify({...report,results:undefined}));
}
if(process.argv[1]&&import.meta.url===pathToFileURL(path.resolve(process.argv[1])).href)await main();
