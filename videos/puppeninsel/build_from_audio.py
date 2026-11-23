"""Baut Tonspur + Timing aus fertigen Sprachaufnahmen (z. B. Dreamina/CapCut).
Aufruf: python build_from_audio.py <words.json> <ausgabe-ordner> <audio1> <audio2> ...
words.json: Wort-Zeitstempel je Datei (aus Whisper), Schlüssel = Dateipfad."""
import json, sys, subprocess, wave
import numpy as np

WORDS, OUT, FILES = sys.argv[1], sys.argv[2], sys.argv[3:]
SR = 48000; FPS = 30; GAP = 0.3

# Untertitel-Chunks: (erstes Wort, letztes Wort, Anzeige, Sprecher) – Wortindizes im Gesamttext
J, M = 'jonas', 'mehmet'
SEGS = [
    [(0, 2, 'IN *340 METERN*', J), (3, 3, 'HÖHE', J), (4, 5, '*KLOPFT* ETWAS', J), (6, 8, 'AN MEINE *DROHNE*', J)],
    [(9, 10, 'ICH DREHE', J), (11, 12, 'DIE *KAMERA*', J), (13, 15, 'UND ES *BLINZELT*', J), (16, 16, '*SEITWÄRTS*', J)],
    [(17, 20, 'ICH BIN *TIM*, 19', J), (21, 24, 'ICH FILME IN *MEXIKO*', J), (25, 25, '*HOCHZEITEN*', J), (26, 28, 'MIT MEINER DROHNE', J), (29, 31, 'HEUTE NUR *DSCHUNGEL*', J), (32, 33, '*DACHTE ICH*', J)],
    [(34, 36, 'NEBEN MEINER DROHNE', J), (37, 39, 'FLIEGT EIN *FLUGSAURIER*', J), (40, 41, '*ZEHN METER*', J), (42, 42, 'SPANNWEITE', J), (43, 45, 'UND AM BEIN', J), (46, 48, 'EIN BLINKENDER *SENDER*', J)],
    [(49, 50, 'DANN *PIEPT*', J), (51, 52, 'MEIN AKKU', J), (53, 54, '*18 PROZENT*', J), (55, 56, 'UND ER', J), (57, 58, '*PIEPT NACH*', J), (59, 60, '*EXAKT* GLEICH', J)],
    [(61, 62, 'ER LEGT', J), (63, 65, 'DEN KOPF *SCHIEF*', J), (66, 68, 'UND *SCHNAPPT* ZU', J)],
    [(69, 70, 'SIGNAL WEG', J), (71, 72, 'DROHNE WEG', J), (73, 75, 'ABER DAS VIDEO', J), (76, 79, 'IST AUF MEINEM *HANDY*', J), (80, 80, 'NATÜRLICH', J), (81, 83, '*POSTE* ICH ES', J), (84, 84, 'SOFORT', J), (85, 88, 'DAS GEHT *SAFE VIRAL*', J)],
    [(89, 91, 'NACHTS UM *DREI*', J), (92, 93, '*KLOPFT* ES', J), (94, 94, '*WIEDER*', J), (95, 95, 'DIESMAL', J), (96, 98, 'AN MEINER *TÜR*', J)],
    [(99, 100, 'ZWEI *MÄNNER*', J), (101, 102, 'SCHWARZE *ANZÜGE*', J), (103, 103, '*SONNENBRILLEN*', J), (104, 107, 'MITTEN IN DER *NACHT*', J), (108, 110, 'AUF DEM AUSWEIS', J), (111, 111, '*PROYECTO QUETZAL*', J)],
    [(112, 113, 'EINER SAGT', J), (114, 116, '*LÖSCH* DAS VIDEO', M), (117, 120, 'WIR JAGEN IHN *NICHT*', M), (121, 123, 'WIR *VERSTECKEN* IHN', M)],
    [(124, 125, 'DANN *VIBRIERT*', J), (126, 127, 'MEIN HANDY', J), (128, 129, '*ZWEI MILLIONEN*', J), (130, 130, 'AUFRUFE', J), (131, 132, 'MIT *STANDORT*', J)],
    [(133, 134, 'DER MANN', J), (135, 136, 'WIRD *STILL*', J), (137, 139, 'DANN NIMMT ER', J), (140, 142, 'DIE *SONNENBRILLE* AB', J)],
    [(143, 144, 'UND *BLINZELT*', J), (145, 145, '*SEITWÄRTS*', J)],
    [(146, 147, '*TEIL 2*', J), (148, 149, 'MORGEN', J)],
]
# zusätzliche Stille (Sekunden) VOR diesem Wort – mehr Spannung vor "Teil 2"
EXTRA_PAUSE = {0: 0.9, 34: 0.5, 69: 0.6, 89: 0.5, 124: 0.2, 143: 0.4, 146: 1.0}


def load(f):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', f, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)


wj = json.load(open(WORDS))
audio, words, off = [], [], 0.0
for f in FILES:
    a = load(f); audio.append(a); audio.append(np.zeros(int(GAP * SR)))
    words += [[w[0], w[1] + off, w[2] + off] for w in wj[f]]
    off += len(a) / SR + GAP
mix = np.concatenate(audio)

# Extra-Pausen einfügen
for wi, pause in sorted(EXTRA_PAUSE.items(), reverse=True):
    cut = 0.0 if wi == 0 else (words[wi - 1][2] + words[wi][1]) / 2
    i = int(cut * SR)
    mix = np.concatenate([mix[:i], np.zeros(int(pause * SR)), mix[i:]])
    for w in words[wi:]: w[1] += pause; w[2] += pause


def deep(a):
    import tempfile, os
    d = tempfile.mkdtemp()
    fi, fo = os.path.join(d, 'i.wav'), os.path.join(d, 'o.wav')
    with wave.open(fi, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(a / (np.abs(a).max() + 1e-9), -1, 1) * 32767 * 0.9).astype('<i2').tobytes())
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', fi, '-af', 'rubberband=pitch=0.8,lowpass=f=5000', fo], check=True)
    with wave.open(fo) as w: y = np.frombuffer(w.readframes(w.getnframes()), '<i2').astype(np.float64) / 32767
    y = np.concatenate([y, np.zeros(max(0, len(a) - len(y)))])[:len(a)]
    return y / (np.abs(y).max() + 1e-9) * np.abs(a).max()


def radio(a):
    X = np.fft.rfft(a); f = np.fft.rfftfreq(len(a), 1 / SR)
    X[(f < 350) | (f > 3200)] = 0
    y = np.fft.irfft(X, len(a))
    pk = np.abs(y).max() + 1e-9
    y = np.tanh(y / pk * 2.5) / np.tanh(2.5) * pk
    y += np.random.default_rng(1).standard_normal(len(y)) * pk * 0.04
    return y * 0.9


# Funkfilter auf Mehmets Passagen (weich überblendet)
for seg in SEGS:
    ms = [c for c in seg if c[3] == M]
    if not ms: continue
    s = int((words[ms[0][0]][1] - 0.04) * SR); e = int((words[ms[-1][1]][2] + 0.12) * SR)
    part = deep(mix[s:e]); fade = int(0.02 * SR)
    ramp = np.ones(e - s); ramp[:fade] = np.linspace(0, 1, fade); ramp[-fade:] = np.linspace(1, 0, fade)
    mix[s:e] = mix[s:e] * (1 - ramp) + part * ramp

end_t = words[-1][2] + 1.6
mix = np.concatenate([mix, np.zeros(max(0, int(end_t * SR) - len(mix)))])[:int(end_t * SR)]
mix = mix / (np.abs(mix).max() + 1e-9) * 0.95
with wave.open(f'{OUT}/voice.wav', 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype('<i2').tobytes())

# Timing
timing = []
for si, seg in enumerate(SEGS):
    chunks = []
    def cstart(c):
        a = c[0]; f = c[4][0] if len(c) > 4 else 0.0
        return words[a][1] + f * (words[a][2] - words[a][1])
    for ci, c in enumerate(seg):
        a, b, text, who = c[:4]
        st = cstart(c)
        en = cstart(seg[ci + 1]) if ci + 1 < len(seg) else words[b][2] + 0.3
        chunks.append({'text': text, 'speaker': who, 'start': round(st, 3), 'end': round(en, 3)})
    timing.append({'start': round(max(0, words[seg[0][0]][1] - 0.15), 3), 'chunks': chunks})
timing[0]['start'] = 0.0
for i in range(len(timing)):
    timing[i]['end'] = timing[i + 1]['start'] if i + 1 < len(timing) else round(end_t, 3)

# Mund pro Frame
spf = SR // FPS; n = int(end_t * FPS) + 1
mouth = np.array([np.sqrt(np.mean(mix[f * spf:(f + 1) * spf] ** 2)) if f * spf < len(mix) else 0 for f in range(n)])
mouth = np.clip(mouth / (np.percentile(mouth[mouth > 0.01], 90) + 1e-9), 0, 1); mouth[mouth < 0.12] = 0
with open(f'{OUT}/timing.js', 'w') as fh:
    fh.write('// automatisch erzeugt von build_from_audio.py\n')
    fh.write('var TIMING=' + json.dumps({'duration': round(end_t - 0.4, 3), 'segs': timing}, ensure_ascii=False) + ';\n')
    fh.write('var MOUTH=' + json.dumps([round(float(x), 2) for x in mouth]) + ';\n')
    fh.write("if(typeof module!=='undefined')module.exports={TIMING,MOUTH};\n")
print('Dauer', round(end_t, 2))
