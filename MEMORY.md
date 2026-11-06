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

- Animationen (nach Kritik „langweilig“): Einbau gestaffelt (CSS rise), Hero mit tippendem Code-Fenster, Toast „+20 Lektion abgeschlossen“ und Lichtlinien im Raster; Werte-Karten mit Live-Zeilen; Projektkarten mit Mini-Visuals (Log, Fortschritt/Punkte, Pipeline, Code-Review-Diff); Heatmap mit Zählern und pulsierendem Heute; Stack mit wandernder Markierung; Kontakt mit Punkte-Welle und rollendem Button-Text

- Interaktive Profilseite (Wunsch: interaktiv + animiert; GitHub-README kann kein JS): site/template.html → site/build.py → docs/index.html (Schriften eingebettet). Terminal mit Befehlen, Themen-Chips, Maus-Glow, Projektfilter + Modal, Heatmap-Tooltips, Stack-Auswahl markiert Projekte, Punkte-System mit Toasts, Hell/Navy-Schalter, Mail kopieren. Als Artifact veröffentlicht (privat) und für GitHub Pages (/docs) vorbereitet
- README: CTA-Kachel auf die Pages-Seite, FAQ als aufklappbare <details>; Action baut docs mit und kopiert contributions.json nach docs/

## Offene Punkte / Fragen
- GitHub Pages im Repo aktivieren (main, /docs); URL angenommen: https://skurllextv.github.io/SkurllexTV/
- District-Karte ohne Link (Server noch nicht öffentlich)

## Nächster Schritt
Repo-Inhalt komplett ersetzen, Action einmal manuell starten.
