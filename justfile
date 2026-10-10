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

check-contrast:
    python3 scripts/check_contrast.py

# Everything that must pass before merging
check: test-scripts check-i18n check-contrast
    zola check
    zola build
    python3 scripts/smoke_test.py public

# Accessibility audit: builds against a local URL, then runs axe + reflow + motion checks
a11y:
    zola build --base-url http://127.0.0.1:4173 --output-dir target/a11y --force
    node scripts/a11y.mjs target/a11y

# What CI runs
ci: check a11y
