"""Publish the completed fourth hundred-page batch and preserve prior 330 artifacts."""
from pathlib import Path
import json,hashlib,datetime,html
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
J=Path(__file__).resolve().parents[1];ROOT=J.parent;B=ROOT/'htr-fourth-100-pages';OLD=ROOT/'interpretation-third-100-pages'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for part in iter(lambda:f.read(8*1024*1024),b''):h.update(part)
 return h.hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
vm=read(J/'manifest.json');vv=read(J/'validation.json');usage=read(J/'usage-final.json')
assert vm['status']=='complete' and len(vm['pages'])==100
assert vv['status']=='passed' and vv['completed_pages']==100 and vv['tei_rng_valid_files']==100
assert all(c['all_segments_covered_once_in_order'] and c['tei_rng_valid'] and c['opened_native_tiles_pixel_verified'] and c['native_zone_coverage_verified'] for c in vv['checks'])
readback=read(J/'final-readback-validation.json')
assert readback['status']=='passed' and readback['tei_disk_relaxng_valid_files']==100
assert read(B/'validation.json')['status']=='passed'
assert read(B/'ocr-proarc/validation.json')['all_checks_passed']
prior=read(B/'previous-artifacts-sha256.json')
for path,digest in prior.items():assert sha(ROOT/path)==digest,'Prior artifact changed: '+path
pages=read(OLD/'completion-validation.json')['pages'].copy();assert len(pages)==330
raw={p['folio']:p for p in read(B/'manifest.json')['pages']}
for p in vm['pages']:
 f=p['folio'];src=raw[f];out=J/f;d=read(out/'reconstruction.json')
 assert sha(out/'reconstruction.json')==p['reconstruction_sha256']
 for n,digest in p['exports_sha256'].items():assert sha(out/n)==digest
 pages.append({'folio':f,'source_folder':B.name,'source_original':src['original'],'source_sha256':src['original_sha256'],'segments':p['segments'],'passages':p['passages'],'blank_selected_text':p['segments']==0,'review':J.name+'/'+f+'/review.html','raw_comparison':B.name+'/pages/'+f+'/comparison.html','human_reviewed':False})
assert len(pages)==430 and len({p['folio'] for p in pages})==430
key=lambda p:(int(p['folio'][:-1]),p['folio'][-1])
for name,target in [('reconstruction.la.txt','reconstruction-all.la.txt'),('translation.cs.txt','translation-all.cs.txt')]:
 texts=[]
 for p in sorted(pages,key=key):
  out=ROOT/Path(p['review']).parent
  if p['blank_selected_text']:content='Bez vybraného hlavního textu; viz záznam obrazové kontroly.\n'
  elif (out/name).exists():content=(out/name).read_text(encoding='utf-8')
  else:
   assert p['folio']=='20v' and out.name=='full-page-20v'
   field='reconstructed_la' if name.startswith('reconstruction') else 'translation_cs'
   content='\n\n'.join(x['title_cs']+'\n'+x[field] for x in read(out/'reconstruction.json')['passages'])+'\n'
  texts.append('=== Folio '+p['folio']+' ===\n'+content)
 (J/target).write_text('\n'.join(texts),encoding='utf-8')
segments=sum(p['segments'] for p in pages);new_segments=sum(p['segments'] for p in vm['pages']);passages=sum(p['passages'] for p in vm['pages']);tiles=sum(p['inspected_native_tiles'] for p in vm['pages']);blank=sum(p['blank_selected_text'] for p in pages)
assert blank>=3
truncated=[(p['folio'],line['id']) for p in raw.values() for line in read(B/'pages'/p['folio']/'medusa.candidates.json')['lines'] if line['hit_token_limit']]
assessment=f'''# Čtvrtá stovka: závěr rozšíření pilotu M II 220

Dokončeno dalších **100 různých stran, 184r–235r**. Celkem má pilot **430 stran a {segments:,} segmentů**: {len(pages)-blank} stran s vybraným hlavním textem a {blank} záznamů absence vybraného hlavního textu. Nová etapa přidává {new_segments} segmentů, {passages} výkladových pasáží a evidenci {tiles} skutečně otevřených nativních výřezů. Předchozích 330 stran zůstalo beze změny.

[Společný prohlížeč 430 stran](../pilot-index.html) · [Nových 100 návrhů](index.html) · [Souhrnná latina](reconstruction-all.la.txt) · [Souhrnná čeština](translation-all.cs.txt) · [HTR](../htr-fourth-100-pages/index.html) · [OCR pro ProArc](../htr-fourth-100-pages/ocr-proarc/README.md).

Oba místní kandidáti jsou CATMuS medieval 1.6.0 / Kraken a ENC-PSL/Medusa0.2Line-4B. Neupravené Unicode HTR se uchovává samostatně. Frontier asistent po kontrole nativních obrazů navrhl rozvedenou latinskou rekonstrukci a český překlad. Jde o pracovní návrhy s redakční interpunkcí a místní normalizací. Nejsou ověřeným diplomatickým přepisem. Také neoznačená slova zůstávají návrhem.

Výběr zahrnuje hlavní textové oblasti; všechny marginálie ani celý rukopis dosud zpracovány nejsou. Od 212v je text uspořádán do dvou sloupců; 212r obsahuje hlavní text pouze nahoře. Shoda modelů nepotvrzuje četbu a společná segmentace může ovlivnit oba kandidáty. Medusa dosáhla limitu generování u {len(truncated)} segmentů na {len({f for f,_ in truncated})} stranách; tyto řádky jsou zaznamenány v raw provenienci. Při obrazové kontrole se vyskytly také repetice a vynechání, které nebyly převzaty jako bezpečné čtení. ⟦text?⟧ označuje spornou četbu, [text?] domněnku a ⟦…⟧ nevyřešený text, nikoli doloženou fyzickou ztrátu. Atribuce autorům a citace nebyly porovnány s kritickými vydáními; Cappelli nebyl pro nové návrhy konzultován.

Všech 100 nových TEI exportů prošlo oficiálním Relax NG **TEI P5 4.12.0**. Kontroly ověřily pokrytí každého HTR segmentu právě jednou v pořadí, původní/pracovní SHA-256, nativní pixely otevřených výřezů, úplné pokrytí zvolených oblastí a místní odkazy. Zachováno všech {len(prior)} starších souborů podle SHA-256. Schematron se nespouštěl. [Interpretace](validation.json), [nezávislé opětovné načtení TEI](final-readback-validation.json), [úplnost](completion-validation.json), [raw HTR](../htr-fourth-100-pages/validation.json), [OCR](../htr-fourth-100-pages/ocr-proarc/validation.json).

Nových 100 párů TXT/ALTO má lokální XSD 3.0 a vybrané strukturální kontroly pro NDK OCR. Nejde o kompletní NDK PSP ani test importu do živého ProArcu. Případné náhrady slovní lokalizace obálkou řádku jsou jednotlivě označeny v OCR provenienci. Technická validace nepotvrzuje paleografickou ani překladovou správnost. Odborná revize a nezávislý referenční přepis nebyly provedeny; **CER/WER a procento správně přeloženého textu nejsou změřeny**.

Placená modelová API: **0 volání**. HTR běželo místně, interpretace v tomto chatu s třemi souběžnými asistenty. Zaokrouhlené sdílené týdenní využití účtu: {usage['weekly_start_used_percent']}→{usage['weekly_used_percent']} %, změna {usage['weekly_change_percentage_points']} procentních bodů, přibližně zbývá {usage['weekly_remaining_percent']} %. Přesné frontier tokeny ani peněžní API ekvivalent nejsou dostupné. Elektřina, amortizace a odborná revize nejsou oceněny. [Spotřeba](usage-report.md).
'''
(J/'assessment.md').write_text(assessment,encoding='utf-8')
(J/'usage-report.md').write_text(f'''# Spotřeba nové stovky

Rozsah: 100 nových HTR stran a 100 pracovních rekonstrukcí/překladů; výsledný pilot 430 stran. Hlavní asistent a 3 souběžní asistenti sdílejí účet.

|Ukazatel|Hodnota|
|---|---:|
|Týdenní využití na začátku|{usage['weekly_start_used_percent']} %|
|Týdenní využití při dokončení|{usage['weekly_used_percent']} %|
|Rozdíl|{usage['weekly_change_percentage_points']} procentních bodů|
|Přibližně zbývá|{usage['weekly_remaining_percent']} %|
|Placená modelová API|0 volání|
|Přesné frontier tokeny|Nedostupné|
|Elektřina a amortizace|Neměřeno|

Jde o zaokrouhlený odečet celého účtu, nikoli izolované tokenové měření. Předplatné není rozpočítáno na projekt. Místní Medusa tokeny nesouvisí s týdenním limitem frontier asistenta. [Počáteční odečet](../htr-fourth-100-pages/usage-start.json), [závěrečný odečet](usage-final.json), [místní časy a tokeny](../htr-fourth-100-pages/usage-report.md).
''',encoding='utf-8')
(J/'README.md').write_text('# Dokončeno dalších 100 stran\n\n[Prohlížeč 430 stran](../pilot-index.html) · [Nové návrhy](index.html) · [Závěr](assessment.md) · [Spotřeba](usage-report.md) · [Validace](validation.json).\n\nKaždá nová strana má původní HTR, pracovní latinu a češtinu, JSON, TEI P5 4.12.0 a obrazové podklady. Souhrnné TXT obsahují všech 430 stran. Všechny interpretace jsou proposed, bez odborné revize.\n',encoding='utf-8')
completion={'status':'pending_final_link_check','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'total_raw_pages':430,'total_segments':segments,'new_interpretation_records':100,'previous_interpretations_preserved':330,'text_pages_with_proposed_reconstruction_and_translation':430-blank,'blank_records':blank,'new_passages':passages,'opened_native_tiles':tiles,'previous_artifacts_checked':len(prior),'previous_artifacts_sha256_unchanged':True,'expert_reference':False,'cer':None,'wer':None,'pages':pages}
# The linked completion record exists with pending status until link checks pass.
save(J/'completion-validation.json',completion)
style='body{font:17px/1.6 system-ui;margin:0;background:#f5f2e9;color:#28251e}main{max-width:1200px;margin:auto;padding:28px}a{color:#245d80}table{border-collapse:collapse;width:100%;background:white}td,th{padding:10px;border:1px solid #d8d0bf;text-align:left}.badge{color:#863f21}.toolbar{position:sticky;top:0;background:#e7e1d5;padding:12px}input,select{font:inherit;padding:6px}h1{line-height:1.2}@media(max-width:700px){main{padding:14px}table{font-size:14px}}'
body='<h1>M II 220 · 430 zpracovaných stran</h1><p class="badge">'+str(430-blank)+' stran s pracovním latinským návrhem a českým překladem · '+str(blank)+' záznamů bez hlavního textu · bez odborné revize</p><p>Dokončeno dalších 100 stran 184r–235r. Původní obrazy a oba HTR kandidáti jsou zachované. Návrhy zahrnují vybrané hlavní oblasti. Nejistoty jsou vyznačeny; také neoznačená slova zůstávají návrhem.</p><nav>'
for href,label in [('assessment.md','Závěr a omezení'),('usage-report.md','Spotřeba'),('index.html','Nových 100 návrhů'),('reconstruction-all.la.txt','Souhrnná latina TXT'),('translation-all.cs.txt','Souhrnná čeština TXT')]:body+='<a href="'+J.name+'/'+href+'">'+label+'</a> · '
body+='</nav><p>Týdenní sdílené využití: '+str(usage['weekly_start_used_percent'])+'→'+str(usage['weekly_used_percent'])+'%. Placená modelová API: 0 volání.</p><h2>HTR a OCR exporty</h2><ul>'
folders=['pilot-ten-pages','pilot-next-ten-pages','pilot-third-ten-pages','htr-next-100-pages','htr-second-100-pages','htr-third-100-pages','htr-fourth-100-pages']
for folder in folders:body+='<li><a href="'+folder+'/index.html">'+folder+'</a></li>'
body+='</ul><p><a href="proarc-ocr-pilot-20-pages/README.md">OCR prvních 20 stran</a> · <a href="htr-fourth-100-pages/ocr-proarc/README.md">OCR nové stovky a ZIP</a></p><h2>Všechny strany v pořadí foliace</h2><div class="toolbar"><label>Folio <input id="filter" type="search" placeholder="např.168r"></label> <label>Etapa <select id="batch"><option value="">Všechny</option>'
for folder in folders:body+='<option value="'+folder+'">'+folder+'</option>'
body+='</select></label></div><table><thead><tr><th>Folio</th><th>Rekonstrukce a překlad</th><th>Obrazy a HTR</th><th>Segmenty</th></tr></thead><tbody>'
for p in sorted(pages,key=key):body+='<tr data-folio="'+p['folio']+'" data-batch="'+p['source_folder']+'"><td>'+p['folio']+'</td><td><a href="'+p['review']+'">'+('Záznam bez textu' if p['blank_selected_text'] else 'Latina a čeština')+'</a></td><td><a href="'+p['raw_comparison']+'">CATMuS / Medusa</a></td><td>'+str(p['segments'])+'</td></tr>'
body+='</tbody></table><p>Nových 100 TEI exportů prošlo Relax NG TEI P5 4.12.0. CER/WER bez nezávislé reference není stanoveno.</p><p><a href="'+J.name+'/validation.json">Validace nových interpretací</a> · <a href="'+J.name+'/completion-validation.json">Úplnost a zachování předchozích souborů</a></p><footer>Místní výzkumný pilot. Rekonstrukce a překlady jsou návrhy pro další revizi.</footer>'
body+="<script>function update(){const q=document.getElementById('filter').value.trim().toLowerCase(),b=document.getElementById('batch').value;document.querySelectorAll('tbody tr').forEach(r=>r.hidden=(!r.dataset.folio.includes(q))||(b&&r.dataset.batch!==b));}document.getElementById('filter').addEventListener('input',update);document.getElementById('batch').addEventListener('change',update);</script>"
(ROOT/'pilot-index.html').write_text('<!doctype html><html lang="cs"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>M II 220 · 430 stran</title><style>'+style+'</style></head><body><main>'+body+'</main></body></html>',encoding='utf-8')
index=(J/'index.html').read_text(encoding='utf-8');nav='<nav><a href="assessment.md">Závěr</a> · <a href="usage-report.md">Spotřeba</a> · <a href="reconstruction-all.la.txt">Souhrnná latina</a> · <a href="translation-all.cs.txt">Souhrnná čeština</a></nav>'
if 'href="assessment.md"' not in index:index=index.replace('<h1>',nav+'<h1>',1)
(J/'index.html').write_text(index,encoding='utf-8')
class Links(HTMLParser):
 def __init__(self):super().__init__();self.links=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  for k in ['href','src']:
   if k in a:self.links.append(a[k])
checked=0
for hp in [ROOT/'pilot-index.html',J/'index.html']:
 parser=Links();parser.feed(hp.read_text(encoding='utf-8'))
 for href in parser.links:
  url=urlsplit(href)
  if url.scheme or url.netloc:continue
  target=(hp.parent/unquote(url.path)).resolve() if url.path else hp
  assert target.is_file(),str(hp)+' missing '+href
  checked+=1
completion.update({'status':'passed','final_overview_links_checked':checked,'final_overview_links_valid':True,'report_sha256':sha(J/'assessment.md'),'usage_report_sha256':sha(J/'usage-report.md'),'combined_latin_sha256':sha(J/'reconstruction-all.la.txt'),'combined_czech_sha256':sha(J/'translation-all.cs.txt'),'global_index_sha256':sha(ROOT/'pilot-index.html'),'interpretation_index_sha256':sha(J/'index.html')})
save(J/'completion-validation.json',completion)
print('FINAL_REPORT_COMPLETE',430,'pages',passages,'new passages',tiles,'native images',len(prior),'prior files preserved',flush=True)
