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
