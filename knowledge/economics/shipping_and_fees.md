# Shipping & Fees — Cost Benchmarks by Geo, Weight Class, and Payment Method

> This file documents shipping cost tiers and fee assumptions used by the Margin Analysis Agent
> (Architecture Section 12) and Pricing Analysis Agent (Architecture Section 11). These values
> are used as defaults when live shipping quotes from supplier integrations are unavailable.
>
> Shipping costs are estimated ranges based on general knowledge of eCommerce fulfillment rates.
> They are NOT derived from a current carrier-rate analysis — verify against actual carrier quotes
> before relying on them for real margin decisions. Payment processor fees are publicly published
> rates (Stripe, PayPal, Shopify Payments) as of 2026, and are factually verifiable.

**last_updated**: 2026-07-09

**Changelog**:
- 2026-07-09: Initial version — shipping tiers for US/EU/UK, payment fees, duty/tax notes.

---

## Rule 1: Shipping Cost Tiers by Weight Class (US Domestic)

Estimated eCommerce volume-discount rates. These are rough estimates — actual rates depend on carrier contract, volume, and dimensional weight.

| Weight Class | Ground (5–8 day) | Expedited (2–3 day) | Notes |
|---|---|---|---|
| 0–4 oz (lightweight: phone accessories, jewelry) | $3.00–$4.00 | $5.00–$7.00 | Fits in a poly mailer; lowest cost tier |
| 4–8 oz (small gadgets, cosmetics single items) | $4.00–$5.50 | $6.50–$9.00 | Still poly-mailer eligible |
| 8–16 oz (kitchen gadgets single, apparel) | $5.00–$7.00 | $8.00–$11.00 | May require small box for fragile items |
| 1–3 lbs (larger gadgets, bundles, shoes) | $7.00–$10.00 | $11.00–$16.00 | Boxed shipping; rate depends on box dimensions |
| 3–5 lbs (bundles, small appliances) | $10.00–$14.00 | $16.00–$22.00 | Dimensional weight becomes a factor |
| 5–10 lbs (multi-item bundles, larger home goods) | $14.00–$20.00 | $22.00–$30.00 | Significant cost; bundling economics improve if spread across multiple units |

### Rule 1.1: Free Shipping Threshold

If the product's price supports it, free shipping (absorbing the cost into the margin) is widely
believed to improve conversion rates in the sub-$50 price range. (The exact lift percentage varies
significantly by category and audience — treat as a directional heuristic, not a measured figure.)
The margin analysis should check:

```
Free shipping viable if: (price − COGS − payment_fees − CPA) > (shipping_cost × 3)
```

This ensures the contribution margin can absorb the shipping cost and still leave room for
returns and profit. If this condition is not met, the product should be sold with paid shipping
($3.99–$9.99 depending on weight) rather than absorbing the cost.

---

## Rule 2: Shipping Cost Tiers (EU)

Estimated intra-EU volume-discount rates. EU cross-border shipping is generally more expensive than
domestic within a single EU country (the exact premium varies by corridor and carrier). These rates
assume fulfillment from a single EU hub (e.g.,
Germany or Netherlands) shipping to any EU destination.

| Weight Class | Standard (5–10 day) | Tracked (3–5 day) | Notes |
|---|---|---|---|
| 0–4 oz | €3.50–€5.00 | €5.00–€7.00 | Letter-post in some countries; tracked is preferred for eCommerce |
| 4–8 oz | €4.00–€6.00 | €6.00–€9.00 | |
| 8–16 oz | €5.00–€7.50 | €8.00–€12.00 | |
| 1–3 lbs | €7.00–€11.00 | €12.00–€17.00 | |
| 3–5 lbs | €11.00–€16.00 | €17.00–€24.00 | |
| 5–10 lbs | €16.00–€22.00 | €24.00–€33.00 | |

**EU-specific notes**:
- VAT (20% avg) is included in the price for B2C sales to EU consumers — do NOT add VAT on top of
  the listed price in margin calculations unless selling B2B. VAT registration threshold: €10K/year
  in cross-border EU sales before an EU VAT number is required.
- IOSS (Import One-Stop Shop) required for shipments under €150 from outside the EU — this is the
  seller's responsibility, not reported to the consumer. The IOSS number must be printed on the
  customs form.

---

## Rule 3: Shipping Cost Tiers (UK)

Estimated UK domestic volume-discount rates.

| Weight Class | Standard (2–4 day) | Tracked (1–2 day) | Notes |
|---|---|---|---|
| 0–4 oz | £2.50–£3.50 | £3.50–£5.00 | Royal Mail Large Letter rates |
| 4–8 oz | £3.00–£4.50 | £5.00–£7.00 | |
| 8–16 oz | £3.50–£5.50 | £6.50–£9.00 | |
| 1–3 lbs | £5.00–£8.00 | £9.00–£13.00 | |
| 3–5 lbs | £8.00–£12.00 | £13.00–£18.00 | |
| 5–10 lbs | £12.00–£17.00 | £18.00–£25.00 | |

**UK-specific notes**:
- VAT (20%) applies to all B2C sales over £135 in value, OR on a case-by-case basis depending on
  fulfillment model. For goods under £135 sold from outside the UK, VAT is collected at point of sale
  and remitted by the seller via OSS (One Stop Shop).
- UK imposes a 2.5% duty for imports from non-preferential trading partners (most non-EU countries).
  Some categories have higher duty rates (electronics: 0–14%, textiles: 8–12%, ceramics: 8%).
  See Rule 5 for category-specific duty ranges.

---

## Rule 4: Payment Processor Fees

Per Architecture Section 12: "Payment Processing Fees (~3%)." The following table provides
more specific breakdowns.

| Provider | Scenario | Rate | Notes |
|---|---|---|---|
| Stripe | Standard (US) | 2.9% + $0.30 per transaction | Most common for US-based DTC operators |
| Stripe | International cards | 3.9% + $0.30 | +1% for non-US-issued cards |
| PayPal | Standard | 2.99% + $0.49 | Slightly higher flat fee vs Stripe |
| PayPal | Micropayments (< $10) | 5% + $0.05 | Better for very low AOV; check which pricing tier the account is on |
| Shopify Payments | Standard | 2.9% + $0.30 (same as Stripe — uses Stripe infrastructure) | Only available for Shopify stores |
| Klarna/BNPL | Where offered | 3.5–6% + $0.30 | Higher rate but increases conversion 10–20% on $50+ orders |

**Default assumption for margin calculations**: 3% + $0.30 per transaction (Stripe standard US rate,
consistent with Architecture Section 12's ~3% reference). This is acceptable for products priced
$15–$100. For products under $15, the $0.30 fixed fee becomes disproportionately significant
(2%+ of revenue) and should be modeled separately if margin precision is critical.

---

## Rule 5: Duty & Tax Notes by Region

Duty rates and tax rules vary significantly by product category and source/destination country.
The following are general heuristics — always verify against current tariff schedules for the
specific HS code.

### 5.1: US Imports (from China, most common eCommerce sourcing route)

| Category | Duty Rate (approx) | Notes |
|---|---|---|
| General consumer goods | 0–5% | Most DTC products (kitchen, home, pet, accessories) fall in this range |
| Textiles & apparel | 8–16% | Higher — specific rate depends on fiber composition and country of origin |
| Electronics | 0–3.5% | Generally low for consumer electronics |
| Footwear | 6–20% | Wide range depending on material and construction |
| Ceramics, glassware | 5–8% | |
| Furniture | 0–5.5% | |

**De Minimis**: For shipments valued under $800 (USD), no duty or formal customs entry is required
for imports into the US (Section 321 de minimis). Most DTC eCommerce shipments from China fall
under this threshold. Estimated — any future regulatory change to the de minimis threshold would
significantly affect margin assumptions for sub-$50 products sourced from China.

### 5.2: EU Imports

| Category | Duty Rate (approx) | Notes |
|---|---|---|
| General consumer goods | 0–4% | Most non-textile items |
| Textiles & apparel | 8–12% | Higher rate, consistent across the EU |
| Electronics | 0–3% | |
| Footwear | 8–17% | |
| Ceramics, glassware | 5–7% | |

**De Minimis**: The EU's de minimis threshold is €150 for customs duties (shipments under €150 are
duty-free). VAT is still applicable on all shipments regardless of value (see Rule 2's IOSS note).
As of mid-2026, the EU is considering eliminating the €150 threshold for eCommerce imports — this
would materially affect margins for DTC sellers shipping to the EU.

### 5.3: UK Imports

| Category | Duty Rate (approx) | Notes |
|---|---|---|
| General consumer goods | 0–4% | |
| Textiles & apparel | 8–12% | |
| Electronics | 0–3.5% | |
| Footwear | 8–16% | |
| Ceramics, glassware | 5–8% | |

**De Minimis**: UK de minimis threshold is £135 for customs duties. Under £135, no duty applies
but VAT (20%) is collected at point of sale via the OSS mechanism (see Rule 3).

### 5.4: Canada Imports

- **De Minimis**: CAD $40 for duty-free, CAD $150 for tax-free (lower threshold than US/EU)
  — most eCommerce shipments will incur duties and taxes
- **General duty rate**: 0–8% for most consumer goods, 18% for textiles
- **PST/QST**: Provincial sales taxes (8–10%) apply in addition to federal GST/HST (5–13%)
  depending on province, making Canada a structurally high-cost import destination for DTC

### 5.5: Australia Imports

- **De Minimis**: AUD $1,000 for duty and GST exemption — a generous threshold for most DTC shipments
- **General duty rate**: 0–5% for most consumer goods
- **GST**: 10% applies on imports over AUD $1,000 (most single-item DTC orders fall under this)

---

## Rule 6: Margin Calculation Template (for use by Margin Analysis Agent)

The Margin Agent should use the following formula per Architecture Section 12, pulling values
from the relevant tables above when live data is unavailable:

```
Net Margin per Unit =
  Price
  − COGS (from supplier data)
  − Shipping Cost (from weight/geo table above)
  − Payment Fee (3% of Price + $0.30, per Rule 4)
  − Returns Cost (Return Rate × (Price + Shipping × 2), per margin_benchmarks.md Rule 3.1)
  − Estimated CPA (from live FB Ads data OR margin_benchmarks.md default per category)
```

If the resulting net margin percentage is below 15%, the product cannot support paid acquisition
at scale per Architecture Section 2.3's hard veto and Section 12's decision rules.
