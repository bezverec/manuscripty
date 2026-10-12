import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {makeProposal,githubProposalUrl} from './public/proposal-core.mjs';
import {makeSegmentationProposal} from './public/segmentation-core.mjs';
import {HTR_FIELDS,SEGMENTATION_FIELDS,openProposalNumbers,HTR_TEXT_FIELDS} from './public/issue-form-core.mjs';
import {parseIssue,validateProposal,collectProposals} from './scripts/proposals.mjs';
import validateIssue from './scripts/validate-issue.mjs';
const publicRoot=path.resolve('public'),page=JSON.parse(await fs.readFile('public/data/20v/page.json','utf8')),line=page.lines[1];
const context={...page,line_id:line.id,raw_htr:line.raw_htr,source_segment_ids:line.source_segment_ids,bbox:line.bbox,source_url:'https://example.com',crop_url:line.image};
const p=makeProposal(context,'medusa','Opravený návrh','Viditelný znak','id','2026-10-12T00:00:00Z');
const body=proposal=>Object.entries(proposal).map(([key,v])=>'### '+key+'\n\n'+(typeof v==='string'&&!HTR_TEXT_FIELDS.has(key)?v:JSON.stringify(v))+'\n').join('\n');
assert.deepEqual(parseIssue(body(p),'htr'),p);
assert.deepEqual(parseIssue('### proposal_json\n\n\x60\x60\x60json\n'+JSON.stringify(p)+'\n\x60\x60\x60','htr'),p);
assert.throws(()=>parseIssue('### schema\nx\n### schema\ny','htr'),/opakuje/);
assert.equal((await validateProposal(p,'htr',publicRoot)).document_id,page.document_id);
for(const patch of [{schema:'unknown'},{folio:'../20v'},{document_id:'../data'},{source_sha256:'0'.repeat(64)},{line_id:'unknown'},{source_segment_ids:['unknown']},{bbox:[0,0,1,1]},{model:'unknown'},{original_htr:'changed'},{expert_review:true}]){
 await assert.rejects(validateProposal({...p,...patch},'htr',publicRoot));
}
const segments=page.lines.slice(0,2).map(l=>({id:l.id,source_segment_ids:l.source_segment_ids,bbox:l.bbox}));
const s=makeSegmentationProposal({...page,segments},'merge',segments.map(l=>l.id),[[1,1,10,10]],'Obraz','id','utc');
await validateProposal(s,'segmentace',publicRoot);
await assert.rejects(validateProposal({...s,original_segments:[{...s.original_segments[0],id:'unknown'}]},'segmentace',publicRoot));
await assert.rejects(validateProposal({...s,proposed_regions:[{id:'proposal_region_1',order:2,bbox:[1,1,10,10]}]},'segmentace',publicRoot));
const add=makeSegmentationProposal({...page,segments},'add',[],[[1,1,10,10]],'Obraz','id','utc');
const issues=[{number:8,state:'open',labels:['htr-oprava'],body:body(p)},{number:12,state:'open',labels:[{name:'segmentace-oprava'}],body:body(s)},{number:15,state:'open',labels:['segmentace-oprava'],body:body(add)},{number:9,state:'closed',labels:['htr-oprava'],body:body(p)},{number:10,state:'open',labels:['htr-oprava'],body:body({...p,source_sha256:'0'.repeat(64)})},{number:11,state:'open',labels:['htr-oprava'],body:body(p),pull_request:{}}];
const index=await collectProposals(issues,publicRoot);
assert.equal(JSON.stringify(index),JSON.stringify(await collectProposals([...issues].reverse(),publicRoot)));
const spaced={...p,original_htr:'  '+p.original_htr+'\n',proposed_htr:' návrh \n'};assert.deepEqual(parseIssue(body(spaced),'htr'),spaced);
assert.deepEqual(index['20v'][line.id],[8,12]);assert.deepEqual(index['20v']['*'],[15]);
assert.deepEqual(openProposalNumbers(index,page.document_id,'20v',line.id),[8,12,15]);
assert.deepEqual(openProposalNumbers(index,'vkol-m-ii-153','20v',line.id),[]);
assert.deepEqual(openProposalNumbers({'20v':{[line.id]:[3]}},page.document_id,'20v',line.id),[3]);
assert.deepEqual(openProposalNumbers({documents:{[page.document_id]:{'20v':{[line.id]:['<script>',2,-1]}}}},page.document_id,'20v',line.id),[2]);
const temporary=await fs.mkdtemp(path.join(os.tmpdir(),'manuscripty-proposals-'));
try{
 const directory=path.join(temporary,'data','vkol-m-ii-153','20v');await fs.mkdir(directory,{recursive:true});
 await fs.writeFile(path.join(directory,'page.json'),JSON.stringify({...page,document_id:'vkol-m-ii-153'}));
 const next={...p,document_id:'vkol-m-ii-153',manuscript:'M II 153'};
 const multi=await collectProposals([{number:19,state:'open',labels:['htr-oprava'],body:body(next)}],temporary);
 assert.deepEqual(multi.documents['vkol-m-ii-153']['20v'][line.id],[19]);assert.equal(multi['20v'],undefined);
}finally{await fs.rm(temporary,{recursive:true,force:true});}
for(const [name,fields] of [['htr',HTR_FIELDS],['segmentace',SEGMENTATION_FIELDS]]){
 const yaml=await fs.readFile('../.github/ISSUE_TEMPLATE/'+name+'-oprava.yml','utf8');
 assert.deepEqual([...yaml.matchAll(/^    id: ([a-z0-9_]+)$/gm)].map(m=>m[1]),[...fields,'proposal_json']);
}
assert.equal(new URL(githubProposalUrl(p)).searchParams.has('labels'),false);
// Repeated edits update one bot comment rather than creating a stream.
const comments=[],labels=['htr-oprava'],api={rest:{issues:{get:async()=>({data:{...issues[0],body:body({...p,source_sha256:'0'.repeat(64)}),labels}}),listComments:'list',createComment:async args=>comments.push({id:1,user:{login:'github-actions[bot]'},body:args.body}),updateComment:async args=>{comments[0].body=args.body;},addLabels:async args=>labels.push(...args.labels),removeLabel:async args=>{labels.splice(labels.indexOf(args.name),1);}}},paginate:async()=>comments};
await validateIssue({github:api,context:{repo:{owner:'owner',repo:'repo'},payload:{issue:{number:8}}},core:{info(){}},publicRoot});
await validateIssue({github:api,context:{repo:{owner:'owner',repo:'repo'},payload:{issue:{number:8}}},core:{info(){}},publicRoot});
assert.equal(comments.length,1);assert.deepEqual(labels,['htr-oprava','needs-info']);
api.rest.issues.get=async()=>({data:{...issues[0],labels}});
await validateIssue({github:api,context:{repo:{owner:'owner',repo:'repo'},payload:{issue:{number:8}}},core:{info(){}},publicRoot});
assert.equal(comments.length,1);assert.deepEqual(labels,['htr-oprava']);
console.log('Proposal workflow validation passed: forms, exact identity, namespace isolation, safe issue parsing, index and idempotent feedback.');

// Test Git data API writes without network or shell execution.
const {default:updateProposals}=await import('./scripts/update-proposals.mjs');
const calls={blobs:[],trees:[],commits:[],refs:[],pulls:[],closed:[]};
let existingRef=false,existingPulls=[],openIssues=[issues[0]];
const mock={rest:{repos:{get:async()=>({data:{default_branch:'main'}})},issues:{listForRepo:'issues'},pulls:{
 list:async()=>({data:existingPulls}),create:async args=>{calls.pulls.push(args);existingPulls=[{number:101}];},update:async args=>calls.closed.push(args)
},git:{
 getRef:async args=>{if(args.ref==='heads/main')return {data:{object:{sha:'base'}}};if(!existingRef)throw Object.assign(Error('missing'),{status:404});return {data:{object:{sha:'generated'}}};},
 getCommit:async args=>({data:{tree:{sha:args.commit_sha==='base'?'base-tree':'generated-tree'}}}),
 createBlob:async args=>{calls.blobs.push(args);return {data:{sha:'blob'+calls.blobs.length}};},
 createTree:async args=>{calls.trees.push(args);return {data:{sha:'generated-tree'}};},
 createCommit:async args=>{calls.commits.push(args);return {data:{sha:'generated'}};},
 createRef:async args=>{calls.refs.push(args);existingRef=true;},
 updateRef:async args=>{calls.refs.push(args);}
}},paginate:async()=>openIssues};
const workflowContext={repo:{owner:'owner',repo:'repo'}},quietCore={info(){}};
await updateProposals({github:mock,context:workflowContext,core:quietCore,publicRoot});
assert.deepEqual(calls.trees[0].tree.map(item=>item.path),['web/public/proposals.json','docs/web-source-manifest.json']);
assert.equal(calls.commits.length,1);assert.equal(calls.pulls.length,1);
const manifest=JSON.parse(calls.blobs[1].content),indexEntry=manifest.files.find(e=>e.path==='web/public/proposals.json');
const crypto=await import('node:crypto');assert.equal(indexEntry.sha256,crypto.createHash('sha256').update(calls.blobs[0].content).digest('hex'));
assert.equal(indexEntry.bytes,Buffer.byteLength(calls.blobs[0].content));
await updateProposals({github:mock,context:workflowContext,core:quietCore,publicRoot});
assert.equal(calls.commits.length,1);assert.equal(calls.pulls.length,1);
openIssues=[];await updateProposals({github:mock,context:workflowContext,core:quietCore,publicRoot});
assert.equal(calls.closed.length,1);assert.equal(calls.closed[0].state,'closed');
console.log('Proposal PR generation passed: only index + manifest, exact hash, stable branch/PR, stale draft cleanup.');
