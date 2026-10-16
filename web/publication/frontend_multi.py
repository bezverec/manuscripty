"""Integrate the five reviewed frontend phases with a second manuscript."""
from pathlib import Path
import hashlib,html,re
REV='20261012-6'
DOC='vkol-m-ii-153'

def decorate_record(record,doc,description):
 """Keep one canonical description and safe, local filtered search on both records."""
 from catalogue_records import without_fixity_notice
 record=without_fixity_notice(record)
 title=html.escape(doc.get('title') or doc.get('display_title_cs',''),quote=True)
 description=html.escape(description,quote=True)
 image='https://rukopisy-data.digitalizaty.cz/'+('v2/'+DOC+'/previews/5r.webp' if doc['id']==DOC else 'v1/previews/20v.webp')
 for name in ['description']:
  record=re.sub(r'<meta name="'+name+r'"[^>]*>','',record)
 for prop in ['og:title','og:description','og:url','og:image']:
  record=re.sub(r'<meta property="'+prop+r'"[^>]*>','',record)
 extra=f'<meta name="description" content="{description}"><meta property="og:title" content="{title}"><meta property="og:description" content="{description}"><meta property="og:url" content="{html.escape(doc["uri"],quote=True)}"><meta property="og:image" content="{image}"><link rel="icon" type="image/svg+xml" href="/favicon.svg?v={REV}">'
 if '/search.js' not in record:extra+='<link rel="stylesheet" href="/folio.css?v=20261012-3"><script type="module" src="/search.js?v=20261012-3"></script>'
 record=record.replace('</head>',extra+'</head>')
 if 'data-folio-search' not in record:
  search=f'<section class="folio-search" data-folio-search data-document="{doc["id"]}"><h2>Hledat v textech tohoto rukopisu</h2><form role="search"><label for="folio-search-query">Slovo nebo část textu<input class="field" id="folio-search-query" name="q" type="search" required></label><button class="btn btn--primary" type="submit">Hledat</button></form><p class="folio-search-status" role="status" aria-live="polite"></p><ol class="folio-search-results"></ol><button class="btn folio-search-more" type="button" data-search-more hidden>Další výsledky</button><noscript><p>Vyhledávání vyžaduje JavaScript. Textové stránky lze číst bez něj.</p></noscript></section>'
  record=record.replace('</main>',search+'</main>')
 from digitization_support import decorate_record as support_record
 return support_record(record)
def write(path,text):
 if path.suffix=='.html':
  from markup import normalize_html
  text=normalize_html(text)
 path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text,encoding='utf8',newline='\n')
def once(text,old,new):
 if text.count(old)!=1:raise ValueError('Frontend anchor changed: '+old[:90])
 return text.replace(old,new,1)
def patch_frontend(base,out,legacy_doc):
 originals={}
 def load(name):
  raw=(base/name).read_bytes();originals[name]=hashlib.sha256(raw).hexdigest();return raw.decode('utf8')
 j=load('rukopis.js')
 j=once(j,'(() => {','window.MANUSCRIPT_READY.then(() => {')
 j=once(j,'})();',"}).catch(() => { document.getElementById('load-status').textContent='Rukopis se nepodařilo načíst. Obnovte stránku nebo přejděte na úvod.'; });")
 j=once(j,'  const PAGES = DATA.pages;',"  const PAGES = DATA.pages;\n  const shelfmark=DATA.document.shelfmark || DATA.title;")
 j=j.replace("'Vědecká knihovna v Olomouci, M II 220, ' +","'Vědecká knihovna v Olomouci, ' + shelfmark + ', ' +")
 j=j.replace("new URL('https://rukopisy.digitalizaty.cz/rukopis')",'new URL(DATA.document.reader)')
 old='<p class="prose">Všech 664 textových stran má kandidáty CATMuS a Medusa; u 20v je navíc zachovaný Tridis a podrobná slovní analýza. Dva fyzické řádky 20v spojují původní segmentové výstupy Medusy; zdrojové segmenty zůstávají uvedené. Ostatní strany mají pasážový výklad. Rozsah vrstev se mezi etapami liší.</p>'
 j=once(j,old,'<p class="prose">\' + esc(DATA.processing_note || \'Rozsah dostupných vrstev je uveden u jednotlivých stran. Původní HTR je zachované odděleně od pracovního výkladu.\') + \'</p>')
 j=once(j,'<section lang="la"><h3>Latinská rekonstrukce</h3>','<section lang="\' + esc(p.language || page().language || \'la\') + \'"><h3>Rekonstrukce (jazyk předlohy)</h3>')
 j=once(j,"  $('#ms-title').textContent = DATA.title;","""  $('#ms-title').textContent = shelfmark;
  $('#ms-title').href=DATA.document.uri;
  document.title=shelfmark+' · řádková analýza a překlad';
  document.querySelector('link[rel=canonical]').href=DATA.document.reader;
  document.querySelector('meta[property="og:url"]').content=DATA.document.reader;
  document.querySelector('meta[property="og:title"]').content=document.title;
  document.querySelector('meta[property="og:image"]').content=PAGES.find(p=>p.folio==='5r')?.preview || PAGES[0].preview;
  document.querySelectorAll('[data-document-link]').forEach(a=>a.href=DATA.document.uri);
  $('#document-permalink').value=DATA.document.uri;
  $('#document-tei').href=DATA.document.tei;
  $('#document-citation').textContent='Vědecká knihovna v Olomouci, '+shelfmark+'. Pracovní přepis, rekonstrukce a český překlad bez odborné revize.';
  $('#ms-origin-shelfmark').textContent=shelfmark;
  $('#document-description-title').textContent=DATA.title;
  $('#description-shelfmark').textContent=shelfmark;
  if(DATA.description_cs)$('#document-description-detail').textContent=DATA.description_cs;
  document.querySelectorAll('[data-summary-link]').forEach(a=>a.href=DATA.document.uri+'#ai-shrnuti');
  if(DATA.document.id==='vkol-m-ii-153'){
    $('#structure-basis').textContent='Katalogové členění podle dodaného digitalizačního popisu; názvy interpretačních pasáží jsou pracovní návrhy AI. Rozsahy děl se mohou překrývat.';
    $('#line-reading-notice').textContent='Pracovní čtení bez odborné revize. Zobrazujeme oba původní HTR, příznaky a pasážové poznámky; slovní geometrie není určena.';
    $('#reading-language option[value=both]').textContent='Předloha a čeština';
    $('#reading-language option[value=latin]').textContent='Rekonstrukce v jazyce předlohy';
    $('#view-vyklad').textContent='Předloha a čeština';
  }
""")
 j=re.sub(r'\?v=20261012-[1-5]', '?v='+REV,j)
 write(out/'rukopis.js',j)
 h=load('rukopis.html')
 h=re.sub(r'src="pilot-data\.js\?v=[^"]+"','src="document-loader.js?v='+REV+'"',h,count=1)
 for old,new in [
 (' · M II 220</p>',' · <span id="ms-origin-shelfmark">M II 220</span></p>'),
 ('<h2>Rukopis M II 220</h2>','<h2 id="document-description-title">Rukopis M II 220</h2>'),
 ('signatura M II 220.','signatura <span id="description-shelfmark">M II 220</span>.'),
 ('<p class="prose">Veřejný pilot obsahuje','<p id="document-description-detail" class="prose">Veřejný pilot obsahuje'),
 ('<p class="citation">Vědecká knihovna','<p id="document-citation" class="citation">Vědecká knihovna'),
 ('href="/tei/vkol-m-ii-220.xml" download','id="document-tei" href="/tei/vkol-m-ii-220.xml" download'),
 ('<p class="sample-notice">Pracovní obsah','<p id="structure-basis" class="sample-notice">Pracovní obsah'),
 ('<p class="notice">Pracovní čtení','<p id="line-reading-notice" class="notice">Pracovní čtení')]:h=once(h,old,new)
 h=h.replace('href="/rukopisy/vkol-m-ii-220"','data-document-link href="/rukopisy/vkol-m-ii-220"')
 h=h.replace('href="/summary"','data-summary-link href="/summary"')
 h=re.sub(r'\?v=20261012-[1-5]', '?v='+REV,h)
 h=h.replace('rukopis.js?v='+REV, 'rukopis.js?v=20261014-2')
 from digitization_support import decorate_viewer, install_assets
 write(out/'rukopis.html',decorate_viewer(h))
 install_assets(out)
 s=load('structure.js')
 s=once(s,"fetch('structure.json?v=20261011-6')","fetch((window.PILOT_DATA.structure_url || 'structure.json')+'?v="+REV+"')")
 s=once(s,"  host.innerHTML=groups.length?","  const catalogue=(structure.catalogue_items||[]).filter(i=>!query||normalized(i.title+' '+i.from+' '+i.to).includes(query)).map(i=>'<li><button type=\"button\" data-structure-folio=\"'+esc(i.from)+'\">'+esc(i.title)+'</button> · '+esc(i.from+'–'+i.to)+'</li>').join('');\n  host.innerHTML=(catalogue?'<details class=\"structure-group\" open><summary>Katalogový obsah kodexu</summary><ol>'+catalogue+'</ol></details>':'')+(groups.length?")
 s=once(s,"jiné folio nebo slovo.</p>';","jiné folio nebo slovo.</p>');")
 write(out/'structure.js',s)
 # Copy shared reviewed modules; all identity handling already exists in phase 4.
 for f in ['proposal-core.mjs','segmentation-core.mjs','issue-form-core.mjs','corrections.js','segmentation.js','header-actions.js','feature-config.js','iiif-link.js']:
  code=load(f);code=re.sub(r'\?v=20261012-[1-5]', '?v='+REV,code);write(out/f,code)
 loader="""(() => {
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
"""
 write(out/'document-loader.js',loader)
 css=load('styles.css')+'''
/* Katalog více rukopisů. */
.catalogue-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:28px}
.catalogue-card{border:1px solid var(--line);padding:20px;min-width:0}
.catalogue-card img{display:block;width:100%;height:280px;object-fit:contain;background:#eeece7;margin-bottom:20px}
.catalogue-card h3{font:28px var(--serif);margin:0 0 8px}
.catalogue-card .hero-actions{gap:8px}
.catalogue-card .btn{font-size:13px;padding:8px 10px}
.catalogue-card p{line-height:1.6}
.catalogue-meta{font-size:13px;color:var(--muted)}
.hero .folio-search{margin-top:24px;max-width:760px}
.hero .folio-search h2{font-size:20px}
@media(max-width:760px){.catalogue-grid{grid-template-columns:1fr}.catalogue-card img{height:240px}}
'''
 write(out/'styles.css',css)
 oldhome=load('index.html')
 search=re.search(r'<section class="container folio-search".*?</section>',oldhome,re.S).group().replace('class="container folio-search"','class="folio-search"').replace('Hledat v přepisech rukopisu','Hledat v textech rukopisů')
 cards=''
 for ident,shelf,date,img in [('vkol-m-ii-220','M II 220','15. století podle katalogů','https://rukopisy-data.digitalizaty.cz/v1/previews/20v.webp'),(DOC,'M II 153','Druhá polovina 14. století podle katalogu','https://rukopisy-data.digitalizaty.cz/v2/'+DOC+'/previews/5r.webp')]:
  reader='/rukopis'+('?doc='+DOC if ident==DOC else '')
  cards+=f'''<article class="catalogue-card"><a href="/rukopisy/{ident}" aria-label="Záznam rukopisu {shelf}"><img src="{img}" alt="Náhled rukopisu {shelf}" loading="lazy"></a><p class="eyebrow">Vědecká knihovna v Olomouci</p><h3>{shelf} · Textus varii</h3><p>Sbírka různých textů</p><p class="catalogue-meta">{date} · latinský rukopis</p><p>Původní HTR, obrazové výřezy, pracovní rekonstrukce a český překlad.</p><div class="hero-actions"><a class="btn btn--primary" href="{reader}">Prohlížet rukopis</a><a class="btn" href="/rukopisy/{ident}">Přehled a zdroje</a></div></article>'''
 home=f'''<!doctype html><html lang="cs"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Rukopisy · snímek po snímku</title><meta name="description" content="Rukopisy Vědecké knihovny v Olomouci: digitální obrazy, původní HTR, pracovní rekonstrukce a české překlady."><link rel="canonical" href="https://rukopisy.digitalizaty.cz/"><link rel="icon" type="image/svg+xml" href="/favicon.svg?v={REV}"><link rel="stylesheet" href="/styles.css?v={REV}"><link rel="stylesheet" href="/folio.css?v=20261012-3"><script type="module" src="/search.js?v=20261012-3"></script><meta property="og:title" content="Rukopisy, snímek po snímku."><meta property="og:description" content="Přepis s pomocí AI. Opravy od uživatelů. Dva rukopisy z fondů Vědecké knihovny v Olomouci."><meta property="og:url" content="https://rukopisy.digitalizaty.cz/"><meta property="og:image" content="https://rukopisy-data.digitalizaty.cz/v1/previews/20v.webp"></head><body>
<header class="site-header"><div class="container"><a class="brand" href="/"><svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M3 5.5c3-1.3 6-1.3 9 .5v13c-3-1.8-6-1.8-9-.5zM21 5.5c-3-1.3-6-1.3-9 .5v13c3-1.8 6-1.8 9-.5z"></path></svg>Rukopisy</a><nav class="site-nav" aria-label="Hlavní navigace"><a href="#rukopisy">Rukopisy</a><a href="#pilot">Přepis a opravy</a><a href="#o-pilotu">O projektu</a></nav></div></header>
<main><section class="hero"><div class="container"><p class="eyebrow">Digitální obrazy · pracovní textové vrstvy</p><h1>Rukopisy, snímek po snímku.</h1><p class="lead">Prohlížejte rukopisy z fondů <a href="https://www.vkol.cz/">Vědecké knihovny v Olomouci</a>. Porovnávejte obraz s původními přepisy HTR a čtěte pracovní rekonstrukce a české překlady.</p>{search}<p class="stats">2 rukopisy · 874 snímků · pracovní návrhy bez odborné revize</p></div></section>
<section class="section" id="rukopisy"><div class="container"><div class="section-head"><h2 class="h2">Rukopisy</h2><span class="muted">Sbírka Vědecké knihovny v Olomouci</span></div><div class="catalogue-grid">{cards}</div></div></section>
<section class="pilot" id="pilot"><div class="container"><div class="section-head"><div><h2>Přepis s pomocí AI. Opravy od uživatelů.</h2><p>Vyberte rukopis, stranu a řádek. U obrazu můžete porovnat původní výstupy CATMuS a Medusa, pracovní rekonstrukci, český překlad a označené nejistoty.</p></div><a class="badge" href="https://github.com/bezverec/manuscripty/issues">Návrhy oprav · GitHub / JSON</a></div><ol class="steps"><li><span class="num">1</span><h3>Obraz a HTR</h3><p>Dlaždice v původním rozlišení a zdrojové výřezy se zachovanými ID.</p></li><li><span class="num">2</span><h3>Rekonstrukce a překlad</h3><p>Smyslové úseky s odkazy na obraz, podklady a poznámky k nejistému čtení.</p></li><li><span class="num">3</span><h3>Návrhy oprav</h3><p>Opravy HTR i hranic segmentů lze uložit do JSON a předložit přes GitHub k posouzení.</p></li></ol></div></section>
<section class="section" id="o-pilotu"><div class="container"><h2 class="h2">O výzkumném projektu</h2><p>Projekt zkoumá možnosti místních HTR modelů a AI při zpřístupňování historických rukopisů. Přepisy, rekonstrukce, překlady a shrnutí jsou pracovní návrhy bez odborné revize. Shoda modelů ani validita XML nepotvrzují správnost čtení.</p><p>Katalogové údaje a jejich zdroje najdete u jednotlivých dokumentů. Uvedení knihovny jako instituce uchovávající rukopis neoznačuje výsledky AI za její odborné stanovisko.</p><p><a href="https://github.com/bezverec/manuscripty">Architektura, použité HTR technologie a metodika na GitHubu</a></p></div></section></main><footer class="site-footer"><div class="container">Rukopisy · výzkumný projekt Manuscripty</div></footer></body></html>'''
 write(out/'index.html',home)
 return originals
