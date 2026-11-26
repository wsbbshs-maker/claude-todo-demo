// Test bed for the recipe pieces (NOT our film): vanilla three 0.175 + postprocessing 6.37.2.
// ?v=before  ~ current look (Lambert, emissive 0.36 sprites, fog 90-560, no ink, no grade)
// ?v=after   recipe (InkEffect, toon-lit sprites with bulge normals, DoF, grade)
// ?v=inkonly after-lighting without grade (to see the ink alone)
import * as THREE from "three";
import {
  BloomEffect,
  DepthOfFieldEffect,
  EffectComposer,
  EffectPass,
  RenderPass,
  ToneMappingEffect,
  ToneMappingMode,
} from "postprocessing";
import { InkEffect } from "../ink-effect";
import { GradeEffect, GRADE_DAY, GRADE_GOLDEN, GRADE_NIGHT } from "../grade-effect";
import { bulgeNormalMap, characterMaterial } from "../character-lighting";

const params = new URLSearchParams(location.search);
const V = params.get("v") ?? "after";
const LIGHT = params.get("light") ?? "day";
const AFTER = V !== "before";
const DOF = params.get("dof") !== "0";
const W = 540, H = 960;

const renderer = new THREE.WebGLRenderer({ antialias: false, preserveDrawingBuffer: true, powerPreference: "high-performance" });
renderer.setSize(W, H);
renderer.setPixelRatio(1);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
document.body.appendChild(renderer.domElement);

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(38, W / H, 0.5, 1500);
camera.position.set(-2.2, 3.3, 9.2);
camera.lookAt(2.2, 3.0, 1.0);

// ---------- painted textures (quick stand-ins for paint.ts) ----------
function rng(seed: number) { return () => ((seed = (seed * 16807) % 2147483647) / 2147483647); }
function paint(w: number, h: number, base: string, strokes: string[], n: number, seed: number, len = 14) {
  const c = document.createElement("canvas"); c.width = w; c.height = h;
  const g = c.getContext("2d")!; const r = rng(seed);
  g.fillStyle = base; g.fillRect(0, 0, w, h);
  for (let i = 0; i < n; i++) {
    g.strokeStyle = strokes[i % strokes.length]; g.globalAlpha = 0.25 + r() * 0.35;
    g.lineWidth = 2 + r() * 5; g.lineCap = "round";
    const x = r() * w, y = r() * h, a = r() * Math.PI;
    g.beginPath(); g.moveTo(x, y); g.lineTo(x + Math.cos(a) * len * (0.5 + r()), y + Math.sin(a) * len * (0.5 + r())); g.stroke();
  }
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace;
  t.wrapS = t.wrapT = THREE.RepeatWrapping; t.anisotropy = 4; return t;
}
const grassT = paint(256, 256, "#5f9e2f", ["#7cc23a", "#3f7a22", "#9bd04a", "#2f6a2a"], 900, 3, 10); grassT.repeat.set(30, 30);
const plankT = paint(256, 256, "#a8703a", ["#c98a48", "#7a4a22", "#5a3416"], 500, 7, 40); plankT.repeat.set(1, 8);
const wallT = paint(256, 256, "#e8c98a", ["#f5dca8", "#c9a060", "#d8b070"], 500, 11, 12);
const wall2T = paint(256, 256, "#d97a5a", ["#e89878", "#b85a3e", "#f0a888"], 500, 13, 12);
const roofT = paint(256, 256, "#3c5a9a", ["#5a7ac0", "#2a3c70", "#4a6ab0"], 600, 17, 18); roofT.repeat.set(2, 2);
const stoneT = paint(256, 256, "#9a9088", ["#b8aea4", "#6e6660", "#857a70"], 700, 19, 10);
const waterT = paint(256, 256, "#2f8fbf", ["#5fc0e8", "#1f6f9f", "#8fdcf5"], 600, 23, 30); waterT.repeat.set(8, 8);

const M = (map: THREE.Texture, color = "#ffffff") => new THREE.MeshLambertMaterial({ map, color });

// ---------- world ----------
const ground = new THREE.Mesh(new THREE.PlaneGeometry(800, 800), M(grassT));
ground.rotation.x = -Math.PI / 2; ground.receiveShadow = true; scene.add(ground);
const water = new THREE.Mesh(new THREE.PlaneGeometry(14, 800), new THREE.MeshPhongMaterial({ map: waterT, shininess: 60, specular: new THREE.Color("#bfe8ff") }));
water.rotation.x = -Math.PI / 2; water.position.set(4, 0.02, 0); scene.add(water);

// bridge deck + towers
const deck = new THREE.Mesh(new THREE.BoxGeometry(18, 0.35, 3.2), M(plankT)); deck.position.set(4, 1.6, 2); deck.castShadow = deck.receiveShadow = true; scene.add(deck);
for (const x of [-4.5, 12.5]) for (const z of [0.4, 3.6]) {
  const t = new THREE.Mesh(new THREE.BoxGeometry(0.9, 7, 0.9), M(stoneT)); t.position.set(x, 3.5, z); t.castShadow = t.receiveShadow = true; scene.add(t);
}
const rail = new THREE.Mesh(new THREE.BoxGeometry(18, 0.12, 0.12), M(plankT)); rail.position.set(4, 2.6, 0.5); rail.castShadow = true; scene.add(rail);

function house(x: number, z: number, w: number, d: number, h: number, wall: THREE.Texture, rot = 0) {
  const g = new THREE.Group();
  const body = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), M(wall)); body.position.y = h / 2; body.castShadow = body.receiveShadow = true; g.add(body);
  const shape = new THREE.Shape(); shape.moveTo(-w / 2 - 0.3, 0); shape.lineTo(0, h * 0.55); shape.lineTo(w / 2 + 0.3, 0); shape.lineTo(-w / 2 - 0.3, 0);
  const roof = new THREE.Mesh(new THREE.ExtrudeGeometry(shape, { depth: d + 0.6, bevelEnabled: false }), M(roofT));
  roof.position.set(0, h, -d / 2 - 0.3); roof.castShadow = roof.receiveShadow = true; g.add(roof);
  const win = new THREE.Mesh(new THREE.BoxGeometry(w * 0.25, h * 0.25, 0.05), new THREE.MeshLambertMaterial({ color: "#2a3050" }));
  win.position.set(-w * 0.2, h * 0.55, d / 2 + 0.02); g.add(win);
  const win2 = win.clone(); win2.position.x = w * 0.2; g.add(win2);
  g.position.set(x, 0, z); g.rotation.y = rot; scene.add(g);
}
house(-9, -6, 5, 4, 4.5, wallT, 0.3); house(-3, -14, 6, 5, 5.5, wall2T, -0.2); house(16, -10, 5, 5, 4, wallT, 0.5);
house(24, -30, 7, 5, 6, wall2T, 0.1); house(-18, -28, 6, 5, 5, wallT, 0.4); house(8, -45, 8, 6, 7, wall2T, -0.3);
for (let i = 0; i < 14; i++) {
  const r = rng(100 + i);
  const tree = new THREE.Mesh(new THREE.IcosahedronGeometry(1.6 + r() * 1.2, 1), new THREE.MeshLambertMaterial({ color: "#3f8f2f", flatShading: true }));
  tree.position.set(-30 + r() * 70, 2.5, -20 - r() * 60); tree.castShadow = true; scene.add(tree);
}

// sky (depthWrite off -> depth stays 1, no ink on the sky)
const skyMat = new THREE.ShaderMaterial({
  side: THREE.BackSide, depthWrite: false, fog: false,
  uniforms: { top: { value: new THREE.Color(LIGHT === "night" ? "#1a2470" : LIGHT === "golden" ? "#5a7ad8" : "#3f8ff0") }, bot: { value: new THREE.Color(LIGHT === "night" ? "#4a5ab8" : LIGHT === "golden" ? "#ffb070" : "#bfe6ff") } },
  vertexShader: "varying vec3 p; void main(){ p = normalize(position); gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.); }",
  fragmentShader: "uniform vec3 top; uniform vec3 bot; varying vec3 p; void main(){ gl_FragColor = vec4(mix(bot, top, smoothstep(-0.05, 0.5, p.y)), 1.); }",
});
const sky = new THREE.Mesh(new THREE.SphereGeometry(1200, 32, 16), skyMat); sky.renderOrder = -1; scene.add(sky);

// ---------- characters (own simple design: oval-egg head, coat, tall hat) ----------
function figure(coat: string, skin: string, headOnly = false) {
  const c = document.createElement("canvas"); c.width = 600; c.height = 1000;
  const g = c.getContext("2d")!; g.lineJoin = "round"; g.lineCap = "round";
  const ink = (fill: string, path: () => void, lw = 9) => { g.beginPath(); path(); g.fillStyle = fill; g.fill(); g.lineWidth = lw; g.strokeStyle = "#140c14"; g.stroke(); };
  if (!headOnly) {
    ink("#2b2b44", () => { g.moveTo(240, 640); g.lineTo(220, 960); g.lineTo(285, 960); g.lineTo(300, 700); g.lineTo(315, 960); g.lineTo(380, 960); g.lineTo(360, 640); g.closePath(); });
    ink(coat, () => { g.moveTo(215, 390); g.quadraticCurveTo(300, 360, 385, 390); g.lineTo(405, 680); g.quadraticCurveTo(300, 700, 195, 680); g.closePath(); });
    ink(coat, () => { g.moveTo(215, 400); g.quadraticCurveTo(160, 520, 175, 640); g.lineTo(215, 640); g.quadraticCurveTo(220, 520, 245, 450); g.closePath(); });
    ink(coat, () => { g.moveTo(385, 400); g.quadraticCurveTo(440, 520, 425, 640); g.lineTo(385, 640); g.quadraticCurveTo(380, 520, 355, 450); g.closePath(); });
    g.fillStyle = "#f2d24a"; for (const y of [440, 500, 560, 620]) { g.beginPath(); g.arc(300, y, 9, 0, 7); g.fill(); }
  }
  // egg-shaped head: wider jaw, narrower crown, slight chin
  ink(skin, () => { g.moveTo(300, 175); g.bezierCurveTo(385, 175, 395, 260, 385, 310); g.bezierCurveTo(375, 365, 335, 385, 300, 385); g.bezierCurveTo(255, 385, 215, 360, 212, 300); g.bezierCurveTo(208, 240, 230, 175, 300, 175); });
  if (!headOnly) {
    g.fillStyle = "#140c14"; g.beginPath(); g.ellipse(270, 280, 8, 12, 0, 0, 7); g.fill(); g.beginPath(); g.ellipse(335, 280, 8, 12, 0, 0, 7); g.fill();
    g.lineWidth = 7; g.strokeStyle = "#140c14"; g.beginPath(); g.arc(305, 320, 26, 0.3, Math.PI - 0.5); g.stroke();
    ink("#1e1e2e", () => { g.moveTo(232, 205); g.lineTo(245, 60); g.lineTo(360, 60); g.lineTo(372, 205); g.closePath(); });
  }
  return c;
}

function sprite(coat: string, skin: string, x: number, z: number, h = 2.0) {
  const draw = figure(coat, skin);
  let mat: THREE.Material;
  if (AFTER) {
    const nrm = bulgeNormalMap(draw, { parts: [{ mask: figure(coat, skin, true), weight: 1.2, radius: 18 }] });
    mat = characterMaterial(draw, nrm, 0.08);
  } else {
    const map = new THREE.CanvasTexture(draw); map.colorSpace = THREE.SRGBColorSpace;
    mat = new THREE.MeshLambertMaterial({ map, emissiveMap: map, emissive: new THREE.Color(1, 1, 1), emissiveIntensity: 0.36, alphaTest: 0.5 });
  }
  const m = new THREE.Mesh(new THREE.PlaneGeometry(h * 0.6, h), mat);
  m.position.set(x, 1.78 + h / 2 - h * 0.025, z);
  m.castShadow = true; m.receiveShadow = AFTER;
  m.customDepthMaterial = new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking, map: (mat as any).map, alphaTest: 0.5 });
  scene.add(m); return m;
}
const sprites = [sprite("#c8282e", "#f0b48a", 0.2, 2.6), sprite("#2a5ac8", "#c98a5a", 2.6, 1.5), sprite("#c8282e", "#f5c49a", 6.5, 2.2), sprite("#c8282e", "#e0a070", 9.5, 1.7)];
for (const s of sprites) s.lookAt(camera.position.x, s.position.y, camera.position.z);

// ---------- lights ----------
const golden = LIGHT === "golden";
const night = LIGHT === "night";
const sun = new THREE.DirectionalLight(night ? "#8fa8ff" : golden ? "#ffb070" : (AFTER ? "#ffe2b8" : "#fff4e0"), night ? 3.0 : AFTER ? (golden ? 4.8 : 4.2) : 2.2);
sun.position.set(-34, golden ? 14 : 34, 6); sun.target.position.set(2, 0, 0); scene.add(sun.target);
sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048);
Object.assign(sun.shadow.camera, { left: -30, right: 30, top: 30, bottom: -30, near: 1, far: 150 });
sun.shadow.bias = -0.0004; sun.shadow.normalBias = 0.03; scene.add(sun);
const hemi = AFTER
  ? new THREE.HemisphereLight(night ? "#5a6ad0" : golden ? "#8a7ad8" : "#9cc4ff", night ? "#2a2478" : golden ? "#4a2f8a" : "#5a4aa8", night ? 2.4 : golden ? 1.0 : 1.1)
  : new THREE.HemisphereLight("#ffffff", "#d8d0c0", 1.6);
scene.add(hemi);
const fill = new THREE.DirectionalLight(AFTER ? "#7a86ff" : "#ffffff", AFTER ? 0.35 : 0.6); fill.position.set(30, 10, -10); scene.add(fill);

if (night) { // warm window light pool next to the blue soldier
  const pool = new THREE.PointLight("#ffb347", 40, 10, 1.6); pool.position.set(4.2, 3.6, 3.4); scene.add(pool);
}
scene.fog = night ? new THREE.Fog("#1a2050", 120, 700) : AFTER ? new THREE.Fog(golden ? "#e8a080" : "#bcd8f0", 180, 900) : new THREE.Fog("#d8e8f5", 90, 560);

// ---------- post ----------
const composer = new EffectComposer(renderer, { frameBufferType: THREE.HalfFloatType, multisampling: 4 });
composer.addPass(new RenderPass(scene, camera));
const ink = new InkEffect({ thickness: 2 * (W / 1080) }); // 2 px at 1080 wide -> 1 px at 540
ink.setCamera(camera, H);
const focusDist = camera.position.distanceTo(sprites[1].position);
const dof = new DepthOfFieldEffect(camera, { worldFocusDistance: focusDist, worldFocusRange: focusDist * 0.9, bokehScale: 3.0, resolutionScale: 0.5 });
const bloom = new BloomEffect({ intensity: 0.3, luminanceThreshold: 0.86, mipmapBlur: true });
const tone = new ToneMappingEffect({ mode: ToneMappingMode.NEUTRAL });
if (V === "before") {
  composer.addPass(new EffectPass(camera, dof));
  composer.addPass(new EffectPass(camera, bloom, tone));
} else {
  composer.addPass(new EffectPass(camera, ink));
  if (DOF) composer.addPass(new EffectPass(camera, dof));
  const effects: any[] = [bloom, tone];
  if (V === "after") effects.push(new GradeEffect(night ? GRADE_NIGHT : golden ? GRADE_GOLDEN : GRADE_DAY));
  composer.addPass(new EffectPass(camera, ...effects));
}

// shadow map + DoF need a couple of frames to settle
let n = 0;
function tick() { composer.render(); if (++n < 4) requestAnimationFrame(tick); else (window as any).__done = true; }
requestAnimationFrame(tick);
