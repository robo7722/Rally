# Aufgabe: Echte Motoraufnahmen laden und einbauen (lokal ausführen!)

> Muss **lokal** laufen: In Cloud-Sitzungen sperrt Wikimedia alle Downloads (HTTP 429).
> Start: in einer lokalen Claude-Code-Sitzung im Rally-Ordner sagen: „Arbeite docs/AUFGABE-echte-Motoraufnahmen.md ab“.

## Ziel
Für einige Autos fehlen echte Motoraufnahmen. Lade sie von Wikimedia Commons und baue sie mit `tools/make_engine_real.py`
als eigene Motorgruppen ein. **Nur echte Aufnahmen, keine KI (kein ElevenLabs) für Motorgeräusche.**
Zuerst lesen: `docs/Motorgeräusche.md` (v14.18, v14.19), `engine/QUELLEN.md`, `tools/make_engine_real.py`.

## Stand (v14.19)
- Gruppen in `engine/engine.json`: `turbo4` (Lancer Evo VI, 14 Autos), `sauger4` (Morris Mini: Mini, Fulvia, Alpine). Autos: `{"g": "<gruppe>"}`.
- `tools/make_engine_real.py`: `SOURCES` (Gruppe → Commons-Datei, Zylinder, Urheber, Beschreibung), `GROUPS` (Gruppe → Auto-IDs).
  Lädt nach `tools/_engine_raw/real/`, sucht gleichmäßige Abschnitte, baut 8 Stufen (900–7400 U/min) per Rubberband.
  Nicht ladbare Quelle → Autos fallen auf `turbo4` zurück. `turbo5` (Audi RS3) ist schon eingetragen.
- Auto-IDs: audi, p959, stratos, r5, p205, rs200, s4, delta, escort, celica, lancer, subaru, fiat, bmw, mini, fulvia, alpine.

## Herunterladen (Commons-Sammlung „… - engine and exhaust sound (YouTube …)“, meist CC BY 3.0)
Pfad: `https://upload.wikimedia.org/wikipedia/commons/<md5[0]>/<md5[0:2]>/<Dateiname>` (md5 des Namens mit Unterstrichen).
Unter genau diesem Namen in `tools/_engine_raw/real/` ablegen (das Skript lädt auch selbst). Eigener User-Agent, Pausen zwischen Downloads.
1. `Audi_RS3_-_engine_and_exhaust_sound_(YouTube_uuEytKIzqeY).opus` – Fünfzylinder → `turbo5` für audi (eingetragen)
2. `Subaru_WRX_STI_-_engine_and_exhaust_sound_(YouTube--bynUdphkbc).opus` (alternativ `Subaru_Impreza_STI_with_modified_exhaust_-_engine_and_exhaust_sound_(YouTube_7c4BSSRq3bo).opus`) → neue Gruppe `boxer4` für subaru
3. `Ford_Escort_RS2000_(Supersprint_exhaust)_-_engine_and_exhaust_sound_(YouTube_B2swcWkMOMM).opus` – Sauger mit hohen Drehzahlen → bessere Quelle für `sauger4`, ggf. Gruppe `sauger16v` für fiat, bmw
4. `Renault_5_Turbo_2_-_engine_and_exhaust_sound_(YouTube_9yqNZjwGvCo).opus` – optional für r5
5. Sechszylinder suchen („<Auto> engine and exhaust sound“): Boxer-Sechs (Porsche 911) für p959, V6 (Ferrari Dino, Alfa V6, Lancia) für stratos; sonst beide `turbo5`.

Lizenz/Urheber je Datei prüfen: Commons-API `action=query&prop=imageinfo&iiprop=extmetadata` (LicenseShortName, Artist). Nur CC BY / CC BY-SA / gemeinfrei.

## Einbauen
- `SOURCES`/`GROUPS` ergänzen (Zylinder: Boxer-4 = 4, Reihen-5 = 5, Sechszylinder = 6); jedes Auto genau in einer Gruppe.
- `python tools/make_engine_real.py` (braucht ffmpeg **mit rubberband** – `ffmpeg -filters | findstr rubberband` –, numpy, scipy).
- Ausgabe prüfen: Abschnitte sollen 900–7400 U/min möglichst abdecken; Verschiebungen > ~6 Halbtöne klingen künstlich. Aufnahmen mit nur Leerlauf nicht verwenden.
- Hörproben: `python tools/engine_demo.py <auto-id>` → `engine_demo/<auto>.mp3`.
- Quellen nachtragen: `engine/QUELLEN.md`, README „Motorgeräusche“, Quellenzeile in `index.html` (Einstellungen unter „Effekte“, `<small …>Motorgeräusche: …</small>`).
- Version v14.19 → v14.20 in `index.html` (Titel + `const VERSION`) und `sw.js` (`rally-racing-v14-19`).
- Vor dem Commit: Modul-Skript aus `index.html` extrahieren und `node --check` (ein Syntaxfehler legt das ganze Spiel lahm).
- `docs/Motorgeräusche.md` um Abschnitt v14.20 ergänzen; committen und auf `main` pushen.

## Fertig, wenn
Audi, Impreza und möglichst 959/Stratos eigene echte Aufnahmen nutzen, alle Quellen genannt sind, das Spiel fehlerfrei startet und alles auf `main` liegt.
