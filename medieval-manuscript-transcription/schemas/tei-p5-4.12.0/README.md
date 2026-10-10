# Offline schéma TEI P5 4.12.0

Soubor tei_all.rng je oficiální schéma TEI All verze 4.12.0. Verze je ověřena v komentáři schématu; přesný SHA-256 a datum získání jsou v sources.json. Stažená kopie je pevná, další exporty ani validace nic nestahují.

Namespace TEI zůstává http://www.tei-c.org/ns/1.0. Číslo vydání je v atributu TEI/@version a xml-model ukazuje na tuto místní kopii. Přenosný offline balíček musí obsahovat schéma i exporty se zachovanými relativními cestami. Při exportu na jiný disk ve Windows se použije místní file URI; po přesunu je nutné exportovat znovu.

Validátor používá lxml (zde 6.1.1), zakazuje síť, DTD i rozbalování entit a ověřuje kontrolní součet schématu. Kontroluje Relax NG a místní odkazy facs. Oficiální RNG obsahuje také vložená pravidla Schematron s XPath 2; ta lxml RelaxNG nevykonává. Neoznačujeme proto výsledek za plnou validaci Schematron ani za odbornou revizi přepisu. ALTO XSD se tímto nevaliduje.

Původ: https://tei-c.org/release/xml/tei/custom/schema/relaxng/tei_all.rng
Vydání: https://github.com/TEIC/TEI/releases/tag/P5_Release_4.12.0
Licence: v souboru je zachováno oficiální oznámení o dostupnosti TEI pod CC BY a BSD-2. Viz https://tei-c.org/about/frequently-asked-questions/#licensing

fetch_schema.py je pouze explicitní obnovovací nástroj vyžadující síť, není součást offline validace. Odmítne jiné vydání než 4.12.0.
