import fs from 'node:fs/promises';
import path from 'node:path';
import {isDeepStrictEqual} from 'node:util';
import {HTR_FIELDS,SEGMENTATION_FIELDS,LEGACY_DOCUMENT,HTR_TEXT_FIELDS} from '../public/issue-form-core.mjs';
import {makeSegmentationProposal} from '../public/segmentation-core.mjs';
const JSON_FIELDS=new Set([...HTR_TEXT_FIELDS,'source_segment_ids','bbox','original_segments','proposed_regions','coordinate_system','image_width','image_height','expert_review']);
export const VALIDATION_MARKER='<!-- manuscripty-proposal-validation-v1 -->';
export function parseIssue(body,type) {
 if(typeof body!=='string'||body.length>100000)throw Error('Chybí formulář nebo je příliš dlouhý.');
 const allowed=new Set([...HTR_FIELDS,...SEGMENTATION_FIELDS,'proposal_json']),fields=Object.create(null);
 let key=null,buffer=[];
 const flush=()=>{if(key!==null){if(Object.hasOwn(fields,key))throw Error('Pole se opakuje: '+key);fields[key]=buffer.join('\n').trim();}};
 let fenced=false;
 for(const line of body.split(/\r?\n/)){
  if(/^\x60\x60\x60/.test(line))fenced=!fenced;
  const heading=!fenced&&/^### ([a-z0-9_]+)\s*$/.exec(line);
  if(heading){flush();key=allowed.has(heading[1])?heading[1]:null;buffer=[];}else buffer.push(line);
 }flush();
 if(fields.proposal_json&&fields.proposal_json!=='_No response_'){
  const text=fields.proposal_json.replace(/^\x60\x60\x60(?:json)?\s*\n/,'').replace(/\n\x60\x60\x60$/,'');
  const p=JSON.parse(text);if(!p||Array.isArray(p)||typeof p!=='object')throw Error('Export musí být objekt JSON.');return p;
 }
 const p={};
 for(const id of type==='htr'?HTR_FIELDS:SEGMENTATION_FIELDS){const value=fields[id];if(value===undefined||value==='_No response_'||!value)continue;p[id]=JSON_FIELDS.has(id)?JSON.parse(value):value;}
 return p;
}
function fail(condition,message){if(!condition)throw Error(message);}
function same(a,b){return isDeepStrictEqual(a,b);}
export async function validateProposal(p,type,publicRoot) {
 fail(p.schema===(type==='htr'?'manuscripty-htr-proposal-v1':'manuscripty-segmentation-proposal-v1'),'Neznámé nebo nesprávné schema.');
 const document=p.document_id||LEGACY_DOCUMENT;
 fail(typeof document==='string'&&/^[a-z0-9][a-z0-9-]{0,100}$/.test(document),'Neplatný document_id.');
 fail(typeof p.folio==='string'&&/^[a-zA-Z0-9]{1,20}$/.test(p.folio),'Neplatné folio.');
 const candidates=[path.join(publicRoot,'data',document,p.folio,'page.json'),path.join(publicRoot,'rukopisy',document,'data',p.folio,'page.json')];
 if(document===LEGACY_DOCUMENT)candidates.push(path.join(publicRoot,'data',p.folio,'page.json'));
 let page=null;for(const file of candidates){try{page=JSON.parse(await fs.readFile(file,'utf8'));break;}catch(e){if(e.code!=='ENOENT')throw e;}}
 fail(page&&page.folio===p.folio&&page.document_id===document,'Dokument nebo folio v publikovaných datech neexistuje.');
 fail(typeof p.source_sha256==='string'&&/^[a-f0-9]{64}$/.test(p.source_sha256)&&p.source_sha256===page.source_sha256,'source_sha256 neodpovídá původnímu skenu.');
 fail(p.status==='proposed'&&p.expert_review===false,'Návrh musí mít status proposed a expert_review false.');
 fail(typeof p.id==='string'&&p.id.length>0&&p.id.length<=200,'Chybí ID návrhu.');
 fail(typeof p.reason_cs==='string'&&p.reason_cs.trim()&&p.reason_cs.length<=2000,'Chybí zdůvodnění nebo je příliš dlouhé.');
 let lineIds=[];
 if(type==='htr'){
  const line=page.lines.find(l=>l.id===p.line_id);
  fail(line,'line_id v tomto foliu neexistuje.');
  fail(same(p.source_segment_ids,line.source_segment_ids)&&same(p.bbox,line.bbox),'Zdrojová ID nebo bbox neodpovídají řádku.');
  fail(Object.hasOwn(line.raw_htr,p.model)&&p.original_htr===line.raw_htr[p.model],'Model nebo původní HTR neodpovídá datům.');
  fail(typeof p.proposed_htr==='string'&&p.proposed_htr.trim()&&p.proposed_htr.length<=2000&&p.proposed_htr!==p.original_htr,'Navržený HTR chybí, je příliš dlouhý nebo se neliší.');
  lineIds=[line.id];
 }else{
  fail(p.image_width===page.width&&p.image_height===page.height&&p.source_original===page.source_original,'Rozměry nebo zdrojový soubor neodpovídají.');
  fail(same(p.coordinate_system,{origin:'top-left',units:'original-image-pixels',bbox_format:['x','y','width','height']}),'Neplatný souřadnicový systém.');
  fail(Array.isArray(p.original_segments)&&Array.isArray(p.proposed_regions),'Chybí původní segmenty nebo nové oblasti.');
  const segments=page.lines.map(l=>({id:l.id,bbox:l.bbox,source_segment_ids:l.source_segment_ids}));
  const rebuilt=makeSegmentationProposal({...page,segments},p.operation,p.original_segments.map(s=>s.id),p.proposed_regions.map(s=>s.bbox),p.reason_cs,p.id,p.created_utc);
  fail(same(rebuilt.original_segments,p.original_segments)&&same(rebuilt.proposed_regions,p.proposed_regions),'segment_id, zdrojová geometrie nebo pořadí oblastí neodpovídají.');
  lineIds=p.original_segments.map(s=>s.id);if(!lineIds.length)lineIds=['*'];
 }
 return {document_id:document,folio:p.folio,line_ids:lineIds};
}
export function proposalType(issue) {
 const labels=(issue.labels||[]).map(l=>typeof l==='string'?l:l.name);
 const types=[['htr-oprava','htr'],['segmentace-oprava','segmentace']].filter(([label])=>labels.includes(label));
 return types.length===1?types[0][1]:null;
}
export async function collectProposals(issues,publicRoot) {
 const documents=Object.create(null);
 for(const issue of issues){
  if(issue.pull_request||issue.state!=='open')continue;const type=proposalType(issue);if(!type)continue;
  try{const identity=await validateProposal(parseIssue(issue.body,type),type,publicRoot);
   const doc=documents[identity.document_id]||=Object.create(null),folio=doc[identity.folio]||=Object.create(null);
   for(const id of identity.line_ids){const nums=folio[id]||=[];if(!nums.includes(issue.number))nums.push(issue.number);}
  }catch{ /* Invalid drafts are excluded; validation workflow provides feedback. */ }
 }
 for(const doc of Object.values(documents))for(const folio of Object.values(doc))for(const nums of Object.values(folio))nums.sort((a,b)=>a-b);
 const ordered=Object.fromEntries(Object.keys(documents).sort().map(id=>[id,Object.fromEntries(Object.keys(documents[id]).sort().map(folio=>[folio,Object.fromEntries(Object.keys(documents[id][folio]).sort().map(line=>[line,documents[id][folio][line]]))]))]));
 return {...(ordered[LEGACY_DOCUMENT]||{}),documents:ordered};
}
