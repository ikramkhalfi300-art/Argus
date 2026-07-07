"""
Golden-set tests for the Discovery Agent.

These tests make REAL Anthropic API calls and require ANTHROPIC_API_KEY
to be set in the environment (or a .env file). They are skipped in CI
where the key is not available.

Run locally with: python -m pytest tests/golden_set/ -v
"""

import json
import os

import pytest

from app.agents.discovery_agent import analyze_product
from app.schemas.product_identity import ProductIdentity

pytestmark = [
    pytest.mark.skipif(
        not os.getenv("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set — requires real API calls",
    ),
    pytest.mark.golden_set,
]


def _dump(identity: ProductIdentity) -> str:
    return json.dumps(json.loads(identity.model_dump_json()), indent=2)


@pytest.mark.asyncio
async def test_golden_sony_headphones():
    """Well-known branded product — brand should be returned confidently."""
    identity = await analyze_product("text", "Sony WH-1000XM5 wireless headphones")
    print(f"\n--- Sony WH-1000XM5 ---\n{_dump(identity)}")
    assert isinstance(identity, ProductIdentity)
    assert identity.name and "Sony" in identity.name
    assert len(identity.category) >= 5


@pytest.mark.asyncio
async def test_golden_nike_shoes():
    """Well-known branded product."""
    identity = await analyze_product("text", "Nike Air Max 270 running shoes")
    print(f"\n--- Nike Air Max 270 ---\n{_dump(identity)}")
    assert isinstance(identity, ProductIdentity)
    assert identity.name and "Nike" in identity.name
    assert len(identity.category) >= 3


@pytest.mark.asyncio
async def test_golden_generic_bluetooth_speaker():
    """
    Hallucination-temptation case: generic/white-label product.
    The agent should NOT fabricate a brand name like 'Bose' or 'JBL'.
    """
    identity = await analyze_product(
        "text",
        "Portable bluetooth speaker, water-resistant, 20h battery, "
        "no-name brand sold on Amazon Basics"
    )
    print(f"\n--- Generic Bluetooth Speaker (hallucination guardrail) ---\n{_dump(identity)}")
    assert isinstance(identity, ProductIdentity)
    known_brands = {"bose", "jbl", "sony", "marshall", "ultimate ears", "anker", "bang & olufsen"}
    name_lower = identity.name.lower()
    for brand in known_brands:
        if brand in name_lower:
            pytest.fail(f"Agent fabricated brand name '{brand}' for a generic/no-name product")


@pytest.mark.asyncio
async def test_golden_wool_coat_without_brand():
    """
    Another hallucination-temptation case: a category where luxury brands
    are commonly named, but the input doesn't specify any.
    """
    identity = await analyze_product(
        "text",
        "Womens winter wool coat, long length, charcoal color, mid-range price"
    )
    print(f"\n--- Wool Coat (hallucination guardrail) ---\n{_dump(identity)}")
    assert isinstance(identity, ProductIdentity)
    luxury_brands = {"burberry", "gucci", "prada", "max mara", "loro piana", "moncler"}
    name_lower = identity.name.lower()
    for brand in luxury_brands:
        if brand in name_lower:
            pytest.fail(f"Agent fabricated luxury brand '{brand}' when none was specified")


@pytest.mark.asyncio
async def test_golden_ergonomic_keyboard():
    """Product with clear category — no brand name in input."""
    identity = await analyze_product("text", "Ergonomic split mechanical keyboard with wrist rest")
    print(f"\n--- Ergonomic Keyboard ---\n{_dump(identity)}")
    assert isinstance(identity, ProductIdentity)
    assert len(identity.name) >= 10
    assert len(identity.subcategory) >= 3


@pytest.mark.asyncio
async def test_golden_camping_tent():
    """Outdoor gear — broad category."""
    identity = await analyze_product("text", "4-person waterproof camping tent with rainfly")
    print(f"\n--- Camping Tent ---\n{_dump(identity)}")
    assert isinstance(identity, ProductIdentity)
    assert len(identity.name) >= 10
    assert len(identity.category) >= 5


@pytest.mark.asyncio
async def test_golden_matcha_powder():
    """Food/beverage product."""
    identity = await analyze_product("text", "Organic ceremonial grade matcha green tea powder")
    print(f"\n--- Matcha Powder ---\n{_dump(identity)}")
    assert isinstance(identity, ProductIdentity)
    assert len(identity.name) >= 10
    assert len(identity.category) >= 5


@pytest.mark.asyncio
async def test_golden_white_label_usb_cable():
    """
    Critical hallucination test: white-label/generic USB cable.
    Should NOT claim it's anker/belkin/apple/etc.
    """
    identity = await analyze_product(
        "text",
        "USB-C to USB-C charging cable 6ft, fast charge 100W, nylon braided, generic brand"
    )
    print(f"\n--- Generic USB-C Cable (hallucination guardrail) ---\n{_dump(identity)}")
    assert isinstance(identity, ProductIdentity)
    cable_brands = {"anker", "belkin", "apple", "samsung", "nomad", "ugreen", "baseus"}
    name_lower = identity.name.lower()
    for brand in cable_brands:
        if brand in name_lower:
            pytest.fail(f"Agent fabricated brand '{brand}' for a generic cable")
