// Camera timing helpers for Remotion (story.ts CAMS), derived from the measured reference moves:
//  - camera holds ~80 % of frames (< 0.5 px/frame at 720 px = < 0.75 px/frame at 1080 px)
//  - moves are ease-out bursts: PEAK speed on the FIRST frame, then decay.
//    Measured example (720p px/frame): 6, 26, 12, 14, 6, 5, 2, 1
//    -> log-linear fit: speed ratio 0.60 per frame (tau ~1.95 frames), ~36-40 % of the whole move
//       happens in the first frame, 79 % after 3 frames, 96 % after 6, done after ~10.
//  - no ease-in. A burst starts at full speed (reads as a "snap" to the next subject).

import { Easing, interpolate } from "remotion";

export const BURST_RATIO = 0.6; // per-frame speed decay (fit to the measured move)
export const BURST_FRAMES = 10;

/** 0..1 progress of a camera burst that starts at `start` (frame `start` already moves 40 %). */
export function burst(frame: number, start: number, frames = BURST_FRAMES, ratio = BURST_RATIO): number {
  if (frame < start) return 0;
  const n = frame - start + 1;
  return Math.min(1, (1 - ratio ** n) / (1 - ratio ** frames));
}

/** Same feel with Remotion's own easing (ratio 0.587/frame over 13 frames; close enough). */
export const burstInterp = (frame: number, start: number, from: number, to: number) =>
  interpolate(frame, [start - 1, start + 12], [from, to], {
    easing: Easing.out(Easing.exp),
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

/**
 * Slow push-in while the camera "holds". Returns an fov multiplier (1 -> 1 - amount).
 * Keep the edge drift under the hold threshold: amount/frames < 0.75 / (outputHeight / 2).
 * At 1080x1920: amount <= 0.00078 * frames, e.g. 4-6 % over a 3 s (90 frame) hold.
 */
export function pushIn(frame: number, start: number, end: number, amount = 0.05): number {
  const maxAmount = (0.75 / 960) * (end - start);
  const a = Math.min(amount, maxAmount);
  const t = Math.min(1, Math.max(0, (frame - start) / (end - start)));
  return 1 - a * t;
}

/**
 * Dutch tilt (camera roll, radians) for drama/falls: snaps in with a burst, eases back out.
 * Angle is a starting value (not measured): 8 deg for "something is wrong", 12-15 deg for the fall.
 */
export function dutch(frame: number, start: number, end: number, deg = 10): number {
  const inP = burst(frame, start);
  const outP = frame >= end ? burst(frame, end, 14) : 0;
  return ((deg * Math.PI) / 180) * (inP - outP);
}

/** 4-frame white flash (impact, bolt snaps). Opacity per frame, starting values. */
export function flash(frame: number, at: number): number {
  const seq = [0.85, 0.55, 0.25, 0.08];
  const i = frame - at;
  return i >= 0 && i < seq.length ? seq[i] : 0;
}

/** 6-8 frame crossfade when the PLACE changes: opacity of the incoming Sequence. */
export function dissolve(frame: number, start: number, frames = 7): number {
  return Math.min(1, Math.max(0, (frame - start + 1) / frames));
}

/**
 * Whip pan: screen-space velocity (uv units per frame) of the scene centre, for a directional
 * motion-blur effect (see whip-blur-effect.ts). Feed it the camera at frame-1 and frame.
 */
export function screenVelocity(
  project: (frame: number) => { x: number; y: number }, // NDC of a fixed world point (e.g. old look-at target)
  frame: number,
): { x: number; y: number } {
  const a = project(frame - 1);
  const b = project(frame);
  return { x: (b.x - a.x) * 0.5, y: (b.y - a.y) * 0.5 }; // NDC -> uv
}
