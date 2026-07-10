"""Structure test: every KB file created in Sprint 3.1.1 must have `last_updated` and `Changelog` headers."""

import os
import re

KB_FILES = [
    "knowledge/market/winning_products.md",
    "knowledge/market/market_saturation.md",
    "knowledge/market/seasonality_calendar.md",
    "knowledge/market/niche_taxonomy.md",
    "knowledge/economics/pricing.md",
    "knowledge/economics/margin_benchmarks.md",
    "knowledge/economics/shipping_and_fees.md",
]

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def test_all_files_exist():
    for rel_path in KB_FILES:
        full = os.path.join(ROOT, rel_path)
        assert os.path.isfile(full), f"Missing file: {rel_path}"


def test_last_updated_header():
    for rel_path in KB_FILES:
        full = os.path.join(ROOT, rel_path)
        with open(full, encoding="utf-8") as f:
            content = f.read()
        assert re.search(r"\*\*last_updated\*\*:\s*\d{4}-\d{2}-\d{2}", content), \
            f"{rel_path}: missing '**last_updated**: YYYY-MM-DD' header"


def test_changelog_section():
    for rel_path in KB_FILES:
        full = os.path.join(ROOT, rel_path)
        with open(full, encoding="utf-8") as f:
            content = f.read()
        assert "**Changelog**:" in content or "# Changelog" in content, \
            f"{rel_path}: missing Changelog section"
        assert "Initial version" in content or "- " in content[content.index("Changelog"):content.index("Changelog") + 200], \
            f"{rel_path}: Changelog section appears empty or missing bullet entries"
