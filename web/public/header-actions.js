(() => {
  'use strict';
  const toggle=document.getElementById('more-actions-toggle');
  const panel=document.getElementById('more-actions-panel');
  function close(focus=false){panel.hidden=true;toggle.setAttribute('aria-expanded','false');if(focus)toggle.focus({preventScroll:true});}
  toggle.addEventListener('click',()=>{const open=panel.hidden;panel.hidden=!open;toggle.setAttribute('aria-expanded',String(open));});
  document.addEventListener('click',e=>{if(!e.target.closest('.more-actions') || e.target.closest('[data-goto-tab]'))close();});
  document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!panel.hidden){e.preventDefault();close(true);}});
  window.matchMedia('(min-width:961px)').addEventListener('change',()=>close());
})();
