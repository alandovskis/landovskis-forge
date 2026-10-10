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
