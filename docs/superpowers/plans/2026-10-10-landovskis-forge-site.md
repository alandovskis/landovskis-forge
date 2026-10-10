# Landovskis Forge Site Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and deploy the bilingual (EN/FR) dark "forge" portfolio site for Landovskis Forge, showcasing Cityloom, with Zola on GitHub Pages at landovskisforge.ca.

**Architecture:** Zola generates plain HTML/CSS from Markdown content, hand-written Tera templates and Sass. UI strings live in Zola's `[translations]` tables in `config.toml`; page copy lives in per-language Markdown files with identical front matter keys. Small stdlib-only Python scripts enforce EN/FR parity, colour contrast and built-site invariants; a Playwright + axe script audits accessibility. GitHub Actions runs the checks on PRs and deploys `main` to Pages.

**Tech Stack:** Zola (latest, 0.23.x at time of writing), Sass via Zola, Python 3.9+ stdlib (scripts), Node + Playwright + `@axe-core/playwright` (a11y audit), `just`, GitHub Actions, JetBrains Mono (OFL).

**Spec:** `docs/superpowers/specs/2026-10-10-landovskis-forge-site-design.md`

## Global Constraints

- Static site generator is **Zola**; output is plain HTML/CSS; **no JS framework and no `<script>` tags** in built pages.
- **Bilingual EN/FR**: English at `/`, French at `/fr/`, French written as **fr-CA**. No hardcoded user-facing strings in templates; no string concatenation (named `{placeholders}` + Tera `replace`). EN and FR change in the same commit. French uses a non-breaking space (` `) before `: ; ! ?` and inside `« »`.
- Visual direction: **dark forge shell**; one accent, **ember orange** (`#ff8a3d`); Cityloom's blue appears only inside screenshots; JetBrains Mono for headings/labels, system UI sans stack for body; motion disabled under `prefers-reduced-motion`; mobile first.
- **WCAG 2.2 AA**: contrast, keyboard navigation, visible focus, skip link, semantic landmarks, alt text in both languages.
- **No third-party requests, analytics or cookies**; fonts self-hosted.
- **No invented metrics, users, testimonials or benchmarks**; every Cityloom claim traces to <https://github.com/alandovskis/cityloom> (`README.md`, `PRODUCT.md`). State plainly that catalogue data is synthetic placeholder data. Do **not** claim a licence (the repo has none).
- "Try it" (`cityloom.app`) is **hidden** until `extra.cityloom_demo_enabled = true`.
- CI is **GitHub Actions** only; `permissions: contents: read` at top level, extra permissions per job; `concurrency`; `timeout-minutes` on every job; first-party actions pinned to the major version, third-party actions to a commit SHA; logic lives in the `justfile`, workflows call it.
- Always use the latest version of any dependency.
- Hosting: GitHub Pages, custom domain `landovskisforge.ca` set in repository settings (a `CNAME` file is ignored by Actions-based Pages deploys, so none is committed).
- Every commit message uses a conventional-commit subject and ends with the trailer line `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>` (given as a second `-m` argument in the steps below).
- Scripts under `scripts/` must run on Python 3.9 (the macOS system `python3`): no `tomllib`, no `X | Y` type hints.

## Review Focus

Inputs and conditions the spec implies but does not spell out; each has a pinning check in the named task.

1. **The 404 page is served from any URL depth** (e.g. `/fr/nope/x`), so its CSS and links must be absolute, not relative. (Task 2 smoke test, Task 3 stylesheet link.)
2. **A page with no counterpart in the other language** would give a dead switcher link or an untranslated page. (Task 1 parity check; the switcher only renders for translations that exist, Task 2.)
3. **`cityloom.app` is not live**: no dead "Try it" button may ship while disabled, and `zola check` must not fail on it. (Task 2 `link_checker`, Task 4 smoke test.)
4. **French text is 20–30% longer** and must not overflow or force horizontal scroll at 320 px. (Task 7 reflow check.)
5. **Entrance animation must never leave content invisible** (reduced-motion users, animation not running). (Task 7 opacity check.)

---

## File Structure

```
.gitignore                         ignores build output and caches
justfile                           all commands; CI calls these
config.toml                        Zola config, EN+FR translation tables, site extras
content/_index.md, _index.fr.md    home copy (front matter only)
content/projects/_index.md, .fr.md projects section (not rendered)
content/projects/cityloom.md, .fr.md  case study
templates/base.html                document shell, head, header, footer, language switcher
templates/index.html               home
templates/project.html             case study
templates/404.html                 bilingual not-found
templates/partials/contact_links.html, project_actions.html, project_card.html
templates/macros/image.html        WebP screenshot macro
sass/main.scss + _tokens.scss _fonts.scss _base.scss _layout.scss
static/fonts/JetBrainsMono-{Regular,Bold}.woff2, OFL.txt
assets/screenshots/{home,street,intersection}.png   sources, processed by Zola
scripts/tomlite.py                 one-line-value TOML subset parser (shared)
scripts/check_i18n.py + test_check_i18n.py
scripts/check_contrast.py + test_check_contrast.py
scripts/smoke_test.py              built-site invariants
scripts/a11y.mjs                   Playwright + axe audit
scripts/capture_screenshots.mjs    Cityloom screenshot capture
package.json, package-lock.json    a11y/screenshot tooling
.github/workflows/{ci,deploy}.yml, .github/dependabot.yml
README.md
```

---

### Task 1: Toolchain and EN/FR parity checker

**Files:**
- Create: `scripts/tomlite.py`, `scripts/check_i18n.py`, `scripts/test_check_i18n.py`, `.gitignore`

**Interfaces:**
- Produces: `tomlite.parse(text: str, source: str) -> dict[str, dict[str, str]]` (table name → key → raw value; top-level keys under `""`; raises `ValueError` on multi-line strings or unparsable lines); `tomlite.front_matter(text: str, source: str) -> dict[str, dict[str, str]]`.
- Produces: `check_i18n.check_translations(config_text: str) -> list[str]`, `check_i18n.check_content(content_dir: pathlib.Path) -> list[str]`, `check_i18n.main(root: pathlib.Path) -> int` (0 = ok). Each problem is one human-readable string.

- [ ] **Step 1: Install Zola and verify**

Run: `brew install zola && zola --version`
Expected: prints `zola 0.23.x` or newer.

- [ ] **Step 2: Create `.gitignore`**

```gitignore
public/
target/
node_modules/
static/processed_images/
__pycache__/
.DS_Store
```

- [ ] **Step 3: Write the failing tests** — `scripts/test_check_i18n.py`

```python
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import check_i18n
import tomlite

CONFIG_OK = """\
base_url = "https://example.test"

[translations]
hello = "Hello"
year = "© {year} Forge"

[languages.fr]
title = "Forge"

[languages.fr.translations]
hello = "Bonjour"
year = "© {year} Forge"
"""


class TomlitePlaceholderTests(unittest.TestCase):
    def test_parses_tables_and_top_level_keys(self):
        tables = tomlite.parse(CONFIG_OK, "config.toml")
        self.assertEqual(tables[""]["base_url"], '"https://example.test"')
        self.assertEqual(tables["translations"]["hello"], '"Hello"')
        self.assertEqual(tables["languages.fr.translations"]["hello"], '"Bonjour"')

    def test_rejects_multiline_strings(self):
        with self.assertRaises(ValueError):
            tomlite.parse('a = """x\ny"""\n', "f")

    def test_rejects_unparsable_lines(self):
        with self.assertRaises(ValueError):
            tomlite.parse("[t]\n  \"orphan\",\n", "f")

    def test_front_matter_extracts_plus_delimited_block(self):
        text = '+++\ntitle = "T"\n[extra]\nk = "v"\n+++\nbody\n'
        tables = tomlite.front_matter(text, "p.md")
        self.assertEqual(tables["extra"]["k"], '"v"')

    def test_front_matter_requires_block(self):
        with self.assertRaises(ValueError):
            tomlite.front_matter("no front matter", "p.md")


class TranslationTests(unittest.TestCase):
    def test_matching_tables_pass(self):
        self.assertEqual(check_i18n.check_translations(CONFIG_OK), [])

    def test_key_missing_in_french(self):
        text = CONFIG_OK.replace('hello = "Bonjour"\n', "")
        problems = check_i18n.check_translations(text)
        self.assertEqual(len(problems), 1)
        self.assertIn("hello", problems[0])
        self.assertIn("missing in fr", problems[0])

    def test_key_missing_in_english(self):
        text = CONFIG_OK.replace('[translations]\nhello = "Hello"\n', "[translations]\n")
        problems = check_i18n.check_translations(text)
        self.assertEqual(len(problems), 1)
        self.assertIn("missing in en", problems[0])

    def test_placeholder_mismatch(self):
        head, _, tail = CONFIG_OK.rpartition('year = "© {year} Forge"')
        text = head + 'year = "© {annee} Forge"' + tail
        problems = check_i18n.check_translations(text)
        self.assertEqual(len(problems), 1)
        self.assertIn("placeholders", problems[0])

    def test_no_translation_table_is_a_problem(self):
        problems = check_i18n.check_translations('base_url = "x"\n')
        self.assertTrue(any("[translations]" in p for p in problems))


def write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


PAGE = '+++\ntitle = "T"\n[extra]\nk = "v"\n+++\n'


class ContentTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_paired_content_passes(self):
        write(self.root, "_index.md", PAGE)
        write(self.root, "_index.fr.md", PAGE)
        write(self.root, "projects/a.md", PAGE)
        write(self.root, "projects/a.fr.md", PAGE)
        self.assertEqual(check_i18n.check_content(self.root), [])

    def test_missing_french_counterpart(self):
        write(self.root, "a.md", PAGE)
        problems = check_i18n.check_content(self.root)
        self.assertEqual(len(problems), 1)
        self.assertIn("no French counterpart", problems[0])

    def test_missing_english_counterpart(self):
        write(self.root, "a.fr.md", PAGE)
        problems = check_i18n.check_content(self.root)
        self.assertEqual(len(problems), 1)
        self.assertIn("no English counterpart", problems[0])

    def test_front_matter_key_mismatch(self):
        write(self.root, "a.md", PAGE)
        write(self.root, "a.fr.md", PAGE.replace('k = "v"\n', ""))
        problems = check_i18n.check_content(self.root)
        self.assertEqual(len(problems), 1)
        self.assertIn("extra", problems[0])
        self.assertIn("k", problems[0])


class MainTests(unittest.TestCase):
    def test_main_reports_and_returns_nonzero(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root, "config.toml", CONFIG_OK.replace('hello = "Bonjour"\n', ""))
            write(root, "content/a.md", PAGE)
            self.assertEqual(check_i18n.main(root), 1)

    def test_main_returns_zero_when_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root, "config.toml", CONFIG_OK)
            write(root, "content/a.md", PAGE)
            write(root, "content/a.fr.md", PAGE)
            self.assertEqual(check_i18n.main(root), 0)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 4: Run tests to verify they fail**

Run: `python3 -m unittest discover -s scripts -p 'test_*.py'`
Expected: FAIL / ERROR with `ModuleNotFoundError: No module named 'check_i18n'`.

- [ ] **Step 5: Implement `scripts/tomlite.py`**

```python
"""A tiny parser for the TOML subset this site uses.

Only `[table]` / `[[table]]` headers and one-line `key = value` pairs are supported, which is all
the translation tables and front matter need. Values are returned as raw text. Anything else
(multi-line strings, multi-line arrays) is rejected loudly so that parity checks never silently
skip content.
"""
import re

TABLE_RE = re.compile(r'^\s*\[\[?([A-Za-z0-9_.\-"]+)\]\]?\s*(#.*)?$')
KEY_RE = re.compile(r"^\s*([A-Za-z0-9_\-]+)\s*=\s*(.*)$")
FRONT_MATTER_RE = re.compile(r"\A\+\+\+\n(.*?)\n\+\+\+\n", re.S)


def parse(text, source):
    """Return {table: {key: raw value}}; top-level keys live under the table name ''."""
    tables = {"": {}}
    current = ""
    for number, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if '"""' in line or "'''" in line:
            raise ValueError(f"{source}:{number}: multi-line strings are not supported")
        table = TABLE_RE.match(line)
        if table:
            current = table.group(1)
            tables.setdefault(current, {})
            continue
        key = KEY_RE.match(line)
        if key:
            tables[current][key.group(1)] = key.group(2)
            continue
        raise ValueError(f"{source}:{number}: cannot parse line: {line!r}")
    return tables


def front_matter(text, source):
    """Parse the `+++` delimited front matter block of a Zola content file."""
    match = FRONT_MATTER_RE.match(text)
    if not match:
        raise ValueError(f"{source}: no +++ front matter block")
    return parse(match.group(1), source)
```

- [ ] **Step 6: Implement `scripts/check_i18n.py`**

```python
#!/usr/bin/env python3
"""Check EN/FR parity: translation tables, content file pairs, and front matter keys."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import tomlite

PLACEHOLDER_RE = re.compile(r"\{[a-z_]+\}")


def check_translations(config_text):
    tables = tomlite.parse(config_text, "config.toml")
    english = tables.get("translations", {})
    french = tables.get("languages.fr.translations", {})
    if not english or not french:
        return ["config.toml: both [translations] and [languages.fr.translations] must exist"]
    problems = []
    for key in sorted(english.keys() - french.keys()):
        problems.append(f"translations: key '{key}' missing in fr")
    for key in sorted(french.keys() - english.keys()):
        problems.append(f"translations: key '{key}' missing in en")
    for key in sorted(english.keys() & french.keys()):
        en_ph = sorted(PLACEHOLDER_RE.findall(english[key]))
        fr_ph = sorted(PLACEHOLDER_RE.findall(french[key]))
        if en_ph != fr_ph:
            problems.append(f"translations: key '{key}' placeholders differ: en {en_ph} vs fr {fr_ph}")
    return problems


def _english_name(path):
    return path.with_name(path.name[: -len(".fr.md")] + ".md")


def check_content(content_dir):
    files = sorted(content_dir.rglob("*.md"))
    english = {p.relative_to(content_dir) for p in files if not p.name.endswith(".fr.md")}
    french = {_english_name(p).relative_to(content_dir) for p in files if p.name.endswith(".fr.md")}
    problems = []
    for rel in sorted(english - french):
        problems.append(f"content: {rel} has no French counterpart")
    for rel in sorted(french - english):
        problems.append(f"content: {rel} has no English counterpart")
    for rel in sorted(english & french):
        fr_rel = rel.with_name(rel.name[: -len(".md")] + ".fr.md")
        en_tables = tomlite.front_matter((content_dir / rel).read_text(encoding="utf-8"), str(rel))
        fr_tables = tomlite.front_matter((content_dir / fr_rel).read_text(encoding="utf-8"), str(fr_rel))
        for table in sorted(en_tables.keys() | fr_tables.keys()):
            en_keys = set(en_tables.get(table, {}))
            fr_keys = set(fr_tables.get(table, {}))
            if en_keys != fr_keys:
                problems.append(
                    f"content: {rel} front matter [{table or 'top level'}] keys differ: "
                    f"only en {sorted(en_keys - fr_keys)}, only fr {sorted(fr_keys - en_keys)}"
                )
    return problems


def main(root):
    config = (root / "config.toml").read_text(encoding="utf-8")
    problems = check_translations(config) + check_content(root / "content")
    for problem in problems:
        print(problem, file=sys.stderr)
    if problems:
        return 1
    print("i18n parity ok")
    return 0


if __name__ == "__main__":
    sys.exit(main(Path(__file__).resolve().parent.parent))
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `python3 -m unittest discover -s scripts -p 'test_*.py' -v`
Expected: all tests `ok`.

- [ ] **Step 8: Commit**

```bash
git add .gitignore scripts/tomlite.py scripts/check_i18n.py scripts/test_check_i18n.py
git commit -m "feat: add EN/FR parity checker" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Zola skeleton with bilingual shell and smoke test

**Files:**
- Create: `config.toml`, `justfile`, `templates/base.html`, `templates/index.html`, `templates/404.html`, `templates/partials/contact_links.html`, `content/_index.md`, `content/_index.fr.md`, `sass/main.scss`, `scripts/smoke_test.py`

**Interfaces:**
- Consumes: `tomlite.parse` (Task 1).
- Produces: base template blocks `content` (inside `<main id="main">`) and `page_title` (inside `<title>`); template globals `home_path` (`/` or `/fr/`), `lang_suffix` (`""` or `.fr`), `home_url`, `ctx` (current page/section or `false`); `partials/contact_links.html`; config extras `github_url`, `source_url`, `cityloom_demo_url`, `cityloom_demo_enabled`, `contact_email`; translation keys listed in Step 3.
- Produces: `scripts/smoke_test.py <public-dir>` exits non-zero on any violated invariant.

- [ ] **Step 1: Write the failing smoke test** — `scripts/smoke_test.py`

```python
#!/usr/bin/env python3
"""Smoke-test a built site: pages exist, languages are declared and linked, no scripts, no dead
demo link. Usage: smoke_test.py <public-dir>"""
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import tomlite

ROOT = Path(__file__).resolve().parent.parent

# (file, lang, counterpart file)
PAGES = [
    ("index.html", "en", "fr/index.html"),
    ("fr/index.html", "fr", "index.html"),
]
REQUIRED_FILES = ["404.html", "sitemap.xml", "robots.txt", "atom.xml", "fr/atom.xml", "main.css"]


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.lang = None
        self.canonical = None
        self.alternates = {}
        self.stylesheets = []
        self.hrefs = []
        self.h1 = 0
        self.scripts = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "html":
            self.lang = a.get("lang")
        elif tag == "h1":
            self.h1 += 1
        elif tag == "script":
            self.scripts += 1
        elif tag == "link":
            rel = a.get("rel")
            if rel == "canonical":
                self.canonical = a.get("href")
            elif rel == "alternate" and a.get("hreflang"):
                self.alternates[a["hreflang"]] = a.get("href")
            elif rel == "stylesheet":
                self.stylesheets.append(a.get("href"))
        elif tag == "a" and a.get("href"):
            self.hrefs.append(a["href"])


def load(path):
    page = Page()
    page.feed(path.read_text(encoding="utf-8"))
    return page


def main(public):
    problems = []
    config = tomlite.parse((ROOT / "config.toml").read_text(encoding="utf-8"), "config.toml")
    extra = config.get("extra", {})
    demo_url = extra.get("cityloom_demo_url", "").strip('"')
    demo_enabled = extra.get("cityloom_demo_enabled", "false") == "true"

    for name in REQUIRED_FILES:
        if not (public / name).is_file():
            problems.append(f"missing built file: {name}")

    pages = {}
    for name, lang, counterpart in PAGES:
        path = public / name
        if not path.is_file():
            problems.append(f"missing page: {name}")
            continue
        page = load(path)
        pages[name] = page
        if page.lang != lang:
            problems.append(f"{name}: <html lang> is {page.lang!r}, expected {lang!r}")
        if page.h1 != 1:
            problems.append(f"{name}: expected exactly one <h1>, found {page.h1}")
        for needed in ("en", "fr", "x-default"):
            if needed not in page.alternates:
                problems.append(f"{name}: missing hreflang={needed} alternate")
        if page.canonical is None or page.alternates.get(lang) != page.canonical:
            problems.append(f"{name}: canonical does not match its own hreflang alternate")
    for name, lang, counterpart in PAGES:
        if name in pages and counterpart in pages:
            other_lang = pages[counterpart].lang
            if pages[name].alternates.get(other_lang) != pages[counterpart].canonical:
                problems.append(f"{name}: hreflang={other_lang} does not point at {counterpart}")

    not_found = public / "404.html"
    if not_found.is_file():
        page = load(not_found)
        for link in page.stylesheets + page.hrefs:
            if not (link.startswith("http://") or link.startswith("https://")):
                problems.append(f"404.html: relative URL {link!r} breaks at nested paths")
        for name, _, _ in PAGES:
            if name in pages and pages[name].canonical not in page.hrefs:
                problems.append(f"404.html: does not link to {name}")

    for html in sorted(public.rglob("*.html")):
        page = load(html)
        rel = html.relative_to(public)
        if page.scripts:
            problems.append(f"{rel}: contains <script>; the site must work without JavaScript")
        if not demo_enabled and demo_url and any(h.rstrip("/") == demo_url.rstrip("/") for h in page.hrefs):
            problems.append(f"{rel}: links to {demo_url} while cityloom_demo_enabled is false")

    if demo_enabled and "index.html" in pages:
        if not any(h.rstrip("/") == demo_url.rstrip("/") for h in pages["index.html"].hrefs):
            problems.append("index.html: demo enabled but no link to the demo")

    for problem in problems:
        print(problem, file=sys.stderr)
    if problems:
        return 1
    print("smoke test ok")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: smoke_test.py <public-dir>", file=sys.stderr)
        sys.exit(2)
    sys.exit(main(Path(sys.argv[1])))
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python3 scripts/smoke_test.py public`
Expected: FAIL (non-zero) — the config and the built site do not exist yet (`FileNotFoundError` for `config.toml` is acceptable as the failing state).

- [ ] **Step 3: Create `config.toml`**

```toml
base_url = "https://landovskisforge.ca"
title = "Landovskis Forge"
description = "Web software in Rust and WebAssembly, designed, built and tested end to end."
default_language = "en"
compile_sass = true
generate_feeds = true
feed_filenames = ["atom.xml"]

[link_checker]
# cityloom.app is not live yet; remove this prefix once it is.
skip_prefixes = ["https://cityloom.app"]
internal_level = "error"
external_level = "warn"

[extra]
github_url = "https://github.com/alandovskis"
source_url = "https://github.com/alandovskis/cityloom"
cityloom_demo_url = "https://cityloom.app"
cityloom_demo_enabled = false
contact_email = ""

[translations]
site_name = "Landovskis Forge"
site_description = "Web software in Rust and WebAssembly, designed, built and tested end to end."
skip_to_content = "Skip to content"
nav_main = "Main"
nav_cityloom = "Cityloom"
lang_name = "English"
cta_see_cityloom = "See Cityloom"
cta_try_it = "Try it"
cta_source = "Source on GitHub"
cta_read_more = "Read the case study"
featured_label = "01 / Project"
about_label = "02 / About"
contact_label = "03 / Contact"
contact_email_link = "Email"
contact_github_link = "GitHub"
footer_copy = "© {year} Landovskis Forge"
not_found_title = "Page not found"
not_found_text = "That page does not exist. Start from the home page."
og_locale = "en_CA"

[languages.fr]
title = "Landovskis Forge"
description = "Des logiciels web en Rust et WebAssembly, conçus, développés et testés de bout en bout."
generate_feeds = true

[languages.fr.translations]
site_name = "Landovskis Forge"
site_description = "Des logiciels web en Rust et WebAssembly, conçus, développés et testés de bout en bout."
skip_to_content = "Passer au contenu"
nav_main = "Principale"
nav_cityloom = "Cityloom"
lang_name = "Français"
cta_see_cityloom = "Découvrir Cityloom"
cta_try_it = "L'essayer"
cta_source = "Code source sur GitHub"
cta_read_more = "Lire l'étude de cas"
featured_label = "01 / Projet"
about_label = "02 / À propos"
contact_label = "03 / Contact"
contact_email_link = "Courriel"
contact_github_link = "GitHub"
footer_copy = "© {year} Landovskis Forge"
not_found_title = "Page introuvable"
not_found_text = "Cette page n'existe pas. Repartez de la page d'accueil."
og_locale = "fr_CA"
```

- [ ] **Step 4: Create content stubs**

`content/_index.md`:
```toml
+++
title = "Landovskis Forge"
description = "Web software in Rust and WebAssembly, designed, built and tested end to end."
template = "index.html"

[extra]
hero_kicker = "Rust · WebAssembly · Open data"
hero_pitch = "Web software in Rust and WebAssembly, designed, built and tested end to end."
+++
```

`content/_index.fr.md`:
```toml
+++
title = "Landovskis Forge"
description = "Des logiciels web en Rust et WebAssembly, conçus, développés et testés de bout en bout."
template = "index.html"

[extra]
hero_kicker = "Rust · WebAssembly · Données ouvertes"
hero_pitch = "Des logiciels web en Rust et WebAssembly, conçus, développés et testés de bout en bout."
+++
```

- [ ] **Step 5: Create `templates/partials/contact_links.html`**

```jinja
<ul class="link-list">
  {% if config.extra.contact_email %}
  <li><a href="mailto:{{ config.extra.contact_email }}">{{ trans(key="contact_email_link") }}</a></li>
  {% endif %}
  <li><a href="{{ config.extra.github_url }}" rel="me">{{ trans(key="contact_github_link") }}</a></li>
</ul>
```

- [ ] **Step 6: Create `templates/base.html`**

```jinja
{% set_global home_path = "/" %}
{% set_global lang_suffix = "" %}
{% if lang != config.default_language %}
  {% set_global home_path = "/" ~ lang ~ "/" %}
  {% set_global lang_suffix = "." ~ lang %}
{% endif %}
{% set_global ctx = false %}
{% if page is defined %}
  {% set_global ctx = page %}
{% elif section is defined %}
  {% set_global ctx = section %}
{% endif %}
{% set_global page_title = trans(key="site_name") %}
{% if ctx and ctx.title and ctx.title != trans(key="site_name") %}
  {% set_global page_title = ctx.title ~ " · " ~ trans(key="site_name") %}
{% endif %}
{% set_global page_description = trans(key="site_description") %}
{% if ctx and ctx.description %}
  {% set_global page_description = ctx.description %}
{% endif %}
{% set home_url = get_url(path=home_path) %}
{% set feed_url = get_url(path=home_path ~ "atom.xml") %}
{% set year = now() | date(format="%Y") %}
<!doctype html>
<html lang="{{ lang }}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{% block page_title %}{{ page_title }}{% endblock page_title %}</title>
  <meta name="description" content="{{ page_description }}">
  <meta name="color-scheme" content="dark">
  <meta name="theme-color" content="#0b0e13">
  {% if ctx %}
  <link rel="canonical" href="{{ ctx.permalink }}">
  {% for t in ctx.translations %}
  <link rel="alternate" hreflang="{{ t.lang }}" href="{{ t.permalink }}">
  {% if t.lang == config.default_language %}
  <link rel="alternate" hreflang="x-default" href="{{ t.permalink }}">
  {% endif %}
  {% endfor %}
  <meta property="og:url" content="{{ ctx.permalink }}">
  {% endif %}
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="{{ trans(key='site_name') }}">
  <meta property="og:title" content="{{ page_title }}">
  <meta property="og:description" content="{{ page_description }}">
  <meta property="og:locale" content="{{ trans(key='og_locale') }}">
  <meta name="twitter:card" content="summary_large_image">
  <link rel="alternate" type="application/atom+xml" title="{{ trans(key='site_name') }}" href="{{ feed_url }}">
  <link rel="stylesheet" href="{{ get_url(path='main.css') }}">
</head>
<body>
  <a class="skip-link" href="#main">{{ trans(key="skip_to_content") }}</a>
  <header class="site-header">
    <div class="wrap site-header__inner">
      <a class="brand" href="{{ home_url }}"><span class="brand__mark" aria-hidden="true">▚</span>{{ trans(key="site_name") }}</a>
      <nav class="site-nav" aria-label="{{ trans(key='nav_main') }}">
        {% if ctx %}
        {% for t in ctx.translations %}
        {% if t.lang != lang %}
        <a class="lang-switch" href="{{ t.permalink }}" hreflang="{{ t.lang }}" lang="{{ t.lang }}">{{ trans(key="lang_name", lang=t.lang) }}</a>
        {% endif %}
        {% endfor %}
        {% endif %}
      </nav>
    </div>
  </header>
  <main id="main" tabindex="-1">
    {% block content %}{% endblock content %}
  </main>
  <footer class="site-footer">
    <div class="wrap site-footer__inner">
      <p>{{ trans(key="footer_copy") | replace(from="{year}", to=year) }}</p>
      {% include "partials/contact_links.html" %}
    </div>
  </footer>
</body>
</html>
```

- [ ] **Step 7: Create `templates/index.html` and `templates/404.html`**

`templates/index.html`:
```jinja
{% extends "base.html" %}
{% block content %}
<section class="hero">
  <div class="wrap">
    <p class="eyebrow reveal">{{ section.extra.hero_kicker }}</p>
    <h1 class="reveal">{{ section.title }}</h1>
    <p class="lede reveal">{{ section.extra.hero_pitch }}</p>
  </div>
</section>
{% endblock content %}
```

`templates/404.html` (absolute URLs only, both languages):
```jinja
{% extends "base.html" %}
{% block page_title %}{{ trans(key="not_found_title") }} · {{ trans(key="site_name") }}{% endblock page_title %}
{% block content %}
<section class="wrap prose not-found">
  <h1 lang="en">{{ trans(key="not_found_title", lang="en") }}</h1>
  <p lang="en">{{ trans(key="not_found_text", lang="en") }}</p>
  <h2 lang="fr">{{ trans(key="not_found_title", lang="fr") }}</h2>
  <p lang="fr">{{ trans(key="not_found_text", lang="fr") }}</p>
  <ul class="link-list">
    <li><a href="{{ get_url(path='@/_index.md') }}" hreflang="en" lang="en">{{ trans(key="lang_name", lang="en") }}</a></li>
    <li><a href="{{ get_url(path='@/_index.fr.md') }}" hreflang="fr" lang="fr">{{ trans(key="lang_name", lang="fr") }}</a></li>
  </ul>
</section>
{% endblock content %}
```

- [ ] **Step 8: Create a minimal `sass/main.scss` and the `justfile`**

`sass/main.scss`:
```scss
body { margin: 0; }
```

`justfile`:
```make
set shell := ["bash", "-euo", "pipefail", "-c"]

default:
    @just --list

# Live-reloading dev server
serve:
    zola serve

# Production build into public/
build:
    zola build

# Unit tests for the helper scripts
test-scripts:
    python3 -m unittest discover -s scripts -p 'test_*.py'

check-i18n:
    python3 scripts/check_i18n.py

# Everything that must pass before merging
check: test-scripts check-i18n
    zola check
    zola build
    python3 scripts/smoke_test.py public
```

- [ ] **Step 9: Build and run the smoke test**

Run: `just check`
Expected: PASS ending with `smoke test ok`. If `zola build` rejects a Tera construct (for example `is defined` or `set_global` inside `if`), adjust the base template minimally and re-run; the smoke test is the oracle. If `zola check` or the build fails on `[languages.fr] description`, remove only that key and re-run.

- [ ] **Step 10: Inspect the output**

Run: `grep -E 'lang=|hreflang|canonical' public/index.html public/fr/index.html | head -20 && ls public public/fr`
Expected: `lang="en"` / `lang="fr"`, `hreflang` en, fr, x-default on both pages; `atom.xml`, `sitemap.xml`, `robots.txt`, `fr/atom.xml` present.

- [ ] **Step 11: Commit**

```bash
git add config.toml justfile templates content sass scripts/smoke_test.py
git commit -m "feat: add bilingual Zola skeleton and smoke test" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Design system (tokens, fonts, base styles)

**Files:**
- Create: `scripts/check_contrast.py`, `scripts/test_check_contrast.py`, `sass/_tokens.scss`, `sass/_fonts.scss`, `sass/_base.scss`, `sass/_layout.scss`, `static/fonts/JetBrainsMono-Regular.woff2`, `static/fonts/JetBrainsMono-Bold.woff2`, `static/fonts/OFL.txt`
- Modify: `sass/main.scss`, `templates/base.html` (font preload), `justfile` (`check-contrast`)

**Interfaces:**
- Produces: CSS custom properties `--bg --surface --surface-2 --line --text --muted --accent --accent-ink --font-mono --font-sans --radius --wrap --gutter`; classes `.wrap .prose .eyebrow .lede .reveal .hero .btn .btn--primary .actions .card .window .window__bar .window__dot .tag .tags .link-list .site-header .site-footer .skip-link .lang-switch .brand` used by later templates.
- Produces: `check_contrast.contrast_ratio(fg: str, bg: str) -> float`, `check_contrast.main(root) -> int`.

- [ ] **Step 1: Write the failing contrast tests** — `scripts/test_check_contrast.py`

```python
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import check_contrast


class ContrastTests(unittest.TestCase):
    def test_black_on_white_is_21(self):
        self.assertAlmostEqual(check_contrast.contrast_ratio("#000000", "#ffffff"), 21.0, places=1)

    def test_same_colour_is_1(self):
        self.assertAlmostEqual(check_contrast.contrast_ratio("#336699", "#336699"), 1.0, places=2)

    def test_reads_tokens_and_flags_low_contrast(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "sass").mkdir()
            tokens = ":root {\n" + "".join(
                f"  --{name}: {value};\n"
                for name, value in {
                    "bg": "#0b0e13", "surface": "#11161d", "surface-2": "#171d26",
                    "text": "#e6eaf0", "muted": "#222222", "accent": "#ff8a3d",
                    "accent-ink": "#0b0e13",
                }.items()
            ) + "}\n"
            (root / "sass" / "_tokens.scss").write_text(tokens, encoding="utf-8")
            self.assertEqual(check_contrast.main(root), 1)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run to verify failure**

Run: `python3 -m unittest scripts.test_check_contrast 2>&1 | tail -5` (or `python3 -m unittest discover -s scripts -p 'test_check_contrast.py'`)
Expected: ERROR `No module named 'check_contrast'`.

- [ ] **Step 3: Implement `scripts/check_contrast.py`**

```python
#!/usr/bin/env python3
"""Check WCAG contrast of the colour token pairs the site uses (sass/_tokens.scss)."""
import re
import sys
from pathlib import Path

TOKEN_RE = re.compile(r"^\s*--([a-z0-9\-]+):\s*(#[0-9a-fA-F]{6})\s*;", re.M)

# (foreground, background, minimum ratio, what it is used for)
PAIRS = [
    ("text", "bg", 4.5, "body text on page"),
    ("text", "surface", 4.5, "body text on panels"),
    ("muted", "bg", 4.5, "secondary text on page"),
    ("muted", "surface", 4.5, "secondary text on panels"),
    ("muted", "surface-2", 4.5, "secondary text on raised panels"),
    ("accent", "bg", 4.5, "links and labels on page"),
    ("accent", "surface", 4.5, "links and labels on panels"),
    ("accent-ink", "accent", 4.5, "text on primary buttons"),
]


def _channel(value):
    c = value / 255
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def _luminance(hex_colour):
    r, g, b = (int(hex_colour[i:i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * _channel(r) + 0.7152 * _channel(g) + 0.0722 * _channel(b)


def contrast_ratio(fg, bg):
    lighter, darker = sorted((_luminance(fg), _luminance(bg)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


def main(root):
    text = (root / "sass" / "_tokens.scss").read_text(encoding="utf-8")
    tokens = dict(TOKEN_RE.findall(text))
    problems = []
    for fg, bg, minimum, use in PAIRS:
        if fg not in tokens or bg not in tokens:
            problems.append(f"missing token for pair --{fg} on --{bg}")
            continue
        ratio = contrast_ratio(tokens[fg], tokens[bg])
        if ratio < minimum:
            problems.append(f"--{fg} on --{bg} ({use}): {ratio:.2f} < {minimum}")
    for problem in problems:
        print(problem, file=sys.stderr)
    if problems:
        return 1
    print("contrast ok")
    return 0


if __name__ == "__main__":
    sys.exit(main(Path(__file__).resolve().parent.parent))
```

- [ ] **Step 4: Run to verify the tests pass**

Run: `python3 -m unittest discover -s scripts -p 'test_check_contrast.py' -v`
Expected: 3 tests `ok`.

- [ ] **Step 5: Create `sass/_tokens.scss`**

```scss
:root {
  --bg: #0b0e13;
  --surface: #11161d;
  --surface-2: #171d26;
  --line: #263040;
  --text: #e6eaf0;
  --muted: #9aa5b5;
  --accent: #ff8a3d;
  --accent-ink: #0b0e13;

  --font-mono: "JetBrains Mono", ui-monospace, "SF Mono", Menlo, Consolas, monospace;
  --font-sans: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;

  --radius: 0.5rem;
  --wrap: 72rem;
  --gutter: clamp(1rem, 4vw, 2rem);
}
```

- [ ] **Step 6: Run the real contrast check**

Run: `python3 scripts/check_contrast.py`
Expected: `contrast ok`. If a pair fails, lighten the failing foreground token (or darken the background) until it passes and rerun.

- [ ] **Step 7: Download the fonts (untrusted download: scratch dir, not the repo)**

```bash
S=/private/tmp/claude-501/-Users-alex-src-site/fa59edb7-f10f-4485-a926-b715c91db9be/scratchpad
mkdir -p "$S/jb" && gh release download v2.304 -R JetBrains/JetBrainsMono -p '*.zip' -D "$S/jb" --clobber
unzip -o -j "$S"/jb/JetBrainsMono-2.304.zip 'fonts/webfonts/JetBrainsMono-Regular.woff2' 'fonts/webfonts/JetBrainsMono-Bold.woff2' 'OFL.txt' -d /Users/alex/src/site/static/fonts
ls -l /Users/alex/src/site/static/fonts
```
Before this step, run `gh api repos/JetBrains/JetBrainsMono/releases/latest --jq .tag_name`; if it is newer than `v2.304`, use that tag and its zip name, and re-list the zip's contents with `unzip -l` to confirm the `fonts/webfonts/` paths.
Expected: three files, each WOFF2 about 90 KB, plus `OFL.txt`.

- [ ] **Step 8: Create `sass/_fonts.scss`**

```scss
@font-face {
  font-family: "JetBrains Mono";
  src: url("/fonts/JetBrainsMono-Regular.woff2") format("woff2");
  font-weight: 400;
  font-style: normal;
  font-display: swap;
}

@font-face {
  font-family: "JetBrains Mono";
  src: url("/fonts/JetBrainsMono-Bold.woff2") format("woff2");
  font-weight: 700;
  font-style: normal;
  font-display: swap;
}
```

- [ ] **Step 9: Create `sass/_base.scss`**

```scss
*, *::before, *::after { box-sizing: border-box; }

html {
  color-scheme: dark;
  -webkit-text-size-adjust: 100%;
  scroll-behavior: smooth;
}

body {
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font: 1rem/1.65 var(--font-sans);
}

img { display: block; max-width: 100%; height: auto; }

a { color: var(--accent); text-underline-offset: 0.2em; }
a:hover { text-decoration-thickness: 2px; }

:focus-visible { outline: 2px solid var(--accent); outline-offset: 3px; border-radius: 2px; }
main:focus { outline: none; }

h1, h2, h3 {
  margin: 0 0 0.6em;
  font-family: var(--font-mono);
  font-weight: 700;
  line-height: 1.15;
  letter-spacing: -0.01em;
  overflow-wrap: anywhere;
}
h1 { font-size: clamp(2rem, 6vw, 3.5rem); }
h2 { font-size: clamp(1.4rem, 3vw, 2rem); }
h3 { font-size: 1.15rem; }

p { margin: 0 0 1em; max-width: 68ch; }
code { font-family: var(--font-mono); font-size: 0.92em; }

.eyebrow {
  margin: 0 0 1rem;
  color: var(--accent);
  font: 700 0.8rem/1.3 var(--font-mono);
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.lede { max-width: 56ch; color: var(--muted); font-size: clamp(1.1rem, 2.4vw, 1.35rem); }

.skip-link {
  position: absolute;
  top: -4rem;
  left: var(--gutter);
  z-index: 10;
  padding: 0.5rem 0.9rem;
  border-radius: var(--radius);
  background: var(--accent);
  color: var(--accent-ink);
  font-family: var(--font-mono);
  font-weight: 700;
}
.skip-link:focus { top: 0.5rem; }

@media (prefers-reduced-motion: no-preference) {
  .reveal { animation: rise 0.6s cubic-bezier(0.2, 0.7, 0.2, 1) both; }

  @keyframes rise {
    from { opacity: 0; transform: translateY(12px); }
    to { opacity: 1; transform: none; }
  }
}

@media (prefers-reduced-motion: reduce) {
  html { scroll-behavior: auto; }
}
```

- [ ] **Step 10: Create `sass/_layout.scss`**

```scss
.wrap { width: min(100% - 2 * var(--gutter), var(--wrap)); margin-inline: auto; }
.prose { padding-block: 3rem; }

.site-header { border-bottom: 1px solid var(--line); }
.site-header__inner {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem 1.5rem;
  min-height: 4rem;
}
.brand {
  color: var(--text);
  font: 700 1rem/1 var(--font-mono);
  text-decoration: none;
  letter-spacing: 0.02em;
}
.brand__mark { margin-right: 0.6rem; color: var(--accent); }
.site-nav { display: flex; flex-wrap: wrap; gap: 0.25rem 1.25rem; font: 0.9rem/1 var(--font-mono); }
.site-nav a { display: inline-flex; align-items: center; min-height: 44px; }
.lang-switch { color: var(--muted); }

.site-footer { margin-top: 5rem; border-top: 1px solid var(--line); color: var(--muted); }
.site-footer__inner {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 1rem 2rem;
  padding-block: 1.5rem;
}
.site-footer p { margin: 0; font-family: var(--font-mono); font-size: 0.85rem; }

.link-list { display: flex; flex-wrap: wrap; gap: 0.25rem 1.5rem; margin: 0; padding: 0; list-style: none; }
.link-list a { display: inline-flex; align-items: center; min-height: 44px; }

.hero {
  position: relative;
  isolation: isolate;
  padding-block: clamp(3rem, 10vw, 7rem) clamp(2.5rem, 8vw, 5rem);

  &::before {
    content: "";
    position: absolute;
    inset: 0;
    z-index: -1;
    background-image:
      linear-gradient(var(--line) 1px, transparent 1px),
      linear-gradient(90deg, var(--line) 1px, transparent 1px);
    background-size: 3rem 3rem;
    opacity: 0.45;
    -webkit-mask-image: radial-gradient(ellipse at 30% 0%, #000 0%, transparent 70%);
    mask-image: radial-gradient(ellipse at 30% 0%, #000 0%, transparent 70%);
  }
}

.actions { display: flex; flex-wrap: wrap; gap: 0.75rem; margin-top: 1.75rem; }

.btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  min-height: 44px;
  padding: 0.7rem 1.2rem;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--surface);
  color: var(--text);
  font: 700 0.95rem/1.2 var(--font-mono);
  text-decoration: none;
  transition: border-color 0.15s ease;

  &:hover { border-color: var(--accent); }

  &--primary {
    border-color: var(--accent);
    background: var(--accent);
    color: var(--accent-ink);
  }
}

.section { padding-block: clamp(2.5rem, 7vw, 4.5rem); border-top: 1px solid var(--line); }

.card {
  display: grid;
  gap: 1.5rem;
  padding: clamp(1rem, 3vw, 2rem);
  border: 1px solid var(--line);
  border-radius: calc(var(--radius) * 1.5);
  background: var(--surface);
}
@media (min-width: 56rem) {
  .card--split { grid-template-columns: 1fr 1.3fr; align-items: center; }
}

.tags { display: flex; flex-wrap: wrap; gap: 0.5rem; margin: 1rem 0 0; padding: 0; list-style: none; }
.tag {
  padding: 0.25rem 0.6rem;
  border: 1px solid var(--line);
  border-radius: 999px;
  color: var(--muted);
  font: 0.8rem/1.2 var(--font-mono);
}

.window {
  margin: 0;
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: 0.75rem;
  background: var(--surface);
  box-shadow: 0 24px 60px -24px rgba(255, 138, 61, 0.25);

  &__bar { display: flex; gap: 0.4rem; padding: 0.6rem 0.8rem; border-bottom: 1px solid var(--line); background: var(--surface-2); }
  &__dot { width: 0.6rem; height: 0.6rem; border-radius: 50%; background: var(--line); }
  figcaption { padding: 0.75rem 1rem; color: var(--muted); font-size: 0.9rem; }
}
```

- [ ] **Step 11: Wire the stylesheet, preload fonts, and add the justfile target**

`sass/main.scss`:
```scss
@import "tokens";
@import "fonts";
@import "base";
@import "layout";
```

In `templates/base.html`, add directly after the stylesheet `<link>`:
```jinja
  <link rel="preload" href="{{ get_url(path='fonts/JetBrainsMono-Bold.woff2') }}" as="font" type="font/woff2" crossorigin>
```

In `justfile`, add the recipe and extend `check`:
```make
check-contrast:
    python3 scripts/check_contrast.py

check: test-scripts check-i18n check-contrast
    zola check
    zola build
    python3 scripts/smoke_test.py public
```
(Replace the existing `check` recipe.)

- [ ] **Step 12: Verify**

Run: `just check && ls public/main.css && grep -c 'JetBrains Mono' public/main.css`
Expected: passes; `main.css` exists and mentions JetBrains Mono. If `@import` is rejected by Zola's Sass compiler, switch the four lines to `@use "tokens"; ...` (keep order) and re-run.

- [ ] **Step 13: Commit**

```bash
git add sass static scripts/check_contrast.py scripts/test_check_contrast.py templates/base.html justfile
git commit -m "feat: add dark forge design system with contrast check" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Home page (hero, about, contact)

**Files:**
- Modify: `templates/index.html`, `content/_index.md`, `content/_index.fr.md`, `config.toml` (nothing new), `scripts/check_i18n.py` (no change)
- Test: `scripts/smoke_test.py` already asserts the demo link rules and one `<h1>`

**Interfaces:**
- Consumes: base template, `partials/contact_links.html`, classes from Task 3, config extras `cityloom_demo_enabled`, `cityloom_demo_url`.
- Produces: home sections `.hero`, `#about`, `#contact`; front matter keys `hero_kicker hero_pitch about_title about_text` in both languages.

- [ ] **Step 1: Write the failing check** — extend `PAGES` expectations: add to the smoke test a required home section id check. In `scripts/smoke_test.py`, inside the `for name, lang, counterpart in PAGES:` loop, after the `h1` check add:

```python
        if 'id="about"' not in path.read_text(encoding="utf-8"):
            problems.append(f"{name}: missing #about section")
```

Run: `just check`
Expected: FAIL with `index.html: missing #about section` (and the FR page).

- [ ] **Step 2: Extend front matter**

`content/_index.md` `[extra]` gains:
```toml
about_title = "About the forge"
about_text = "Landovskis Forge is the portfolio of Alex Landovskis. The work here is held to a short list of standards: it is tested, it is accessible, it speaks English and French, and it says plainly what is finished and what is not."
```
`content/_index.fr.md` `[extra]` gains:
```toml
about_title = "À propos de la forge"
about_text = "Landovskis Forge est le portfolio d'Alex Landovskis. Le travail présenté ici respecte une courte liste d'exigences : il est testé, accessible, offert en français et en anglais, et il dit clairement ce qui est terminé et ce qui ne l'est pas."
```

- [ ] **Step 3: Replace `templates/index.html`**

```jinja
{% extends "base.html" %}
{% block content %}
<section class="hero">
  <div class="wrap">
    <p class="eyebrow reveal">{{ section.extra.hero_kicker }}</p>
    <h1 class="reveal">{{ section.title }}</h1>
    <p class="lede reveal">{{ section.extra.hero_pitch }}</p>
    <div class="actions reveal">
      {% if config.extra.cityloom_demo_enabled %}
      <a class="btn btn--primary" href="{{ config.extra.cityloom_demo_url }}">{{ trans(key="cta_try_it") }}</a>
      {% endif %}
      <a class="btn{% if not config.extra.cityloom_demo_enabled %} btn--primary{% endif %}" href="#about">{{ trans(key="about_label") }}</a>
    </div>
  </div>
</section>

<section class="section" id="about">
  <div class="wrap">
    <p class="eyebrow">{{ trans(key="about_label") }}</p>
    <h2>{{ section.extra.about_title }}</h2>
    <p>{{ section.extra.about_text }}</p>
  </div>
</section>

<section class="section" id="contact">
  <div class="wrap">
    <p class="eyebrow">{{ trans(key="contact_label") }}</p>
    {% include "partials/contact_links.html" %}
  </div>
</section>
{% endblock content %}
```
(The "See Cityloom" button and featured card arrive in Task 6, when the case study exists.)

- [ ] **Step 4: Verify**

Run: `just check`
Expected: PASS. Then open `just serve` and visually confirm the hero (grid background, ember accent, mono heading) on `/` and `/fr/` at desktop and a 375 px-wide window; confirm the language switcher goes to the other language's home.

- [ ] **Step 5: Commit**

```bash
git add templates/index.html content scripts/smoke_test.py
git commit -m "feat: add home hero, about and contact sections" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 5: Cityloom screenshots

**Files:**
- Create: `package.json`, `package-lock.json` (via npm), `scripts/capture_screenshots.mjs`, `assets/screenshots/home.png`, `assets/screenshots/street.png`, `assets/screenshots/intersection.png`

**Interfaces:**
- Produces: three PNGs (1440×900) of the Cityloom EN UI at `assets/screenshots/{home,street,intersection}.png`. The map page is **not** captured (it needs the 1.2 GB basemap data; do not download without the author's go-ahead).

- [ ] **Step 1: Install tooling with the latest versions**

```bash
cd /Users/alex/src/site
npm init -y >/dev/null
npm install --save-dev --save-exact playwright @axe-core/playwright
npx playwright install chromium
```
Then edit `package.json`: set `"name": "landovskis-forge-site"`, `"private": true`, `"type": "module"`, remove the `main`, `scripts.test`, `keywords`, `author`, `license` fields that `npm init` added.
Expected: `node_modules/` exists, `package-lock.json` created, both packages listed under `devDependencies`.

- [ ] **Step 2: Get a local Cityloom build (outside this repo)**

```bash
S=/private/tmp/claude-501/-Users-alex-src-site/fa59edb7-f10f-4485-a926-b715c91db9be/scratchpad
git clone https://github.com/alandovskis/cityloom.git "$S/cityloom"
cd "$S/cityloom" && cat CLAUDE.md | head -60 && just setup && just build
```
Expected: `just build` produces `web/pkg`. If `just setup` needs tools the machine lacks (Rust target, wasm-bindgen), install what the error asks for (latest versions) and retry. Do **not** run `just prepare` (the 1.2 GB download).

- [ ] **Step 3: Serve it**

Run (background): `cd "$S/cityloom" && just serve` and confirm `curl -sI http://127.0.0.1:8137/ | head -1` returns `HTTP/1.1 200`.

- [ ] **Step 4: Write `scripts/capture_screenshots.mjs`**

```js
// Captures the Cityloom UI for the case study. Usage:
//   node scripts/capture_screenshots.mjs [base-url]   (default http://127.0.0.1:8137)
import { chromium } from "playwright";
import { mkdir } from "node:fs/promises";

const base = process.argv[2] ?? "http://127.0.0.1:8137";
const out = new URL("../assets/screenshots/", import.meta.url).pathname;

// name -> page path. Adjust the path or add steps if a page needs a place chosen first.
const shots = [
  { name: "home", path: "/" },
  { name: "street", path: "/street.html" },
  { name: "intersection", path: "/intersection.html" },
];

await mkdir(out, { recursive: true });
const browser = await chromium.launch();
const context = await browser.newContext({
  viewport: { width: 1440, height: 900 },
  deviceScaleFactor: 1,
  locale: "en-CA",
  reducedMotion: "reduce",
});
for (const { name, path } of shots) {
  const page = await context.newPage();
  await page.goto(base + path, { waitUntil: "networkidle" });
  await page.waitForTimeout(1500);
  await page.screenshot({ path: `${out}${name}.png` });
  console.log(`captured ${name}`);
  await page.close();
}
await browser.close();
```

- [ ] **Step 5: Capture and inspect every image**

Run: `node scripts/capture_screenshots.mjs`
Then Read each PNG (`assets/screenshots/home.png`, `street.png`, `intersection.png`). Each must show the real product UI, not an error, blank page or loading spinner.
If a page shows an empty or error state, open it in the browser tools, find the shortest user path to a populated view (the README says the home page finds a place by name; the map opens the street and junction editors), encode that path as steps in the `shots` entry (clicks/fills before the screenshot), and re-capture. Network access to OpenStreetMap services is required for places outside the pre-built tiles.

- [ ] **Step 6: Stop the Cityloom server and commit**

Stop the background `just serve`. Then:
```bash
cd /Users/alex/src/site
git add package.json package-lock.json scripts/capture_screenshots.mjs assets/screenshots
git commit -m "feat: capture Cityloom screenshots" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 6: Cityloom case study and featured card

**Files:**
- Create: `content/projects/_index.md`, `content/projects/_index.fr.md`, `content/projects/cityloom.md`, `content/projects/cityloom.fr.md`, `templates/project.html`, `templates/macros/image.html`, `templates/partials/project_actions.html`, `templates/partials/project_card.html`
- Modify: `templates/index.html`, `templates/base.html` (nav link + `og:image`), `scripts/smoke_test.py` (`PAGES`), `sass/_layout.scss`, `config.toml` (translation `surfaces_note` not needed; add nothing)

**Interfaces:**
- Consumes: `resize_image`, classes from Task 3, screenshots from Task 5, config extras.
- Produces: pages `/projects/cityloom/` and `/fr/projects/cityloom/`; front matter keys on the case study `[extra]`: `tags` (array), `hero_image`, `hero_alt`, `problem_title`, `problem_text`, `surfaces_title`, `surfaces_intro`, `architecture_title`, `architecture_caption`, `shared_title`, `shared_text`; array tables `[[extra.surfaces]]` (`image`, `title`, `alt`, `text`) and `[[extra.slices]]` (`name`, `text`).

- [ ] **Step 1: Write the failing smoke expectations**

In `scripts/smoke_test.py`, extend `PAGES`:
```python
PAGES = [
    ("index.html", "en", "fr/index.html"),
    ("fr/index.html", "fr", "index.html"),
    ("projects/cityloom/index.html", "en", "fr/projects/cityloom/index.html"),
    ("fr/projects/cityloom/index.html", "fr", "projects/cityloom/index.html"),
]
```
The `#about` check added in Task 4 must apply to the home pages only: change it to `if name.endswith("index.html") and "projects" not in name and ...` — concretely replace that check with:
```python
        if "projects" not in name and 'id="about"' not in path.read_text(encoding="utf-8"):
            problems.append(f"{name}: missing #about section")
```
Also add, inside the same loop, an image-dimension check for every page:
```python
        for tag in re.findall(r"<img[^>]*>", path.read_text(encoding="utf-8")):
            if "width=" not in tag or "height=" not in tag or "alt=" not in tag:
                problems.append(f"{name}: <img> without width, height and alt: {tag[:60]}")
```
Run: `just check`
Expected: FAIL: `missing page: projects/cityloom/index.html` etc.

- [ ] **Step 2: Create the projects section files**

`content/projects/_index.md`:
```toml
+++
title = "Projects"
render = false
sort_by = "date"
page_template = "project.html"
+++
```
`content/projects/_index.fr.md`:
```toml
+++
title = "Projets"
render = false
sort_by = "date"
page_template = "project.html"
+++
```
If Zola rejects `render = false`, replace it with `redirect_to = "/"` (and `"/fr/"` in the FR file).

- [ ] **Step 3: Create `content/projects/cityloom.md`**

First re-open each screenshot and make sure every `alt` below describes what that PNG actually shows; correct any that do not.

```toml
+++
title = "Cityloom"
description = "Streetmix at city scale: residents compose and compare whole-city scenarios."
date = 2026-10-10
template = "project.html"

[extra]
tags = ["Rust", "WebAssembly", "Leptos", "OpenStreetMap"]
hero_image = "assets/screenshots/street.png"
hero_alt = "The Cityloom street editor, showing the cross-section of a street being edited."
problem_title = "The problem"
problem_text = "Streetmix lets anyone design a single street. Cityloom lifts that to the whole city: residents compose and compare city-wide scenarios without professional planning tools. It is built for ordinary residents, first in a web browser and later in native mobile apps."
surfaces_title = "The surfaces"
surfaces_intro = "A city map ties the surfaces together and opens the street and intersection editors one at a time."
architecture_title = "Architecture"
architecture_caption = "Each feature is a vertical slice. Slices reach one another only through a model, and a view-model reaches the browser only through ports, so it is tested on the host with fakes."
shared_title = "shared/"
shared_text = "Catalogue and units, ports to the browser (with test fakes), the reactive core."

[[extra.surfaces]]
image = "assets/screenshots/home.png"
title = "Find a place"
alt = "The Cityloom home page, with a search field for finding a place by name."
text = "Search for a place by name. Its streets come from OpenStreetMap and become a city to edit."

[[extra.surfaces]]
image = "assets/screenshots/street.png"
title = "Street editor"
alt = "The Cityloom street editor, showing the cross-section of a street being edited."
text = "Edit the cross-section of a street. The editing rules live in a model, and a screen reader is given the same state in words."

[[extra.surfaces]]
image = "assets/screenshots/intersection.png"
title = "Intersection editor"
alt = "The Cityloom intersection editor, showing a junction where streets meet."
text = "Edit the junction where streets meet, built the same model-first way as the street editor."

[[extra.slices]]
name = "street/"
text = "Editing rules, view-model, views"

[[extra.slices]]
name = "junction/"
text = "Editing rules, geometry, view-model, views"

[[extra.slices]]
name = "map/"
text = "View-model, basemap overlay, views"

[[extra.slices]]
name = "city/"
text = "City from OpenStreetMap, storage, page binding"

[[extra.slices]]
name = "shell/"
text = "Settings menu, sidebars, notes tabs"
+++

## How it is built

Cityloom is written in Rust and compiled to WebAssembly, with Leptos rendering the interface in the browser. Logic lives in view-models that know nothing about the page; views bind to them and decide nothing. Browser tests drive the built pages with Playwright.

Continuous integration runs formatting, unit tests and browser tests through `just`, with actions pinned to commits and Dependabot proposing weekly updates. The interface is bilingual, English and French, with Fluent translation files.

## What is open

The source is public on GitHub. Open source and open data are stated product principles: streets come from OpenStreetMap through Nominatim, Overpass and osm2streets, and the Montréal basemap is built from a Geofabrik extract with Planetiler.

## Status

Cityloom is early. Catalogue widths, rules and capacity rates are synthetic placeholders, not real standards or measurements. Native Android and iOS apps are planned after the web release.
```

- [ ] **Step 4: Create `content/projects/cityloom.fr.md`** (same keys, same order, fr-CA)

```toml
+++
title = "Cityloom"
description = "Streetmix à l'échelle de la ville : les résidents composent et comparent des scénarios pour toute la ville."
date = 2026-10-10
template = "project.html"

[extra]
tags = ["Rust", "WebAssembly", "Leptos", "OpenStreetMap"]
hero_image = "assets/screenshots/street.png"
hero_alt = "L'éditeur de rues de Cityloom, montrant la coupe transversale d'une rue en cours de modification."
problem_title = "Le problème"
problem_text = "Streetmix permet à tout le monde de concevoir une seule rue. Cityloom étend l'idée à toute la ville : les résidents composent et comparent des scénarios à l'échelle de la ville, sans outils professionnels d'urbanisme. Il s'adresse aux résidents ordinaires, d'abord dans un navigateur web, puis dans des applications mobiles natives."
surfaces_title = "Les interfaces"
surfaces_intro = "Une carte de la ville relie les interfaces et ouvre tour à tour les éditeurs de rues et d'intersections."
architecture_title = "Architecture"
architecture_caption = "Chaque fonctionnalité est une tranche verticale. Les tranches ne communiquent entre elles que par un modèle, et un modèle de vue n'atteint le navigateur que par des ports : on le teste donc sur l'hôte avec des doublures."
shared_title = "shared/"
shared_text = "Catalogue et unités, ports vers le navigateur (avec doublures de test), noyau réactif."

[[extra.surfaces]]
image = "assets/screenshots/home.png"
title = "Trouver un lieu"
alt = "La page d'accueil de Cityloom, avec un champ de recherche pour trouver un lieu par son nom."
text = "Cherchez un lieu par son nom. Ses rues viennent d'OpenStreetMap et deviennent une ville à modifier."

[[extra.surfaces]]
image = "assets/screenshots/street.png"
title = "Éditeur de rues"
alt = "L'éditeur de rues de Cityloom, montrant la coupe transversale d'une rue en cours de modification."
text = "Modifiez la coupe transversale d'une rue. Les règles d'édition vivent dans un modèle, et un lecteur d'écran reçoit le même état en mots."

[[extra.surfaces]]
image = "assets/screenshots/intersection.png"
title = "Éditeur d'intersections"
alt = "L'éditeur d'intersections de Cityloom, montrant un carrefour où se croisent des rues."
text = "Modifiez le carrefour où les rues se croisent, selon la même approche centrée sur le modèle que l'éditeur de rues."

[[extra.slices]]
name = "street/"
text = "Règles d'édition, modèle de vue, vues"

[[extra.slices]]
name = "junction/"
text = "Règles d'édition, géométrie, modèle de vue, vues"

[[extra.slices]]
name = "map/"
text = "Modèle de vue, couche sur le fond de carte, vues"

[[extra.slices]]
name = "city/"
text = "Ville issue d'OpenStreetMap, stockage, liaison avec la page"

[[extra.slices]]
name = "shell/"
text = "Menu des paramètres, panneaux latéraux, onglets de notes"
+++

## Comment il est construit

Cityloom est écrit en Rust et compilé en WebAssembly, avec Leptos pour afficher l'interface dans le navigateur. La logique vit dans des modèles de vue qui ignorent tout de la page ; les vues s'y lient et ne décident de rien. Des tests de navigateur pilotent les pages construites avec Playwright.

L'intégration continue exécute le formatage, les tests unitaires et les tests de navigateur par l'entremise de `just`, avec des actions épinglées à des commits et Dependabot qui propose des mises à jour chaque semaine. L'interface est bilingue, en français et en anglais, avec des fichiers de traduction Fluent.

## Ce qui est ouvert

Le code source est public sur GitHub. Le code ouvert et les données ouvertes sont des principes déclarés du produit : les rues viennent d'OpenStreetMap par Nominatim, Overpass et osm2streets, et le fond de carte de Montréal est construit à partir d'un extrait de Geofabrik avec Planetiler.

## État d'avancement

Cityloom en est à ses débuts. Les largeurs du catalogue, les règles et les débits de capacité sont des valeurs fictives, et non de vraies normes ou mesures. Des applications Android et iOS natives sont prévues après la version web.
```

- [ ] **Step 5: Create `templates/macros/image.html`**

```jinja
{% macro shot(path, alt, width=1200, eager=false) %}
{% set img = resize_image(path=path, width=width, op="fit_width", format="webp", quality=82) %}
<img src="{{ img.url }}" width="{{ img.width }}" height="{{ img.height }}" alt="{{ alt }}"{% if not eager %} loading="lazy" decoding="async"{% endif %}>
{% endmacro shot %}
```

- [ ] **Step 6: Create the partials**

`templates/partials/project_actions.html`:
```jinja
<div class="actions">
  {% if config.extra.cityloom_demo_enabled %}
  <a class="btn btn--primary" href="{{ config.extra.cityloom_demo_url }}">{{ trans(key="cta_try_it") }}</a>
  {% endif %}
  <a class="btn{% if not config.extra.cityloom_demo_enabled %} btn--primary{% endif %}" href="{{ config.extra.source_url }}">{{ trans(key="cta_source") }}</a>
</div>
```

`templates/partials/project_card.html` (expects `project` to be set by the includer):
```jinja
{% import "macros/image.html" as img %}
<article class="card card--split">
  <div>
    <p class="eyebrow">{{ trans(key="featured_label") }}</p>
    <h2>{{ project.title }}</h2>
    <p class="lede">{{ project.description }}</p>
    <ul class="tags">
      {% for tag in project.extra.tags %}<li class="tag">{{ tag }}</li>{% endfor %}
    </ul>
    <div class="actions">
      <a class="btn btn--primary" href="{{ project.permalink }}">{{ trans(key="cta_read_more") }}</a>
    </div>
  </div>
  <figure class="window">
    <div class="window__bar" aria-hidden="true"><span class="window__dot"></span><span class="window__dot"></span><span class="window__dot"></span></div>
    {{ img::shot(path=project.extra.hero_image, alt=project.extra.hero_alt, width=1000) }}
  </figure>
</article>
```

- [ ] **Step 7: Create `templates/project.html`**

```jinja
{% extends "base.html" %}
{% import "macros/image.html" as img %}
{% block content %}
<article>
  <header class="hero">
    <div class="wrap">
      <p class="eyebrow reveal">{{ trans(key="featured_label") }}</p>
      <h1 class="reveal">{{ page.title }}</h1>
      <p class="lede reveal">{{ page.description }}</p>
      <ul class="tags reveal">
        {% for tag in page.extra.tags %}<li class="tag">{{ tag }}</li>{% endfor %}
      </ul>
      <div class="reveal">{% include "partials/project_actions.html" %}</div>
    </div>
  </header>

  <section class="section">
    <div class="wrap">
      <h2>{{ page.extra.problem_title }}</h2>
      <p>{{ page.extra.problem_text }}</p>
    </div>
  </section>

  <section class="section">
    <div class="wrap">
      <h2>{{ page.extra.surfaces_title }}</h2>
      <p>{{ page.extra.surfaces_intro }}</p>
      <div class="surfaces">
        {% for s in page.extra.surfaces %}
        <figure class="window">
          <div class="window__bar" aria-hidden="true"><span class="window__dot"></span><span class="window__dot"></span><span class="window__dot"></span></div>
          {{ img::shot(path=s.image, alt=s.alt) }}
          <figcaption><strong>{{ s.title }}</strong> — {{ s.text }}</figcaption>
        </figure>
        {% endfor %}
      </div>
    </div>
  </section>

  <section class="section">
    <div class="wrap">
      <h2>{{ page.extra.architecture_title }}</h2>
      <p>{{ page.extra.architecture_caption }}</p>
      <ul class="slices">
        {% for slice in page.extra.slices %}
        <li class="slice"><code>{{ slice.name }}</code><span>{{ slice.text }}</span></li>
        {% endfor %}
      </ul>
      <p class="slice-shared"><code>{{ page.extra.shared_title }}</code> {{ page.extra.shared_text }}</p>
    </div>
  </section>

  <section class="section">
    <div class="wrap prose-body">
      {{ page.content | safe }}
    </div>
  </section>
</article>
{% endblock content %}
```

- [ ] **Step 8: Add layout styles** — append to `sass/_layout.scss`

```scss
.surfaces { display: grid; gap: 1.5rem; margin-top: 1.5rem; }
@media (min-width: 56rem) {
  .surfaces { grid-template-columns: 1fr 1fr; }
  .surfaces .window:first-child { grid-column: 1 / -1; }
}

.slices {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(14rem, 1fr));
  gap: 0.75rem;
  margin: 1.5rem 0 0;
  padding: 0;
  list-style: none;
}
.slice {
  display: grid;
  gap: 0.35rem;
  padding: 1rem;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--surface);

  code { color: var(--accent); font-weight: 700; }
  span { color: var(--muted); font-size: 0.9rem; }
}
.slice-shared {
  margin: 0.75rem 0 0;
  padding: 1rem;
  border: 1px dashed var(--line);
  border-radius: var(--radius);
  color: var(--muted);

  code { margin-right: 0.5rem; color: var(--accent); font-weight: 700; }
}
.prose-body h2 { margin-top: 2rem; }
.prose-body h2:first-child { margin-top: 0; }
```

- [ ] **Step 9: Wire navigation, featured card, hero button and OG image**

In `templates/base.html`, inside `<nav ...>` before the language switcher loop add:
```jinja
        <a href="{{ get_url(path='@/projects/cityloom' ~ lang_suffix ~ '.md') }}">{{ trans(key="nav_cityloom") }}</a>
```
In `<head>` after the `og:locale` meta add:
```jinja
  {% set og_image = resize_image(path="assets/screenshots/street.png", width=1200, height=630, op="fill", format="png") %}
  <meta property="og:image" content="{{ og_image.url }}">
```
In `templates/index.html`, replace the secondary hero button with a link to the case study and insert the featured section after the hero:
```jinja
      <a class="btn{% if not config.extra.cityloom_demo_enabled %} btn--primary{% endif %}" href="{{ get_url(path='@/projects/cityloom' ~ lang_suffix ~ '.md') }}">{{ trans(key="cta_see_cityloom") }}</a>
```
```jinja
<section class="section" id="projects">
  <div class="wrap">
    {% set project = get_page(path="projects/cityloom" ~ lang_suffix ~ ".md") %}
    {% include "partials/project_card.html" %}
  </div>
</section>
```
The `cta_see_cityloom` button replaces the Task 4 `about_label` button, so `#about` stays reachable from the page but no longer has a hero button.

- [ ] **Step 10: Verify**

Run: `just check`
Expected: PASS (`smoke test ok`). Then `just serve` and inspect `/`, `/projects/cityloom/`, `/fr/`, `/fr/projects/cityloom/`: screenshots render in window frames, tags and slice grid show, the language switcher lands on the matching page, and no "Try it" button appears.

- [ ] **Step 11: Commit**

```bash
git add content templates sass scripts/smoke_test.py
git commit -m "feat: add Cityloom case study and featured card" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 7: Accessibility, reflow and motion audit

**Files:**
- Create: `scripts/a11y.mjs`
- Modify: `justfile`, `.gitignore` (already ignores `target/`)

**Interfaces:**
- Consumes: built site served locally; `playwright`, `@axe-core/playwright` from Task 5.
- Produces: `just a11y` exits non-zero on any axe violation (WCAG 2.0/2.1/2.2 A and AA tags), horizontal overflow at 320 px, or an invisible `.reveal` element.

- [ ] **Step 1: Write the audit** — `scripts/a11y.mjs`

```js
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
```

- [ ] **Step 2: Add the justfile recipe**

```make
# Accessibility audit: builds against a local URL, then runs axe + reflow + motion checks
a11y:
    zola build --base-url http://127.0.0.1:4173 --output-dir target/a11y --force
    node scripts/a11y.mjs target/a11y
```
(`--force` lets Zola overwrite an existing output directory. If this Zola version does not accept `--force`, delete `target/a11y` first with `rm -rf target/a11y` and drop the flag.)

- [ ] **Step 3: Run it**

Run: `just a11y`
Expected on a correct build: `a11y ok`. Any failure is a real defect: fix it in the template or Sass (for example a missing label, low contrast, an overflowing French string, a wrapping slice card), keep both languages in step, rebuild and re-run until `a11y ok`. Do not weaken the audit.

- [ ] **Step 4: Manual keyboard pass**

Run `just serve`. On `/` and `/fr/`: press Tab from the page top; the first stop is the skip link and it works; focus rings are visible on every link and button; the language switcher is reachable. Record the result in the commit message body.

- [ ] **Step 5: Commit**

```bash
git add scripts/a11y.mjs justfile
git commit -m "test: add accessibility, reflow and motion audit" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 8: CI, deploy, Dependabot and README

**Files:**
- Create: `.github/workflows/ci.yml`, `.github/workflows/deploy.yml`, `.github/dependabot.yml`, `README.md`
- Modify: `justfile` (`ci` recipe)

**Interfaces:**
- Consumes: all `just` recipes.
- Produces: `just ci` (everything CI runs); required PR check named `site` (job id of `ci.yml`).

- [ ] **Step 1: Add the `ci` recipe** to `justfile`

```make
# What CI runs
ci: check a11y
```

- [ ] **Step 2: Re-resolve action versions before writing the workflows**

Run:
```bash
for r in actions/checkout actions/setup-node actions/upload-pages-artifact actions/deploy-pages taiki-e/install-action; do printf "%s " $r; gh api repos/$r/releases/latest --jq .tag_name; done
gh api repos/taiki-e/install-action/commits/$(gh api repos/taiki-e/install-action/releases/latest --jq .tag_name) --jq .sha
```
Use the printed major versions for the first-party actions below (at planning time: checkout v7, setup-node v7, upload-pages-artifact v5, deploy-pages v5) and the printed SHA plus tag comment for `taiki-e/install-action` (at planning time `ab6895351a88b908e96a4697860d4ffea5e57dbe # v2.87.27`). If newer, use the newer values.

- [ ] **Step 3: Create `.github/workflows/ci.yml`**

```yaml
name: CI

on:
  pull_request:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' }}

jobs:
  site:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v7
      - uses: taiki-e/install-action@ab6895351a88b908e96a4697860d4ffea5e57dbe # v2.87.27
        with:
          tool: just,zola
      - uses: actions/setup-node@v7
        with:
          node-version: lts/*
          cache: npm
      - run: npm ci
      - run: npx playwright install --with-deps chromium
      - run: just ci
```

- [ ] **Step 4: Create `.github/workflows/deploy.yml`**

```yaml
name: Deploy

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: pages
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v7
      - uses: taiki-e/install-action@ab6895351a88b908e96a4697860d4ffea5e57dbe # v2.87.27
        with:
          tool: just,zola
      - run: just build
      - run: python3 scripts/smoke_test.py public
      - uses: actions/upload-pages-artifact@v5
        with:
          path: public

  deploy:
    needs: build
    runs-on: ubuntu-latest
    timeout-minutes: 10
    permissions:
      pages: write
      id-token: write
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - id: deployment
        uses: actions/deploy-pages@v5
```

- [ ] **Step 5: Create `.github/dependabot.yml`**

```yaml
version: 2
updates:
  - package-ecosystem: github-actions
    directory: /
    schedule:
      interval: weekly
  - package-ecosystem: npm
    directory: /
    schedule:
      interval: weekly
```

- [ ] **Step 6: Validate the workflows**

Run: `brew install actionlint && actionlint`
Expected: no output (exit 0).

- [ ] **Step 7: Create `README.md`**

````markdown
# Landovskis Forge

Portfolio site for Landovskis Forge, built with [Zola](https://www.getzola.org) and published to
GitHub Pages at <https://landovskisforge.ca>. Bilingual: English at `/`, French (fr-CA) at `/fr/`.

## Commands

```sh
brew install zola just actionlint   # once
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
- Always edit EN and FR in the same commit. In French use a non-breaking space (` `) before
  `: ; ! ?` and inside `« »`.
- Add a project: add `content/projects/<name>.md` and `<name>.fr.md`, then link it from the home
  template.
- Screenshots: `node scripts/capture_screenshots.mjs` against a local Cityloom build.

## Turning on the live demo

When <https://cityloom.app> is live: set `cityloom_demo_enabled = true` under `[extra]` in
`config.toml` and remove the `skip_prefixes` line from `[link_checker]`.

## Setting the contact email

Set `contact_email` under `[extra]` in `config.toml`. Leave it empty to show GitHub only. The
address is published on a public page.

## One-time GitHub and DNS setup

1. Repository Settings → Pages → Source: **GitHub Actions**.
2. Settings → Pages → Custom domain: `landovskisforge.ca`; enable **Enforce HTTPS** once the
   certificate is issued. Verify the domain first (Account Settings → Pages → Add a domain).
3. DNS at the registrar, apex: four `A` records `185.199.108.153`, `185.199.109.153`,
   `185.199.110.153`, `185.199.111.153` (optionally `AAAA` `2606:50c0:8000::153` through
   `2606:50c0:8003::153`); `www`: a `CNAME` to `<github-user>.github.io`.
4. Branch protection on `main`: require the `site` check.

A `CNAME` file is not needed: Actions-based Pages deploys ignore it.

## Licences

Site code: see the repository. JetBrains Mono is under the SIL Open Font License
(`static/fonts/OFL.txt`).
````

- [ ] **Step 8: Verify locally**

Run: `just ci`
Expected: PASS (`a11y ok` is the last line).

- [ ] **Step 9: Commit**

```bash
git add .github justfile README.md
git commit -m "ci: add CI, Pages deploy and Dependabot" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 9: Final verification and hand-off

**Files:** none created; the checks may modify earlier files.

- [ ] **Step 1: Full local run from a clean state**

Run: `rm -rf public target static/processed_images && just ci`
Expected: PASS.

- [ ] **Step 2: Real-browser visual review**

Run `just serve`. In a real browser (Chrome tools or Playwright screenshots saved to the scratchpad), view `/`, `/projects/cityloom/`, `/fr/`, `/fr/projects/cityloom/` and `/missing` at 1440, 768 and 375 px wide. Check: nothing clipped or overlapping, French strings wrap cleanly, screenshots crisp inside their frames, ember accent only on links/labels/primary buttons, hero grid subtle. Fix any defect in both languages and re-run `just ci`.

- [ ] **Step 3: Copy honesty review**

Read both case-study files and both home files against the Cityloom `README.md` and `PRODUCT.md`. Every statement must be supported there; remove any that is not. Confirm the status paragraph says the data is synthetic placeholder data and no licence is claimed.

- [ ] **Step 4: Push and watch CI** (only after the author confirms the remote exists and says to push)

```bash
git remote -v
git push -u origin main
gh run watch
```
Expected: CI `site` job green; Deploy runs only after the author has set Pages to GitHub Actions.

- [ ] **Step 5: Hand-off to the author** — report in the final message: what was built, the exact `just` commands, and the four open decisions from the spec (contact email, optional map screenshot, `cityloom.app` go-live, DNS and Pages settings) with the README section that covers each. State that the home, case-study and about copy are drafts for the author to edit.

---

## Self-review (spec coverage)

- Purpose/audience, honesty rules: Global Constraints, Task 6 copy, Task 9 step 3.
- Generator, hosting, domain: Tasks 2, 8; `CNAME` replaced by Settings (verified: ignored by Actions deploys).
- Bilingual EN/FR, fr-CA, switcher, hreflang, `lang`, parity check, nbsp: Tasks 1, 2, 6, README.
- Visual direction (palette, type, motifs, motion, responsive, wordmark): Task 3 and Task 2 `brand`.
- IA (home, case study, 404; projects as Markdown): Tasks 2, 4, 6.
- Assets/privacy (no third parties, self-hosted fonts, WebP with dimensions): Tasks 3, 6; smoke test forbids scripts.
- Quality bar (WCAG 2.2 AA, skip link, landmarks, OG, sitemap, feed, robots): Tasks 2, 3, 7; Zola generates sitemap, feed and robots.
- Screenshots (map deferred): Task 5.
- CI/CD per `ci` rules: Task 8.
- Testing section: parity (Task 1), `zola check` (Task 2), smoke (Tasks 2, 4, 6), axe + keyboard + visual (Tasks 7, 9).
- Open decisions: surfaced in README and Task 9 step 5; contact defaults to GitHub only until the author sets an email.
