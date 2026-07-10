"""Hard veto override rules (Architecture Section 2.3).

Each rule is an independently-testable private function that reads from
specific AgentOutput.raw_findings fields. Vetoes are checked AFTER the
composite score is calculated and OVERRIDE it — a triggered veto produces
NO-GO regardless of the composite score's value.

Exposed function:
    check_hard_vetoes(agent_outputs) -> dict

Intended calling pattern (for future orchestrator / Chief Analyst):
    scorecard = calculate_composite_score(agent_outputs)
    veto_result = check_hard_vetoes(agent_outputs)
    if veto_result["vetoed"]:
        verdict = "NO-GO"  # veto overrides composite score
    else:
        # apply score thresholds from Section 2.2
        ...

IMPORTANT: There is NO runtime enforcement of this calling order at this layer.
A lazy caller could call calculate_composite_score() alone and ignore
check_hard_vetoes() — getting a favorable verdict despite a triggered veto.
This risk is documented here; runtime enforcement belongs in the orchestrator
(Phase 6), not in individual function signatures.

Missing-agent edge case
-----------------------
If a veto rule's required agent output is not present in the list, the rule
is added to the `unverifiable_rules` list and does NOT trigger a veto.
This is conservative: "no data" is not treated as "no problem." The caller
(Chief Analyst / orchestrator) can decide how to surface unverifiable rules
in the final memo.
"""

from __future__ import annotations

from typing import Any


# ── Rule 1: Margin veto ──────────────────────────────────────────────────────

def _check_margin_veto(
    agent_outputs: list[Any],
) -> tuple[bool, str | None, bool]:
    """Veto if net margin after realistic CPA < 15% — economics can't support paid acquisition.

    Reads from: margin_analysis_agent.raw_findings["net_margin_pct_after_ads"]
    Trigger: value is numeric and < 15.0
    If margin_analysis_agent absent from agent_outputs → unverifiable (not triggered).

    Returns: (triggered, reason, verifiable)
    """
    for output in agent_outputs:
        if output.agent_name == "margin_analysis_agent":
            margin = output.raw_findings.get("net_margin_pct_after_ads")
            if margin is not None and margin < 15.0:
                return True, "Net margin after realistic CPA < 15%", True
            return False, None, True
    return False, None, False


# ── Rule 2: Compliance blocklist veto ────────────────────────────────────────

def _check_compliance_veto(
    agent_outputs: list[Any],
) -> tuple[bool, str | None, bool]:
    """Veto if product appears on legal/compliance blocklist.

    Reads from: risk_analysis_agent.raw_findings fields:
      - legal_risk == "Severe"
      - platform_policy_risk == "Severe"

    These fields proxy the compliance blocklist check. The full deterministic
    check (category + keyword matching against compliance_blocklist.md) is the
    Validation Gate's responsibility in stage 1.5 — by the time the Scoring
    Engine runs, the product has already passed that gate. This veto serves as
    a second-line safety net: the Risk Analysis Agent may surface additional
    compliance issues (e.g., newly identified legal risks) that the gate missed.

    If risk_analysis_agent is absent → unverifiable (not triggered).

    Returns: (triggered, reason, verifiable)
    """
    for output in agent_outputs:
        if output.agent_name == "risk_analysis_agent":
            rf = output.raw_findings
            legal = rf.get("legal_risk", "")
            platform = rf.get("platform_policy_risk", "")
            if legal == "Severe" or platform == "Severe":
                return True, "Product flagged on legal/compliance blocklist", True
            return False, None, True
    return False, None, False


# ── Rule 3: Creative angles veto ─────────────────────────────────────────────

def _check_creative_angles_veto(
    agent_outputs: list[Any],
) -> tuple[bool, str | None, bool]:
    """Veto if fewer than 2 viable creative angles exist — fatigue risk too high.

    Reads from: creative_opportunity_agent.raw_findings["viable_angles"]
    Trigger: len(viable_angles) < 2
    If creative_opportunity_agent absent → unverifiable (not triggered).

    Returns: (triggered, reason, verifiable)
    """
    for output in agent_outputs:
        if output.agent_name == "creative_opportunity_agent":
            angles = output.raw_findings.get("viable_angles", [])
            if len(angles) < 2:
                return True, "Fewer than 2 viable creative angles", True
            return False, None, True
    return False, None, False


# ── Rule 4: Saturation veto ──────────────────────────────────────────────────

def _check_saturation_veto(
    agent_outputs: list[Any],
) -> tuple[bool, str | None, bool]:
    """Veto if >5 large-scale advertisers run identical offer 60+ days with no differentiation angle.

    Reads from multiple agents:
      market_saturation_agent.raw_findings:
        - active_advertiser_count > 5
        - avg_ad_run_duration_days >= 60
      competitor_analysis_agent.raw_findings:
        - gaps_identified (non-empty means differentiation angle exists)
      creative_opportunity_agent.raw_findings:
        - angle_saturation_map (any "underused"/"open" means differentiation exists)

    All sub-conditions must be met:
      1. active_advertiser_count > 5
      2. avg_ad_run_duration_days >= 60
      3. No differentiation angle available (checked via competitor gaps OR creative saturation)

    If market_saturation_agent is absent → unverifiable (not triggered).
    If conditions 1+2 are met but neither competitor_analysis_agent nor
    creative_opportunity_agent is present → unverifiable (cannot verify condition 3).

    Returns: (triggered, reason, verifiable)
    """
    market_sat = None
    competitor = None
    creative_opp = None

    for output in agent_outputs:
        name = output.agent_name
        if name == "market_saturation_agent":
            market_sat = output
        elif name == "competitor_analysis_agent":
            competitor = output
        elif name == "creative_opportunity_agent":
            creative_opp = output

    # Must have market saturation data at minimum
    if market_sat is None:
        return False, None, False

    rf = market_sat.raw_findings
    if rf.get("active_advertiser_count", 0) <= 5:
        return False, None, True
    if rf.get("avg_ad_run_duration_days", 0) < 60:
        return False, None, True

    # Conditions 1+2 met. Check condition 3: is there any differentiation angle?
    has_diff = False
    diff_source_found = False

    if competitor is not None:
        diff_source_found = True
        gaps = competitor.raw_findings.get("gaps_identified", [])
        if gaps:  # non-empty = differentiation angle exists
            has_diff = True

    if creative_opp is not None:
        diff_source_found = True
        angle_map = creative_opp.raw_findings.get("angle_saturation_map", {})
        if any(
            v.lower() in ("underused", "open") for v in angle_map.values()
        ):
            has_diff = True

    # If no source could check differentiation → unverifiable
    if not diff_source_found:
        return False, None, False

    # Conditions 1+2 met AND no differentiation available → VETO
    if not has_diff:
        return True, (
            "Market saturated: >5 advertisers, 60+ days, "
            "no differentiation angle available"
        ), True

    return False, None, True


# ── Public API ───────────────────────────────────────────────────────────────

def check_hard_vetoes(agent_outputs: list[Any]) -> dict:
    """Check all 4 hard veto rules against the provided agent outputs.

    Args:
        agent_outputs: List of AgentOutput objects from the 10 domain agents.

    Returns:
        dict with keys:
            vetoed (bool): Whether any veto rule triggered.
            triggered_rules (list[str]): Names/descriptions of triggered rules.
            unverifiable_rules (list[str]): Rules that could not be evaluated
                because their required agent output was missing.
    """
    triggered_rules: list[str] = []
    unverifiable_rules: list[str] = []

    # Each rule function returns (triggered, reason, verifiable).
    # If verifiable is False, the required agent data was missing.

    rules = [
        ("Net margin after realistic CPA < 15%", _check_margin_veto),
        ("Product flagged on legal/compliance blocklist", _check_compliance_veto),
        ("Fewer than 2 viable creative angles", _check_creative_angles_veto),
        ("Market saturation with no differentiation angle", _check_saturation_veto),
    ]

    for rule_name, check_fn in rules:
        triggered, reason, verifiable = check_fn(agent_outputs)
        if triggered:
            triggered_rules.append(reason or rule_name)
        elif not verifiable:
            unverifiable_rules.append(rule_name)

    return {
        "vetoed": len(triggered_rules) > 0,
        "triggered_rules": triggered_rules,
        "unverifiable_rules": unverifiable_rules,
    }
