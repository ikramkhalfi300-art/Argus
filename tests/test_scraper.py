"""Unit tests for product_page_scraper using saved HTML fixtures."""

from pathlib import Path

import pytest
from bs4 import BeautifulSoup

from integrations.product_page_scraper import (
    _extract_description,
    _extract_images,
    _extract_price,
    _extract_title,
    _extract_variants,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "html"


def _soup(name: str) -> BeautifulSoup:
    html = (FIXTURES / name).read_text(encoding="utf-8")
    return BeautifulSoup(html, "html.parser")


class TestScraperExtractors:
    def test_extract_title_from_og(self):
        soup = _soup("product_page.html")
        assert _extract_title(soup) == "Premium Wireless Headphones - ANC Pro X1"

    def test_extract_price(self):
        soup = _soup("product_page.html")
        price = _extract_price(soup)
        assert "299.99" in price

    def test_extract_description(self):
        soup = _soup("product_page.html")
        desc = _extract_description(soup)
        assert "noise cancelling" in desc.lower()

    def test_extract_images(self):
        soup = _soup("product_page.html")
        imgs = _extract_images(soup, "https://example.com")
        assert len(imgs) >= 1
        assert any("headphones-main" in img for img in imgs)

    def test_extract_variants(self):
        soup = _soup("product_page.html")
        variants = _extract_variants(soup)
        assert "Black" in variants
        assert "White" in variants
        assert "Navy Blue" in variants

    def test_minimal_page_graceful(self):
        soup = _soup("minimal_page.html")
        assert _extract_title(soup) == "Plain Widget"
        assert _extract_price(soup) == ""
        assert _extract_description(soup) == ""  # no meta desc or classed elements
        imgs = _extract_images(soup, "https://example.com")
        assert len(imgs) >= 1
        assert _extract_variants(soup) == []
