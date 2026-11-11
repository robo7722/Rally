# Erzeugt die Beifahrer-Schnipsel in voice/ (edge-tts, Microsoft Neural-Stimme).
# Je Ansage zwei Betonungen: <key>_m.mp3 = mitten im Satz (Stimme bleibt oben), <key>.mp3 = Satzende (Stimme senkt sich).
# Aufruf: python tools/make_voice.py [Zielordner]
import asyncio, os, sys
import edge_tts

VOICE = "de-DE-FlorianMultilingualNeural"
RATE = "+18%"
NUM = ["eins", "zwei", "drei", "vier", "fünf", "sechs"]
DIST = {50: "fünfzig", 100: "hundert", 150: "hundertfünfzig", 200: "zweihundert", 250: "zweihundertfünfzig", 300: "dreihundert", 350: "dreihundertfünfzig", 400: "vierhundert"}
BOTH = {"hn": "Haarnadel", "lang": "lang", "zz": "zieht zu", "of": "öffnet", "ns": "nicht schneiden", "lg": "lange Gerade",
        "zs": "Zuschauer auf der Strecke", "leicht": "leicht", "mittel": "mittel", "eng": "eng", "neunzig": "neunzig",
        "kuppe": "Kuppe", "sprung": "Sprung", "eis": "Eis"}
for i, n in enumerate(NUM, 1):
    BOTH[f"l{i}"] = f"Links {n}"; BOTH[f"r{i}"] = f"Rechts {n}"
for d, w in DIST.items():
    BOTH[f"d{d}"] = w
JOBS = {}
for k, t in BOTH.items():
    JOBS[k] = t + "."
    JOBS[k + "_m"] = t + ","
JOBS["ach"] = "Achtung!"
JOBS["in"] = "in"
JOBS["go"] = "Los geht's!"
JOBS["ziel"] = "Ziel! Gut gemacht."
JOBS["ready"] = "Beifahrer bereit."

async def one(out, key, text, sem):
    async with sem:
        for attempt in range(4):
            try:
                await edge_tts.Communicate(text, VOICE, rate=RATE).save(os.path.join(out, key + ".mp3"))
                return
            except Exception as e:
                if attempt == 3: raise
                await asyncio.sleep(1 + attempt)

async def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "voice"
    os.makedirs(out, exist_ok=True)
    sem = asyncio.Semaphore(4)
    await asyncio.gather(*(one(out, k, t, sem) for k, t in JOBS.items()))
    print(len(JOBS), "Dateien in", out)

asyncio.run(main())
