# Rally

## Beifahrer-Stimme

Die Ansagen des Beifahrers wurden mit [ElevenLabs](https://elevenlabs.io) erzeugt (Stimme "Daniel"), siehe `tools/make_voice.py`.

## Motorgeräusche

Die Motorgeräusche wurden mit ElevenLabs Sound Effects erzeugt und orientieren sich an den echten Rallyeautos
(z. B. Fünfzylinder des Audi Quattro S1, Boxer des Impreza, Dino-V6 des Stratos). Je Auto gibt es fünf nahtlose
Schleifen vom Leerlauf bis kurz vor den Begrenzer (`engine/`); das Spiel blendet je nach Drehzahl zwischen zwei
Stufen über und passt die Tonhöhe an. Erzeugt mit `tools/make_engine.py`, Hörproben mit `tools/engine_demo.py`.
Details: `docs/Motorgeräusche.md`.
