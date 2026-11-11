# Erzeugt die Beifahrer-Schnipsel in voice/ (edge-tts, Microsoft Neural-Stimme de-DE-ConradNeural).
# Je Ansage zwei Betonungen:
#   <key>.mp3    = Satzende (Stimme senkt sich): das Wort allein mit Punkt gesprochen
#   <key>_m.mp3  = Satzmitte (Stimme bleibt oben): aus einem ganzen Satz "<Wort>, rechts vier." herausgeschnitten,
#                  denn nur im Satzzusammenhang betont die Stimme so, als ginge es weiter
# Braucht: pip install edge-tts imageio-ffmpeg
# Aufruf: python tools/make_voice.py [Zielordner]
import array, asyncio, os, subprocess, sys
import edge_tts, imageio_ffmpeg

VOICE = "de-DE-ConradNeural"
RATE = "+8%"
SR = 24000
FF = imageio_ffmpeg.get_ffmpeg_exe()
NUM = ["eins", "zwei", "drei", "vier", "fünf", "sechs"]
DIST = {50: "fünfzig", 100: "hundert", 150: "hundertfünfzig", 200: "zweihundert", 250: "zweihundertfünfzig", 300: "dreihundert", 350: "dreihundertfünfzig", 400: "vierhundert"}
# Wörter, die mitten im Satz und am Ende vorkommen
BOTH = {"hn": "Haarnadel", "lang": "lang", "zz": "zieht zu", "of": "öffnet", "ns": "nicht schneiden",
        "zs": "Zuschauer auf der Strecke", "leicht": "leicht", "mittel": "mittel", "eng": "eng", "neunzig": "neunzig",
        "kuppe": "Kuppe", "sprung": "Sprung", "eis": "Eis"}
for i, n in enumerate(NUM, 1):
    BOTH[f"l{i}"] = f"Links {n}"; BOTH[f"r{i}"] = f"Rechts {n}"
    BOTH[f"il{i}"] = f"in Links {n}"; BOTH[f"ir{i}"] = f"in Rechts {n}"   # "in" gleich mitgesprochen: fließt natürlicher
# nur am Satzende bzw. als eigener Satz
END = {"lg": "lange Gerade.", "ach": "Achtung!", "in": "in", "go": "Los geht's!", "ziel": "Ziel! Gut gemacht.", "ready": "Beifahrer bereit."}
for d, w in DIST.items():
    END[f"d{d}"] = w + "."

async def tts(text):
    """-> (mp3-Bytes, [(Wort, Start s, Ende s)])"""
    for attempt in range(4):
        try:
            audio, words = bytearray(), []
            async for ch in edge_tts.Communicate(text, VOICE, rate=RATE, boundary="WordBoundary").stream():
                if ch["type"] == "audio": audio += ch["data"]
                elif ch["type"] == "WordBoundary": words.append((ch["text"], ch["offset"] / 1e7, (ch["offset"] + ch["duration"]) / 1e7))
            if audio: return bytes(audio), words
        except Exception:
            if attempt == 3: raise
        await asyncio.sleep(1 + attempt)
    raise RuntimeError("keine Audiodaten: " + text)

def decode(mp3):
    pcm = subprocess.run([FF, "-v", "error", "-i", "pipe:0", "-f", "s16le", "-ac", "1", "-ar", str(SR), "pipe:1"], input=mp3, capture_output=True, check=True).stdout
    return array.array("h", pcm)

def encode(samples, path):
    subprocess.run([FF, "-v", "error", "-y", "-f", "s16le", "-ac", "1", "-ar", str(SR), "-i", "pipe:0", "-c:a", "libmp3lame", "-b:a", "48k", path], input=samples.tobytes(), check=True)

def quietest(s, a, b, win=int(SR * 0.012)):
    """leiseste Stelle zwischen a und b (Abtastwerte): dort wird geschnitten"""
    a, b = max(0, a), min(len(s) - win, b)
    best, bi = None, a
    for i in range(a, max(a + 1, b), win // 2):
        e = sum(abs(v) for v in s[i:i + win])
        if best is None or e < best: best, bi = e, i
    return bi + win // 2, best / win

async def make(out, key, text, mid, sem, report):
    async with sem:
        if not mid:
            mp3, _ = await tts(text)
            encode(decode(mp3), os.path.join(out, key + ".mp3"))
            return
        nw = len(text.split())
        mp3, words = await tts(text + ", rechts vier.")
        s = decode(mp3)
        if len(words) < nw + 1: raise RuntimeError(f"Wortgrenzen fehlen: {key} {words}")
        end_w, next_w = words[nw - 1][2], words[nw][1]
        cut, lvl = quietest(s, int(end_w * SR), int(max(next_w, end_w + 0.05) * SR))
        seg = s[:cut]
        fade = min(len(seg), int(SR * 0.012))
        for i in range(fade): seg[len(seg) - 1 - i] = int(seg[len(seg) - 1 - i] * i / fade)
        encode(seg, os.path.join(out, key + "_m.mp3"))
        report.append((key, round(cut / SR, 2), round(next_w - end_w, 2), round(lvl)))

async def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "voice"
    os.makedirs(out, exist_ok=True)
    sem, report = asyncio.Semaphore(4), []
    jobs = [make(out, k, t + ".", False, sem, report) for k, t in BOTH.items()]
    jobs += [make(out, k, t, True, sem, report) for k, t in BOTH.items()]
    jobs += [make(out, k, t, False, sem, report) for k, t in END.items()]
    await asyncio.gather(*jobs)
    for r in sorted(report): print("%-8s Schnitt bei %.2fs, Pause %.2fs, Pegel am Schnitt %d" % r)
    print(len(jobs), "Dateien in", out)

asyncio.run(main())
