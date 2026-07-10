"""Unit tests for confidence level calculator (Sprint 2.1.3).

Thresholds under test:
  avg_data_completeness_pct  |  Confidence
  --------------------------+-------------
  < 50.0                    |  "Low"
  50.0 – 79.9               |  "Medium"
  >= 80.0                   |  "High"

See confidence_calculator.py for threshold reasoning.
"""

import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parents[1]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import pytest
from app.schemas.agent_output import AgentOutput
from scoring.pillar_calculators.confidence_calculator import calculate_confidence


# ── Helper ──────────────────────────────────────────────────────────────────

def _make_agent(name: str, pillar: str, completeness: float) -> AgentOutput:
    return AgentOutput(
        agent_name=name,
        pillar=pillar,
        sub_score=50.0,
        confidence="Medium",
        evidence=[{"claim": "Test", "citation": "Source"}],
        data_completeness_pct=completeness,
    )


# ── Low confidence scenarios ────────────────────────────────────────────────

def test_low_confidence_single_agent():
    """Single agent at 30% completeness → avg=30.0 → Low."""
    outputs = [
        _make_agent("margin_analysis_agent", "unit_economics", 30.0),
    ]
    assert calculate_confidence(outputs) == "Low"


def test_low_confidence_multi_agent():
    """Multiple agents all below 50% → avg < 50 → Low."""
    outputs = [
        _make_agent("fb_ads_analysis_agent", "demand_strength", 20.0),
        _make_agent("tiktok_trend_agent", "demand_strength", 40.0),
        _make_agent("margin_analysis_agent", "unit_economics", 35.0),
    ]
    # avg = (20 + 40 + 35) / 3 = 31.67
    assert calculate_confidence(outputs) == "Low"


def test_low_confidence_boundary():
    """avg = 49.9 → should still be Low (below 50 threshold)."""
    outputs = [
        _make_agent("agent_1", "demand_strength", 49.9),
        _make_agent("agent_2", "unit_economics", 49.9),
    ]
    assert calculate_confidence(outputs) == "Low"


# ── Medium confidence scenarios ─────────────────────────────────────────────

def test_medium_confidence_low_end():
    """avg = 50.0 → just at the Medium threshold."""
    outputs = [
        _make_agent("margin_analysis_agent", "unit_economics", 50.0),
    ]
    assert calculate_confidence(outputs) == "Medium"


def test_medium_confidence_mid_range():
    """avg = 65.0 → solid Medium."""
    outputs = [
        _make_agent("fb_ads_analysis_agent", "demand_strength", 70.0),
        _make_agent("tiktok_trend_agent", "demand_strength", 60.0),
    ]
    # avg = 65.0
    assert calculate_confidence(outputs) == "Medium"


def test_medium_confidence_high_end():
    """avg = 79.9 → still Medium (below 80 threshold)."""
    outputs = [
        _make_agent("agent_1", "demand_strength", 79.9),
    ]
    assert calculate_confidence(outputs) == "Medium"


# ── High confidence scenarios ───────────────────────────────────────────────

def test_high_confidence_single_agent():
    """Single agent at 80% → avg=80.0 → High."""
    outputs = [
        _make_agent("margin_analysis_agent", "unit_economics", 80.0),
    ]
    assert calculate_confidence(outputs) == "High"


def test_high_confidence_all_100():
    """All agents at 100% completeness → avg=100 → High."""
    outputs = [
        _make_agent("margin_analysis_agent", "unit_economics", 100.0),
        _make_agent("fb_ads_analysis_agent", "demand_strength", 100.0),
        _make_agent("creative_opportunity_agent", "creative_runway", 100.0),
    ]
    assert calculate_confidence(outputs) == "High"


def test_high_confidence_mixed():
    """Some below 100 but avg still >= 80 → High."""
    outputs = [
        _make_agent("agent_1", "demand_strength", 90.0),
        _make_agent("agent_2", "unit_economics", 85.0),
        _make_agent("agent_3", "creative_runway", 75.0),
        _make_agent("agent_4", "risk_profile", 95.0),
    ]
    # avg = (90 + 85 + 75 + 95) / 4 = 86.25
    assert calculate_confidence(outputs) == "High"


# ── Edge cases ──────────────────────────────────────────────────────────────

def test_confidence_empty_input_raises_error():
    """Empty list should raise ValueError."""
    with pytest.raises(ValueError, match="agent_outputs list is empty"):
        calculate_confidence([])


def test_confidence_all_zeros():
    """All agents at 0% completeness → avg=0 → Low."""
    outputs = [
        _make_agent("agent_1", "demand_strength", 0.0),
        _make_agent("agent_2", "unit_economics", 0.0),
    ]
    assert calculate_confidence(outputs) == "Low"
