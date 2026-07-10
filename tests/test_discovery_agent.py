"""Tests for the Discovery Agent with mocked LLM (CI-safe)."""

import pytest
from pydantic import ValidationError

from app.agents.discovery_agent import (
    analyze_product,
    analyze_product_image,
    analyze_niche_shortlist,
    _build_input_text,
)
from app.schemas.product_identity import ProductIdentity


class TestBuildInputText:
    def test_text_input(self):
        result = _build_input_text("text", "wireless mouse")
        assert "product name: wireless mouse" in result

    def test_url_input_without_scrape(self):
        result = _build_input_text("url", "https://example.com/item")
        assert "product URL:" in result

    def test_url_input_with_scraped_data(self):
        scraped = {"title": "Super Mouse", "price": "$49.99", "variants": ["red", "blue"]}
        result = _build_input_text("url", "https://example.com/mouse", scraped)
        assert "Super Mouse" in result
        assert "$49.99" in result
        assert "red" in result


class TestAnalyzeProductMock:
    @pytest.mark.asyncio
    async def test_returns_valid_identity(self):
        mock = {
            "name": "Mock Product",
            "category": "Electronics",
            "subcategory": "Accessories",
            "variants": ["black", "white"],
            "normalized_keywords": ["mock", "test", "product"],
            "detected_niche": "testing equipment",
            "image_refs": [],
            "source_url": None,
        }
        identity = await analyze_product("text", "mock product", _mock_response=mock)
        assert isinstance(identity, ProductIdentity)
        assert identity.name == "Mock Product"
        assert identity.category == "Electronics"

    @pytest.mark.asyncio
    async def test_fills_missing_name_from_input(self):
        mock = {"category": "Test", "subcategory": "Sub"}
        identity = await analyze_product("text", "Fallback Product", _mock_response=mock)
        assert identity.name == "Fallback Product"

    @pytest.mark.asyncio
    async def test_filters_unknown_fields(self):
        mock = {"name": "Clean", "category": "A", "subcategory": "B",
                "made_up_field": "should be ignored"}
        identity = await analyze_product("text", "x", _mock_response=mock)
        assert identity.name == "Clean"
        assert not hasattr(identity, "made_up_field")

    @pytest.mark.asyncio
    async def test_empty_name_falls_back_to_input(self):
        mock = {"name": "", "category": "Test", "subcategory": "Sub"}
        identity = await analyze_product("text", "fallback", _mock_response=mock)
        assert identity.name == "fallback"
        assert identity.category == "Test"
        assert identity.subcategory == "Sub"

    @pytest.mark.asyncio
    async def test_rejects_empty_name_without_fallback(self):
        mock = {}
        with pytest.raises(ValidationError):
            await analyze_product("text", "", _mock_response=mock)


class TestAnalyzeProductImageMock:
    @pytest.mark.asyncio
    async def test_returns_valid_identity_from_image(self):
        mock = {
            "name": "Image Product",
            "category": "Electronics",
            "subcategory": "Headphones",
            "normalized_keywords": ["wireless", "headphones", "noise cancelling"],
            "detected_niche": "audio enthusiasts",
        }
        identity = await analyze_product_image(
            "https://example.com/img/headphone.jpg",
            _mock_response=mock,
        )
        assert isinstance(identity, ProductIdentity)
        assert identity.name == "Image Product"
        assert identity.detected_niche == "audio enthusiasts"

    @pytest.mark.asyncio
    async def test_image_product_requires_name(self):
        mock = {"category": "Test", "subcategory": "Item"}
        identity = await analyze_product_image(
            "https://example.com/img/item.jpg",
            _mock_response=mock,
        )
        assert identity.name == "Unknown Product"


class TestAnalyzeNicheShortlistMock:
    @pytest.mark.asyncio
    async def test_returns_list_of_identities(self):
        mock = [
            {
                "name": "Niche Product A",
                "category": "Home",
                "subcategory": "Kitchen",
                "normalized_keywords": ["eco", "kitchen"],
                "detected_niche": "eco-conscious home cooks",
            },
            {
                "name": "Niche Product B",
                "category": "Home",
                "subcategory": "Bathroom",
                "normalized_keywords": ["bamboo", "bath"],
                "detected_niche": "zero-waste bathroom",
            },
        ]
        results = await analyze_niche_shortlist("eco-friendly home products", _mock_response=mock)
        assert len(results) == 2
        assert all(isinstance(r, ProductIdentity) for r in results)
        assert results[0].name == "Niche Product A"
        assert results[1].name == "Niche Product B"

    @pytest.mark.asyncio
    async def test_all_candidates_valid(self):
        mock = [
            {"name": "P1", "category": "A", "subcategory": "B"},
            {"name": "P2", "category": "C", "subcategory": "D"},
        ]
        results = await analyze_niche_shortlist("test", _mock_response=mock)
        for r in results:
            assert r.name
            assert r.category
            assert r.subcategory
