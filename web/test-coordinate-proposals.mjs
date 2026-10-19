import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {makeProposal,proposalMarkdown,githubProposalUrl} from './public/proposal-core.mjs';
import {makeSegmentationProposal,segmentationMarkdown,segmentationGithubUrl} from './public/segmentation-core.mjs';
import {proposalCoordinates} from './public/coordinate-core.mjs';
import {HTR_TEXT_FIELDS} from './public/issue-form-core.mjs';
import {parseIssue,validateProposal} from './scripts/proposals.mjs';

const master='a'.repeat(64), raster='b'.repeat(64);
const coordinate={id:'vkol-m-i-259_FS_coordinate',sha256:raster,width:5600,height:3900,frame:0,derived_from_sha256:master,original_tiff_frame:0,rotation_ccw_degrees:90,source_to_coordinate_pixel_edge_affine:[[0,1,0],[-1,0,3900],[0,0,1]],bbox_format:'xywh',origin:'top-left'};
const line={id:'fFS_l001',source_segment_ids:['fFS_l001'],bbox:[100,200,500,100],raw_htr:{catmus:'ãte',medusa:'ante'},image:'https://example.org/crop.webp'};
const page={document_id:'vkol-m-i-259',document_uri:'https://example.org/rukopisy/vkol-m-i-259',manuscript:'M I 259',folio:'FS',width:5600,height:3900,source_original:'master.TIF',source_sha256:master,coordinate_source:coordinate,model_input:{sha256:'c'.repeat(64),mask:'white outside selected main-text area'},models:{catmus:'CATMuS',medusa:'Medusa'},lines:[line]};
const c={...page,line_id:line.id,source_segment_ids:line.source_segment_ids,bbox:line.bbox,raw_htr:line.raw_htr,crop_url:line.image,source_url:'https://example.org/reader#FS',segments:[line],preview_url:'https://example.org/preview.webp'};
const h=makeProposal(c,'medusa','[ante?]','Čtení podle obrazu.','h-id','2026-10-19T00:00:00Z');
const s=makeSegmentationProposal(c,'resize',[line.id],[[100,190,500,110]],'Horní hranice.','s-id','2026-10-19T00:00:00Z');
assert.equal(h.schema,'manuscripty-htr-proposal-v2');assert.equal(s.schema,'manuscripty-segmentation-proposal-v2');
for(const p of [h,s]){
 assert.equal(p.source_sha256,master);assert.equal(p.coordinate_source.sha256,raster);
 assert.equal(p.coordinate_source.model_input,undefined);assert.equal(p.coordinate_system.units,'coordinate-image-pixels');
 assert.equal(p.coordinate_system.coordinate_source_id,coordinate.id);assert.equal(p.coordinate_system.coordinate_source_sha256,raster);
 assert.deepEqual(p.coordinate_source.source_to_coordinate_pixel_edge_affine,coordinate.source_to_coordinate_pixel_edge_affine);
}
assert.ok(proposalMarkdown(h).includes('nikoli neotočeného TIFF'));assert.ok(segmentationMarkdown(s).includes('výslovně identifikovaného koordinačního obrazu'));
const body=p=>Object.entries(p).map(([k,v])=>'### '+k+'\n\n'+(typeof v==='string'&&!HTR_TEXT_FIELDS.has(k)?v:JSON.stringify(v))+'\n').join('\n');
for(const [p,type,url] of [[h,'htr',githubProposalUrl(h)],[s,'segmentace',segmentationGithubUrl(s)]]){
 assert.deepEqual(parseIssue(body(p),type),p);
 assert.deepEqual(parseIssue('### proposal_json\n'+JSON.stringify(p),type),p);
 assert.ok(url);assert.deepEqual(JSON.parse(new URL(url).searchParams.get('coordinate_source')),coordinate);
 assert.deepEqual(JSON.parse(new URL(url).searchParams.get('coordinate_system')),p.coordinate_system);
}
const copy=makeProposal(c,'medusa','aliud','Obraz','id','utc');copy.coordinate_source.source_to_coordinate_pixel_edge_affine[0][0]=99;
assert.equal(c.coordinate_source.source_to_coordinate_pixel_edge_affine[0][0],0);
assert.throws(()=>makeProposal({...c,coordinate_source:undefined},'medusa','x','Obraz','id','utc'),/Chybí identifikace/);
assert.throws(()=>makeSegmentationProposal({...c,coordinate_source:undefined},'add',[],[[1,1,10,10]],'Obraz','id','utc'),/Chybí identifikace/);
for(const patch of [{sha256:'not-a-hash'},{derived_from_sha256:'d'.repeat(64)},{width:3900},{frame:1},{unknown:'local path'},{source_to_coordinate_pixel_edge_affine:[[0,1,0],[-1,0,3899],[0,0,1]]}]){
 assert.throws(()=>makeProposal({...c,coordinate_source:{...coordinate,...patch}},'medusa','x','Obraz','id','utc'));
}
assert.throws(()=>makeProposal({...c,bbox:[5599,0,2,2]},'medusa','x','Obraz','id','utc'),/mimo koordinační/);
assert.equal(proposalCoordinates({...c,coordinate_source:{...coordinate,original_tiff_frame:1}}).coordinate_source.frame,0);
for(const [degrees,matrix] of [[0,[[1,0,0],[0,1,0],[0,0,1]]],[90,[[0,1,0],[-1,0,3900],[0,0,1]]],[180,[[-1,0,5600],[0,-1,3900],[0,0,1]]],[270,[[0,-1,5600],[1,0,0],[0,0,1]]]]){
 assert.equal(proposalCoordinates({...c,coordinate_source:{...coordinate,rotation_ccw_degrees:degrees,source_to_coordinate_pixel_edge_affine:matrix}}).coordinate_source.rotation_ccw_degrees,degrees);
}
const temporary=await fs.mkdtemp(path.join(os.tmpdir(),'manuscripty-coordinate-'));
try{
 const writePage=async p=>{const dir=path.join(temporary,'data',p.document_id,p.folio);await fs.mkdir(dir,{recursive:true});await fs.writeFile(path.join(dir,'page.json'),JSON.stringify(p));};
 await writePage(page);
 const extra={...page,folio:'extra-83v'};await writePage(extra);
 const extraProposal=makeProposal({...c,folio:extra.folio},'medusa','x','Obraz','extra-id','utc');
 assert.equal((await validateProposal(extraProposal,'htr',temporary)).folio,'extra-83v');
 for(const [p,type] of [[h,'htr'],[s,'segmentace']]){
  assert.equal((await validateProposal(p,type,temporary)).document_id,page.document_id);
  for(const patch of [{source_sha256:'0'.repeat(64)},{coordinate_source:{...coordinate,sha256:'d'.repeat(64)}},{coordinate_source:{...coordinate,source_to_coordinate_pixel_edge_affine:[[0,1,0],[-1,0,3899],[0,0,1]]}},{coordinate_system:{...p.coordinate_system,units:'original-image-pixels'}},{coordinate_system:{...p.coordinate_system,coordinate_source_id:'other'}}])await assert.rejects(validateProposal({...p,...patch},type,temporary));
  const downgrade={...p,schema:p.schema.replace(/v2$/,'v1')};delete downgrade.coordinate_source;delete downgrade.coordinate_system;
  await assert.rejects(validateProposal(downgrade,type,temporary),/v2/);
 }
 // Both older manuscripts retain their original proposal schemas and geometry.
 for(const id of ['vkol-m-ii-220','vkol-m-ii-153']){
  const old={...page,document_id:id};delete old.coordinate_source;await writePage(old);
  const context={...c,document_id:id};delete context.coordinate_source;
  const oldH=makeProposal(context,'medusa','x','Obraz','id','utc'),oldS=makeSegmentationProposal(context,'add',[],[[1,1,10,10]],'Obraz','id','utc');
  assert.equal(oldH.schema,'manuscripty-htr-proposal-v1');assert.equal(oldS.schema,'manuscripty-segmentation-proposal-v1');
  assert.equal(oldS.coordinate_system.units,'original-image-pixels');
  await validateProposal(oldH,'htr',temporary);await validateProposal(oldS,'segmentace',temporary);
  await assert.rejects(validateProposal({...oldH,schema:'manuscripty-htr-proposal-v2',coordinate_source:coordinate},'htr',temporary));
 }
}finally{
 const resolved=await fs.realpath(temporary),root=await fs.realpath(os.tmpdir());assert.ok(resolved.startsWith(root+path.sep));
 await fs.rm(resolved,{recursive:true,force:true});
}
console.log('Coordinate proposal tests passed: full raster/TIFF/model-mask separation, rotations at pixel edges, JSON and issue forms, tamper rejection, v1 compatibility for both older manuscripts.');
