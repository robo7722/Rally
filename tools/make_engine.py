# Erzeugt die Motorgeräusche in engine/ mit ElevenLabs (Sound Effects, Modell eleven_text_to_sound_v2).
# Je Auto fünf Drehzahlstufen (Leerlauf, niedrig, mittel, hoch, Begrenzer-nah), jede als nahtlose Schleife.
# Das Spiel blendet je nach Drehzahl zwischen zwei benachbarten Stufen über und passt die Tonhöhe an.
#
# Ablauf je Auto:
#   1. je Stufe TAKES Aufnahmen erzeugen (loop=true, Drehzahl im Prompt). ElevenLabs hält die Drehzahl nur grob ein,
#      deshalb entsteht ein Pool, aus dem jede Stufe besetzt wird.
#   2. in jeder Aufnahme den gleichmäßigsten Abschnitt (WIN s) suchen: Klangspektrum und Lautstärke möglichst konstant
#   3. Zündfrequenz messen (-> tatsächliche Drehzahl, Autokorrelation; mit synthetischen Signalen auf <1 % geprüft)
#   4. beste Besetzung aller Stufen: gleichmäßig, nah an der Soll-Drehzahl, aufsteigend (sonst springt die Tonhöhe beim
#      Überblenden). Liegt eine Stufe zu weit daneben, wird gezielt eine weitere Aufnahme erzeugt (bis TAKES_MAX).
#   5. auf gleiche Lautheit bringen, Naht weich überblenden
#   6. als <auto>_<stufe>.mp3 speichern, mit 0,1 s Vorlauf/Nachlauf (aus der Schleife selbst), damit der MP3-Versatz
#      der Browser beim Schleifen keine Lücke macht. Schleifenlänge und gemessene Drehzahl ("ref") stehen in engine/engine.json.
#
# Braucht: ffmpeg, numpy, scipy und die Umgebungsvariable ELEVENLABS_API_KEY (wird nie ausgegeben).
# Aufruf: python tools/make_engine.py [Auto ...]          (ohne Angabe: alle Autos)
import json, os, subprocess, sys, time, urllib.request, urllib.error
import numpy as np
from scipy.signal import butter, sosfiltfilt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "engine")
RAW = os.path.join(ROOT, "tools", "_engine_raw")   # Rohaufnahmen (nicht im Repo)
SR = 44100
DUR = 5.0          # Länge je Aufnahme (s)
TAKES = 3
TAKES_MAX = 6      # höchstens so viele Varianten je Stufe, wenn keine passt
WIN = 2.6          # Länge des ausgewählten, gleichmäßigsten Abschnitts (s)
XF = 0.12          # Überblendung an der Naht (s)
PAD = 0.1          # Vor-/Nachlauf in der Datei (s)

# Drehzahlstufen (passend zur Spielphysik: Leerlauf 950, Hochschalten 7250, Begrenzer 7800)
STEPS = [
    ("idle", 950,  "idling at a steady {rpm} rpm with no throttle, lumpy idle"),
    ("low",  2200, "running at a constant steady {rpm} rpm under light throttle"),
    ("mid",  3700, "running at a constant steady {rpm} rpm under half throttle, steady drone"),
    ("high", 5400, "running at a constant steady {rpm} rpm under full throttle, loud steady drone"),
    ("max",  7200, "screaming at a constant {rpm} rpm at full throttle just below the rev limiter, loud steady high-pitched drone"),
]

# Motor je Auto (an den echten Rallyeautos orientiert); cyl = Zylinder (für die Zündfrequenz)
CARS = {
    "fiat":    (4, "Fiat 131 Abarth Rally, 2.0 litre naturally aspirated 16-valve inline-four with twin Weber carburettors, raspy induction roar, straight exhaust"),
    "r5":      (4, "Renault 5 Turbo rally car, 1.4 litre turbocharged inline-four mid-engine, raspy small turbo engine with turbo whistle"),
    "bmw":     (4, "BMW M3 E30 Group A rally car, S14 2.3 litre naturally aspirated inline-four with individual throttle bodies, hard metallic high-revving rasp"),
    "delta":   (4, "Lancia Delta HF Integrale Group A, 2.0 litre 16-valve turbocharged inline-four, gruff turbo bark and wastegate chatter"),
    "escort":  (4, "Ford Escort RS Cosworth rally car, 2.0 litre YB turbocharged inline-four, deep raw turbo engine with big turbo whoosh"),
    "celica":  (4, "Toyota Celica GT-Four ST185 rally car, 3S-GTE 2.0 litre turbocharged inline-four, smooth but angry turbo engine"),
    "subaru":  (4, "Subaru Impreza WRC rally car, 2.0 litre turbocharged boxer flat-four, deep off-beat boxer rumble, anti-lag crackle"),
    "lancer":  (4, "Mitsubishi Lancer Evolution WRC rally car, 4G63 2.0 litre turbocharged inline-four, harsh aggressive turbo engine with anti-lag"),
    "audi":    (5, "Audi Sport Quattro S1 E2 Group B rally car, 2.1 litre turbocharged inline-five, iconic warbling five-cylinder howl, turbo whistle"),
    "rs200":   (4, "Ford RS200 Group B rally car, 1.8 litre Cosworth BDT turbocharged inline-four mid-engine, raw angry turbo engine"),
    "p959":    (6, "Porsche 959 rally car, 2.85 litre twin-turbo flat-six, smooth deep boxer six with turbo whoosh"),
    "s4":      (4, "Lancia Delta S4 Group B rally car, 1.8 litre supercharged and turbocharged inline-four mid-engine, supercharger whine and turbo"),
    "p205":    (4, "Peugeot 205 Turbo 16 Group B rally car, 1.8 litre turbocharged inline-four mid-engine, sharp raspy turbo engine"),
    "stratos": (6, "Lancia Stratos HF rally car, Ferrari Dino 2.4 litre naturally aspirated V6, exotic high-pitched V6 howl"),
    "mini":    (4, "classic Mini Cooper S rally car, 1.3 litre BMC A-series inline-four, small buzzy raspy engine with straight-cut gear whine"),
    "fulvia":  (4, "Lancia Fulvia HF rally car, 1.6 litre narrow-angle V4, raspy twin-carburettor engine"),
    "alpine":  (4, "Alpine A110 1600S rally car, 1.6 litre Renault inline-four rear-engine with Weber carburettors, light raspy sporty engine"),
}

def api_key():
    k = os.environ.get("ELEVENLABS_API_KEY")
    if not k and os.name == "nt":
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as h: k = winreg.QueryValueEx(h, "ELEVENLABS_API_KEY")[0]
        except OSError: k = None
    return (k or "dummy").strip()   # in der Cloud-Umgebung ergänzt ein Proxy den Schlüssel

def generate(prompt, path):
    if os.path.exists(path): return
    body = {"text": prompt, "duration_seconds": DUR, "loop": True, "prompt_influence": 0.6, "model_id": "eleven_text_to_sound_v2"}
    req = urllib.request.Request("https://api.elevenlabs.io/v1/sound-generation?output_format=mp3_44100_192", data=json.dumps(body).encode(),
                                 headers={"xi-api-key": api_key(), "Content-Type": "application/json", "User-Agent": "engine-tool"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=120) as r: data = r.read()
            break
        except (urllib.error.HTTPError, urllib.error.URLError) as e:
            code = getattr(e, "code", 0)
            if code in (0, 429, 500, 502, 503) and attempt < 4: time.sleep(3 + attempt * 5); continue
            sys.exit("Fehler %s: %s" % (code, e.read().decode("utf-8", "replace")[:300] if hasattr(e, "read") else e))
    with open(path, "wb") as f: f.write(data)

def decode(path):
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "pipe:1"], capture_output=True, check=True).stdout
    return np.frombuffer(pcm, np.float32).astype(np.float64)

def firing_freq(x, f_exp):
    """Zündfrequenz per Autokorrelation der tieffrequenten Hüllkurve, gesucht im Bereich 0,55..1,8 x erwartet"""
    sos = butter(4, [15, min(4000, f_exp * 6)], btype="band", fs=SR, output="sos")
    y = sosfiltfilt(sos, x)
    y -= y.mean()
    n = len(y); F = np.fft.rfft(y, 2 * n); ac = np.fft.irfft(F * np.conj(F))[:n]; ac /= ac[0] + 1e-12
    lo, hi = int(SR / (f_exp * 1.8)), int(SR / (f_exp * 0.55))
    hi = min(hi, n // 3)
    i = lo + int(np.argmax(ac[lo:hi]))
    # parabolische Verfeinerung
    if 0 < i < n - 1:
        a, b, c = ac[i - 1], ac[i], ac[i + 1]; d = 0.5 * (a - c) / (a - 2 * b + c + 1e-12); i = i + d
    return SR / i, float(ac[int(round(i))])

def spec_frames(x, n=4096, hop=1024):
    win = np.hanning(n); fr = np.arange(n // 2 + 1) * SR / n; band = (fr > 25) & (fr < 3000)
    idx = range(0, len(x) - n, hop)
    S = np.array([np.log(np.abs(np.fft.rfft(x[i:i + n] * win))[band] + 1e-6) for i in idx])
    E = np.array([np.sqrt(np.mean(x[i:i + n] ** 2)) + 1e-9 for i in idx])
    return S, 20 * np.log10(E), hop

def analyse(x, cyl, rpm_nom):
    """gleichmäßigsten Abschnitt suchen und messen -> dict(start, rpm, conf, score)"""
    f_exp = rpm_nom * cyl / 120
    S, E, hop = spec_frames(x)
    nw = int(WIN * SR / hop); best = None
    for s0 in range(0, len(S) - nw, 2):
        Sw = S[s0:s0 + nw]
        flux = float(np.mean(np.abs(Sw - Sw.mean(0))))           # wie stark sich das Klangbild ändert
        ld = float(np.std(E[s0:s0 + nw]))                         # Lautstärkeschwankung (dB)
        sc = flux + ld * 0.08
        if best is None or sc < best[0]: best = (sc, s0)
    sc, s0 = best; start = s0 * hop; seg = x[start:start + int(WIN * SR)]
    f, conf = firing_freq(seg, f_exp)
    fs = [firing_freq(seg[i:i + SR // 2], f)[0] for i in range(0, len(seg) - SR // 2, SR // 4)]
    pitch_var = float(np.std(np.log(fs)))
    return dict(start=start, rpm=f * 120 / cyl, conf=conf, pitch_var=pitch_var, steady=sc, score=sc + pitch_var * 6 + (1 - conf) * 0.4)

def make_loop(x):
    """Naht weich überblenden: Schleifenlänge L = len - XF; Anfang mischt in das Ende über"""
    nx = int(XF * SR); L = len(x) - nx
    t = np.linspace(0, np.pi / 2, nx)
    y = x[:L].copy()
    y[:nx] = x[:nx] * np.sin(t) + x[L:L + nx] * np.cos(t)
    return y

def loudnorm(y, target_db=-17.0):
    rms = np.sqrt(np.mean(y ** 2)) + 1e-9
    y = y * 10 ** ((target_db - 20 * np.log10(rms)) / 20)
    peak = np.max(np.abs(y))
    if peak > 0.97: y *= 0.97 / peak   # Spitzen begrenzen
    return y

def encode(y, path):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ac", "1", "-ar", str(SR), "-i", "pipe:0", "-c:a", "libmp3lame", "-b:a", "96k", path],
                   input=y.astype(np.float32).tobytes(), check=True)

def usable(slot, j):
    """darf eine Aufnahme mit Prompt j die Stufe slot besetzen? Leerlauf nur aus Leerlauf-Prompts, sonst Nachbar-Prompts."""
    return (slot == 0) == (j == 0) and abs(slot - j) <= 1

def choose(pool):
    """pool: Liste von (Prompt-Index, Wertung, Drehzahl) -> beste Besetzung der Stufen (Pool-Indizes), Kosten.
    Kosten: Gleichmäßigkeit + Abweichung von der Soll-Drehzahl; die Drehzahlen müssen um mindestens 15 % steigen."""
    import itertools
    cand = [sorted([i for i, (j, sc, r) in enumerate(pool) if usable(s, j)], key=lambda i: pool[i][1] + 1.5 * abs(np.log(pool[i][2] / STEPS[s][1])))[:8]
            for s in range(len(STEPS))]
    best = (1e9, None)
    for combo in itertools.product(*cand):
        if len(set(combo)) < len(combo): continue
        cost, prev = 0.0, 0
        for s, i in enumerate(combo):
            _, sc, rpm = pool[i]; dev = abs(np.log(rpm / STEPS[s][1]))
            cost += sc + 1.5 * dev + (4 if dev > 0.45 else 0) + (6 if rpm < prev * 1.15 else 0)
            prev = rpm
        if cost < best[0]: best = (cost, combo)
    return best

def main():
    os.makedirs(OUT, exist_ok=True); os.makedirs(RAW, exist_ok=True)
    man_path = os.path.join(OUT, "engine.json")
    man = json.load(open(man_path)) if os.path.exists(man_path) else {}
    man["pad"] = PAD; man.setdefault("cars", {})
    todo = sys.argv[1:] or list(CARS)
    for cid in todo:
        cyl, desc = CARS[cid]
        prompts = ["%s, engine %s, recorded close to the exhaust from behind the car, constant engine speed, no gear shifts, no revving up or down, isolated engine sound only"
                   % (desc, how.format(rpm=rpm_nom)) for _, rpm_nom, how in STEPS]
        pool = []                     # (Prompt-Index, Variante, Ton, Analyse)
        cnt = [0] * len(STEPS)
        def add(j):
            name, rpm_nom, _ = STEPS[j]; k = cnt[j]; cnt[j] += 1
            raw = os.path.join(RAW, "%s_%s_%d.mp3" % (cid, name, k))
            generate(prompts[j], raw)
            x = decode(raw); a = analyse(x, cyl, rpm_nom); pool.append((j, k, x, a))
            print("  %-7s %-4s Take %d: ab %.1f s, %5.0f U/min (soll %d, Sicherheit %.2f), Tonhöhe ±%.3f, gleichmäßig %.3f, Wertung %.2f"
                  % (cid, name, k, a["start"] / SR, a["rpm"], rpm_nom, a["conf"], a["pitch_var"], a["steady"], a["score"]))
        for j in range(len(STEPS)):
            for _ in range(TAKES): add(j)
        while True:
            cost, combo = choose([(j, a["score"], a["rpm"]) for j, _, _, a in pool])
            # schlechteste Stufe (zu weit weg von der Soll-Drehzahl oder nicht aufsteigend) bekommt eine weitere Variante
            worst, ws, prev = 0, -1, 0
            for s_, i in enumerate(combo):
                rpm = pool[i][3]["rpm"]; pen = abs(np.log(rpm / STEPS[s_][1])) + (1 if rpm < prev * 1.15 else 0); prev = rpm
                if pen > worst: worst, ws = pen, s_
            if worst <= 0.3 or cnt[ws] >= TAKES_MAX: break
            print("  -> weitere Variante für %s (beste: %.0f U/min)" % (STEPS[ws][0], pool[combo[ws]][3]["rpm"])); add(ws)
        steps = []
        for s_, i in enumerate(combo):
            name, rpm_nom, _ = STEPS[s_]; j, k, x, a = pool[i]
            seg = x[a["start"]:a["start"] + int(WIN * SR)]
            y = loudnorm(make_loop(seg)); L = len(y); p = int(PAD * SR)
            encode(np.concatenate([y[-p:], y, y[:p]]), os.path.join(OUT, "%s_%s.mp3" % (cid, name)))
            steps.append({"n": name, "rpm": rpm_nom, "ref": round(a["rpm"]), "len": round(L / SR, 5), "src": "%s_%d" % (STEPS[j][0], k)})
        man["cars"][cid] = {"cyl": cyl, "steps": steps}
        json.dump(man, open(man_path, "w"), indent=1)
        print("%s fertig: %s" % (cid, ", ".join("%s %d" % (s["n"], s["ref"]) for s in steps)))

if __name__ == "__main__":
    main()
