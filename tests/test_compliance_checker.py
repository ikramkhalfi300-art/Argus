"""Tests for the Compliance Checker (deterministic, no LLM)."""

import re
from pathlib import Path

import pytest

from app.schemas.product_identity import ProductIdentity
from app.services.compliance_checker import (
    BlocklistRule,
    ComplianceResult,
    check_compliance,
    load_rules,
)

BLOCKLIST_PATH = (
    Path(__file__).resolve().parent.parent
    / "knowledge"
    / "risk"
    / "compliance_blocklist.md"
)


# ── Parser tests ────────────────────────────────────────────────────────────


class TestBlocklistParser:
    def test_blocklist_file_exists(self):
        assert BLOCKLIST_PATH.exists(), f"Blocklist not found at {BLOCKLIST_PATH}"

    def test_blocklist_contains_expected_rules(self):
        markdown = BLOCKLIST_PATH.read_text(encoding="utf-8")
        rule_headings = re.findall(r"^## Rule \d+:", markdown, re.MULTILINE)
        assert len(rule_headings) >= 6, (
            f"Expected at least 6 block rules, found {len(rule_headings)}"
        )

    def test_parse_rules_returns_rules(self):
        rules = load_rules(BLOCKLIST_PATH)
        assert len(rules) >= 6, f"Expected >=6 block rules, parsed {len(rules)}"
        for rule in rules:
            assert rule.action == "block"
            assert rule.title

    def test_each_rule_has_at_least_one_match_field(self):
        rules = load_rules(BLOCKLIST_PATH)
        for rule in rules:
            has_categories = len(rule.categories) > 0
            has_subcategories = len(rule.subcategories) > 0
            has_keywords = len(rule.keywords) > 0
            assert has_categories or has_subcategories or has_keywords, (
                f"Rule '{rule.title}' has no match fields"
            )

    def test_each_rule_targets_meta_and_tiktok(self):
        rules = load_rules(BLOCKLIST_PATH)
        for rule in rules:
            platforms_lower = [p.lower() for p in rule.platforms]
            assert "meta" in platforms_lower, f"Rule '{rule.title}' missing 'meta' in platforms"
            assert "tiktok" in platforms_lower, (
                f"Rule '{rule.title}' missing 'tiktok' in platforms"
            )


# ── Blocked-category tests ──────────────────────────────────────────────────


class TestComplianceBlockedCategories:
    """Each test creates a ProductIdentity that SHOULD be flagged by a specific rule."""

    def _check(self, identity: ProductIdentity) -> ComplianceResult:
        rules = load_rules(BLOCKLIST_PATH)
        return check_compliance(identity, rules=rules)

    # ── Rule 1: Dietary Supplements & Weight Loss ──

    def test_block_dietary_supplement_by_category(self):
        identity = ProductIdentity(
            name="Premium Whey Protein Powder",
            category="Sports Nutrition & Dietary Supplements",
            subcategory="Protein Powders",
            normalized_keywords=["whey protein", "muscle recovery", "post workout"],
        )
        result = self._check(identity)
        assert result.flagged, "Dietary supplement by category should be flagged"
        assert any("Dietary Supplements" in r["rule"] for r in result.matched_rules)

    def test_block_weight_loss_by_keyword(self):
        identity = ProductIdentity(
            name="Herbal Fat Burner Capsules",
            category="Health & Wellness",
            subcategory="Herbal Supplements",
            normalized_keywords=[
                "fat burner",
                "weight loss",
                "metabolism boost",
                "natural herbs",
            ],
        )
        result = self._check(identity)
        assert result.flagged, "Weight loss product by keyword should be flagged"
        assert any("Dietary Supplements" in r["rule"] for r in result.matched_rules)

    # ── Rule 2: Weapons & Weapons-Adjacent ──

    def test_block_weapons_by_category(self):
        identity = ProductIdentity(
            name="Tactical Hunting Knife",
            category="Weapons & Tactical Gear",
            subcategory="Hunting Knives",
            normalized_keywords=["hunting knife", "tactical blade", "outdoor gear"],
        )
        result = self._check(identity)
        assert result.flagged, "Weapons-adjacent category should be flagged"
        assert any("Weapons" in r["rule"] for r in result.matched_rules)

    def test_block_firearm_holster_by_subcategory(self):
        identity = ProductIdentity(
            name="Premium Leather Gun Holster",
            category="Outdoor Accessories",
            subcategory="Gun Holsters & Accessories",
            normalized_keywords=["leather holster", "belt holster", "concealed carry"],
        )
        result = self._check(identity)
        assert result.flagged, "Gun holster by subcategory should be flagged"
        rule_names = [r["rule"] for r in result.matched_rules]
        assert any("Weapons" in rn for rn in rule_names)

    def test_block_pepper_spray_by_keyword(self):
        identity = ProductIdentity(
            name="Personal Safety Alarm Keychain",
            category="Safety & Security",
            subcategory="Personal Protection",
            normalized_keywords=["pepper spray", "personal safety", "self defense"],
        )
        result = self._check(identity)
        assert result.flagged, "Pepper spray keyword should be flagged"

    # ── Rule 3: Adult Content ──

    def test_block_adult_content_by_category(self):
        identity = ProductIdentity(
            name="Premium Silicone Massage Wand",
            category="Sexual Wellness Products",
            subcategory="Adult Massagers",
            normalized_keywords=["personal massager", "wellness product", "self care"],
        )
        result = self._check(identity)
        assert result.flagged, "Adult content by category should be flagged"
        assert any("Adult Content" in r["rule"] for r in result.matched_rules)

    def test_block_adult_toy_by_keyword(self):
        identity = ProductIdentity(
            name="Relaxation Massage Device",
            category="Health & Wellness",
            subcategory="Massage Equipment",
            normalized_keywords=[
                "vibrating massager",
                "muscle relaxation",
                "sex toy",
                "intimate massager",
            ],
        )
        result = self._check(identity)
        assert result.flagged, "Adult keyword should be flagged"
        assert any("Adult Content" in r["rule"] for r in result.matched_rules)

    # ── Rule 4: Counterfeit & IP-Infringing ──

    def test_block_counterfeit_by_category(self):
        identity = ProductIdentity(
            name="Luxury Designer Watch Inspired Style",
            category="Counterfeit Goods & Replicas",
            subcategory="Replica Watches",
            normalized_keywords=["replica watch", "luxury style", "affordable alternative"],
        )
        result = self._check(identity)
        assert result.flagged, "Counterfeit category should be flagged"
        assert any("Counterfeit" in r["rule"] for r in result.matched_rules)

    def test_block_replica_sneakers_by_keyword(self):
        identity = ProductIdentity(
            name="Vintage Style Canvas Shoes",
            category="Footwear",
            subcategory="Casual Sneakers",
            normalized_keywords=[
                "canvas sneakers",
                "1:1 quality",
                "designer lookalike",
                "vintage style",
            ],
        )
        result = self._check(identity)
        assert result.flagged, "Replica keyword should be flagged"

    def test_block_replica_by_subcategory(self):
        identity = ProductIdentity(
            name="Fashion Sunglasses",
            category="Accessories",
            subcategory="Replica Sunglasses",
            normalized_keywords=["fashion shades", "UV protection"],
        )
        result = self._check(identity)
        assert result.flagged, "Replica subcategory should be flagged"

    # ── Rule 5: Tobacco, Vaping & Recreational Drugs ──

    def test_block_vape_by_category(self):
        identity = ProductIdentity(
            name="Disposable Vape Pen",
            category="Vaping Products",
            subcategory="Disposable E-Cigarettes",
            normalized_keywords=["vape pen", "nicotine", "portable vape"],
        )
        result = self._check(identity)
        assert result.flagged, "Vape by category should be flagged"
        assert any("Tobacco" in r["rule"] or "Vaping" in r["rule"] for r in result.matched_rules)

    def test_block_cannabis_by_keyword(self):
        identity = ProductIdentity(
            name="Relaxation Herbal Tea Blend",
            category="Beverages",
            subcategory="Herbal Tea",
            normalized_keywords=["herbal tea", "relaxation blend", "CBD", "calming herbs"],
        )
        result = self._check(identity)
        assert result.flagged, "CBD keyword should be flagged"
        assert any("Tobacco" in r["rule"] or "Vaping" in r["rule"] for r in result.matched_rules)

    # ── Rule 6: Prescription & Pharmaceutical ──

    def test_block_prescription_by_subcategory(self):
        identity = ProductIdentity(
            name="Online Doctor Consultation",
            category="Healthcare Services",
            subcategory="Online Pharmacy",
            normalized_keywords=["online doctor", "prescription delivery", "healthcare"],
        )
        result = self._check(identity)
        assert result.flagged, "Online pharmacy should be flagged"
        assert any("Prescription" in r["rule"] or "Pharmaceutical" in r["rule"]
                   for r in result.matched_rules)

    def test_block_sarms_by_keyword(self):
        identity = ProductIdentity(
            name="Advanced Muscle Building Formula",
            category="Sports Nutrition",
            subcategory="Training Supplements",
            normalized_keywords=["muscle growth", "SARMs", "research chemical", "RAD-140"],
        )
        result = self._check(identity)
        assert result.flagged, "SARMs keyword should be flagged"

    # ── Rule 7: Alcohol ──

    def test_block_alcohol_by_category(self):
        identity = ProductIdentity(
            name="Craft IPA Beer Variety Pack",
            category="Alcoholic Beverages",
            subcategory="Craft Beer",
            normalized_keywords=["craft beer", "IPA", "ale", "beverages"],
        )
        result = self._check(identity)
        assert result.flagged, "Alcohol by category should be flagged"
        assert any("Alcohol" in r["rule"] for r in result.matched_rules)

    # ── Rule 8: Gambling ──

    def test_block_gambling_by_category(self):
        identity = ProductIdentity(
            name="Professional Poker Chip Set",
            category="Gambling & Casino",
            subcategory="Poker Supplies",
            normalized_keywords=["poker chips", "card game", "casino quality"],
        )
        result = self._check(identity)
        assert result.flagged, "Gambling by category should be flagged"
        assert any("Gambling" in r["rule"] for r in result.matched_rules)


# ── Clear-pass tests ────────────────────────────────────────────────────────


class TestComplianceClearPass:
    """These products should NEVER be flagged."""

    def _check(self, identity: ProductIdentity) -> ComplianceResult:
        rules = load_rules(BLOCKLIST_PATH)
        return check_compliance(identity, rules=rules)

    def test_clear_kitchen_tools(self):
        identity = ProductIdentity(
            name="Professional Chef's Knife",
            category="Kitchen Tools & Accessories",
            subcategory="Cookware & Cutlery",
            normalized_keywords=[
                "chef knife",
                "kitchen knife",
                "cooking utensils",
                "professional cookware",
            ],
        )
        result = self._check(identity)
        assert not result.flagged, (
            f"Kitchen tools should not be flagged, matched: {result.matched_rules}"
        )
        assert len(result.matched_rules) == 0

    def test_clear_pet_accessories(self):
        identity = ProductIdentity(
            name="Orthopedic Dog Bed for Small Breeds",
            category="Pet Accessories & Supplies",
            subcategory="Pet Beds & Furniture",
            normalized_keywords=[
                "dog bed",
                "pet bed",
                "orthopedic support",
                "small dog bed",
            ],
        )
        result = self._check(identity)
        assert not result.flagged, (
            f"Pet accessories should not be flagged, matched: {result.matched_rules}"
        )
        assert len(result.matched_rules) == 0

    def test_clear_garden_tools(self):
        identity = ProductIdentity(
            name="Ergonomic Garden Pruning Shears",
            category="Garden & Outdoor",
            subcategory="Gardening Tools",
            normalized_keywords=[
                "pruning shears",
                "gardening tools",
                "garden shears",
                "ergonomic handle",
            ],
        )
        result = self._check(identity)
        assert not result.flagged, (
            f"Garden tools should not be flagged, matched: {result.matched_rules}"
        )
        assert len(result.matched_rules) == 0

    def test_clear_office_supplies(self):
        identity = ProductIdentity(
            name="Standing Desk Adjustable Height",
            category="Office Furniture",
            subcategory="Desks & Workstations",
            normalized_keywords=[
                "standing desk",
                "adjustable desk",
                "office furniture",
                "ergonomic workspace",
            ],
        )
        result = self._check(identity)
        assert not result.flagged, (
            f"Office supplies should not be flagged, matched: {result.matched_rules}"
        )
        assert len(result.matched_rules) == 0
