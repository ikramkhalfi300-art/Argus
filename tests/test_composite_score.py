"""Unit tests for the deterministic composite score calculator (Sprint 2.1.2).

Each test has a hand-calculated expected value shown in the docstring so the
reviewer can independently re-derive the math without reading the implementation.

All five scenarios use mock AgentOutput objects with sub_score values only —
no evidence, confidence, or raw_findings needed since the Scoring Engine reads
only sub_score and pillar/agent_name.

Hand-calculations were done BEFORE running the code — expected values were
computed by hand on paper / calculator, then written into these test assertions
as the ground truth. The code was then run against them.
"""

import sys
from pathlib import Path

# Ensure the project root is on sys.path so `scoring` is importable
_project_root = Path(__file__).resolve().parents[1]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import pytest
from app.schemas.agent_output import AgentOutput
from scoring.pillar_calculators.composite_score import calculate_composite_score


# ── Helper ──────────────────────────────────────────────────────────────────

def _make_agent(name: str, pillar: str, score: float) -> AgentOutput:
    return AgentOutput(
        agent_name=name,
        pillar=pillar,
        sub_score=score,
        confidence="Medium",
        evidence=[{"claim": "Test", "citation": "Source"}],
        data_completeness_pct=100.0,
    )


# ── Scenario 1: Full data, all 7 pillars, multi-agent pillars present ───────

def test_full_data_all_pillars():
    """
    All 7 pillars present. Multi-agent pillars have 2 agents each.
    Pillar scores (averaged):
      demand_strength:           avg(80, 70) = 75.00
      unit_economics:            avg(60, 75) = 67.50
      competitive_saturation:    avg(65, 45) = 55.00
      creative_runway:           80.00
      customer_psychology_fit:   70.00
      risk_profile:              55.00
      reviews_sentiment_quality: 85.00

    Composite = Σ(pillar_score × weight)
    = 75.00×0.20 + 67.50×0.20 + 55.00×0.15 + 80.00×0.15
      + 70.00×0.10 + 55.00×0.10 + 85.00×0.10
    = 15.00 + 13.50 + 8.25 + 12.00 + 7.00 + 5.50 + 8.50
    = 69.75
    """
    outputs = [
        _make_agent("fb_ads_analysis_agent", "demand_strength", 80),
        _make_agent("tiktok_trend_agent", "demand_strength", 70),
        _make_agent("pricing_analysis_agent", "unit_economics", 60),
        _make_agent("margin_analysis_agent", "unit_economics", 75),
        _make_agent("market_saturation_agent", "competitive_saturation", 65),
        _make_agent("competitor_analysis_agent", "competitive_saturation", 45),
        _make_agent("creative_opportunity_agent", "creative_runway", 80),
        _make_agent("customer_psychology_agent", "customer_psychology_fit", 70),
        _make_agent("risk_analysis_agent", "risk_profile", 55),
        _make_agent("amazon_review_agent", "reviews_sentiment_quality", 85),
    ]
    result = calculate_composite_score(outputs)

    assert result["composite_score"] == 69.75
    assert result["weight_redistribution_applied"] is False
    assert result["missing_pillars"] == []

    # Spot-check pillar breakdown
    bd = result["pillar_breakdown"]
    assert bd["demand_strength"]["score"] == 75.0
    assert bd["demand_strength"]["weight"] == 0.20
    assert bd["demand_strength"]["adjusted_weight"] == 0.20
    assert bd["unit_economics"]["score"] == 67.5
    assert bd["competitive_saturation"]["score"] == 55.0


# ── Scenario 2: One pillar missing (risk_profile) ───────────────────────────

def test_one_missing_pillar():
    """
    All 10 agents present EXCEPT risk_analysis_agent → risk_profile is missing.

    Present pillars and original weights:
      demand_strength:           0.20
      unit_economics:            0.20
      competitive_saturation:    0.15
      creative_runway:           0.15
      customer_psychology_fit:   0.10
      reviews_sentiment_quality: 0.10
    Sum of present = 0.90

    Adjusted weights:
      demand_strength:           0.20/0.90 = 2/9 ≈ 0.222222...
      unit_economics:            0.20/0.90 = 2/9 ≈ 0.222222...
      competitive_saturation:    0.15/0.90 = 1/6 ≈ 0.166667
      creative_runway:           0.15/0.90 = 1/6 ≈ 0.166667
      customer_psychology_fit:   0.10/0.90 = 1/9 ≈ 0.111111
      reviews_sentiment_quality: 0.10/0.90 = 1/9 ≈ 0.111111

    Using scores from Scenario 1:

    Composite = (75×20 + 67.5×20 + 55×15 + 80×15 + 70×10 + 85×10) / 90
    = (1500 + 1350 + 825 + 1200 + 700 + 850) / 90
    = 6425 / 90
    = 71.388889  (rounded to 6 decimal places)
    """
    outputs = [
        _make_agent("fb_ads_analysis_agent", "demand_strength", 80),
        _make_agent("tiktok_trend_agent", "demand_strength", 70),
        _make_agent("pricing_analysis_agent", "unit_economics", 60),
        _make_agent("margin_analysis_agent", "unit_economics", 75),
        _make_agent("market_saturation_agent", "competitive_saturation", 65),
        _make_agent("competitor_analysis_agent", "competitive_saturation", 45),
        _make_agent("creative_opportunity_agent", "creative_runway", 80),
        _make_agent("customer_psychology_agent", "customer_psychology_fit", 70),
        # risk_analysis_agent is absent
        _make_agent("amazon_review_agent", "reviews_sentiment_quality", 85),
    ]
    result = calculate_composite_score(outputs)

    assert result["composite_score"] == 71.388889
    assert result["weight_redistribution_applied"] is True
    assert result["missing_pillars"] == ["risk_profile"]

    # Check that adjusted weights sum to 1.0
    adj_sum = sum(p["adjusted_weight"] for p in result["pillar_breakdown"].values())
    assert adj_sum == pytest.approx(1.0, rel=1e-6)


# ── Scenario 3: Two pillars missing ─────────────────────────────────────────

def test_two_missing_pillars():
    """
    risk_profile AND customer_psychology_fit both missing.

    Present pillars and original weights:
      demand_strength:           0.20
      unit_economics:            0.20
      competitive_saturation:    0.15
      creative_runway:           0.15
      reviews_sentiment_quality: 0.10
    Sum of present = 0.80

    Adjusted weights:
      demand_strength:           0.20/0.80 = 0.25
      unit_economics:            0.20/0.80 = 0.25
      competitive_saturation:    0.15/0.80 = 0.1875
      creative_runway:           0.15/0.80 = 0.1875
      reviews_sentiment_quality: 0.10/0.80 = 0.125

    Using scores from Scenario 1:

    Composite = (75×20 + 67.5×20 + 55×15 + 80×15 + 85×10) / 80
    = (1500 + 1350 + 825 + 1200 + 850) / 80
    = 5725 / 80
    = 71.5625
    """
    outputs = [
        _make_agent("fb_ads_analysis_agent", "demand_strength", 80),
        _make_agent("tiktok_trend_agent", "demand_strength", 70),
        _make_agent("pricing_analysis_agent", "unit_economics", 60),
        _make_agent("margin_analysis_agent", "unit_economics", 75),
        _make_agent("market_saturation_agent", "competitive_saturation", 65),
        _make_agent("competitor_analysis_agent", "competitive_saturation", 45),
        _make_agent("creative_opportunity_agent", "creative_runway", 80),
        # customer_psychology_agent is absent
        # risk_analysis_agent is absent
        _make_agent("amazon_review_agent", "reviews_sentiment_quality", 85),
    ]
    result = calculate_composite_score(outputs)

    assert result["composite_score"] == 71.5625
    assert result["weight_redistribution_applied"] is True
    assert set(result["missing_pillars"]) == {"risk_profile", "customer_psychology_fit"}

    adj_sum = sum(p["adjusted_weight"] for p in result["pillar_breakdown"].values())
    assert adj_sum == pytest.approx(1.0, rel=1e-9)


# ── Scenario 4: All pillars, single-agent only (no multi-agent averages) ────

def test_all_single_agent_per_pillar():
    """
    All 7 pillars present but each has exactly ONE contributing agent
    (no multi-agent averages needed).

    Pillar scores (same as the single-agent sub_score):
      demand_strength:           80
      unit_economics:            60
      competitive_saturation:    65
      creative_runway:           80
      customer_psychology_fit:   70
      risk_profile:              55
      reviews_sentiment_quality: 85

    Composite = 80×0.20 + 60×0.20 + 65×0.15 + 80×0.15
                + 70×0.10 + 55×0.10 + 85×0.10
    = 16 + 12 + 9.75 + 12 + 7 + 5.5 + 8.5
    = 70.75
    """
    outputs = [
        _make_agent("fb_ads_analysis_agent", "demand_strength", 80),
        # No tiktok_trend_agent
        _make_agent("pricing_analysis_agent", "unit_economics", 60),
        # No margin_analysis_agent
        _make_agent("market_saturation_agent", "competitive_saturation", 65),
        # No competitor_analysis_agent
        _make_agent("creative_opportunity_agent", "creative_runway", 80),
        _make_agent("customer_psychology_agent", "customer_psychology_fit", 70),
        _make_agent("risk_analysis_agent", "risk_profile", 55),
        _make_agent("amazon_review_agent", "reviews_sentiment_quality", 85),
    ]
    result = calculate_composite_score(outputs)

    assert result["composite_score"] == 70.75
    assert result["weight_redistribution_applied"] is False
    assert result["missing_pillars"] == []

    # Check that single-agent pillars have only one agent in breakdown
    assert result["pillar_breakdown"]["demand_strength"]["agents"] == ["fb_ads_analysis_agent"]


# ── Scenario 5: Low scores, below NO-GO threshold ──────────────────────────

def test_low_scores_no_go_range():
    """
    All pillars present, multi-agent, but low scores.
    Designed to produce composite < 55 (NO-GO threshold).

    Pillar scores:
      demand_strength:           avg(40, 30) = 35
      unit_economics:            avg(35, 45) = 40
      competitive_saturation:    avg(50, 40) = 45
      creative_runway:           25
      customer_psychology_fit:   60
      risk_profile:              70
      reviews_sentiment_quality: 55

    Composite = 35×0.20 + 40×0.20 + 45×0.15 + 25×0.15
                + 60×0.10 + 70×0.10 + 55×0.10
    = 7 + 8 + 6.75 + 3.75 + 6 + 7 + 5.5
    = 44.0
    """
    outputs = [
        _make_agent("fb_ads_analysis_agent", "demand_strength", 40),
        _make_agent("tiktok_trend_agent", "demand_strength", 30),
        _make_agent("pricing_analysis_agent", "unit_economics", 35),
        _make_agent("margin_analysis_agent", "unit_economics", 45),
        _make_agent("market_saturation_agent", "competitive_saturation", 50),
        _make_agent("competitor_analysis_agent", "competitive_saturation", 40),
        _make_agent("creative_opportunity_agent", "creative_runway", 25),
        _make_agent("customer_psychology_agent", "customer_psychology_fit", 60),
        _make_agent("risk_analysis_agent", "risk_profile", 70),
        _make_agent("amazon_review_agent", "reviews_sentiment_quality", 55),
    ]
    result = calculate_composite_score(outputs)

    assert result["composite_score"] == 44.0
    # Verify it's below the NO-GO threshold
    assert result["composite_score"] < 55.0


# ── Scenario 6 (bonus): Empty list raises ValueError ────────────────────────

def test_empty_input_raises_error():
    with pytest.raises(ValueError, match="agent_outputs list is empty"):
        calculate_composite_score([])
