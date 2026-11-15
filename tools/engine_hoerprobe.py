# Hörprobe eines Motors ohne das Spiel – bildet engUpd/engGran aus index.html nach (wie F1Racing tools/sounds/hoerprobe_mx5.py).
# Fester Ablauf (Zeittabelle, Sekunden):
#   0,0–2,5 Leerlauf · 2,5–5,0 und 5,6–8,4 zwei Gasstöße im Stand · 9,4–12,2 Anfahren Vollgas bis 7.000 · 12,2–12,4 Schalten
#   12,4–14,4 Vollgas 5.000 -> 7.300 · 14,4–17,0 Gas weg bis Leerlauf · 17,0–18,5 Leerlauf
# Gibt den Pegel je 0,1 s aus (Sprünge/Löcher an Übergängen).
# Aufruf: python tools/engine_hoerprobe.py <auto-id oder gruppe> [ausgabe.mp3]     (Standard: engine_demo/<name>.mp3)
import json, os, subprocess, sys, wave
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); SR = 32000
M = json.load(open(os.path.join(ROOT, "engine", "engine.json")))

def cfg(name):
    cd = M["groups"].get(name) or M["cars"][name]
    if "g" in cd: cd = M["groups"][cd["g"]]
    if cd.get("v") == 3: return cd
    zf = cd.get("cyl", 4) / 2
    return {"cyl": cd.get("cyl", 4), "vol": 0.6, "scale": 1, "xf": [0, 1], "loops": [[s["f"], s["ref"] * zf / 60] for s in cd["steps"]], "blips": [],
            "gran": None, "schub": [cd["schub"]["f"], cd["schub"]["ref"] * zf / 60, 0.35] if cd.get("schub") else None}

def L(f):
    w = wave.open(os.path.join(ROOT, "engine", f)); x = np.frombuffer(w.readframes(w.getnframes()), "<i2") / 32768.
    if w.getframerate() != SR: x = np.interp(np.arange(int(len(x) * SR / w.getframerate())) * w.getframerate() / SR, np.arange(len(x)), x)
    return x

def ablauf(blen=(2.5, 2.8)):
    seq = []; blips = []   # je 10 ms: (Drehzahl, Gas, Gasstoß aktiv)
    def ramp(a, b, sec, thr): n = int(sec * 100); seq.extend((a + (b - a) * k / n, thr, 0) for k in range(n))
    def blip(dur): blips.append(len(seq) / 100); seq.extend((950, 0.8, 1) for _ in range(int((dur - 0.3) * 100))); seq.extend((950, 0, 0) for _ in range(30))
    ramp(950, 950, 2.5, 0); blip(blen[0]); ramp(950, 950, 3.1 - blen[0], 0); blip(blen[1]); ramp(950, 950, 3.8 - blen[1], 0)
    ramp(950, 7000, 2.8, 1); ramp(7000, 5000, 0.2, 0.2); ramp(5000, 7300, 2.0, 1); ramp(7300, 950, 2.6, 0); ramp(950, 950, 1.5, 0)
    rpm = np.array([s[0] for s in seq]); thr = np.array([s[1] for s in seq]); bl = np.array([s[2] for s in seq], float)
    for i in range(1, len(rpm)): rpm[i] = rpm[i - 1] + (rpm[i] - rpm[i - 1]) * 0.35
    return rpm, thr, bl, blips

def render(name):
    D = cfg(name)
    bf = [L(f) for f in D.get("blips", [])]; blen = tuple(len(bf[k % len(bf)]) / SR for k in range(2)) if bf else (2.5, 2.8)
    rpmG, thr, bl, blips = ablauf(blen); N = len(rpmG) * SR // 100; tt = np.arange(len(rpmG)) / 100; t = np.arange(N) / SR
    rpm = np.interp(t, tt, rpmG) * D.get("scale", 1); T = np.interp(t, tt, thr); fq = rpm / 60 * D["cyl"] / 2
    B = np.interp(t, tt, np.convolve(bl, np.ones(16) / 16, "same")) if D.get("blips") else np.zeros(N)
    gw = np.zeros(N)
    if D.get("gran"):
        G = D["gran"]; gw = np.clip((rpm - G["von"]) / (G["bis"] - G["von"]), 0, 1)
        if G.get("aus"): gw *= 1 - np.clip((rpm - G["aus"][0]) / (G["aus"][1] - G["aus"][0]), 0, 1)
        gw = gw * gw * (3 - 2 * gw)
    loops = D["loops"]; bases = np.array([l[1] for l in loops]); eng = np.zeros(N)
    if len(loops) == 1: W = [np.ones(N)]
    else:
        i = np.clip(np.searchsorted(bases, fq) - 1, 0, len(loops) - 2); u = np.clip(np.log(fq / bases[i]) / np.log(bases[i + 1] / bases[i]), 0, 1)
        xf = [l[2] if len(l) > 2 else D.get("xf", [0.38, 0.24]) for l in loops]; xs = np.array([a[0] for a in xf])[i]; xw = np.array([a[1] for a in xf])[i]
        x = np.clip((u - xs) / xw, 0, 1); x = x * x * (3 - 2 * x)
        W = [np.where(i == k, np.cos(x * np.pi / 2), 0) + np.where(i + 1 == k, np.sin(x * np.pi / 2), 0) for k in range(len(loops))]
    for k, (f, base, *_) in enumerate(loops):
        b = L(f); pos = (np.cumsum(np.clip(fq / base, 0.4, 2.2)) + np.random.rand() * len(b)) % len(b); j = pos.astype(int); fr = pos - j
        eng += W[k] * (b[j] * (1 - fr) + b[(j + 1) % len(b)] * fr)
    eng *= np.cos(gw * np.pi / 2)
    if D.get("gran"):   # Granular wie engGran
        G = D["gran"]; gl = int(0.1 * SR); win = np.sin(np.pi * np.arange(gl) / (gl - 1)) ** 2 / 1.5; gr = np.zeros(N + 2 * gl)
        for qi, q in enumerate(G["quellen"]):
            dz = L(q["file"]); TT = np.array([a[0] for a in q["tab"]]); RR = np.array([a[1] for a in q["tab"]], float)
            Sx, ST, Sr, Tn = 0.0, 0.0, 1.0, 0.0
            while Tn < N / SR:
                k0 = min(int(Tn * SR), N - 1); rp = rpm[k0]; r = np.clip(rp, RR[0], RR[-1]); k = min(max(np.searchsorted(RR, r) - 1, 0), len(RR) - 2)
                p = TT[k] + np.clip((r - RR[k]) / max(1, RR[k + 1] - RR[k]), 0, 1) * (TT[k + 1] - TT[k]); rt = np.clip(rp / r, 0.55, 1.04); per = 120 / (D["cyl"] * r)
                cont = Sx + (Tn - ST) * Sr; s0 = cont + round((p - cont) / per) * per
                if not abs(s0 - p) < 0.06 or s0 < 0: s0 = p
                s0 = min(max(s0, 0), len(dz) / SR - 0.1 * rt - 0.005)
                x2 = 0.0
                if len(G["quellen"]) > 1: x2 = np.clip((rp - (G["wechsel"] - G["xf"])) / (2 * G["xf"]), 0, 1); x2 = x2 * x2 * (3 - 2 * x2)
                w = np.sin(gw[k0] * np.pi / 2) * (np.cos(x2 * np.pi / 2) if qi == 0 else np.sin(x2 * np.pi / 2))
                if w > 0.002:
                    src = s0 * SR + np.arange(gl) * rt; i0 = src.astype(int); fr = src - i0; g = dz[i0] * (1 - fr) + dz[np.minimum(i0 + 1, len(dz) - 1)] * fr
                    gr[k0:k0 + gl] += g * win * w
                Sx, ST, Sr = s0, Tn, rt; Tn += 0.1 / 3
        eng += gr[:N]
    # Tiefpass 1.500 + Gas·10.500 Hz (einfacher Einpol-Filter, blockweise)
    y = np.zeros(N); z = 0.0
    for s0 in range(0, N, 256):
        a = 1 - np.exp(-2 * np.pi * (1500 + T[s0] * 10500) / SR)
        for q in range(s0, min(N, s0 + 256)): z += a * (eng[q] - z); y[q] = z
    sAmt = np.clip((0.45 - T) / 0.35, 0, 1) * np.clip((rpm - 3200) / 2000, 0, 1) if D.get("schub") else np.zeros(N)
    V = (0.5 + 0.5 * T) * (1 - 0.35 * sAmt) * (1 - B); Vs = V.copy(); au, ad = 1 - np.exp(-1 / (0.14 * SR)), 1 - np.exp(-1 / (0.04 * SR))
    for k in range(1, N): Vs[k] = Vs[k - 1] + (V[k] - Vs[k - 1]) * (au if V[k] > Vs[k - 1] and D.get("gran") else ad)
    out = y * Vs * D["vol"] / 0.6
    if D.get("schub"):
        b = L(D["schub"][0]); pos = (np.cumsum(np.clip(fq / D["schub"][1], 0.5, 1.8)) + np.random.rand() * len(b)) % len(b); j = pos.astype(int)
        out += b[j] * sAmt * D["schub"][2] * D["vol"] * 1.6
    for k, t0 in enumerate(blips):
        if not D.get("blips"): break
        b = L(D["blips"][k % len(D["blips"])]); s0 = int(t0 * SR); e = min(N, s0 + len(b)); out[s0:e] += b[:e - s0] * D["vol"] / 0.6
    return out / (np.abs(out).max() + 1e-9) * 0.7

if __name__ == "__main__":
    name = sys.argv[1]; dst = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "engine_demo", name + ".mp3")
    os.makedirs(os.path.dirname(dst), exist_ok=True); out = render(name)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "s16le", "-ar", str(SR), "-ac", "1", "-i", "-", "-b:a", "128k", dst], input=(out * 32767).astype("<i2").tobytes(), check=True)
    h = int(0.1 * SR); e = [np.sqrt(np.mean(out[q:q + h] ** 2)) for q in range(0, len(out) - h, h)]
    print(dst); print("Pegel je 0,1 s:", " ".join("%.1f:%.2f" % (q / 10, v) for q, v in enumerate(e)))
    d = np.abs(np.diff(20 * np.log10(np.array(e) + 1e-4))); big = [(q / 10, d[q]) for q in range(len(d)) if d[q] > 6]
    print("Sprünge > 6 dB:", ", ".join("%.1f s (%.0f dB)" % b for b in big) or "keine")
