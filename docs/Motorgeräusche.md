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

## v14.17 – Stratos klang wie ein Elektroauto
Stand: 15.11.2026.

**Messung:** Die oberen Stratos-Stufen waren fast reine Töne (spektrale Flachheit 0,004; andere Autos 0,03–0,13) mit **0 % Energie unter 250 Hz**:
nur Heulen, keine Verbrennung, kein Auspuffdruck → E-Motor-Klang. Ursache: Prompt „high-pitched exotic Italian V6 howl“.
Alle anderen v2-Autos geprüft: unauffällig (wenig Flachheit kommt dort mit viel Tiefton = normales Grollen).

**Änderungen (`tools/make_engine2.py`):**
- Stratos-Prompt betont Verbrennung: „loud raw gritty combustion, deep raspy exhaust roar, mechanical rattle, intake gurgle“
  (das Wort „electric“ bewusst nicht verwendet, Verneinungen lenken das Modell oft erst dorthin). Prompt-Grenze bei ElevenLabs: **450 Zeichen**.
- Neues Klangmaß `timbre()`: Flachheit 40 Hz–8 kHz und Tiefton-Anteil 30–250 Hz. **Elektro-Signatur = Flachheit < 0,02 und Tiefton < 10 %** →
  Strafwert 3, solche Aufnahmen werden automatisch aussortiert (gilt für alle künftigen Autos).
- Raue Aufnahmen ohne klaren Ton: Messung unsicher (Sicherheit < 0,25) → verlangte Drehzahl als Referenz statt Zufallswert
  (Stratos-Vollgas maß 4.600 am Rand des Suchbereichs und wäre +8 Halbtöne verschoben worden).
- `TAKES=4` als Umgebungsvariable für mehr Varianten.

**Ergebnis Stratos** (Flachheit/Tiefton je Stufe): 0,005/99 · 0,006/98 · 0,001/99 · 0,011/93 · 0,014/85 · 0,065/63 · 0,066/56 · 0,082/55 (vorher oben 0,004/0).
Kosten: ~700 Credits.

## v14.18 – Echte Aufnahmen, Motoren zusammengefasst
Stand: 15.11.2026. Rückmeldung: „Subaru wie ein Traktor, auf einem springt der Sound, BMW komplett falsch. Weniger unterschiedliche
Motoren, dafür gute. Mit Originalen abgleichen. – Kannst du nicht die echten Geräusche nehmen?“

**Quellen:** Wikimedia Commons hat eine Sammlung „<Auto> – engine and exhaust sound (YouTube …)“ unter **CC BY 3.0** (Namensnennung nötig →
Einstellungen unter „Effekte“, README, `engine/QUELLEN.md`). Geladen: Lancer Evo VI, Lancia Delta Integrale, Morris Mini.
Gefunden, aber wegen Drosselung (HTTP 429 von upload.wikimedia.org, auch mit Pausen) **nicht** geladen: Subaru WRX STI, Escort RS2000
(Supersprint), Renault 5 Turbo 2, Subaru Impreza STI, Alpine A110 (2017), BMW M3 (neuere Modelle). Direkter Pfad:
`https://upload.wikimedia.org/wikipedia/commons/<md5[0]>/<md5[0:2]>/<Dateiname>` (md5 des Dateinamens mit Unterstrichen).

**Gruppen (5 Klangsätze statt 17):**
| Gruppe | Quelle | Autos |
|---|---|---|
| turbo4 | Lancer Evo VI (echt) | R5, 205, RS200, S4, Delta, Escort, Celica, Lancer, Impreza, 131, M3 |
| sauger4 | Morris Mini (echt) | Mini, Fulvia, Alpine |
| eigen | ElevenLabs | Quattro S1, 959, Stratos |

**Verfahren (`tools/make_engine_real.py`):**
1. Drehzahlverlauf der Aufnahme alle 50 ms (Zündfrequenz, Autokorrelation; Vierzylinder U/min = Hz × 30).
2. Gleichmäßige Abschnitte: Tonhöhe ±3 %, klare Periode (Güte > 0,5), höchstens 22 dB unter dem Lautesten, ≥ 0,35 s.
   Lancer: 31 Abschnitte 1.250–6.820 U/min. Mini: 10 Abschnitte, nur 770–840 und 2.550–3.340 U/min. Delta: nur ~1.600 U/min (nicht genutzt).
3. Leiter 900…7.400 U/min: je Stufe der Abschnitt mit der kleinsten Verschiebung (Güte und Länge zählen mit).
4. Abschnitte sind kurz (0,4–1 s) → zu **2-s-Loops verlängert**: zufällige Körner (0,15 s, Hann, 50 % Überlappung), immer um ganze
   Zündperioden versetzt und im Zündtakt platziert → phasengleich, kein Wiederholungsmuster, kreisförmig nahtlos.
5. Rubberband (Formanten erhalten), RMS 0,14, WAV 32 kHz. Spiel: `engine.json` → `groups`, Autos mit `{"g": …}`.

**Abgleich mit dem Original** (Spektrum in 24 Bändern 40 Hz–8 kHz, Abweichung / Korrelation je Stufe):
- turbo4: 1300 0,7 dB/1,00 · 1850 2,4/0,94 · 2600 0,4/1,00 · 3500 0,6/1,00 · 4600 1,1/1,00 · 5900 1,8/0,96 · 7400 2,7/0,89; Leerlauf 900 (−5,6 HT) 6,7/0,78.
- sauger4: gut bis 3.500 (≤ 2,2 dB/≥ 0,97); oben stark verschoben (4600 +5,5 HT 6,7/0,72 · 5900 +9,8 HT 7,5/0,68 · 7400 +13,8 HT 8,5/0,64).
  Deshalb 131 und M3 (16V bis > 7.000 U/min) in die Turbo-Gruppe; Mini/Fulvia/Alpine bleiben beim Mini-Klang.
- Feste Linie um ~700 Hz in der Turbo-Hörprobe: keine Störung, sondern eine Resonanz, die schon im Original zu sehen ist.

**Offen:**
- Escort RS2000 laden (sobald Wikimedia nicht mehr drosselt) → echte Sauger-Aufnahme mit hohen Drehzahlen für Mini/Fulvia/Alpine (und evtl. 131/M3).
- Subaru WRX STI laden → echter Boxer für das Impreza, falls gewünscht (aktuell Turbo-Gruppe, damit kein „Traktor“).
- Kein Schub-Loop in den echten Gruppen (Fehlzündungen kommen synthetisch).

## v14.19 – Nur noch echte Motorgeräusche, kein ElevenLabs mehr
Stand: 15.11.2026. Wunsch: „Kein ElevenLabs mehr, nur noch die echten Motorensounds angepasst.“

- Quattro S1, 959 und Stratos (bisher ElevenLabs) nutzen jetzt die echte **Turbo-Vierzylinder**-Aufnahme (Lancer Evo VI).
- Gefunden: **Audi RS3** (2,5-TFSI-Fünfzylinder, Nachfahre des Quattro-Motors) – `File:Audi_RS3_-_engine_and_exhaust_sound_(YouTube_uuEytKIzqeY).opus`.
  Download scheiterte (Wikimedia 429, 6 Versuche über 8 Minuten). Ist in `tools/make_engine_real.py` als Gruppe `turbo5` für
  Quattro S1, 959 und Stratos eingetragen und wird automatisch genutzt, sobald der Download klappt (Skript erneut ausführen).
  Lizenz/Urheber dann in `engine/QUELLEN.md` und Einstellungen ergänzen.
- Entfernt: `tools/make_engine.py`, `tools/make_engine2.py` (ElevenLabs-Motoren), alle `audi_*`, `p959_*`, `stratos_*` in `engine/`.
  Die Beifahrer-Stimme (voice/) ist weiterhin ElevenLabs – betrifft nur die Motoren.
- `engine/` jetzt 16 WAV-Loops (2 Gruppen × 8 Stufen), ~3,5 MB.

## v14.20 – Eigene echte Aufnahmen für Quattro S1, Impreza, 959 und Stratos
Stand: 15.11.2026, lokal ausgeführt (`docs/AUFGABE-echte-Motoraufnahmen.md`; in der Cloud sperrt Wikimedia mit HTTP 429).
Alle neuen Quellen: Wikimedia Commons, **CC BY 3.0**, Lizenz und Urheber per Commons-API (`extmetadata`) geprüft.

**Gruppen (6 Klangsätze):**
| Gruppe | Aufnahme (Urheber) | Autos | Abdeckung / größte Verschiebung |
|---|---|---|---|
| turbo4 | Lancer Evo VI (prone) | R5, 205, RS200, S4, Delta, Escort, Celica, Lancer, 131, M3 | unverändert |
| sauger4 | Morris Mini (Luciano's Classics) | Mini, Fulvia, Alpine | unverändert |
| turbo5 | Audi RS3 (Jay Chesterman) | Quattro S1 | 450–6.800 U/min, max. −5,1 HT (1850) |
| boxer4 | Subaru Impreza STI mit Sportauspuff (Great Explorer) | Impreza | 550–6.000 U/min, max. +3,6 HT (7400) |
| boxer6 | Porsche 911 GT3 RS (Supercars67) | 959 | 1.040–8.480 U/min, max. +3,3 HT (4600) |
| v6 | Alfa Romeo GTV6, Busso-V6 (Doppia Frizione) | Stratos | 390–4.200 U/min, oben +5,9 HT (5900) / +9,8 HT (7400) |

**Skript (`tools/make_engine_real.py`):**
- Messfehler behoben: Die Tonhöhensuche endete bei 320 Hz. Treffer genau am Rand sind keine echte Periode (Audi zeigte dort ~60
  Scheinabschnitte bei „7.782 U/min“) → Randtreffer bekommen Güte 0. Obergrenze jetzt zylinderabhängig (8.500 U/min, mind. 320 Hz):
  Sechszylinder wurden vorher nur bis 6.400 U/min erkannt.
- `SOURCES` je Gruppe: (Zylinder, Beschreibung, Liste von (Datei, Urheber)). Mehrere Aufnahmen pro Gruppe möglich – je Stufe gewinnt der
  beste Abschnitt aus allen. `credit` in `engine.json` ist jetzt eine Liste.
- Ist eine Aufnahme gerade nicht ladbar, bleibt eine schon gebaute Gruppe erhalten (vorher fiel sie auf turbo4 zurück – beim
  erneuten Ausführen hätte das Mini/Fulvia/Alpine umgehängt, weil Lancer/Mini nicht im Repo liegen).
- `tools/engine_demo.py` lief seit v14.18 nicht mehr (`pad` fehlt bei Gruppen) – repariert.
- Werkzeuge unter Windows (ARM64): `winget install Gyan.FFmpeg` (full build mit Rubberband), `pip install scipy`.

**Geprüft und nicht genommen:**
- Subaru WRX STI (Hungarian Supercar Spotters): nur bis ~3.500 U/min → Impreza STI genommen.
- Ford Escort RS2000 (Shamrock): nur 1.230–3.460 U/min, oben +5 bis +13 HT → nicht besser als der Mini; keine Gruppe `sauger16v`,
  131 und M3 bleiben bei turbo4.
- Renault 5 Turbo 2 (ECHAPPEMENT LIBRE): 32 s, nur 3.800–8.300 U/min → R5 bleibt bei turbo4.
- Porsche 911 Turbo (Adam Coats): bis 4.600 U/min, oben +8 HT; Porsche 996 und 911 GT2: fast nur Leerlauf; GT3 RS (hpwTF8TXcaA):
  gut, aber kürzer als 1t2wz1iLHJ4.
- Fiat 130 Coupé (V6): nur 5 Abschnitte.

**Offen:**
- Stratos: oben +5,9/+9,8 Halbtöne (GTV6-Aufnahme dreht kaum über 4.200). Nachgeladen und geprüft (später am 15.11.2026),
  keine hilft oben: Alfa 147 (tVyI5DC3F9k) nur 2 Abschnitte 2.900/3.600 U/min; Alfa 156 (UwnBSjQfJt8) und Renault Laguna II V6
  (F9eJ7lo4Zno) keine gleichmäßigen Abschnitte; Alfa 159 (EA7OiOGca4A) 550–3.700 U/min. Gesucht bleibt eine V6-Aufnahme mit
  gleichmäßigen Abschnitten über 5.000 U/min; eintragen als zweite Datei in `SOURCES["v6"]`, Skript erneut ausführen.


## v14.21 – Motorsound in Schichten nach der F1Racing-Anleitung
Stand: 15.11.2026. Vorlage: F1Racing `docs/MOTORSOUND-ANLEITUNG.md` (Roadster v2.14, vom Nutzer abgenommen).
Umgesetzt für die zwei Gruppen, deren Rohaufnahmen in der Cloud vorliegen: **turbo4** (10 Autos) und **sauger4** (Mini, Fulvia, Alpine).
turbo5/boxer4/boxer6/v6 (Quattro, Impreza, 959, Stratos) laufen weiter als Drehzahl-Leiter aus v14.20 – Rohaufnahmen nur lokal.

### Wichtigster Befund: die alte Turbo-Leiter war falsch gemessen
Drehzahl-/Pegel-Diagramme der Aufnahmen (wie in der Anleitung, Abschnitt 3) zeigen:
- **Lancer Evo VI = Onboard-Fahrt**, Drehzahl im Sägezahn durch die Gänge, **nur 4.000–7.400 U/min**, kein Leerlauf, keine niedrigen Drehzahlen.
  Die alte Messung (kurzes Fenster, ohne Oktav-Prüfung) hielt Punkte bei 1.250–3.500 U/min für niedrige Drehzahlen – das waren Oktavfehler.
  Folge in v14.18–v14.20: im Spiel lief bei 1.300 U/min in Wahrheit ein Motor mit ~5.000 U/min → „klingt falsch“.
- **Morris Mini**: Leerlauf ~790 U/min (lange Periode geprüft, halbe Periode nicht periodisch), 3 echte Gasstöße (bis 2.950 / 4.250 / 5.750),
  Fahrt 2.000–4.400 U/min. Ideal für die Vorlage.
- **Lancia Delta Integrale** (neu als Quelle, CC BY 3.0, Grzegorz Kalinecki): Kaltstart – Gasstöße bis 4.200/5.200, freier Durchzug
  2.400 → 5.160 U/min (8,15–9,7 s), danach 1 min erhöhter Leerlauf ~1.600 U/min.

### Schichten (Datei `engine/engine.json`, Gruppen mit `"v": 3`)
| Schicht | turbo4 | sauger4 |
|---|---|---|
| Leerlauf-Loop | Delta 30,5 s, 3 s, −6 HT → 38.5 Hz ≈ 1155 U/min | Mini 19,85 s, 1,6 s → 27.8 Hz ≈ 834 U/min |
| Gasstöße | Delta 12,05 s (2,1 s) | Mini 7,85 s / 11,55 s / 15,65 s |
| Durchzug (Granular) | Delta 8,15–9,7 s (2.418→5.161) + Lancer 11,95–14,3 s (4.267→6.358), Übergabe 4714 ± 447 | Mini 15,72–16,86 s (1.684→5.749) |
| Granular ein / aus | 1386→2055 / [5722, 6358] | 1001→1432 / bis oben |
| Stufe oben | Lancer 14,6 s (0,6 s, zu 2 s verlängert) ≈ 6.930 U/min | – |
| Gas weg | Lancer 56,55 s ≈ 5.270 U/min | – (synthetische Fehlzündungen) |
| Drehzahl-Faktor `scale` | 1,0 | 0,74 (Mini dreht ~6.000: Spiel 7.800 → Klang 5.770) |

### Aufbereitung (`tools/make_engine_schichten.py`)
Wie Anleitung Abschnitt 4: Tonhöhe der Loops glätten (`flatten`, 32-ms-Messung ±25 %), Loop-Naht gleich laut überblenden (kurze Abschnitte:
Körner im Zündtakt auf 2 s), RMS 0,14, höchstens ±6 HT; Gasstöße: 10 ms ein, 0,25 s aus, Pegel über dem Leerlauf mit Exponent 0,45;
Durchzug: Drehzahl-Tabelle (25 ms, Median ±0,1 s, monoton). **Zusätzlich**: Durchzug-Pegel auf eine glatte Zielkurve gebracht
(0,11 → 0,17 mit der Drehzahl, Hüllkurve 0,2 s) – sonst Loch beim Anfahren (Delta-Durchzug beginnt kalt und leise, −9 dB) und an der Übergabe.
Grundton jeder Schleife mit Drehzahl-Hinweis aus dem Diagramm gemessen (±35 %), sonst Oktavfehler (Lancer-Stufe maß erst 3.478 statt 6.927).

### Spiel (`index.html`, `engCfg` / `engLoad` / `engUpd` / `engGran`)
Port von `sndEngine`/`granTick` aus F1Racing: Loops logarithmisch mit Fenster `[0,38; 0,24]` + Smoothstep überblendet, Granular alle 33 ms
ein 100-ms-Korn (phasenrichtig, über dem Ende ≤ 1,04-fach), Gasstoß im Stand (Gas > 45 % nach < 40 %, Auto steht; Loops stumm; Gas nach der
Spitze gehalten → Loops übernehmen), Schub `(0,45 − Gas)/0,35 × (U/min − 3.200)/2.000` mit Neustart an zufälliger Stelle, Tiefpass
1.500 + Gas·10.500 Hz, Gasgeben blendet weich ein (0,14 s). Synthetische Fehlzündungs-Knaller nur ohne Schub-Loop.
Alte Leiter-Gruppen (v2) laufen über denselben Code (`engCfg` wandelt sie in Loops mit durchgehender Überblendung um).

### Prüfung
- `tools/engine_hoerprobe_spiel.js`: lädt den **echten Motor-Code** aus `index.html` in eine leere Seite und rendert offline denselben Ablauf
  (OfflineAudioContext) → `engine_demo/<auto>.mp3` + Pegel je 0,1 s. Keine Fehler; Gasstöße, Körner, Schub laufen.
  (Das ganze Spiel headless zu fahren ist zu langsam: Software-3D, jedes 50-ms-Warten > 1 s.)
- `tools/engine_hoerprobe.py`: dasselbe in Python (ohne Browser). Ablauf/Zeittabelle:

| Sekunde | Ablauf |
|---|---|
| 0–2,5 | Leerlauf |
| 2,5 / 5,6 | Gasstoß im Stand |
| 9,4–12,2 | Anfahren Vollgas bis 7.000 |
| 12,2–12,4 | Schalten |
| 12,4–14,4 | Vollgas 5.000 → 7.300 |
| 14,4–17,0 | Gas weg bis Leerlauf |
| 17,0–18,5 | Leerlauf |

- Pegel: sauger4 ohne Sprünge außer dem gewollten Einsatz der Gasstöße; turbo4 nach Pegel-Glättung ohne Löcher, kleine Delle (~4 dB) an der
  Übergabe Delta→Lancer (beide Durchzüge dort gleich laut 0,14–0,16 → natürliche Schwankung).
- Zweiter Delta-Gasstoß (7,95 s) verworfen: beginnt im leisen Kaltstart, nach dem Angleichen fast doppelt so laut.

### Offen
- turbo5/boxer4/boxer6/v6 ebenfalls in Schichten aufbauen (lokal, Rohaufnahmen dort): Diagramme zeichnen, Abschnitte wählen, in `SCHICHTEN` eintragen.
- turbo4 hat nur einen echten Gasstoß; Lancer-Aufnahme hat keinen Leerlauf. Bessere Turbo-Aufnahme mit Leerlauf + Gasstößen + Durchzug suchen.
- `tools/engine_demo.py` entfernt (ersetzt durch die beiden Hörprobe-Werkzeuge).

## v14.22 – Zurück zum synthetischen Motor
Stand: 15.11.2026. Wunsch des Nutzers: „Lass uns wieder die synthetischen Sounds wie ursprünglich gehabt nehmen.“

- `index.html`, `sw.js`, `README.md` auf den Stand **v14.14** zurückgesetzt (vor allen Motoraufnahmen): der Motor ist wieder der
  ursprüngliche Web-Audio-Synthesizer (Abschnitt „Ton: Motor, Drift, Effekte, Musik“, `initAudio`/`updAudio`). Seit v14.14 hatte sich in
  diesen Dateien nur der Motor-Code geändert, sonst nichts.
- Entfernt: `engine/`, `engine_demo/`, `tools/make_engine_real.py`, `tools/make_engine_schichten.py`, `tools/engine_hoerprobe.py`,
  `tools/engine_hoerprobe_spiel.js`, `docs/AUFGABE-echte-Motoraufnahmen.md`. Die Quellenangaben der Commons-Aufnahmen entfallen damit.
- **Wiederherstellen**: alles liegt in der Git-Historie. Letzter Stand mit echten Aufnahmen (Schichten): Commit `15498bb` (v14.21),
  z. B. `git checkout 15498bb -- engine tools/make_engine_schichten.py …` und `index.html` aus diesem Commit.

### Rückblick (Kurzfassung)
| Version | Ansatz | Ergebnis |
|---|---|---|
| v14.15–v14.17 | ElevenLabs, 5–8 KI-Loops je Auto | Drehzahl im Prompt nur grob getroffen, Stufen aus verschiedenen Aufnahmen, Stratos „wie Elektroauto“ |
| v14.18–v14.20 | echte Commons-Aufnahmen, Drehzahl-Leiter | Lancer-Aufnahme falsch vermessen (Onboard nur 4.000–7.400 U/min, Oktavfehler) |
| v14.21 | Schichten nach F1Racing-Anleitung | nicht mehr abgenommen – zurück zum Synthesizer |
