"""Tests for the Discovery Agent with mocked LLM (CI-safe)."""

import pytest
from pydantic import ValidationError

from app.agents.discovery_agent import analyze_product, _build_input_text
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
