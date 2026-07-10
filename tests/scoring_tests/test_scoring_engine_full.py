"""Golden-dataset regression test suite for the complete Scoring Engine.

Reads ./golden_dataset.json and validates every scenario against the three
already-approved functions from Sprints 2.1.1-2.1.3:
  - calculate_composite_score()   (Sprint 2.1.2)
  - check_hard_vetoes()           (Sprint 2.1.3)
  - calculate_confidence()        (Sprint 2.1.3)

This is the permanent regression tripwire for all future /scoring changes.
"""

import json
from pathlib import Path

import pytest
from app.schemas.agent_output import AgentOutput
from scoring.pillar_calculators.composite_score import calculate_composite_score
from scoring.veto_rules.hard_vetoes import check_hard_vetoes
from scoring.pillar_calculators.confidence_calculator import calculate_confidence


_DATASET_PATH = Path(__file__).resolve().parent / "golden_dataset.json"


def _load_dataset() -> list[dict]:
    with open(_DATASET_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return data["scenarios"]


def _to_agent_output(raw: dict) -> AgentOutput:
    """Convert a raw JSON agent-output dict to an AgentOutput instance."""
    return AgentOutput(
        agent_name=raw["agent_name"],
        pillar=raw["pillar"],
        sub_score=raw["sub_score"],
        confidence=raw["confidence"],
        evidence=[{"claim": "Dataset scenario", "citation": "Golden dataset"}],
        data_completeness_pct=raw["data_completeness_pct"],
        raw_findings=raw.get("raw_findings", {}),
    )


# ── Parametrized test: one per scenario ──────────────────────────────────────


@pytest.mark.parametrize(
    "scenario",
    _load_dataset(),
    ids=lambda s: f"scenario_{s['id']:02d}_{s['name'][:50]}",
)
def test_golden_dataset_scenario(scenario: dict):
    outputs = [_to_agent_output(o) for o in scenario["agent_outputs"]]

    # 1. Composite score
    scorecard = calculate_composite_score(outputs)
    assert scorecard["composite_score"] == pytest.approx(
        scenario["expected_composite"], rel=1e-6
    ), (
        f"Scenario {scenario['id']}: expected composite "
        f"{scenario['expected_composite']}, got {scorecard['composite_score']}"
    )

    # 2. Threshold-derived verdict (ignoring vetoes)
    cs = scorecard["composite_score"]
    threshold_verdict = "GO" if cs >= 75 else ("CONDITIONAL" if cs >= 55 else "NO-GO")
    assert threshold_verdict == scenario["expected_threshold_verdict"], (
        f"Scenario {scenario['id']}: expected threshold verdict "
        f"'{scenario['expected_threshold_verdict']}', got '{threshold_verdict}'"
    )

    # 3. Veto check
    veto_result = check_hard_vetoes(outputs)
    assert veto_result["vetoed"] == scenario["expected_vetoed"], (
        f"Scenario {scenario['id']}: expected vetoed={scenario['expected_vetoed']}, "
        f"got {veto_result['vetoed']}. Triggered: {veto_result['triggered_rules']}"
    )
    # Verify expected triggered rules match (order-independent)
    assert sorted(veto_result["triggered_rules"]) == sorted(
        scenario["expected_triggered_rules"]
    ), (
        f"Scenario {scenario['id']}: triggered rules mismatch.\n"
        f"  Expected: {sorted(scenario['expected_triggered_rules'])}\n"
        f"  Got:      {sorted(veto_result['triggered_rules'])}"
    )

    # 4. Confidence
    confidence = calculate_confidence(outputs)
    assert confidence == scenario["expected_confidence"], (
        f"Scenario {scenario['id']}: expected confidence "
        f"'{scenario['expected_confidence']}', got '{confidence}'"
    )
