# Motorgeräusche v3: echte Aufnahmen statt KI (siehe docs/Motorgeräusche.md, Abschnitt v14.18).
#
# Quellen: frei lizenzierte Aufnahmen von Wikimedia Commons (CC BY 3.0, Urheber in SOURCES und engine/QUELLEN.md).
# Die Motoren sind zu Gruppen zusammengefasst (weniger, dafür echte Klänge); welches Auto welche Gruppe nutzt, steht in GROUPS.
#
# Ablauf je Gruppe:
#   1. Aufnahme laden (wird bei Bedarf von upload.wikimedia.org geholt, Ablage tools/_engine_raw/real/, nicht im Repo)
#   2. Drehzahlverlauf messen: Zündfrequenz per Autokorrelation alle 50 ms (Vierzylinder: U/min = Hz x 30)
#   3. gleichmäßige Abschnitte suchen: Tonhöhe stabil (±3 %), klare Periode, laut genug, mind. 0,35 s
#   4. Drehzahlleiter LADDER: je Stufe der Abschnitt mit der kleinsten Tonhöhen-Verschiebung (Güte und Länge zählen mit),
#      Abschnitt -> 2-s-Loop aus zufälligen Körnern im Zündtakt (texture) -> 3x hintereinander -> Rubberband (Formanten bleiben)
#      -> mittleres Drittel
#   5. RMS 0,14, WAV mono 32 kHz -> engine/<gruppe>_<i>.wav, Eintrag in engine/engine.json ("groups", Autos mit "g")
#
# Aufruf: python tools/make_engine_real.py        Braucht ffmpeg (mit rubberband), numpy, scipy.
import hashlib, json, os, subprocess, sys, urllib.parse, wave
import numpy as np
from scipy.signal import butter, sosfiltfilt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "engine"); RAW = os.path.join(ROOT, "tools", "_engine_raw", "real")
SR_IN = 22050; SR = 32000; RMS = 0.14
LADDER = [900, 1300, 1850, 2600, 3500, 4600, 5900, 7400]

SOURCES = {   # Gruppe: (Commons-Datei, Zylinder, Urheber, Beschreibung)
    "turbo4": ("Mitsubishi_Lancer_Evolution_VI_-_engine_and_exhaust_sound_(YouTube_p2UANOqploM).opus", 4, "prone (YouTube), via Wikimedia Commons",
               "Turbo-Vierzylinder (Mitsubishi Lancer Evolution VI, 4G63)"),
    "sauger4": ("Morris_Mini_-_engine_and_exhaust_sound_(YouTube_K-j53v8lwzM).opus", 4, "Luciano's Classics (YouTube), via Wikimedia Commons",
                "Sauger-Vierzylinder (1969 Morris Mini Cooper 1000)"),
}
GROUPS = {
    # Fiat 131 und BMW M3 (drehfreudige 16V-Sauger bis >7000 U/min): die Mini-Aufnahme reicht nur bis ~3300 U/min, darüber
    # wäre bis +14 Halbtöne verschoben (Spektrum-Korrelation zum Original nur 0,64) -> echte hohe Drehzahlen des Lancer passen besser
    "turbo4": ["r5", "p205", "rs200", "s4", "delta", "escort", "celica", "lancer", "subaru", "fiat", "bmw"],
    "sauger4": ["mini", "fulvia", "alpine"],
}
LICENSE = "CC BY 3.0 (https://creativecommons.org/licenses/by/3.0)"

def fetch(name):
    os.makedirs(RAW, exist_ok=True); path = os.path.join(RAW, name)
    if os.path.exists(path) and os.path.getsize(path) > 100000: return path
    h = hashlib.md5(name.encode()).hexdigest()
    url = "https://upload.wikimedia.org/wikipedia/commons/%s/%s/%s" % (h[0], h[:2], urllib.parse.quote(name))
    subprocess.run(["curl", "-sS", "-m", "90", "-A", "RallyGameEngineResearch/1.0 (educational)", "-o", path, url], check=True)
    if os.path.getsize(path) < 100000: sys.exit("Download gedrosselt (Wikimedia 429), später erneut versuchen: " + name)
    return path

def load(path, sr=SR_IN, af=None):
    cmd = ["ffmpeg", "-v", "error", "-i", path] + (["-af", af] if af else []) + ["-ac", "1", "-ar", str(sr), "-f", "f32le", "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32).astype(np.float64)

def save_wav(path, x, sr=SR):
    pcm = np.clip(np.round(x * 32767), -32768, 32767).astype("<i2")
    with wave.open(path, "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(pcm.tobytes())

def track(x, fmin=18, fmax=320, win=0.25, hop=0.05):
    """(Zeit, Hz, Güte der Periode, dB) je Fenster"""
    y = sosfiltfilt(butter(4, [15, 1200], btype="band", fs=SR_IN, output="sos"), x)
    W, H = int(win * SR_IN), int(hop * SR_IN); out = []
    for s in range(0, len(y) - W, H):
        seg = y[s:s + W] - y[s:s + W].mean(); r = np.sqrt(np.mean(seg ** 2))
        F = np.fft.rfft(seg, 2 * W); ac = np.fft.irfft(F * np.conj(F))[:W]; ac /= ac[0] + 1e-12
        lo, hi = int(SR_IN / fmax), int(SR_IN / fmin); i = lo + int(np.argmax(ac[lo:hi]))
        out.append((s / SR_IN, SR_IN / i, ac[i], 20 * np.log10(r + 1e-9)))
    return np.array(out)

def segments(t, minlen=0.35, tol=0.03, cmin=0.5):
    """zusammenhängende Abschnitte mit stabiler Tonhöhe -> (Start s, Ende s, Hz, Güte, dB)"""
    hop = t[1, 0] - t[0, 0]; dbmin = np.max(t[:, 3]) - 22; out = []; i = 0; n = len(t)
    while i < n:
        j = i
        while j + 1 < n and abs(np.log(t[j + 1, 1] / t[i, 1])) < tol and t[j + 1, 2] > cmin and t[j + 1, 3] > dbmin: j += 1
        if t[i, 2] > cmin and t[i, 3] > dbmin and (j - i + 1) * hop >= minlen:
            out.append((t[i, 0], t[j, 0] + 0.25, float(np.median(t[i:j + 1, 1])), float(np.mean(t[i:j + 1, 2])), float(np.mean(t[i:j + 1, 3]))))
        i = j + 1
    return out

def shift(x, st, sr):
    if abs(st) < 0.01: return x
    tmp = os.path.join(RAW, "_tmp.wav"); save_wav(tmp, x / max(1.0, np.abs(x).max()), sr)
    try: return load(tmp, sr, "rubberband=pitch=%.6f:formant=preserved:pitchq=quality" % 2 ** (st / 12))
    finally: os.remove(tmp)

def texture(x, f, sr, dur=2.0, grain=0.15, seed=1):
    """Kurzen gleichmäßigen Abschnitt zu einem langen nahtlosen Loop ohne hörbares Wiederholungsmuster verlängern:
    Körner (Hann-Fenster, 50 % Überlappung) an zufälligen Stellen des Abschnitts, aber immer um ganze Zündperioden
    versetzt und im Ausgang im Zündtakt platziert -> phasengleich (kein Kammfilter), kreisförmig -> nahtlos."""
    rng = np.random.default_rng(seed); P = sr / f
    hop = max(1, round(grain / 2 * sr / P)) * P; L = int(round(2 * hop))
    nh = max(4, int(round(dur * sr / hop))); N = int(round(nh * hop))
    w = np.hanning(L); out = np.zeros(N); maxm = int((len(x) - L - 1) / P)
    if maxm < 1: return x
    for j in range(nh):
        src = int(round(rng.integers(0, maxm + 1) * P)); pos = int(round(j * hop))
        g = x[src:src + L] * w; idx = (pos + np.arange(L)) % N; np.add.at(out, idx, g)
    return out

def make_loop(seg, st, f):
    """Abschnitt (SR_IN, Zündfrequenz f) -> langer, nahtloser, verschobener Loop (SR)"""
    tmp = os.path.join(RAW, "_rs.wav"); save_wav(tmp, seg / max(1.0, np.abs(seg).max()), SR_IN)
    x = load(tmp, SR); os.remove(tmp)
    lp = texture(x, f, SR); n = len(lp)
    y = shift(np.concatenate([lp, lp, lp]), st, SR)
    out = y[n:2 * n].copy(); k = min(int(0.03 * SR), n // 8); t2 = np.linspace(0, np.pi / 2, k)
    out[:k] = y[n:n + k] * np.sin(t2) + y[2 * n:2 * n + k] * np.cos(t2)   # Restfehler der Verschiebung glätten
    return out * RMS / (np.sqrt(np.mean(out ** 2)) + 1e-9)

def main():
    man_path = os.path.join(OUT, "engine.json"); man = json.load(open(man_path)); man.setdefault("groups", {})
    for g, (name, cyl, author, desc) in SOURCES.items():
        x = load(fetch(name)); segs = segments(track(x))
        print("%s: %d gleichmäßige Abschnitte, %s" % (g, len(segs), ", ".join("%.0f" % (s[2] * 120 / cyl) for s in sorted(segs, key=lambda s: s[2]))))
        steps = []
        for i, T in enumerate(LADDER):
            def cost(s):
                st = 12 * np.log2(T / (s[2] * 120 / cyl))
                return abs(st) + (1 - s[3]) * 4 - min(s[1] - s[0], 1.2) * 1.5
            s = min(segs, key=cost); rpm = s[2] * 120 / cyl; st = 12 * np.log2(T / rpm)
            a, b = int((s[0] + 0.05) * SR_IN), int((s[1] - 0.05) * SR_IN)
            fn = "%s_%d.wav" % (g, i); save_wav(os.path.join(OUT, fn), make_loop(x[a:b], st, s[2]))
            steps.append({"f": fn, "ref": T, "src": "%.2f-%.2f s, %.0f U/min, %+.1f HT" % (s[0], s[1], rpm, st)})
            print("  %5d U/min <- %s" % (T, steps[-1]["src"]))
        man["groups"][g] = {"cyl": cyl, "v": 2, "steps": steps, "desc": desc,
                            "credit": {"file": "https://commons.wikimedia.org/wiki/File:" + name, "author": author, "license": LICENSE}}
        for cid in GROUPS[g]:
            man["cars"][cid] = {"g": g}
            for f in os.listdir(OUT):   # bisherige Einzel-Dateien dieses Autos entfernen
                if f.startswith(cid + "_"): os.remove(os.path.join(OUT, f))
    json.dump(man, open(man_path, "w"), indent=1, ensure_ascii=False)

if __name__ == "__main__":
    main()
