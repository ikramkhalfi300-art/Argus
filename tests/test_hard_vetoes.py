"""Unit tests for hard veto override rules (Sprint 2.1.3).

Each veto rule has:
  1. A trigger test — mock scenario designed to hit that specific rule.
  2. A clean test — mock scenario that should NOT trigger the rule.

Plus the critical "high score but vetoed" scenario: a set of agent outputs
that produce composite_score >= 75 (GO range) via Sprint 2.1.2's calculator
but also trigger a veto — confirming the veto check overrides regardless.

All mock data hand-constructed with explicit expected values.
"""

import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parents[1]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import pytest
from app.schemas.agent_output import AgentOutput
from scoring.veto_rules.hard_vetoes import check_hard_vetoes


# ── Helper ──────────────────────────────────────────────────────────────────

def _make_agent(
    name: str,
    pillar: str,
    score: float,
    raw_findings: dict | None = None,
    completeness: float = 100.0,
) -> AgentOutput:
    return AgentOutput(
        agent_name=name,
        pillar=pillar,
        sub_score=score,
        confidence="Medium",
        evidence=[{"claim": "Test", "citation": "Source"}],
        data_completeness_pct=completeness,
        raw_findings=raw_findings or {},
    )


# ── Veto 1: Margin veto (net_margin_pct_after_ads < 15%) ───────────────────

def test_margin_veto_triggers():
    """net_margin_pct_after_ads = 12.0 (< 15) → veto triggered."""
    outputs = [
        _make_agent("margin_analysis_agent", "unit_economics", 30.0, {
            "net_margin_pct_after_ads": 12.0,
            "gross_margin_pct": 50.0,
            "breakeven_cpa": 8.50,
            "contribution_margin_per_unit": 4.20,
        }),
    ]
    result = check_hard_vetoes(outputs)
    assert result["vetoed"] is True
    assert any("margin" in r.lower() for r in result["triggered_rules"])


def test_margin_veto_clean():
    """net_margin_pct_after_ads = 22.5 (>= 15) → veto NOT triggered."""
    outputs = [
        _make_agent("margin_analysis_agent", "unit_economics", 50.0, {
            "net_margin_pct_after_ads": 22.5,
            "gross_margin_pct": 65.0,
            "breakeven_cpa": 18.75,
            "contribution_margin_per_unit": 12.30,
        }),
    ]
    result = check_hard_vetoes(outputs)
    assert result["vetoed"] is False


def test_margin_veto_absent_agent():
    """margin_analysis_agent not present → unverifiable, not triggered."""
    outputs = [
        _make_agent("fb_ads_analysis_agent", "demand_strength", 80, {}),
    ]
    result = check_hard_vetoes(outputs)
    assert result["vetoed"] is False
    assert any("margin" in r.lower() for r in result["unverifiable_rules"])


# ── Veto 2: Compliance blocklist veto ───────────────────────────────────────

def test_compliance_veto_triggers():
    """legal_risk = "Severe" → veto triggered."""
    outputs = [
        _make_agent("risk_analysis_agent", "risk_profile", 10.0, {
            "legal_risk": "Severe",
            "platform_policy_risk": "Low",
            "supplier_risk": "Low",
            "seasonality_risk": "Low",
            "reputational_risk": "Low",
            "overall_risk_level": "Severe",
        }),
    ]
    result = check_hard_vetoes(outputs)
    assert result["vetoed"] is True
    assert any("compliance" in r.lower() or "legal" in r.lower() for r in result["triggered_rules"])


def test_compliance_veto_platform_policy_triggers():
    """platform_policy_risk = "Severe" → veto triggered."""
    outputs = [
        _make_agent("risk_analysis_agent", "risk_profile", 10.0, {
            "legal_risk": "Low",
            "platform_policy_risk": "Severe",
            "overall_risk_level": "Severe",
        }),
    ]
    result = check_hard_vetoes(outputs)
    assert result["vetoed"] is True


def test_compliance_veto_clean():
    """All risk levels Low/Moderate → veto NOT triggered."""
    outputs = [
        _make_agent("risk_analysis_agent", "risk_profile", 80.0, {
            "legal_risk": "Low",
            "platform_policy_risk": "Low",
            "supplier_risk": "Moderate",
            "seasonality_risk": "Low",
            "reputational_risk": "Low",
            "overall_risk_level": "Low",
        }),
    ]
    result = check_hard_vetoes(outputs)
    assert result["vetoed"] is False


def test_compliance_veto_absent_agent():
    """risk_analysis_agent not present → unverifiable."""
    outputs = [
        _make_agent("fb_ads_analysis_agent", "demand_strength", 80, {}),
    ]
    result = check_hard_vetoes(outputs)
    assert result["vetoed"] is False
    assert any("compliance" in r.lower() or "blocklist" in r.lower()
               for r in result["unverifiable_rules"])


# ── Veto 3: Creative angles veto (viable_angles < 2) ────────────────────────

def test_creative_angles_veto_triggers():
    """Only 1 viable angle → veto triggered."""
    outputs = [
        _make_agent("creative_opportunity_agent", "creative_runway", 20.0, {
            "viable_angles": ["only one angle"],
            "fatigue_risk_level": "High",
        }),
    ]
    result = check_hard_vetoes(outputs)
    assert result["vetoed"] is True
    assert any("creative" in r.lower() for r in result["triggered_rules"])


def test_creative_angles_veto_zero_angles():
    """Zero viable angles → veto triggered."""
    outputs = [
        _make_agent("creative_opportunity_agent", "creative_runway", 0.0, {
            "viable_angles": [],
            "fatigue_risk_level": "Critical",
        }),
    ]
    result = check_hard_vetoes(outputs)
    assert result["vetoed"] is True


def test_creative_angles_veto_clean():
    """3 viable angles → veto NOT triggered."""
    outputs = [
        _make_agent("creative_opportunity_agent", "creative_runway", 75.0, {
            "viable_angles": [
                "angle A", "angle B", "angle C",
            ],
            "fatigue_risk_level": "Low",
        }),
    ]
    result = check_hard_vetoes(outputs)
    assert result["vetoed"] is False


def test_creative_angles_veto_absent_agent():
    """creative_opportunity_agent not present → unverifiable."""
    outputs = [
        _make_agent("fb_ads_analysis_agent", "demand_strength", 80, {}),
    ]
    result = check_hard_vetoes(outputs)
    assert result["vetoed"] is False
    assert any("creative" in r.lower() for r in result["unverifiable_rules"])


# ── Veto 4: Saturation veto ──────────────────────────────────────────────────

def test_saturation_veto_triggers():
    """>5 advertisers, 60+ days, no gaps, all angles crowded → veto triggered."""
    outputs = [
        _make_agent("market_saturation_agent", "competitive_saturation", 20.0, {
            "active_advertiser_count": 12,
            "avg_ad_run_duration_days": 90,
            "market_stage": "Peak",
        }),
        _make_agent("competitor_analysis_agent", "competitive_saturation", 30.0, {
            "top_competitors": [{"name": "Store A", "estimated_scale": "large", "price": 29.99}],
            "gaps_identified": [],
            "competitive_barrier": "High",
        }),
        _make_agent("creative_opportunity_agent", "creative_runway", 10.0, {
            "viable_angles": ["one tired angle"],
            "angle_saturation_map": {"one tired angle": "crowded"},
        }),
    ]
    result = check_hard_vetoes(outputs)
    assert result["vetoed"] is True
    assert any("saturat" in r.lower() for r in result["triggered_rules"])


def test_saturation_veto_clean_low_advertisers():
    """Only 3 advertisers (< 5 threshold) → veto NOT triggered."""
    outputs = [
        _make_agent("market_saturation_agent", "competitive_saturation", 80.0, {
            "active_advertiser_count": 3,
            "avg_ad_run_duration_days": 90,
            "market_stage": "Growing",
        }),
    ]
    result = check_hard_vetoes(outputs)
    assert result["vetoed"] is False


def test_saturation_veto_clean_short_duration():
    """Short run duration (< 60 days) → veto NOT triggered."""
    outputs = [
        _make_agent("market_saturation_agent", "competitive_saturation", 70.0, {
            "active_advertiser_count": 10,
            "avg_ad_run_duration_days": 30,
            "market_stage": "Growing",
        }),
    ]
    result = check_hard_vetoes(outputs)
    assert result["vetoed"] is False


def test_saturation_veto_clean_gaps_exist():
    """>5 advertisers, 60+ days, but gaps exist → differentiation available → NOT vetoed."""
    outputs = [
        _make_agent("market_saturation_agent", "competitive_saturation", 30.0, {
            "active_advertiser_count": 12,
            "avg_ad_run_duration_days": 90,
            "market_stage": "Peak",
        }),
        _make_agent("competitor_analysis_agent", "competitive_saturation", 65.0, {
            "gaps_identified": ["no bundle options", "no extended warranty"],
            "competitive_barrier": "Medium",
        }),
    ]
    result = check_hard_vetoes(outputs)
    assert result["vetoed"] is False


def test_saturation_veto_clean_underused_angles():
    """>5 advertisers, 60+ days, but underused angles exist → NOT vetoed."""
    outputs = [
        _make_agent("market_saturation_agent", "competitive_saturation", 30.0, {
            "active_advertiser_count": 12,
            "avg_ad_run_duration_days": 90,
            "market_stage": "Peak",
        }),
        _make_agent("creative_opportunity_agent", "creative_runway", 70.0, {
            "viable_angles": ["angle A", "angle B"],
            "angle_saturation_map": {
                "angle A": "crowded",
                "angle B": "underused",
            },
        }),
    ]
    result = check_hard_vetoes(outputs)
    assert result["vetoed"] is False


def test_saturation_veto_absent_market_sat():
    """market_saturation_agent not present → unverifiable."""
    outputs = [
        _make_agent("competitor_analysis_agent", "competitive_saturation", 50.0, {
            "gaps_identified": [],
            "competitive_barrier": "High",
        }),
    ]
    result = check_hard_vetoes(outputs)
    assert result["vetoed"] is False
    # Should appear in unverifiable — needs at minimum market_saturation_agent
    assert any("saturat" in r.lower() for r in result["unverifiable_rules"]), (
        f"Expected saturation in unverifiable_rules, got: {result['unverifiable_rules']}"
    )


# ── The critical test: "high score but vetoed" ──────────────────────────────

def test_high_score_vetoed_by_compliance():
    """
    All agents return sub_score = 95 → composite_score = 95.0 (strong GO).
    But risk_analysis_agent has legal_risk = "Severe" → compliance veto triggered.

    This proves veto override behavior: even with a near-perfect composite score,
    the veto forces NO-GO. A caller who only calls calculate_composite_score()
    would see 95.0 (GO) and be dangerously misled.

    Hand calculation of composite score:
      demand_strength:           avg(95, 95) = 95 × 0.20 = 19.0
      unit_economics:            avg(95, 95) = 95 × 0.20 = 19.0
      competitive_saturation:    avg(95, 95) = 95 × 0.15 = 14.25
      creative_runway:           95 × 0.15 = 14.25
      customer_psychology_fit:   95 × 0.10 = 9.5
      risk_profile:              95 × 0.10 = 9.5
      reviews_sentiment_quality: 95 × 0.10 = 9.5
      Total: 95.0
    """
    outputs = [
        _make_agent("fb_ads_analysis_agent", "demand_strength", 95,
                    {"active_ad_count": 34}),
        _make_agent("tiktok_trend_agent", "demand_strength", 95,
                    {"hashtag_views": 5000000}),
        _make_agent("pricing_analysis_agent", "unit_economics", 95,
                    {"recommended_price_range": {"min": 29.99, "max": 39.99}}),
        _make_agent("margin_analysis_agent", "unit_economics", 95,
                    {"net_margin_pct_after_ads": 35.0}),
        _make_agent("market_saturation_agent", "competitive_saturation", 95,
                    {"active_advertiser_count": 3, "market_stage": "Emerging"}),
        _make_agent("competitor_analysis_agent", "competitive_saturation", 95,
                    {"gaps_identified": ["no bundle"], "competitive_barrier": "Low"}),
        _make_agent("creative_opportunity_agent", "creative_runway", 95,
                    {"viable_angles": ["angle A", "angle B", "angle C"]}),
        _make_agent("customer_psychology_agent", "customer_psychology_fit", 95,
                    {"core_pain_point": "test"}),
        _make_agent("risk_analysis_agent", "risk_profile", 95,
                    {"legal_risk": "Severe", "platform_policy_risk": "Low",
                     "supplier_risk": "Low", "seasonality_risk": "Low",
                     "reputational_risk": "Low", "overall_risk_level": "Severe"}),
        _make_agent("amazon_review_agent", "reviews_sentiment_quality", 95,
                    {"avg_rating": 4.5}),
    ]

    # First: confirm composite score via Sprint 2.1.2 calculator
    from scoring.pillar_calculators.composite_score import calculate_composite_score
    scorecard = calculate_composite_score(outputs)
    assert scorecard["composite_score"] == 95.0, (
        f"Expected composite 95.0, got {scorecard['composite_score']}"
    )

    # Second: veto check MUST flag this despite the high score
    veto_result = check_hard_vetoes(outputs)
    assert veto_result["vetoed"] is True, (
        "High composite score must NOT bypass veto check"
    )
    assert any("compliance" in r.lower() or "legal" in r.lower()
               for r in veto_result["triggered_rules"]), (
        f"Expected compliance veto, got: {veto_result['triggered_rules']}"
    )

    # Third: confirm the danger — ignoring the veto gives a misleading GO verdict
    cs = scorecard["composite_score"]
    misleading_verdict = "GO" if cs >= 75 else ("CONDITIONAL" if cs >= 55 else "NO-GO")
    assert misleading_verdict == "GO", "Composite alone suggests GO (misleading)"
    # The veto correctly overrides this
    assert veto_result["vetoed"] is True, "Veto correctly overrides"


def test_high_score_vetoed_by_creative_angles():
    """
    All agents except creative_opportunity_agent score 100.
    creative_opportunity_agent has sub_score = 0 (due to only 1 viable angle)
    AND raw_findings has viable_angles = ["only one"] → creative angles veto.

    Hand calculation:
      demand_strength:           avg(100, 100) = 100 × 0.20 = 20.0
      unit_economics:            avg(100, 100) = 100 × 0.20 = 20.0
      competitive_saturation:    avg(100, 100) = 100 × 0.15 = 15.0
      creative_runway:           0 × 0.15 = 0.0
      customer_psychology_fit:   100 × 0.10 = 10.0
      risk_profile:              100 × 0.10 = 10.0
      reviews_sentiment_quality: 100 × 0.10 = 10.0
      Total: 85.0

    Even with creative_runway at 0, the composite is 85 — strong GO via
    score thresholds. But the creative angles veto overrides it.
    """
    outputs = [
        _make_agent("fb_ads_analysis_agent", "demand_strength", 100, {}),
        _make_agent("tiktok_trend_agent", "demand_strength", 100, {}),
        _make_agent("pricing_analysis_agent", "unit_economics", 100, {}),
        _make_agent("margin_analysis_agent", "unit_economics", 100, {}),
        _make_agent("market_saturation_agent", "competitive_saturation", 100, {}),
        _make_agent("competitor_analysis_agent", "competitive_saturation", 100, {}),
        _make_agent("creative_opportunity_agent", "creative_runway", 0,
                    {"viable_angles": ["only one angle"],
                     "fatigue_risk_level": "Critical"}),
        _make_agent("customer_psychology_agent", "customer_psychology_fit", 100, {}),
        _make_agent("risk_analysis_agent", "risk_profile", 100, {}),
        _make_agent("amazon_review_agent", "reviews_sentiment_quality", 100, {}),
    ]

    from scoring.pillar_calculators.composite_score import calculate_composite_score
    scorecard = calculate_composite_score(outputs)
    assert scorecard["composite_score"] == 85.0, (
        f"Expected composite 85.0, got {scorecard['composite_score']}"
    )

    veto_result = check_hard_vetoes(outputs)
    assert veto_result["vetoed"] is True
    assert any("creative" in r.lower() for r in veto_result["triggered_rules"])

    # Confirm the danger: composite alone suggests GO
    cs = scorecard["composite_score"]
    misleading = "GO" if cs >= 75 else ("CONDITIONAL" if cs >= 55 else "NO-GO")
    assert misleading == "GO", f"Composite {cs} alone misleadingly suggests {misleading}"
