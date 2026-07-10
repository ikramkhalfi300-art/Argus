# Market Saturation — Advertiser Count Thresholds & Differentiation Gap Detection

> This file defines the market-stage classification system and differentiation-gap detection rules.
> Market-stage classifications are consistent with Architecture Section 9's definitions (Emerging/Growing/Peak/Declining).
> Used by the Market Saturation Agent, Competitor Analysis Agent, and Scoring Engine (Competitive Saturation pillar).

**last_updated**: 2026-07-09

**Changelog**:
- 2026-07-09: Initial version — stage thresholds, trend-direction rules, differentiation-gap matrix.

---

## Rule 1: Market Stage Classification (Advertiser Count + Trend Direction)

Classification is based on two axes: **absolute advertiser count** and **90-day trend direction** (rising/flat/declining). Trend is determined by comparing advertiser count from 90 days ago vs. current.

| Stage | Advertiser Count | 90-Day Trend | Score Interpretation |
|---|---|---|---|
| Emerging | <5 | Rising | High opportunity — early mover advantage available |
| Growing | 5–20 | Rising | Good opportunity — market is expanding, room for entrants |
| Peak | 20+ | Flat | Saturated — differentiation required for entry |
| Declining | Was 20+, now dropping | Declining | Late stage — market may be exiting hype cycle |

**Consistency note**: These thresholds match Architecture Section 9 line 290 (Emerging <5, Growing 5–20, Peak 20+, Declining was 20+ dropping). No deviation.

### Rule 1.1: Trend Direction Calculation

1. **Rising**: Advertiser count increased by >=20% over the trailing 90 days, OR count grew by >=3 new entrants in 90 days
2. **Flat**: Count changed <20% and net entrant change is -2 to +2 over 90 days
3. **Declining**: Count decreased by >=15% over 90 days, OR >=3 advertisers have stopped running ads for the product in the trailing 90 days

**Edge case — low base**: For Emerging markets (<5 advertisers), a change of just 1–2 advertisers qualifies as "Rising" even if percentage growth is >100%. Do not treat a market going from 1 advertiser to 3 as "stable."

### Rule 1.2: Trend-Velocity Modifier

For Growing and Peak stages, additionally check **acceleration** (is growth speeding up or slowing down?):
- **Accelerating** (last 30 days added more new advertisers than the prior 60 days) → still early-mid growth phase — favorable
- **Decelerating** (new entrants slowing) → approaching saturation — less favorable
- This modifier shifts the saturation sub-score by +/-5 points but does not change the stage classification

---

## Rule 2: Saturation Sub-Score Calculation

The raw saturation score (0–100) is driven by three inputs:

```
Saturation Score = (stage_base_score) + (differentiation_bonus) − (scale_penalty)
```

| Stage | Base Score |
|---|---|
| Emerging | 85 |
| Growing | 70 |
| Peak, differentiation available | 45 |
| Peak, no differentiation available | 25 |
| Declining, differentiation available | 30 |
| Declining, no differentiation | 15 |

### Rule 2.1: Differentiation Bonus (+0 to +15)

A differentiation angle exists if any of these are true:
- No competitor is executing a different price tier (e.g., all competitors at $19.99, opportunity to launch a premium $39.99 version)
- No competitor offers a bundle/pack variant
- No competitor targets a specific sub-audience (e.g., all general, none targeting pet owners specifically for a cleaning product)
- Gap exists in geo coverage (all US, none EU)
- Gap exists in offer structure (all single-sale, none with subscription/refill model)

**Bonus values**:
- 1 gap identified: +5
- 2+ gaps identified: +10
- 2+ gaps AND at least one gap is structural (different price tier or different business model, not just a different ad angle): +15

### Rule 2.2: Scale Penalty (−5 to −20)

A penalty is applied if the market has:
- Any single advertiser running ads for 60+ days with engagement proxy suggesting sustained spend (high-confidence scale signal): −5
- 3+ large-scale advertisers (estimated monthly ad spend >$10K each, per Architecture Section 10): −10
- Market dominated by a branded incumbent (brand-name product, not a generic): −15
- Branded incumbent WITH >500 Amazon reviews: −20

---

## Rule 3: Hard Veto Trigger Detection (per Architecture Section 2.3)

The hard veto rule fires if:
1. Saturation score <= 25 (Peak with no differentiation OR Declining with no differentiation)
2. AND more than 5 large-scale (estimated spend >$5K/month per advertiser) advertisers running the identical offer for 60+ days
3. AND no differentiation angle is available per Rule 2.1

If all three conditions are met, the Saturation Agent outputs `trigger_veto_check: true` for the Scoring Engine's hard veto evaluator.

---

## Rule 4: Data Completeness Flags

When determining confidence in the saturation analysis:

| Data Scenario | Completeness Effect |
|---|---|
| FB Ad Library data available for target geo | Full data — standard confidence |
| FB Ad Library data partial/blocked for geo | Drop one confidence tier; explicitly note which geo(s) missing |
| Only TikTok data available (no FB ads found) | Flag "non-paid-channel saturation" — use modified thresholds (TikTok Shop seller counts vs FB advertiser counts) |
| No ad data from any source | Saturation pillar scored "Insufficient Data" — weight redistributed per Architecture Section 8's edge case; confidence downgraded to Low |

**Consistency note**: The "Insufficient Data" / weight-redistribution behavior matches Architecture Section 8's specification and the Scoring Engine's missing-pillar logic (Sprint 2.1.2).
