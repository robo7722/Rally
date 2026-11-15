# Motorgeräusche v2 (nach dem Vorbild von F1Racing, docs/SOUNDS.md dort) – siehe docs/Motorgeräusche.md.
#
# Warum v2: In v1 kam jede der fünf Drehzahlstufen aus einer anderen Zufallsaufnahme -> beim Hochdrehen wechselte der
# "Motor" mehrfach seinen Charakter, viele Autos klangen falsch. Jetzt:
#   1. je Auto wenige Basisaufnahmen (ElevenLabs Sound Effects): Leerlauf, ~1800 U/min, ~3000 U/min unter Last, ~6500 U/min Vollgas,
#      Gas weg (Schub: Blubbern/Knallen). Prompts wie bei F1Racing ("Onboard recording ... steady unchanging drone,
#      no revving, no acceleration, no gear change"), hohe Prompt-Treue. Je Basis TAKES Varianten, die gleichmäßigste gewinnt.
#   2. Drehzahl jeder Basis messen (Zündfrequenz = U/min x Zylinder / 120, Autokorrelation, Oktavfehler-Prüfung).
#   3. Drehzahlleiter LADDER: jede Stufe ist eine Tonhöhen-Verschiebung der nächstliegenden Basis mit Rubberband
#      (Formanten bleiben erhalten -> kein "Spielzeugmotor"). Dadurch klingt es über den ganzen Bereich wie ein Motor,
#      und das Spiel muss je Stufe nur noch ~0,85-1,17-fach nachstimmen.
#   4. Loops: Ausschnitt 3x hintereinander -> Rubberband -> mittleres Drittel, Naht 0,15 s gleich laut überblendet,
#      RMS 0,14, WAV mono 32 kHz 16 bit (MP3 hätte Stille am Anfang -> Knacken beim Loopen).
#
# Aufruf: python tools/make_engine2.py auto [auto ...]     Braucht ffmpeg (mit rubberband), numpy, scipy.
# Der API-Schlüssel kommt aus ELEVENLABS_API_KEY (in der Cloud-Umgebung ergänzt ihn der Proxy).
import json, os, subprocess, sys, wave
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_engine as v1   # generate(), firing_freq(), spec_frames()

ROOT = v1.ROOT; OUT = v1.OUT; RAW = os.path.join(ROOT, "tools", "_engine_raw", "v2")
SR_IN = 44100; SR = 32000; RMS = 0.14
TAKES = 3; WIN = 2.5; XF = 0.15
LADDER = [900, 1300, 1850, 2600, 3500, 4600, 5900, 7400]   # Spiel: Leerlauf 950, Begrenzer 7800
MAX_SHIFT = 10   # Halbtöne; mehr wird gemeldet

NO = ", no music, no voices, no other cars"
BASES = {   # Name: (Prompt mit {d}, Soll-U/min, Prompt-Treue, Länge s)
    "leer":  ("{d}, engine idling steadily at about 900 rpm, recorded close to the exhaust, lumpy idle, constant, no revving" + NO, 900, 0.7, 4),
    "tief":  ("Onboard recording of a {d}, engine running at a constant low 1800 rpm with light throttle, steady unchanging low rumble, no revving, no acceleration, no gear change" + NO, 1800, 0.8, 4),
    "last":  ("Onboard recording of a {d}, engine running at a constant 3000 rpm under load, steady unchanging drone, no revving, no acceleration, no gear change" + NO, 3000, 0.8, 4),
    "voll":  ("Onboard recording of a {d}, engine screaming at a constant 6500 rpm at full throttle, sustained steady unchanging high-pitched drone, no revving, no acceleration, no gear change" + NO, 6500, 0.85, 4),
    "schub": ("{d} on overrun, throttle closed at 5000 rpm while braking, exhaust burble, crackles and pops, steady, no acceleration, no gear change" + NO, 5000, 0.75, 3),
}
# Motor je Auto (Klangcharakter ausdrücklich beschrieben, nicht nur der Modellname); cyl für die Zündfrequenz
CARS = {
    "mini":    (4, "classic 1960s Mini Cooper S rally car with a tiny 1.3 litre BMC A-series four-cylinder engine, high-pitched buzzy raspy small four-cylinder, twin SU carburettors, small sporty exhaust"),
    "fiat":    (4, "1970s Fiat 131 Abarth rally car with a 2.0 litre naturally aspirated twin-cam 16-valve four-cylinder engine, hard raspy induction roar, open straight-through exhaust, no turbo"),
    "stratos": (6, "1970s Lancia Stratos HF rally car with the Ferrari Dino 2.4 litre naturally aspirated V6 engine, high-pitched exotic Italian V6 howl, triple Weber carburettors, no turbo"),
    "r5":      (4, "1980s Renault 5 Turbo rally car with a 1.4 litre turbocharged four-cylinder mid-engine, raspy gruff four-cylinder with loud turbo whistle and wastegate chatter"),
    "bmw":     (4, "1980s BMW M3 E30 Group A rally car with the S14 2.3 litre naturally aspirated four-cylinder engine, individual throttle bodies, hard metallic high-revving rasp, no turbo"),
    "escort":  (4, "1990s Ford Escort RS Cosworth Group A rally car with a 2.0 litre turbocharged four-cylinder engine, deep gruff turbo four-cylinder with big turbo whoosh and anti-lag pops"),
    "celica":  (4, "Toyota Celica GT-Four Group A rally car with a 2.0 litre turbocharged four-cylinder engine, gruff turbo four-cylinder with turbo whistle"),
    "delta":   (4, "Lancia Delta HF Integrale Group A rally car with a 2.0 litre 16-valve turbocharged four-cylinder engine, gruff raspy turbo four-cylinder with wastegate flutter"),
    "subaru":  (4, "Subaru Impreza WRC rally car with a 2.0 litre turbocharged flat-four boxer engine, deep uneven off-beat boxer burble, anti-lag bangs"),
    "lancer":  (4, "Mitsubishi Lancer Evolution WRC rally car with the 4G63 2.0 litre turbocharged four-cylinder engine, harsh raspy turbo four-cylinder, anti-lag crackles"),
}

def load(path, af=None, sr=SR_IN):
    cmd = ["ffmpeg", "-v", "error", "-i", path] + (["-af", af] if af else []) + ["-ac", "1", "-ar", str(sr), "-f", "f32le", "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32).astype(np.float64)

def save_wav(path, x, sr=SR):
    pcm = np.clip(np.round(x * 32767), -32768, 32767).astype("<i2")
    with wave.open(path, "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(pcm.tobytes())

def measure(x, cyl, rpm_nom):
    """Drehzahl über die Zündfrequenz (Autokorrelation). Gesucht wird nur 0,7-1,45 x Soll: Mit den F1-Prompts liegen die
    Aufnahmen nah an der verlangten Drehzahl, ein weiter Suchbereich rastet dagegen an Nebengeräuschen ein
    (z. B. Getriebeheulen beim Mini, konstanter Ton bei 214 Hz) oder springt um Oktaven."""
    from scipy.signal import butter, sosfiltfilt
    f_exp = rpm_nom * cyl / 120
    y = sosfiltfilt(butter(4, [15, min(4000, f_exp * 8)], btype="band", fs=SR_IN, output="sos"), x); y -= y.mean()
    n = len(y); F = np.fft.rfft(y, 2 * n); ac = np.fft.irfft(F * np.conj(F))[:n]; ac /= ac[0] + 1e-12
    lo, hi = int(SR_IN / (f_exp * 1.45)), min(int(SR_IN / (f_exp * 0.7)), n // 3)
    i = lo + int(np.argmax(ac[lo:hi]))
    if 0 < i < n - 1:
        a, b, c = ac[i - 1], ac[i], ac[i + 1]; d = 0.5 * (a - c) / (a - 2 * b + c + 1e-12)
        if abs(d) < 1: i = i + d   # Verfeinerung nur, wenn sie im Nachbarbereich bleibt
    return SR_IN / i * 120 / cyl, float(ac[int(round(i))])

def steady(x, win):
    """gleichmäßigster Abschnitt (Klangspektrum + Lautstärke) -> (Start, Wert)"""
    S, E, hop = v1.spec_frames(x); nw = int(win * SR_IN / hop); best = (1e9, 0)
    for s0 in range(2, max(3, len(S) - nw), 2):   # erste ~0,1 s auslassen (Einschwingen)
        Sw = S[s0:s0 + nw]; sc = float(np.mean(np.abs(Sw - Sw.mean(0)))) + float(np.std(E[s0:s0 + nw])) * 0.08
        if sc < best[0]: best = (sc, s0 * hop)
    return best[1], best[0]

def analyse(x, cyl, rpm_nom, win):
    start, st = steady(x, win); seg = x[start:start + int(win * SR_IN)]
    rpm, conf = measure(seg, cyl, rpm_nom)
    part = [measure(seg[i:i + SR_IN // 2], cyl, rpm)[0] for i in range(0, len(seg) - SR_IN // 2, SR_IN // 4)]
    pv = float(np.std(np.log(part)))
    return dict(seg=seg, rpm=rpm, conf=conf, pv=pv, steady=st, score=st + pv * 6 + (1 - conf) * 0.4)

def shift(x, st):
    """Tonhöhe um st Halbtöne, Formanten bleiben (Rubberband)"""
    tmp = os.path.join(RAW, "_tmp.wav"); save_wav(tmp, x / max(1.0, np.abs(x).max()), SR_IN)
    try: return load(tmp, "rubberband=pitch=%.6f:formant=preserved:pitchq=quality" % 2 ** (st / 12), SR_IN)
    finally: os.remove(tmp)

def make_loop(x, st):
    """Ausschnitt -> (verschobener) nahtloser Loop in SR"""
    n = len(x)
    y = shift(np.concatenate([x, x, x]), st) if abs(st) > 0.01 else np.concatenate([x, x, x])
    y = load_resample(y)
    n = int(round(n * SR / SR_IN)); xf = int(XF * SR); t = np.linspace(0, np.pi / 2, xf)
    out = y[n:2 * n].copy(); out[:xf] = y[n:n + xf] * np.sin(t) + y[2 * n:2 * n + xf] * np.cos(t)
    return out * RMS / (np.sqrt(np.mean(out ** 2)) + 1e-9)

def load_resample(y):
    tmp = os.path.join(RAW, "_rs.wav"); save_wav(tmp, y / max(1.0, np.abs(y).max()), SR_IN)
    try: return load(tmp, None, SR)
    finally: os.remove(tmp)

def main():
    os.makedirs(RAW, exist_ok=True)
    man_path = os.path.join(OUT, "engine.json"); man = json.load(open(man_path))
    for cid in sys.argv[1:]:
        cyl, desc = CARS[cid]; base = {}
        for bn, (pt, rpm_nom, infl, dur) in BASES.items():
            best = None
            for k in range(TAKES if bn != "schub" else 2):
                raw = os.path.join(RAW, "%s_%s_%d.mp3" % (cid, bn, k))
                v1.DUR = dur; generate(pt.format(d=desc), raw, dur, infl)
                x = load(raw); a = analyse(x, cyl, rpm_nom, min(WIN, len(x) / SR_IN - 0.4))
                print("  %-7s %-5s Take %d: %5.0f U/min (soll %d, Sicherheit %.2f), Tonhöhe ±%.3f, gleichmäßig %.3f, Wertung %.2f"
                      % (cid, bn, k, a["rpm"], rpm_nom, a["conf"], a["pv"], a["steady"], a["score"]), flush=True)
                # Nähe zur Soll-Drehzahl zählt mit; beim Leerlauf ist leichtes Schwanken normal (Tonhöhe weniger streng)
                a["score"] += 1.5 * abs(np.log(a["rpm"] / rpm_nom)) - (a["pv"] * 4 if bn == "leer" else 0)
                if best is None or a["score"] < best[1]["score"]: best = (k, a)
            base[bn] = best
        steps = []
        for i, T in enumerate(LADDER):
            # Leerlauf-Aufnahme nur für die untersten Stufen, sonst die Last-Aufnahme mit der kleinsten Verschiebung
            cands = ["leer"] if T <= 1000 else ["leer", "tief"] if T <= 1400 else ["tief", "last", "voll"]
            bn = min(cands, key=lambda b: abs(np.log(T / base[b][1]["rpm"])))
            k, a = base[bn]; st = 12 * np.log2(T / a["rpm"])
            if abs(st) > MAX_SHIFT: print("  ! %s %d U/min: %+.1f Halbtöne aus %s" % (cid, T, st, bn))
            fn = "%s_%d.wav" % (cid, i); save_wav(os.path.join(OUT, fn), make_loop(a["seg"], st))
            steps.append({"f": fn, "ref": T, "src": "%s_%d %+.1f HT" % (bn, k, st)})
        k, a = base["schub"]
        fn = "%s_schub.wav" % cid; save_wav(os.path.join(OUT, fn), make_loop(a["seg"], 0))
        man["cars"][cid] = {"cyl": cyl, "v": 2, "steps": steps, "schub": {"f": fn, "ref": round(a["rpm"]), "src": "schub_%d" % k},
                            "base": {b: round(base[b][1]["rpm"]) for b in base}}
        json.dump(man, open(man_path, "w"), indent=1)
        for f in os.listdir(OUT):   # alte v1-Dateien dieses Autos entfernen
            if f.startswith(cid + "_") and f.endswith(".mp3"): os.remove(os.path.join(OUT, f))
        print("%s fertig: Basis %s | %s" % (cid, man["cars"][cid]["base"], " · ".join(s["src"] for s in steps)), flush=True)

def generate(prompt, path, dur, infl):
    if os.path.exists(path): return
    import urllib.request, urllib.error, time
    body = {"text": prompt, "duration_seconds": dur, "loop": True, "prompt_influence": infl, "model_id": "eleven_text_to_sound_v2"}
    req = urllib.request.Request("https://api.elevenlabs.io/v1/sound-generation?output_format=mp3_44100_192", data=json.dumps(body).encode(),
                                 headers={"xi-api-key": v1.api_key(), "Content-Type": "application/json", "User-Agent": "engine-tool"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=120) as r: data = r.read()
            break
        except (urllib.error.HTTPError, urllib.error.URLError) as e:
            code = getattr(e, "code", 0)
            if code in (0, 429, 500, 502, 503) and attempt < 4: time.sleep(3 + attempt * 5); continue
            sys.exit("Fehler %s" % code)
    with open(path, "wb") as f: f.write(data)

if __name__ == "__main__":
    main()
