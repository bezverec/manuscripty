import {makeProposal,proposalMarkdown,githubProposalUrl} from './proposal-core.mjs?v=20261019-1';
const dialog=document.querySelector('#correction-dialog'),form=document.querySelector('#correction-form'),modelSelect=document.querySelector('#correction-model'),proposedInput=document.querySelector('#correction-proposed'),reasonInput=document.querySelector('#correction-reason'),status=document.querySelector('#correction-status'),preview=document.querySelector('#correction-preview'),githubLink=document.querySelector('#correction-github'),download=document.querySelector('#correction-download');
let context=null,proposal=null;
function invalidate(){proposal=null;preview.hidden=true;githubLink.hidden=true;githubLink.removeAttribute('href');download.disabled=true;status.textContent='';}
function selectModel(){document.querySelector('#correction-original').value=context.raw_htr[modelSelect.value];proposedInput.value=context.raw_htr[modelSelect.value];invalidate();}
window.addEventListener('manuscripty:propose-htr',event=>{
 context=structuredClone(event.detail);form.reset();modelSelect.replaceChildren();
 for(const [key,label] of Object.entries(context.models)){if(typeof context.raw_htr[key]!=='string')continue;const option=document.createElement('option');option.value=key;option.textContent=label;modelSelect.append(option);}
 modelSelect.value=Object.hasOwn(context.raw_htr,context.model)?context.model:modelSelect.options[0].value;
 document.querySelector('#correction-target').textContent=(context.manuscript||'M II 220')+' · '+context.folio+' · '+context.line_id;
 const crop=document.querySelector('#correction-crop');crop.src=context.crop_url;crop.alt='Podklad návrhu: '+context.line_id;
 document.querySelector('#correction-source').href=context.source_url;selectModel();dialog.showModal();proposedInput.focus();
});
modelSelect.addEventListener('change',selectModel);proposedInput.addEventListener('input',invalidate);reasonInput.addEventListener('input',invalidate);
document.querySelector('#correction-close').addEventListener('click',()=>dialog.close());
form.addEventListener('submit',event=>{
 event.preventDefault();invalidate();
 try{proposal=makeProposal(context,modelSelect.value,proposedInput.value,reasonInput.value,crypto.randomUUID(),new Date().toISOString());
 document.querySelector('#correction-preview-text').textContent=proposalMarkdown(proposal);preview.hidden=false;download.disabled=false;
 const url=githubProposalUrl(proposal);
 if(url){githubLink.href=url;githubLink.hidden=false;status.textContent='Návrh je připraven. Na GitHubu jej ještě zkontrolujete a odešlete tlačítkem Create issue.';}
 else{githubLink.href='https://github.com/bezverec/manuscripty/issues/new?template=htr-oprava.yml';githubLink.hidden=false;status.textContent='Návrh je příliš dlouhý pro předvyplněný odkaz. Uložte JSON a vložte jeho obsah do pole proposal_json k novému hlášení na GitHubu.';}
 }catch(error){status.textContent=error.message;}
});
download.addEventListener('click',()=>{if(!proposal)return;const url=URL.createObjectURL(new Blob([JSON.stringify(proposal,null,2)+'\n'],{type:'application/json;charset=utf-8'}));const link=document.createElement('a');link.href=url;link.download=proposal.document_id+'-'+proposal.folio+'-'+proposal.line_id+'-'+proposal.model+'-navrh.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
