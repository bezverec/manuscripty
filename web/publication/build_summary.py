"""Build a source-linked AI orientation summary; never edit source readings."""
import argparse, hashlib, html, json
from pathlib import Path

DOC='vkol-m-ii-153'
ORIGIN='https://rukopisy.digitalizaty.cz'
THEMES=[
('laska','Kristovo utrpení, láska a modlitba','První rozsáhlý celek propojuje rozjímání o Kristově utrpení s osobní modlitbou. Mariina bolest, Kristovy rány a eucharistické obrazy mají čtenáře vést k účasti na utrpení a k lásce. Katalog jej označuje jako Stimulus amoris; toto jméno neoznačuje celý vícedílný kodex.',['5r','20r','36r']),
('vnitrni-clovek','Vnitřní člověk a duchovní obnova','Další texty se obracejí k tělesné pomíjivosti, ceně duše a potřebě obrácení. Modlitby nad Kristovým životem a vzkříšením spojují vzpomínání na události s obnovou samotné duše. Dobové přímluvy za Svatou zemi patří historickému obsahu textu; nejsou samy dokladem přesného data jeho opsání.',['39r','46v','54v']),
('zavdavek','Rozhovor o závdavku duše','Dialog Huga s Duší vykládá duchovní lásku jako přípravu na trvalé společenství. Královský sňatek slouží jako obraz přípravy nevěsty. Duše se v závěru ptá na sladkou vnitřní zkušenost; odpověď ji chápe jako skrytou návštěvu milovaného a předchuť budoucí plnosti. Připsání Hugovi se uchovává spolu s katalogovým zdrojem; přeškrtnutý explicit a další poznámky zůstávají odlišeny.',['55v','61r','63v']),
('zpoved','Zpověď a rozhřešení nemocného','Na 64r je formulář vyznání a rozhřešení pro nemocného na prahu smrti. Zpověď probírá odkládání, nedostatečnou lítost a zastírání okolností hříchů. Závěrečná poznámka jmenuje Urbana VI. a Německý dům. Navržené čtení roku MCCCXCI? je nejistý údaj uvnitř formule; nepoužíváme jej jako potvrzený rok vzniku kodexu.',['64r']),
('souzeni','Dvanáct užitků soužení','Pojednání o soužení vybízí k trpělivosti a k hledání vnitřní útěchy. Oznamuje dvanáct užitků; na začátku představuje soužení jako Boží pomoc proti světským klamům. Bůh je popisován jako společník sužované duše. Závěr pojednání přechází k výňatkům s připsáními dalším autoritám; tato připsání nejsou nezávisle ověřenou identifikací citátů.',['64v','73v']),
('modlitby','Modlitební výklady a mariánský pozdrav','V modlitebním pojednání se rozjímají Boží přítomnost, neměnnost a stvořitelská moc. Výklad Salve regina klade vedle obdivu k Mariině velikosti pokoru, důvěru a prosbu o vedení. Katalogová připsání Pseudo-Augustinovi nebo Pseudo-Bernardovi jsou uvedena v popisu dokumentu, aby se nezaměňovala s bezpečně doloženým autorstvím.',['74v','82v']),
('hodinky','Rozjímání podle hodinek','Závěrečný větší celek rozvrhuje Kristovo utrpení podle sedmi hodinek. Požaduje střídmost a omezení rozptýlení, aby čtenář děj živě zpřítomnil. Modlitba o Mariině bolesti přechází k rozsudku, nesení kříže a ukřižování; kříž je vykládán jako lék, soudcovský trůn a obětní oltář.',['86v','89v']),
]

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf8'))
def write(p,s):
 if p.suffix=='.html':
  from markup import normalize_html
  s=normalize_html(s)
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s,encoding='utf8',newline='\n')
def build(source,out,complete):
 source=source.resolve();out=out.resolve()
 if out==source or out.is_relative_to(source) or source.is_relative_to(out):raise ValueError('Source and output must be disjoint')
 data=load(out/'data'/DOC/'manifest.json')
 if complete and not data['publication_ready']:raise ValueError('Incomplete text publication')
 themes=[]
 for ident,title,text,folios in THEMES:
  sources=[]
  for folio in folios:
   p=source/'interpretation'/(folio+'.json');obj=load(p)
   if not obj['lines']:raise ValueError('Summary source has no text: '+folio)
   first=obj['lines'][0]['id']
   sources.append({'folio':folio,'line_id':first,'uri':ORIGIN+'/rukopis?doc='+DOC+'&vrstva=vyklad#'+folio+'-'+first,'interpretation_sha256':sha(p),'source_sha256':obj['source'].get('original_sha256') or obj['source'].get('sha256')})
  themes.append({'id':ident,'title_cs':title,'summary_cs':text,'sources':sources})
 record={'schema':'manuscripty-ai-summary-v1','document_id':DOC,'date':'2026-10-12','status':'proposed','expert_review':False,'description_cs':'Orientační AI shrnutí obrazově kontrolovaných pracovních rekonstrukcí a českých překladů; obsahuje zdrojové odkazy, nikoli nové potvrzení autorství.','metadata_sha256':sha(source/'document.json'),'themes':themes,'catalogue_only_notes_cs':['Souhrnný název Textus varii pochází z dodaného digitalizačního XML. Stimulus amoris a Contemplacio de passione Christi jsou různé dílčí identifikace podle odlišných katalogů.','Datace do druhé poloviny 14. století a údaj Dolany, kartuziáni — vazba jsou katalogová tvrzení.','Katalog uvádí na 96v latinské a německé recepty a jiné doplňky. Tyto historické texty se nepředkládají jako současná léčebná doporučení.'],'catalogue_sources':['https://manuscripta.cz/manuscript/VKOL_M_II_153/','/data/'+DOC+'/document.json'],'scope_note_cs':'HTR pokrývá vybrané hlavní písařské oblasti a některé texty na vazbě. Ne všechny okrajové přípisy jsou přepsány. Prázdné hlavní textové plochy jsou výslovně označeny; katalogové hranice děl se mohou překrývat.'}
 jsonpath=out/'data'/DOC/'summary.json';write(jsonpath,json.dumps(record,ensure_ascii=False,indent=2)+'\n')
 # The canonical overview contains catalogue and AI parts; former URLs redirect.
 from manuscript_overview import update
 update(out)
 print(json.dumps({'status':'passed','themes':len(themes),'source_interpretations':sum(len(t['sources']) for t in themes),'expert_review':False,'combined_overview':True}))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--require-complete',action='store_true');a=p.parse_args();build(a.source,a.out,a.require_complete)
