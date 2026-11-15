---
tags: [rally, audio, elevenlabs, motor]
erstellt: 2026-11-15
version: v14.15
---
# Motorgeräusche (ElevenLabs)

Realistische Motorgeräusche für alle 17 Autos, an den echten Rallyeautos orientiert, erzeugt mit ElevenLabs Sound Effects
(`eleven_text_to_sound_v2`, `loop: true`). Ersetzt den bisher rein synthetischen Motor (der bleibt als Rückfallebene).

## Prinzip
- Je Auto **fünf Drehzahlstufen** als nahtlose Schleife: Leerlauf, niedrig, mittel, hoch, kurz vor dem Begrenzer (`engine/<auto>_<stufe>.mp3`).
- Im Spiel laufen immer die **zwei Stufen**, zwischen denen die aktuelle Drehzahl liegt: Überblendung mit gleicher Leistung (cos/sin),
  Tonhöhe = Drehzahl / gemessene Aufnahme-Drehzahl (`playbackRate`).
- Ohne Gas: Tiefpass (dumpfer, Schiebebetrieb); Lautstärke steigt mit Drehzahl und Gas; beim Schalten kurzer Einbruch.
- Fehlschüsse, Turbo-Abblasen und Flammen bleiben aus dem bisherigen Code; das synthetische Turbopfeifen ist leiser, weil es meist schon in den Aufnahmen steckt.

## Erkenntnisse
- ElevenLabs hält eine Drehzahl im Prompt nur **grob** ein: derselbe Prompt „3700 rpm“ ergab mal 3200, mal 6700 U/min.
  Deshalb: Pool von Aufnahmen je Auto, jede wird gemessen, dann die beste Besetzung der Stufen gewählt.
- Drehzahlmessung über die Zündfrequenz (Autokorrelation, Zündfrequenz = U/min × Zylinder / 120); mit synthetischen Signalen auf < 1 % geprüft.
- Viele Aufnahmen drehen am Anfang kurz hoch → es wird automatisch der **gleichmäßigste 2,6-s-Abschnitt** genommen (Klangspektrum + Lautstärke).
- Stufen müssen **aufsteigen** (≥ 15 %), sonst springt die Tonhöhe beim Überblenden.
- MP3-Versatz im Browser: Datei hat 0,1 s Vor-/Nachlauf aus der Schleife selbst, `loopStart`/`loopEnd` im Spiel → keine Lücke.
- Kosten: ca. 50 Credits je 5-s-Aufnahme, insgesamt ~15.900 Credits für alle Autos.

## Gemessene Drehzahl je Stufe (U/min)
| Auto | Motor-Vorbild | Zyl. | Leerlauf · niedrig · mittel · hoch · max |
|---|---|---|---|
| fiat | Fiat 131 Abarth Rally | 4 | 1170 · 1936 · 3538 · 4287 · 6645 |
| r5 | Renault 5 Turbo rally car | 4 | 1093 · 2333 · 3460 · 4212 · 8042 |
| bmw | BMW M3 E30 Group A rally car | 4 | 993 · 2291 · 3514 · 5890 · 7176 |
| delta | Lancia Delta HF Integrale Group A | 4 | 1178 · 2788 · 3740 · 4812 · 6663 |
| escort | Ford Escort RS Cosworth rally car | 4 | 957 · 1886 · 3250 · 5540 · 6456 |
| celica | Toyota Celica GT-Four ST185 rally car | 4 | 1163 · 2334 · 3802 · 4875 · 7442 |
| subaru | Subaru Impreza WRC rally car | 4 | 809 · 1754 · 3303 · 3857 · 5516 |
| lancer | Mitsubishi Lancer Evolution WRC rally car | 4 | 736 · 2241 · 3675 · 4856 · 7442 |
| audi | Audi Sport Quattro S1 E2 Group B rally car | 5 | 929 · 2165 · 2937 · 5598 · 7240 |
| rs200 | Ford RS200 Group B rally car | 4 | 1221 · 2451 · 3939 · 5091 · 7225 |
| p959 | Porsche 959 rally car | 6 | 1150 · 2312 · 3196 · 5683 · 8751 |
| s4 | Lancia Delta S4 Group B rally car | 4 | 1038 · 2736 · 3289 · 5085 · 7410 |
| p205 | Peugeot 205 Turbo 16 Group B rally car | 4 | 838 · 2378 · 3548 · 4434 · 8237 |
| stratos | Lancia Stratos HF rally car | 6 | 736 · 2639 · 4519 · 5561 · 9654 |
| mini | classic Mini Cooper S rally car | 4 | 1124 · 3120 · 3623 · 5226 · 7070 |
| fulvia | Lancia Fulvia HF rally car | 4 | 759 · 2389 · 3206 · 5639 · 6939 |
| alpine | Alpine A110 1600S rally car | 4 | 808 · 2065 · 4127 · 5561 · 7286 |

## Dateien
- `tools/make_engine.py` – Erzeugung, Analyse, Auswahl, Schleifenbau (`python tools/make_engine.py [auto ...]`)
- `tools/engine_demo.py` – rendert Hörproben mit der Spiel-Logik (Leerlauf → Gasstoß → Hochschalten → Gas weg)
- `engine/engine.json` – Schleifenlänge und gemessene Drehzahl („ref“) je Stufe
- `engine_demo/<auto>.mp3` – Hörproben
- `index.html`: `ENG`, `engLoad`, `engUpd` (Abschnitt „Motor aus echten Aufnahmen“)

## Ideen / offen
- Subaru (Boxer) hat kaum klare Obertöne; ggf. mit gezieltem Prompt nachgenerieren.
- Getrennte Schleifen für Last/Schiebebetrieb (on/off throttle) würden noch realistischer klingen.
- Innenraum-Variante für Cockpit-Kamera (stärker gedämpft).
