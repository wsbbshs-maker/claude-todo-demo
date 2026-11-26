// Final colour grade: black/white point, S-curve contrast, saturation, split toning
// (blue-purple shadows, warm highlights). Goes LAST, after ToneMapping, in Bridge.tsx.
//
// Works in display (sRGB-encoded) values, because the reference targets were measured on
// display pixels: lum mean 0.43-0.54, lum std 0.21-0.29, p2 0.03-0.11, p98 0.90-1.00,
// saturation 0.38-0.65. Input/output stay linear, as postprocessing expects.

import { Effect, BlendFunction } from "postprocessing";
import { Color, Uniform } from "three";

const fragmentShader = /* glsl */ `
uniform float blackPoint;
uniform float whitePoint;
uniform float pivot;
uniform float contrast;
uniform float saturation;
uniform float vibrance;
uniform vec3 shadowTint;
uniform vec3 highlightTint;
uniform float shadowAmount;
uniform float highlightAmount;
uniform float skinProtect;

vec3 encodeSRGB(vec3 c) {
  c = clamp(c, 0.0, 1.0);
  return mix(c * 12.92, 1.055 * pow(c, vec3(1.0 / 2.4)) - 0.055, step(0.0031308, c));
}
vec3 decodeSRGB(vec3 c) {
  return mix(c / 12.92, pow((c + 0.055) / 1.055, vec3(2.4)), step(0.04045, c));
}

void mainImage(const in vec4 inputColor, const in vec2 uv, out vec4 outputColor) {
  const vec3 W = vec3(0.2126, 0.7152, 0.0722);
  vec3 c = encodeSRGB(inputColor.rgb);

  // levels: pull the darkest values down to ink-black, clip the top a bit
  c = clamp((c - blackPoint) / (whitePoint - blackPoint), 0.0, 1.0);

  // S-curve around pivot; 0 and 1 stay fixed, slope at pivot = contrast
  vec3 lo = pivot * pow(c / pivot, vec3(contrast));
  vec3 hi = 1.0 - (1.0 - pivot) * pow((1.0 - c) / (1.0 - pivot), vec3(contrast));
  c = mix(lo, hi, step(pivot, c));

  // saturation + vibrance (vibrance pushes dull colours more than already-strong ones)
  float y = dot(c, W);
  float chroma = max(c.r, max(c.g, c.b)) - min(c.r, min(c.g, c.b));
  float s = saturation * (1.0 + vibrance * (1.0 - chroma));
  // skin protection: the per-channel S-curve already adds saturation; on skin hues (~7-43 deg,
  // mid-light) pull it back so faces stay peach/tan instead of turning orange
  vec3 hsl = RGBToHSL(c);
  float skin = smoothstep(0.0, 0.03, hsl.x) * (1.0 - smoothstep(0.10, 0.14, hsl.x))
             * smoothstep(0.25, 0.4, hsl.z) * (1.0 - smoothstep(0.8, 0.92, hsl.z));
  s = mix(s, 0.7, skin * skinProtect);
  c = clamp(vec3(y) + (c - vec3(y)) * s, 0.0, 1.0);

  // split toning, chroma only (luma of the tint removed, so it does not lift the blacks)
  y = dot(c, W);
  vec3 sT = encodeSRGB(shadowTint);      // Color uniforms are stored linear; compare in display space
  vec3 hT = encodeSRGB(highlightTint);
  vec3 st = sT - vec3(dot(sT, W));
  vec3 ht = hT - vec3(dot(hT, W));
  float ws = 1.0 - smoothstep(0.05, 0.55, y);
  float wh = smoothstep(0.45, 0.95, y);
  c = clamp(c + st * shadowAmount * ws + ht * highlightAmount * wh, 0.0, 1.0);

  outputColor = vec4(decodeSRGB(c), inputColor.a);
}`;

export type GradeOptions = {
  blackPoint?: number;
  whitePoint?: number;
  pivot?: number;
  contrast?: number;
  saturation?: number;
  vibrance?: number;
  shadowTint?: string;
  highlightTint?: string;
  shadowAmount?: number;
  highlightAmount?: number;
  skinProtect?: number;
};

// Starting values. Tune per light state with measure_look.py until the stats land in range.
export const GRADE_DAY: Required<GradeOptions> = {
  blackPoint: 0.05,
  whitePoint: 0.95,
  pivot: 0.45,
  contrast: 1.35,
  saturation: 1.1,
  vibrance: 0.15,
  shadowTint: "#3d3aa8", // blue-purple
  highlightTint: "#ffc070", // warm
  shadowAmount: 0.35,
  highlightAmount: 0.18,
  skinProtect: 0.7,
};
export const GRADE_GOLDEN: Required<GradeOptions> = {
  ...GRADE_DAY,
  pivot: 0.4,
  whitePoint: 0.9,
  contrast: 1.35,
  saturation: 1.0,
  shadowTint: "#4a2f9e",
  highlightTint: "#ff9a40",
  shadowAmount: 0.4,
  highlightAmount: 0.15,
};
export const GRADE_NIGHT: Required<GradeOptions> = {
  ...GRADE_DAY,
  pivot: 0.36,
  contrast: 1.25,
  saturation: 0.85, // night scenes are already one big blue: pull saturation DOWN
  vibrance: 0,
  shadowTint: "#2a3cc0",
  highlightTint: "#ffb060", // window light pools stay warm
  shadowAmount: 0.25,
  highlightAmount: 0.25,
};

export class GradeEffect extends Effect {
  constructor(opts: GradeOptions = {}) {
    const o = { ...GRADE_DAY, ...opts };
    super("GradeEffect", fragmentShader, {
      blendFunction: BlendFunction.SET,
      uniforms: new Map<string, Uniform>([
        ["blackPoint", new Uniform(o.blackPoint)],
        ["whitePoint", new Uniform(o.whitePoint)],
        ["pivot", new Uniform(o.pivot)],
        ["contrast", new Uniform(o.contrast)],
        ["saturation", new Uniform(o.saturation)],
        ["vibrance", new Uniform(o.vibrance)],
        ["shadowTint", new Uniform(new Color(o.shadowTint))],
        ["highlightTint", new Uniform(new Color(o.highlightTint))],
        ["shadowAmount", new Uniform(o.shadowAmount)],
        ["highlightAmount", new Uniform(o.highlightAmount)],
        ["skinProtect", new Uniform(o.skinProtect)],
      ]),
    });
  }

  /** Blend between two presets (e.g. day -> golden over a story beat), t in 0..1. */
  setMix(a: Required<GradeOptions>, b: Required<GradeOptions>, t: number) {
    for (const k of Object.keys(a) as (keyof GradeOptions)[]) {
      const u = this.uniforms.get(k)!;
      if (u.value instanceof Color) {
        (u.value as Color).set(a[k] as string).lerp(new Color(b[k] as string), t);
      } else {
        u.value = (a[k] as number) + ((b[k] as number) - (a[k] as number)) * t;
      }
    }
  }
}
