# ElevenLabs: verfügbare Stimmen auflisten und Hörproben erzeugen.
# Der Schlüssel wird aus der Umgebungsvariable ELEVENLABS_API_KEY gelesen (auch direkt aus den Windows-Benutzer-Variablen,
# damit kein Neustart nötig ist). Er wird nie ausgegeben oder gespeichert.
# Aufruf:  python tools/el_probe.py                 -> Stimmen auflisten
#          python tools/el_probe.py <voice_id> ...  -> Hörproben je Stimme nach el_test/
import json, os, sys, urllib.request, urllib.error

API = "https://api.elevenlabs.io/v1"
MODEL = "eleven_multilingual_v2"
SAMPLES = {"ansage": "Achtung, Links drei, zieht zu, in Rechts fünf Haarnadel, hundertfünfzig.", "kuppe": "Kuppe, fünfzig."}

def key():
    k = os.environ.get("ELEVENLABS_API_KEY")
    if not k and os.name == "nt":
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as h: k = winreg.QueryValueEx(h, "ELEVENLABS_API_KEY")[0]
        except OSError: k = None
    if not k: sys.exit("ELEVENLABS_API_KEY ist nicht gesetzt.")
    return k.strip()

def call(path, body=None):
    req = urllib.request.Request(API + path, data=json.dumps(body).encode() if body else None,
                                 headers={"xi-api-key": key(), "Content-Type": "application/json", "User-Agent": "voice-tool"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r: return r.read()
    except urllib.error.HTTPError as e:
        raise RuntimeError("Fehler %d: %s" % (e.code, e.read().decode("utf-8", "replace")[:300]))

if len(sys.argv) == 1:
    try:
        sub = json.loads(call("/user/subscription"))
        print("Tarif: %s, Zeichen verbraucht: %s von %s" % (sub.get("tier"), sub.get("character_count"), sub.get("character_limit")))
    except RuntimeError as e: print("Kontodaten nicht lesbar:", str(e)[:160])
    for v in json.loads(call("/voices"))["voices"]:
        lab = v.get("labels") or {}
        print("%s | %-22s | %s | %s | %s | %s" % (v["voice_id"], v["name"][:22], v.get("category"), lab.get("gender"), lab.get("accent"), lab.get("language") or ""))
else:
    os.makedirs("el_test", exist_ok=True)
    for vid in sys.argv[1:]:
        for name, text in SAMPLES.items():
            mp3 = call("/text-to-speech/%s?output_format=mp3_44100_128" % vid, {"text": text, "model_id": MODEL})
            p = os.path.join("el_test", "%s_%s.mp3" % (vid[:8], name)); open(p, "wb").write(mp3); print(p, len(mp3))
