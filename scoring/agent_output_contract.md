# Agent Output Contract

**Canonical reference for all 10 domain analysis agents (Phase 4/5).**
Every agent must return an object conforming to this shape. The Scoring Engine,
Contradiction Auditor, and Synthesizer all depend on this contract being stable
and enforced.

**Last updated**: 2026-07-09
**Sprint**: 2.1.1
**Status**: Approved — locked prior to any domain agent implementation.

---

## 1. Contract Shape

```
AgentOutput {
  agent_name: string                          // the emitting agent's identifier
  pillar: string                              // which of the 7 pillars, or "risk"/"gate"
  sub_score: number (0–100)                   // this agent's pillar contribution
  confidence: "Low" | "Medium" | "High"       // self-assessed evidence confidence
  evidence: [                                  // every claim must cite its source
    { claim: string, citation: string }
  ]
  data_completeness_pct: number (0–100)       // % of expected data points retrieved
  raw_findings: object                        // agent-specific structured data
}
```

### 1.1 Field Rules

| Field | Required | Constraints |
|---|---|---|
| `agent_name` | Yes | Non-empty string. Must match one of the agent identifiers in Section 3. |
| `pillar` | Yes | Non-empty string. Must match one of the 7 pillars or be `"risk"` or `"gate"`. |
| `sub_score` | Yes | Float, 0.0–100.0 inclusive. |
| `confidence` | Yes | One of `"Low"`, `"Medium"`, `"High"`. String, not numeric. |
| `evidence` | Yes | Array, min length 1. Each item must have a non-empty `claim` and non-empty `citation`. |
| `data_completeness_pct` | Yes | Float, 0.0–100.0 inclusive. |
| `raw_findings` | Yes | Object (may be empty `{}`). Agent-specific structured payload. |

### 1.2 Evidence Requirement

Every agent output **must** include at least one evidence entry with a citation.
An empty `evidence` array is invalid. This is the primary anti-hallucination
mechanism — the Contradiction Auditor (Phase 6) uses this field to verify
cross-agent consistency.

Citations should reference the specific data source (FB Ad Library URL, Amazon
ASIN, scraped storefront URL, supplier API record ID) so the citation is
independently verifiable.

---

## 2. Pillar Mapping

Each agent feeds into exactly one of the 7 pillars (Architecture Section 2.1)
or is tagged as a non-pillar agent. The `pillar` field value must match this
table:

| Pillar Value | Weight | Agents |
|---|---|---|
| `"demand_strength"` | 20% | Facebook Ads Analysis, TikTok Trend Analysis |
| `"unit_economics"` | 20% | Pricing Analysis, Margin Analysis |
| `"competitive_saturation"` | 15% | Market Saturation, Competitor Analysis |
| `"creative_runway"` | 15% | Creative Opportunity |
| `"customer_psychology_fit"` | 10% | Customer Psychology |
| `"risk_profile"` | 10% | Risk Analysis |
| `"reviews_sentiment_quality"` | 10% | Amazon Review Analysis |

Non-pillar agents (e.g. Discovery/Validation gate agents) use `"gate"` or
`"risk"` as applicable.

---

## 2.5 `sub_score` Derivation Rule

The architecture documents each agent's output in two separate locations:
- **Outputs** — the domain-specific data object the agent produces (e.g.
  `SaturationResult`, `CompetitorReport`, `MarginResult`).
- **Scoring** — a prose section describing how a 0–100 score is calculated from
  that agent's analysis.

`sub_score` is a **derived value** that each agent must independently compute
and emit as part of the `AgentOutput` contract wrapper. For all 10 agents, the
scoring logic is described in the "Scoring" subsection of their architecture
spec:

| Agent | `sub_score` derived from (Arch Source) |
|---|---|
| Market Saturation | Outputs field `saturation_score` — **named explicitly in the Outputs object** |
| Competitor Analysis | Scoring prose: inversely related to competitive barrier strength, with positive adjustment for exploitable gaps |
| Pricing Analysis | Scoring prose: gap between recommended price and viable-margin price |
| Margin Analysis | Scoring prose: directly proportional to net margin % |
| Facebook Ads Analysis | Scoring prose: evidence of sustained profitable ads + creative diversity |
| TikTok Trend Analysis | Scoring prose: weighted toward commerce-intent virality over raw view count |
| Amazon Review Analysis | Scoring prose: weighted toward absence of structural-defect complaints |
| Customer Psychology | Scoring prose: clarity/strength/consistency of core pain point |
| Creative Opportunity | Scoring prose: count of viable + underused angles |
| Risk Analysis | Scoring prose: inversely proportional to aggregated risk severity |

**Key rule**: `sub_score` is NOT simply copied out of `raw_findings` for most
agents. Only Market Saturation's `saturation_score` appears as a named output
field. For the other 9, the score is an independently computed value based on
the agent's own internal analysis — it must be calculated and placed into the
contract's `sub_score` field, separate from whatever goes into `raw_findings`.
The Scoring Engine reads `sub_score`, not `raw_findings`.

---

## 3. Ten Agent Identifier Values

| # | Agent | `agent_name` value | `pillar` |
|---|---|---|---|
| 1 | Market Saturation Analysis | `"market_saturation_agent"` | `"competitive_saturation"` |
| 2 | Competitor Analysis | `"competitor_analysis_agent"` | `"competitive_saturation"` |
| 3 | Pricing Analysis | `"pricing_analysis_agent"` | `"unit_economics"` |
| 4 | Margin Analysis | `"margin_analysis_agent"` | `"unit_economics"` |
| 5 | Facebook Ads Analysis | `"fb_ads_analysis_agent"` | `"demand_strength"` |
| 6 | TikTok Trend Analysis | `"tiktok_trend_agent"` | `"demand_strength"` |
| 7 | Amazon Review Analysis | `"amazon_review_agent"` | `"reviews_sentiment_quality"` |
| 8 | Customer Psychology Analysis | `"customer_psychology_agent"` | `"customer_psychology_fit"` |
| 9 | Creative Opportunity Analysis | `"creative_opportunity_agent"` | `"creative_runway"` |
| 10 | Risk Analysis | `"risk_analysis_agent"` | `"risk_profile"` |

---

## 4. `raw_findings` Per-Agent Specification

The `raw_findings` field holds agent-specific structured data from the agent's
architecture-documented **Outputs** section. It does **not** include `sub_score`
— that is a derived value placed in the contract's top-level `sub_score` field
per Section 2.5. The per-agent examples below show exactly which fields belong
in `raw_findings` vs. the contract's top-level fields.

The Scoring Engine and Contradiction Auditor treat `raw_findings` as opaque —
they operate on `sub_score`, `confidence`, `evidence`, and `pillar` only.
However, downstream human-facing memo generation (Chief Analyst / Synthesizer)
may read `raw_findings` to produce narrative content.

### 4.1 Market Saturation Agent

Note: `saturation_score` (from the architecture's Outputs) maps to the
contract's top-level `sub_score` field, not to `raw_findings`. The `raw_findings`
below contain the remaining Outputs fields only.

```json
{
  "active_advertiser_count": 12,
  "avg_ad_run_duration_days": 45,
  "market_stage": "Growing"
}
```

### 4.2 Competitor Analysis Agent

```json
{
  "top_competitors": [
    {"name": "Store A", "estimated_scale": "medium", "price": 29.99}
  ],
  "gaps_identified": ["no bundle options", "no extended warranty"],
  "competitive_barrier": "Medium"
}
```

### 4.3 Pricing Analysis Agent

Note: `perceived_value_score` is a component score that feeds into the agent's
internal reasoning. The contract `sub_score` is independently derived (gap
between recommended price and viable-margin price), not equal to
`perceived_value_score`.

```json
{
  "recommended_price_range": {"min": 29.99, "max": 39.99},
  "market_avg_price": 34.50,
  "price_elasticity_notes": "Moderate elasticity — 10% price drop yields ~15% volume increase",
  "perceived_value_score": 72
}
```

### 4.4 Margin Analysis Agent

```json
{
  "gross_margin_pct": 65.0,
  "net_margin_pct_after_ads": 22.5,
  "breakeven_cpa": 18.75,
  "contribution_margin_per_unit": 12.30
}
```

### 4.5 Facebook Ads Analysis Agent

Note: `creative_diversity_score` is a component score used in the agent's
internal analysis. The contract `sub_score` is derived from both sustained ad
evidence AND creative diversity, not equal to `creative_diversity_score` alone.

```json
{
  "active_ad_count": 34,
  "top_performing_angles": ["pain relief", "gift idea"],
  "avg_run_duration_days": 52,
  "estimated_spend_tier": "medium",
  "hook_patterns": ["Before/after transformation", "Problem-solution"],
  "creative_diversity_score": 68
}
```

### 4.6 TikTok Trend Analysis Agent

```json
{
  "trend_stage": "Rising",
  "hashtag_views": 2450000,
  "top_creator_content_examples": ["@creator1 unboxing video", "@creator2 review"],
  "organic_to_paid_ratio": 0.15
}
```

### 4.7 Amazon Review Analysis Agent

```json
{
  "avg_rating": 4.2,
  "review_volume": 187,
  "sentiment_breakdown": {"positive": 0.72, "neutral": 0.18, "negative": 0.10},
  "top_complaints": ["breaks after 2 weeks", "sizing inconsistent"],
  "top_praises": ["great value", "easy to use"],
  "quality_risk_flags": ["structural_defect_risk"]
}
```

### 4.8 Customer Psychology Analysis Agent

```json
{
  "core_pain_point": "Lower back pain from sitting at a desk all day",
  "core_desire": "Pain-free workday without expensive ergonomic furniture",
  "buyer_persona": "Remote workers aged 25–45",
  "purchase_trigger_type": "considered",
  "emotional_hooks": ["pain relief", "comfort", "productivity"]
}
```

### 4.9 Creative Opportunity Analysis Agent

```json
{
  "viable_angles": ["pain relief testimonial", "office setup transformation", "gift for desk worker"],
  "angle_saturation_map": {
    "pain relief testimonial": "crowded",
    "office setup transformation": "underused",
    "gift for desk worker": "underused"
  },
  "recommended_first_test_angles": ["office setup transformation", "gift for desk worker"],
  "fatigue_risk_level": "Low"
}
```

### 4.10 Risk Analysis Agent

```json
{
  "supplier_risk": "Low",
  "seasonality_risk": "Moderate",
  "platform_policy_risk": "Low",
  "legal_risk": "Low",
  "reputational_risk": "Low",
  "overall_risk_level": "Low"
}
```

---

## 5. Validation Rules (Enforced by Pydantic Schema)

- `agent_name`: must be non-empty string
- `pillar`: must be non-empty string
- `sub_score`: must be float/int in range [0.0, 100.0]
- `confidence`: must be exactly one of `"Low"`, `"Medium"`, `"High"`
- `evidence`: must be a non-empty array; each element must have non-empty `claim` and `citation`
- `data_completeness_pct`: must be float/int in range [0.0, 100.0]
- `raw_findings`: must be a JSON object (may be empty `{}`)
