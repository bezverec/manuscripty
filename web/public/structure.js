(() => {
 'use strict';
 const host=document.getElementById('manuscript-toc'), search=document.getElementById('structure-search'), status=document.getElementById('structure-status');
 let structure=null, request=null, current='', active=false, timer;
 const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const countLabel=(n,one,few,many)=>n+' '+(n===1?one:n>1&&n<5?few:many);
 const normalized=s=>String(s).normalize('NFD').replace(/\p{M}/gu,'').toLocaleLowerCase('cs');
 function render(){
  if(!structure)return;
  const query=normalized(search.value.trim()), folioQuery=/^(?:f\.?\s*)?(\d+[rv])$/.exec(query); let count=0, passages=0;
  const groups=structure.groups.map(group=>{
   const pages=group.pages.map(p=>{
    const pageMatch=!query||(folioQuery?normalized(p.folio)===folioQuery[1]:normalized(p.label+' '+p.folio).includes(query));
    const matches=pageMatch?p.passages:p.passages.filter(v=>normalized(v.title).includes(query));
    if(!pageMatch&&!matches.length)return '';
    count++;passages+=matches.length;
    const selected=p.folio===current;
    return '<details class="structure-leaf'+(selected?' is-current':'')+'" data-structure-page="'+esc(p.folio)+'"'+(query||selected?' open':'')+'><summary>'+esc(p.label)+' · '+p.passages.length+' pasáží</summary><button type="button" class="btn btn--sm" data-structure-folio="'+esc(p.folio)+'">Zobrazit stranu</button>'+(!p.passages.length?'<p class="sample-notice">'+esc(p.kind==='binding'?'Obraz vazby / předsádky; zatím bez HTR.':'Bez vybraného hlavního textu.')+'</p>':'')+'<ol class="structure-links">'+matches.map(v=>'<li><button type="button" data-structure-folio="'+esc(p.folio)+'" data-structure-line="'+esc(v.line_id)+'">'+esc(v.title)+'</button></li>').join('')+'</ol></details>';
   }).filter(Boolean);
   if(!pages.length)return '';
   const open=!!query||group.pages.some(p=>p.folio===current);
   return '<details class="structure-group"'+(open?' open':'')+'><summary>'+esc(group.label)+' · '+countLabel(pages.length,'snímek','snímky','snímků')+'</summary>'+pages.join('')+'</details>';
  }).filter(Boolean);
  host.innerHTML=groups.length?groups.join(''):'<p>Žádná shoda. Zkuste jiné folio nebo slovo.</p>';
  status.textContent=(query?'Výsledky: ':'Celkem: ')+countLabel(count,'snímek','snímky','snímků')+' · '+countLabel(passages,'pasáž','pasáže','pasáží');
 }
 async function load(){
  if(structure){render();return;}
  status.textContent='Načítám strukturu celého rukopisu…';
  if(!request) request=fetch('structure.json?v=20261011-6').then(r=>{if(!r.ok)throw Error('HTTP '+r.status);return r.json();}).then(data=>{structure=data;render();}).catch(()=>{request=null;status.textContent='Strukturu se nepodařilo načíst. Zkuste záložku otevřít znovu.';});
  await request;
 }
 window.addEventListener('manuscripty:tab',e=>{current=e.detail.folio;active=e.detail.tab==='struktura';if(active)void load();});
 search.addEventListener('input',()=>{clearTimeout(timer);timer=setTimeout(render,150);});
 host.addEventListener('click',e=>{
  const button=e.target.closest('[data-structure-folio]');if(!button)return;
  window.dispatchEvent(new CustomEvent('manuscripty:navigate-structure',{detail:{folio:button.dataset.structureFolio,line_id:button.dataset.structureLine||null,tab:button.dataset.structureLine?'vyklad':'struktura'}}));
 });
})();
