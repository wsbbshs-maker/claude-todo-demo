// Characters that are LIT by the scene instead of pasted on.
//
// Current state (cast.ts): camera-facing plane, MeshLambertMaterial, emissiveMap = drawing,
// emissive ~0.36. A flat plane has one normal, so the whole figure gets one light value, and the
// 0.36 emissive floor flattens it further -> "sticker" look.
//
// Recipe:
//  1. bulgeNormalMap(): derive a soft "pillow" normal map from the drawing's alpha (and optionally
//     from separate part masks: head, torso, limbs). Sun from the side -> lit side + shadow side.
//  2. MeshToonMaterial with a 3-step gradientMap: flat cartoon fills, but a real light/shadow band
//     that follows the sun, receives shadows and coloured light pools (window light, fire).
//  3. emissive drops to ~0.08 (just keeps faces readable in deep shadow).
//  4. Hemisphere ground colour + fill light carry the blue/purple into the shadow side.

import {
  CanvasTexture,
  Color,
  DataTexture,
  LinearFilter,
  MeshToonMaterial,
  NearestFilter,
  NoColorSpace,
  RedFormat,
  SRGBColorSpace,
  Texture,
  Vector2,
} from "three";

type AnyCanvas = HTMLCanvasElement | OffscreenCanvas;

function makeCanvas(w: number, h: number): AnyCanvas {
  if (typeof OffscreenCanvas !== "undefined") return new OffscreenCanvas(w, h);
  const c = document.createElement("canvas");
  c.width = w;
  c.height = h;
  return c;
}

export type BulgeOptions = {
  /** work resolution as a fraction of the drawing (normal maps are smooth: 0.5 is plenty) */
  scale?: number;
  /** blur radius in DESIGN pixels (600x1000 canvas): how wide the rounded rim is */
  radius?: number;
  /** tan of the normal tilt at the rim (1.2 ~ 50 deg): how round the figure reads */
  strength?: number;
  /** extra masks (same size as the drawing, alpha = part) with weights, e.g. the head drawn alone */
  parts?: { mask: AnyCanvas; weight: number; radius?: number }[];
};

function blurredAlpha(src: AnyCanvas, w: number, h: number, radiusPx: number): Float32Array {
  const c = makeCanvas(w, h);
  const ctx = c.getContext("2d") as CanvasRenderingContext2D;
  ctx.filter = `blur(${radiusPx}px)`;
  ctx.drawImage(src as CanvasImageSource, 0, 0, w, h);
  const px = ctx.getImageData(0, 0, w, h).data;
  const out = new Float32Array(w * h);
  for (let i = 0; i < w * h; i++) out[i] = px[i * 4 + 3] / 255;
  return out;
}

/**
 * Normal map (tangent space, +Z out of the plane) from a character drawing.
 * Cache it per pose/outfit key: ~4-8 ms per call at scale 0.5.
 */
export function bulgeNormalMap(drawing: AnyCanvas, opts: BulgeOptions = {}): CanvasTexture {
  const { scale = 0.5, radius = 28, strength = 1.2, parts = [] } = opts;
  const w = Math.max(2, Math.round(drawing.width * scale));
  const h = Math.max(2, Math.round(drawing.height * scale));

  // height field = blurred silhouette (+ weighted blurred parts, so head/torso/limbs round separately)
  const hgt = blurredAlpha(drawing, w, h, radius * scale);
  let total = 1;
  for (const p of parts) {
    const ph = blurredAlpha(p.mask, w, h, (p.radius ?? radius * 0.6) * scale);
    for (let i = 0; i < hgt.length; i++) hgt[i] += ph[i] * p.weight;
    total += p.weight;
  }
  for (let i = 0; i < hgt.length; i++) hgt[i] /= total;

  const out = makeCanvas(w, h);
  const octx = out.getContext("2d") as CanvasRenderingContext2D;
  const img = octx.createImageData(w, h);
  const d = img.data;
  // CSS blur(r) is a Gaussian with sigma = r; its steepest slope is ~0.4/r per design pixel.
  // Scale so that slope maps to `strength`, independent of work resolution and radius.
  const k = (strength * radius) / 0.4 * (scale / 2); // (xp - xm) spans 2 work px = 2/scale design px
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const xm = hgt[y * w + Math.max(0, x - 1)];
      const xp = hgt[y * w + Math.min(w - 1, x + 1)];
      const ym = hgt[Math.max(0, y - 1) * w + x];
      const yp = hgt[Math.min(h - 1, y + 1) * w + x];
      // canvas y grows downwards, texture v grows upwards -> flip the y gradient
      let nx = -(xp - xm) * k;
      let ny = (yp - ym) * k;
      let nz = 1;
      const len = Math.hypot(nx, ny, nz);
      nx /= len;
      ny /= len;
      nz /= len;
      const i = (y * w + x) * 4;
      d[i] = (nx * 0.5 + 0.5) * 255;
      d[i + 1] = (ny * 0.5 + 0.5) * 255;
      d[i + 2] = (nz * 0.5 + 0.5) * 255;
      d[i + 3] = 255;
    }
  }
  octx.putImageData(img, 0, 0);
  const tex = new CanvasTexture(out as HTMLCanvasElement);
  tex.colorSpace = NoColorSpace; // data, not colour
  tex.minFilter = LinearFilter;
  tex.generateMipmaps = false;
  return tex;
}

/**
 * Toon ramp, indexed by dot(N,L)*0.5+0.5 in equal bins. Values multiply the DIRECT light only.
 * Default 4 texels [0.2, 0.55, 1, 1]: lit wherever the surface faces the sun at all (dot > 0),
 * half-tone where it turns away, deep shadow only on the far side. A 3-texel ramp puts the lit
 * threshold at dot = 0.33, and camera-facing billboards under a side sun sit right on that edge.
 */
export function toonRamp(steps: number[] = [0.2, 0.55, 1.0, 1.0]): DataTexture {
  const data = new Uint8Array(steps.map((v) => Math.round(v * 255)));
  const t = new DataTexture(data, steps.length, 1, RedFormat);
  t.minFilter = NearestFilter;
  t.magFilter = NearestFilter;
  t.generateMipmaps = false;
  t.needsUpdate = true;
  return t;
}

const SHARED_RAMP = toonRamp();

/** Material for one character billboard. `drawing` is the Canvas2D figure from toon.ts. */
export function characterMaterial(drawing: AnyCanvas, normalMap: Texture, emissive = 0.08) {
  const map = new CanvasTexture(drawing as HTMLCanvasElement);
  map.colorSpace = SRGBColorSpace;
  return new MeshToonMaterial({
    map,
    normalMap,
    normalScale: new Vector2(1, 1),
    gradientMap: SHARED_RAMP,
    alphaTest: 0.5,
    transparent: false,
    emissiveMap: map,
    emissive: new Color(1, 1, 1),
    emissiveIntensity: emissive,
  });
}

/* cast.ts changes (sketch):

   // where the sprite material is created
   const nrm = normalCache.get(poseKey) ?? bulgeNormalMap(canvas, { parts: [{ mask: headCanvas, weight: 1.2 }] });
   normalCache.set(poseKey, nrm);
   mesh.material = characterMaterial(canvas, nrm, 0.08);
   mesh.castShadow = true;           // keep the existing customDepthMaterial (alphaTest) for the shadow
   mesh.receiveShadow = true;        // NEW: cable / house / bridge shadows fall across the figures
   // sun shadow settings against self-shadow acne on camera-facing planes:
   sun.shadow.bias = -0.0004; sun.shadow.normalBias = 0.03;

   toon.ts: draw the head into its own small mask canvas (same transform as in the figure), so the
   head rounds separately from the body. Same for the shako/hat if it should read as a solid.
*/
