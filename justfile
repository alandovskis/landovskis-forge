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
