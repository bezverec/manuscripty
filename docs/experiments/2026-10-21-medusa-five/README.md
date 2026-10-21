# M I 259: opětovná kontrola pěti řádků Medusy

21. 10. 2026. Skutečně otevřeny všechny původní nativní výřezy i širší kontext;
stav `proposed`, bez nezávislé odborné revize. Původní kandidáti a veřejný
korpus zůstávají beze změny. [Strojový záznam a evidence](report.json).

| Snímek / segment | Co skutečně obsahuje | Výsledek |
|---|---|---|
| 27v / 63 | Úzký neúplný útržek sousedního listu | Bez spolehlivé souvislé rekonstrukce. |
| 46v / 53 | Úzký útržek sousedního listu ve žlábku | Bez spolehlivé souvislé rekonstrukce. |
| 97v / 14 | Řádek hlavního právního textu | Samostatný návrh rozvedené četby, nejisté slovo a odkaz. |
| 119v / 28 | Řádek hlavního textu o Petrovi a Pavlovi | Samostatný návrh rozvedené četby a češtiny. |
| 124v / 100 | Úzký deformovaný útržek sousedního listu | Chybějící části slov nejsou v obrazu. |

## Nový pokus Medusy

Z původního polygonu vznikla maska, sloupce byly celočíselně posunuty podle
baseline bez převzorkování. Dva hlavní řádky byly zkusmo rozděleny také na
překrývající se poloviny. Devět vstupů bylo uspořádáno do diagnostické plochy;
nejde o novou rukopisnou stranu. [Přesné transformace a SHA](inputs.json).

Přípravu lze opakovat nad původním neveřejným výzkumným prostorem:

```sh
python prepare_inputs.py --source /research/mi259/full-htr --out /staging/new-five-line-inputs
```

Výstup musí být nový a oddělený od vstupů. Skript potřebuje Pillow;
nemění původní obrazy ani nespouští inference. Vstupní obrazy nejsou v Git.

Běžná nezměněná místní služba provedla novou segmentaci Kraken a Medusu 4B,
stejnou revizi vah, NF4/BF16, batch 8, greedy, limit 128. Segmentátor vytvořil
15 částí. **Žádná generace již nenarazila na tokenový limit**, ale některé
řádky byly roztrhány a výstupy zůstaly neúplné či zjevně chybné. Například
119v obsahuje chybnou kandidaturu „Petrus et Panis“ místo viditelného jména
Pavel. Žádný nový raw nebyl vybrán jako náhrada původního segmentu.

[Kandidáti](candidates.json), [nová geometrie](lines.json),
[provenience služby](provenance.json). Služba uvádí `enable_thinking=false`,
ale log současně varuje, že parametr processor ignoruje. Skutečné vykreslení
šablony nebylo v tomto novém pokusu nezávisle ověřeno; samotná hodnota
v provenienci tedy nedokládá vypnutí thinking. Nebylo voláno placené externí API.

## Samostatná rozvedená četba asistenta

Nejde o diplomatický přepis ani nový raw Medusy. Hranaté závorky a otazníky
označují nejistoty; zkratky právních odkazů nejsou celé rozřešeny.

**97v / 14, s doloženým pokračováním v segmentu 15:**

> Ecclesia est consecranda [odkaz: … Solemnitates]. Quod [ligna?] ecclesiae
> consecratae ad [usum?] … / religiosorum, non laicorum, debent admitti […].

Kostel má být posvěcen [právní odkaz]. [Dřevo?] z posvěceného kostela smí
být použito pro potřeby řeholníků, nikoli laiků […].

Nový věcný výklad se týká pravděpodobně dřeva kostela, zatímco předchozí
návrh mluvil o dřevěných kostelech. Podporuje jej právní paralela
v [Ivonově Decretum III, kap. 44, s. 14](https://ivo-of-chartres.github.io/decretum/ivodec_3.pdf#page=14),
která rozlišuje další církevní/klášterní a laické užití dřeva. Jde o
interpretační oporu, nikoli důkaz konkrétních písmenných tvarů tohoto rukopisu.
Nejisté `ligna` ani `ad usum` se proto netváří jako jistě přečtená slova.

**119v / 28:**

> […] Petrus et Paulus fuerunt pares quoad meritum, non [in?] dignitate,
> in qua praecessit Petrus […].

[…] Petr a Pavel byli rovni co do zásluh, nikoli však v důstojnosti, v níž
měl Petr přednost […].

`quoad` je normalizované rozvedení. Spojovací výraz před `dignitate` a
okrajové právní odkazy zůstávají nejisté. Překlad sleduje tuto pracovní četbu.
Tři ostatní výřezy neposkytují podklad pro doplnění celé věty ani překlad.

## Rozsah výsledku

Pět případů bylo posouzeno, dva dostaly zpřesněný návrh četby. **Nebylo
dokončeno pět původních přepisů Medusy.** Jejich limitové příznaky zůstávají
pravdivým záznamem původního běhu. Nové návrhy zde jsou samostatný výzkumný
dodatek v Git, zatím nebyly sloučeny do veřejné ediční vrstvy ani nasazeny.
CER/WER ani nová odborná reference nebyly získány.
