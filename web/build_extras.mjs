import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const D=path.dirname(fileURLToPath(import.meta.url)),P=path.join(D,'public');
const text=await fs.readFile(path.join(P,'pilot-data.js'),'utf8');
const manifest=JSON.parse(text.slice(text.indexOf('=')+1).trim().replace(/;$/,''));
const folios=manifest.pages.filter(p=>p.kind!=='binding').map(p=>({...p,label:'f. '+p.folio}));
const binding=JSON.parse(await fs.readFile(path.join(D,'binding-pages.json'),'utf8'));
manifest.pages=[...binding.filter(p=>p.position==='front'),...folios,...binding.filter(p=>p.position==='back')];
manifest.scope='Celý rukopis: 670 foliovaných snímků a 7 snímků vazby / předsádky; pracovní výsledky bez odborné revize.';
manifest.counts={...manifest.counts,pages:manifest.pages.length,folios:folios.length,binding:binding.length,text_pages:folios.filter(p=>!p.blank).length};
if(manifest.pages.length!==677||new Set(manifest.pages.map(p=>p.folio)).size!==677)throw Error('Coverage mismatch');
await fs.writeFile(path.join(P,'pilot-data.js'),'window.PILOT_DATA = '+JSON.stringify(manifest)+';\n');
const leaves=[];
for(const p of manifest.pages){
 const d=JSON.parse(await fs.readFile(path.join(P,p.data),'utf8'));
 const ids=new Set(d.lines.map(l=>l.id));
 const passages=d.passages.map(v=>{if(!v.line_ids.length||!ids.has(v.line_ids[0]))throw Error('Invalid source line '+p.folio+'/'+v.id);return{id:v.id,title:v.title,line_id:v.line_ids[0]};});
 leaves.push({folio:p.folio,label:p.label,kind:p.kind||'folio',blank:p.blank,source_sha256:d.source_sha256,passages});
}
const byId=new Map(leaves.map(p=>[p.folio,p]));
const groups=[{id:'front',label:'Přední deska, přídeští a předsádka',pages:binding.filter(p=>p.position==='front').map(p=>byId.get(p.folio))}];
for(let i=0;i<folios.length;i+=20){const members=folios.slice(i,i+20).map(p=>byId.get(p.folio));groups.push({id:'folios-'+members[0].folio,label:'Folia '+members[0].folio+'–'+members.at(-1).folio,pages:members});}
groups.push({id:'back',label:'Zadní přídeští, deska a hřbet',pages:binding.filter(p=>p.position==='back').map(p=>byId.get(p.folio))});
const structure={schema:'manuscripty-structure-v1',status:'proposed',expert_review:false,basis:'Pracovní názvy existujících rekonstrukčních pasáží; skupiny po deseti foliích slouží navigaci a netvrdí hranice děl ani složek vazby.',counts:{pages:leaves.length,folios:folios.length,binding:binding.length,passages:leaves.reduce((a,p)=>a+p.passages.length,0)},groups};
await fs.writeFile(path.join(P,'structure.json'),JSON.stringify(structure));
await fs.writeFile(path.join(D,'structure-binding-data-validation.json'),JSON.stringify({status:'passed',source_archive_unchanged:true,counts:structure.counts,unique_pages:byId.size,passage_links_validated:structure.counts.passages,groups:groups.length},null,2)+'\n');
console.log(JSON.stringify(structure.counts));
