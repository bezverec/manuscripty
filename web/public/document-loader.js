(() => {
 'use strict';
 const requested=new URL(location.href).searchParams.get('doc') || 'vkol-m-ii-220';
 const registry={'vkol-m-ii-220':null,'vkol-m-ii-153':'/data/vkol-m-ii-153/manifest.json'};
 window.MANUSCRIPT_READY=new Promise((resolve,reject)=>{
  if(!Object.hasOwn(registry,requested)){reject(Error('Neznámý identifikátor rukopisu.'));return;}
  if(requested==='vkol-m-ii-220'){
   const script=document.createElement('script');script.src='pilot-data.js?v=20261012-6';
   script.onload=()=>window.PILOT_DATA?.document?.id===requested?resolve():reject(Error('Neplatný manifest.'));
   script.onerror=()=>reject(Error('Manifest není dostupný.'));document.head.append(script);return;
  }
  fetch(registry[requested]+'?v=20261012-6').then(r=>{if(!r.ok)throw Error('Manifest není dostupný.');return r.json();})
   .then(data=>{if(data.document?.id!==requested||!Array.isArray(data.pages)||!data.pages.length)throw Error('Neplatný manifest.');window.PILOT_DATA=data;resolve();}).catch(reject);
 });
})();
