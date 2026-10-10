// Audits the built site. Usage: node scripts/a11y.mjs <dir>
//   - axe (WCAG 2.0/2.1/2.2 A and AA) at desktop and 320 px wide
//   - no horizontal scroll at 320 px (WCAG reflow), in both languages
//   - .reveal elements are fully visible with reduced motion and after the animation
import { chromium } from "playwright";
import AxeBuilder from "@axe-core/playwright";
import http from "node:http";
import { readFile } from "node:fs/promises";
import path from "node:path";

const root = path.resolve(process.argv[2] ?? "target/a11y");
const port = 4173;
const pages = ["/", "/fr/", "/projects/cityloom/", "/fr/projects/cityloom/", "/404.html"];
const sizes = [
  { width: 1280, height: 900 },
  { width: 320, height: 640 },
];
const types = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css",
  ".webp": "image/webp",
  ".png": "image/png",
  ".woff2": "font/woff2",
  ".xml": "application/xml",
  ".txt": "text/plain",
};

const server = http.createServer(async (req, res) => {
  const requested = decodeURIComponent(new URL(req.url, "http://x").pathname);
  const rel = requested.endsWith("/") ? requested + "index.html" : requested;
  const file = path.join(root, path.normalize(rel));
  try {
    if (!file.startsWith(root)) throw new Error("outside root");
    const body = await readFile(file);
    res.writeHead(200, { "content-type": types[path.extname(file)] ?? "application/octet-stream" }).end(body);
  } catch {
    res.writeHead(404, { "content-type": types[".html"] }).end(await readFile(path.join(root, "404.html")));
  }
});
await new Promise((resolve) => server.listen(port, "127.0.0.1", resolve));

const failures = [];
const browser = await chromium.launch();

for (const size of sizes) {
  const context = await browser.newContext({ viewport: size });
  for (const url of pages) {
    const page = await context.newPage();
    await page.goto(`http://127.0.0.1:${port}${url}`, { waitUntil: "networkidle" });
    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"])
      .analyze();
    for (const v of results.violations) {
      failures.push(`${url} @${size.width}px axe ${v.id}: ${v.help} (${v.nodes.length} node(s))`);
    }
    if (size.width === 320) {
      const overflow = await page.evaluate(
        () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
      );
      if (overflow > 0) failures.push(`${url} @320px scrolls horizontally by ${overflow}px`);
    }
    await page.close();
  }
  await context.close();
}

for (const reducedMotion of ["reduce", "no-preference"]) {
  const context = await browser.newContext({ viewport: sizes[0], reducedMotion });
  for (const url of pages) {
    const page = await context.newPage();
    await page.goto(`http://127.0.0.1:${port}${url}`, { waitUntil: "networkidle" });
    await page.waitForTimeout(1500);
    const hidden = await page.$$eval(".reveal", (els) =>
      els.filter((el) => getComputedStyle(el).opacity !== "1").length,
    );
    if (hidden > 0) failures.push(`${url} (${reducedMotion}): ${hidden} .reveal element(s) not fully visible`);
    await page.close();
  }
  await context.close();
}

await browser.close();
server.close();

if (failures.length) {
  console.error(failures.join("\n"));
  process.exit(1);
}
console.log("a11y ok");
