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

from app.agents.discovery_agent import (
    analyze_product,
    analyze_product_image,
    analyze_niche_shortlist,
)
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


def _dump_list(identities: list[ProductIdentity]) -> str:
    return json.dumps([json.loads(i.model_dump_json()) for i in identities], indent=2)


# ────────────────────────────── Text-path tests (Sprint 1.1.2) ──────────────────────────────


@pytest.mark.asyncio
async def test_golden_sony_headphones():
    """Well-known branded product — brand should be returned confidently."""
    identity = await analyze_product("text", "Sony WH-1000XM5 wireless headphones")
    print(f"\n--- Sony WH-1000XM5 ---\n{_dump(identity)}")
    assert isinstance(identity, ProductIdentity)
    assert identity.name and "Sony" in identity.name
    assert len(identity.category) >= 5
    assert identity.normalized_keywords, "Prompt requires 5-10 keywords"
    assert len(identity.normalized_keywords) >= 3
    assert identity.detected_niche is not None, "Prompt requires detected_niche"


@pytest.mark.asyncio
async def test_golden_nike_shoes():
    """Well-known branded product."""
    identity = await analyze_product("text", "Nike Air Max 270 running shoes")
    print(f"\n--- Nike Air Max 270 ---\n{_dump(identity)}")
    assert isinstance(identity, ProductIdentity)
    assert identity.name and "Nike" in identity.name
    assert len(identity.category) >= 3
    assert identity.normalized_keywords, "Prompt requires 5-10 keywords"
    assert len(identity.normalized_keywords) >= 3
    assert identity.detected_niche is not None, "Prompt requires detected_niche"


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
    assert identity.normalized_keywords, "Prompt requires 5-10 keywords"
    assert identity.detected_niche is not None, "Prompt requires detected_niche"
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
    assert identity.normalized_keywords, "Prompt requires 5-10 keywords"
    assert identity.detected_niche is not None, "Prompt requires detected_niche"
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
    assert identity.normalized_keywords, "Prompt requires 5-10 keywords"
    assert identity.detected_niche is not None, "Prompt requires detected_niche"


@pytest.mark.asyncio
async def test_golden_camping_tent():
    """Outdoor gear — broad category."""
    identity = await analyze_product("text", "4-person waterproof camping tent with rainfly")
    print(f"\n--- Camping Tent ---\n{_dump(identity)}")
    assert isinstance(identity, ProductIdentity)
    assert len(identity.name) >= 10
    assert len(identity.category) >= 5
    assert identity.normalized_keywords, "Prompt requires 5-10 keywords"
    assert identity.detected_niche is not None, "Prompt requires detected_niche"


@pytest.mark.asyncio
async def test_golden_matcha_powder():
    """Food/beverage product."""
    identity = await analyze_product("text", "Organic ceremonial grade matcha green tea powder")
    print(f"\n--- Matcha Powder ---\n{_dump(identity)}")
    assert isinstance(identity, ProductIdentity)
    assert len(identity.name) >= 10
    assert len(identity.category) >= 5
    assert identity.normalized_keywords, "Prompt requires 5-10 keywords"
    assert identity.detected_niche is not None, "Prompt requires detected_niche"


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
    assert identity.normalized_keywords, "Prompt requires 5-10 keywords"
    assert identity.detected_niche is not None, "Prompt requires detected_niche"
    cable_brands = {"anker", "belkin", "apple", "samsung", "nomad", "ugreen", "baseus"}
    name_lower = identity.name.lower()
    for brand in cable_brands:
        if brand in name_lower:
            pytest.fail(f"Agent fabricated brand '{brand}' for a generic cable")


# ────────────────────────────── Image-path tests (Sprint 1.1.3) ──────────────────────────────


@pytest.mark.asyncio
async def test_golden_image_headphone():
    """Identify product from a real Sony WH-1000XM5 product photo."""
    identity = await analyze_product_image(
        "https://m.media-amazon.com/images/I/51ApBB0G39L._AC_US1000_.jpg"
    )
    print(f"\n--- Image: Sony Headphone ---\n{_dump(identity)}")
    assert isinstance(identity, ProductIdentity)
    assert identity.normalized_keywords, "Image path must produce keywords"
    assert len(identity.normalized_keywords) >= 3
    assert identity.detected_niche is not None, "Image path must detect a niche"
    assert len(identity.category) >= 3
    assert len(identity.subcategory) >= 3


@pytest.mark.asyncio
async def test_golden_image_speaker():
    """Identify product from a real Anker Soundcore 2 product photo."""
    identity = await analyze_product_image(
        "https://cdn11.bigcommerce.com/s-sp9oc95xrw/products/12406/images/57549/anker-soundcore__05718.1681718172.386.513.jpg?c=2"
    )
    print(f"\n--- Image: Bluetooth Speaker ---\n{_dump(identity)}")
    assert isinstance(identity, ProductIdentity)
    assert identity.normalized_keywords, "Image path must produce keywords"
    assert len(identity.normalized_keywords) >= 3
    assert identity.detected_niche is not None


@pytest.mark.asyncio
async def test_golden_image_shoe():
    """Identify product from a real Nike Air Max 270 product photo."""
    identity = await analyze_product_image(
        "https://static.nike.com/a/images/t_default/u_9ddf04c7-2a9a-4d76-add1-d15af8f0263d,c_scale,fl_relative,w_1.0,h_1.0,fl_layer_apply/awjogtdnqxniqqk0wpgf/AIR+MAX+270.png"
    )
    print(f"\n--- Image: Nike Shoe ---\n{_dump(identity)}")
    assert isinstance(identity, ProductIdentity)
    assert identity.normalized_keywords, "Image path must produce keywords"
    assert len(identity.normalized_keywords) >= 3
    assert identity.detected_niche is not None


@pytest.mark.asyncio
async def test_golden_image_camera():
    """Identify product from a real Canon EOS R5 product photo."""
    identity = await analyze_product_image(
        "https://cdn.media.amplience.net/i/canon/eos-r5_front_rf24-105mmf4lisusm_square_32c26ad194234d42b3cd9e582a21c99b"
    )
    print(f"\n--- Image: Camera ---\n{_dump(identity)}")
    assert isinstance(identity, ProductIdentity)
    assert identity.normalized_keywords, "Image path must produce keywords"
    assert len(identity.normalized_keywords) >= 3
    assert identity.detected_niche is not None


@pytest.mark.asyncio
async def test_golden_image_matcha():
    """Identify product from a real Jade Leaf Matcha product photo."""
    identity = await analyze_product_image(
        "https://www.jadeleafmatcha.com/cdn/shop/files/ceremonial-matcha-barista-tin-30g-front_d309535f-9cca-4602-be9c-f7102ff35033.png?v=1763749245"
    )
    print(f"\n--- Image: Matcha Tea ---\n{_dump(identity)}")
    assert isinstance(identity, ProductIdentity)
    assert identity.normalized_keywords, "Image path must produce keywords"
    assert len(identity.normalized_keywords) >= 3
    assert identity.detected_niche is not None


# ────────────────────────────── Niche-shortlist tests (Sprint 1.1.3) ──────────────────────────────


def _check_no_duplicates(candidates: list[ProductIdentity]) -> None:
    """Assert that no two candidates share near-identical name+category combos."""
    seen: set[tuple[str, str]] = set()
    for c in candidates:
        key = (c.name.strip().lower(), c.category.strip().lower())
        if key in seen:
            pytest.fail(f"Duplicate candidate detected: name='{c.name}', category='{c.category}'")
        seen.add(key)


@pytest.mark.asyncio
async def test_golden_niche_eco_home():
    """Niche shortlist for eco-friendly home products."""
    candidates = await analyze_niche_shortlist(
        "Eco-friendly kitchen and home products for zero-waste living"
    )
    print(f"\n--- Niche: Eco Home ---\n{_dump_list(candidates)}")
    assert len(candidates) >= 3, "Niche shortlist must contain at least 3 candidates"
    assert all(isinstance(c, ProductIdentity) for c in candidates)
    for c in candidates:
        assert c.name, "Each candidate must have a name"
        assert c.category, "Each candidate must have a category"
        assert c.subcategory, "Each candidate must have a subcategory"
        assert c.normalized_keywords, "Each candidate must have keywords"
    _check_no_duplicates(candidates)


@pytest.mark.asyncio
async def test_golden_niche_pet_accessories():
    """Niche shortlist for pet accessories — distinct products expected."""
    candidates = await analyze_niche_shortlist(
        "Pet accessories for small dogs — collars, leashes, beds, and toys"
    )
    print(f"\n--- Niche: Pet Accessories ---\n{_dump_list(candidates)}")
    assert len(candidates) >= 3, "Niche shortlist must contain at least 3 candidates"
    for c in candidates:
        assert c.name
        assert c.category
        assert c.subcategory
    _check_no_duplicates(candidates)


@pytest.mark.asyncio
async def test_golden_niche_home_office():
    """Niche shortlist for home office ergonomic accessories under $50."""
    candidates = await analyze_niche_shortlist(
        "Home office ergonomic accessories under $50"
    )
    print(f"\n--- Niche: Home Office ---\n{_dump_list(candidates)}")
    assert len(candidates) >= 3, "Niche shortlist must contain at least 3 candidates"
    for c in candidates:
        assert c.name
        assert c.category
        assert c.subcategory
    _check_no_duplicates(candidates)
