// Hörprobe aus dem ECHTEN Spiel-Code: lädt den Motor-Abschnitt aus index.html in eine leere Seite und rendert offline
// (OfflineAudioContext) denselben Ablauf wie tools/engine_hoerprobe.py. Gibt Pegel je 0,1 s aus, schreibt engine_demo/<auto>.mp3.
// Braucht: node + playwright, ffmpeg, lokaler Server im Repo-Ordner: python -m http.server 8765
// Aufruf: node tools/engine_hoerprobe_spiel.js mini lancer audi
const { chromium } = require('playwright'); const fs = require('fs');
const html = fs.readFileSync(require('path').join(__dirname, '..', 'index.html'), 'utf8');
const a = html.indexOf('// ---------- Motor aus echten Aufnahmen'), b = html.indexOf('let lastThr = 0, popT = 0, stoneT = 0;');
const code = html.slice(a, b);
(async () => {
  const br = await chromium.launch(); const p = await br.newPage(); const errs = [];
  p.on('pageerror', e => errs.push(String(e))); p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  await p.route('**/__t.html', rt => rt.fulfill({ contentType: 'text/html', body: '<!doctype html><script>const clamp=(x,a,b)=>x<a?a:x>b?b:x;const AU={};\n' + code + '\nwindow.E={ENG,engLoad,engUpd};</script>' }));
  await p.goto('http://localhost:8765/__t.html');
  for (const car of process.argv.slice(2)) {
    const res = await p.evaluate(async (car) => {
      const SR = 32000, DUR = 18.5, ac = new OfflineAudioContext(1, SR * DUR, SR);
      AU.ctx = ac; AU.eng = ac.createGain(); AU.eng.connect(ac.destination);
      AU.engLp = ac.createBiquadFilter(); AU.engLp.type = 'lowpass'; AU.engLp.frequency.value = 6000; AU.engLp.connect(AU.eng);
      AU.engS = ac.createGain(); AU.engS.gain.value = 0; AU.engS.connect(AU.engLp);
      const { ENG, engLoad, engUpd } = window.E; ENG.id = null; ENG.ready = false; engLoad(car);
      for (let i = 0; i < 200 && !ENG.ready; i++) await new Promise(r => setTimeout(r, 50));
      if (!ENG.ready) return { fehler: 'nicht geladen' };
      // Ablauf wie tools/engine_hoerprobe.py: 0-2,5 Leerlauf · 2,5 Gasstoß · 5,6 Gasstoß · 9,4-12,2 Anfahren · Schalten · 12,4-14,4 Vollgas · Gas weg
      const plan = t => t < 2.5 ? [950, 0] : t < 2.75 ? [950, 0.8] : t < 5.6 ? [950, 0] : t < 5.85 ? [950, 0.8] : t < 9.4 ? [950, 0] :
        t < 12.2 ? [950 + (7000 - 950) * (t - 9.4) / 2.8, 1] : t < 12.4 ? [6000, 0.2] : t < 14.4 ? [5000 + 2300 * (t - 12.4) / 2, 1] : t < 17 ? [7300 - 6350 * (t - 14.4) / 2.6, 0] : [950, 0];
      let rpm = 950; const dt = 0.02, log = [];
      for (let t = 0.02; t < DUR - 0.05; t += dt) ac.suspend(+t.toFixed(3)).then(() => { const [r, th] = plan(t); rpm += (r - rpm) * 0.5;
        engUpd(rpm, th, 1, ac.currentTime, true, t < 9.4); if (Math.abs(t * 10 - Math.round(t * 10)) < 0.01) log.push(t.toFixed(1) + ' bl=' + !!ENG.bl + ' gr=' + ENG.gr.length); ac.resume(); });
      const buf = await ac.startRendering(), d = buf.getChannelData(0), h = SR / 10, lv = [];
      for (let i = 0; i + h <= d.length; i += h) { let s = 0; for (let k = i; k < i + h; k++) s += d[k] * d[k]; lv.push(+Math.sqrt(s / h).toFixed(3)); }
      return { lv, wav: Array.from(d.filter((_, i) => i % 1 === 0)).map(v => Math.round(v * 20000)), info: { blips: (ENG.D.blips || []).length, gran: !!ENG.D.gran, loops: ENG.D.loops.length } };
    }, car);
    if (res.fehler) { console.log(car, res.fehler); continue; }
    const pcm = Buffer.alloc(res.wav.length * 2); res.wav.forEach((v, i) => pcm.writeInt16LE(Math.max(-32768, Math.min(32767, v)), i * 2));
    const dir = require('path').join(__dirname, '..', 'engine_demo'); fs.mkdirSync(dir, { recursive: true });
    require('child_process').execFileSync('ffmpeg', ['-v', 'error', '-y', '-f', 's16le', '-ar', '32000', '-ac', '1', '-i', '-', '-b:a', '128k', require('path').join(dir, car + '.mp3')], { input: pcm });
    console.log(car, JSON.stringify(res.info)); console.log('  Pegel:', res.lv.map((v, i) => (i / 10).toFixed(1) + ':' + v).join(' '));
  }
  console.log('Fehler:', errs); await br.close();
})();
