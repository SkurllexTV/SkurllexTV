# MEMORY

## Kontext / Ziel
GitHub-Profil-README für Skurllex im Terminal-/Chrome-Stil (Vorlage: oxince), Dark + Light.

## Entscheidungen
- Akzent Lime #C8FF3C (dark) / #5a7300 (light, Kontrast auf Weiß)
- Hero als SVG: "SKURLLEX" in Syne 800 als Pfade, Chrome-Verlauf, Extrusion, Lime-Glow
- JetBrains Mono NL als eingebettetes Subset in jedem SVG
- PGP-Signoff ersetzt durch `./hire`-Terminal (Wunsch des Users)
- Heatmap aus ASCII-Blöcken (··/░░/▒▒/▓▓/██), Stufen über Quartile; Daten per GitHub Action (GraphQL nur dort verfügbar)
- Hero: diagonaler Glanz läuft alle 7 s über den Schriftzug

## Umgesetzt
- assets/{dark,light}: hero, whoami, label-work, card-district/edify/skurllextv/fxserver, stack, signoff
- README.md, gen.py (Generator; Inhalte oben in PROFILE bzw. in den build_*-Funktionen)
- activity.svg (03), card-scripts.svg (05, volle Breite), fetch_contributions.py, .github/workflows/activity.yml (täglich 03:17 UTC)
- Schriften + OFL-Lizenzen in fonts/, damit die Action ohne externe Downloads läuft

## Offene Punkte / Fragen
- Annahme: Mail hi@edifystudios.de, Discord "skurllex": bestätigen
- Card-Links (District, SkurllexTV) noch ohne URL
- Annahme: Shop-Adresse https://b-development.tebex.io/
- Heatmap zeigt bis zum ersten Action-Lauf Demo-Daten ("preview data")

## Nächster Schritt
Daten bestätigen, Repo `skurllex/skurllex` anlegen, Ordner pushen.
