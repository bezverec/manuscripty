/* Pagefind index stays local to Pages; no queries are sent to a server. */
const hosts=document.querySelectorAll('[data-folio-search]');
for(const host of hosts){
 const form=host.querySelector('form'),input=form.querySelector('input'),status=host.querySelector('[role="status"]'),results=host.querySelector('ol'),more=host.querySelector('[data-search-more]');
 let pagefind,request=0,hits=[],offset=0;
 async function showMore(){
  more.disabled=true;
  const current=request,batch=await Promise.all(hits.slice(offset,offset+20).map(result=>result.data()));
  if(current!==request)return;
  for(const hit of batch){
   const li=document.createElement('li'),a=document.createElement('a'),p=document.createElement('p');
   const url=new URL(hit.url,location.origin);
   if(url.origin!==location.origin || !/^\/rukopisy\/vkol-[a-z0-9-]+\/[A-Za-z0-9_-]+(?:\.html)?$/.test(url.pathname))continue;
   a.href=url.pathname.replace(/\.html$/,'')+url.hash;a.textContent=hit.meta.title || 'Stránka rukopisu';
   // Excerpts are text, never injected HTML. Strip only Pagefind's mark wrappers.
   p.textContent=hit.excerpt.replace(/<\/?mark>/g,'');li.append(a,p);results.append(li);
  }
  offset+=batch.length;more.hidden=offset>=hits.length;more.disabled=false;
 }
 form.addEventListener('submit',async event=>{
  event.preventDefault();const query=input.value.trim();if(!query)return;
  const current=++request;results.replaceChildren();more.hidden=true;status.textContent='Hledám…';
  try{
   pagefind ||= await import('/pagefind/pagefind.js');
   const result=await pagefind.search(query,host.dataset.document ? {filters:{rukopis:host.dataset.document}} : {});
   if(current!==request)return;
   hits=result.results;offset=0;status.textContent=hits.length ? `Nalezeno stran: ${hits.length}.` : 'Žádná shoda. Zkuste jiný tvar slova nebo část textu.';
   await showMore();
  }catch{if(current===request)status.textContent='Vyhledávací index není dostupný. Prohlížeč a stránky rukopisu zůstávají přístupné.';}
 });
 more.addEventListener('click',async()=>{try{await showMore();}catch{status.textContent='Další výsledky se nepodařilo načíst.';more.disabled=false;}});
}
