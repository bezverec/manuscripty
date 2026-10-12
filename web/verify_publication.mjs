/** Verify the deployed text snapshot against local bytes; no write credentials. */
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
const here=path.dirname(fileURLToPath(import.meta.url)),root=path.join(here,'public');
const origin='https://rukopisy.digitalizaty.cz';
const digest=b=>crypto.createHash('sha256').update(b).digest('hex');
const data=JSON.parse(await fs.readFile(path.join(root,'data/vkol-m-ii-153/manifest.json'),'utf8'));
if(!data.publication_ready||data.pages.length!==197)throw Error('Incomplete local publication');
const files=['index.html','pilot-data.js','document.json','rukopis.html','rukopis.js','document-loader.js',
 'summary.html','tei/vkol-m-ii-220.xml','tei/vkol-m-ii-153.xml',
 'rukopisy/vkol-m-ii-220.html','rukopisy/vkol-m-ii-153.html',
 'rukopisy/vkol-m-ii-153/shrnuti.html','data/vkol-m-ii-153/summary.json',
 'data/vkol-m-ii-153/manifest.json','data/20v/page.json','sitemap.xml',
 ...data.pages.map(p=>p.data.replace(/^\//,''))];
const results=[];let cursor=0;
await Promise.all(Array.from({length:12},async()=>{
 while(cursor<files.length){
  const relative=files[cursor++],url=origin+'/'+relative.replace(/\.html$/,'');
  const response=await fetch(url,{signal:AbortSignal.timeout(45000),headers:{'Cache-Control':'no-cache'}});
  const actual=Buffer.from(await response.arrayBuffer()),expected=await fs.readFile(path.join(root,relative));
  if(response.status!==200||digest(actual)!==digest(expected))throw Error('Published snapshot mismatch: '+relative+' HTTP '+response.status);
  results.push({path:relative,status:response.status,sha256:digest(actual)});
 }
}));
const missing=await fetch(origin+'/missing-publication-proof-20261012',{signal:AbortSignal.timeout(45000)});
if(missing.status!==404)throw Error('Missing URL must return404');
const report={status:'passed',origin,checked:new Date().toISOString(),new_pages:197,
 text_files_sha256_verified:results.length,not_found_status:missing.status,results:results.sort((a,b)=>a.path.localeCompare(b.path)),
 scope:'Live HTTP status and exact text bytes; image delivery has a separate R2 audit and browser proof.'};
const destination=process.argv[2]||path.resolve(here,'../docs/validation/two-manuscript-public-verification.json');
await fs.writeFile(destination,JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({...report,results:undefined}));
