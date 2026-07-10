# Winning Products — Historical Pattern Reference

> This file documents recurring historical patterns commonly observed across successful eCommerce product launches,
> drawn from general industry knowledge and published marketplace trend analyses.
> Used by the Discovery Agent (pattern-matching during product identification) and the Scoring Engine
> (weighting historical pattern alignment into pillar scores).
>
> Patterns are based on well-known, repeatable category/price-tier/angle/timing combinations that experienced
> eCommerce operators broadly recognize. These are qualitative heuristics, not project-derived empirical findings.
> They should be validated against this project's own data once Phase 4/5 agents are running.

**last_updated**: 2026-07-09

**Changelog**:
- 2026-07-09: Initial version — 4 pattern categories with 12 specific heuristics.

---

## Pattern 1: Sub-$30 Impulse "Pain Eraser"

The single most repeatable winning product pattern in eCommerce: a product that solves a specific, mild annoyance for under $30, with a clear before/after visual.

**Indicators**:
1. **Price range**: $14.99–$29.99 (sweet spot for zero-friction purchasing — no price comparison shopping)
2. **COGS**: $3–$8 per unit (supports 3–5x markup per Architecture Section 11)
3. **Problem clarity**: Solves one problem a person can describe in 5 words ("stops glasses fogging," "organizes cable mess")
4. **Visual proof**: Single clear before/after photo is sufficient to make the sale — no technical explanation needed
5. **Historical win rate**: Products matching all of 1–4 are broadly believed in the eCommerce operator community to have a significantly higher chance of achieving profitable ad spend within 30 days vs. products missing any one indicator. (This is a qualitative heuristic, not an empirically measured figure — treat as directional guidance until validated against this project's own data in Phase 8.)

**Edge case**: Products at $9.99–$14.99 can also win but require higher volume to overcome fixed ad costs — net margin per unit is often too thin for anything beyond break-even testing.

---

## Pattern 2: The "Better Version" Mid-Tier (Considered Purchase, $30–$80)

Products that improve on a known, already-selling category by fixing a specific common complaint.

**Historical examples**:
1. **Rechargeable vs. battery-powered** gadgets — a widely recognized upgrade angle across multiple categories (kitchen scales, string lights, phone stands, pet toys, travel organizers) — customers will pay 1.5–2.5x the base category price for "no batteries needed"
2. **Collapsible/portable version of a bulky home item** — collapsible water bottles, folding silicone food containers, compact travel steamer — win by solving storage pain in an established commodity category
3. **One-step version of a multi-step process** — all-in-one cleaning tool, pre-measured pod detergent, self-stirring mug — win on convenience in a category customers are mildly frustrated with but not actively searching for a replacement

**Thresholds**:
- 1a: Upgrade product price must be 1.5–2.5x the commodity baseline, not 5x+ (at 5x+, you're competing on a different purchase consideration level)
- 1b: The base category must have proven ad-spend evidence (20+ ads running for 60+ days) — fixing a problem nobody is trying to sell for is a product/market fit risk
- 1c: The "better version" must be demonstrable in a 15-second video — improvements that require explanation struggle in feed-based ad formats

---

## Pattern 3: Seasonal/Holiday Spike Products (GO Category)

Products whose demand is structurally concentrated in a known seasonal window, with proven repeatable peaks year-over-year.

**Categories with commonly recognized seasonal patterns**:
1. **Fitness/wellness** (Jan–Mar): Resistance bands, posture correctors, massage guns, yoga accessories — peak search volume Jan 1–Feb 15, declining through March
2. **Summer/travel** (May–Jul): Travel organizers, packing cubes, sun protection accessories, portable fans, car organizers — peak May 15–Jul 15
3. **Back-to-school** (Jul–Sep): Desk organizers, lunch containers, backpack accessories, study aids — peak Aug 1–Sep 15
4. **Gift/holiday** (Oct–Dec): Novelty gifts, personalized items, stocking stuffers, gift sets, home/decor items — peak Nov 1–Dec 15

**Winning within seasonals**:
1. Launch 60–90 days before peak — allows time for ad optimization before demand surge
2. Capitalize on creative that works year one in year two with minimal refresh — the highest-ROI pattern in seasonal eCommerce
3. Beware: a seasonal product analyzed 4+ months out of season will look like a NO-GO — Risk Agent must flag this per Architecture Section 18's edge-case rule, not score it permanently low

---

## Pattern 4: Subscription/Bundle-Model Products (High LTV Signal)

Products that naturally support repeat purchase or upsell bundling show disproportionately high long-term profitability despite higher initial CPA.

**Indicators**:
1. **Consumable or replenishable**: Filter replacements, refill pods, disposable heads, biodegradable bags — the product itself has a natural repurchase cycle of <90 days
2. **Bundle-ready**: Can be packaged as a "starter kit + refill" or "3-pack at a discount" — the unit economics of a $25/unit product at $60/3-pack are significantly better because shipping cost is amortized and CPA is paid once for 3x the order value
3. **Cross-sell adjacency**: Naturally sits next to other products in the same store (e.g., kitchen gadget + set of recipe cards, or a pet product + travel bowl)

**Thresholds**:
- 1a: Subscription/bundle LTV must be at least 3x the first-purchase contribution margin to justify higher initial CPA
- 1b: If the product is consumable but the average refill interval exceeds 90 days, treat as single-purchase with lower LTV — most ad platforms' 7-day click attribution window will not capture the second purchase
- 1c: Products with natural subscription models can sustain a CPA that is 1.5x higher than the single-purchase CPA ceiling and still be profitable long-term — but only test this after proving single-purchase unit economics first

---

## Anti-Patterns (Products That Look Promising but Historically Fail)

1. **First-of-its-kind (no proven category)**: Architecture Section 1.3 explicitly penalizes this. Products that invent a new category ("never seen before!") are widely believed to fail at a higher rate in paid ads testing vs. products in a proven category, because they require educating the market before converting it — a cost most ad budgets can't sustain. (The exact failure-rate differential is not empirically measured — this is a qualitative risk heuristic.)
2. **Single viral video with no ad history**: A TikTok video with 5M views but $0 in ad spend across any platform. Pattern: novelty virality that doesn't convert to purchase intent. Architecture Section 1.3 and Section 14 both address this — the system must verify commerce-intent, not just engagement.
3. **"Premium" version of a commodity with no visible difference**: A $45 product in a category where the average is $18, with no demonstrable quality difference (same OEM source, same materials). These are broadly recognized as failing — customers who buy cheap on Facebook will comparison-shop; customers who buy premium on Facebook need a story, not just a higher price.
