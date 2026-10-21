# Frolat na foliu 20v

Na třech obrazově zkontrolovaných řádcích frolat vynechává písmena a chybně dělí slova. Neposkytuje spolehlivě rozvedený text; kontrolní binarizace tyto problémy neodstranila. Na kontrolovaných příkladech je méně užitečný než dosavadní CATMuS. Nejde o měření přesnosti celé strany.

## Běh

Původní pracovní obraz: rozpoznání 10.80 s, načtení modelu 0.81 s, celý úspěšný běh 12.12 s.
Binarizace nlbin: předzpracování 19.37 s, rozpoznání 6.50 s, celý běh 27.31 s.

CPU, 4 vlákna; Kraken 7.1.1; PyTorch 2.9.0+cpu; oba běhy mají 84 neprázdných výsledků. Žádná nová segmentace, trénink ani placené API.

## Obrazově prohlédnuté příklady

- l002: původní frolat dává „ypocte steilis on glos omis opr“. Binarizace opravuje glos na glosa, další problémy ale zůstávají.
- l052: původní frolat dává „cu quif fi leranas uge et“, binarizovaný „er uf in leranas uge eee“. V obrazu lze rozpoznat posloupnost Cum … tu …, kterou model zkresluje.
- l076: frolat dává „quuy i exmuis me fecistsui“; obraz ukazuje vynechané či spojované části slov. Kandidát CATMuS tu zachovává více čitelného materiálu.

Příklady nejsou odborně ověřeným referenčním přepisem. Výstupy frolat nebyly přeneseny do kritického JSON, TEI ani překladu.

## Omezení

- Oba běhy používají stejné souřadnice a původní segmentaci.
- Frolat má dle autorů vytvářet rozvedené transkripce; surovou shodu s grafematickým CATMuS nelze vydávat za přesnost.
- Rozvedený návrh asistenta není odborná reference. CER/WER se nepočítá.
- Fragmenty l013 a l058 patří k navrženým fyzickým řádkům l012 a l059; jejich samostatné predikce nejsou automaticky připojeny.
- Kraken podle metadat modelu použil starší polygonový extraktor. Závěr platí pro tento konkrétní test.

Doporučení: uchovat jako další kandidát pro porovnání; zatím nepoužívat jako automatický zdroj rozvedeného textu celého rukopisu.

## Provenience a příprava

[Model autorů](https://zenodo.org/records/7516057), v1.0; 16 135 400 bytů; licence dle metadat CC BY-SA 2.0. Model SHA-256: 4cdaac65b9c4332dcee65e49ac8422be77a1f0d0d28d9fd9f53179c2f591da34. Údaj accuracy 89.1 v metadatech není přesnost na tomto rukopisu.

Dva první běhy rozpoznaly všech 84 segmentů (11.08 a 10.35 s), ale uložení do docker-copied složky selhalo kvůli oprávněním. Úspěšný třetí běh použil vlastní /tmp; samostatný další běh zkoušel nlbin. Tyto přípravné pokusy nejsou zahrnuty do časů úspěšných běhů.

Původní pracovní složka obsahovala skripty pro stažení, běh, bezeztrátový přenos UTF-8 a vytvoření porovnání. Běh používá předchozí obraz a segmentaci v /data/mii220-pilot-20261009. Git zachovává jen toto posouzení a [metadata modelu](model-source.json); uvedené pracovní výstupy a skripty nejsou přibalené.

Historické názvy externích pracovních výstupů: `comparison.html`, `comparison.json`, `validation.json`, `run.json`, `binarized/run.json`, `run-attempts.json`. Dřívější relativní odkazy na ně nebyly v tomto repozitáři funkční; při dokumentační kontrole 21. 10. 2026 byly nahrazeny tímto výslovným vymezením rozsahu. Závěr ani naměřené časy původního pilotu se nemění.
