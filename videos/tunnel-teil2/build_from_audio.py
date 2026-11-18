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
    [(0, 1, 'DANN *SCHWEBT*', J), (2, 3, 'EIN *ROTER*', J), (4, 4, '*LUFTBALLON*', J), (5, 7, 'AN MIR VORBEI', J)],
    [(8, 10, 'ICH DREHE MICH', J), (11, 12, '*DOCH* UM', J), (13, 14, 'EIN *CLOWN*', J), (15, 16, 'WEISSES *GRINSEN*', J), (17, 18, 'RIESIGE *SCHUHE*', J)],
    [(19, 19, 'OKAY', J), (20, 22, 'ICH BIN *COOKED*', J)],
    [(23, 25, 'ICH *KENNE* IHN', J), (26, 28, 'AUS DER *ZEITUNG*', J), (29, 29, '*1994*', J), (30, 31, 'WURDE HIER', J), (32, 33, 'EIN *ZIRKUSWAGEN*', J), (34, 34, '*VERSCHÜTTET*', J), (35, 36, 'DER CLOWN', J), (37, 39, 'WURDE *NIE GEFUNDEN*', J)],
    [(40, 41, 'ICH *RENNE*', J)],
    [(42, 45, 'MEHMET *SCHREIT*', J), (46, 47, '*DIGGA*, LAUF!', M), (48, 48, '*NOTAUSGANG*', M), (49, 50, '*800 METER*', M), (51, 54, 'UND SCHAU *IHN AN*', M), (55, 56, 'SOLANGE DU', M), (57, 58, 'IHN *ANSIEHST*', M), (59, 62, 'BEWEGT ER SICH *NICHT*', M)],
    [(63, 65, 'ALSO RENNE ICH', J), (66, 66, '*RÜCKWÄRTS*', J), (67, 67, '*TASCHENLAMPE*', J), (68, 69, 'AUF IHN', J), (70, 72, 'ER BLEIBT *STEHEN*', J), (73, 74, 'UND *GRINST*', J)],
    [(75, 76, 'HINTER IHM', J), (77, 80, 'GEHEN DIE *LAMPEN AUS*', J), (81, 82, 'EINE NACH', J), (83, 84, 'DER *ANDEREN*', J)],
    [(85, 86, '*200 METER*', J), (87, 87, '*100*', J, (0.0, 0.5)), (87, 87, '*50*', J, (0.5, 1.0))],
    [(88, 89, 'DANN *FLACKERT*', J), (90, 91, 'DIE TASCHENLAMPE', J), (92, 92, '*EINMAL*', J), (93, 93, '*ZWEIMAL*', J)],
    [(94, 95, 'UND DANN', J), (96, 98, '*SPÜRE* ICH ES', J), (99, 100, '*WARMER ATEM*', J), (101, 103, 'IN MEINEM *NACKEN*', J)],
    [(104, 105, 'HINTER MIR', J), (106, 107, 'STEHT *JEMAND*', J), (108, 110, '*KREIDEWEISSES* GESICHT', J), (111, 112, '*SCHWARZE* LIPPEN', J), (113, 114, 'EIN *PANTOMIME*', J)],
    [(115, 116, 'ER SAGT', J), (117, 118, '*KEIN WORT*', J), (119, 121, 'ER LEGT NUR', J), (122, 123, 'DEN *FINGER*', J), (124, 126, 'AUF DIE *LIPPEN*', J)],
    [(127, 128, 'VOR MIR', J), (129, 130, 'DER *CLOWN*', J), (131, 132, 'HINTER MIR', J), (133, 134, 'DER *PANTOMIME*', J), (135, 136, 'ICH MUSS', J), (137, 138, 'HIER *RAUS*', J), (139, 142, 'ABER ICH KANN NUR', J), (143, 144, '*EINEN* ANSCHAUEN', J)],
    [(145, 146, '*TEIL 3*', J), (147, 147, 'MORGEN', J)],
]
# zusätzliche Stille (Sekunden) VOR diesem Wort – mehr Spannung vor "Teil 2"
EXTRA_PAUSE = {145: 1.0, 40: 0.3, 94: 0.4}


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
