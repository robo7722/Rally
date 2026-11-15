# Motorgeräusche in Schichten nach der Anleitung aus F1Racing (docs/MOTORSOUND-ANLEITUNG.md dort, Vorlage Roadster v2.14).
# Siehe docs/Motorgeräusche.md, Abschnitt v14.21.
#
# Statt einer Drehzahl-Leiter aus vielen verschobenen Stücken wird jede Motorgruppe aus echten Aufnahmen in Schichten zusammengesetzt:
#   1 Leerlauf      – echter Leerlauf-Abschnitt, Tonhöhe geglättet, nahtloser Loop
#   2 Gasstöße      – echte Gasstöße im Stand (ganze Aufnahme; Pegel über dem Leerlauf zusammengedrückt)
#   3 Durchzug      – echte gleichmäßige Beschleunigung(en) ohne Schalten + Drehzahl-Tabelle -> Granular-Wiedergabe im Spiel
#   4 Stufen        – echte Abschnitte konstanter Drehzahl (Tonhöhe geglättet), höchstens ~±5 Halbtöne verschoben
#   5 Gas weg       – Schub-Loop (Verzögerung mit geschlossenem Gas)
# Schnittzeiten sind von Hand aus Drehzahl-/Pegel-Diagrammen gewählt (wie in F1Racing tools/sounds/mx5_echt.py).
# Lancer-Aufnahme = Onboard-Fahrt (nur 4.000-7.400 U/min, kein Leerlauf) -> Leerlauf/Gasstöße/unterer Durchzug vom Delta Integrale
# (ebenfalls Turbo-Vierzylinder dieser Gruppe; Kaltstart: erhöhter Leerlauf ~1.600 U/min, daher -6 HT).
#
# Aufruf: python tools/make_engine_schichten.py      Braucht ffmpeg (mit rubberband), numpy, scipy. Rohaufnahmen in tools/_engine_raw/real/
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_engine_real import fetch, load, save_wav, shift, texture, OUT, LICENSE

SR = 32000; RMS = 0.14
C = "(YouTube), via Wikimedia Commons"
REC = {   # Kurzname: (Commons-Datei, Urheber, Zylinder)
    "lancer": ("Mitsubishi_Lancer_Evolution_VI_-_engine_and_exhaust_sound_(YouTube_p2UANOqploM).opus", "prone " + C, 4),
    "delta": ("Lancia_Delta_Integrale_-_engine_and_exhaust_sound_(YouTube_0qq7MZ00ipI).opus", "Grzegorz Kalinecki " + C, 4),
    "mini": ("Morris_Mini_-_engine_and_exhaust_sound_(YouTube_K-j53v8lwzM).opus", "Luciano's Classics " + C, 4),
}
SCHICHTEN = {
    "turbo4": {
        "desc": "Turbo-Vierzylinder (Lancia Delta Integrale: Leerlauf, Gasstöße, unterer Durchzug · Mitsubishi Lancer Evo VI: Fahrt)",
        "cyl": 4, "vol": 0.6, "scale": 1.0,
        "leer": ("delta", 30.5, 3.0, -6, 1600),                 # Aufnahme, Start s, Länge s, Halbtöne, U/min laut Diagramm
        # Aufnahme, Start s, Länge s (inkl. Abfall bis Leerlauf). Der Gasstoß bei 7,95 s beginnt im leisen Kaltstart -> beim Angleichen
        # fast doppelt so laut wie der Rest (im Spiel-Code gemessen) -> nicht verwendet.
        "blips": [("delta", 12.05, 2.1)],
        "gran": [("delta", 8.15, 9.7), ("lancer", 11.95, 14.3)],  # Durchzüge (Start, Ende); Übergabe in der Mitte der Überlappung
        "stufen": [("lancer", 14.6, 0.6, 0, 6900)],              # konstante Drehzahl oben
        "schub": ("lancer", 56.55, 0.55, 5500),                   # Gas weg, ~6.000 -> 5.100 U/min
    },
    "sauger4": {
        "desc": "Sauger-Vierzylinder (1969 Morris Mini Cooper 1000: Leerlauf, Gasstöße, Durchzug)",
        "cyl": 4, "vol": 0.6, "scale": 0.74,                     # Mini dreht echt ~6.000: Spiel-Drehzahl 7.800 -> 5.770 U/min Klang
        "leer": ("mini", 19.85, 1.6, 0, 820),
        "blips": [("mini", 7.85, 1.8), ("mini", 11.55, 2.8), ("mini", 15.65, 3.3)],
        "gran": [("mini", 15.72, 16.86)],                          # 1.540 -> 5.750 U/min, Pegel gleichmäßig
        "stufen": [],
        "schub": None,
    },
}

def rec(name):
    f, _, cyl = REC[name]; return load(fetch(f), SR), cyl

def track(x, p0, hop=1024, win=4096):
    """Tonhöhe alle 32 ms (Autokorrelation, nur ±25 % um p0), geglättet – wie F1Racing glaetten.py"""
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); X[f > 4 * p0] = 0; X[f < 0.5 * p0] = 0; y = np.fft.irfft(X, len(x))
    t, p = [], []
    for s in range(0, max(1, len(y) - win), hop):
        seg = y[s:s + win]; a = np.correlate(seg, seg, "full")[len(seg) - 1:]; a /= a[0] + 1e-9
        L0, L1 = int(SR / (p0 * 1.25)), min(int(SR / (p0 * 0.8)), len(a) - 2); l = L0 + int(np.argmax(a[L0:L1]))
        if 0 < l - L0 < L1 - L0 - 1:
            y0, y1, y2 = a[l - 1], a[l], a[l + 1]; l = l + 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2 + 1e-12)
        t.append(s + win / 2); p.append(SR / l)
    p = np.array(p); ps = np.convolve(np.pad(p, 2, mode="edge"), np.ones(5) / 5, "valid")
    return np.array(t), ps

def flatten(x, p0):
    """Aufnahme mit veränderlichem Tempo abspielen, so dass die Tonhöhe konstant ist (kein Auf und Ab an der Loop-Naht)"""
    t, p = track(x, p0); ref = float(np.median(p))
    rate = np.interp(np.arange(len(x)), t, ref / p); pos = np.cumsum(rate); pos = pos[pos < len(x) - 1]
    i = pos.astype(int); fr = pos - i
    return x[i] * (1 - fr) + x[i + 1] * fr, ref

def pitch0(x, hint):
    """Zündfrequenz eines Abschnitts, gesucht nur ±35 % um die Drehzahl aus dem Diagramm (hint in Hz) – sonst Oktavfehler"""
    N = min(8192, len(x) // 2); r = []
    for s in range(0, len(x) - N, N // 2):
        w = x[s:s + N] - x[s:s + N].mean(); X = np.fft.rfft(w, 2 * N); f = np.fft.rfftfreq(2 * N, 1 / SR); X[(f < 15) | (f > 900)] = 0
        ac = np.fft.irfft(np.abs(X) ** 2)[:N]; ac /= ac[0]; L0, L1 = int(SR / (hint * 1.35)), int(SR / (hint * 0.74)); l = L0 + int(np.argmax(ac[L0:L1])); r.append(SR / l)
    return float(np.median(r))

def loopify(x, xf):
    n = len(x) - xf; t = np.linspace(0, 1, xf); y = x[:n].copy()
    y[:xf] = x[:xf] * np.sin(t * np.pi / 2) + x[n:n + xf] * np.cos(t * np.pi / 2); return y

def norm(x): return x * RMS / (np.sqrt(np.mean(x ** 2)) + 1e-9)

def make_loop(x, st, hint):
    """Abschnitt -> geglätteter, nahtloser Loop (kurze Abschnitte zu 2 s verlängert), optional verschoben -> (Loop, Grundton Hz)"""
    y, ref = flatten(x, pitch0(x, hint))
    if len(y) < 1.5 * SR: y = texture(y, ref, SR, dur=2.0)          # Körner im Zündtakt, kreisförmig nahtlos
    else: y = loopify(y, int(min(0.25, len(y) / SR / 6) * SR))
    if abs(st) > 0.01:
        n = len(y); z = shift(np.concatenate([y, y, y]), st, SR); y = z[n:2 * n].copy(); k = int(0.1 * SR); t = np.linspace(0, 1, k)
        y[:k] = z[n:n + k] * np.sin(t * np.pi / 2) + z[2 * n:2 * n + k] * np.cos(t * np.pi / 2); ref *= 2 ** (st / 12)
    return norm(y), ref

def env(x, h):
    p = np.concatenate([np.zeros(h), x ** 2, np.zeros(h)]); c = np.cumsum(np.concatenate([[0], p]))
    return np.sqrt((c[2 * h:] - c[:-2 * h]) / (2 * h))[:len(x)] + 1e-6

def blip(seg, k=0.55):
    """echter Gasstoß: 10 ms ein-, 0,25 s ausblenden; Pegel über dem Leerlauf mit Exponent 1-k zusammendrücken, Leerlauf-Anteil RMS 0,14"""
    seg = seg.copy(); fi, fo = int(0.01 * SR), int(0.25 * SR); seg[:fi] *= np.linspace(0, 1, fi); seg[-fo:] *= np.linspace(1, 0, fo) ** 2
    e = env(seg, int(0.02 * SR)); idle = np.sqrt(np.mean(seg[fi:int(0.12 * SR)] ** 2)) + 1e-6
    y = seg * np.where(e > idle, (e / idle) ** -k, 1.0); y *= RMS / (np.sqrt(np.mean(y[fi:int(0.12 * SR)] ** 2)) + 1e-9)
    if np.abs(y).max() > 0.95: y *= 0.95 / np.abs(y).max()
    return y

def tabelle(seg, cyl, step=0.025):
    """Drehzahl an jeder Stelle des Durchzugs: Autokorrelation alle 25 ms, Median über ±0,1 s, monoton steigend gemacht"""
    N = 2048; hop = int(step * SR); f = np.fft.rfftfreq(N, 1 / SR); T, P = [], []
    for s in range(0, len(seg) - N, hop):
        w = seg[s:s + N]; X = np.fft.rfft(w * np.hanning(N)); X[(f < 20) | (f > 600)] = 0; y = np.fft.irfft(X, N)
        ac = np.correlate(y, y, "full")[N - 1:]; ac /= ac[0] + 1e-9; L0, L1 = int(SR / 300), int(SR / 30); l = L0 + int(np.argmax(ac[L0:L1]))
        T.append((s + N / 2) / SR); P.append(SR / l)
    lp = np.log(np.array(P)); med = np.array([np.median(lp[max(0, i - 4):i + 5]) for i in range(len(lp))])
    return np.array(T), np.exp(np.maximum.accumulate(med)) * 120 / cyl

def main():
    man_path = os.path.join(OUT, "engine.json"); man = json.load(open(man_path))
    for g, S in SCHICHTEN.items():
        for f in os.listdir(OUT):
            if f.startswith(g + "_"): os.remove(os.path.join(OUT, f))
        cyl = S["cyl"]; zf = cyl / 2; cfg = {"v": 3, "desc": S["desc"], "cyl": cyl, "vol": S["vol"], "scale": S["scale"], "loops": [], "blips": []}
        used = set()
        # 1 Leerlauf + 4 Stufen
        for k, (r, a, d, st, rpm) in enumerate([S["leer"]] + S["stufen"]):
            x, _ = rec(r); used.add(r); y, ref = make_loop(x[int(a * SR):int((a + d) * SR)], st, rpm * zf / 60)
            fn = "%s_%s.wav" % (g, "leer" if k == 0 else "st%d" % k); save_wav(os.path.join(OUT, fn), np.clip(y, -0.99, 0.99))
            cfg["loops"].append([fn, round(ref, 1)])
            print("%s %s: %s %.2f s %+d HT -> Grundton %.1f Hz = %.0f U/min" % (g, fn, r, a, st, ref, ref * 60 / zf))
        # 2 Gasstöße
        for k, (r, a, d) in enumerate(S["blips"]):
            x, _ = rec(r); used.add(r); y = blip(x[int(a * SR):int((a + d) * SR)])
            fn = "%s_blip%d.wav" % (g, k + 1); save_wav(os.path.join(OUT, fn), y); cfg["blips"].append(fn)
            e = env(y, int(0.05 * SR)); print("%s %s: %.2f s, Spitze x%.1f über Leerlauf" % (g, fn, len(y) / SR, e.max() / e[:int(0.1 * SR)].mean()))
        # 3 Durchzüge
        q = []; ref_rms = None
        for k, (r, a, b) in enumerate(S["gran"]):
            x, c = rec(r); used.add(r); seg = x[int(a * SR):int(b * SR)].copy(); fi = int(0.01 * SR); seg[:fi] *= np.linspace(0, 1, fi)
            T, Rr = tabelle(seg, c)
            # Pegel glätten: langsame Lautstärke-Hüllkurve (0,2 s) auf eine Zielkurve bringen, die mit der Drehzahl leicht steigt.
            # Grund: Delta-Durchzug beginnt kalt und leise, Lancer (Onboard) wird lauter – sonst Löcher beim Anfahren und an der Übergabe.
            e = env(seg, int(0.1 * SR)); e = np.convolve(e, np.ones(int(0.2 * SR)) / int(0.2 * SR), "same") + 1e-4
            rr = np.interp(np.arange(len(seg)) / SR, T, Rr); target = 0.11 + 0.06 * np.clip((rr - 1500) / 5000, 0, 1)
            y = seg * np.clip(target / e, 0.05, 20); y *= min(1, 0.97 / np.abs(y).max()); ref_rms = 1
            fn = "%s_dz%d.wav" % (g, k + 1); save_wav(os.path.join(OUT, fn), y)
            q.append({"file": fn, "tab": [[round(float(t), 3), int(v)] for t, v in zip(T[::4], Rr[::4])], "T": T, "R": Rr, "y": y})
            print("%s %s: %s %.2f-%.2f s, %.0f -> %.0f U/min" % (g, fn, r, a, b, Rr[0], Rr[-1]))
        lo, hi = q[0]["R"][0], q[-1]["R"][-1]
        cfg["gran"] = {"quellen": [{"file": d["file"], "tab": d["tab"]} for d in q],
                       # einblenden zwischen Leerlauf und Durchzug-Anfang (darunter spielt das Spiel den Anfang langsamer, Tempo >= 0,55)
                       "von": round(max(cfg_idle(cfg, zf) * 1.2, lo * 0.55)), "bis": round(max(cfg_idle(cfg, zf) * 1.45, lo * 0.85)),
                       "aus": [round(hi * 0.9), round(hi * 1.0)] if S["stufen"] else None}
        if len(q) > 1:   # Übergabe-Drehzahl: Mitte der Überlappung
            a0, b0 = q[1]["R"][0], q[0]["R"][-1]; cfg["gran"]["wechsel"] = round((a0 + b0) / 2); cfg["gran"]["xf"] = round(max(100, (b0 - a0) / 2))
        # 5 Gas weg
        if S["schub"]:
            r, a, d, rpm = S["schub"]; x, _ = rec(r); used.add(r); y, ref = make_loop(x[int(a * SR):int((a + d) * SR)], 0, rpm * zf / 60)
            fn = "%s_schub.wav" % g; save_wav(os.path.join(OUT, fn), np.clip(y, -0.99, 0.99)); cfg["schub"] = [fn, round(ref, 1), 0.35]
            print("%s %s: Grundton %.1f Hz = %.0f U/min" % (g, fn, ref, ref * 60 / zf))
        cfg["credit"] = [{"file": "https://commons.wikimedia.org/wiki/File:" + REC[r][0], "author": REC[r][1], "license": LICENSE} for r in sorted(used)]
        man["groups"][g] = cfg
        print("%s: Granular %s" % (g, {k: v for k, v in cfg["gran"].items() if k != "quellen"}))
    json.dump(man, open(man_path, "w"), indent=1, ensure_ascii=False)

def cfg_idle(cfg, zf): return cfg["loops"][0][1] * 60 / zf

if __name__ == "__main__":
    main()
