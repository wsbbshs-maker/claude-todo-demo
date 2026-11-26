// Ink outlines for the 3D world: silhouettes + creases from the depth buffer only.
//
// Drop-in replacement for the current Laplacian-of-1/viewZ pass in ink.ts.
// Why the current pass draws almost nothing: an ABSOLUTE Laplacian of 1/viewZ shrinks
// with 1/z^2, so at 20-60 world units it is ~1e-5..1e-4 and never reaches 0.06.
// This version divides by 1/z (relative jump) and by the angular size of one pixel,
// so both thresholds are distance- and resolution-independent:
//   silhouette = relative depth gap between neighbours (0.03 = 3 % of the distance)
//   crease     = change of surface slope across the pixel, in tan() units
//                (0.6 ~ a 30-35 deg fold; box edges, roof ridges, plank seams)
// No NormalPass: MeshNormalMaterial overrides ignore alphaTest, so every billboard
// character would show up as a rectangle in the normal buffer and get a box outline.
// The depth buffer respects alphaTest, and lines are drawn on the NEAR side only, so on
// characters they land on the outline that toon.ts already draws (no double line).

import { Effect, EffectAttribute, BlendFunction } from "postprocessing";
import { Color, PerspectiveCamera, Uniform } from "three";

const fragmentShader = /* glsl */ `
uniform vec3 inkColor;
uniform float thickness;   // sample offset in output pixels ~ line width
uniform float silhouette;  // relative depth gap that starts a line
uniform float crease;      // slope change (tan units) that starts a line
uniform float pxAngle;     // 2*tan(fov/2)/resolution.y, set every frame
uniform float fadeNear;    // world units: lines at full strength up to here
uniform float fadeFar;     // ... and at farStrength from here on
uniform float farStrength;
uniform float opacity;

float invZ(const in vec2 p) {
  return 1.0 / max(-getViewZ(readDepth(p)), 1e-4);
}

void mainImage(const in vec4 inputColor, const in vec2 uv, const in float depth, out vec4 outputColor) {
  if (depth >= 0.99999) { outputColor = inputColor; return; } // sky: no lines

  vec2 o = texelSize * thickness;
  float c = 1.0 / max(-getViewZ(depth), 1e-4);
  float l = invZ(uv - vec2(o.x, 0.0));
  float r = invZ(uv + vec2(o.x, 0.0));
  float d = invZ(uv - vec2(0.0, o.y));
  float u = invZ(uv + vec2(0.0, o.y));
  vec2 dl = uv + vec2(-o.x, o.y) * 0.7071;
  vec2 dr = uv + vec2(o.x, -o.y) * 0.7071;
  float a = invZ(dl);
  float b = invZ(dr);

  // silhouette: some neighbour is much farther than this pixel -> we are the near edge
  float nearJump = max(max(max(c - l, c - r), max(c - d, c - u)), max(c - a, c - b)) / c;
  float sil = smoothstep(silhouette, silhouette * 1.6, nearJump);

  // crease: second difference of 1/z is exactly 0 on any plane (perspective-correct),
  // normalised by 1/z and by the pixel angle -> "change of tan(slope)" across the pixel
  float absJump = max(max(abs(c - l), abs(c - r)), max(abs(c - d), abs(c - u))) / c;
  float lap = max(abs(l + r - 2.0 * c), abs(d + u - 2.0 * c)) / c;
  float slopeChange = lap / (thickness * pxAngle);
  float cre = smoothstep(crease, crease * 1.8, slopeChange) * (1.0 - step(silhouette, absJump));

  float dist = -getViewZ(depth);
  float fade = mix(1.0, farStrength, smoothstep(fadeNear, fadeFar, dist));
  float ink = max(sil, cre) * fade * opacity;
  outputColor = vec4(mix(inputColor.rgb, inkColor, ink), inputColor.a);
}`;

export type InkOptions = {
  color?: string;
  thickness?: number;
  silhouette?: number;
  crease?: number;
  fadeNear?: number;
  fadeFar?: number;
  farStrength?: number;
  opacity?: number;
};

export class InkEffect extends Effect {
  constructor({
    color = "#1a1020", // warm near-black, not pure #000 (pure black lines on painted textures read as CG)
    thickness = 2, // px at 1080 width (1 px at 540). Keep >= 1: the depth texture is sampled
    // nearest, so sub-pixel offsets land in the same texel and lines drop out.
    silhouette = 0.03,
    crease = 0.6,
    fadeNear = 40,
    fadeFar = 220,
    farStrength = 0.35,
    opacity = 1,
  }: InkOptions = {}) {
    super("InkEffect", fragmentShader, {
      blendFunction: BlendFunction.NORMAL,
      attributes: EffectAttribute.DEPTH,
      uniforms: new Map<string, Uniform>([
        ["inkColor", new Uniform(new Color(color))],
        ["thickness", new Uniform(thickness)],
        ["silhouette", new Uniform(silhouette)],
        ["crease", new Uniform(crease)],
        ["pxAngle", new Uniform(0.0003)],
        ["fadeNear", new Uniform(fadeNear)],
        ["fadeFar", new Uniform(fadeFar)],
        ["farStrength", new Uniform(farStrength)],
        ["opacity", new Uniform(opacity)],
      ]),
    });
  }

  /** Call once per frame (or whenever fov / output height change). */
  setCamera(camera: PerspectiveCamera, outputHeightPx: number) {
    const fov = (camera.fov * Math.PI) / 180;
    this.uniforms.get("pxAngle")!.value = (2 * Math.tan(fov / 2)) / camera.zoom / outputHeightPx;
  }
}

/* React wrapper for Bridge.tsx (@react-three/postprocessing 3 / r3f 9):

import { useMemo, useEffect } from "react";
import { useThree } from "@react-three/fiber";
import { useCurrentFrame } from "remotion";

export function Ink(props: InkOptions) {
  const effect = useMemo(() => new InkEffect(props), []);          // build once
  const camera = useThree((s) => s.camera) as PerspectiveCamera;
  const size = useThree((s) => s.size);
  const dpr = useThree((s) => s.viewport.dpr);
  const frame = useCurrentFrame();
  // Keep pxAngle in sync with the animated fov. Remotion drives rendering per frame, so tie it to
  // the frame (or call effect.setCamera() right where World applies the CAMS camera each frame)
  // instead of relying on useFrame.
  effect.setCamera(camera, size.height * dpr);
  void frame;
  useEffect(() => {                                                  // live-tweak numbers
    for (const [k, v] of Object.entries(props)) {
      const u = effect.uniforms.get(k === "color" ? "inkColor" : k);
      if (!u) continue;
      if (k === "color") (u.value as Color).set(v as string); else u.value = v;
    }
  }, [effect, props]);
  return <primitive object={effect} dispose={null} />;
}
*/
