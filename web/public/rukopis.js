window.MANUSCRIPT_READY.then(async () => {
  'use strict';
  const {resolveReaderHash, renderSupplementalReadings, renderReadingAddenda} = await import('./reader-core.mjs?v=20261021-2');
  const DATA = window.PILOT_DATA;
  const PAGES = DATA.pages;
  const shelfmark=DATA.document.shelfmark || DATA.title;
  const TABS = ['prepis', 'radky', 'vyklad', 'analyza', 'popis', 'struktura', 'citace'];
  const GROUPS = ['text', 'about', 'citace'];
  const TEXT_VIEWS = ['prepis', 'radky', 'vyklad'];
  const groupOf = tab => TEXT_VIEWS.includes(tab) ? 'text' : tab === 'citace' ? 'citace' : 'about';
  let textView = 'prepis', aboutView = 'popis';
  let viewer = null, loadingRequest = 0;
  let overlayTrackers = [];
  const state = { page: 0, line: 0, tab: 'prepis', model: 'catmus', zoom: 1, passage: null };
  const $ = (s) => document.querySelector(s);
  const esc = (s) => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const page = () => PAGES[state.page];
  let proposalIndex = null, proposalLookup = null;
  function proposalLinks(id) {
    const numbers=proposalLookup?.(proposalIndex,page().document_id||DATA.document.id,page().folio,id)||[];
    return numbers.map(n=>'<a href="https://github.com/bezverec/manuscripty/issues/'+n+'" target="_blank" rel="noopener">Otevřený návrh #'+n+'</a>').join(' · ');
  }
  Promise.all([import('./issue-form-core.mjs?v=20261019-1'),fetch('proposals.json?v=20261012-6').then(r=>r.ok?r.json():null)]).then(([core,index])=>{proposalLookup=core.openProposalNumbers;proposalIndex=index;if(page().lines){renderLines();renderAnalysis();}}).catch(()=>{});
  const selectedLine = () => page().lines?.[state.line] || null;
  const statusLabel = s => s === 'uncertain' ? 'Nejisté čtení' : 'Pracovní návrh';
  const asText = v => typeof v === 'string' ? v : JSON.stringify(v, null, 2);
  const notesText = v => Array.isArray(v) ? v.map(asText).join(' · ') : v ? asText(v) : '';
  const linkedPassages = () => selectedLine() ? page().passages.filter(p => p.line_ids.includes(selectedLine().id)) : [];
  function permalink() {
    const url = new URL(location.href);
    url.searchParams.set('vrstva', state.tab);
    url.hash = page().folio + (selectedLine() ? '-' + selectedLine().id : '');
    return url.href;
  }
  function setHash() { history.replaceState(null, '', permalink()); }
  function readHash() {
    let hash = '';
    try { hash = decodeURIComponent(location.hash.slice(1)); } catch { return {page:0,line:0}; }
    return resolveReaderHash(PAGES, hash);
  }
  function folioCanonicalUrl() {
    const url = new URL(DATA.document.uri.replace(/\/$/, '') + '/' + encodeURIComponent(page().folio));
    if (selectedLine()) url.hash = selectedLine().id;
    return url.href;
  }
  function updateCitation() {
    $('#citation').textContent = 'Vědecká knihovna v Olomouci, ' + shelfmark + ', ' + (page().label || 'folio ' + page().folio) + '. Výzkumný pilot: pracovní čtení, rekonstrukce a český překlad bez odborné revize. ' + folioCanonicalUrl();
    $('#permalink').value = folioCanonicalUrl();
  }
  function scrollWithin(container, item) {
    if (!item || !container) return;
    const c=container.getBoundingClientRect(),r=item.getBoundingClientRect();
    if(r.top<c.top)container.scrollTop-=c.top-r.top;
    else if(r.bottom>c.bottom)container.scrollTop+=r.bottom-c.bottom;
    if(r.left<c.left)container.scrollLeft-=c.left-r.left;
    else if(r.right>c.right)container.scrollLeft+=r.right-c.right;
  }
  function highlight() {
    if (!viewer || !viewer.world.getItemAt(0)) return;
    overlayTrackers.forEach(tracker => tracker.destroy());
    overlayTrackers = [];
    viewer.clearOverlays();
    let ids = selectedLine() ? [selectedLine().id] : [];
    if (state.passage) { const p=page().passages.find(p=>p.id===state.passage);if(p)ids=p.line_ids; }
    page().lines.forEach((l,i)=>{const el=document.createElement('div');el.className='scan-zone'+(ids.includes(l.id)?' is-highlighted':'');el.dataset.scanLine=String(i);el.title=l.id;el.setAttribute('aria-hidden','true');const b=l.bbox;viewer.addOverlay({element:el,location:viewer.world.getItemAt(0).imageToViewportRectangle(b[0],b[1],b[2],b[3]),checkResize:false});overlayTrackers.push(new OpenSeadragon.MouseTracker({element:el,clickHandler:event=>{if(event.quick){selectLine(i);setTab('radky');}}}));});
  }
  function proposeHtr() {
    const l=selectedLine();if(!l)return;
    const url=new URL(DATA.document.reader);url.searchParams.set('vrstva','radky');url.hash=page().folio+'-'+l.id;
    window.dispatchEvent(new CustomEvent('manuscripty:propose-htr',{detail:{document_id:page().document_id||DATA.document.id,manuscript:page().manuscript||DATA.document.shelfmark||DATA.title,folio:page().folio,line_id:l.id,source_segment_ids:l.source_segment_ids,bbox:l.bbox,source_sha256:page().source_sha256,coordinate_source:page().coordinate_source,width:page().width,height:page().height,models:page().models,model:state.model,raw_htr:l.raw_htr,source_url:url.href,crop_url:l.image}}));
  }
  function proposeSegmentation() {
    const p=page();if(!p.tiles||!p.source_sha256)return;const url=new URL(DATA.document.reader);url.searchParams.set('vrstva','radky');url.hash=p.folio+(selectedLine()?'-'+selectedLine().id:'');
    window.dispatchEvent(new CustomEvent('manuscripty:propose-segmentation',{detail:{manuscript:p.manuscript||DATA.document.shelfmark||DATA.title,document_id:p.document_id||DATA.document.id,document_uri:p.document_uri||DATA.document.uri,folio:p.folio,width:p.width,height:p.height,source_sha256:p.source_sha256,source_original:p.source_original,coordinate_source:p.coordinate_source,source_url:url.href,preview_url:new URL(p.preview,location.href).href,tiles:{...p.tiles,tilesUrl:new URL(p.tiles.tilesUrl,location.href).href},selected_id:selectedLine()?.id||null,segments:p.lines.map(l=>({id:l.id,source_segment_ids:[...l.source_segment_ids],bbox:[...l.bbox]}))}}));
  }
  function applyZoom() {
    if (viewer && viewer.viewport) {
      if(state.zoom===1)viewer.viewport.goHome();else viewer.viewport.zoomTo(viewer.viewport.getHomeZoom()*state.zoom);
    }
    $('#zoom').textContent = Math.round(state.zoom * 100) + ' %';
  }
  function renderStage() {
    const p=page();$('#page-host').innerHTML='';$('#osd').hidden=false;
    if(!viewer) { viewer=OpenSeadragon({id:'osd',showNavigationControl:false,showNavigator:true,navigatorPosition:'TOP_RIGHT',crossOriginPolicy:'Anonymous',ajaxWithCredentials:false,maxZoomPixelRatio:2,gestureSettingsMouse:{clickToZoom:false},drawer:'canvas'}); viewer.addHandler('open',()=>{highlight();applyZoom();});viewer.addHandler('zoom',()=>{if(viewer.viewport)$('#zoom').textContent=Math.round(viewer.viewport.getZoom()/viewer.viewport.getHomeZoom()*100)+' %';});viewer.addHandler('open-failed',()=>{$('#page-host').textContent='Obraz se nepodařilo načíst. Textové vrstvy zůstávají dostupné.';}); }
    viewer.open({Image:{xmlns:'http://schemas.microsoft.com/deepzoom/2008',Url:p.tiles.tilesUrl,Format:'webp',Overlap:'1',TileSize:'512',Size:{Width:p.width,Height:p.height}}});
  }
  function renderLines() {
    const p = page();
    $('#htr-choice').innerHTML = Object.entries(p.models).map(([key,label]) => '<option value="' + esc(key) + '"' + (key === state.model ? ' selected' : '') + '>' + esc(label) + '</option>').join('');
    $('#htr-choice').disabled=!p.lines.length;$('#line-choice').disabled=!p.lines.length;
    $('#row-count').textContent = p.kind==='binding'?'Zatím bez HTR':p.lines.length + (p.kind === 'physical_lines' ? ' fyzických řádků' : ' segmentů');
    $('#lines').innerHTML = p.lines.map((l,i) => '<li class="line' + (i === state.line ? ' is-selected' : '') + '"><button type="button" class="line-btn" data-line="' + i + '" aria-expanded="' + (i === state.line) + '"><span class="line-n">' + (i + 1) + '</span><span class="line-text">' + esc(l.raw_htr[state.model] ?? 'Výstup není dostupný') + '</span></button>' + (i === state.line ? '<div class="line-actions"><button type="button" class="btn btn--sm" data-open="radky">Řádková analýza</button><button type="button" class="btn btn--sm" data-open="vyklad">Předloha a čeština</button></div>' : '') + (proposalLinks(l.id)?'<p class="line-actions">'+proposalLinks(l.id)+'</p>':'') + '</li>').join('');
    $('#line-choice').innerHTML = p.lines.map((l,i) => '<option value="' + i + '"' + (i === state.line ? ' selected' : '') + '>' + (i + 1) + ' · ' + esc(l.id) + '</option>').join('');
  }
  function renderAnalysis() {
    const l = selectedLine();
    if (!l) { $('#line-analysis').textContent = page().kind==='binding'?'Pro tento snímek zatím nebyl vytvořen HTR přepis.':'Na této straně není vybraný text.'; return; }
    const raw = Object.entries(l.raw_htr).map(([key,text]) => '<h3>' + esc(page().models[key] || key) + '</h3><div class="layer-raw">' + esc(text) + '</div>').join('');
    const hasDifferences = new Set(Object.values(l.raw_htr)).size > 1;
    const words = l.words.length ? '<h3>Diplomatické čtení a rozvedení po slovech</h3><p class="sample-notice">Slovní souřadnice nebyly určeny. Odkaz na obraz se vztahuje k celému řádku.</p><div class="word-table-wrap"><table class="word-table"><thead><tr><th>Diplomatické čtení</th><th>Rozvedení / alternativy</th><th>Stav a zdůvodnění</th></tr></thead><tbody>' + l.words.map(w => '<tr' + (w.status === 'uncertain' ? ' class="is-unsure"' : '') + '><td class="reading-word">' + esc(w.diplomatic) + '<div class="layer-id">' + esc(w.id) + '</div></td><td class="reading-word">' + esc(w.expanded === null ? '⟦rozvedení neurčeno⟧' : w.expanded) + (w.alternatives?.length ? '<div class="word-evidence">Alternativy: ' + esc(notesText(w.alternatives)) + '</div>' : '') + '</td><td>' + esc(statusLabel(w.status)) + '<details class="word-evidence"><summary>Podklady a poznámky</summary><ul>' + (w.evidence || []).map(e => '<li><strong>' + esc(e.source || e.type || 'Podklad') + '</strong>: ' + esc(e.note || asText(e)) + '</li>').join('') + '</ul></details></td></tr>').join('') + '</tbody></table></div>' : '<p class="layer-notes">Samostatné diplomatické čtení po slovech pro tuto stranu nebylo vytvořeno. Dostupná je pasážová rekonstrukce a její poznámky.</p>';
    const passages = linkedPassages().map(p => '<h3>' + esc(p.title) + '</h3>' + (p.notes ? '<p class="layer-notes">' + esc(p.notes) + '</p>' : '')).join('');
    $('#line-analysis').innerHTML = '<article class="analysis-card"><h2>' + (page().kind === 'physical_lines' ? 'Fyzický řádek ' : 'Segment ') + (state.line + 1) + '</h2><p class="layer-id">' + esc(l.id) + ' · původní segmenty: ' + esc(l.source_segment_ids.join(', ')) + '</p><a href="' + esc(l.image) + '" target="_blank" rel="noopener"><img class="line-crop" src="' + esc(l.image) + '" alt="Výřez WebP Q90 v původních rozměrech ' + esc(l.id) + '"></a><p class="sample-notice">' + (hasDifferences ? 'HTR kandidáti se liší.' : 'HTR kandidáti se shodují.') + ' Přesnost ani kalibrované procento jistoty není změřeno.</p>' + (proposalLinks(l.id)?'<p class="sample-notice">'+proposalLinks(l.id)+'</p>':'') + raw + (l.medusa_joined_segments ? '<p class="sample-notice">Medusa: dva původní segmentové výstupy jsou zobrazené za sebou v pořadí uvedených zdrojových ID. Nejde o nové rozpoznání celého fyzického řádku.</p>' : '') + '<button type="button" class="btn btn--primary" data-propose-htr>Navrhnout opravu HTR</button><button type="button" class="btn" data-propose-segmentation>Navrhnout opravu segmentace</button>' + (l.flags.length ? '<p class="layer-id">Příznaky: ' + esc(l.flags.join(', ')) + '</p>' : '') + (l.note ? '<p class="layer-notes">' + esc(l.note) + '</p>' : '') + words + renderReadingAddenda(page().reading_addenda, {lineId:l.id, idPrefix:'analysis'}) + passages + '<button type="button" class="btn" data-open="vyklad">Zobrazit rekonstrukci a překlad související pasáže</button></article>';
  }
  function renderReading() {
    const scope = $('#reading-scope').value;
    const language = $('#reading-language').value;
    const passages = scope === 'all' ? page().passages : linkedPassages();
    const supplemental = renderSupplementalReadings(page().supplemental_readings, {language, pageLanguage:page().language || 'la'});
    $('#reading-passages').innerHTML = renderReadingAddenda(page().reading_addenda, {language, lineId:scope === 'all' ? null : selectedLine()?.id, idPrefix:'interpretation'}) + (passages.length ? passages.map(p => '<article class="reading-card" id="reading-' + esc(p.id) + '"><h2>' + esc(p.title) + '</h2><p class="layer-id">' + esc(p.id) + ' · pracovní návrh, bez odborné revize</p>' + (language !== 'czech' ? '<section lang="' + esc(p.language || page().language || 'la') + '"><h3>Rekonstrukce (jazyk předlohy)</h3><p class="layer-reading">' + esc(p.latin) + '</p></section>' : '') + (language !== 'latin' ? '<section lang="cs"><h3>Český překlad</h3><p class="layer-reading">' + esc(p.czech) + '</p></section>' : '') + (p.notes ? '<h3>Poznámky a nejistoty</h3><p class="layer-notes">' + esc(p.notes) + '</p>' : '') + '<details><summary>Řádky / segmenty obrazového podkladu (' + p.line_ids.length + ')</summary><div class="linked-lines">' + p.line_ids.map(id => '<button type="button" data-source-id="' + esc(id) + '">' + esc(id) + '</button>').join('') + '</div><button type="button" class="btn btn--sm" data-passage="' + esc(p.id) + '">Zvýraznit celou pasáž ve skenu</button></details>' + (p.operations.length ? '<details><summary>Rekonstrukční zásahy (' + p.operations.length + ')</summary>' + p.operations.map(o => '<p class="layer-notes"><span class="layer-id">' + esc(o.id) + '</span> · ' + esc(o.base) + ' → ' + esc(o.proposed) + '<br>' + esc(o.note_cs) + '</p>').join('') + '</details>' : '') + '</article>').join('') : '<p class="layer-notes">'+(page().kind==='binding'?'Pro tento snímek zatím nebyl vytvořen HTR ani rekonstrukce přiřazená k HTR řádkům.':'K vybranému řádku není přiřazena interpretační pasáž.')+'</p>') + supplemental;
  }
  function renderProcessing() {
    const p = page();
    $('#processing-info').innerHTML = '<h2>Vrstvy a podklady strany ' + esc(p.folio) + '</h2><p class="prose">' + esc(p.analysis_scope) + '</p><p class="layer-notes">' + esc(notesText(p.notes) || 'Původní HTR je zachované odděleně od pracovní interpretace.') + '</p><p class="prose">⟦text?⟧ označuje nejisté čtení, [text?] domněnku; nevyřešený text neprokazuje fyzickou ztrátu. Ani neoznačená slova nejsou odborně ověřená.</p><p class="prose">' + esc(DATA.processing_note || 'Rozsah dostupných vrstev je uveden u jednotlivých stran. Původní HTR je zachované odděleně od pracovního výkladu.') + '</p><h3>Podkladové soubory</h3><ul class="download-list">' + p.downloads.map(d => '<li><a href="' + esc(d.href) + '">' + esc(d.name) + '</a></li>').join('') + '</ul><p class="layer-id">SHA-256 původního skenu: ' + esc(p.source_sha256) + '</p><p class="sample-notice">Obrazové dlaždice a výřezy jsou prezentační WebP Q90, se ztrátovou kompresí. Archivní originály a původní PNG zůstávají uchovány lokálně. Publikace nemění odborný stav četby.</p>';
    $('#toc').innerHTML = p.passages.map(passage => '<li><button type="button" data-toc-passage="' + esc(passage.id) + '"><span>' + esc(passage.title) + '</span><span class="f">' + esc(p.folio) + '</span></button></li>').join('');
  }
  function setTab(tab, focus = false, reveal = true) {
    if (tab === 'text') tab = textView;
    if (tab === 'about') tab = aboutView;
    if (!TABS.includes(tab)) return;
    if (reveal) window.dispatchEvent(new CustomEvent('manuscripty:show-panel'));
    state.tab = tab;
    const group = groupOf(tab);
    if (group === 'text') textView = tab;
    if (group === 'about') aboutView = tab;
    GROUPS.forEach(name => {
      const active = group === name, button = $('#tab-' + name);
      button.setAttribute('aria-selected', String(active));
      button.tabIndex = active ? 0 : -1;
      $('#panel-' + name).hidden = !active;
    });
    TEXT_VIEWS.forEach(name => {
      const active = textView === name, button = $('#view-' + name);
      button.setAttribute('aria-selected', String(active));
      button.tabIndex = active ? 0 : -1;
      $('#panel-' + name).hidden = !active;
    });
    if (focus) $('#tab-' + group).focus({preventScroll:true});
    if (group === 'about') scrollWithin($('#text-panel'), $('#panel-' + tab));
    highlight(); setHash(); updateCitation();
    window.dispatchEvent(new CustomEvent('manuscripty:tab',{detail:{tab:state.tab,group,folio:page().folio}}));
  }
  function selectLine(i) {
    const count = page().lines.length;
    state.line = count ? Math.max(0, Math.min(count - 1, i)) : -1;
    state.passage = null;
    renderLines(); renderAnalysis(); renderReading(); highlight(); setHash(); updateCitation();
  }
  async function goToPage(i, line = 0) {
    const index=Math.max(0,Math.min(PAGES.length-1,i)),request=++loadingRequest;
    $('#stage').setAttribute('aria-busy','true');$('#load-status').textContent='Načítám '+(PAGES[index].label||PAGES[index].folio)+'…';
    try {
      if(!PAGES[index].lines) { const response=await fetch(PAGES[index].data+'?v=20261021-2');if(!response.ok)throw new Error('HTTP '+response.status);const data=await response.json();Object.assign(PAGES[index],data); }
      if(request!==loadingRequest)return;
      state.page=index;
      if(typeof line==='string'){let n=page().lines.findIndex(l=>l.id===line);if(n<0&&/^l\d+$/.test(line))n=Number(line.slice(1))-1;line=n<0?0:n;}
      if(Object.keys(page().models).length&&!page().models[state.model])state.model=Object.keys(page().models)[0];
      state.zoom=1;state.passage=null;state.line=page().lines.length?Math.max(0,Math.min(page().lines.length-1,line)):-1;
      document.querySelectorAll('.thumb').forEach((t,n)=>{if(n===state.page)t.setAttribute('aria-current','page');else t.removeAttribute('aria-current');});
      $('#folio').textContent=page().folio;$('#folio-prefix').hidden=page().kind==='binding';$('#total').textContent=String(PAGES.length);$('#page-choice').value=String(state.page);
      $('#ms-sub').textContent=PAGES.length+' snímků · pracovní čtení bez odborné revize';
      $('#suggest-btn').disabled=!page().lines.length;$('#prev').disabled=state.page===0;$('#next').disabled=state.page===PAGES.length-1;
      renderStage();renderLines();renderAnalysis();renderReading();renderProcessing();setTab(state.tab,false,false);setHash();updateCitation();
      $('#load-status').textContent=(page().kind==='binding'?(page().label+' · zatím bez HTR'):page().blank?'Bez vybraného hlavního textu':page().lines.length+' řádků / segmentů · '+page().passages.length+' pasáží')+(page().supplemental_readings?.length?' · '+page().supplemental_readings.length+' samostatných čtení':'');
      scrollWithin($('#thumbs'), document.querySelector('.thumb[aria-current="page"]'));
    }catch(error){if(request===loadingRequest)$('#load-status').textContent='Načtení selhalo. Zvolte stranu znovu nebo obnovte stránku.';}
    finally{if(request===loadingRequest)$('#stage').removeAttribute('aria-busy');}
  }
  $('#ms-title').textContent = shelfmark;
  $('#ms-title').href=DATA.document.uri;
  document.title=shelfmark+' · řádková analýza a překlad';
  document.querySelector('link[rel=canonical]').href=DATA.document.reader;
  document.querySelector('meta[property="og:url"]').content=DATA.document.reader;
  document.querySelector('meta[property="og:title"]').content=document.title;
  document.querySelector('meta[property="og:image"]').content=DATA.document.preview || PAGES.find(p=>p.folio===(DATA.document.id==='vkol-m-i-259'?'1r':'5r'))?.preview || PAGES[0].preview;
  document.querySelectorAll('[data-document-link]').forEach(a=>a.href=DATA.document.uri);
  $('#document-permalink').value=DATA.document.uri;
  $('#document-tei').href=DATA.document.tei;
  $('#document-citation').textContent='Vědecká knihovna v Olomouci, '+shelfmark+'. Pracovní přepis, rekonstrukce a český překlad bez odborné revize.';
  $('#ms-origin-shelfmark').textContent=shelfmark;
  $('#document-description-title').textContent=DATA.title;
  $('#description-shelfmark').textContent=shelfmark;
  if(DATA.description_cs)$('#document-description-detail').textContent=DATA.description_cs;
  document.querySelectorAll('[data-summary-link]').forEach(a=>a.href=DATA.summary_url || DATA.document.uri+'#ai-shrnuti');
  if(DATA.document.id!=='vkol-m-ii-220'){
    $('#structure-basis').textContent=DATA.structure_basis_cs || 'Katalogové členění podle dodaného digitalizačního popisu; názvy interpretačních pasáží jsou pracovní návrhy AI. Rozsahy děl se mohou překrývat.';
    $('#line-reading-notice').textContent='Pracovní čtení bez odborné revize. Zobrazujeme oba původní HTR, příznaky a pasážové poznámky; slovní geometrie není určena.';
    $('#reading-language option[value=both]').textContent='Předloha a čeština';
    $('#reading-language option[value=latin]').textContent='Rekonstrukce v jazyce předlohy';
    $('#view-vyklad').textContent='Předloha a čeština';
  }

  $('#thumbs').innerHTML = PAGES.map((p,i) => '<button type="button" class="thumb" data-page="' + i + '" aria-label="' + esc(p.label || 'Strana '+p.folio) + '"><img class="mini" src="' + esc(p.preview) + '" alt="" loading="lazy"><span>' + esc(p.label || p.folio) + '</span></button>').join('');
  $('#thumbs').addEventListener('click',e => { const button=e.target.closest('[data-page]'); if(button) goToPage(Number(button.dataset.page)); });
  $('#lines').addEventListener('click',e => { const button=e.target.closest('[data-line]'); if(button) selectLine(Number(button.dataset.line)); });
  $('#htr-choice').addEventListener('change',e => { state.model=e.target.value; renderLines(); });
  $('#line-choice').addEventListener('change',e => selectLine(Number(e.target.value)));
  $('#reading-scope').addEventListener('change',() => { state.passage=null; renderReading(); highlight(); });
  $('#reading-language').addEventListener('change',renderReading);
  document.addEventListener('click',e => {
    const correction=e.target.closest('[data-propose-htr]');if(correction)proposeHtr();
    if(e.target.closest('[data-propose-segmentation]'))proposeSegmentation();
    const open=e.target.closest('[data-open]'); if(open) setTab(open.dataset.open);
    const line=e.target.closest('[data-source-id]'); if(line) { selectLine(page().lines.findIndex(l => l.id === line.dataset.sourceId)); setTab('radky'); }
    const passage=e.target.closest('[data-passage]'); if(passage) { state.passage=passage.dataset.passage; highlight(); }
    const toc=e.target.closest('[data-toc-passage]'); if(toc) { const p=page().passages.find(p=>p.id===toc.dataset.tocPassage); if(p) { selectLine(page().lines.findIndex(l=>l.id===p.line_ids[0])); $('#reading-scope').value='linked'; renderReading(); setTab('vyklad'); } }
  });
  function bindTablist(selector, names, prefix, current) {
    const list=$(selector);
    list.addEventListener('click', e=>{const button=e.target.closest('[role="tab"]');if(button)setTab(button.id.slice(prefix.length));});
    list.addEventListener('keydown', e=>{
      if(!e.target.matches('[role="tab"]'))return;
      const i=names.indexOf(e.target.id.slice(prefix.length));
      const next=e.key==='ArrowRight'?names[(i+1)%names.length]:e.key==='ArrowLeft'?names[(i+names.length-1)%names.length]:e.key==='Home'?names[0]:e.key==='End'?names.at(-1):null;
      if(next){e.preventDefault();setTab(next);$('#'+prefix+next).focus({preventScroll:true});}
    });
  }
  bindTablist('.tabs',GROUPS,'tab-',()=>groupOf(state.tab));
  bindTablist('.text-views',TEXT_VIEWS,'view-',()=>textView);
  $('#suggest-btn').addEventListener('click',()=>{setTab('radky');proposeHtr();});
  $('#prev').addEventListener('click',()=>goToPage(state.page-1));$('#next').addEventListener('click',()=>goToPage(state.page+1));
  document.querySelectorAll('[data-goto-tab]').forEach(b=>b.addEventListener('click',()=>setTab(b.dataset.gotoTab,true)));
  document.querySelectorAll('[data-zoom]').forEach(b=>b.addEventListener('click',()=>{state.zoom=b.dataset.zoom==='fit'?1:Math.max(.5,Math.min(3,state.zoom*(b.dataset.zoom==='in'?1.25:.8)));applyZoom();}));
  document.addEventListener('keydown',e=>{if(e.defaultPrevented||document.querySelector('dialog[open]'))return;if(e.altKey||e.ctrlKey||e.metaKey||e.target.closest('input,textarea,select,button,[role="tablist"],[role="separator"]'))return;if(e.key==='ArrowLeft'){e.preventDefault();goToPage(state.page-1);}if(e.key==='ArrowRight'){e.preventDefault();goToPage(state.page+1);}});
  window.addEventListener('manuscripty:navigate-structure',async e=>{const target=e.detail,index=PAGES.findIndex(p=>p.folio===target.folio);if(index<0)return;await goToPage(index,target.line_id||0);if(page().folio===target.folio)setTab(target.tab==='vyklad'?'vyklad':'struktura');});
  window.addEventListener('hashchange',()=>{const h=readHash();goToPage(h.page,h.line);});
  $('#copy-citation').addEventListener('click',async e=>{try{await navigator.clipboard.writeText($('#citation').textContent);e.currentTarget.textContent='Zkopírováno';}catch{e.currentTarget.textContent='Označte citaci a zkopírujte ji';}});
  $('#page-choice').innerHTML=PAGES.map((p,i)=>'<option value="'+i+'">'+esc(p.label||p.folio)+(p.blank?' · bez vybraného textu':'')+'</option>').join('');
  $('#page-choice').addEventListener('change',e=>goToPage(Number(e.target.value)));
  const initial=readHash();
  const initialTab=new URLSearchParams(location.search).get('vrstva');
  if(TABS.includes(initialTab))state.tab=initialTab;
  goToPage(initial.page,initial.line);
}).catch(() => { document.getElementById('load-status').textContent='Rukopis se nepodařilo načíst. Obnovte stránku nebo přejděte na úvod.'; });
