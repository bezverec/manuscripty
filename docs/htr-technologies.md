# Použité HTR technologie a checkpointy

Evidence použití je z lokálních záznamů experimentů a dokončených dávek. Odkazy vedou na původní vydavatele; checkpointy a konvence se nesmějí zaměňovat. Odkazy byly kontrolovány 11. 10. 2026; konkrétní inference se vztahuje k níže zaznamenaným verzím, nikoli k pozdější main větvi modelu.

## Produkční dvojice pro hlavní text

| Technologie | Úloha a použití | Zdroj |
|---|---|---|
| Kraken 7.1.1 | Lokální Docker CPU, blla segmentace, CRNN/CTC rozpoznávání a zarovnání pro OCR | [Dokumentace](https://kraken.re/main/index.html), [zdrojový kód](https://github.com/mittagessen/kraken) |
| CATMuS medieval 1.6.0 | Kandidát surového grafematického HTR na všech 664 textových stranách; bez automatického rozvádění zkratek | [Pevná verze 1.6.0 na Zenodo](https://zenodo.org/records/15030337), [transkripční pravidla](https://catmus-guidelines.github.io/) |
| ENC-PSL/Medusa0.2Line-4B | Nezávislý řádkový VLM kandidát na stejných zdrojových segmentech všech 664 textových stran; lokální GPU, NF4 4bit | [Model](https://huggingface.co/ENC-PSL/Medusa0.2Line-4B), [použitá revize](https://huggingface.co/ENC-PSL/Medusa0.2Line-4B/tree/2e891246c709976eb8fd90274932d1f08debcb15) |

CATMuS SHA-256: 227d10f15a936c2492105b7796a6152647c742f248af117856f417008eadbc9c. Kraken blla checkpoint SHA-256: 77a638a83c9e535620827a09e410ed36391e9e8e8126d5796a0f15b978186056. Medusa revize: 2e891246c709976eb8fd90274932d1f08debcb15; model.safetensors SHA-256: 930f97e19686a94e2a9967014e437162153bb884121aa3923a1e25422d4e708b. Záznam [Medusa](htr-evidence/medusa-study/model-source.json).

Kraken zpracovává polygonové oblasti, Medusa dostává obdélníkové bezztrátové řádkové výřezy s vlastní interní předúpravou. Stejný zdrojový segment nezaručuje stejné vstupní pixely obou enginů. Medusa běžela deterministicky, bez předchozího přepisu a bez tréninku na tomto rukopisu. Podrobné knihovny, prompt a parametry: [reproduction.md](reproduction.md).

## Pilotní alternativy

| Model | Použitá verze nebo revize | Výsledek konkrétního pilotu |
|---|---|---|
| [TRIDIS Kraken v2](https://zenodo.org/records/13862096), Tridis_v2_Medieval_EarlyModern.mlmodel | Zenodo 13862096, verze 2 | Kandidát v původním pilotu; rozvádí zkratky a normalizuje text. Surová predikce není diplomatická reference. |
| [Frolat](https://zenodo.org/records/7516057), frolat_medieval_expan.mlmodel | v1.0; SHA-256 4cdaac65b9c4332dcee65e49ac8422be77a1f0d0d28d9fd9f53179c2f591da34 | Folio 20v, 84 segmentů; původní obraz a kontrolní nlbin binarizace. Tři obrazově posouzené příklady ukázaly vynechávání a dělení slov, bez přesvědčivého přínosu proti CATMuS. |
| [Medusa0.1Line-9B](https://huggingface.co/ENC-PSL/Medusa0.1Line-9B) | 37efd0683dec5170ec45e0b7a6360a4a73af2afb | 20v, NF4 na 12GB RTX 5070. Na šesti kontrolovaných příkladech dílčí přínos pro zkratky, ne jednoznačně lepší celé řádky. |
| [TrOCR Manicule 2026 Latin Medieval](https://huggingface.co/LaMOP/TrOCR_Manicule_2026_Latin_Medieval) | 08e146d2dbf4673da24ce2f2dc5f3343bc62099c | 20v; explicitní decoder_start_token_id=0. Rychlý další kandidát, rozvedené predikce nejsou ověřená ediční vrstva. Šest obrazově posouzených příkladů bez jednoznačného zlepšení proti Medusa 4B. |
| [TRIDIS TrOCR v2](https://huggingface.co/magistermilitum/tridis_v2_HTR_historical_manuscripts) | a9893de9921ceb5db1845d06ac0a9c704d6f9bb2 | 20v; architektura sestavena podle receptu a rozměrů vah, strict load, počáteční token 0, beam search 3. Šest posouzených příkladů bez jednoznačného zlepšení; nezaměňovat s TRIDIS Kraken. |

Záznamy checkpointů a posouzení jsou v [htr-evidence](htr-evidence). Modelové karty obsahují výsledky z jiných datasetů; jejich accuracy/CER nejsou přesností na M II 220. Pilot nemá nezávislou odbornou referenci, proto se nepublikuje žebříček podle CER/WER. U 20v odpovídá 84 původních segmentů 82 pracovním fyzickým řádkům; spojení fragmentů v UI nezměnilo původní HTR.

## Další součásti pipeline

[PyTorch](https://pytorch.org/), [Transformers](https://huggingface.co/docs/transformers/), [bitsandbytes](https://huggingface.co/docs/bitsandbytes/), [Accelerate](https://huggingface.co/docs/accelerate/) a [Hugging Face Hub](https://huggingface.co/docs/huggingface_hub/) slouží lokálnímu načtení a inference; Docker odděluje CPU a GPU prostředí. lxml a Pillow zajišťují XML validaci a obrazové deriváty. Český překlad a latinskou rekonstrukci navrhoval asistent z obrazů a kandidátů; nejde o automatickou funkci některého HTR checkpointu ani o volání placeného modelového API z přibalených skriptů.

[TEI P5 4.12.0](https://github.com/TEIC/TEI/releases/tag/P5_Release_4.12.0) používá přibalené offline RNG. [ALTO](https://www.loc.gov/standards/alto/) 3.0 je cílem produkčního OCR pro ProArc; referenční exporter má odlišnou výchozí ALTO 4.4. [OpenSeadragon](https://openseadragon.github.io/) 6.1.1 je prohlížeč obrazů, Cloudflare Pages/R2 publikační infrastruktura, nikoli HTR engine.

Váhy nejsou přibaleny. Záznamy model-source zachovávají deklarované licence konkrétních experimentů; modely, schémata, knihovny a vlastní kód mají odlišnou provenienci. Pro použití nového checkpointu znovu načtěte jeho konkrétní modelovou kartu.
