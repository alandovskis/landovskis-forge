# Landovskis Forge portfolio site: design

Date: 2026-10-10
Status: awaiting review

## 1. Purpose and audience

A product showcase for **Landovskis Forge**, a development portfolio. The only project so far is
**Cityloom** (<https://github.com/alandovskis/cityloom>). The audience is potential employers.
Success: an employer can understand what Cityloom is, see it, judge the engineering quality behind
it, try it, and contact the author, in a couple of minutes and in either English or French.

## 2. Decisions already made

| Topic | Decision |
|---|---|
| Generator | **Zola** (Rust static site generator, single binary, plain HTML/CSS output, no WASM). Leptos SSG was rejected as disproportionate for a content site. |
| Hosting | GitHub Pages, custom domain `landovskisforge.ca` (via `static/CNAME`). |
| Languages | Bilingual **EN/FR**, English at `/`, French at `/fr/`. French is written as **fr-CA** (`.ca` domain, Montréal-focused project). |
| Visual direction | High-tech, **dark forge shell**. Cityloom is shown in its own light UI inside framed screenshots. |
| Live demo | `cityloom.app`, **not live yet** (no response as of 2026-10-10). The "Try it" link is driven by one config value so it can be enabled without template changes. |
| Content honesty | No invented metrics, users, testimonials or benchmarks. Every claim traces to the Cityloom repo (`README.md`, `PRODUCT.md`). Copy is a draft for the author to edit. |

## 3. Cityloom facts the content may use

Taken from the repository, not invented:

- "Streetmix at city scale": residents compose and compare whole-city scenarios.
- Three surfaces: city map (`map.html`), street cross-section editor (`street.html`), intersection
  editor (`intersection.html`). A home page finds a place by name; streets come from OpenStreetMap
  (Nominatim, Overpass, osm2streets). Edits persist in browser storage.
- Stack: Rust compiled to WebAssembly, Leptos (client-side rendered), Fluent for i18n (bilingual),
  Playwright end-to-end tests, `just` task runner, GitHub Actions CI, Dependabot.
- Architecture: vertical slices (`street/`, `junction/`, `map/`, `city/`, `shell/`, `shared/`); a
  view-model has no page in it and reaches the browser only through ports, so it is tested on the
  host with fakes; slices reach each other only through models.
- Open source code and open data are binding product principles. Native Android and iOS apps are
  planned after the web release.
- Status: early. Catalogue widths, rules and capacity rates are **synthetic placeholders**; this
  must be stated plainly on the case study page.
- The repository currently has no licence file; the site must not claim a specific licence.

## 4. Information architecture

```
/                       Home (EN)            /fr/                      Accueil (FR)
/projects/cityloom/     Case study (EN)      /fr/projects/cityloom/    Étude de cas (FR)
/404.html               Not found            (bilingual body, links to both homes)
```

Projects are Markdown files under `content/projects/`; a second project is a new file, not new
templates.

### Home

1. **Hero:** "Landovskis Forge", a one-line pitch, buttons *See Cityloom* (case study) and *Try it*
   (`cityloom.app`, shown only when enabled in config).
2. **Featured project:** Cityloom card with the pitch, a hero screenshot and spec-style tags
   (Rust, WebAssembly, Leptos, OpenStreetMap).
3. **About the forge:** two or three sentences on who builds this and how; values taken from the
   repo: tested, accessible, bilingual, open data.
4. **Contact and footer:** contact link(s), GitHub link, language switcher.

### Cityloom case study

Summary with *Try it* and *Source* buttons; problem and audience; the three surfaces with one
screenshot each; "How it's built" (vertical slices and ports diagram, testing and CI); what is open
(stack, OSM data, Montréal basemap pipeline); status, including the synthetic-data statement.

## 5. Visual design

- **Palette:** near-black blue-grey background (~`#0B0E13`), slightly lighter panels, 1px hairline
  borders, cool off-white text, muted blue-grey secondary text, and **one accent, ember orange**
  (~`#FF8A3D`) for links, focus rings and key labels. Cityloom's blue appears only inside
  screenshots. Final values are verified for WCAG 2.2 AA contrast.
- **Type:** self-hosted JetBrains Mono (OFL, Regular and Bold WOFF2) for headings, labels and
  metadata; the system UI sans stack for body text (no body-font download).
- **Motifs:** faint engineering grid behind the hero; spec-sheet labels (`01 / PROJECT`,
  `STACK: RUST · WASM`); screenshots in thin-bordered window frames with a soft ember-tinted glow.
  No stock imagery, neon or decorative gradients.
- **Motion:** one restrained fade-and-rise on load plus hover/focus states; all disabled under
  `prefers-reduced-motion`.
- **Responsive:** mobile first; single column on small screens; no fixed-width labels (French runs
  20–30% longer).
- **Logo:** none exists; a text wordmark is used.

## 6. Technical design

### Build

Zola with hand-written templates and Sass. No JS framework. Pages work fully without JavaScript.
Zola and every other dependency are pinned to their latest releases at implementation time.

### Internationalisation

- Zola multilingual mode, languages `en` (default) and `fr`.
- UI strings live in Zola's native translation tables in `config.toml` (`[translations]` for EN,
  `[languages.fr.translations]` for FR), referenced by ASCII key via `trans()`; no hardcoded
  user-facing strings in templates; no string concatenation (named `{placeholders}` filled with
  Tera's `replace`).
- Content pages exist per language (`_index.md` / `_index.fr.md`, etc.). Page copy that is not
  Markdown body lives in front matter `[extra]`, with identical keys in both languages.
- Language switcher is a plain link to the translated page; `<html lang>` and `hreflang`
  alternates are set per page; the choice needs no JS to work.
- **Parity check** (script run by `just check` and CI): the EN and FR translation tables have
  identical keys and placeholders, every content file has its counterpart, and counterparts have
  identical front matter keys.
- French typography: non-breaking space before `: ; ! ?` and inside `« »`.

### Assets and privacy

Fonts self-hosted. Screenshots are PNG sources under `assets/screenshots/`, converted to WebP by
Zola's `resize_image` with explicit width/height. No third-party requests,
analytics or cookies.

### Quality bar

WCAG 2.2 AA: contrast, keyboard navigation, visible focus, skip link, semantic landmarks, alt text
in both languages. OpenGraph/Twitter tags, sitemap, Atom feed and `robots.txt` (all generated by Zola).

### Screenshots

Captured with Playwright from a local build of Cityloom. The street and junction editors work
without the large tile data. The map page needs the basemap (1.2 GB Geofabrik download plus
Planetiler); it is **not** fetched without the author's go-ahead, and the map screenshot is skipped
until then.

### Repository layout

```
config.toml
content/{_index.md, _index.fr.md, projects/cityloom.md, projects/cityloom.fr.md}
templates/  sass/
static/{fonts, CNAME}
assets/screenshots/              # PNG sources, processed by Zola
scripts/                         # i18n parity, contrast, smoke, a11y checks (+ tests)
justfile
.github/workflows/{ci.yml, deploy.yml}
.github/dependabot.yml
```

### CI/CD (GitHub Actions, per the `ci` rules)

- `ci.yml` (`pull_request`, `push` to `main`, `workflow_dispatch`): `zola check`, i18n parity
  check, build. Top-level `permissions: contents: read`, `concurrency` with
  `cancel-in-progress`, `timeout-minutes` per job. A final aggregate job is the single required
  check.
- `deploy.yml` (`push` to `main`): build with pinned latest Zola, publish with the official
  `actions/upload-pages-artifact` and `actions/deploy-pages`; `pages: write` and `id-token: write`
  only on the deploy job; `github-pages` environment.
- Actions pinned to a commit SHA (third-party) or major version (first-party), current releases
  looked up at implementation. Dependabot for Actions.
- All logic lives in the `justfile` (`just serve`, `just build`, `just check`); workflows call it.
- One-time manual steps (documented in the README): set Pages source to GitHub Actions, set the
  custom domain, configure DNS for `landovskisforge.ca`, enable HTTPS enforcement.

## 7. Testing

- Parity check (above) has its own tests with known-bad fixtures.
- `zola check` for internal and external links.
- Build smoke test: both languages produce the expected pages, `lang` attributes and `hreflang`
  links.
- Accessibility: automated axe scan of built pages in both languages; manual keyboard pass.
- Visual check in a real browser at mobile and desktop widths, in EN and FR, before sign-off.

## 8. Out of scope

Blog, CMS, comments, analytics, contact form (needs a backend), light theme or theme toggle,
multiple projects beyond the Cityloom entry, embedding the live Cityloom app.

## 9. Open decisions

1. **Contact method.** Not yet chosen: `mailto:` (which address), LinkedIn, GitHub only, or a
   combination. It is a config value; the address is public once published, so it must come from
   the author. Needed before the first deploy.
2. **Map screenshot.** Whether to download the 1.2 GB basemap data to capture the map page.
3. **`cityloom.app` go-live.** The *Try it* button stays hidden until the author enables it.
4. **Domain DNS and Pages settings** are performed by the author in GitHub and the registrar.
