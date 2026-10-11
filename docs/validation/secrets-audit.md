# Kontrola secrets při aktualizaci repozitáře 11. 10. 2026

Nástroj: [Gitleaks 8.30.1](https://github.com/gitleaks/gitleaks/releases/tag/v8.30.1), místní provedení, redakce hodnot --redact=100.

Připravený obsah repozitáře byl zkontrolován v režimu dir: 369 920 500 bajtů, žádný nález. Po přidání pomocných souborů a commitu se před push provádí ještě git --log-opts=--all nad dostupnou historií. JSON výstup skenu historie je uložen jako gitleaks-history.json; prázdné pole znamená žádné detekované nálezy.

Kontrola Git indexu vylučuje samostatné obrazy, modelové váhy, archivy, node_modules, .env, .credentials, .aws a .wrangler. Veřejné webové texty a frontend mají samostatný soupis SHA-256. Do repozitáře se nekopírují účtové konfigurační soubory ani credential cache.

GitHub Actions repository secrets: 0 podle metadata kontroly 11. 10. 2026. Secret scanning a push protection jsou v nastavení repozitáře vypnuté; tato aktualizace nastavení nemění. Automatická detekce nemusí poznat každý vlastní formát hesla nebo tajný údaj, proto výsledek znamená žádné detekované secrets v uvedeném rozsahu, nikoli absolutní záruku. Hodnoty přístupových údajů nebyly publikovány ani posílány externímu skeneru.
