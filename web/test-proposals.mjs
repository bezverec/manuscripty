import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {makeProposal,proposalMarkdown,githubProposalUrl} from './public/proposal-core.mjs';
const page=JSON.parse(await fs.readFile('./public/data/20v/page.json','utf8'));
const line=page.lines[1],c={folio:page.folio,line_id:line.id,source_segment_ids:line.source_segment_ids,bbox:line.bbox,source_sha256:page.source_sha256,models:page.models,raw_htr:line.raw_htr,source_url:'https://rukopisy.digitalizaty.cz/rukopis?vrsta=radky#20v-'+line.id,crop_url:line.image};
const results=[];
function test(name,fn){fn();results.push({name,status:'passed'});}
test('Unchanged HTR rejected',()=>assert.throws(()=>makeProposal(c,'medusa',line.raw_htr.medusa,'Obraz','id','utc'),/shodný/));
test('Whitespace-only suggestion rejected',()=>assert.throws(()=>makeProposal(c,'medusa','  ','Obraz','id','utc'),/Vyplňte/));
test('Unknown model rejected',()=>assert.throws(()=>makeProposal(c,'unknown','text','Obraz','id','utc'),/dostupný/));
test('Reason required',()=>assert.throws(()=>makeProposal(c,'medusa','text','  ','id','utc'),/zdůvodnění/));
const candidate='ypoc̄te sterilis dᵗ glosa omīa opera';
const p=makeProposal(c,'medusa',candidate,'Dlouhé s a zkratka podle výřezu.','id','utc');
test('Original Unicode and source IDs preserved',()=>{assert.equal(p.original_htr,line.raw_htr.medusa);assert.equal(p.proposed_htr,candidate);assert.deepEqual(p.source_segment_ids,line.source_segment_ids);assert.equal(p.source_sha256,page.source_sha256);assert.equal(p.expert_review,false);});
test('Source arrays do not alias mutable viewer context',()=>{const copy=makeProposal(c,'medusa','text','Obraz','id','utc');copy.bbox[0]=0;assert.notEqual(c.bbox[0],0);});
test('Issue draft targets exact repository and carries original/source data',()=>{const u=new URL(githubProposalUrl(p));assert.equal(u.origin,'https://github.com');assert.equal(u.pathname,'/bezverec/manuscripty/issues/new');assert.equal(u.searchParams.get('template'),'htr-oprava.yml');assert.equal(u.searchParams.has('labels'),false);assert.equal(u.searchParams.get('document_id'),'vkol-m-ii-220');assert.equal(JSON.parse(u.searchParams.get('original_htr')),p.original_htr);assert.deepEqual(JSON.parse(u.searchParams.get('source_segment_ids')),p.source_segment_ids);assert.equal(JSON.parse(u.searchParams.get('proposed_htr')),p.proposed_htr);});
test('Long Unicode draft switches to JSON export',()=>{const large=makeProposal(c,'medusa','ž'.repeat(2000),'ř'.repeat(2000),'id','utc');assert.equal(githubProposalUrl(large),null);});
test('Bounded fields reject oversize input',()=>assert.throws(()=>makeProposal(c,'medusa','x'.repeat(2001),'Obraz','id','utc'),/2 000/));
test('Markdown fence does not close on user backticks',()=>{const q=makeProposal(c,'medusa','\x60\x60\x60\n<img src=x onerror=alert(1)>','Obraz','id','utc');assert.ok(proposalMarkdown(q).includes('\x60\x60\x60\x60\n\x60\x60\x60'));});
const summaryText=await fs.readFile('./public/summary.json','utf8');
test('Generated sources resolve to existing folia and segment IDs',()=>{for(const section of JSON.parse(summaryText).sections){for(const source of section.sources){const fragment=new URL(source.url,'https://rukopisy.digitalizaty.cz/').hash.slice(1);assert.equal(fragment.split('-')[0],source.folio);assert.ok(source.source_sha256.match(/^[a-f0-9]{64}$/));}}});


test('Additional manuscript identity reaches form unchanged',()=>{const q=makeProposal({...c,document_id:'vkol-m-ii-153',manuscript:'M II 153'},'medusa','text','Obraz','id','utc');const u=new URL(githubProposalUrl(q));assert.equal(q.document_id,'vkol-m-ii-153');assert.equal(u.searchParams.get('document_id'),q.document_id);assert.ok(u.searchParams.get('title').includes('M II 153'));});
const report={status:'passed',tests:results,checked_utc:new Date().toISOString()};await fs.writeFile('proposal-validation.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report));
