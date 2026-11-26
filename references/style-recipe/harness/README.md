# Test harness (stand-in scene, not our film)

Needs three@0.175.0, postprocessing@6.37.2, esbuild, and Playwright with Chromium.

```bash
npm i three@0.175.0 postprocessing@6.37.2 esbuild   # in any folder; point NODE_PATH at its node_modules
NODE_PATH=<that>/node_modules npx esbuild main.ts --bundle --format=iife --outfile=bundle.js
node shoot.cjs out before:day inkonly:day+dof=0 after:day after:golden after:night
```
Variants: `before` (approx. current setup), `inkonly` (new lighting, no grade), `after` (full recipe).
Light: `day`, `golden`, `night`. Extra URL params after `+`, e.g. `dof=0`.
