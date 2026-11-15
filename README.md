# Rally

## Beifahrer-Stimme

Die Ansagen des Beifahrers wurden mit [ElevenLabs](https://elevenlabs.io) erzeugt (Stimme "Daniel"), siehe `tools/make_voice.py`.

## Motorgeräusche

Die Motorgeräusche wurden mit ElevenLabs Sound Effects erzeugt und orientieren sich an den echten Rallyeautos
(z. B. Fünfzylinder des Audi Quattro S1, Boxer des Impreza, Dino-V6 des Stratos). Je Auto gibt es fünf nahtlose
Schleifen vom Leerlauf bis kurz vor den Begrenzer (`engine/`); das Spiel blendet je nach Drehzahl zwischen zwei
Stufen über und passt die Tonhöhe an. Erzeugt mit `tools/make_engine.py` (v1) bzw. `tools/make_engine2.py` (v2: wenige Basisaufnahmen, Drehzahlleiter per Rubberband, Schub-Loop), Hörproben mit `tools/engine_demo.py`.
Details: `docs/Motorgeräusche.md`.

**Motorgeräusche ab v14.18:** Die meisten Autos nutzen echte Aufnahmen von Wikimedia Commons (CC BY 3.0):
„Mitsubishi Lancer Evolution VI – engine and exhaust sound“ von *prone* und „Morris Mini – engine and exhaust sound“ von
*Luciano's Classics*, geschnitten und in der Tonhöhe angepasst. Details und Links: `engine/QUELLEN.md`.
