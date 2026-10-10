# Landovskis Forge

Portfolio site for Landovskis Forge, built with [Zola](https://www.getzola.org) and published to
GitHub Pages at <https://landovskisforge.ca>. Bilingual: English at `/`, French (fr-CA) at `/fr/`.

## Commands

```sh
brew install zola just actionlint           # once
npm ci && npx playwright install chromium   # once, for the accessibility audit
just serve     # dev server
just check     # i18n parity, contrast, zola check, build, smoke test
just a11y      # axe + reflow + motion audit (needs the npm setup above)
just ci        # check + a11y, exactly what CI runs
```

## Editing content

- UI strings: `[translations]` (English) and `[languages.fr.translations]` (French) in `config.toml`.
- Page copy: `content/**/*.md` with a French twin `*.fr.md`. Front matter keys must match in both
  files; values must stay on one line (`scripts/check_i18n.py` enforces this).
- Always edit EN and FR in the same commit. In French use a non-breaking space before `: ; ! ?` and
  inside `« »`: write ` ` inside front matter strings and a real U+00A0 character in Markdown
  bodies.
- Add a project: add `content/projects/<name>.md` and `<name>.fr.md`, then link it from the home
  template.
- Screenshots: serve a local Cityloom build (`just serve` in its checkout), then
  `node scripts/capture_screenshots.mjs <path to the Cityloom checkout>`. It uses Cityloom's own
  e2e fixtures, so no large map data is needed.

## Bumping tool versions

Zola and just are pinned in `.github/workflows/ci.yml` and `deploy.yml` (`tool: just@X,zola@Y`);
Dependabot does not track them. To bump, change both files, run `just ci` locally with the same
versions, and commit. `scripts/test_workflows.py` fails if a tool is left unpinned.

## Turning on the live demo

When <https://cityloom.app> is live: set `cityloom_demo_enabled = true` under `[extra]` in
`config.toml` and remove the `skip_prefixes` line from `[link_checker]`.

## Setting the contact email

Set `contact_email` under `[extra]` in `config.toml`. Leave it empty to show GitHub only. The
address is published on a public page.

## One-time GitHub and DNS setup

1. Repository Settings → Pages → Source: **GitHub Actions**.
2. Verify the domain first (Account Settings → Pages → Add a domain), then Settings → Pages →
   Custom domain: `landovskisforge.ca`; enable **Enforce HTTPS** once the certificate is issued.
3. DNS at the registrar, apex: four `A` records `185.199.108.153`, `185.199.109.153`,
   `185.199.110.153`, `185.199.111.153` (optionally `AAAA` `2606:50c0:8000::153` through
   `2606:50c0:8003::153`); `www`: a `CNAME` to `<github-user>.github.io`.
4. Branch protection on `main`: require the `site` check.

A `CNAME` file is not needed: Actions-based Pages deploys ignore it.

## Licences

JetBrains Mono is under the SIL Open Font License (`static/fonts/OFL.txt`). Cityloom screenshots
show OpenStreetMap data (© OpenStreetMap contributors).
