// Captures the Cityloom UI for the case study from a local Cityloom checkout, offline, using the
// same fixtures as Cityloom's own browser tests (a Plateau Mont-Royal metro tile and basemap).
// Usage: node scripts/capture_screenshots.mjs <cityloom-checkout> [base-url]
//   base-url defaults to http://127.0.0.1:8137 (run `just serve` in the checkout first)
import { chromium } from "playwright";
import { readFileSync } from "node:fs";
import { mkdir } from "node:fs/promises";
import path from "node:path";

const checkout = process.argv[2];
if (!checkout) {
  console.error("usage: capture_screenshots.mjs <cityloom-checkout> [base-url]");
  process.exit(2);
}
const base = process.argv[3] ?? "http://127.0.0.1:8137";
const out = new URL("../assets/screenshots/", import.meta.url).pathname;
const pbf = readFileSync(path.join(checkout, "e2e/fixtures/plateau.osm.pbf"));
const tiles = readFileSync(path.join(checkout, "e2e/fixtures/plateau.pmtiles"));

await mkdir(out, { recursive: true });
const browser = await chromium.launch({ args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"] });
const context = await browser.newContext({
  viewport: { width: 1440, height: 900 },
  deviceScaleFactor: 1,
  locale: "en-CA",
  reducedMotion: "reduce",
});
await context.addInitScript(() => {
  try {
    if (localStorage.getItem("cityloom-lang") === null) localStorage.setItem("cityloom-lang", "en");
  } catch {
    // storage blocked: the page falls back to its own default
  }
});

// Serve the basemap as a static host with range support does.
await context.route("**/data/basemap/montreal.pmtiles", async (route) => {
  const range = /bytes=(\d+)-(\d*)/.exec(route.request().headers()["range"] ?? "");
  if (!range) return route.fulfill({ body: tiles, headers: { "accept-ranges": "bytes" } });
  const start = Number(range[1]);
  const end = Math.min(range[2] ? Number(range[2]) : tiles.length - 1, tiles.length - 1);
  await route.fulfill({
    status: 206,
    body: tiles.subarray(start, end + 1),
    headers: { "content-range": `bytes ${start}-${end}/${tiles.length}`, "accept-ranges": "bytes" },
  });
});
await context.route("**/data/metro/index.json", (route) =>
  route.fulfill({ json: { lon0: -73.6078, lat0: 45.5161, dlon: 0.0257, dlat: 0.018, tiles: ["0_0"] } }),
);
await context.route("**/data/metro/0_0.osm.pbf", (route) => route.fulfill({ body: pbf }));
await context.route("https://overpass-api.de/**", (route) => route.abort());

const page = await context.newPage();
const shot = async (name) => {
  await page.waitForTimeout(1200);
  await page.screenshot({ path: `${out}${name}.png` });
  console.log(`captured ${name}`);
};

// The map, then the editors by the addresses the map gives its places.
await page.goto(`${base}/map.html`);
await page.waitForFunction(() => {
  const m = window.cityloomMap;
  return !!m && !!m.getSource("places") && m.areTilesLoaded() && m.querySourceFeatures("places").length > 0;
});
await page.waitForFunction(() => !window.cityloomMap.isMoving());
const places = await page.evaluate(() => {
  const hots = new Set();
  for (const f of window.cityloomMap.querySourceFeatures("places")) hots.add(f.properties.hot);
  const hrefs = (kind, file, param) =>
    [...hots]
      .filter((h) => h.startsWith(`${kind}-`))
      .map((h) => Number(h.slice(2)))
      .sort((a, b) => a - b)
      .map((uid) => `${file}?${param}=${uid}`);
  return { junctions: hrefs("j", "intersection.html", "junction"), streets: hrefs("s", "street.html", "street") };
});
await shot("map");
await page.goto(`${base}/${places.streets[0]}`);
await shot("street");
await page.goto(`${base}/${places.junctions[0]}`);
await shot("intersection");
await page.goto(`${base}/`);
await shot("home");

await browser.close();
