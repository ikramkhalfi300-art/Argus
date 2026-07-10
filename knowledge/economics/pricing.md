# Pricing — Category-Specific Markup Heuristics & Price-Elasticity Notes

> This file provides markup-multiple guidance by price tier, price-elasticity notes by category,
> and bundle-pricing patterns. Used by the Pricing Analysis Agent (Architecture Section 11)
> as the knowledge base for recommended price range determination.
>
> Cross-check consistency: These heuristics match the markup multiples referenced in
> Architecture Section 6 (3-5x COGS for sub-$30 impulse buys, 2.5-3x for $50+ considered purchases).
> Where these heuristics extend beyond what the architecture specifies, they are labeled as
> "extension" below.

**last_updated**: 2026-07-09

**Changelog**:
- 2026-07-09: Initial version — markup heuristics, elasticity notes, bundle patterns.

---

## Rule 1: Markup Multiples by Price Tier

The appropriate COGS-to-price markup varies by price tier, driven by the proportion of ad spend the price must support.

| Price Tier | Multiple of COGS | Rationale | Architecture Reference |
|---|---|---|---|
| Sub-$15 (micro-impulse) | 4x–6x | Lowest AOV means ad cost consumes the largest % of revenue; higher markup required to leave any margin after $8–$12 CPA | Extension of Section 6 logic |
| $15–$29.99 (impulse) | 3x–5x | Standard impulse-buy tier; 3x is minimum for healthy margin, 5x is achievable with strong perceived value | Section 6 explicitly: "3-5x COGS for sub-$30 impulse buys" |
| $30–$49.99 (low-considered) | 2.5x–4x | Transition zone — customer begins price-comparing but not yet deeply; premium positioning can push above 3x | Extension |
| $50–$99.99 (considered) | 2.5x–3x | Customers actively compare; premium differentiation needed to sustain >3x | Section 6 explicitly: "2.5-3x for $50+ considered purchases" |
| $100+ (high-considered) | 2x–2.5x | CPA as % of AOV naturally lower; high-ticket customers are less price-sensitive but more quality-sensitive | Extension |

### Rule 1.1: Minimum Viable Markup Check

For any price tier, the markup must leave room for:
- **Cost of goods** (COGS): variable
- **Shipping**: $3–$15 (see shipping_and_fees.md)
- **Payment processing**: ~3% of price (per Architecture Section 12)
- **Returns cost**: 2–15% of price depending on category (see margin_benchmarks.md)
- **Ad spend**: target CPA should be ≤ 30% of price for healthy unit economics (per Architecture Section 12's 15% net margin floor logic — at 30% CPA + other costs, 15% net margin is achievable at the low end of each markup tier)

If the resulting net margin after all costs is below 15%, the pricing is flagged as blocking per Architecture Section 11's decision rule and Section 2.3's hard veto threshold.

---

## Rule 2: Price-Elasticity Notes by Category

Price sensitivity varies significantly by category. The following notes inform the Pricing Agent's recommended price range.

| Category | Elasticity | Behavior Notes |
|---|---|---|
| Kitchen gadgets | Medium | Customers will pay a premium for "works better than current solution" but not for "looks nicer." Function-first pricing. |
| Beauty tools | Low–Medium | Medium elasticity at sub-$30 (impulse); lower elasticity at $30+ (brand/perceived-quality-driven). Strong angle + packaging can support higher price. |
| Phone accessories | High | Highly elastic — near-identical products available at many price points. Differentiate via bundling or unique claim (military-grade drop protection, magnetic ecosystem). |
| Pet supplies | Low | Consistently lowest elasticity across eCommerce — pet owners are less price-sensitive than any other common DTC category. Pricing can be 10–20% above average without volume loss. |
| Fitness equipment | Medium | New Year resolution buyers are less price-sensitive (Jan); same buyers become price-sensitive by March. Timing-dependent elasticity. |
| Home organization | Medium | Customers pay for "promise of order" — price tolerance correlates with problem severity (messy garage > mild desk clutter). |
| Travel accessories | Medium–High | Pre-trip buyers less price-sensitive; non-urgent buyers compare more. Higher tolerance for unique features (compression, RFID, TSA-friendly). |
| Baby/kids | Low | Second-lowest elasticity after pets. Safety/convenience-driven buying. Supports premium pricing if quality signal is clear. |
| Outdoor/garden | Medium | Functional purchases; price sensitivity increases as product complexity decreases (a trowel has no premium tier; a grill thermometer has more room). |

---

## Rule 3: Premium Positioning Feasibility

A product can command a premium price (top of its markup-multiple range or higher) if:

1. **Material quality signal** — stainless steel vs. plastic, BPA-free silicone vs. unknown plastic, borosilicate glass vs. standard glass. Customers can visually identify a quality material difference.
2. **Design differentiation** — a genuinely different visual design (Scandinavian/minimalist, retro, patent-protected shape) vs. a generic white-label product. Generic products cannot command premium without brand-building.
3. **Guarantee/bundle** — "Lifetime guarantee" or "buy the 3-pack and save 25%" can lift effective price 15–30% above the single-unit baseline.
4. **Certification badge** — FSA/CE/FCC certification, organic/BPA-free/cruelty-free label, patent-pending claim. Visible trust signals support premium pricing.

**If none of these conditions are met, default to the middle or low end of the markup-multiple range for the price tier.** There is no point pricing a generic product at 5x COGS when 10 identical products are selling at 3x COGS on the same ad platform.

---

## Rule 4: Bundle-Pricing Patterns

### Rule 4.1: Per-Unit Discount in Bundles

Standard bundle discount tiers:
- **2-pack**: 10–15% discount vs. single-unit price (per-unit price is 85–90% of single)
- **3-pack**: 15–25% discount (per-unit is 75–85% of single)
- **5+ pack**: 25–35% discount (per-unit is 65–75% of single)

**Rationale**: The discount must be meaningful enough to incentivize the bundle purchase (reducing return rate and shipping cost per unit) but not so deep that it erodes contribution margin. A bundle discount that brings per-unit margin below the 15% net floor is self-defeating.

### Rule 4.2: Bundle AOV Target

The total bundle price should target an AOV of at least $35–$50. At this level, the order margin can absorb a $15–$20 CPA and still clear the 15% net margin floor. Single-unit prices below $20 create a structural challenge for paid-acquisition profitability.

### Rule 4.3: Cross-Sell Bundling

If the product naturally pairs with another product in the same store (e.g., kitchen gadget + reusable storage bag set, or pet bed + travel bowl), price the bundle at the main product's price + 40–50% of the add-on's single-unit price. This captures the "add-to-order" impulse without requiring the customer to feel they're overpaying for the secondary item.

---

## Rule 5: Competitive Pricing Heuristic

When competitor pricing data is available, the Pricing Agent should:

1. Identify the median competitor price for the closest comparable product (same category, same quality tier, same bundle structure)
2. If a differentiation gap exists (Rule 3 conditions), price 10–20% above the median
3. If no differentiation gap exists, price at or slightly below (0–10% below) the median — not more than 10% below, as aggressive discounting on a generic product trains the algorithm to expect your price to be the lowest, making it hard to raise later

**Exception**: If the median competitor price is below the minimum viable price per Rule 1.1 (doesn't leave 15% net margin after all costs), flag the category as "margin-constrained — competitive pricing incompatible with profitable unit economics." This feeds into the Unit Economics pillar score.
