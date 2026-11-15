# Hörprobe der Motorgeräusche: bildet die Wiedergabe im Spiel nach (zwei benachbarte Drehzahlstufen, Überblendung mit
# gleicher Leistung, Tonhöhe = Drehzahl / Aufnahme-Drehzahl) und rendert je Auto einen Ablauf
# Leerlauf -> Gas im Stand -> Hochschalten durch die Gänge -> Gas weg -> Leerlauf.
# Aufruf: python tools/engine_demo.py [Zielordner] [Auto ...]      (Standard: engine_demo/)
import json, os, subprocess, sys
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SR = 44100

def decode(path):
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "pipe:1"], capture_output=True, check=True).stdout
    return np.frombuffer(pcm, np.float32).astype(np.float64)

def rpm_curve():
    """(Drehzahl, Gas) je Abtastwert"""
    seg = []
    def hold(sec, rpm, thr): seg.append((np.full(int(sec * SR), rpm), np.full(int(sec * SR), thr)))
    def ramp(sec, r0, r1, thr): seg.append((np.geomspace(r0, r1, int(sec * SR)), np.full(int(sec * SR), thr)))
    hold(2.0, 950, 0)
    ramp(0.6, 950, 5200, 1); ramp(0.8, 5200, 950, 0); hold(0.6, 950, 0)          # Gasstoß im Stand
    for r0, dur in ((1100, 2.2), (4900, 1.8), (5500, 2.0), (5800, 2.3)):          # Gänge 1-4
        ramp(dur, r0, 7300, 1); hold(0.12, 7300 * 0.7, 0.2)
    hold(1.2, 7300, 1)
    ramp(2.5, 7300, 2500, 0); ramp(1.5, 2500, 950, 0); hold(1.5, 950, 0)
    r = np.concatenate([s[0] for s in seg]); t = np.concatenate([s[1] for s in seg])
    k = int(0.03 * SR); kern = np.ones(k) / k                                    # wie setTargetAtTime: weich
    return np.convolve(r, kern, "same"), np.convolve(t, kern, "same")

def render(cid, M):
    cd = M["cars"][cid]; pad = int(M["pad"] * SR)
    if "g" in cd: cd = M["groups"][cd["g"]]   # zusammengefasste Motoren
    loops = []
    for st in cd["steps"]:
        if cd.get("v") == 2: loops.append((decode(os.path.join(ROOT, "engine", st["f"])), st["ref"])); continue
        x = decode(os.path.join(ROOT, "engine", "%s_%s.mp3" % (cid, st["n"])))
        L = int(round(st["len"] * SR)); loops.append((x[pad:pad + L], st["ref"]))
    rpm, thr = rpm_curve(); n = len(rpm); out = np.zeros(n)
    refs = np.array([r for _, r in loops])
    i = np.clip(np.searchsorted(refs, rpm) - 1, 0, len(refs) - 2)
    x = np.clip(np.log(rpm / refs[i]) / np.log(refs[i + 1] / refs[i]), 0, 1)
    for j, (lp, ref) in enumerate(loops):
        w = np.where(i == j, np.cos(x * np.pi / 2), 0) + np.where(i + 1 == j, np.sin(x * np.pi / 2), 0)
        rate = np.clip(rpm / ref, 0.45, 2.2)
        ph = np.cumsum(rate) + np.random.rand() * len(lp)
        k0 = np.floor(ph).astype(np.int64); fr = ph - k0
        y = lp[k0 % len(lp)] * (1 - fr) + lp[(k0 + 1) % len(lp)] * fr
        out += w * y
    lv = (0.5 + 0.5 * np.clip((rpm - 900) / 6500, 0, 1)) * (0.62 + 0.38 * thr)
    sw = np.clip((0.45 - thr) / 0.35, 0, 1) * np.clip((rpm - 2500) / 1500, 0, 1) if cd.get("schub") else np.zeros(n)
    out *= lv * (1 - 0.35 * sw)
    sch = None
    if cd.get("schub"):   # Gas weg: Schub-Loop, am Tiefpass vorbei
        lp = decode(os.path.join(ROOT, "engine", cd["schub"]["f"])); rate = np.clip(rpm / cd["schub"]["ref"], 0.6, 1.6)
        ph = np.cumsum(rate) + np.random.rand() * len(lp); k0 = np.floor(ph).astype(np.int64); fr = ph - k0
        sch = (lp[k0 % len(lp)] * (1 - fr) + lp[(k0 + 1) % len(lp)] * fr) * sw * lv * 1.2
    # Schiebebetrieb dumpfer: einfacher Tiefpass, Grenzfrequenz folgt Gas und Drehzahl (blockweise)
    fc = 1400 + rpm * 0.5 + thr * 9000; y = np.zeros(n); z = 0.0
    a = 1 - np.exp(-2 * np.pi * fc / SR)
    for s0 in range(0, n, 512):
        aa = a[s0]
        for _ in range(1):
            seg = out[s0:s0 + 512]; o = np.empty_like(seg)
            for q in range(len(seg)): z += aa * (seg[q] - z); o[q] = z
            y[s0:s0 + 512] = o
    if sch is not None: y = y + sch
    return y / (np.max(np.abs(y)) + 1e-9) * 0.9

def main():
    args = sys.argv[1:]
    dst = os.path.join(ROOT, "engine_demo")
    if args and not args[0] in json.load(open(os.path.join(ROOT, "engine", "engine.json")))["cars"]: dst = args.pop(0)
    M = json.load(open(os.path.join(ROOT, "engine", "engine.json")))
    os.makedirs(dst, exist_ok=True)
    for cid in args or list(M["cars"]):
        y = render(cid, M)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ac", "1", "-ar", str(SR), "-i", "pipe:0", "-c:a", "libmp3lame", "-b:a", "128k",
                        os.path.join(dst, cid + ".mp3")], input=y.astype(np.float32).tobytes(), check=True)
        print(cid, "->", os.path.join(dst, cid + ".mp3"))

if __name__ == "__main__":
    main()
