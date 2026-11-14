# Technik in 60s – Runbook

YouTube-Kanal „Technik in 60s“ (@Technikin60s), Kanal-ID UCCOqO6cc4eHwJd_63GL_ghQ. Besitzer: Ali.
Deutsche Erklär-Shorts zu Strom, Energie und Gebäudetechnik. Ziel: Reichweite → Affiliate + später YPP.

## Ablauf pro Video (sparsam mit Tokens!)
1. `sh pipeline/setup.sh`
2. Nächstes Thema aus `backlog.md` nehmen (erste Zeile ohne ✅).
3. Fakten mit 1–2 Websuchen prüfen (nur Zahlen, die ins Video kommen). Keine ungeprüften Zahlen.
4. `topics/NN-slug.json` nach dem Muster von `topics/02-trafo.json` schreiben.
   Stil (Vorbild @Selbstgebaut3D): Hook = die Frage, sofort in Sekunde 0. Kurze, bildhafte Sätze, ein Aha-Moment, Wörter erscheinen einzeln groß im Bild (macht build.py automatisch). Titel = Neugier-Frage + Emoji + #shorts.
   Szenentypen: `icon` (icon: turbine|generator|trafo|sine|bolt|sun|battery|bulb|plug), `formula` (max 3 rows), `cards` (max 4), `compare`. Feld `captions` ist nicht mehr nötig.
   Gesprochener Text (`say`): Zahlen als Wörter ausschreiben, kurze Sätze. Ziel 40–60 s. 3–5 Szenen.
5. `python3 pipeline/build.py topics/NN-slug.json` → `out/NN-slug.mp4` (+ 3 Standbilder in /tmp zur Sichtkontrolle, eines ansehen).
6. Video + JSON committen und pushen (main).
   Raw-URL: `https://raw.githubusercontent.com/testblyed-png/technikin60s/main/out/NN-slug.mp4`
7. Upload im eingebauten Browser (Claude-Desktop-App auf Alis PC):
   - `https://studio.youtube.com/channel/UCCOqO6cc4eHwJd_63GL_ghQ/videos/upload?d=ud` öffnen
   - `pipeline/upload.js` mit ersetzten Platzhaltern per javascript_tool ausführen.
   - Lädt als **PRIVAT** hoch. Nie selbst veröffentlichen – Ali schaltet auf öffentlich.
8. `backlog.md`: Thema mit ✅ + Datum markieren, `log.md` eine Zeile anhängen (Datum, Titel, Link). Committen + pushen.
9. Ali per PushNotification kurz informieren: „Neues Video privat hochgeladen: <Titel> – bitte prüfen & veröffentlichen.“

## Regeln
- Nur fachlich korrekte Inhalte, keine Clickbait-Falschaussagen. Quellen für Zahlen in die Beschreibung.
- Musik/Effekte werden selbst generiert (urheberrechtsfrei). Stimme: Thorsten (CC0).
- Wenn Browser/Desktop-App nicht erreichbar: Video trotzdem bauen + pushen, Ali benachrichtigen, Upload beim nächsten Lauf nachholen.
