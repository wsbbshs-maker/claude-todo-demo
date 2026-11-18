"""Synthetisiert die Soundeffekt-Spur passend zu schedule.json.
Aufruf: python3 sfx.py schedule.json out.wav"""
import json, sys, wave
import numpy as np

SR = 48000
rng = np.random.default_rng(7)
sched = json.load(open(sys.argv[1]))
DUR = sched['duration'] + 0.5
N = int(DUR * SR)
L = np.zeros(N); R = np.zeros(N)


def t_(d): return np.arange(int(d * SR)) / SR
def env(n, a=0.005, r=0.1):
    e = np.ones(n); ai = max(1, int(a * SR)); ri = max(1, int(r * SR))
    e[:ai] = np.linspace(0, 1, ai); e[-ri:] *= np.linspace(1, 0, ri); return e
def onepole_lp(x, fc):
    a = np.exp(-2 * np.pi * fc / SR); y = np.empty_like(x); s = 0.0
    for i in range(len(x)): s = (1 - a) * x[i] + a * s; y[i] = s
    return y
def bandnoise(d, lo, hi):
    n = int(d * SR); X = np.fft.rfft(rng.standard_normal(n)); f = np.fft.rfftfreq(n, 1 / SR)
    X[(f < lo) | (f > hi)] = 0; y = np.fft.irfft(X, n); return y / (np.abs(y).max() + 1e-9)
def add(sig, at, gain=1.0, pan=0.0):
    i = int(at * SR); j = min(N, i + len(sig)); s = sig[:j - i] * gain
    L[i:j] += s * (1 - max(0, pan)); R[i:j] += s * (1 + min(0, pan))
def echo(x, delay=0.18, fb=0.45, n=5):
    out = np.concatenate([x, np.zeros(int(delay * SR * n))])
    for k in range(1, n + 1):
        d = int(delay * SR * k); out[d:d + len(x)] += x * fb ** k
    return out

# --- Klangbausteine ---
def whoosh(d=0.45):
    n = int(d * SR); x = bandnoise(d, 300, 6000); f = np.linspace(0, 1, n)
    return x * np.sin(np.pi * f) ** 2 * 0.6
def hit(freq=50, d=2.5):
    t = t_(d); f = freq * (1 + 1.5 * np.exp(-t * 18))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.2)
    x += bandnoise(d, 80, 2000) * np.exp(-t * 25) * 0.5
    return np.tanh(x * 1.8) * 0.9
def blip():
    t = t_(0.18); return (np.sin(2 * np.pi * 1320 * t) + 0.5 * np.sin(2 * np.pi * 1980 * t)) * np.exp(-t * 25) * 0.35
def static(d, lo=1500, hi=9000):
    x = bandnoise(d, lo, hi); n = len(x)
    gate = np.repeat(rng.uniform(0.3, 1, int(d * 40) + 1), SR // 40)[:n]
    return x * gate * env(n, 0.02, 0.1)
def squelch():
    c = bandnoise(0.06, 500, 6000) * np.exp(-t_(0.06) * 60)
    s = bandnoise(0.35, 800, 4000) * env(int(0.35 * SR), 0.005, 0.15)
    return np.concatenate([c, s * 0.7])
def footstep():
    t = t_(0.12); x = bandnoise(0.12, 80, 1800) * np.exp(-t * 45) + np.sin(2 * np.pi * 70 * t) * np.exp(-t * 35)
    return echo(x * 0.8, 0.16, 0.4, 4)
def heartbeat():
    def thump(): t = t_(0.18); return np.sin(2 * np.pi * 55 * t) * np.exp(-t * 22) + bandnoise(0.18, 40, 300) * np.exp(-t * 40) * 0.3
    return np.concatenate([thump(), np.zeros(int(0.12 * SR)), thump() * 0.7])
def buzz(d, f0=120, flick=False):
    t = t_(d); x = sum(np.sin(2 * np.pi * f0 * k * t) / k for k in range(1, 9))
    if flick:
        g = np.repeat(rng.choice([1, 1, 1, 0.1], int(d * 9) + 1), SR // 9)[:len(t)]; x *= g
    return x / np.abs(x).max() * env(len(t), 0.05, 0.2)
def riser(d):
    t = t_(d); f = 200 + 1400 * (t / d) ** 2
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.3 + bandnoise(d, 2000, 8000) * 0.4 * (t / d)
    return x * (t / d) ** 1.5
def dissonance(d):
    t = t_(d); x = sum(np.sin(2 * np.pi * f * t) for f in (311, 330, 466, 494)) / 4
    return x * env(len(t), 0.02, 1.0) * (1 + 0.3 * np.sin(2 * np.pi * 7 * t))


# --- Teil 2: zusätzliche Klangbausteine ---
def musicbox(d, start_note=0):
    notes=[76,74,72,71,72,74,67,0,76,74,72,71,69,0,71,72]  # schräge Moll-Spieluhr (MIDI)
    out=np.zeros(int(d*SR)); step=0.42; i=start_note; k=0
    while k*step<d-0.3:
        n=notes[i%len(notes)]; i+=1
        if n:
            f=440*2**((n-69)/12)*(1+0.012*np.sin(k)); tt=t_(1.2)
            tone=(np.sin(2*np.pi*f*tt)+0.3*np.sin(2*np.pi*2.01*f*tt))*np.exp(-tt*4.5)
            a=int(k*step*SR); b=min(len(out),a+len(tone)); out[a:b]+=tone[:b-a]
        k+=1
    return out*0.5
def squeak(d=0.35, f0=900):
    tt=t_(d); f=f0+300*np.sin(2*np.pi*3*tt)
    return np.sin(2*np.pi*np.cumsum(f)/SR)*env(len(tt),0.02,0.1)*0.5
def breath(d):
    out=np.zeros(int(d*SR)); k=0.0
    while k<d-0.3:
        b=bandnoise(0.28,400,3000)*np.sin(np.linspace(0,np.pi,int(0.28*SR)))**2
        a=int(k*SR); out[a:a+len(b)]+=b[:len(out)-a]; k+=0.42
    return out*0.35
def clunk():
    tt=t_(0.5); return (np.sin(2*np.pi*90*tt)*np.exp(-tt*14)+bandnoise(0.5,200,3000)*np.exp(-tt*30)*.5)
def click():
    tt=t_(0.05); return bandnoise(0.05,1000,8000)*np.exp(-tt*120)

# --- Grundatmosphäre (auch auf Handylautsprechern hörbar) ---
t = np.arange(N) / SR
pad = (np.sin(2 * np.pi * 55 * t) * 0.5 + np.sin(2 * np.pi * 110 * t) * 0.35 + np.sin(2 * np.pi * 164.8 * t) * 0.18)
pad *= 0.6 + 0.4 * np.sin(2 * np.pi * 0.07 * t)
wind = onepole_lp(rng.standard_normal(N), 900); wind /= np.abs(wind).max()
L += pad * 0.10 + wind * 0.10; R += pad * 0.10 + np.roll(wind, 3000) * 0.10

# --- Szenenbezogene Effekte ---
segs = sched['segs']
for i, s in enumerate(segs):
    a, b, d = s['start'], s['end'], s['end'] - s['start']
    if i > 0: add(whoosh(), a - 0.2, 0.55)
    sc = s['scene']
    if sc == 'monitorWall':
        add(buzz(d, 60), a, 0.07); add(static(d), a, 0.10)
        for k in range(6): add(static(0.12, 800, 9000), a + 0.6 + k * 1.1 + rng.uniform(0, .3), 0.35, rng.uniform(-.5, .5))
    elif sc in ('tunnel', 'tunnelWalk'):
        add(buzz(d, 120, flick=(sc == 'tunnelWalk')), a, 0.06)
        if sc == 'tunnelWalk':
            k = 0.2
            while k < d - 0.2:
                add(footstep(), a + k, 0.55, 0.15 if int(k / 0.449) % 2 else -0.15); k += 0.449
    elif sc == 'cam':
        add(static(d, 2000, 9000), a, 0.13); add(buzz(d, 60), a, 0.05)
        if s['jump']:
            add(blip(), a + 0.5, 0.9); add(hit(65, 1.5), a + 0.5, 0.55)
    elif sc == 'radio':
        g = 1.3 if s['red'] else 1.0
        add(squelch(), a + 0.05, 0.6 * g)
        add(static(d - 0.2, 600, 4000), a + 0.3, 0.11 * g)
        add(squelch(), b - 0.5, 0.45 * g)
        if s['red']: add(riser(d), a, 0.55)
    elif sc == 'face':
        k = 0.1; rate = 0.95
        while k < d:
            add(heartbeat(), a + k, 0.75 + 0.3 * k / d); k += rate; rate *= 0.95
    elif sc == 'balloon':
        add(musicbox(d+1), a, 0.35)
        k=0.3
        while k<d-0.3: add(squeak(0.25,1100+rng.uniform(-150,150)), a+k, 0.18, rng.uniform(-.6,.6)); k+=rng.uniform(0.8,1.4)
    elif sc == 'clownReveal':
        add(hit(48,3.0), a+0.05, 0.9); add(musicbox(d, 4), a+0.3, 0.3); add(dissonance(d), a, 0.12)
        add(squeak(0.3,500), a+d*0.7, 0.4); add(squeak(0.3,450), a+d*0.85, 0.4)
    elif sc == 'newspaper':
        add(bandnoise(0.6,1500,8000)*env(int(0.6*SR),0.05,0.3), a, 0.35); add(musicbox(d, 8), a, 0.18)
    elif sc == 'run':
        k=0.0
        while k<d: add(footstep(), a+k, 0.7, 0.2 if int(k/0.24)%2 else -0.2); k+=0.24
        add(breath(d), a, 0.8); add(hit(55,1.2), a, 0.6)
        k=0.1
        while k<d: add(squeak(0.18,600), a+k, 0.22, 0.1); k+=0.48
    elif sc == 'beam':
        k=0.0
        while k<d: add(footstep(), a+k, 0.45, -0.15 if int(k/0.4)%2 else 0.15); k+=0.4
        add(breath(d), a, 0.45)
        if s.get('lampsOut'):
            ts=np.linspace(0,1,400); e=ts*ts*(3-2*ts)
            for i in range(2,14):
                kk=ts[np.searchsorted(e,(i-1)/12.5)] if (i-1)/12.5<1 else None
                if kk is not None: add(clunk(), a+kk*d, 0.5, rng.uniform(-.3,.3))
        if s.get('flicker'):
            for k in np.arange(0, d, 0.12):
                if rng.random()<0.45: add(click(), a+k, 0.6)
            add(buzz(d,120,flick=True), a, 0.1)
        if s.get('exit'): add(musicbox(d, 2), a, 0.15)
    elif sc == 'two':
        add(hit(40,3.5), s.get('reveal',a+d*0.45), 1.0); add(dissonance(d*0.6), s.get('reveal',a+d*0.45), 0.22); add(musicbox(d*0.6, 0), s.get('reveal',a+d*0.45), 0.35)
    elif sc == 'behind':
        add(hit(42, 3.5), a, 1.0); add(dissonance(d + 0.5), a, 0.18); add(static(d, 1000, 9000), a, 0.12)
    elif sc == 'end':
        add(hit(38, 2.5), a + 0.05, 0.8)

# Ausklang & Normalisierung
fade = int(1.5 * SR); L[-fade:] *= np.linspace(1, 0, fade); R[-fade:] *= np.linspace(1, 0, fade)
m = max(np.abs(L).max(), np.abs(R).max()); L, R = L / m * 0.89, R / m * 0.89
out = (np.stack([L, R], 1) * 32767).astype('<i2')
w = wave.open(sys.argv[2], 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(out.tobytes()); w.close()
print('ok', DUR)
