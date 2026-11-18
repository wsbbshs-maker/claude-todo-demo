"""Erzeugt das Voiceover mit Piper (Stimme "Thorsten", Deutsch) und berechnet daraus
Szenen-/Untertitel-Timing (timing.js) sowie die Mundöffnung pro Frame.
Aufruf: python voice.py <modell.onnx> <segs.json> <ausgabe-ordner>"""
import json, sys, wave, io
import numpy as np
from piper import PiperVoice, SynthesisConfig

MODEL, SEGS, OUT = sys.argv[1:4]
SR_OUT = 48000
FPS = 30

# Sprechertext je Szene (j = Jonas/Erzähler, m = Mehmet über Funk)
PARTS = [
    [('j', 'Wenn du nachts allein in einem Tunnel arbeitest, gibt es eine Regel: Schau nicht auf Kamera vier.')],
    [('j', 'Ich bin Jonas. Nachtwache im neuen Brandbergtunnel. Noch nicht eröffnet. Niemand darf hier rein.')],
    [('j', 'Um drei Uhr sieben steht auf Kamera vier jemand. Mitten auf der Fahrbahn. Er schaut direkt in die Kamera.')],
    [('j', 'Ich funke Mehmet an, am Nordportal. Er sagt:'), ('m', 'Das Tor ist zu. Hier ist keiner reingekommen.')],
    [('j', 'Ich schaue wieder hin. Er ist näher.')],
    [('j', 'Ich gehe raus in die Röhre. Die Lampen summen. Die Fahrbahn ist leer.')],
    [('j', 'Zurück im Container. Kamera vier. Er steht genau da, wo ich eben stand.')],
    [('j', 'Und jetzt verstehe ich es. Er bewegt sich nur, wenn ich nicht hinsehe.')],
    [('j', 'Dann knackt das Funkgerät. Mehmet flüstert:'), ('m', 'Jonas ... auf meiner Kamera ist er auch. Und er ist schon bei dir.')],
    [('j', 'Ich drehe mich nicht um.')],
    [('j', 'Teil zwei ... morgen.')],
]

voice = PiperVoice.load(MODEL)
SR = voice.config.sample_rate


def synth(text, who):
    cfg = SynthesisConfig(length_scale=1.12 if who == 'j' else 1.2, noise_scale=0.6, noise_w_scale=0.7)
    a = np.concatenate([np.frombuffer(c.audio_int16_bytes, dtype=np.int16) for c in voice.synthesize(text, cfg)]).astype(np.float32) / 32768
    # Stille an den Rändern abschneiden
    env = np.abs(a) > 0.02
    idx = np.where(env)[0]
    a = a[max(0, idx[0] - int(0.03 * SR)): idx[-1] + int(0.06 * SR)]
    # auf 48 kHz
    n = int(len(a) * SR_OUT / SR)
    a = np.interp(np.linspace(0, len(a) - 1, n), np.arange(len(a)), a)
    if who == 'm':
        a = radio(a)
    return a


def radio(a):
    # Funkgerät: Bandpass 350–3200 Hz, leichte Verzerrung, Rauschen
    X = np.fft.rfft(a); f = np.fft.rfftfreq(len(a), 1 / SR_OUT)
    X[(f < 350) | (f > 3200)] = 0
    y = np.fft.irfft(X, len(a))
    y = np.tanh(y * 3.5) / np.tanh(3.5)
    y += np.random.default_rng(1).standard_normal(len(y)) * 0.02
    return y * 0.8


def voiced_map(a):
    """Liefert kumulierte 'gesprochene Zeit' pro Sample (Pausen zählen nicht)."""
    win = int(0.02 * SR_OUT)
    rms = np.sqrt(np.convolve(a ** 2, np.ones(win) / win, 'same'))
    voiced = rms > 0.025
    return np.cumsum(voiced) / SR_OUT


segs = json.load(open(SEGS))
assert len(segs) == len(PARTS)
track = []
cursor = 0.35
timing = []
for si, (seg, parts) in enumerate(zip(segs, PARTS)):
    chunks = seg['chunks']
    seg_start = cursor
    out_chunks = []
    for pi, (who, text) in enumerate(parts):
        a = synth(text, who)
        my_chunks = [c for c in chunks if (c.startswith('M|')) == (who == 'm')]
        vm = voiced_map(a)
        total_v = vm[-1]
        weights = np.array([len(c.replace('M|', '').replace('*', '')) for c in my_chunks], float)
        bounds = np.concatenate([[0], np.cumsum(weights) / weights.sum() * total_v])
        for ci, c in enumerate(my_chunks):
            s_idx = int(np.searchsorted(vm, bounds[ci] + 1e-6))
            e_idx = int(np.searchsorted(vm, bounds[ci + 1] - 1e-6))
            out_chunks.append({'text': c.replace('M|', ''), 'speaker': 'mehmet' if who == 'm' else 'jonas',
                               'start': round(cursor + s_idx / SR_OUT, 3), 'end': round(cursor + e_idx / SR_OUT + 0.05, 3)})
        track.append((cursor, a))
        cursor += len(a) / SR_OUT + (0.35 if pi < len(parts) - 1 else 0)
    cursor += max(0.4, seg['tail'])
    timing.append({'start': round(seg_start - (0.0 if si == 0 else 0.15), 3), 'chunks': out_chunks})
# Szenengrenzen: jede Szene endet, wo die nächste beginnt
for i in range(len(timing)):
    timing[i]['end'] = timing[i + 1]['start'] if i + 1 < len(timing) else round(cursor, 3)
timing[0]['start'] = 0.0
duration = cursor

# Gesamtspur
N = int((duration + 0.5) * SR_OUT)
mix = np.zeros(N)
for start, a in track:
    i = int(start * SR_OUT); mix[i:i + len(a)] += a
mix = mix / (np.abs(mix).max() + 1e-9) * 0.95
pcm = (mix * 32767).astype('<i2')
with wave.open(f'{OUT}/voice.wav', 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR_OUT); w.writeframes(pcm.tobytes())

# Mundöffnung pro Frame (Lautstärke-Hüllkurve)
spf = SR_OUT // FPS
frames = int(duration * FPS) + 1
mouth = []
for f in range(frames):
    seg = mix[f * spf:(f + 1) * spf]
    mouth.append(float(np.sqrt(np.mean(seg ** 2))) if len(seg) else 0.0)
mouth = np.array(mouth); mouth = np.clip(mouth / (np.percentile(mouth[mouth > 0.01], 90) + 1e-9), 0, 1)
mouth[mouth < 0.12] = 0

with open(f'{OUT}/timing.js', 'w') as fh:
    fh.write('// automatisch erzeugt von voice.py\n')
    fh.write('var TIMING=' + json.dumps({'duration': round(duration, 3), 'segs': timing}) + ';\n')
    fh.write('var MOUTH=' + json.dumps([round(float(x), 2) for x in mouth]) + ';\n')
    fh.write("if(typeof module!=='undefined')module.exports={TIMING,MOUTH};\n")
print('Dauer', round(duration, 2), 's')
