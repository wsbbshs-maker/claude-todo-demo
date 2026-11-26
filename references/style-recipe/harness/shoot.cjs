// node shoot.cjs <outdir> [variant:light ...]   e.g. node shoot.cjs out before:day after:day after:golden
const { chromium } = require("playwright");
const path = require("path");
const fs = require("fs");
(async () => {
  const out = process.argv[2] || "out";
  const variants = process.argv.slice(3).length ? process.argv.slice(3) : ["before:day", "inkonly:day", "after:day", "after:golden"];
  fs.mkdirSync(out, { recursive: true });
  const browser = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
  const page = await browser.newPage({ viewport: { width: 540, height: 960 }, deviceScaleFactor: 1 });
  const logs = [];
  page.on("console", (m) => logs.push(`[${m.type()}] ${m.text()}`));
  page.on("pageerror", (e) => logs.push(`[pageerror] ${e.message}`));
  const html = "file://" + path.resolve(__dirname, "index.html");
  for (const v of variants) {
    const [variant, light] = v.split(":");
    const [lt, extra] = (light || "day").split("+");
    await page.goto(`${html}?v=${variant}&light=${lt}${extra ? "&" + extra : ""}`);
    await page.waitForFunction(() => window.__done === true, null, { timeout: 120000 });
    await page.locator("canvas").screenshot({ path: path.join(out, `${variant}_${light.replace(/[^a-z0-9]+/gi, "-")}.png`) });
    console.log("shot", variant, light);
  }
  for (const l of logs) if (!/GPU stall|Automatic fallback|swiftshader/i.test(l)) console.log(l);
  await browser.close();
})();
