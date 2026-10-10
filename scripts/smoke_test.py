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
    ("projects/cityloom/index.html", "en", "fr/projects/cityloom/index.html"),
    ("fr/projects/cityloom/index.html", "fr", "projects/cityloom/index.html"),
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
        if "projects" not in name and 'id="about"' not in path.read_text(encoding="utf-8"):
            problems.append(f"{name}: missing #about section")
        for tag in re.findall(r"<img[^>]*>", path.read_text(encoding="utf-8")):
            if "width=" not in tag or "height=" not in tag or "alt=" not in tag:
                problems.append(f"{name}: <img> without width, height and alt: {tag[:60]}")
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
            if not (link.startswith(("http://", "https://", "#"))):
                problems.append(f"404.html: relative URL {link!r} breaks at nested paths")
        for name, _, _ in PAGES:
            if "projects" not in name and name in pages and pages[name].canonical not in page.hrefs:
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
