// Directional motion blur for whip pans / fast bursts. Velocity = how far the image moves this
// frame (uv units), from camera.ts screenVelocity(). Shutter 0.5 = 180 deg. Zero cost when idle
// (set effect.blendMode.opacity.value = 0 or skip the pass when |velocity| < ~0.002).

import { Effect, EffectAttribute, BlendFunction } from "postprocessing";
import { Uniform, Vector2 } from "three";

const fragmentShader = /* glsl */ `
uniform vec2 velocity;
uniform float shutter;
void mainImage(const in vec4 inputColor, const in vec2 uv, out vec4 outputColor) {
  vec2 v = velocity * shutter;
  vec4 acc = vec4(0.0);
  for (int i = 0; i < 16; i++) {
    float t = float(i) / 15.0 - 0.5;
    acc += texture2D(inputBuffer, clamp(uv - v * t, 0.0, 1.0));
  }
  outputColor = acc / 16.0;
}`;

export class WhipBlurEffect extends Effect {
  constructor(shutter = 0.5) {
    super("WhipBlurEffect", fragmentShader, {
      blendFunction: BlendFunction.SET,
      attributes: EffectAttribute.CONVOLUTION, // samples neighbours -> needs its own EffectPass
      uniforms: new Map<string, Uniform>([
        ["velocity", new Uniform(new Vector2())],
        ["shutter", new Uniform(shutter)],
      ]),
    });
  }
  setVelocity(x: number, y: number) {
    (this.uniforms.get("velocity")!.value as Vector2).set(x, y);
  }
}
