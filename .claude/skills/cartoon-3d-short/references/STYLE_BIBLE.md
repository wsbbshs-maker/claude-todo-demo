# the reference channel style bible (study of latest 20 shorts, 2026-10-30)
Private study only. The study files below live in a local folder and are never shipped or shared. Videos: vids/ (720p, original EN audio), transcripts: tx/, per-video measurements: measure/summary.json,
30 fps contact sheets: measure/<video>_sheets/ (each sheet = 2 s, 60 frames).

## Format
- Vertical 1080x1920, 30 fps, 31-78 s (median ~60 s), voice starts at frame 1-4 (no intro, no logo, no outro, no CTA).
- Voice: one male narrator, fast and steady: 3.5-4.1 words/s (median 3.7), almost no pauses (word gaps >0.25 s total <1 s per video).
- Loudness -14 LUFS integrated, LRA ~2.4 LU (heavily compressed). Music/SFX bed under voice only ~5-10 dB below speech.
- Captions: one word (sometimes 2-3) at a time, white bold sans, thin black outline, lower-middle, hard swaps on each word.
  (OUR RULE: no captions unless the user asks.)

## Script formula (20/20 follow it)
1. **Hook = paradox stated as fact, sentence 1, no setup.** A person did something that sounds dumb/impossible with stakes,
   or "If you X, you'd Y", or "X is illegal, yet ...". ~10-16 words.
2. **Setting in 1-2 lines**, present tense, concrete details (time of day, a named everyman, numbers).
3. **Escalation, 3-6 beats**: others laugh / doubt / mock (short in-character dialogue lines), stakes climb.
   1-2 exaggeration jokes per video (claim vs reality, "so slow X, and X was ...").
4. **Mystery beat**: a question or "Wait, ...?" (~1 per video).
5. **Pivot word "You see,"** (14 of 20 videos) → the real mechanism. Often an everyday analogy
   ("Ever ...?", "think about the last time ...", "picture your body as ...").
6. **Ironic payoff** in the last 1-2 sentences, short, lands the twist. Video ends on the last word.
- Two modes: story mode (third person "he", named everyman, present tense) and "Imagine you're..." second person.
- Sentences ~13.5 words median, plain spoken English, contractions, no jargon unless explained in the next clause.

## Picture
- 2D flat cartoon characters (simple outlined faces, thin black outline, flat colors) standing in **3D toon environments**.
- 3D environments: hand-painted textures, saturated colors, **thin black ink outlines on 3D geometry** (edges + creases),
  soft depth of field on backgrounds, warm key light + blue/purple shadows, light pools (window light) that also tint the characters.
- Characters receive scene light/shadow (they are lit, not pure emission), cast ground shadows.
- Color stats (per video median, whole frame incl. ink lines and night/interior shots): lum mean 0.43-0.54,
  lum std 0.21-0.29, p2 0.03-0.11, p98 0.9-1.0, saturation 0.38-0.65. Lighting changes with story beats
  (noon -> sunset -> night-blue for the explanation).
  **Do not grade toward that p2.** The low p2 comes from the ink lines and the night/interior shots, not from dark
  surfaces. Day frames without ink have lifted, coloured darks: non-ink Y' p5 0.23, Y' p50 0.57, HSV S mean 0.44
  (see `reports/grade.md` section 1 table, measured with an ink mask and correct bt709 decoding).
- Every sentence is illustrated literally; props carry the joke (beers, frogs, milk cart).

## Camera / editing (measured; corrected, see `reports/motion.md`)
The first version of this section said "camera holds ~80 % of frames, moves are ease-out bursts with peak speed on
frame 1". That came from an integer phase correlation that cannot see motion below ~4 px/f, and it is **wrong**.
Sub-pixel measurement over 32,337 frames (720p px/f, multiply by 1.5 for 1080x1920):
- **The camera almost never stands still**: hold (< 0.3 px/f) 10 % of frames, drift 24 %, move 65 %.
- **Moves are symmetric ease-in-out glides**: ~10 f in, ~10 f out, ~23 f total, median peak 14-16 px/f
  (strong moves: attack 8 f, release 7 f). About 6 moves per 10 s.
- **Every quiet stretch pushes in**: median 0.14 %/f (p75 0.34); push-in runs ~35 f; ~0.6 %/f on punch words.
- **Hard cuts are rare** (0-1 per video in 12/20; most detected "cuts" are 4-frame flashes). Place changes use
  continuous moves (follow an object, fly-through), a 6-8 frame dissolve, or a rare whip pan (0.45 per minute,
  45-93 px/f, always with strong directional motion blur).
- **Rolls**: ~3 per 10 s, median 3.6 deg over 18 f. **Impacts**: 6-8 frame kicks that flip sign every frame
  (~3 px at 720p). **No hand-held float.**
- Low camera heights; dutch tilts for drama/falls.

## Effects
- Muzzle fire, glow/aura bursts, sparkles on impact, splash sprites, speed lines, dust puffs, music notes, stars,
  light shafts; all flat 2D cartoon sprites composited into the 3D scene.
