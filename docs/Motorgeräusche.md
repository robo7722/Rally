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


## v14.16 – Motorgeräusche v2 (Rückmeldung: „klingen komplett falsch“)
Stand: 15.11.2026. Betroffen: Mini, 131 Abarth, Stratos, R5 Turbo, alle Gruppe A (M3, Escort, Celica, Delta), alle WRC (Impreza, Lancer).
Unverändert (v1): Quattro S1, RS200, 959, Delta S4, 205 T16, Fulvia, Alpine.

**Ursache (Vergleich mit F1Racing, `docs/SOUNDS.md` dort):**
1. In v1 kam **jede Drehzahlstufe aus einer anderen Zufallsaufnahme** → beim Hochdrehen wechselte der Motor mehrfach seinen Charakter.
   F1Racing nutzt wenige Basisaufnahmen und füllt die Stufen mit **Rubberband** (`formant=preserved`) auf → durchgehend ein Motor.
2. Schwache Prompts: ohne „steady unchanging drone, no revving, no acceleration, no gear change“ und mit Prompt-Treue 0,6 lag die Drehzahl
   wild daneben (3700 verlangt → 3200 bis 6700). Mit den F1-Prompts und Treue 0,8–0,85 treffen die Aufnahmen fast genau (Mini „3000“ → 3170–3230).
3. Drehzahlmessung mit weitem Suchbereich + Oktavkorrektur rastete an Nebengeräuschen ein: Beim Mini erzeugte „straight-cut gearbox whine“
   im Prompt einen konstanten 214-Hz-Ton (Obertöne 428/641/859 Hz) in **allen** Aufnahmen. Jetzt: Suche nur 0,7–1,45 × Soll, kein Getriebeheulen im Prompt.
4. Kein eigener Klang für Gas weg.

**Neu (`tools/make_engine2.py`):**
- Je Auto 5 Basisaufnahmen: Leerlauf (~900), tief (~1800), Last (~3000), Vollgas (~6500), Schub (Gas weg, Blubbern/Knallen). Je 3 Varianten (Schub 2),
  gewählt nach Gleichmäßigkeit + Nähe zur Soll-Drehzahl (beim Leerlauf darf die Tonhöhe schwanken).
- **Drehzahlleiter** 900 · 1300 · 1850 · 2600 · 3500 · 4600 · 5900 · 7400: jede Stufe = nächstliegende Basis, per Rubberband verschoben (meist ≤ 6 Halbtöne).
  Im Spiel wird je Stufe nur ~0,85–1,17-fach nachgestimmt.
- Loops wie bei F1Racing: Ausschnitt 3× → Rubberband → mittleres Drittel, Naht 0,15 s überblendet, RMS 0,14, **WAV mono 32 kHz**.
- Spiel: `engine.json` mit `v: 2`, `steps[].f`, `schub`. Schub-Anteil = `(0,45 − Gas)/0,35 × (U/min − 2500)/1500`, Hauptmotor dabei −35 %,
  Schub läuft am Tiefpass vorbei. Synthetische Fehlzündungs-Knaller entfallen dann (Flammen bleiben).
- Service Worker liest die Dateiliste aus `engine/engine.json`.
- Kosten v2: ca. 7.500 Credits (10 Autos × 14 Aufnahmen + Mini neu); Konto danach 23.392 von 30.005 verbraucht.

| Auto | Basis-Drehzahlen (gemessen) | Leiter-Quellen | Schub U/min |
|---|---|---|---|
| fiat | leer 684 · tief 1545 · last 3850 · voll 7063 · schub 5568 | leer_1 +4.8 HT · tief_1 -3.0 HT · tief_1 +3.1 HT · last_0 -6.8 HT · last_0 -1.7 HT · last_0 +3.1 HT · voll_2 -3.1 HT · voll_2 +0.8 HT | 5568 |
| r5 | leer 903 · tief 2401 · last 3700 · voll 8279 · schub 7334 | leer_0 -0.1 HT · leer_0 +6.3 HT · tief_2 -4.5 HT · tief_2 +1.4 HT · last_0 -1.0 HT · last_0 +3.8 HT · voll_2 -5.9 HT · voll_2 -1.9 HT | 7334 |
| bmw | leer 815 · tief 2085 · last 4181 · voll 6845 · schub 7279 | leer_0 +1.7 HT · leer_0 +8.1 HT · tief_0 -2.1 HT · tief_0 +3.8 HT · last_1 -3.1 HT · last_1 +1.7 HT · voll_0 -2.6 HT · voll_0 +1.3 HT | 7279 |
| delta | leer 1168 · tief 2331 · last 3400 · voll 6393 · schub 5038 | leer_1 -4.5 HT · leer_1 +1.8 HT · tief_2 -4.0 HT · tief_2 +1.9 HT · last_2 +0.5 HT · last_2 +5.2 HT · voll_0 -1.4 HT · voll_0 +2.5 HT | 5038 |
| escort | leer 764 · tief 1895 · last 3390 · voll 7162 · schub 4636 | leer_1 +2.8 HT · tief_0 -6.5 HT · tief_0 -0.4 HT · last_2 -4.6 HT · last_2 +0.6 HT · last_2 +5.3 HT · voll_0 -3.4 HT · voll_0 +0.6 HT | 4636 |
| celica | leer 971 · tief 1701 · last 2938 · voll 8460 · schub 7178 | leer_1 -1.3 HT · tief_0 -4.7 HT · tief_0 +1.5 HT · last_2 -2.1 HT · last_2 +3.0 HT · last_2 +7.8 HT · voll_0 -6.2 HT · voll_0 -2.3 HT | 7178 |
| subaru | leer 810 · tief 1853 · last 3891 · voll 8376 · schub 3553 | leer_2 +1.8 HT · tief_0 -6.1 HT · tief_0 -0.0 HT · tief_0 +5.9 HT · last_0 -1.8 HT · last_0 +2.9 HT · voll_1 -6.1 HT · voll_1 -2.1 HT | 3553 |
| lancer | leer 932 · tief 2247 · last 3719 · voll 7228 · schub 6820 | leer_2 -0.6 HT · leer_2 +5.8 HT · tief_1 -3.4 HT · tief_1 +2.5 HT · last_2 -1.0 HT · last_2 +3.7 HT · voll_0 -3.5 HT · voll_0 +0.4 HT | 6820 |
| stratos | leer 1076 · tief 2640 · last 2592 · voll 7338 · schub 6263 | leer_2 -3.1 HT · leer_2 +3.3 HT · last_2 -5.8 HT · last_2 +0.1 HT · tief_0 +4.9 HT · voll_2 -8.1 HT · voll_2 -3.8 HT · voll_2 +0.1 HT | 6263 |
| mini | leer 950 · tief 1877 · last 3222 · voll 6510 · schub 6665 | leer_0 -0.9 HT · leer_0 +5.4 HT · tief_0 -0.3 HT · last_2 -3.7 HT · last_2 +1.4 HT · voll_2 -6.0 HT · voll_2 -1.7 HT · voll_2 +2.2 HT | 6665 |

**Fehler unterwegs:** Ein Kommentar mitten in einer Code-Zeile (Fehlzündungen) hat die schließende Klammer auskommentiert → das ganze Spiel startete nicht.
Vor jedem Push jetzt: Modul-Skript extrahieren und `node --check`, dann Browser-Test (Playwright).

**Offen / Ideen:**
- Die v1-Autos (Quattro, RS200, 959, S4, 205, Fulvia, Alpine) bei Bedarf ebenfalls auf v2 umstellen: `python tools/make_engine2.py <auto>` (Eintrag in `CARS` ergänzen).
- Basisaufnahmen per Gehör prüfen; die Messung kann bei KI-Aufnahmen weiter danebenliegen.
