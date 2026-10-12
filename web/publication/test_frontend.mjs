// Portable, read-only frontend contract tests. No browser/network/deployment.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import vm from 'node:vm';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';

const required=['source','base-public','staged','build-report','report-dir'];
const options={};
for(let i=2;i<process.argv.length;i+=2){
  const name=process.argv[i]?.replace(/^--/,'');
  assert.ok(required.includes(name)&&process.argv[i+1]&&!process.argv[i+1].startsWith('--'),'Use explicit --source --base-public --staged --build-report --report-dir paths');
  assert.ok(!options[name],'Duplicate option: '+name);
  options[name]=path.resolve(process.argv[i+1]);
}
for(const name of required)assert.ok(options[name],'Missing --'+name);
const {source,staged}=options;
const base=options['base-public'], reportDir=options['report-dir'];
const inside=(child,root)=>{const relative=path.relative(root,child);return relative===''||(!relative.startsWith('..'+path.sep)&&relative!=='..'&&!path.isAbsolute(relative));};
for(const root of [source,staged,base])assert.ok(!inside(reportDir,root)&&!inside(root,reportDir),'Report root overlaps input');
const resolveFile=async name=>{
  for(const root of [staged,base]){
    const file=path.resolve(root,name);assert.ok(inside(file,root),'Path escapes declared root');
    try{if((await fs.stat(file)).isFile())return file;}catch(error){if(error.code!=='ENOENT')throw error;}
  }
  throw Error('Missing overlay/base asset: '+name);
};
const read=async name=>fs.readFile(await resolveFile(name),'utf8');
const tests=[];
async function test(name,fn){await fn();tests.push({name,status:'passed'});}
const manifest=JSON.parse(await read('data/vkol-m-ii-153/manifest.json'));
const sourceManifest=JSON.parse(await fs.readFile(path.join(source,'manifest.json'),'utf8'));
const build=JSON.parse(await fs.readFile(options['build-report'],'utf8'));
const defaultManifestCode=await read('pilot-data.js');
const loader=await read('document-loader.js');

async function route(href,{httpOK=true,response=manifest}={}){
  const log={fetch:[],scripts:[]};
  const context={URL,location:{href},window:{},document:{createElement:()=>({}),head:{append(script){log.scripts.push(script.src);vm.runInContext(defaultManifestCode,context);script.onload();}}},fetch:async url=>{log.fetch.push(url);return {ok:httpOK,json:async()=>response};}};
  vm.createContext(context);vm.runInContext(loader,context);
  await context.window.MANUSCRIPT_READY;
  return {log,data:context.window.PILOT_DATA};
}

await test('Explicit build provenance matches source/output and baseline SHA inventory',async()=>{
  assert.equal(build.status,'passed');assert.equal(path.resolve(build.source),source);assert.equal(path.resolve(build.output),staged);
  assert.ok(Object.keys(build.base_files_sha256).length>0);
  for(const [name,expected] of Object.entries(build.base_files_sha256)){
    const file=path.resolve(base,name);assert.ok(inside(file,base));
    assert.equal(createHash('sha256').update(await fs.readFile(file)).digest('hex'),expected,'Baseline changed: '+name);
  }
  assert.deepEqual(manifest.pages.map(p=>p.folio),sourceManifest.pages.map(p=>p.folio));
  assert.equal(manifest.publication_ready,build.publication_ready);
});
await test('Legacy reader URL retains 677 page entries, counts and original routing',async()=>{
  const result=await route('https://rukopisy.digitalizaty.cz/rukopis?vrstva=vyklad#20v-f20v_l001');
  assert.equal(result.data.document.id,'vkol-m-ii-220');assert.equal(result.data.pages.length,677);
  assert.deepEqual(result.log.fetch,[]);assert.equal(result.log.scripts.length,1);assert.match(result.log.scripts[0],/^pilot-data\.js\?v=/);
  const oldContext={window:{}};vm.runInNewContext(await fs.readFile(path.join(base,'pilot-data.js'),'utf8'),oldContext);
  assert.equal(JSON.stringify(result.data.pages),JSON.stringify(oldContext.window.PILOT_DATA.pages));
  assert.equal(JSON.stringify(result.data.counts),JSON.stringify(oldContext.window.PILOT_DATA.counts));
  assert.equal(result.data.document.reader,'https://rukopisy.digitalizaty.cz/rukopis');
});
await test('Explicit second manuscript selects only the namespaced manifest',async()=>{
  const result=await route('https://rukopisy.digitalizaty.cz/rukopis?doc=vkol-m-ii-153&vrstva=radky#5r-f5r_l001');
  assert.equal(result.data.document.id,'vkol-m-ii-153');assert.equal(result.data.pages.length,manifest.pages.length);
  assert.equal(result.log.scripts.length,0);assert.equal(result.log.fetch.length,1);assert.match(result.log.fetch[0],/^\/data\/vkol-m-ii-153\/manifest\.json\?v=/);
});
await test('Unknown document IDs and failed or mismatched manifests fail closed',async()=>{
  await assert.rejects(route('https://rukopisy.digitalizaty.cz/rukopis?doc=https://evil.invalid/file.json'),/Neznámý/);
  await assert.rejects(route('https://rukopisy.digitalizaty.cz/rukopis?doc=..%2Fdocument'),/Neznámý/);
  const href='https://rukopisy.digitalizaty.cz/rukopis?doc=vkol-m-ii-153';
  await assert.rejects(route(href,{httpOK:false}),/Manifest/);
  await assert.rejects(route(href,{response:{document:{id:'vkol-m-ii-220'},pages:manifest.pages}}),/manifest/i);
  await assert.rejects(route(href,{response:{document:{id:'vkol-m-ii-153'},pages:[]}}),/manifest/i);
});
const proposal=await import(pathToFileURL(await resolveFile('proposal-core.mjs')));
const segmentation=await import(pathToFileURL(await resolveFile('segmentation-core.mjs')));
const page=JSON.parse(await read(manifest.pages.find(p=>p.folio==='5r').data.slice(1)));
const line=page.lines[0];
const context={document_id:page.document_id,document_uri:page.document_uri,manuscript:'M II 153',folio:page.folio,line_id:line.id,source_segment_ids:line.source_segment_ids,bbox:line.bbox,source_sha256:page.source_sha256,models:page.models,raw_htr:line.raw_htr,source_url:manifest.document.reader+'#'+page.folio+'-'+line.id,crop_url:line.image};
await test('HTR proposals preserve Unicode, source identity, raw output and geometry',()=>{
  const p=proposal.makeProposal(context,'catmus','Navržená změna ⁊ ꝰ','Podle obrazu','test','2026-10-12T00:00:00Z');
  assert.equal(p.document_id,'vkol-m-ii-153');assert.equal(p.manuscript,'M II 153');assert.equal(p.original_htr,line.raw_htr.catmus);assert.equal(p.proposed_htr,'Navržená změna ⁊ ꝰ');assert.equal(p.source_url,context.source_url);assert.equal(p.expert_review,false);
  const url=new URL(proposal.githubProposalUrl(p));assert.match(url.searchParams.get('title'),/^\[HTR\] M II 153/);assert.equal(url.searchParams.get('template'),'htr-oprava.yml');assert.equal(url.searchParams.get('source_url'),context.source_url);
  p.bbox[0]++;assert.deepEqual(context.bbox,line.bbox);
});
await test('Legacy HTR callers keep M II 220 identity and reject unchanged or unknown models',()=>{
  const old={...context};delete old.document_id;delete old.document_uri;delete old.manuscript;
  const p=proposal.makeProposal(old,'catmus','Jiné čtení','Podle obrazu','test','utc');assert.equal(p.manuscript,'M II 220');assert.equal(p.document_id,'vkol-m-ii-220');
  assert.throws(()=>proposal.makeProposal(context,'catmus',line.raw_htr.catmus,'Podle obrazu','test','utc'),/shodný/);
  assert.throws(()=>proposal.makeProposal(context,'unknown','Jiné','Podle obrazu','test','utc'),/dostupný/);
});
await test('Segmentation proposals keep namespaced identity and original regions immutable',()=>{
  const ctx={...context,width:page.width,height:page.height,source_original:page.source_original,segments:[{id:line.id,source_segment_ids:line.source_segment_ids,bbox:line.bbox}]};
  const bbox=[...line.bbox];bbox[1]++;
  const p=segmentation.makeSegmentationProposal(ctx,'resize',[line.id],[bbox],'Podle obrazu','test','utc');
  assert.equal(p.document_id,'vkol-m-ii-153');assert.equal(p.manuscript,'M II 153');assert.deepEqual(p.original_segments[0].bbox,line.bbox);assert.deepEqual(p.proposed_regions[0].bbox,bbox);
  assert.match(new URL(segmentation.segmentationGithubUrl(p)).searchParams.get('title'),/^\[Segmentace\] M II 153/);
  assert.throws(()=>segmentation.makeSegmentationProposal(ctx,'resize',[line.id],[line.bbox],'Podle obrazu','test','utc'),/shodné/);
  p.proposed_regions[0].bbox[0]++;assert.deepEqual(ctx.segments[0].bbox,line.bbox);
});
await test('Reader resolves document identity, canonical reader URL and mixed-language interpretation',async()=>{
  const code=await read('rukopis.js');
  assert.ok((code.match(/new URL\(DATA\.document\.reader\)/g)||[]).length>=2);
  assert.ok(code.includes('manuscript:page().manuscript||DATA.document.shelfmark||DATA.title'));
  assert.ok(!code.includes('Všech 664'));assert.match(code,/DATA\.document\.uri/);assert.match(code,/window\.MANUSCRIPT_READY\.then/);
  assert.ok(code.includes('Rekonstrukce (jazyk předlohy)'));assert.ok(code.includes('p.language || page().language'));
});
await test('Record/homepage navigation identifies both manuscripts and institutional custody',async()=>{
  for(const id of ['vkol-m-ii-220','vkol-m-ii-153']){
    const record=await read('rukopisy/'+id+'.html');assert.ok(record.includes('https://www.vkol.cz/'));assert.ok(record.includes('data-document="'+id+'"'));assert.ok(record.includes('data-folio-search'));
    const home=await read('index.html');assert.ok(home.includes('/rukopisy/'+id));
  }
  const record=await read('rukopisy/vkol-m-ii-153.html');assert.ok(record.includes('https://manuscripta.cz/manuscript/VKOL_M_II_153/'));
  assert.ok(!(await read('index.html')).includes('href="5r.html"'));
});
await test('Panel controls, correction dialogs and reviewed shared assets survive the overlay',async()=>{
  const html=await read('rukopis.html');
  for(const id of ['text-panel','toggle-thumbs','toggle-text-panel','panel-resizer','document-permalink','correction-dialog','segmentation-dialog','manuscript-toc'])assert.ok(html.includes('id="'+id+'"'),id);
  for(const file of ['styles.css','folio.css','search.js','proposal-core.mjs','segmentation-core.mjs','header-actions.js','feature-config.js','iiif-link.js'])assert.ok(await resolveFile(file));
});
await fs.mkdir(reportDir,{recursive:true});
await fs.writeFile(path.join(reportDir,'frontend-test-report.json'),JSON.stringify({status:'passed',tests,source_pages:sourceManifest.pages.length,legacy_pages:677,browser_visual_test:false,scope:'Frontend contracts in Node VM; no browser rendering or network operations'},null,2)+'\n');
console.log(JSON.stringify({status:'passed',tests:tests.length}));
