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
