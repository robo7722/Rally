# Rally

## Beifahrer-Stimme

Die Ansagen des Beifahrers wurden mit [ElevenLabs](https://elevenlabs.io) erzeugt (Stimme "Daniel"), siehe `tools/make_voice.py`.

## Motorgeräusche

Alle Motorgeräusche sind echte Aufnahmen von Wikimedia Commons (CC BY 3.0): „Mitsubishi Lancer Evolution VI – engine and exhaust
sound“ von *prone* (Turbo-Vierzylinder, 14 Autos) und „Morris Mini – engine and exhaust sound“ von *Luciano's Classics*
(Sauger-Vierzylinder, Mini/Fulvia/Alpine), geschnitten, zu Loops verlängert und in der Tonhöhe angepasst
(`tools/make_engine_real.py`, Hörproben `tools/engine_demo.py`). Das Spiel blendet je nach Drehzahl zwischen acht Stufen über.
Details und Links: `engine/QUELLEN.md`, `docs/Motorgeräusche.md`.
