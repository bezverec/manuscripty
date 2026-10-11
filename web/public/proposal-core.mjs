const REPOSITORY='https://github.com/bezverec/manuscripty';
export function makeProposal(c,model,proposed,reason,id,createdUtc){
 if(!c||!Object.hasOwn(c.raw_htr,model))throw Error('Vyberte dostupný HTR model.');
 if(!proposed.trim())throw Error('Vyplňte navržený přepis.');
 if(proposed===c.raw_htr[model])throw Error('Návrh je shodný s původním HTR.');
 if(!reason.trim())throw Error('Doplňte zdůvodnění podle obrazu.');
 if(proposed.length>2000||reason.length>2000)throw Error('Přepis a zdůvodnění mohou mít nejvýše 2 000 znaků.');
 return {schema:'manuscripty-htr-proposal-v1',id,created_utc:createdUtc,manuscript:'M II 220',folio:c.folio,line_id:c.line_id,source_segment_ids:[...c.source_segment_ids],bbox:[...c.bbox],source_sha256:c.source_sha256,model,model_label:c.models[model],original_htr:c.raw_htr[model],proposed_htr:proposed,reason_cs:reason,source_url:c.source_url,crop_url:c.crop_url,status:'proposed',expert_review:false};
}
function fenced(text){const runs=text.match(/\x60+/g)||[];const fence=String.fromCharCode(96).repeat(Math.max(3,...runs.map(s=>s.length+1)));return fence+'\n'+text+'\n'+fence;}
export function proposalMarkdown(p){return ['## Návrh opravy HTR','- Rukopis: '+p.manuscript,'- Folio: '+p.folio,'- Řádek / segment: '+p.line_id,'- Zdrojové segmenty: '+p.source_segment_ids.join(', '),'- Model: '+p.model_label,'- SHA-256 původního skenu: '+p.source_sha256,'- Odkaz na analýzu: '+p.source_url,'- Obrazový výřez: '+p.crop_url,'','### Původní HTR',fenced(p.original_htr),'','### Navržený přepis',fenced(p.proposed_htr),'','### Zdůvodnění podle obrazu',p.reason_cs,'','Návrh čeká na posouzení. Původní HTR se nemění a nejde o odborně schválenou opravu.','','ID návrhu: '+p.id].join('\n');}
export function githubProposalUrl(p){const url=new URL(REPOSITORY+'/issues/new');url.searchParams.set('title','[HTR] M II 220 · '+p.folio+' · '+p.line_id+' · '+p.model);url.searchParams.set('body',proposalMarkdown(p));return url.href.length<=7500?url.href:null;}
