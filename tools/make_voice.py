# Erzeugt die Beifahrer-Schnipsel in voice/ mit ElevenLabs (Stimme "Daniel", Modell eleven_multilingual_v2).
# Jeder Schnipsel wird in einem ganzen Satz gesprochen und an den Sprechpausen (Kommas) herausgeschnitten,
# damit Aussprache und Betonung zum Satzzusammenhang passen:
#   <key>_m.mp3 = Satzmitte (Stimme bleibt oben):  "<Wort>, rechts vier."   -> erster Teil
#   <key>.mp3   = Satzende (Stimme senkt sich):    "Achtung, <Wort>."       -> letzter Teil
# Braucht: pip install imageio-ffmpeg  und die Umgebungsvariable ELEVENLABS_API_KEY (wird nie ausgegeben).
# Aufruf: python tools/make_voice.py [Zielordner] [Schlüssel ...]     (Schlüssel z. B. "kuppe l3_m": nur diese neu erzeugen)
import array, base64, json, os, subprocess, sys, time, urllib.request, urllib.error
import imageio_ffmpeg

VOICE_ID = "onwK4e9ZLuTAKqWW03F9"   # Daniel
MODEL = "eleven_multilingual_v2"
SR = 44100
SEP = ', <break time="0.35s" /> '   # kurze Sprechpause an den Schnittstellen (die Stimme macht an Kommas sonst kaum eine)
FF = imageio_ffmpeg.get_ffmpeg_exe()
NUM = ["eins", "zwei", "drei", "vier", "fünf", "sechs"]
DIST = {50: "fünfzig", 100: "hundert", 150: "hundertfünfzig", 200: "zweihundert", 250: "zweihundertfünfzig", 300: "dreihundert", 350: "dreihundertfünfzig", 400: "vierhundert"}
# Wörter, die mitten im Satz und am Ende vorkommen
BOTH = {"hn": "Haarnadel", "lang": "lang", "zz": "zieht zu", "of": "öffnet", "ns": "nicht schneiden",
        "zs": "Zuschauer auf der Strecke", "leicht": "leicht", "mittel": "mittel", "eng": "eng", "neunzig": "neunzig",
        "sprung": "Sprung", "eis": "Eis"}
for i, n in enumerate(NUM, 1):
    BOTH[f"l{i}"] = f"Links {n}"; BOTH[f"r{i}"] = f"Rechts {n}"
    BOTH[f"il{i}"] = f"in Links {n}"; BOTH[f"ir{i}"] = f"in Rechts {n}"   # "in" gleich mitgesprochen: fließt natürlicher

# key -> (Satzteile, Index des gewünschten Teils, Satzzeichen am Ende)
JOBS = {}
for k, t in BOTH.items():
    pre = "Links zwei" if k[0] == "i" and k[1] in "lr" else "Achtung"
    JOBS[k + "_m"] = ([t, "rechts vier"], 0, ".")
    JOBS[k] = ([pre, t], 1, ".")
for d, w in DIST.items():
    JOBS[f"d{d}"] = (["Links drei", w], 1, ".")
JOBS["kuppe"] = (["Achtung", "Kuppe"], 1, ".")
# "Haarnadel" spricht die Stimme nur in dieser Schreibweise und mit einem Wort davor richtig aus (per Hörprobe ausgewählt)
JOBS["hn_m"] = (["Links eins", "Hahr-Nadel", "rechts vier"], 1, ".")
JOBS["hn"] = (["Links eins", "Hahr-Nadel"], 1, ".")
JOBS["lg"] = (["Links drei", "lange Gerade"], 1, ".")
JOBS["ach"] = (["Achtung", "links drei"], 0, ".")
JOBS["in"] = (["Links drei", "in", "Kuppe"], 1, ".")
JOBS["go"] = (["Los geht's"], 0, "!")
JOBS["ziel"] = (["Ziel! Gut gemacht"], 0, ".")
JOBS["ready"] = (["Beifahrer bereit"], 0, ".")

def api_key():
    k = os.environ.get("ELEVENLABS_API_KEY")
    if not k and os.name == "nt":
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as h: k = winreg.QueryValueEx(h, "ELEVENLABS_API_KEY")[0]
        except OSError: k = None
    if not k: sys.exit("ELEVENLABS_API_KEY ist nicht gesetzt.")
    return k.strip()

def tts(text):
    """-> (PCM-Abtastwerte, Zeichen, Startzeiten, Endzeiten)"""
    req = urllib.request.Request("https://api.elevenlabs.io/v1/text-to-speech/%s/with-timestamps?output_format=mp3_44100_128" % VOICE_ID,
                                 data=json.dumps({"text": text, "model_id": MODEL}).encode(),
                                 headers={"xi-api-key": api_key(), "Content-Type": "application/json", "User-Agent": "voice-tool"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=90) as r: js = json.loads(r.read())
            break
        except urllib.error.HTTPError as e:
            msg = e.read().decode("utf-8", "replace")[:300]
            if e.code in (429, 500, 502, 503) and attempt < 3: time.sleep(3 + attempt * 4); continue
            sys.exit("Fehler %d bei '%s': %s" % (e.code, text, msg))
    pcm = subprocess.run([FF, "-v", "error", "-i", "pipe:0", "-f", "s16le", "-ac", "1", "-ar", str(SR), "pipe:1"], input=base64.b64decode(js["audio_base64"]), capture_output=True, check=True).stdout
    al = js["alignment"]
    return array.array("h", pcm), al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"]

def encode(samples, path):
    subprocess.run([FF, "-v", "error", "-y", "-f", "s16le", "-ac", "1", "-ar", str(SR), "-i", "pipe:0", "-c:a", "libmp3lame", "-b:a", "64k", path], input=samples.tobytes(), check=True)

def quietest(s, a, b, win=int(SR * 0.012)):
    """leiseste Stelle zwischen a und b (Abtastwerte): dort wird geschnitten"""
    a, b = max(0, a), min(len(s) - win, b)
    best, bi = None, a
    for i in range(a, max(a + 1, b), win // 2):
        e = sum(abs(v) for v in s[i:i + win])
        if best is None or e < best: best, bi = e, i
    return bi + win // 2, best / win

def make(out, key):
    parts, idx, end = JOBS[key]
    text = SEP.join(parts) + end
    s, ch, t0, t1 = tts(text)
    if "".join(ch) != text: print("  Hinweis: Zeichenfolge weicht ab bei", key)
    # Zeichenpositionen der Teile im Text
    pos, o = [], 0
    for p in parts: pos.append((o, o + len(p))); o += len(p) + len(SEP)
    a, b, lvl = 0, len(s), 0
    if idx > 0:   # Schnitt in der Pause vor dem Teil
        a, l1 = quietest(s, int(t1[pos[idx - 1][1] - 1] * SR), int(t0[pos[idx][0]] * SR) + 1); lvl = max(lvl, l1)
    if idx < len(parts) - 1:   # Schnitt in der Pause nach dem Teil
        b, l2 = quietest(s, int(t1[pos[idx][1] - 1] * SR), int(t0[pos[idx + 1][0]] * SR) + 1); lvl = max(lvl, l2)
    seg = s[a:b]
    fade = min(len(seg) // 2, int(SR * 0.008))
    for i in range(fade):
        if idx > 0: seg[i] = int(seg[i] * i / fade)
        if idx < len(parts) - 1: seg[len(seg) - 1 - i] = int(seg[len(seg) - 1 - i] * i / fade)
    encode(seg, os.path.join(out, key + ".mp3"))
    print("%-10s %-40s %.2fs  Pegel am Schnitt %d" % (key, ", ".join(parts) + end, len(seg) / SR, lvl))
    return len(text)

def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "voice"
    only = sys.argv[2:]
    os.makedirs(out, exist_ok=True)
    n = sum(make(out, k) for k in JOBS if not only or k in only)
    print(len(only) or len(JOBS), "Dateien in", out, "-", n, "Zeichen verbraucht")

main()
