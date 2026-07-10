"""Confidence level calculator (Architecture Section 2.4).

Confidence is based on data completeness, not the composite score itself.
A verdict built on sparse data must be flagged Low confidence even if the
composite score looks decisive — and this must be surfaced to the reader.

Data source
-----------
Each AgentOutput object carries a `data_completeness_pct` field (0.0–100.0)
indicating what fraction of expected data points the agent actually retrieved.
Confidence is calculated as the simple average of these values across all
provided AgentOutput objects.

If an agent did not run at all, it does not contribute an AgentOutput object
and therefore does not affect the average. Missing pillars are tracked
separately by the composite score calculator's weight redistribution logic
and should be surfaced alongside the confidence level.

Thresholds (chosen with deliberate conservatism)
----------
  avg_data_completeness_pct  |  Confidence
  --------------------------+-------------
  < 50.0                    |  "Low"
  50.0 – 79.9               |  "Medium"
  >= 80.0                   |  "High"

Reasoning
---------
- < 50% (Low): More than half of expected data points are missing. The output
  is speculative — directional at best but not reliable for confident decisions.
  This aligns with standard scoring conventions where < 50% = insufficient data.

- 50–79.9% (Medium): Meaningful data exists but notable gaps remain. Suitable
  for directional signals and "go with conditions" verdicts, but the reader
  must be aware that significant data points are missing.

- ≥ 80% (High): Most expected data was retrieved. The verdict can be presented
  with confidence. This is a deliberately high bar — 80%+ means the analysis
  is substantially complete. A GO based on 40 ad results and 200 reviews would
  reach this level; a GO based on 3 ad results and no review data would not.

These thresholds are intentionally symmetric and linear. They can be
recalibrated during Phase 8 backtesting if historical analysis shows they
are too conservative or too permissive.
"""

from __future__ import annotations

from typing import Any


def calculate_confidence(agent_outputs: list[Any]) -> str:
    """Calculate confidence level from aggregate data completeness.

    Args:
        agent_outputs: List of AgentOutput objects. Each object must have a
            `data_completeness_pct` field (float, 0.0–100.0).

    Returns:
        "Low", "Medium", or "High" based on the average completeness.

    Raises:
        ValueError: If agent_outputs is empty (no data to judge).
    """
    if not agent_outputs:
        raise ValueError(
            "Cannot calculate confidence: agent_outputs list is empty"
        )

    avg = sum(o.data_completeness_pct for o in agent_outputs) / len(agent_outputs)

    if avg < 50.0:
        return "Low"
    if avg < 80.0:
        return "Medium"
    return "High"
