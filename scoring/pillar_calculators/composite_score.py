"""Deterministic composite score calculator for the 7-pillar Investment Scorecard.

This module implements the weighted-sum math from Architecture Section 2.1.
It is pure deterministic code — no LLM calls, no business logic beyond the
formula. It consumes AgentOutput objects (Sprint 2.1.1 contract) and produces
a composite score with a per-pillar breakdown.

Two key design decisions are documented here because they are not fully
specified in the architecture prose and require an explicit, reviewable decision:

Decision 1 — Multi-agent-per-pillar aggregation
-------------------------------------------------
Some pillars are fed by multiple agents (e.g., demand_strength ←
fb_ads_analysis_agent + tiktok_trend_agent). This module uses a SIMPLE AVERAGE
of the sub_score values from all agents feeding that pillar. This is the most
transparent approach — no hidden weighting by confidence, data_completeness,
or other factors. Those are separate concerns handled in Sprint 2.1.3
(confidence calculator) and the Chief Analyst/Synthesizer (narrative
interpretation).

  pillar_score = avg(sub_score for each agent mapped to this pillar)

If a pillar has exactly one contributing agent, pillar_score = that agent's
sub_score (single-element average).

Decision 2 — Proportional weight redistribution for missing pillars
-------------------------------------------------------------------
When one or more pillars have NO contributing AgentOutputs (the agents either
didn't run or returned no data), their weight must be redistributed
proportionally across the remaining pillars that DO have data. The formula:

  Let W = {w_1, w_2, ..., w_7} be the original weights (ΣW = 1.0).
  Let P_missing be the set of pillars with no AgentOutputs.
  Let P_present be the remaining pillars.

  For each pillar i in P_present:
    adjusted_weight_i = w_i / (Σ w_j for all j in P_present)

  This ensures Σ(adjusted_weights over P_present) = 1.0 while preserving the
  original proportional relationships between the remaining pillars.

  Example: If demand_strength (0.20) and competitive_saturation (0.15) are
  missing, the remaining weights are {unit_economics: 0.20, creative_runway: 0.15,
  customer_psychology_fit: 0.10, risk_profile: 0.10, reviews_sentiment_quality: 0.10}
  with sum = 0.65. Each is divided by 0.65:
    unit_economics → 0.20/0.65 ≈ 0.3077
    creative_runway → 0.15/0.65 ≈ 0.2308
    etc.

Edge case: If ALL pillars are missing (empty input list), the function raises
ValueError — no score can be calculated from zero data.
"""

import yaml
from pathlib import Path


# ── Pillar-to-agent mapping (from agent_output_contract.md Section 2) ───────
# This maps each pillar value to the set of agent_name values that feed it.
# The Scoring Engine uses this to group AgentOutput.sub_score values by pillar.

PILLAR_AGENTS: dict[str, set[str]] = {
    "demand_strength":           {"fb_ads_analysis_agent", "tiktok_trend_agent"},
    "unit_economics":            {"pricing_analysis_agent", "margin_analysis_agent"},
    "competitive_saturation":    {"market_saturation_agent", "competitor_analysis_agent"},
    "creative_runway":           {"creative_opportunity_agent"},
    "customer_psychology_fit":   {"customer_psychology_agent"},
    "risk_profile":              {"risk_analysis_agent"},
    "reviews_sentiment_quality": {"amazon_review_agent"},
}


def _load_weights(path: Path | None = None) -> dict[str, float]:
    """Load pillar weights from a YAML config file.

    Args:
        path: Path to the YAML weights file. Defaults to the project's
              default_weights.yaml relative to this file's location.

    Returns:
        dict mapping pillar name (str) to weight (float, 0.0–1.0).
    """
    if path is None:
        path = Path(__file__).resolve().parents[1] / "weights_config" / "default_weights.yaml"
    with open(path, encoding="utf-8") as f:
        weights: dict[str, float] = yaml.safe_load(f)
    return weights


def _pillar_score(agent_outputs: list) -> float:
    """Aggregate multiple AgentOutput sub_scores for one pillar into a single score.

    Uses simple average of all sub_score values. This is the multi-agent-per-pillar
    aggregation rule documented in this module's docstring (Decision 1).

    Args:
        agent_outputs: All AgentOutput objects for a single pillar.

    Returns:
        Average sub_score (float, 0.0–100.0).
    """
    if not agent_outputs:
        return 0.0
    return sum(o.sub_score for o in agent_outputs) / len(agent_outputs)


def calculate_composite_score(
    agent_outputs: list,
    weights_path: Path | None = None,
) -> dict:
    """Calculate the weighted composite Investment Scorecard score.

    Args:
        agent_outputs: List of AgentOutput objects (outputs from the 10 domain
                       agents). Must conform to the Sprint 2.1.1 contract shape
                       with at least agent_name, pillar, and sub_score fields.
        weights_path: Optional override path to a YAML weights file. If None,
                      the default weights from default_weights.yaml are used.

    Returns:
        dict with keys:
            composite_score (float): 0.0–100.0, the weighted sum.
            pillar_breakdown (dict): Per-pillar detail keyed by pillar name,
                each value is a dict with:
                    score (float): the pillar's aggregated sub_score.
                    weight (float): the pillar's original weight.
                    adjusted_weight (float): weight used in this calculation
                        (may differ from original if redistribution occurred).
                    agents (list[str]): agent_name values that contributed.
            missing_pillars (list[str]): pillars with no data.
            weight_redistribution_applied (bool): whether redistribution occurred.

    Raises:
        ValueError: If agent_outputs is empty (no data to score).
    """
    if not agent_outputs:
        raise ValueError("Cannot calculate composite score: agent_outputs list is empty")

    weights = _load_weights(weights_path)

    # Group AgentOutputs by pillar
    by_pillar: dict[str, list] = {p: [] for p in weights}
    for output in agent_outputs:
        pillar = output.pillar
        if pillar in by_pillar:
            by_pillar[pillar].append(output)

    # Separate present and missing pillars
    present_pillars = {p: outputs for p, outputs in by_pillar.items() if outputs}
    missing_pillars = [p for p, outputs in by_pillar.items() if not outputs]

    # Calculate pillar scores
    pillar_scores: dict[str, float] = {}
    pillar_agents: dict[str, list[str]] = {}
    for pillar, outputs in present_pillars.items():
        pillar_scores[pillar] = _pillar_score(outputs)
        pillar_agents[pillar] = [o.agent_name for o in outputs]

    # Calculate adjusted weights (redistribution if pillars are missing)
    weight_redistribution_applied = bool(missing_pillars)

    if weight_redistribution_applied:
        # Sum remaining weights, redistribute proportionally
        total_present_weight = sum(weights[p] for p in present_pillars)
        adjusted_weights: dict[str, float] = {
            p: weights[p] / total_present_weight for p in present_pillars
        }
    else:
        adjusted_weights = {p: weights[p] for p in present_pillars}

    # Composite score
    composite = sum(
        pillar_scores[p] * adjusted_weights[p] for p in present_pillars
    )

    # Build pillar_breakdown
    pillar_breakdown = {}
    for p in present_pillars:
        pillar_breakdown[p] = {
            "score": pillar_scores[p],
            "weight": weights[p],
            "adjusted_weight": adjusted_weights[p],
            "agents": pillar_agents[p],
        }

    return {
        "composite_score": round(composite, 6),
        "pillar_breakdown": pillar_breakdown,
        "missing_pillars": missing_pillars,
        "weight_redistribution_applied": weight_redistribution_applied,
    }
