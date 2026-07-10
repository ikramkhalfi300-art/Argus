"""
Golden-set tests for the Validation Agent (LLM gray-area judgment).

These tests make REAL Anthropic API calls and require ANTHROPIC_API_KEY
to be set in the environment (or a .env file). They are skipped in CI
where the key is not available.

Run locally with: python -m pytest tests/agent_prompt_tests/ -v

IMPORTANT: These tests print the LLM's reasoning text to stdout so the
reviewer can manually evaluate judgment quality (per Review Gate 1.2.2).
"""

import json
import os

import pytest

from app.agents.validation_agent import run_validation_judgment
from app.schemas.product_identity import ProductIdentity
from app.schemas.validation_result import ValidationJudgment
from app.services.compliance_checker import check_compliance

pytestmark = [
    pytest.mark.skipif(
        not os.getenv("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set — requires real API calls",
    ),
    pytest.mark.golden_set,
]


def _dump_judgment(j: ValidationJudgment) -> str:
    return json.dumps(json.loads(j.model_dump_json()), indent=2)


def _check_deterministic(product: ProductIdentity) -> dict:
    """Run the deterministic check independently so we know what it says."""
    result = check_compliance(product)
    return {"flagged": result.flagged, "matched_rules": result.matched_rules}


def _print_product(product: ProductIdentity) -> None:
    print(f"  name: {product.name}")
    print(f"  category: {product.category}")
    print(f"  subcategory: {product.subcategory}")
    print(f"  keywords: {product.normalized_keywords}")
    print(f"  niche: {product.detected_niche}")


# ────────────────────────────── Gray-Area Cases ──────────────────────────────


@pytest.mark.asyncio
async def test_gray_slip_past_posture_corrector():
    """
    Gray area: ergonomic posture corrector back brace.
    This is health-adjacent but not a supplement or medication.
    The deterministic check should NOT flag it. The LLM should evaluate
    whether it falls under restricted advertising (health claims).
    """
    product = ProductIdentity(
        name="Adjustable Posture Corrector Back Brace for Men and Women",
        category="Health & Wellness",
        subcategory="Posture Support & Braces",
        normalized_keywords=[
            "posture corrector",
            "back brace",
            "ergonomic support",
            "upper back straightener",
            "shoulder support",
        ],
        detected_niche="office workers with back pain",
    )
    det = _check_deterministic(product)
    judgment = await run_validation_judgment(product)

    print(f"\n=== SLIP-PAST CASE: Posture Corrector ===")
    _print_product(product)
    print(f"\nDeterministic check: {json.dumps(det, indent=2)}")
    print(f"LLM judgment:\n{_dump_judgment(judgment)}")

    # Deterministic should NOT flag this (not a blocked category)
    assert not det["flagged"], (
        "Deterministic check should not flag a posture corrector"
    )
    # LLM judgment is the interesting part — the reviewer must check reasoning
    assert isinstance(judgment, ValidationJudgment)
    assert judgment.reasoning, "LLM must provide reasoning"


@pytest.mark.asyncio
async def test_gray_slip_past_essential_oil_diffuser():
    """
    Gray area: aromatherapy essential oil diffuser.
    Wellness-adjacent but not a health claim per se.
    The deterministic check should NOT flag it.
    """
    product = ProductIdentity(
        name="Ultrasonic Aromatherapy Essential Oil Diffuser",
        category="Home & Decor",
        subcategory="Air Fresheners & Diffusers",
        normalized_keywords=[
            "essential oil diffuser",
            "aromatherapy diffuser",
            "ultrasonic humidifier",
            "room fragrance",
            "calming mist",
        ],
        detected_niche="home wellness enthusiasts",
    )
    det = _check_deterministic(product)
    judgment = await run_validation_judgment(product)

    print(f"\n=== SLIP-PAST CASE: Essential Oil Diffuser ===")
    _print_product(product)
    print(f"\nDeterministic check: {json.dumps(det, indent=2)}")
    print(f"LLM judgment:\n{_dump_judgment(judgment)}")

    assert not det["flagged"]
    assert isinstance(judgment, ValidationJudgment)
    assert judgment.reasoning


@pytest.mark.asyncio
async def test_gray_slip_past_resistance_bands():
    """
    Gray area: resistance bands for exercise / fitness.
    Fitness equipment — not a supplement or health claim.
    """
    product = ProductIdentity(
        name="Set of 5 Resistance Bands for Exercise, Pilates, Yoga",
        category="Sports & Fitness",
        subcategory="Exercise Bands & Tubes",
        normalized_keywords=[
            "resistance bands",
            "exercise bands",
            "workout bands",
            "pilates equipment",
            "home gym accessories",
        ],
        detected_niche="home fitness enthusiasts",
    )
    det = _check_deterministic(product)
    judgment = await run_validation_judgment(product)

    print(f"\n=== SLIP-PAST CASE: Resistance Bands ===")
    _print_product(product)
    print(f"\nDeterministic check: {json.dumps(det, indent=2)}")
    print(f"LLM judgment:\n{_dump_judgment(judgment)}")

    assert not det["flagged"]
    assert isinstance(judgment, ValidationJudgment)
    assert judgment.reasoning


@pytest.mark.asyncio
async def test_gray_clear_pass_kitchen_apron():
    """
    Clear pass: a kitchen apron. Neither deterministic nor LLM should flag.
    """
    product = ProductIdentity(
        name="Organic Cotton Kitchen Apron with Adjustable Neck",
        category="Kitchen Tools & Accessories",
        subcategory="Aprons & Kitchen Textiles",
        normalized_keywords=[
            "kitchen apron",
            "cooking apron",
            "cotton apron",
            "adjustable apron",
            "chef apron",
        ],
        detected_niche="home cooks",
    )
    det = _check_deterministic(product)
    judgment = await run_validation_judgment(product)

    print(f"\n=== CLEAR PASS: Kitchen Apron ===")
    _print_product(product)
    print(f"\nDeterministic check: {json.dumps(det, indent=2)}")
    print(f"LLM judgment:\n{_dump_judgment(judgment)}")

    assert not det["flagged"]
    assert not judgment.is_flagged, (
        f"LLM should not flag a clear-pass kitchen apron. "
        f"Reasoning: {judgment.reasoning}"
    )
    assert judgment.reasoning


@pytest.mark.asyncio
async def test_gray_clear_pass_bamboo_cutting_board():
    """
    Clear pass: bamboo cutting board. Should pass everything.
    """
    product = ProductIdentity(
        name="Organic Bamboo Cutting Board for Kitchen",
        category="Kitchen Tools & Accessories",
        subcategory="Cutting Boards & Choppers",
        normalized_keywords=[
            "bamboo cutting board",
            "kitchen cutting board",
            "chopping board",
            "wooden cutting board",
            "eco-friendly kitchen",
        ],
        detected_niche="eco-conscious home cooks",
    )
    det = _check_deterministic(product)
    judgment = await run_validation_judgment(product)

    print(f"\n=== CLEAR PASS: Bamboo Cutting Board ===")
    _print_product(product)
    print(f"\nDeterministic check: {json.dumps(det, indent=2)}")
    print(f"LLM judgment:\n{_dump_judgment(judgment)}")

    assert not det["flagged"]
    assert not judgment.is_flagged, (
        f"LLM should not flag a bamboo cutting board. "
        f"Reasoning: {judgment.reasoning}"
    )
    assert judgment.reasoning


@pytest.mark.asyncio
async def test_gray_therapeutic_massage_gun():
    """
    Gray area: massage gun described as 'therapeutic'.
    The word 'therapeutic' could trigger health-claim concerns.
    Deterministic should NOT flag (not a blocked category).
    LLM should evaluate the gray area.
    """
    product = ProductIdentity(
        name="Deep Tissue Massage Gun for Muscle Recovery",
        category="Health & Wellness",
        subcategory="Massage Equipment & Tools",
        normalized_keywords=[
            "massage gun",
            "percussion massager",
            "muscle recovery",
            "deep tissue massage",
            "handheld massager",
        ],
        detected_niche="athletes and fitness enthusiasts",
    )
    det = _check_deterministic(product)
    judgment = await run_validation_judgment(product)

    print(f"\n=== GRAY AREA: Massage Gun ('therapeutic' claim risk) ===")
    _print_product(product)
    print(f"\nDeterministic check: {json.dumps(det, indent=2)}")
    print(f"LLM judgment:\n{_dump_judgment(judgment)}")

    assert not det["flagged"]
    assert isinstance(judgment, ValidationJudgment)
    assert judgment.reasoning


@pytest.mark.asyncio
async def test_gray_clear_pass_pet_leash():
    """
    Clear pass: pet leash. Should pass everything.
    """
    product = ProductIdentity(
        name="Reflective Dog Leash for Walking, 5ft Nylon",
        category="Pet Accessories & Supplies",
        subcategory="Pet Collars & Leashes",
        normalized_keywords=[
            "dog leash",
            "pet leash",
            "nylon dog leash",
            "reflective leash",
            "walking leash",
        ],
        detected_niche="dog owners",
    )
    det = _check_deterministic(product)
    judgment = await run_validation_judgment(product)

    print(f"\n=== CLEAR PASS: Pet Leash ===")
    _print_product(product)
    print(f"\nDeterministic check: {json.dumps(det, indent=2)}")
    print(f"LLM judgment:\n{_dump_judgment(judgment)}")

    assert not det["flagged"]
    assert not judgment.is_flagged, (
        f"LLM should not flag a pet leash. "
        f"Reasoning: {judgment.reasoning}"
    )


@pytest.mark.asyncio
async def test_gray_crypto_trading_bot():
    """
    Genuinely gray case: automated crypto trading bot.

    Financial/cryptocurrency services are restricted on Meta and TikTok
    but are NOT covered by compliance_blocklist.md at all.

    Deterministic check should NOT flag (no match in blocklist rules).
    LLM SHOULD flag as a restricted financial service.
    """
    product = ProductIdentity(
        name="Automated Crypto Trading Bot with AI Signals",
        category="Finance & Software",
        subcategory="Trading Software & Tools",
        normalized_keywords=[
            "automated trading",
            "crypto bot",
            "AI trading signals",
            "passive income",
            "market analysis",
        ],
        detected_niche="cryptocurrency investors",
    )
    det = _check_deterministic(product)
    judgment = await run_validation_judgment(product)

    print(f"\n=== GRAY AREA: Crypto Trading Bot (financial gap) ===")
    _print_product(product)
    print(f"\nDeterministic check: {json.dumps(det, indent=2)}")
    print(f"LLM judgment:\n{_dump_judgment(judgment)}")

    assert not det["flagged"], (
        "Deterministic must NOT flag crypto — it's not in compliance_blocklist.md"
    )
    assert judgment.is_flagged, (
        "LLM should flag financial/crypto product as restricted. "
        f"Reasoning: {judgment.reasoning}"
    )


@pytest.mark.asyncio
async def test_gray_skin_tag_remover():
    """
    Genuinely gray case: skin tag remover cream.

    This product makes implied medical claims (removes skin tags, moles)
    but does NOT match any category/subcategory/keyword in the blocklist.
    The blocklist covers supplements, weapons, adult, counterfeit, tobacco,
    pharmaceuticals, alcohol, gambling — NOT general beauty/skincare products
    making unsubstantiated medical claims.

    Deterministic should NOT flag. LLM SHOULD flag as unsubstantiated
    health/medical claims.
    """
    product = ProductIdentity(
        name="Skin Tag & Mole Remover Cream - Fast Acting Formula",
        category="Beauty & Personal Care",
        subcategory="Skin Care Treatments",
        normalized_keywords=[
            "skin tag remover",
            "mole removal cream",
            "skin care treatment",
            "beauty skincare",
            "gentle removal formula",
        ],
        detected_niche="people seeking at-home skincare treatments",
    )
    det = _check_deterministic(product)
    judgment = await run_validation_judgment(product)

    print(f"\n=== GRAY AREA: Skin Tag Remover (unsubstantiated medical claims) ===")
    _print_product(product)
    print(f"\nDeterministic check: {json.dumps(det, indent=2)}")
    print(f"LLM judgment:\n{_dump_judgment(judgment)}")

    assert not det["flagged"], (
        "Deterministic must NOT flag skin tag remover — beauty products "
        "are not in compliance_blocklist.md"
    )
    assert judgment.is_flagged, (
        "LLM should flag for unsubstantiated medical claims. "
        f"Reasoning: {judgment.reasoning}"
    )


# ────────────────────────────── Clear-Block Cases ──────────────────────────────


@pytest.mark.asyncio
async def test_clear_block_weight_loss_supplement():
    """
    Clear block: weight loss supplement. Both deterministic and LLM should flag.
    """
    product = ProductIdentity(
        name="Advanced Fat Burner Weight Loss Pills",
        category="Dietary Supplements & Weight Loss",
        subcategory="Fat Burner Pills",
        normalized_keywords=[
            "fat burner",
            "weight loss",
            "thermogenic",
            "appetite suppressant",
            "metabolism boost",
        ],
        detected_niche="people trying to lose weight",
    )
    det = _check_deterministic(product)
    judgment = await run_validation_judgment(product)

    print(f"\n=== CLEAR BLOCK: Weight Loss Supplement ===")
    _print_product(product)
    print(f"\nDeterministic check: {json.dumps(det, indent=2)}")
    print(f"LLM judgment:\n{_dump_judgment(judgment)}")

    assert det["flagged"], "Deterministic should flag this"
    assert judgment.is_flagged, (
        f"LLM should also flag this. Reasoning: {judgment.reasoning}"
    )
