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


# --- Flugsaurier: Klangbausteine ---
def propeller(d, f0=205):
    tt=t_(d); f=f0*(1+0.02*np.sin(2*np.pi*0.7*tt)); ph=2*np.pi*np.cumsum(f)/SR
    x=sum(np.sin(k*ph)/k for k in range(1,7))*0.5+bandnoise(d,300,2500)*0.25
    return x/np.abs(x).max()*env(len(tt),0.2,0.3)
def knock():
    tt=t_(0.18); return (np.sin(2*np.pi*950*tt)*np.exp(-tt*55)+bandnoise(0.18,500,4500)*np.exp(-tt*90)*0.8+np.sin(2*np.pi*180*tt)*np.exp(-tt*40)*0.6)
def doorknock():
    tt=t_(0.3); return (np.sin(2*np.pi*170*tt)*np.exp(-tt*28)+np.sin(2*np.pi*520*tt)*np.exp(-tt*45)*0.6+bandnoise(0.3,200,2500)*np.exp(-tt*70)*0.7)
def screech(d=1.1, base=900):
    tt=t_(d); f=base+500*np.sin(np.pi*tt/d)-250*(tt/d)+60*np.sin(2*np.pi*31*tt)
    ph=2*np.pi*np.cumsum(f)/SR; x=np.sign(np.sin(ph))*0.5+np.sin(2*ph)*0.4
    x=x*(0.7+0.3*bandnoise(d,50,400)); X=np.fft.rfft(x); fr=np.fft.rfftfreq(len(x),1/SR); X[(fr<500)|(fr>6000)]=0
    y=np.fft.irfft(X,len(x)); y=np.tanh(y/np.abs(y).max()*2.2)
    return y*env(len(tt),0.04,0.35)*0.6
def wingflap():
    tt=t_(0.4); return bandnoise(0.4,60,700)*np.sin(np.linspace(0,np.pi,len(tt)))**2*1.2
def beepE():
    out=np.zeros(int(0.3*SR))
    for s0 in (0,0.14):
        tt=t_(0.08); b=np.sin(2*np.pi*2700*tt)*env(len(tt),0.005,0.01); i=int(s0*SR); out[i:i+len(b)]+=b
    return out*0.6
def beepC():
    out=np.zeros(int(0.32*SR))
    for s0 in (0,0.15):
        tt=t_(0.1); f=2550+90*np.sin(2*np.pi*23*tt); b=np.sin(2*np.pi*np.cumsum(f)/SR)*env(len(tt),0.01,0.02)*(0.75+0.25*bandnoise(0.1,100,900))
        i=int(s0*SR); out[i:i+len(b)]+=b
    return out*0.6
def clack():
    tt=t_(0.25); return bandnoise(0.25,1500,7000)*np.exp(-tt*70)+np.sin(2*np.pi*90*tt)*np.exp(-tt*25)*0.8
def tap():
    tt=t_(0.04); return np.sin(2*np.pi*1800*tt)*np.exp(-tt*150)*0.6
def ping():
    tt=t_(0.6); return (np.sin(2*np.pi*1320*tt)+0.6*np.sin(2*np.pi*1980*tt))*np.exp(-tt*7)*0.35
def vibrate():
    tt=t_(0.35); return np.sign(np.sin(2*np.pi*165*tt))*env(len(tt),0.01,0.05)*0.25*(0.6+0.4*np.sin(2*np.pi*20*tt))
def creak(d=1.0):
    tt=t_(d); f=320+60*np.sin(2*np.pi*1.5*tt)+30*bandnoise(d,1,20); ph=2*np.pi*np.cumsum(f)/SR
    x=np.sign(np.sin(ph))*(0.5+0.5*np.abs(np.sin(2*np.pi*9*tt)))
    X=np.fft.rfft(x); fr=np.fft.rfftfreq(len(x),1/SR); X[(fr<300)|(fr>3000)]=0; y=np.fft.irfft(X,len(x))
    return y/np.abs(y).max()*env(len(tt),0.1,0.3)*0.4
def crickets(d):
    out=np.zeros(int(d*SR)); k=0.0
    while k<d-0.2:
        tt=t_(0.12); c=np.sin(2*np.pi*4600*tt)*(0.5+0.5*np.sign(np.sin(2*np.pi*55*tt)))*env(len(tt),0.01,0.03)
        i=int(k*SR); out[i:i+len(c)]+=c[:len(out)-i]; k+=rng.uniform(0.25,0.6)
    return out*0.25
def jungle(d):
    out=bandnoise(d,5000,8500)*(0.5+0.5*np.sin(2*np.pi*18*t_(d)))*0.12; k=0.2
    while k<d-0.3:
        tt=t_(0.18); f=np.linspace(rng.uniform(2200,3200),rng.uniform(3200,4200),len(tt)); b=np.sin(2*np.pi*np.cumsum(f)/SR)*env(len(tt),0.01,0.06)
        i=int(k*SR); out[i:i+len(b)]+=b[:len(out)-i]*0.3; k+=rng.uniform(0.3,0.9)
    return out
def wetblink():
    tt=t_(0.45); f=np.linspace(900,250,len(tt)); x=bandnoise(0.45,200,2500)*np.sin(np.linspace(0,np.pi,len(tt)))**2
    return (x*0.7+np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-tt*8)*0.4)*0.8
def growl(d):
    tt=t_(d); f=70+12*np.sin(2*np.pi*3*tt); x=np.sign(np.sin(2*np.pi*np.cumsum(f)/SR))*(0.6+0.4*bandnoise(d,20,200))
    X=np.fft.rfft(x); fr=np.fft.rfftfreq(len(x),1/SR); X[fr>700]=0; y=np.fft.irfft(X,len(x))
    return y/np.abs(y).max()*env(len(tt),0.3,0.4)*0.5


# --- Puppeninsel: Klangbausteine ---
def bandkeep(x, bands):
    X=np.fft.rfft(x); f=np.fft.rfftfreq(len(x),1/SR); m=np.zeros_like(f)
    for lo,hi,g in bands: m[(f>=lo)&(f<=hi)]+=g
    return np.fft.irfft(X*m,len(x))
def mama(pitch=1.0):
    out=[]
    for (f0,f1,d) in ((380,330,0.26),(345,290,0.36)):
        tt=t_(d); f=np.linspace(f0,f1,len(tt))*pitch*(1+0.03*np.sin(2*np.pi*6*tt)); ph=2*np.pi*np.cumsum(f)/SR
        src=sum(np.sin(k*ph)/k for k in range(1,14))
        v=bandkeep(src,[(550,950,1.0),(1050,1450,0.8),(2300,2900,0.35)])
        e=env(len(tt),0.05,0.08); e[:int(0.05*SR)]*=np.linspace(0.2,1,int(0.05*SR))
        out+= [v/np.abs(v).max()*e, np.zeros(int(0.09*SR))]
    y=np.concatenate(out); y+=bandnoise(len(y)/SR,2000,6000)*0.05
    return np.tanh(y*1.6)*0.6
def waterlap(d):
    tt=t_(d); x=onepole_lp(rng.standard_normal(len(tt)),500); x/=np.abs(x).max()
    return x*(0.55+0.45*np.sin(2*np.pi*0.35*tt+1))**2*0.6
def drip():
    tt=t_(0.25); f=np.linspace(1500,700,len(tt)); return np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-tt*25)*0.5
def frogs(d):
    out=np.zeros(int(d*SR)); k=0.1
    while k<d-0.3:
        tt=t_(0.22); f0=rng.uniform(110,190); c=np.sign(np.sin(2*np.pi*f0*tt))*(0.5+0.5*np.sign(np.sin(2*np.pi*24*tt)))*env(len(tt),0.01,0.05)
        c=bandkeep(c,[(80,900,1.0)]); i=int(k*SR); out[i:i+len(c)]+=c[:len(out)-i]*0.35; k+=rng.uniform(0.4,1.1)
    return out
def whispers(d):
    out=np.zeros(int(d*SR)); k=0.0
    while k<d-0.4:
        w=rng.uniform(0.4,0.9); tt=t_(w); x=bandnoise(w,1800,7000)*(0.5+0.5*np.sin(2*np.pi*rng.uniform(5,8)*tt))**2*env(len(tt),0.08,0.15)
        i=int(k*SR); out[i:i+len(x)]+=x[:len(out)-i]*0.5; k+=rng.uniform(0.2,0.5)
    return out
def glasstick():
    tt=t_(0.12); return (np.sin(2*np.pi*3400*tt)+0.5*np.sin(2*np.pi*5200*tt))*np.exp(-tt*55)*0.5
def clocktick(d,step=0.12):
    out=np.zeros(int(d*SR)); k=0.0
    while k<d-0.05:
        tt=t_(0.03); c=bandnoise(0.03,2000,7000)*np.exp(-tt*200); i=int(k*SR); out[i:i+len(c)]+=c[:len(out)-i]*0.6; k+=step; step=max(0.05,step*0.985)
    return out
def birds(d):
    out=np.zeros(int(d*SR)); k=0.1
    while k<d-0.3:
        n=rng.integers(2,5)
        for j in range(n):
            tt=t_(0.09); f=np.linspace(rng.uniform(2600,3600),rng.uniform(3600,4800),len(tt)); b=np.sin(2*np.pi*np.cumsum(f)/SR)*env(len(tt),0.01,0.03)
            i=int((k+j*0.12)*SR); out[i:i+len(b)]+=b[:max(0,len(out)-i)]*0.25
        k+=rng.uniform(0.6,1.4)
    return out


# --- Echtes Flüstern aus der Sprachaufnahme (Zufallsphase = gehauchte Stimme) ---
VOICE=None; WORDS=None
if len(sys.argv)>4:
    with wave.open(sys.argv[3]) as w_: VOICE=np.frombuffer(w_.readframes(w_.getnframes()),'<i2').astype(np.float64)/32767
    WORDS=json.load(open(sys.argv[4]))
def whisperize(x, stretch=1.3, n=1024, hop=256):
    if len(x)<n+2*hop: x=np.concatenate([x,np.zeros(n+2*hop-len(x))])
    win=np.hanning(n); fr=[np.fft.rfft(x[i:i+n]*win) for i in range(0,len(x)-n,hop)]
    mag=np.abs(np.array(fr)); ker=np.ones(9)/9
    mag=np.array([np.convolve(m,ker,'same') for m in mag])
    ho=int(hop*stretch); y=np.zeros(ho*len(mag)+n); ws=np.zeros_like(y)
    for i,m in enumerate(mag):
        ph=np.exp(1j*rng.uniform(0,2*np.pi,len(m))); y[i*ho:i*ho+n]+=np.fft.irfft(m*ph,n)*win; ws[i*ho:i*ho+n]+=win**2
    y/=np.maximum(ws,1e-2); y=bandkeep(y,[(350,9500,1.0),(2000,6000,0.6)])
    y*=env(len(y),0.03,0.12)
    return y/(np.abs(y).max()+1e-9)
def wbank(keys):
    if VOICE is None: return []
    out=[]
    for (w,a_,b_) in WORDS:
        if any(k.lower() in w.lower() for k in keys):
            sg=VOICE[max(0,int((a_-0.05)*SR)):int((b_+0.08)*SR)]
            if len(sg)>3000: out.append(whisperize(sg, stretch=rng.uniform(1.15,1.55)))
    return out
def wphrase(i0,i1,stretch=1.3):
    if VOICE is None: return None
    a_=WORDS[i0][1]; b_=WORDS[i1][2]
    return whisperize(VOICE[max(0,int((a_-0.05)*SR)):int((b_+0.1)*SR)],stretch)
def wscatter(a,d,pool,rate=1.5,gain=0.5,width=0.85):
    if not pool: return
    k=rng.uniform(0,0.4)
    while k<d-0.3:
        w=pool[rng.integers(len(pool))]
        add(echo(w*rng.uniform(0.55,1.0),0.12,0.35,3), a+k, gain, rng.uniform(-width,width)); k+=rng.exponential(1.0/rate)+0.15
POOL_ALL=wbank(['Puppe','Augen','allein','hier','Wasser','Kind','recht','flüstern','Nacht','dich','mir'])

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
    elif sc == 'neck':
        k=0.4
        while k<d-0.5:
            b=bandnoise(1.0,150,1800)*np.sin(np.linspace(0,np.pi,int(1.0*SR)))**3
            add(b, a+k, 0.55, 0.7); k+=1.25
        k=0.1; rate=0.8
        while k<d: add(heartbeat(), a+k, 0.7); k+=rate; rate*=0.96
    elif sc == 'mimeReveal':
        add(hit(45,3.0), a+0.05, 0.95); add(dissonance(d), a, 0.16); add(musicbox(d, 6), a+0.5, 0.2)
    elif sc == 'mimeClose':
        cs_ = s.get('psst', a+d*0.5)
        ps=bandnoise(1.1,2500,9000)*env(int(1.1*SR),0.15,0.6)
        add(ps, cs_, 0.5)
        tt=t_(d); add(np.sin(2*np.pi*1975*tt)*env(len(tt),0.8,0.5)*0.15, a, 1.0)
    elif sc == 'between':
        k=0.0; rate=0.62
        while k<d: add(heartbeat(), a+k, 0.8); k+=rate; rate=max(0.4,rate*0.97)
        k=0.0
        while k<d-0.3: add(whoosh(0.3), a+k, 0.5, 0.6 if int(k/1.15)%2 else -0.6); k+=1.15
        add(musicbox(d, 3), a, 0.22); add(riser(d), a, 0.4)
    elif sc == 'dronePOV':
        add(propeller(d+0.3), a, 0.22)
        for k in (0.12, 0.42, 0.72): add(knock(), k, 1.0)
        add(whoosh(0.9), 0.0, 0.7); add(wingflap(), 0.35, 0.8); add(wingflap(), 0.9, 0.6)
        add(screech(0.7,700), d-1.2, 0.25, 0.5)
    elif sc == 'eyeClose':
        add(whoosh(0.4), a, 0.8); add(propeller(d,190), a, 0.12); add(growl(d), a, 0.5)
        for bt in s.get('blinks',[]): add(wetblink(), bt, 0.9)
    elif sc == 'intro':
        add(jungle(d), a, 1.0); add(propeller(d,230), a, 0.05)
        lt_ = s.get('last', a+d-1.0); add(whoosh(1.0), lt_, 0.9); add(wingflap(), lt_+0.1, 1.0); add(hit(50,1.5), lt_+0.3, 0.5)
    elif sc == 'reveal':
        add(bandnoise(d,200,1500)*env(int(d*SR),0.3,0.3), a, 0.12); add(propeller(d,210), a, 0.14); add(screech(1.2), a+0.25, 0.6, 0.3)
        k=0.0
        while k<d: add(wingflap(), a+k, 0.7); k+=2*np.pi/6.5
    elif sc == 'mimic':
        add(propeller(d,210), a, 0.12); add(bandnoise(d,200,1500)*env(int(d*SR),0.3,0.3), a, 0.08)
        for bt in s.get('dBeeps',[]): add(beepE(), bt, 0.8, -0.4)
        for bt in s.get('pBeeps',[]): add(beepC(), bt, 0.85, 0.4)
    elif sc == 'snap':
        ls=s.get('lunge', a+d*0.6)
        add(propeller(ls-a+0.4,215), a, 0.15); add(growl(ls-a), a, 0.4); add(screech(0.6,1100), ls-0.05, 0.7); add(clack(), ls+0.33, 1.0)
        add(bandnoise(a+d-ls-0.45,300,9000)*env(int((a+d-ls-0.45)*SR),0.005,0.2), ls+0.45, 0.35)
    elif sc == 'phone':
        add(jungle(d), a, 0.5); pt=s.get('post', a+d*0.6)
        add(tap(), pt-0.05, 1.0); add(whoosh(0.5), pt+0.05, 0.4); add(ping(), pt+0.62, 1.0)
        k=pt+1.1
        while k<a+d: add(ping(), k, 0.5, rng.uniform(-.5,.5)); k+=rng.uniform(0.35,0.7)
    elif sc == 'nightDoor':
        add(crickets(d), a, 1.0); add(buzz(d,60), a, 0.03); kn=s.get('knock', a+d*0.3)-0.08
        for k in (0, 0.3, 0.6): add(doorknock(), kn+k, 1.0)
        add(heartbeat(), kn+1.2, 0.6); add(heartbeat(), kn+2.0, 0.6)
    elif sc == 'agents':
        add(creak(1.1), a+0.02, 0.8); add(hit(50,2.0), a+0.1, 0.7); add(buzz(d,50), a, 0.04)
        bt=s.get('badge'); 
        if bt: add(whoosh(0.35), bt-0.1, 0.6); add(hit(60,1.2), bt+0.2, 0.4)
    elif sc == 'agentTalk':
        add(dissonance(d), a, 0.06); k=0.2
        while k<d: add(heartbeat(), a+k, 0.45); k+=0.9
    elif sc == 'viral':
        k=0.0
        while k<d: add(vibrate(), a+k, 1.0); k+=0.55
        k=0.1
        while k<d: add(ping(), a+k, 0.45, rng.uniform(-.6,.6)); k+=max(0.12, 0.45-k*0.07)
        add(riser(d), a, 0.4); st=s.get('standort')
        if st: add(hit(45,1.5), st, 0.7)
    elif sc == 'glasses':
        tt=t_(d); add(np.sin(2*np.pi*1975*tt)*env(len(tt),0.8,0.5)*0.12, a, 1.0)
        lt_=s.get('lift')
        if lt_: add(hit(42,3.0), lt_+0.4, 1.0); add(dissonance(a+d-lt_), lt_+0.4, 0.15); add(growl(a+d-lt_), lt_+0.4, 0.4)
    elif sc == 'agentBlink':
        for bt in s.get('blinks',[]): add(wetblink(), bt, 1.0)
        add(hit(38,3.5), a+0.05, 0.9); add(screech(1.4,650), a+d*0.55, 0.45, -0.3)
    elif sc == 'dollBlink':
        add(mama(), 0.08, 0.95, -0.2); add(creak(0.7), 0.28, 0.35, 0.2)
        pp=wbank(['Puppen'])
        if pp: add(echo(pp[0],0.12,0.35,3), 0.5, 0.35, 0.65)
        add(waterlap(d), a, 0.5); add(frogs(d), a, 0.6)
        add(musicbox(d+1.0, 0), a+0.3, 0.22); c1=s.get('c1')
        if c1: add(hit(48,2.0), c1, 0.6); add(glasstick(), 1.0, 0.5)
    elif sc == 'canal':
        add(waterlap(d), a, 0.6); add(frogs(d), a, 0.7); add(crickets(d), a, 0.6); add(musicbox(d, 4), a, 0.18)
        add(creak(1.0), a+d*0.4, 0.18, -0.6); wscatter(a,d,wbank(['gruseligsten','Welt','Ende']),0.45,0.22)
    elif sc == 'ghostGirl':
        add(waterlap(d), a, 0.5); add(musicbox(d, 8), a, 0.2); k=0.3
        while k<d: add(drip(), a+k, 0.45, rng.uniform(-.4,.4)); k+=rng.uniform(0.35,0.8)
        if VOICE is not None: wscatter(a,d,wbank(['Wasser','Kind','hier']),0.7,0.3)
        else: add(whispers(d), a, 0.12)
    elif sc == 'oldMan':
        add(waterlap(d), a, 0.6); add(frogs(d), a, 0.5); add(creak(0.8), a+0.3, 0.25, -0.4)
        add(bandnoise(0.6,200,2000)*env(int(0.6*SR),0.02,0.4), a+d*0.45, 0.35, 0.4)
    elif sc == 'hangFirst':
        add(creak(1.4), a+0.2, 0.5, 0.3); add(creak(1.0), a+d*0.6, 0.35, 0.3); add(waterlap(d), a, 0.4); add(musicbox(d, 2), a, 0.2)
    elif sc == 'timelapse':
        add(clocktick(d), a, 0.7); add(whoosh(0.8), a, 0.6); add(riser(d), a, 0.3); add(musicbox(d, 6), a, 0.2)
        k=0.2
        while k<d: add(creak(0.3), a+k, 0.12, rng.uniform(-.6,.6)); k+=rng.uniform(0.3,0.6)
    elif sc == 'whisper':
        add(crickets(d), a, 0.4)
        if VOICE is not None: wscatter(a,d,POOL_ALL,3.0,0.85,0.95); wscatter(a+0.2,d,POOL_ALL,1.5,0.6,0.95)
        else: add(whispers(d), a, 0.9)
        k=0.2
        while k<d: add(heartbeat(), a+k, 0.5); k+=0.85
        ws=s.get('wsnap')
        if ws:
            for j in range(7): add(glasstick(), ws+j*0.025, 0.55, rng.uniform(-.7,.7))
            add(hit(44,2.5), ws+0.02, 0.9)
    elif sc == 'watchers':
        add(musicbox(d, 10), a, 0.25); add(dissonance(d), a, 0.06); add(waterlap(d), a, 0.3); add(mama(0.8), a+d-1.0, 0.25, 0.6)
        wscatter(a,d,wbank(['anschaut','dich','Puppe','Zeit']),0.8,0.3)
    elif sc == 'man2001':
        add(waterlap(d), a, 0.7); add(dissonance(d), a, 0.07); k=0.4
        while k<d: add(drip(), a+k, 0.35); k+=rng.uniform(0.6,1.2)
        add(hit(40,3.0), a+0.1, 0.5)
    elif sc == 'notAlone':
        add(musicbox(d+0.5, 12), a, 0.3); add(crickets(d), a, 0.5); add(waterlap(d), a, 0.4)
        wa=wphrase(131,131,1.5)
        if wa is not None: add(echo(wa,0.14,0.4,4), a+d-0.9, 0.45, 0.7)
    elif sc == 'loop':
        k=0.1
        while k<d: add(heartbeat(), a+k, 0.7); k+=0.8
        lr=s.get('lrev')
        if lr:
            add(hit(40,3.2), lr, 1.0); add(mama(0.7), lr+0.15, 0.45); add(dissonance(a+d-lr), lr, 0.15)
            wp=wphrase(143,145,1.35)
            if wp is not None: add(echo(wp,0.13,0.4,4), lr+0.9, 0.5, -0.6); add(echo(wp,0.17,0.35,3), lr+1.05, 0.35, 0.6)
    elif sc == 'placeReveal':
        add(birds(d), a, 1.0); add(waterlap(d), a, 0.5); pn=s.get('pname')
        if pn: add(whoosh(0.6), pn-0.25, 0.6); add(hit(55,1.8), pn, 0.6)
        add(musicbox(d, 0), a, 0.2)
    elif sc == 'follow':
        add(musicbox(d, 3), a, 0.25); add(birds(d), a, 0.4); add(hit(42,3.0), a+d-1.4, 0.8)
        wf=wphrase(159,160,1.4)
        if wf is not None: add(echo(wf,0.14,0.4,4), a+d-2.3, 0.5, -0.7); add(echo(wf,0.14,0.4,4), a+d-1.5, 0.45, 0.7)
        else: add(whispers(d), a, 0.25)
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
