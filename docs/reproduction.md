# Prostředí a reprodukce

Dokumentace aktualizována 21. 10. 2026. Samostatně lze ověřit referenční exporter se syntetickou ukázkou a veřejný korpus tří rukopisů; dávková inference vyžaduje obnovený výzkumný prostor. Následující historický recept se vztahuje ke čtvrté stovce M II 220. Produkční inference nebyla při údržbě repozitáře znovu opakována. Aktuální ověření webu a sestavení 1 245 folií popisuje [web/README.md](../web/README.md).

## Samostatná kontrola

Z kořene repozitáře, s Pythonem a závislostmi:

~~~sh
python -m pip install -r requirements-reference.txt
python -m unittest discover -s medieval-manuscript-transcription/tests -v
python medieval-manuscript-transcription/scripts/export.py --input medieval-manuscript-transcription/assets/demo.json --out-dir demo-output --validate-tei
python medieval-manuscript-transcription/scripts/validate_tei.py demo-output/edition.tei.xml --report demo-output/tei-validation.json
~~~

Instalace vyžaduje dostupný balíčkový zdroj; vlastní TEI validace používá místní pevné schéma bez sítě. Referenční exporter má výchozí ALTO 4.4, zatímco produkční ProArc větev používá ALTO 3.0.

## Zaznamenané historické prostředí M II 220

| Součást | Použitá konfigurace |
|---|---|
| Hostitel | Windows, Docker Desktop; pracovní adresář připojen jako /workspace |
| CPU | Kraken 7.1.1, dva shardy, každý 4 vlákna |
| GPU | NVIDIA RTX 5070, CUDA; PyTorch 2.10.0+cu129 |
| Medusa knihovny | transformers 5.2.0, bitsandbytes 0.49.2, accelerate 1.13.0, huggingface-hub 1.33.0 |
| Exporty a obrazy | lxml 6.1.1, Pillow 12.1.1 |
| CATMuS cache | /models/catmus-medieval-1.6.0.mlmodel |
| Medusa cache | /opt/medusa-model |

CATMuS SHA-256: 227d10f15a936c2492105b7796a6152647c742f248af117856f417008eadbc9c.

Kraken blla SHA-256: 77a638a83c9e535620827a09e410ed36391e9e8e8126d5796a0f15b978186056.

Medusa model: ENC-PSL/Medusa0.2Line-4B, revize 2e891246c709976eb8fd90274932d1f08debcb15; model.safetensors SHA-256: 930f97e19686a94e2a9967014e437162153bb884121aa3923a1e25422d4e708b.

Medusa používá NF4 4bitové váhy s double quantization a BF16 compute, batch 16, max_new_tokens 128, do_sample False, enable_thinking False, min_pixels 65536, max_pixels 401408, local_files_only True a trust_remote_code False. Prompt je:

~~~text
Transcribe the handwritten text in this line image.
Output ONLY the transcription.
~~~

## Obnovení dávkového prostředí

Zachovejte relativní rozložení zdrojových složek v kořeni obnoveného datového pracovního prostoru. Doplnit je nutné EX/ s archivními TIFF, manifesty a výstupy dřívějších etap, modelové cache a Docker prostředí. selection.json a assignments/*.json poslední dávky jsou přibaleny; nejde o konfiguraci libovolné nové stovky. Názvy a cílové počty jsou pevně zapsané ve skriptech. build_final_report.py vyžaduje i výsledky předchozích 330 stran, kontrolní součty, záznamy spotřeby a dokončené validace.

Dockerfile, plný dependency lock a image digest původních kontejnerů nejsou v tomto snapshotu. Tabulka popisuje zaznamenané použité prostředí, nikoli garantovaný recept na sestavení identické image. Obnovení samotné cache bez tokenizeru, processoru a dalších souborů Medusy nestačí. Vedle závislostí v tabulce používá Kraken větev také knihovny dodané prostředím Kraken, například shapely.

## Pořadí kroků v obnoveném prostoru

Nejprve se skutečně otevřou obrazy a schválí oblasti. Následuje snapshot starších artefaktů a příprava poslední dávky:

~~~sh
python htr-fourth-100-pages/scripts/snapshot_prior.py
python htr-fourth-100-pages/scripts/prepare_pages.py
~~~

Příklady pro původní existující kontejnery; dva CPU příkazy spustit souběžně ve dvou terminálech, GPU může čekat na dokončené řádky:

~~~sh
docker exec -e CATMUS_SHARD=1 mii220-pilot10-kraken python /workspace/htr-fourth-100-pages/scripts/start_catmus.py
docker exec -e CATMUS_SHARD=2 mii220-pilot10-kraken python /workspace/htr-fourth-100-pages/scripts/start_catmus.py
docker exec mii220-medusa-20261009 python /workspace/htr-fourth-100-pages/scripts/run_medusa.py
~~~

Po CATMuS se spojí shardy pomocí collect_catmus.py. OCR export potřebuje Kraken a CATMuS cache, tedy odpovídající CPU prostředí:

~~~sh
python htr-fourth-100-pages/scripts/collect_catmus.py
docker exec mii220-pilot10-kraken python /workspace/htr-fourth-100-pages/scripts/run_export_when_ready.py
python interpretation-fourth-100-pages/scripts/prepare_tiles.py
~~~

Následuje skutečné čtení obrazů asistentem a zápis reconstruction.json jednotlivých stran s nejistotami a proveniencí. SKILL.md určuje postup, ale sám neposkytuje modelové API ani přístup k obrazům. Exportery tento krok nenahrazují.

Hotové návrhy exportuje export_interpretation.py; validate_final_exports.py a audit_native_decode.py ověřují exporty a použité obrazy. Dávkový finalizátor a build_final_report.py potom vyžadují úplný soubor jejich vstupních auditů. Přesné závislosti jsou vidět ve zdrojích; čekací skripty mohou čekat bez časového limitu, pokud chybí manifest nebo dokončený výstup. Jejich spuštění nad samotným Git clone proto není smysluplná zkouška.

Na novém rukopisu je nutné upravit konfigurační vazby a počty, vybrat textové oblasti z jeho obrazů a vytvořit vlastní provenienci. Zkopírování stávajících značek kontroly na nové obrazy není obrazová kontrola.

## Současná veřejná větev a další rukopisy

Při obnově používejte přijatý veřejný snapshot včetně pozdějších čtení a anotací.
Základní rebuild M I 259 je sám nepřenese; oba redakční importéry mají pevné
historické vstupy a nejsou obecným opakovatelným migračním nástrojem.
[Pravidla zachování vrstev](../web/publication/README.md).

Textový korpus tří rukopisů a frontend jsou v `web/public`. Obnovu médií a Pages nasazení popisuje [web/README.md](../web/README.md), adaptéry [publication/README.md](../web/publication/README.md). M I 259 používá v hlavním běhu batch 8, v samostatném recovery batch 1 / limit 256 / repetition penalty 1.08; historický batch 16 výše není jeho konfigurace. Přesný model, vstupy, orientace a limity: [mi259-processing.md](mi259-processing.md). Plný výzkumný runner a neveřejná data M I 259 nejsou v tomto Git snapshotu; přibalený adaptér sám nezajišťuje reprodukci inference. Revize pilotních checkpointů: [htr-technologies.md](htr-technologies.md).
