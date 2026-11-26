# Style recipe: from the measured reference rules to code for BridgeShort

Topic folder: `references/style-recipe/` · Report: `references/reports/style-recipe.md`

## 0. Scope and limits (read first)

- Input: the measured rule summary (format, voice, loudness, script formula, picture, camera, effects).
  The 20 reference videos, our stills and the Remotion project were **not** available in this session.
  So this report does **not** contain new reference measurements, and it does **not** measure our
  current frames. Instead it delivers:
  1. tested building blocks for our stack (shaders, materials, camera timing, audio, script check),
  2. a measurement script (`measure_look.py`) that compares our stills with the colour targets, to run
     where the material lives,
  3. starting values, each marked **measured** (from the summary) or **start** (my choice, to calibrate).
- Testing: all shader/material code was compiled and rendered in a stand-in scene with the **same
  versions** (three 0.175.0, postprocessing 6.37.2; vanilla three, not r3f) in headless Chromium, and
  type-checked with `tsc --strict`. The stand-in scene is my own quick test bed (boxes, planks, simple
  figures), **not our film**. The "before" variant only *approximates* our setup from CONTEXT.md
  (Lambert, emissive 0.36 sprites, fog 90-560, white hemisphere, no grade, no working ink).
- Nothing under `your Remotion project` was touched.

## 1. Targets (measured, from the summary)

| What | Target |
|---|---|
| Frame | 1080x1920, 30 fps, 31-78 s (median ~60 s); voice starts frame 1-4; no intro/logo/outro/CTA |
| Voice | one male narrator, 3.5-4.1 words/s (median 3.7); word gaps > 0.25 s sum to < 1 s per video |
| Loudness | -14 LUFS integrated, LRA ~2.4 LU, bed 5-10 dB under speech |
| lum mean / std | 0.43-0.54 / 0.21-0.29 (per-video median) |
| lum p2 / p98 | 0.03-0.11 (deep darks) / 0.90-1.00 |
| saturation | 0.38-0.65 |
| Camera | holds ~80 % of frames (< 0.5 px/frame at 720p); moves = ease-out bursts, peak speed on frame 1, decay over ~8-10 frames (example 6, 26, 12, 14, 6, 5, 2, 1 px/frame at 720p) |
| Cuts | 0-1 hard cuts per video (12/20); place changes = 6-8 frame dissolve or continuous camera move; "cuts" detected = 4-frame flashes |
| Look | 2D flat outlined characters in 3D toon worlds; painted textures; thin ink lines on edges + creases; soft DoF backgrounds; warm key + blue/purple shadows; light pools tint characters; characters lit + cast ground shadows; light follows story beats (noon -> sunset -> night-blue for the explanation) |
| Captions | ours: none unless the user asks |

Derived numbers (computed here from the measured camera example):
- speed ratio per frame **0.60** (log-linear fit, tau 1.95 frames); 36-40 % of the move in the first
  frame, 79 % after 3 frames, 96 % after 6, done after ~10.
- "hold" threshold at 1080 width: < 0.75 px/frame -> a push-in may change fov by at most
  0.078 % per frame (e.g. 4-6 % over a 90-frame hold).

## 2. Test results (stand-in scene, 540x960)

Images:
- `references/style-recipe/shots/compare_states.png`: before | after day | after golden | after night
- `references/style-recipe/shots/compare_ink_2x.png`: no ink vs InkEffect (DoF off to show the lines)
- `references/style-recipe/shots/compare_character_3x.png`: Lambert+emissive 0.36 vs toon ramp + bulge normals + received shadow
- single renders: `references/style-recipe/shots/*.png`

`python3 measure_look.py <png> --no-mask` (full frame, no captions in our renders):

| Render | lum mean | lum std | p2 | p98 | sat |
|---|---|---|---|---|---|
| target | 0.43-0.54 | 0.21-0.29 | 0.03-0.11 | 0.90-1.00 | 0.38-0.65 |
| before (approx. current) | 0.528 | **0.201** | 0.061 | **0.807** | 0.652 |
| after, day | 0.516 | 0.282 | **0.015** | 0.890 | **0.679** |
| after, golden | 0.407 | 0.290 | 0.019 | 0.784 | 0.691 |
| after, night | 0.226 | 0.143 | 0.014 | 0.548 | 0.872 |

(An earlier framing of the same scene with more sky/water gave before: std 0.148, p2 **0.286**, which
is the "pastel" signature: no real darks.)

Reading it:
- Day moves into range on mean/std/p98; p2 overshoots (0.015 < 0.03) and sat is slightly high, because
  the test textures are already very saturated. Our pastel frames need *more* saturation, so the
  same preset may land inside. **Tune on our stills with the loop in 5.6, don't copy the numbers blind.**
- Golden and night are single shots. The targets are **per-video medians**, so darker golden/night
  shots are fine as long as the whole video's median lands in range.
- Visible issues left in the test: ink lines are aliased (depth isn't multisampled -> add SMAA after
  Ink); characters' shadow side is too dark/maroon (raise hemisphere/fill, see 5.3); tan skin still
  drifts to orange under the warm sun (skinProtect helps, but check faces on our palette).

## 3. Top 5 changes, ranked by visual impact

1. **Light ratio + colour grade** (kills "flat, pastel"). Push fog out (90-560 -> 180-900), hemisphere
   ground colour blue-purple instead of near-white, sun ~4x hemisphere, then `GradeEffect` after
   ToneMapping (black point, S-curve, saturation, split toning). Stats: std 0.20 -> 0.28, p98 0.81 -> 0.89.
2. **Characters lit, not pasted**: `MeshToonMaterial` + 4-step ramp + bulge normal map from the
   drawing's alpha (head rounded separately), `receiveShadow = true`, emissive 0.36 -> 0.08. Gives a
   lit side, a shadow side, cast shadows across the figures and coloured light pools on them.
3. **Ink that actually draws**: replace the absolute Laplacian (threshold 0.06 never fires) with the
   relative, distance-independent `InkEffect` (silhouette 3 % depth gap, crease 0.6 tan-units, 2 px at
   1080). Lines on roofs, walls, planks, rails, water edge; none on the sky; no doubled character outlines.
4. **Camera grammar**: holds with slow push-ins, ease-out bursts (ratio 0.6/frame, no ease-in),
   dutch tilt + 4-frame flash for the bolt snap, 7-frame dissolves for place changes, whip blur
   during bursts. This is the "lively movement" without cutting.
5. **Depth of field on backgrounds** focused on the speaking subject each shot (ink goes *before*
   DoF so background lines soften with it), plus the night-blue/golden light states switched with
   the story beats via `GradeEffect.setMix`.

Then: egg-shaped heads (5.4), audio mastering (6), script check (7).

## 4. Files in `references/style-recipe/`

| File | What | Status |
|---|---|---|
| `ink-effect.ts` | `InkEffect` (postprocessing Effect, depth only) + React wrapper sketch | compiled + rendered, tsc OK |
| `grade-effect.ts` | `GradeEffect` + presets `GRADE_DAY/GOLDEN/NIGHT` + `setMix()` | compiled + rendered, tsc OK |
| `character-lighting.ts` | `bulgeNormalMap()`, `toonRamp()`, `characterMaterial()` | rendered, tsc OK |
| `whip-blur-effect.ts` | directional blur for whip pans | tsc OK, **not rendered** |
| `camera.ts` | `burst`, `burstInterp`, `pushIn`, `dutch`, `flash`, `dissolve`, `screenVelocity` | parses; math checked against the fit |
| `measure_look.py` | colour stats vs targets (images or videos, caption band masked) | run on test renders |
| `master_audio.py` | voice + bed premix to -14 LUFS (ffmpeg) | run on synthetic audio: I -14.0, TP -1.0, bed -7 dB |
| `check_script.py` | script vs formula (pace, hook, "You see,", mystery beat, payoff ...) | run on a dummy text |
| `harness/` | test scene (`main.ts`, `shoot.cjs`, `index.html`); needs three 0.175 + postprocessing 6.37.2 + esbuild | used for all renders |

## 5. Implementation recipe

### 5.1 `Bridge.tsx`: effect chain

```tsx
<EffectComposer multisampling={4} frameBufferType={HalfFloatType}>
  <Ink thickness={2} silhouette={0.03} crease={0.6} fadeNear={40} fadeFar={220} farStrength={0.35} />
  <SMAA />                                   {/* the ink is computed per pixel from depth -> anti-alias it */}
  <DepthOfField worldFocusDistance={focusDist} worldFocusRange={focusDist * 0.9} bokehScale={5} />
  <Bloom intensity={0.3} luminanceThreshold={0.86} mipmapBlur />
  <ToneMapping mode={ToneMappingMode.NEUTRAL} />
  <Grade from={GRADE_DAY} to={GRADE_GOLDEN} t={beatMix} />   {/* LAST */}
</EffectComposer>
```

- `focusDist` = camera -> current subject (per shot, from CAMS). Harness used `bokehScale` 3 at 540 px
  (resolutionScale 0.5), so start at ~5-6 for 1080 (**start**).
- Wrapper for the grade (same pattern as the existing Ink wrapper):

```tsx
export function Grade({ from, to = from, t = 0 }: { from: Required<GradeOptions>; to?: Required<GradeOptions>; t?: number }) {
  const effect = useMemo(() => new GradeEffect(from), []);
  effect.setMix(from, to, t);                // day -> golden -> night across story beats
  return <primitive object={effect} dispose={null} />;
}
```

### 5.2 `ink.ts` -> `InkEffect`

Why the current pass draws almost nothing: an absolute Laplacian of 1/viewZ scales with 1/z², so at
20-60 world units it is ~1e-5 to 1e-4 and never reaches 0.06. `InkEffect` divides by 1/z (relative gap) and by
the angular size of a pixel, so both thresholds mean the same thing at every distance and resolution.

| Uniform | Value | Meaning |
|---|---|---|
| `inkColor` | `#1a1020` | warm near-black (**start**) |
| `thickness` | 2 px at 1080 (1 at 540) | sample offset ~ line width; keep >= 1 (depth is sampled nearest) (**start**: measure ref line width) |
| `silhouette` | 0.03 | depth gap of 3 % of the distance starts a line |
| `crease` | 0.6 | slope change in tan units (~30-35 deg fold) |
| `fadeNear/fadeFar/farStrength` | 40 / 220 / 0.35 | lines thin out with distance (DoF softens them further) |
| `pxAngle` | set per frame | `ink.setCamera(camera, outputHeightPx)` wherever World applies the CAMS camera |

Rules: no NormalPass (its override material ignores `alphaTest`, billboards become rectangles);
lines are drawn on the **near** side only (on characters they land on their own drawn outline);
the sky sphere should use `depthWrite: false` so the sky stays at depth 1 (no lines on it); camera
`near` >= 0.3 keeps far creases clean.

### 5.3 Light (`story.ts` LIGHTS, `world.ts`)

Values used in the test renders. Intensities are three r175 units with our post chain. **What carries
over is the ratio** (sun ~3.5-4x hemisphere by day) and the colours. All **start**.

| State | Sun / moon | Hemisphere sky / ground / int. | Fill | Fog | Extra |
|---|---|---|---|---|---|
| day | `#ffe2b8` 4.2, high side light | `#9cc4ff` / `#5a4aa8` / 1.1 | `#7a86ff` 0.35 from the opposite side | `#bcd8f0` 180-900 | |
| golden | `#ffb070` 4.8, low (long shadows) | `#8a7ad8` / `#4a2f8a` / 1.0 | as day | `#e8a080` 180-900 | |
| night (explanation) | `#8fa8ff` 3.0 | `#5a6ad0` / `#2a2478` / 2.4 | none | `#1a2050` 120-700 | window pools: `PointLight('#ffb347', 40, 10, 1.6)` near characters |
| before (approx. current) | `#fff4e0` 2.2 | `#ffffff` / `#d8d0c0` / 1.6 | white 0.6 | `#d8e8f5` 90-560 | |

- Fog 90-560 is a prime suspect for the pastel look: it pulls everything beyond 90 units toward a
  light blue-grey (low contrast, low saturation). Push it out and let DoF do the depth separation.
- Shadow side of characters came out too dark in the test (~35 % of lit). Target ~45-55 % and
  visibly blue-purple: raise hemisphere intensity ~1.4-1.6 or the toon ramp's first steps.
- Sun shadow on billboards: `bias -0.0004`, `normalBias 0.03` (no acne in the test).

### 5.4 Characters (`cast.ts`, `toon.ts`)

```ts
// cast.ts, where a sprite material is made
const nrm = normalCache.get(poseKey) ?? bulgeNormalMap(canvas, { parts: [{ mask: headCanvas, weight: 1.2, radius: 18 }] });
normalCache.set(poseKey, nrm);                       // ~4-8 ms per call at scale 0.5 -> cache per pose
mesh.material = characterMaterial(canvas, nrm, 0.08); // MeshToonMaterial, ramp [0.2, 0.55, 1, 1], emissive 0.08
mesh.receiveShadow = true;                            // keep castShadow + the alphaTest depth material
```

- `bulgeNormalMap` options: `radius` 28 design px (rim width), `strength` 1.2 (tan of the rim tilt),
  `scale` 0.5. Normal map uses `NoColorSpace`.
- Ramp: 4 texels `[0.2, 0.55, 1, 1]`. With the default 3-texel ramp the lit threshold sits at
  dot(N,L) = 0.33, and camera-facing billboards under a side sun flicker right on that edge.
- Effect sprites (notes, stars, bursts, splash) stay **unlit** (`MeshBasicMaterial`, colour x1.5 so
  Bloom catches them): they read as light sources.
- Heads not circles: the test figure uses an egg shape (wider cheeks/jaw, narrower crown). As a
  Canvas2D path relative to centre `cx`, top `t`, height `h`, half-width `w`:

```ts
function eggHead(g: CanvasRenderingContext2D, cx: number, t: number, h: number, w: number) {
  const X = (f: number) => cx + f * w, Y = (f: number) => t + f * h;
  g.moveTo(X(0), Y(0));
  g.bezierCurveTo(X(0.94), Y(0), X(1.06), Y(0.40), X(0.94), Y(0.64));
  g.bezierCurveTo(X(0.83), Y(0.90), X(0.39), Y(1), X(0), Y(1));
  g.bezierCurveTo(X(-0.5), Y(1), X(-0.94), Y(0.88), X(-0.98), Y(0.60));
  g.bezierCurveTo(X(-1.02), Y(0.31), X(-0.78), Y(0), X(0), Y(0));
}
```
  The slight asymmetry is deliberate (reads hand-drawn). Draw the same path into `headCanvas` for the
  normal map. Proportions (head:body ratio, shoulder width) were **not** measured here; see 8.

### 5.5 Camera (`story.ts` CAMS) with `camera.ts`

| Need | Helper | Values |
|---|---|---|
| move to next subject | `burst(frame, start)` or `burstInterp(frame, start, from, to)` | ratio 0.6/frame, 10 frames, no ease-in (**measured**) |
| hold | `pushIn(frame, start, end, 0.05)` (fov multiplier) | capped at 0.078 %/frame -> stays a "hold" (**derived**) |
| drama / fall | `dutch(frame, start, end, 10)` | 8 deg unease, 12-15 deg for the fall (**start**) |
| impact / bolt snap | `flash(frame, at)` white overlay | 0.85, 0.55, 0.25, 0.08 (**start**; 4 frames **measured**) |
| place change (golden park, bank, tourists) | `dissolve(frame, start, 7)` on overlapping `<Sequence>`s | 6-8 frames (**measured**) |
| whip pan | `WhipBlurEffect` + `screenVelocity()` | shutter 0.5, only when blur > ~0.002 uv/frame (**start**) |

Keep cameras low (deck / knee-to-chest height) and use object-follow moves (a note, a falling bolt,
a splash) as transitions instead of cuts.

### 5.6 Calibration loop (run where the material is)

```bash
# 1 check the definitions: these must land in the target ranges
python3 references/style-recipe/measure_look.py references/vids/01_*.mp4 references/vids/05_*.mp4 --fps 2
# 2 our current stills (the gap)
python3 references/style-recipe/measure_look.py "your Remotion project/out/bridge/test/c_*.jpg"
# 3 after each change: re-render a few stills, re-measure, adjust GRADE_* / LIGHTS
```
lum = Rec.709 luma on display values, sat = HSV saturation mean, caption band 60-74 % masked. If step 1
does not reproduce the targets, the summary used other definitions: adjust `frame_stats()` first.

## 6. Audio (`master_audio.py`)

`python3 master_audio.py voice.wav music.wav mix.wav --tighten --bed-db 7`

- Leading silence trimmed to 20 ms -> first word on frame 1-2. `--tighten` shortens pauses > 0.18 s to
  0.08 s. **Run it before the visuals are timed**, because it shifts every timestamp after a pause.
- Voice: highpass 80 Hz, compressor 4:1 @ -24 dB, two-pass loudnorm to -15 LUFS. Bed normalised to
  -22 LUFS (7 dB under) + light sidechain ducking. Final two-pass loudnorm -14 LUFS / -1 dBTP.
- Synthetic test: final I -14.0 LUFS, TP -1.0 dB, bed 7 dB under the voice, 0.7 s leading silence removed.
- Remotion: one `<Audio>` with the premix at volume 1 from frame 1; check the rendered mp4 with
  `ffmpeg -i out.mp4 -af ebur128=peak=true -f null -`.
- Words for 67 s at 3.7 w/s: ~248.

## 7. Script (`check_script.py`)

`python3 check_script.py script.txt --seconds 67` reports words vs planned length, median sentence length
(~13.5), hook length (10-16), position of "You see," (second half), mystery beat, analogy, dialogue
lines, contractions, last-sentence length, and over-long sentences. It checks structure only; story and
wording stay ours.

## 8. Still to measure on the references (could not be done here)

| Gap | How |
|---|---|
| ink line width (px at 720) and whether creases are thinner than silhouettes | nearest-upscaled crops, dark-run length perpendicular to edges, outside the caption band |
| character outline width vs world ink width | same, on characters |
| DoF blur by depth (px) | edge spread on background vs subject edges |
| character proportions (head:body, head aspect, shoulder:hip) | bounding boxes of 30+ characters |
| shadow-side colour/brightness on characters and ground (hex, % of lit) | paired lit/shadow samples on the same material |
| flash curve over its 4 frames, dissolve curve | mean luma per frame around detected events |

## 9. Next steps

1. Run the calibration loop (5.6) step 1, then step 2 on our current stills.
2. The lead wires `InkEffect` + `GradeEffect` into `Bridge.tsx` and swaps the character material in `cast.ts`.
3. Re-render a handful of stills (day, golden, river, bank), re-measure, tune `GRADE_*` and LIGHTS.
4. Measure the gaps in section 8 and replace the **start** values.
