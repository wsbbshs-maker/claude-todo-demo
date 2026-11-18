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
    [(0, 2, 'WENN DU *NACHTS*', J), (3, 6, 'ALLEINE IN EINEM *TUNNEL*', J), (7, 7, 'ARBEITEST', J), (8, 11, 'GIBT ES EINE *REGEL*', J), (12, 13, 'SCHAU NICHT', J), (14, 16, 'AUF *KAMERA VIER*', J)],
    [(17, 19, 'ICH BIN *JONAS*', J), (20, 20, '*NACHTWACHE*', J), (21, 22, 'IM NEUEN', J), (23, 24, '*BRANDBERGTUNNEL*', J), (25, 27, 'NOCH NICHT *ERÖFFNET*', J), (28, 29, 'NIEMAND DARF', J), (30, 31, '*HIER REIN*', J)],
    [(32, 35, 'UM *3:07 UHR*', J), (36, 39, 'STEHT AUF KAMERA VIER', J), (40, 40, '*JEMAND*', J), (41, 44, 'MITTEN AUF DER *FAHRBAHN*', J), (45, 47, 'ER SCHAUT *DIREKT*', J), (48, 50, 'IN DIE *KAMERA*', J)],
    [(51, 54, 'ICH FUNKE *MEHMET* AN', J), (55, 56, 'AM *NORDPORTAL*', J), (57, 58, 'ER SAGT', J), (59, 62, 'DAS TOR *IST ZU*', M), (63, 65, 'HIER IST *KEINER*', M), (66, 66, 'REINGEKOMMEN', M)],
    [(67, 68, 'ICH SCHAUE', J), (69, 70, '*WIEDER* HIN', J), (71, 73, 'ER IST *NÄHER*', J)],
    [(74, 76, 'ICH GEHE RAUS', J), (77, 79, 'IN DIE *RÖHRE*', J), (80, 81, 'DIE LAMPEN *SUMMEN*', J), (82, 83, 'DIE FAHRBAHN', J), (84, 85, 'IST *LEER*', J)],
    [(86, 88, 'ZURÜCK IM *CONTAINER*', J), (89, 90, '*KAMERA VIER*', J), (91, 94, 'ER STEHT *GENAU DA*', J), (95, 98, 'WO ICH EBEN *STAND*', J)],
    [(99, 100, 'UND JETZT', J), (101, 103, '*VERSTEHE* ICH ES', J), (104, 107, 'ER BEWEGT SICH NUR', J), (108, 110, 'WENN ICH *NICHT*', J), (111, 111, '*HINSEHE*', J)],
    [(112, 113, 'DANN *KNACKT*', J), (114, 115, 'DAS FUNKGERÄT', J), (116, 117, 'MEHMET *FLÜSTERT*', J), (118, 118, '*JONAS*', M), (119, 121, 'AUF MEINER KAMERA', M), (122, 124, 'IST ER *AUCH*', M), (125, 128, 'UND ER IST SCHON', M), (129, 130, '*BEI DIR*', M)],
    [(131, 133, 'ICH DREHE MICH', J), (134, 135, '*NICHT* UM', J)],
    [(136, 137, '*TEIL 2*', J), (138, 138, 'MORGEN', J)],
]
# zusätzliche Stille (Sekunden) VOR diesem Wort – mehr Spannung vor "Teil 2"
EXTRA_PAUSE = {136: 1.0}


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
    cut = (words[wi - 1][2] + words[wi][1]) / 2
    i = int(cut * SR)
    mix = np.concatenate([mix[:i], np.zeros(int(pause * SR)), mix[i:]])
    for w in words[wi:]: w[1] += pause; w[2] += pause


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
    part = radio(mix[s:e]); fade = int(0.02 * SR)
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
    for ci, (a, b, text, who) in enumerate(seg):
        st = words[a][1]
        en = words[seg[ci + 1][0]][1] if ci + 1 < len(seg) else words[b][2] + 0.3
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
