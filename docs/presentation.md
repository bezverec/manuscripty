# Publikovaná prezentace

Web běží na [rukopisy.digitalizaty.cz](https://rukopisy.digitalizaty.cz), Cloudflare Pages projekt rukopisy-digitalizaty. Aktuální snapshot: 11. 10. 2026, revize 20261011-6. Přehled dokumentu: [M II 220](https://rukopisy.digitalizaty.cz/rukopisy/vkol-m-ii-220), z fondů Vědecké knihovny v Olomouci.

Statické HTML/CSS/JavaScript a textové JSON/TEI/TXT běží v Pages. OpenSeadragon 6.1.1 načítá WebP dlaždice ve formátu pyramid DZI. Folia využívají [obrazovou doménu](https://rukopisy-data.digitalizaty.cz) s R2 bucketem rukopisy-mii220; snímky vazby jsou v binding-media/ v Pages. Q90, dlaždice 512 pixelů, překryv 1 pixel; výřezy a náhledy jsou samostatné deriváty. Původní TIFF zůstávají v lokálním archivu.

| Skutečně vytvořené deriváty | Počet objektů | Bajty |
|---|---:|---:|
| Folia v R2, včetně 50 297 řádkových výřezů | 158 837 | 10 213 360 984 |
| Vazba v Pages | 1 175 | 45 188 048 |

Jde o objemy obrazových derivátů, nikoli celkový prostor archivu. Historické odhady a měřicí skripty nejsou současným fakturačním výkazem; podmínky poskytovatele se musí ověřit při nové kalkulaci.

Frontend obsahuje prohlížeč skenů, řádkové čtení a přepisy, pasážové rekonstrukce a překlady, navigaci pracovní strukturou, AI shrnutí, textové exporty a sdílené odkazy na dokument, folio a řádek. Pravý panel lze roztáhnout; obě boční části lze skrýt a obnovit šipkami. Rozhraní návrhů HTR a segmentace zachovává původní ID a SHA-256 zdroje. GitHub slouží jako místo návrhů, nevytváří automaticky schválenou edici.

Git obsahuje web/public bez obrazů. Pro lokální zkoušku fungují foliované obrazy přes R2; sedm snímků vazby vyžaduje obnovit ignorované binding-media. Před novým nasazením je tato obnova povinná, aby nové Pages nasazení neztratilo snímky vazby. [Návod a kontrolní součty](../web/README.md).

Publikace se nadále provádí ručně pomocí Wrangler; tato aktualizace GitHubu sama nevytváří nové Pages nasazení ani nemění DNS, R2 nebo přístupové klíče.
