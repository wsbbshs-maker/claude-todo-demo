#!/usr/bin/env python3
"""Premix voice + music bed to the measured reference loudness (ffmpeg only).

  python3 master_audio.py voice.wav music.wav mix.wav [--tighten] [--bed-db 7]

Targets (reference measurements): -14 LUFS integrated, LRA ~2.4 LU, bed 5-10 dB under speech,
voice from frame 1-4 (leading silence trimmed to 20 ms), almost no pauses.

Steps
 1 voice: (optional --tighten) pauses > 0.18 s shortened to 0.08 s; highpass 80 Hz; compressor
   4:1 at -24 dB -> small loudness range; normalised to -15 LUFS (two-pass, linear).
   Run --tighten BEFORE the visuals are timed: it changes every word timestamp after a pause.
 2 music: normalised to (-15 - bed_db) LUFS, light sidechain ducking under the voice.
 3 mix, then final two-pass loudnorm to -14 LUFS / -1 dBTP, and a report of I / LRA / TP.
Put the result into Remotion as ONE <Audio> at volume 1, starting at frame 1.
"""
import argparse
import json
import re
import subprocess
import tempfile
from pathlib import Path


def ff(*args):
    return subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-y", *args], capture_output=True, text=True, check=True)


def loudnorm_two_pass(src, dst, I, TP=-1.0, LRA=4.0, pre=""):
    chain = (pre + "," if pre else "")
    r = ff("-i", src, "-af", f"{chain}loudnorm=I={I}:TP={TP}:LRA={LRA}:print_format=json", "-f", "null", "-")
    m = json.loads(re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr, re.S).group(0))
    ff("-i", src, "-af",
       f"{chain}loudnorm=I={I}:TP={TP}:LRA={LRA}:measured_I={m['input_i']}:measured_TP={m['input_tp']}"
       f":measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true",
       "-ar", "48000", dst)


def ebur128(path):
    r = ff("-i", path, "-af", "ebur128=peak=true", "-f", "null", "-")
    s = r.stderr[r.stderr.rfind("Summary:"):]
    get = lambda k: float(re.search(k + r":\s+(-?[\d.]+)", s).group(1))
    return {"I": get("I"), "LRA": get("LRA"), "TP": get("Peak")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("voice")
    ap.add_argument("music")
    ap.add_argument("out")
    ap.add_argument("--tighten", action="store_true", help="shorten pauses (do this before timing the edit)")
    ap.add_argument("--bed-db", type=float, default=7.0, help="music level under speech (5-10)")
    a = ap.parse_args()

    with tempfile.TemporaryDirectory() as t:
        t = Path(t)
        pre = []
        # leading silence -> 20 ms, so the first word lands on frame 1-2
        trim = "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.02"
        if a.tighten:
            trim += ":stop_periods=-1:stop_duration=0.18:stop_threshold=-45dB:stop_silence=0.08"
        pre.append(trim)
        pre.append("highpass=f=80")
        pre.append("acompressor=threshold=-24dB:ratio=4:attack=5:release=80:makeup=2")
        loudnorm_two_pass(a.voice, str(t / "v.wav"), I=-15, LRA=3, pre=",".join(pre))
        loudnorm_two_pass(a.music, str(t / "m.wav"), I=-15 - a.bed_db, LRA=6)
        ff("-i", str(t / "v.wav"), "-i", str(t / "m.wav"), "-filter_complex",
           "[1:a][0:a]sidechaincompress=threshold=0.06:ratio=3:attack=20:release=250[duck];"
           "[0:a][duck]amix=inputs=2:duration=first:normalize=0[mix]",
           "-map", "[mix]", "-ar", "48000", str(t / "mix.wav"))
        loudnorm_two_pass(str(t / "mix.wav"), a.out, I=-14, TP=-1.0, LRA=4)
        print("voice  ", ebur128(str(t / "v.wav")))
        print("music  ", ebur128(str(t / "m.wav")))
    print("final  ", ebur128(a.out), " target I=-14 LRA~2.4 TP<=-1")


if __name__ == "__main__":
    main()
