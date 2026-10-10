from pathlib import Path
import json,datetime,html,re
H=Path(__file__).resolve().parents[1];R=H.parent
def rd(p):return json.loads(p.read_text(encoding='utf-8'))
def wr(p,s):p.write_text(s,encoding='utf-8')
s=rd(H/'summary.json');c=rd(H/'catmus-batch.json');m=rd(H/'medusa-batch.json');o=rd(H/'ocr-proarc/manifest.json');v=rd(H/'ocr-proarc/validation.json');z=rd(H/'ocr-proarc/package-check.json');prior=rd(H/'prior-outputs-final-check.json');selection=rd(H/'manifest.json')
folios=[p['folio'] for p in selection['pages']];count=len(folios)
assert count and all([p['folio'] for p in x['pages']]==folios for x in [s,c,m,o])
assert c['status']==m['status']==o['status']=='success' and v['all_checks_passed'] and z['zip_crc_and_file_hashes_valid']
n=s['total_segments'];allcount=prior['prior_raw_pages']+count;allsegments=prior['prior_segments']+n
blank=[p['folio'] for p in s['pages'] if p['segments']==0];cn=sum(p['catmus_nonempty'] for p in s['pages']);mn=sum(p['medusa_nonempty'] for p in s['pages']);tr=[a for p in m['pages'] for a in p.get('truncated_lines',[])];fallback=[p['folio'] for p in c['pages'] if p.get('polygonizer_fallback_events')]
J=R/'interpretation-fourth-100-pages'
assignment_counts={name:len(rd(J/'assignments'/f'{name}.json')['folios']) for name in ['parent','b','a','c']}
assert sum(assignment_counts.values())==count
assignment_text=' / '.join(f"{name}: {num}" for name,num in assignment_counts.items())
fallback_details='; '.join(f"{p['folio']}, zóna {event.get('zone','?')}: {event['fallback']}" for p in c['pages'] for event in p.get('polygonizer_fallback_events',[]))
range_cs=folios[0]+'–'+folios[-1];vr=rd(H/'visual-review.json') if (H/'visual-review.json').exists() else {}
ass=f'''# HTR nové dávky — výsledek

Dokončeno {count} nových stran {range_cs}; jednotlivá folia a vybrané oblasti obsahuje manifest.json. Celkem je zpracováno {allcount} různých stran se dvěma HTR kandidáty a {allsegments:,} segmentů. Nová dávka má {n:,} segmentů; CATMuS {cn:,} neprázdných výstupů a Medusa {mn:,}. Folia s nulou segmentů: {', '.join(blank) or 'žádná'}. Nulový počet dokládá absenci vybraného hlavního textu, nikoli celkové posouzení všech stop na originálu.

Oba kandidáti používají stejné detekované základní linky a polygony v souřadnicích originálu. CATMuS používá interní extrakci a narovnání řádku Kraken rpred ze společného pracovního obrazu; Medusa uložený bezztrátový PNG výřez s dokumentovaným přesahem a vlastní předzpracování. Nejde o totožné vstupní tenzory. Segment může být fragment řádku nebo iniciály. Zpracování je omezené na oblasti uvedené v manifestu, s jejich stanoveným pořadím; okrajové poznámky mimo ně nejsou zahrnuté. Surový Unicode zůstává bez oprav a normalizace.

CATMuS běžel v Kraken {c.get('engine',{}).get('kraken','neuvedeno')} na {c.get('engine',{}).get('device','neuvedeno')}; CPU pracovníků {c.get('parallel_cpu_workers','neuvedeno')}, vlákna na pracovníka {c.get('threads_per_worker','neuvedeno')}. Medusa: {m.get('model_id','neuvedeno')}, revize {m.get('revision','neuvedeno')}, {m.get('precision','neuvedeno')}, dávka {m.get('batch_size','neuvedeno')}, maximum nových tokenů {m.get('max_new_tokens','neuvedeno')}. SHA modelů, prompt a nastavení jsou v catmus-batch.json a medusa-batch.json.

Limit bez EOS byl dosažen u {len(tr)} segmentů: {', '.join(tr) or 'žádný'}. Náhradní polygonizace: {', '.join(fallback) or 'žádná'}. Počáteční vizuální výběr dokumentuje visual-review.json: {vr.get('overview_pages_inspected',vr.get('overview_pages',0))} stran na {len(vr.get('contact_sheets_actually_opened',[]))} skutečně otevřených přehledech. Tento záznam sám není nativní paleografickou kontrolou. Následnou kontrolu všech vybraných hlavních oblastí v nativních pásech dokládá samostatný manifest a validace v ../interpretation-fourth-100-pages/; aktuální skutečnou úplnost uvádí jeho manifest a validační záznam. Aktuální autorské rozdělení z assignments: {assignment_text}. Detaily všech {len(fallback)} náhradních polygonizací: {fallback_details}. Původní detekované baseline zůstaly zachovány; obrazové ověření dokládají rekonstrukce dotčených folií. Nejde o úplnou paleografickou korekturu. Bez nezávislé odborné reference nejsou vypočteny CER/WER a shoda modelů nepotvrzuje správnost čtení.

OCR používá CATMuS a CTC zarovnání s ověřeným zachováním raw textu: {o['totals']['exported_textlines']:,} TextLine, {o['totals']['words']:,} String; {o['totals']['unlocalized_words_line_envelope']} slov používá výslovně označenou obálku skutečného řádku při zdegenerovaném slovním polygonu. TXT vzniká ze serializovaného ALTO s dokumentovaným sjednocením bílých znaků. Ověřeno lokální XSD ALTO {o.get('schema_version','neuvedeno')} a vybrané strukturální kontroly NDK OCR; nejde o úplný NDK PSP ani test importu do živého ProArcu. ZIP má {z['zip_bytes']:,} bajtů a ověřené CRC a souborové SHA256.

[HTR srovnání](index.html) · [Technické kontroly](validation.json) · [Provenance sedmi fallbacků](fallback-visual-audit.json) · [OCR export](ocr-proarc/README.md) · [OCR validace](ocr-proarc/validation.json) · [Nové výkladové návrhy](../interpretation-fourth-100-pages/index.html).

Dosavadních {prior['prior_raw_pages']} stran i jejich staré výklady jsou zmrazené a porovnávané s previous-artifacts-sha256.json. Root pilot-index.html se záměrně aktualizuje. Nová rekonstrukce latiny a český překlad tvoří samostatnou návrhovou vrstvu bez odborné reference.
'''
wr(H/'assessment.md',ass)
history=rd(H/'medusa-session-history.json') if (H/'medusa-session-history.json').exists() else {}
prior_sessions=[x for x in history.get('sessions',[]) if x.get('stop_observed_utc')]
prior_wall=sum(x.get('observed_wall_seconds',0) for x in prior_sessions)
prior_load=sum(x.get('batch_snapshot',{}).get('model_load_seconds',0) for x in prior_sessions)
gpu_checkpointed=m.get('checkpointed_recognition_seconds_all_sessions',s['new_medusa_recognition_seconds'])
cat_history=rd(H/'catmus-session-history.json') if (H/'catmus-session-history.json').exists() else {}
cat_prior_sessions=cat_history.get('sessions',[])
cat_history_text='; '.join(f"shard {x.get('shard','?')}: předchozí pozorovaná wall {x.get('observed_wall_seconds',0):.3f} s, původní načtení {x.get('batch_snapshot',{}).get('engine',{}).get('model_load_seconds',0):.3f} s" for x in cat_prior_sessions) or 'žádné předchozí ukončené shardy'
cat_final_shards=[rd(p) for p in sorted(H.glob('catmus-batch-part*.json'))]
cat_current_loads='; '.join(f"shard {x.get('shard',i+1)}: {x.get('engine',{}).get('model_load_seconds',0):.3f} s" for i,x in enumerate(cat_final_shards) if isinstance(x,dict)) or str(c.get('engine',{}).get('model_load_seconds','viz finální shard metadata'))
rows=[('CATMuS segmentace CPU',s['new_segmentation_seconds']),('Bezztrátové výřezy',s['new_crop_seconds']),('CATMuS rozpoznávání CPU',s['new_catmus_recognition_seconds']),('Medusa uložený sdílený čas GPU všech relací',gpu_checkpointed),('CTC zarovnání a OCR export CPU',sum(p['seconds'] for p in o['pages']))]
inputt=sum(p.get('total_input_tokens',0) for p in m['pages']);outt=sum(p.get('total_output_tokens',0) for p in m['pages']);peak=max((p.get('gpu_peak_allocated_bytes',0) for p in m['pages']),default=0)
usage=f'# Spotřeba — {count} nových skenů\n\nPlacená modelová API: **0 volání**. Lokální již uložené modely. Příkon ani finanční cena místního výpočtu nebyly měřeny.\n\n| Operace | Sekundy | Minuty |\n|---|---:|---:|\n'+'\n'.join(f'| {name} | {sec:.3f} | {sec/60:.2f} |' for name,sec in rows)
usage+=f'\n\nČasy CPU, GPU a OCR se překrývají; jejich součet není celkové trvání projektu. Sdílený čas GPU není jednotlivá latence každého výřezu. Medusa současná relace včetně načtení a čekání: {m.get("total_seconds",0):.3f} s (rozsah {m.get("total_seconds_scope","současná relace")}), současné načtení modelu {m.get("model_load_seconds",0):.3f} s; předchozí ukončené relace pozorováno {prior_wall:.3f} s včetně {prior_load:.3f} s načtení. Uložený čas GPU všech relací {gpu_checkpointed:.3f} s zahrnuje zachované checkpointy právě jednou, současné nové rozpoznávání {m.get("current_session_recognition_seconds",0):.3f} s; čekání na CATMuS {m.get("waiting_for_catmus_seconds",0):.3f} s; OCR proces {o.get("seconds",0):.3f} s. Lokální Medusa má {inputt:,} vstupních a {outt:,} výstupních tokenů bez paddingu; nesouvisí s limitem frontier asistenta. Maximum alokace PyTorch {peak/1024**3:.3f} GiB. Tokeny jsou součtem konečných kandidátů, zachované checkpointy se nepřičítají podruhé. Neuložený rozpracovaný výpočet při ukončení předchozí relace není změřen; jeho spotřebu neodhadujeme. Relace dokládá medusa-session-history.json.\n'
usage+=f'\nCATMuS checkpoint-resume: {cat_history_text}. Tyto shardy běžely souběžně; jejich pozorovanou wall nesčítáme jako elapsed dobu. Současné načtení modelů: {cat_current_loads}. Konečné uložené časy segmentace a rozpoznávání zahrnují zachované folio checkpointy jednou. Neuložené rozpracované segmentace/rozpoznávání při přerušení nemají změřený čas a nejsou rozpočítány na folia. Podrobnosti a kontrolní součty zachovaných souborů: catmus-session-history.json.\n'
start=rd(H/'usage-start.json') if (H/'usage-start.json').exists() else {};end=rd(H/'usage-end.json') if (H/'usage-end.json').exists() else {}
usage+=f'\nSdílené týdenní okno účtu při zahájení: {start.get("weekly_used_percent","nezaznamenáno")} %. Konečný odečet: {end.get("weekly_used_percent","dosud nezaznamenán")} %. Zaokrouhlené odečty neumožňují izolovat cenu ani tokeny této dávky; čas a údaje jsou v usage-start.json a případném usage-end.json.\n'
wr(H/'usage-report.md',usage)
old=(H/'prior-pilot-index.html').read_text(encoding='utf-8')
banner=f'<aside id="batch-fourth-100-complete" style="padding:16px;background:#e7e1d5"><h2>Dokončena nová dávka {count} stran</h2><p>Celkem {allcount} různých stran HTR, {allsegments} segmentů. HTR hotovo; nové výklady a překlady se průběžně doplňují.</p><p><a href="{H.name}/index.html">Dávka {range_cs}</a> · <a href="{H.name}/assessment.md">Výsledek a omezení</a> · <a href="{H.name}/usage-report.md">Spotřeba</a> · <a href="interpretation-fourth-100-pages/index.html">Nové návrhy a české překlady</a></p></aside>'
old=re.sub(r'(<title>).*?(</title>)',lambda a:a[1]+f'M II 220 · {allcount} stran HTR'+a[2],old,count=1,flags=re.S).replace('<main>','<main>'+banner,1)
wr(R/'pilot-index.html',old)
print(json.dumps({'completed_pages':count,'new_segments':n,'all_pages':allcount,'all_segments':allsegments,'truncated':len(tr)}),flush=True)
