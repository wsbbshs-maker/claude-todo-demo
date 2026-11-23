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
    [(0, 2, 'EINE DIESER *PUPPEN*', J), (3, 5, 'IST *KEINE* PUPPE', J)],
    [(6, 8, 'DU SIEHST GERADE', J), (9, 11, 'EINEN DER *GRUSELIGSTEN*', J), (12, 14, '*ORTE* DER WELT', J), (15, 17, 'WO ER IST', J), (18, 20, 'SAGE ICH DIR', J), (21, 22, 'AM *ENDE*', J)],
    [(23, 25, 'ICH WAR NOCH', J), (26, 27, 'EIN *KIND*', J), (28, 30, 'ALS ICH HIER', J), (31, 34, 'INS *WASSER* GEFALLEN BIN', J), (35, 35, 'SEITDEM', J), (36, 38, 'BIN ICH *HIER*', J)],
    [(39, 40, 'DANN KAM', J), (41, 43, 'EIN *ALTER MANN*', J), (44, 47, 'ER HAT EINE *PUPPE*', J), (48, 50, 'IM WASSER GEFUNDEN', J), (51, 52, '*MEINE* PUPPE', J)],
    [(53, 55, 'ER HAT SIE', J), (56, 59, 'IN EINEN *BAUM* GEHÄNGT', J), (60, 61, 'DAMIT ICH', J), (62, 64, 'NICHT *ALLEIN* BIN', J)],
    [(65, 67, 'DANN NOCH EINE', J), (68, 70, 'UND NOCH EINE', J), (71, 73, '*FÜNFZIG JAHRE* LANG', J), (74, 75, 'AM ENDE', J), (76, 77, '*ÜBER TAUSEND*', J)],
    [(78, 81, 'NACHTS HAT ER SIE', J), (82, 83, '*FLÜSTERN* GEHÖRT', J), (84, 86, 'ER HAT GESAGT', J), (87, 88, 'SIE BEWEGEN', J), (89, 90, 'DIE *AUGEN*', J), (91, 93, 'ER HATTE *RECHT*', J)],
    [(94, 96, '*SPEICHER* DIR DAS', J), (97, 97, 'LIEBER', J), (98, 100, 'BEIM *ZWEITEN* MAL', J), (101, 102, 'SIEHST DU', J), (103, 105, 'WELCHE PUPPE DICH', J), (106, 109, 'DIE GANZE ZEIT *ANSCHAUT*', J)],
    [(110, 112, 'IM JAHR *2001*', J), (113, 115, 'HABEN SIE IHN', J), (116, 116, '*GEFUNDEN*', J), (117, 118, 'IM KANAL', J), (119, 120, 'GENAU DA', J), (121, 125, 'WO ER *MICH* GEFUNDEN HAT', J)],
    [(126, 126, 'SEITDEM', J), (127, 128, 'BIN ICH', J), (129, 131, 'NICHT MEHR *ALLEIN*', J)],
    [(132, 135, 'ICH HABE AM ANFANG', J), (136, 136, 'GESAGT', J), (137, 139, 'EINE DIESER PUPPEN', J), (140, 142, 'IST *KEINE* PUPPE', J), (143, 145, '*DAS WAR ICH*', J)],
    [(146, 148, 'DIESER ORT HEISST', J), (149, 152, '*ISLA DE LAS MUÑECAS*', J), (153, 156, 'DIE *INSEL DER PUPPEN*', J), (157, 158, 'IN *MEXIKO*', J)],
    [(159, 160, '*FOLG MIR*', J), (161, 164, 'DANN ZEIG ICH DIR', J), (165, 168, 'WAS ER IN SEINER', J), (169, 170, '*LETZTEN NACHT*', J), (171, 172, 'GESEHEN HAT', J)],
]
# zusätzliche Stille (Sekunden) VOR diesem Wort – mehr Spannung vor "Teil 2"
EXTRA_PAUSE = {0: 0.9, 39: 0.3, 53: 0.2, 78: 0.4, 94: 0.6, 110: 0.4, 126: 0.4, 132: 0.6, 146: 0.6, 159: 0.3}


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
json.dump([[w[0], round(w[1], 3), round(w[2], 3)] for w in words], open(f'{OUT}/words_final.json', 'w'), ensure_ascii=False)
print('Dauer', round(end_t, 2))
