#!/usr/bin/env python3
"""Colour/contrast stats per frame and per clip, compared with the reference targets.

Usage:
  python3 measure_look.py "../../your Remotion project/out/bridge/test/c_*.jpg"
  python3 measure_look.py ../vids/01_*.mp4 --fps 2            # videos: frames via ffmpeg
  python3 measure_look.py a.png b.png --no-mask --per-frame

Definitions (CALIBRATE FIRST: run it on 2-3 reference videos. If the medians land inside the
target ranges below, these are the same definitions the targets were measured with):
  lum  = Rec.709 luma of the display (sRGB-encoded) values, 0..1
  sat  = HSV saturation (max-min)/max, pixel mean
  p2/p98 = 2nd / 98th percentile of lum
The caption band (60-74 % of frame height) is masked unless --no-mask.
Only numpy + PIL (+ ffmpeg for videos).
"""
import argparse
import glob
import subprocess
import sys

import numpy as np
from PIL import Image

TARGETS = {  # per-video medians measured on the 20 reference shorts
    "lum_mean": (0.43, 0.54),
    "lum_std": (0.21, 0.29),
    "p2": (0.03, 0.11),
    "p98": (0.90, 1.00),
    "sat": (0.38, 0.65),
}
W709 = np.array([0.2126, 0.7152, 0.0722], np.float32)


def frame_stats(rgb: np.ndarray, mask_caption: bool) -> dict:
    a = rgb.astype(np.float32) / 255.0
    h = a.shape[0]
    if mask_caption:
        keep = np.ones(h, bool)
        keep[int(h * 0.60): int(h * 0.74)] = False
        a = a[keep]
    px = a.reshape(-1, 3)
    lum = px @ W709
    mx = px.max(1)
    mn = px.min(1)
    sat = np.where(mx > 1e-6, (mx - mn) / np.maximum(mx, 1e-6), 0.0)
    p2, p98 = np.percentile(lum, [2, 98])
    return {
        "lum_mean": float(lum.mean()),
        "lum_std": float(lum.std()),
        "p2": float(p2),
        "p98": float(p98),
        "sat": float(sat.mean()),
    }


def video_frames(path: str, fps: float):
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
         "-of", "csv=p=0", path], capture_output=True, text=True, check=True)
    w, h = map(int, probe.stdout.strip().split(",")[:2])
    proc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-i", path, "-vf", f"fps={fps}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        stdout=subprocess.PIPE)
    n = w * h * 3
    while True:
        buf = proc.stdout.read(n)
        if len(buf) < n:
            break
        yield np.frombuffer(buf, np.uint8).reshape(h, w, 3)
    proc.wait()


def verdict(key: str, v: float) -> str:
    lo, hi = TARGETS[key]
    if v < lo:
        return f"LOW  (-{lo - v:.2f})"
    if v > hi:
        return f"HIGH (+{v - hi:.2f})"
    return "ok"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="+", help="images, globs or videos")
    ap.add_argument("--fps", type=float, default=2.0, help="sampling rate for videos")
    ap.add_argument("--no-mask", action="store_true", help="do not mask the caption band")
    ap.add_argument("--per-frame", action="store_true")
    args = ap.parse_args()

    files = []
    for p in args.inputs:
        files += sorted(glob.glob(p)) or [p]
    vids = [f for f in files if f.lower().endswith((".mp4", ".mov", ".webm", ".mkv"))]
    imgs = [f for f in files if f not in vids]

    groups = {f: list(video_frames(f, args.fps)) for f in vids}
    if imgs:
        groups["images (%d)" % len(imgs)] = [np.asarray(Image.open(f).convert("RGB")) for f in imgs]

    keys = list(TARGETS)
    for name, frames in groups.items():
        if not frames:
            print(f"{name}: no frames", file=sys.stderr)
            continue
        rows = [frame_stats(f, not args.no_mask) for f in frames]
        if args.per_frame:
            src = imgs if name.startswith("images") else [f"{name}#{i}" for i in range(len(rows))]
            for s, r in zip(src, rows):
                print(f"  {s:60s} " + "  ".join(f"{k}={r[k]:.3f}" for k in keys))
        med = {k: float(np.median([r[k] for r in rows])) for k in keys}
        print(f"\n{name}  ({len(rows)} frames, median)")
        print(f"  {'stat':9s} {'value':>6s}   target       verdict")
        for k in keys:
            lo, hi = TARGETS[k]
            print(f"  {k:9s} {med[k]:6.3f}   {lo:.2f}-{hi:.2f}    {verdict(k, med[k])}")


if __name__ == "__main__":
    main()
