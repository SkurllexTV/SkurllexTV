# MEMORY

## Kontext / Ziel
GitHub-Profil und Social-Assets für skurllex, neu aufgebaut nach dem Skurllex Branding Kit v1.0 (November 2026).

## Entscheidungen
- Kit ist maßgeblich: Navy #0F1B2D, Skurl Blue #2B5BE0, Weiß als Basis; Blue Light #7FA2FF auf Navy; Violett nur in Glows/Verläufen
- Schriften: Geist (800 für Headlines, aus der Variable-Font instanziert), Geist Mono (Logo, Labels, Nummern)
- Logo `~/skurllex▌`, Cursor blinkt nur digital, keine Effekte am Logo
- Light = Standard, Navy = Dark-Mode-Variante (prefers-color-scheme)
- Sprache Deutsch, per du, Headline-Formel „[Thema]. [Auflösung].“
- Alte v1 (Lime, Chrome-3D, ASCII) verworfen, weil das Kit Neon-Gaming und Glow-Effekte ausschließt

## Umgesetzt
- gen.py: hero (rollendes Thema + blinkender Cursor, Linienraster mit Fade, 3 driftende Glows), about (01, Werte-Karten), projects + 4 Projektkarten (02), activity (03, Heatmap, Daten per Action), stack (04), contact (05, Punktraster)
- brand.py: Avatare navy/blau/weiß (1024 px), Discord-Profilbanner 1360×480, Discord-Server-Banner 960×540
- Mail/Domain aus dem Kit: hallo@skurllex.com, skurllex.com

## Offene Punkte / Fragen
- District-Karte ohne Link (Server noch nicht öffentlich)

## Nächster Schritt
Repo-Inhalt komplett ersetzen, Action einmal manuell starten.
