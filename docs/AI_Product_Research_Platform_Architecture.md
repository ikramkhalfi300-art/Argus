# AI Product Research & Decision Intelligence Platform
## Complete System Architecture & Build Documentation

---

## 0. PROJECT VISION

Most "winning product finder" tools (Dropship.io, PPSpy, Minea, etc.) answer one question: *"What products are trending?"*

This platform answers a fundamentally different, harder question:

> **"Should I invest my money into testing this specific product, right now, in this specific market — and if yes, how, and with how much budget?"**

This is not a product discovery tool. It is a **capital allocation decision engine** for eCommerce operators, disguised as a product research tool. Every module exists to feed one final artifact: a **Go / No-Go / Go-with-Conditions investment memo**, the way an analyst would write one before a fund deploys capital.

The system must behave like a skeptical, experienced eCommerce operator who has lost money before — not like a hype engine that says "this is trending, sell it now."

### Design Principles
- **Asymmetric skepticism**: default posture is "prove to me this is worth the risk," not "confirm my excitement."
- **Every score must be explainable** — no black-box numbers. Every output traces back to raw evidence.
- **Money-first framing** — everything converts back to: expected margin, required ad budget, breakeven CPA, downside risk, and time-to-signal.
- **Agent specialization over one giant prompt** — each domain (ads, pricing, psychology, saturation) is a separate expert agent with its own knowledge base, not one LLM call doing everything.
- **Human stays the decision-maker** — the system produces a recommendation with confidence + reasoning, not an autonomous buy/sell action.

---

## 1. CORE PHILOSOPHY

### 1.1 The "Investment Analyst" Mental Model
Traditional tools ask: *Is this product winning?*
This system asks the four questions a VC asks before funding a startup:

1. **Market**: Is there proven, durable demand? (not a 3-week TikTok spike)
2. **Unit Economics**: Can this product be profitable after ads, COGS, shipping, returns, and platform fees?
3. **Competitive Moat**: Can I actually win share here, or is the market already saturated by better-funded competitors?
4. **Execution Risk**: What could kill this test — creative fatigue, supplier reliability, platform policy, seasonality, legal/compliance?

### 1.2 The Three Verdicts
Every product run through the system ends in one of three states:
- ✅ **GO** — Strong signal across demand, economics, and competitive space. Recommended test budget provided.
- ⚠️ **GO WITH CONDITIONS** — Real opportunity but with a named risk (e.g., "only viable if you can source below $X" or "only in EU market, saturated in US"). Conditions are explicit and testable.
- ❌ **NO-GO** — Documented reasons, so the founder learns *why*, not just *no*.

### 1.3 Anti-Hype Guardrails
- The system explicitly penalizes products that only show "TikTok virality" with no ad spend evidence (viral ≠ profitable).
- The system explicitly penalizes products with no repeatable historical winning pattern (a first-of-its-kind product gets flagged as "higher uncertainty," not "innovative and safe").
- Saturation and Reddit/review-mining data are weighted as highly as ad presence — the system is built to catch "everyone is already fatigued on this" before you spend on it.

---

## 2. DECISION FRAMEWORK

### 2.1 The Investment Scorecard (Master Output)

The final decision is a weighted composite across 7 pillars, each scored 0–100:

| Pillar | Weight | What it measures |
|---|---|---|
| Demand Strength | 20% | Search + social + ad volume trend durability |
| Unit Economics | 20% | Realistic net margin after all costs |
| Competitive Saturation | 15% | How crowded/defensible the niche is |
| Creative Runway | 15% | How many distinct ad angles are viable (fatigue resistance) |
| Customer Psychology Fit | 10% | Strength/clarity of the pain-point → solution story |
| Risk Profile | 10% | Legal, supplier, platform, seasonality risk |
| Reviews/Sentiment Quality | 10% | Product quality signal from existing sellers' reviews |

**Composite Score = Σ(pillar_score × weight)**

### 2.2 Decision Thresholds
- **≥ 75** → GO (recommended test budget: $150–$300, 3–5 creatives, 3–5 day test window)
- **55–74** → GO WITH CONDITIONS (system names the specific condition(s) that must hold)
- **< 55** → NO-GO (system states which pillar(s) failed and by how much)

### 2.3 Hard Veto Rules (override the composite score)
Regardless of composite score, auto NO-GO if:
- Net margin after realistic CPA < 15% → economics can't support paid acquisition.
- Product appears on a legal/compliance blocklist (electronics near-fire-risk, health claims, weapons-adjacent, IP-infringing).
- Fewer than 2 viable creative angles exist (creative-fatigue risk too high to sustain a test).
- Saturation score indicates >5 large-scale (Yes, Level 4+) advertisers running the identical offer for 60+ days with no differentiation angle available.

### 2.4 Confidence Rating
Every verdict ships with a **Confidence Level** (Low / Medium / High) based on **data completeness**, not just score — e.g., a GO based on 40 ad results and 200 reviews is High Confidence; a GO based on 3 ad results and no review data is Low Confidence, and the system says so explicitly.

---

## 3. AI REASONING PIPELINE

### 3.1 Pipeline Overview (Orchestration Flow)

```
[Input: Product URL / Name / Image]
        │
        ▼
[1. Discovery/Ingestion Agent] → normalizes product identity, category, variants
        │
        ▼
[2. Parallel Analysis Layer] (agents run concurrently, each independent)
  ├─ Market Saturation Agent
  ├─ Competitor Analysis Agent
  ├─ Pricing Analysis Agent
  ├─ Margin Analysis Agent
  ├─ Facebook Ads Analysis Agent
  ├─ TikTok Trend Agent
  ├─ Amazon Review Mining Agent
  ├─ Customer Psychology Agent
  ├─ Creative Opportunity Agent
  └─ Risk Analysis Agent
        │
        ▼
[3. Validation Agent] — cross-checks agents for contradictions
        │
        ▼
[4. Scoring Engine] — deterministic math, not LLM guesswork
        │
        ▼
[5. Chief Analyst Agent (Orchestrator/Synthesizer)] — writes the investment memo
        │
        ▼
[6. Output: Decision Report (GO / CONDITIONAL / NO-GO)]
```

### 3.2 Why Parallel + Specialized (not one mega-agent)
- Each domain agent has a **narrow, high-quality knowledge base** (see Section 5) rather than one prompt trying to know everything about ads, psychology, and margins at once — this is the single biggest quality lever in the whole system.
- Specialized agents can be independently improved, re-prompted, or swapped for better models without touching the rest of the pipeline.
- Parallel execution keeps total analysis time reasonable (target: under 3 minutes end-to-end for a full report).

### 3.3 The "Validation Agent" — Critical Anti-Hallucination Layer
Before scoring, a dedicated agent re-reads all outputs from the 10 domain agents and checks:
- Do any two agents contradict each other? (e.g., Pricing Agent says "premium positioning viable" while Saturation Agent says "20 sellers racing to the bottom on price")
- Is any claim made without a data citation? (flagged and down-weighted)
- Are confidence levels consistent with actual evidence volume?

This agent's job is to **catch and flag hallucination or overconfidence** before it reaches the scoring math — it does not generate new analysis.

### 3.4 The Chief Analyst / Synthesizer Agent
This is the "senior partner" persona — takes the validated, scored data and writes the human-readable memo in the tone of an investment analyst: direct, numbers-first, unafraid to say "don't do this."

---

## 4. KNOWLEDGE SYSTEM

### 4.1 Why a Knowledge System (not just prompts)
LLMs are generalists. A senior eCommerce strategist's edge is **pattern memory** — thousands of past winning/losing products, ad accounts, and niches. The Knowledge System is how we simulate that memory: a structured, versioned set of markdown documents that every agent is grounded in via retrieval (RAG) before reasoning.

### 4.2 Structure
Each knowledge file is:
- **Atomic** — one domain per file, so agents only retrieve what's relevant to them (controls cost + reduces noise).
- **Rule-based, not vague** — written as explicit heuristics and thresholds ("CPA > 40% of AOV = red flag"), not general essays.
- **Versioned** — knowledge files carry a `last_updated` date and changelog, since ad platform behavior and consumer trends shift every few months.
- **Evidence-linked** — where possible, rules cite the pattern that produced them ("observed across 200+ scaled Q4 2024 apparel launches").

### 4.3 Retrieval Strategy
Each agent has a fixed "knowledge manifest" — the specific KB files it is allowed to retrieve from (e.g., the Facebook Ads Agent only pulls from `facebook_ads.md`, `creative_rules.md`, `marketing_angles.md`). This prevents context bloat and keeps each agent's expertise narrow and accurate.

---

## 5. DATA SOURCES

| Source | What it provides | Access method | Reliability notes |
|---|---|---|---|
| Facebook Ad Library | Live/historical ads, run duration, ad text, page info | Public API/scrape | Free, official, most important single source |
| TikTok Creative Center | Trending sounds, hashtags, ad examples | Public API/scrape | Good for early trend signal, weak for economics |
| Amazon | Reviews, star distribution, Q&A, BSR | Scrape (rate-limit aware) | Best source for product-quality truth |
| Google Trends | Search interest over time, geography | Public API | Good for durability check, not intent-quality |
| AliExpress/CJ/Supplier APIs | COGS, MOQ, shipping times, supplier ratings | API/scrape | Needed for margin math and supply risk |
| Shopify store scanners (e.g. public storefront scraping) | Competitor pricing, store count, store age | Scrape | Used for saturation + competitor pillars |
| Reddit / forums | Unfiltered customer language and objections | Public API (PRAW) | Best source for psychology/language mining |
| Exchange rate / tax APIs | Currency and duty normalization | API | Needed for accurate margin across geos |

### Edge Cases & Failure Handling (applies platform-wide)
- **Rate limiting / scraping blocked** → system falls back to cached data with an explicit "data freshness: X days old" flag, never silently serves stale data as fresh.
- **Source returns zero results** → pillar score is marked "Insufficient Data" rather than defaulted to a neutral score — this avoids false confidence.
- **Conflicting currency/region data** → default to the user's target launch market, explicitly stated in the report.

---

## 6–19. ANALYSIS MODULES

*(Each module follows the same documentation contract: Purpose, Inputs, Outputs, Logic, Decision Rules, AI Prompt Core, Scoring, Improvements, Edge Cases, Failure Cases.)*

---

### 6. PRODUCT DISCOVERY PIPELINE

**Purpose**: Take a raw input (URL, image, product name, or "find me products in X niche") and produce a normalized Product Identity Object that every downstream agent consumes.

**Inputs**: User query (text/URL/image), optional category/niche filter, optional target market/geo.

**Outputs**: `ProductIdentity{ name, category, subcategory, variants[], normalized_keywords[], detected_niche, image_refs[], source_url }`

**Logic**:
1. If image provided → reverse-image-search + vision model to identify product type and generate candidate names.
2. If URL provided → scrape product page (title, images, price, variants, description).
3. If free-text niche query (e.g. "find winning pet products") → run Discovery Agent across TikTok/FB ad libraries filtered by category to generate a shortlist of 10–20 candidates.
4. Deduplicate near-identical variants (same product, different color/size) into one identity with variant metadata.

**Decision Rules**: A product only proceeds to full analysis if it can be mapped to at least one concrete category + at least 3 corroborating data points (e.g., found in ad library + found on a supplier + found in reviews). Otherwise flagged "Unverified Product — Insufficient Identity Match."

**AI Prompt Core** (Discovery Agent):
```
You are a product identification analyst. Given {input}, identify:
1. The precise product category and subcategory
2. 5-10 normalized search keywords a buyer would use
3. The likely target customer niche
4. Red flags if this looks like a knockoff/IP-infringing item
Return structured JSON only. Do not guess brand names you cannot verify.
```

**Scoring**: N/A (gatekeeping stage, not scored) — outputs a binary "Ready for Analysis" / "Needs Clarification" flag.

**Possible Improvements**: Fine-tuned product-category classifier to reduce LLM cost per discovery call; barcode/UPC lookup integration.

**Edge Cases**: Generic/white-label products with no distinguishing features; products sold under many different names across stores.

**Failure Cases**: Image too ambiguous (e.g., "a gadget" with no clear category) → system asks user one clarifying question instead of guessing.

---

### 7. PRODUCT VALIDATION PIPELINE

**Purpose**: Confirm the product is real, currently sellable, and not already legally/compliance blocked before spending compute on full analysis.

**Inputs**: `ProductIdentity` object.

**Outputs**: `ValidationResult{ is_valid, is_saleable_on_meta, is_saleable_on_tiktok, compliance_flags[], supplier_availability }`

**Logic**:
1. Cross-check product category against Meta/TikTok prohibited & restricted content policies (weapons, health claims, supplements, adult, counterfeits).
2. Check supplier availability (in-stock, MOQ reasonable, shipping time < target threshold, e.g. 12 days).
3. Check for obvious IP infringement (branded characters, logos, copied listing photos from a trademarked brand).

**Decision Rules**: Any compliance_flag = true → hard stop, product marked NO-GO regardless of downstream scores (see Section 2.3 Hard Vetoes).

**AI Prompt Core**:
```
You are a platform-policy compliance analyst for Meta and TikTok ads.
Given this product: {product_identity}
1. Does this fall under restricted advertising categories (health claims, supplements, weapons-adjacent, adult, financial products)?
2. Is there visible IP/trademark risk in the images or branding?
3. State your reasoning citing the specific policy clause where possible.
Return: {is_flagged: bool, flags: [], reasoning: string}
```

**Scoring**: Pass/Fail gate, not weighted into composite score — but a Fail always forces NO-GO.

**Possible Improvements**: Maintain a living `compliance_blocklist.md` updated as platform policies change; add EU/UK-specific compliance (CE marking, etc.) for cross-border sellers.

**Edge Cases**: Products legal in one country, restricted in another (e.g., certain supplements EU vs US) — system must be geo-aware.

**Failure Cases**: Policy ambiguity (gray-area products like "wellness" gadgets) → system defaults to flagging as "Requires Manual Legal Review," never silently approves.

---

### 8. PRODUCT SCORING ENGINE

**Purpose**: The deterministic math core that converts all agent outputs into the final Investment Scorecard (Section 2.1). This is NOT an LLM call — it's a rules/weights engine for consistency and auditability.

**Inputs**: All 10 domain agent outputs (each pre-normalized to a 0–100 sub-score with supporting evidence array).

**Outputs**: `ScoreCard{ pillar_scores{}, composite_score, verdict, confidence_level, triggered_vetoes[] }`

**Logic**: Weighted sum per Section 2.1, veto-check per Section 2.3, confidence calculation based on data completeness (% of expected data points actually retrieved per pillar).

**Decision Rules**: See Section 2.2 and 2.3 (thresholds and hard vetoes).

**AI Prompt Core**: None — pure deterministic code. (This is the one module explicitly NOT driven by an LLM prompt, by design, to keep the final score auditable and non-hallucinated.)

**Scoring**: This module *is* the scoring system (see 2.1).

**Possible Improvements**: Make pillar weights configurable per user (a supplement seller may want to weight Risk higher; a fashion seller may weight Creative Runway higher); backtest weights against historical known winners/losers to calibrate.

**Edge Cases**: Missing data for a pillar (e.g., no Amazon listing exists for a TikTok-native product) → that pillar's weight is redistributed proportionally across the remaining pillars, and confidence level is downgraded accordingly, not silently defaulted to 50.

**Failure Cases**: Two pillars in direct conflict with similar evidence strength — system flags "Mixed Signal" in the memo rather than letting the weighted average mask the disagreement.

---

### 9. MARKET SATURATION ANALYSIS

**Purpose**: Determine whether the market opportunity is still open or already crowded/exhausted.

**Inputs**: Product identity, category keywords, geo/target market.

**Outputs**: `SaturationResult{ active_advertiser_count, avg_ad_run_duration, market_stage (Emerging/Growing/Peak/Declining), saturation_score }`

**Logic**:
1. Query FB Ad Library + TikTok Creative Center for all active ads matching product keywords/category.
2. Count distinct advertisers, average ad run duration, and estimate ad spend tier via engagement proxy.
3. Plot advertiser count over the last 90 days to detect trend direction (rising = still opportunity; flat/declining after a peak = late-stage).
4. Classify market stage: **Emerging** (<5 advertisers, rising), **Growing** (5–20, rising), **Peak** (20+, flat), **Declining** (was 20+, now dropping).

**Decision Rules**:
- Emerging/Growing → high saturation_score (opportunity open).
- Peak with no differentiation angle available → low score, flagged for hard veto review.
- Declining → low score, explicit "market may be exiting hype cycle" flag.

**AI Prompt Core**:
```
You are a market-saturation analyst. Given this data on active advertisers for {product} over the last 90 days: {ad_data}
1. Classify the market stage (Emerging/Growing/Peak/Declining) with reasoning
2. Identify if there's a differentiation angle still available (different niche, different price tier, different bundle) or if it's a pure price/speed race
3. State your confidence based on data volume
Return structured JSON with citations to specific ad examples.
```

**Scoring**: 0–100, driven primarily by (a) market stage classification and (b) availability of a differentiation angle. Peak-with-no-angle scores below 30 automatically.

**Possible Improvements**: Add store-count scanning (how many Shopify stores currently list this exact product) as a second saturation signal beyond ads.

**Edge Cases**: Product with low ad presence but high organic/TikTok Shop presence — saturation must account for non-paid channels too, not just Ad Library data.

**Failure Cases**: Ad Library data blocked/incomplete for a region → system explicitly states "Saturation analysis based on partial data (X region only)."

---

### 10. COMPETITOR ANALYSIS

**Purpose**: Identify who is already selling this product well, and what their playbook is — since you're not just entering a market, you're competing with specific operators.

**Inputs**: Product identity, saturation data (advertiser list).

**Outputs**: `CompetitorReport{ top_competitors[], their_pricing, their_positioning, their_offer_structure, estimated_scale, gaps_identified[] }`

**Logic**:
1. From the saturation module's advertiser list, identify the top 3–5 by estimated scale (ad run duration + engagement proxy + store signals).
2. Scrape their storefronts: pricing, bundle structure, guarantee/return policy, upsells, reviews count.
3. Identify what they are NOT doing (underserved angle, geo, price tier, bundle type) — this becomes the "gap."

**Decision Rules**: If top competitors have >500 reviews and a mature funnel (upsells, bundles, strong guarantee) with no visible weakness → high competitive barrier, lowers score. If competitors are thin (few reviews, generic single-product store, no bundling) → opportunity to out-execute, raises score.

**AI Prompt Core**:
```
You are a competitive intelligence analyst. Given these top competitor stores for {product}: {competitor_data}
1. Summarize each competitor's positioning, price point, and offer structure in one line each
2. Identify the single biggest gap or weakness across all of them (price tier, guarantee, bundling, geo, or audience)
3. Rate the overall competitive barrier to entry: Low/Medium/High
Cite specific evidence for each claim.
```

**Scoring**: 0–100, inversely related to competitive barrier strength, but with a positive adjustment if a clear, executable gap is identified.

**Possible Improvements**: Automated "funnel teardown" screenshots of competitor checkout flow for the user's reference.

**Edge Cases**: Market dominated by one large, hard-to-differentiate player (e.g., an established brand) — system should flag "Branded Incumbent Risk" distinctly from generic saturation.

**Failure Cases**: Competitor stores are private/password-protected or geo-blocked — system notes reduced confidence rather than guessing offer structure.

---

### 11. PRICING ANALYSIS

**Purpose**: Determine the realistic, defensible price point the market will bear.

**Inputs**: Competitor pricing data, Amazon pricing, supplier COGS, category price-elasticity heuristics (from `pricing.md`).

**Outputs**: `PricingResult{ recommended_price_range, market_avg_price, price_elasticity_notes, perceived_value_score }`

**Logic**: Cross-reference competitor and Amazon price points, weighted toward stores with strongest signals of scale (per Competitor module), then apply category-specific markup heuristics from the knowledge base (e.g., "impulse-buy sub-$30 products should carry 3–5x COGS markup for ad-supported margin; considered-purchase $50+ products can carry 2.5–3x").

**Decision Rules**: If recommended price range creates margin below the 15% hard-veto threshold after realistic CPA (see Margin module) → flag pricing as a blocking constraint, not just informational.

**AI Prompt Core**:
```
You are a pricing strategist. Given: market prices {competitor_prices}, COGS {cogs}, category {category}
1. Recommend a price range with reasoning (not just "match competitors")
2. Note if the product supports premium positioning (bundle, better guarantee, or perceived quality gap) vs. must compete on price
3. Flag if COGS makes profitable pricing implausible in this market
```

**Scoring**: 0–100 based on gap between recommended price and viable-margin price (closer/positive gap = higher score).

**Possible Improvements**: A/B price-point testing recommendation baked into report ("test $34.99 vs $39.99").

**Edge Cases**: Highly fragmented pricing across competitors (some $19, some $59 for near-identical items) → system should identify *why* (bundle size, brand, quality tier) rather than average blindly.

**Failure Cases**: No comparable pricing data found at all → falls back to COGS-multiple heuristic only, with confidence flagged Low.

---

### 12. MARGIN ANALYSIS

**Purpose**: The single most important economic gate — determine if this product can be profitable after ALL real costs, not just COGS.

**Inputs**: COGS, shipping cost, platform fees (Shopify/payment processor %), estimated return rate (from category heuristics + reviews data), recommended price, estimated CPA (from FB Ads module).

**Outputs**: `MarginResult{ gross_margin_pct, net_margin_pct_after_ads, breakeven_cpa, contribution_margin_per_unit }`

**Logic**:
```
Net Margin = Price − COGS − Shipping − Payment Processing Fees (~3%) − Estimated Returns Cost − Estimated CPA
Breakeven CPA = Price − COGS − Shipping − Payment Fees − Returns Cost
```
Estimated CPA is pulled from the FB Ads module's benchmark data for the category; if unavailable, category defaults from `margin_benchmarks.md` are used.

**Decision Rules**: Net margin after ads < 15% → Hard Veto (Section 2.3). 15–25% → Conditional (flag "thin margin, requires tight CPA control"). >25% → strong pillar score.

**AI Prompt Core**:
```
You are a unit-economics analyst. Given: price {price}, COGS {cogs}, shipping {shipping}, category avg CPA {cpa}, category avg return rate {returns}
1. Calculate gross and net margin step by step, showing your math
2. State the breakeven CPA explicitly
3. Flag if this is a "thin margin" product requiring unusually tight ad efficiency to work
```

**Scoring**: 0–100, directly proportional to net margin % (0% or negative = 0, 40%+ = 100, scaled linearly with the 15% hard floor).

**Possible Improvements**: Live currency/duty calculator for cross-border sellers; scenario modeling (best/expected/worst case margin).

**Edge Cases**: High-ticket/considered-purchase items where CPA is naturally higher but so is AOV — margin math must not penalize these using impulse-buy CPA benchmarks.

**Failure Cases**: No reliable CPA benchmark exists for a brand-new category → system uses the closest adjacent category's benchmark and explicitly labels it an "estimated proxy," flagging Low confidence.

---

### 13. FACEBOOK ADS ANALYSIS

**Purpose**: Determine actual paid-acquisition proof — the strongest single signal of real, sustained demand.

**Inputs**: Product keywords, category, geo, FB Ad Library data.

**Outputs**: `FBAdsResult{ active_ads[], top_performing_angles[], avg_run_duration, estimated_spend_tier, hook_patterns[], creative_diversity_score }`

**Logic**:
1. Pull all active + recent (90-day) ads matching the product.
2. Cluster ads by angle/hook (e.g., "pain relief," "gift idea," "before/after transformation") using the Psychology + Creative knowledge bases.
3. Identify the longest-running ads (a strong signal of profitability — dead ads get killed fast) and extract their hook structure.
4. Score creative diversity — how many genuinely different angles exist vs. everyone running the same one ad.

**Decision Rules**: Zero ads found at all → treat as a red flag unless product is TikTok-native (cross-check TikTok module first). 1–2 advertisers with very long run durations (60+ days) = strong proof + moderate saturation — favorable. 10+ advertisers all running near-identical ads for 90+ days = saturated, low creative-differentiation opportunity.

**AI Prompt Core**:
```
You are a Meta ads intelligence analyst. Given these active/recent ads for {product}: {ad_library_data}
1. Cluster the ads into distinct marketing angles (name each angle)
2. Identify the ad(s) with the longest run duration — these are likely the most profitable; extract their hook (first line/first 3 seconds)
3. Rate creative diversity in the space: Low/Medium/High
4. Estimate whether this looks like an early-stage or late-stage opportunity based on entrant count and diversity
Cite each claim with the specific ad it came from.
```

**Scoring**: 0–100 based on (evidence of sustained profitable ads) + (creative diversity/room for new angles), NOT raw ad count alone (raw count alone rewards saturation, which is wrong).

**Possible Improvements**: Estimated-spend modeling via engagement-rate proxies; historical ad archive tracking (has this exact ad run before, paused, relaunched — a "revival" pattern is a strong signal).

**Edge Cases**: Product sold under many different brand names/pages simultaneously — must aggregate by product identity, not by advertiser page.

**Failure Cases**: Ad Library API/scrape returns incomplete geo coverage → explicitly caveat the region(s) covered.

---

### 14. TIKTOK TREND ANALYSIS

**Purpose**: Capture organic/early-stage demand signal that often precedes paid ad presence — critical for catching products in the Emerging stage.

**Inputs**: Product keywords, TikTok Creative Center data, hashtag view counts, trending sound correlation.

**Outputs**: `TikTokResult{ trend_stage (Rising/Peaking/Declining), hashtag_views, top_creator_content_examples[], organic_to_paid_ratio }`

**Logic**:
1. Pull hashtag/keyword view trends over 30/90 days.
2. Cross-reference with FB Ads data: is organic virality converting into paid ad presence yet (a leading indicator of monetization) or is it "engagement without commerce" (common with novelty/comedy virality that never converts to sales)?
3. Classify trend stage using view-count velocity.

**Decision Rules**: Rising organic trend + zero paid ads yet = "Early Mover Opportunity" flag, higher score with explicit "unproven monetization" caveat. Peaking/Declining organic + already saturated paid = late, lower score.

**AI Prompt Core**:
```
You are a TikTok trend analyst. Given hashtag/view data over 90 days for {product}: {tiktok_data}
1. Classify the trend stage: Rising/Peaking/Declining
2. Assess whether this virality looks commerce-driven (unboxings, demos, "link in bio") vs. pure entertainment/novelty with no purchase intent signal
3. Flag if this appears to be an early-mover opportunity ahead of paid ad saturation
```

**Scoring**: 0–100, weighted toward "commerce-intent virality" over raw view count (a dance trend ≠ a product demand signal).

**Possible Improvements**: Creator outreach cost estimator (organic seeding budget needed to replicate trend).

**Edge Cases**: Trend driven by a single mega-creator (fragile, may not be replicable) vs. broad-based organic adoption (durable) — must be distinguished explicitly.

**Failure Cases**: TikTok data access limited/blocked → system relies on Google Trends as a secondary proxy and lowers confidence rating accordingly.

---

### 15. AMAZON REVIEW ANALYSIS

**Purpose**: Ground-truth product quality and real customer language — the best antidote to being fooled by a good ad for a bad product.

**Inputs**: Amazon listing(s) matching the product, review text corpus, star distribution, Q&A section.

**Outputs**: `ReviewAnalysis{ avg_rating, review_volume, sentiment_breakdown, top_complaints[], top_praises[], quality_risk_flags[] }`

**Logic**:
1. Scrape reviews (aim for 100+ sample where available).
2. NLP-cluster complaints (e.g., "breaks after 2 weeks," "doesn't match photos," "sizing is off") and praises separately.
3. Flag any complaint cluster that indicates a structural product defect vs. a marketing/expectation-mismatch issue (the former is far more dangerous for a paid-ads business — high return/refund/chargeback risk).

**Decision Rules**: Avg rating < 3.5 with recurring defect complaints → strong negative flag, pulls score down significantly regardless of other pillars' strength (bad product will burn ad spend on returns/chargebacks). Avg rating > 4.2 with volume > 200 → strong positive signal.

**AI Prompt Core**:
```
You are a product-quality analyst mining Amazon reviews. Given this review corpus for {product}: {review_data}
1. Summarize the top 3 complaint themes and top 3 praise themes, each with representative (paraphrased, not quoted verbatim) examples
2. Classify whether complaints are structural defects (breaks, doesn't work) vs. expectation-mismatch (sizing, color) — the former is a much bigger red flag
3. Give an overall quality-risk rating: Low/Medium/High
```

**Scoring**: 0–100, weighted heavily toward absence of structural-defect complaints; volume and rating are secondary modifiers.

**Possible Improvements**: Track review velocity over time (accelerating negative reviews = quality is degrading, e.g. factory changed materials).

**Edge Cases**: No matching Amazon listing exists (TikTok/Shopify-exclusive product) → fall back to Trustpilot/store reviews/Reddit mentions, explicitly noted as a secondary source.

**Failure Cases**: Reviews clearly manipulated/incentivized (unnatural 5-star clustering with generic text) → system flags "Review Authenticity Concern" rather than trusting the score at face value.

---

### 16. CUSTOMER PSYCHOLOGY ANALYSIS

**Purpose**: Understand the emotional/psychological driver behind why someone buys this — the foundation of every good ad angle and offer decision.

**Inputs**: Reviews (why people bought it, in their own words), ad hooks (from FB module), Reddit/forum language, category psychology heuristics (`consumer_behavior.md`, `psychology.md`).

**Outputs**: `PsychologyResult{ core_pain_point, core_desire, buyer_persona, purchase_trigger_type (impulse/considered/gift/status), emotional_hooks[] }`

**Logic**: Extract recurring language patterns from reviews/forums that reveal the *real* reason for purchase (often different from the marketed reason — e.g., a posture-corrector product is often bought for pain relief, not "better posture" per se). Classify against a known taxonomy of purchase triggers.

**Decision Rules**: Strong, singular, clearly-articulated pain point across many independent sources = high score (easy to build ad angles around). Vague/fragmented reasons for purchase (everyone buys it for a different, weak reason) = lower score (harder to build a resonant ad).

**AI Prompt Core**:
```
You are a consumer psychology analyst. Given customer language from reviews and forums about {product}: {language_corpus}
1. Identify the single strongest, most recurring pain point or desire driving purchase (in the customer's own words/paraphrase)
2. Classify the purchase trigger: impulse, considered, gift-giving, or status/identity
3. Note if there are multiple distinct buyer personas with different motivations (this affects how many creative angles are viable)
```

**Scoring**: 0–100 based on clarity/strength/consistency of the core pain point identified across sources.

**Possible Improvements**: Sentiment-over-time tracking to detect if the core pain point is durable or was a passing cultural moment.

**Edge Cases**: Product with genuinely multiple distinct use-cases/personas (e.g., a gadget bought both as a gift and for personal use) — should be scored as a positive (more creative angles) not treated as "unclear positioning."

**Failure Cases**: Insufficient customer language data (new/low-review product) → psychology output marked "Hypothesized, Unvalidated" and downstream Creative Opportunity confidence is lowered accordingly.

---

### 17. CREATIVE OPPORTUNITY ANALYSIS

**Purpose**: Determine how many genuinely different, resonant ad angles can be built — directly predicts how long a test/scale can run before creative fatigue kills it.

**Inputs**: Psychology output (pain points/personas), FB Ads angle clusters (what's already been done), creative-rules knowledge base.

**Outputs**: `CreativeOpportunity{ viable_angles[], angle_saturation_map, recommended_first_test_angles[3-5], fatigue_risk_level }`

**Logic**: Cross-reference the identified pain points/personas against what competitors are ALREADY running (from FB Ads module) to find angles that are valid but underused — the "gap" the user can own first.

**Decision Rules**: <2 viable distinct angles = Hard Veto trigger (Section 2.3) — too fragile a test. 2–3 angles = Conditional, flagged "narrow creative runway, monitor fatigue closely." 4+ = strong score.

**AI Prompt Core**:
```
You are a creative strategist. Given: identified pain points/personas {psychology_data}, and angles competitors are already using {fb_ads_angles}
1. List all genuinely distinct angles this product could support (not just tone variations of the same angle)
2. Mark which are already crowded vs. underused/open
3. Recommend the 3-5 angles to test first, prioritizing underused ones with strong psychology backing
```

**Scoring**: 0–100, primarily driven by count of viable + underused angles.

**Possible Improvements**: Auto-generate rough ad script/hook drafts for each recommended angle as a starting point (not full creative production, just strategic scaffolding).

**Edge Cases**: A product with only one true angle but where that angle is completely unclaimed by competitors — still risky long-term (fatigue) but may warrant a "GO WITH CONDITIONS: fast burn, plan short test window" rather than outright NO-GO.

**Failure Cases**: All existing angles found are near-identical → system explicitly states "no clear differentiation angle identified" rather than fabricating a forced one.

---

### 18. RISK ANALYSIS

**Purpose**: Catch everything that isn't captured by demand/economics/competition scores but could still kill the test or the business.

**Inputs**: All prior module outputs, supplier data, seasonality calendar, compliance flags, category legal-risk knowledge base.

**Outputs**: `RiskResult{ supplier_risk, seasonality_risk, platform_policy_risk, legal_risk, reputational_risk, overall_risk_level }`

**Logic**: Systematic checklist review:
- **Supplier risk**: single-source supplier, long shipping times, MOQ lock-in, quality-consistency history.
- **Seasonality risk**: is demand structurally tied to a season/holiday (higher risk of a short window, needs to be timed correctly)?
- **Platform policy risk**: category prone to ad account bans or disapprovals even if not outright prohibited (e.g., "before/after" claims).
- **Legal risk**: patents, trademarks, safety certifications required (e.g., CE/FCC for electronics).
- **Reputational risk**: product with high complaint rate that could damage a broader store brand if bundled with other SKUs.

**Decision Rules**: Any single risk category rated "Severe" contributes to hard veto review even if not an automatic veto on its own; multiple "Moderate" risks stack additively into the Risk pillar score.

**AI Prompt Core**:
```
You are a risk analyst reviewing a product for a paid-ads eCommerce test. Given all findings: {aggregated_module_data}
1. Rate each risk category (Supplier/Seasonality/Platform Policy/Legal/Reputational) as Low/Moderate/Severe with one-line reasoning
2. Identify the single biggest risk factor overall
3. Recommend a specific mitigation if one exists (e.g., "source from 2 backup suppliers before scaling")
```

**Scoring**: 0–100, inversely proportional to aggregated risk severity.

**Possible Improvements**: Automated supplier-diversity checker (cross-reference multiple supplier platforms for the same product to avoid single-source dependency).

**Edge Cases**: Seasonal product analyzed outside its season — system must flag "off-season analysis, re-test 60 days before peak season" rather than penalizing it as permanently low-demand.

**Failure Cases**: Legal/certification requirements vary by target country and data is incomplete — system defaults to flagging "Requires Legal Verification for [target market]" rather than assuming compliance.

---

### 19. PRODUCT FINAL DECISION (Investment Memo)

**Purpose**: The human-facing synthesis — a senior-analyst-toned memo, not a dashboard of numbers.

**Inputs**: Full ScoreCard (Section 8), all module outputs and their citations, Validation Agent's contradiction-check notes.

**Outputs**: A structured memo:
```
1. VERDICT (GO / CONDITIONAL / NO-GO) + Confidence Level
2. One-paragraph executive summary (the "why" in plain language)
3. Pillar-by-pillar breakdown with score + 2-3 line justification each
4. Named risks / conditions (if any)
5. If GO: recommended test budget, creative angles to start with, target CPA ceiling
6. If NO-GO: the specific pillar(s)/veto that failed, and what would need to change for reconsideration
```

**Logic**: Chief Analyst Agent synthesizes all validated data into the above structure — explicitly instructed to write like a skeptical human analyst, not a sales pitch for the product.

**Decision Rules**: Memo tone/content must always match the ScoreCard verdict exactly — the Synthesizer Agent is not permitted to override or soften the deterministic scoring engine's verdict; it can only explain and contextualize it.

**AI Prompt Core**:
```
You are a senior eCommerce investment analyst writing a decision memo for a founder about to risk real ad budget.
You have been given a full validated data package: {all_module_outputs_and_scorecard}
Write the memo in the exact structure specified: Verdict, Executive Summary, Pillar Breakdown, Risks/Conditions, Recommendation.
Be direct. If this is a bad investment, say so clearly and explain why, citing the specific evidence.
Do not inflate confidence beyond what the data supports. Do not use hype language ("amazing," "huge winner").
```

**Scoring**: N/A — presentation layer only, must faithfully reflect the Scoring Engine's output.

**Possible Improvements**: Auto-generate a one-page PDF version and a Notion/Airtable export for the user's own tracking system.

**Edge Cases**: Borderline score (e.g., 74/75) — memo should explicitly note "this sits right at the GO/CONDITIONAL boundary" rather than presenting false precision.

**Failure Cases**: Any module returned "Insufficient Data" — memo must surface this prominently at the top, not bury it, since it directly affects how much to trust the verdict.

---

## 20. PROJECT FOLDER STRUCTURE

```
/docs
    /architecture           → this document, module specs, decision framework docs
    /changelog              → versioned notes on scoring/weight changes over time
    /onboarding              → how a new dev/analyst understands the system

/knowledge                  → the Knowledge System (see Section 21) — markdown KB files, RAG-indexed
    /market/
    /economics/
    /advertising/
    /psychology/
    /risk/
    /_manifests/            → per-agent "which files can this agent retrieve" config

/prompts                    → all agent system prompts, versioned as .md or .txt, one file per agent
    /discovery/
    /validation/
    /analysis/              → one subfolder per domain agent (fb_ads, tiktok, pricing, etc.)
    /scoring/
    /synthesizer/

/agents                     → agent orchestration configs (which model, which tools, which knowledge manifest, memory settings)
    /discovery_agent.yaml
    /validation_agent.yaml
    /analysis/*.yaml         → one config per domain agent
    /chief_analyst_agent.yaml

/workflows                  → the pipeline orchestration definitions (sequence, parallelization, retries, fallbacks)
    /full_analysis_workflow.yaml
    /quick_scan_workflow.yaml   → lighter-weight version for shortlisting many products fast
    /error_handling.yaml

/database                   → schema + migrations for storing products, scores, reports, historical runs
    /schema/
    /migrations/

/backend                    → API layer, agent orchestration runtime, integrations with data sources
    /api/
    /integrations/          → FB Ad Library, TikTok, Amazon, supplier APIs, etc.
    /services/

/frontend                   → the dashboard/report UI
    /components/
    /pages/
    /report-viewer/         → renders the Investment Memo output

/scoring                    → the deterministic Scoring Engine code (Section 8) — kept separate from LLM logic deliberately
    /pillar_calculators/
    /veto_rules/
    /weights_config/

/reports                    → generated report artifacts (JSON + rendered PDF/Markdown) per product run, historical archive

/tests
    /agent_prompt_tests/     → golden-set test cases per agent (known products with expected verdicts)
    /scoring_tests/          → unit tests on the scoring math
    /integration_tests/      → full pipeline end-to-end tests
    /regression_tests/       → catches score drift after knowledge base or prompt updates
```

---

## 21. KNOWLEDGE BASE — FILE-BY-FILE SPEC

Located under `/knowledge/`, grouped by domain. Each file below should be written as explicit, numbered heuristics/thresholds — not prose essays — so agents can retrieve and apply them directly.

### `/knowledge/market/`
- **`winning_products.md`** — Documented historical patterns of what made past products succeed (category, price tier, angle, timing), used as pattern-matching reference by the Discovery and Scoring agents.
- **`market_saturation.md`** — Thresholds for advertiser counts per market stage (Emerging/Growing/Peak/Declining), how to detect differentiation gaps.
- **`seasonality_calendar.md`** — Category-by-category seasonal demand windows (e.g., fitness = Jan, gifts = Nov-Dec) used by the Risk module.
- **`niche_taxonomy.md`** — Standardized category/subcategory tree so all agents classify products consistently.

### `/knowledge/economics/`
- **`pricing.md`** — Category-specific markup heuristics, price-elasticity notes, bundle-pricing patterns.
- **`margin_benchmarks.md`** — Default CPA benchmarks and return-rate benchmarks per category, used when live data is unavailable.
- **`shipping_and_fees.md`** — Standard shipping cost tiers by geo/weight class, payment processor fee assumptions, duty/tax rules by region.

### `/knowledge/advertising/`
- **`facebook_ads.md`** — Signal interpretation rules (what a long ad run duration means, how to read engagement proxies), Ad Library query patterns.
- **`tiktok_trends.md`** — How to distinguish commerce-intent virality from entertainment virality; hashtag velocity thresholds.
- **`marketing_angles.md`** — Taxonomy of proven angle types (pain-relief, transformation, gift, status, convenience, novelty) with examples.
- **`creative_rules.md`** — What makes an ad angle "genuinely distinct" vs. a tone variation; fatigue-risk indicators.

### `/knowledge/psychology/`
- **`psychology.md`** — Core behavioral-psychology principles applied to purchase decisions (loss aversion, social proof, urgency, identity signaling).
- **`consumer_behavior.md`** — Purchase-trigger taxonomy (impulse/considered/gift/status) and how to detect each from customer language.
- **`review_language_patterns.md`** — Common linguistic markers that distinguish structural product complaints from expectation-mismatch complaints.

### `/knowledge/risk/`
- **`compliance_blocklist.md`** — Living list of prohibited/restricted categories per platform (Meta, TikTok) and per major target geo.
- **`supplier_risk_patterns.md`** — Red flags in supplier data (single-source dependency, MOQ traps, historically inconsistent quality).
- **`legal_certification_requirements.md`** — Category-specific certification needs by region (CE, FCC, health-claim restrictions, etc.).

### `/knowledge/scoring/`
- **`product_scoring.md`** — The full documented scoring framework (mirrors Section 2 of this doc) as the canonical reference the Scoring Engine and Synthesizer Agent are grounded against.
- **`competitor_analysis.md`** — How to weigh competitor scale signals, what constitutes a "mature funnel," how to identify exploitable gaps.

### `/knowledge/_manifests/`
- One YAML/markdown file per agent listing exactly which KB files that agent is permitted to retrieve — this is what keeps each agent's context narrow and its expertise sharp (see Section 4.3).

---

## 22. AI AGENT ROSTER — FULL SPECIFICATIONS

### 22.1 Discovery Agent
- **Role**: Product identification and normalization.
- **Responsibility**: Convert raw input into a validated `ProductIdentity` object; run niche-shortlist discovery when given an open-ended category query.
- **Inputs**: Raw text/URL/image + optional filters.
- **Outputs**: `ProductIdentity` object(s).
- **Tools**: Web scraper, reverse image search, vision model call.
- **Prompt**: See Section 6.
- **Memory**: Stateless per run; caches recent identity lookups for 24h to avoid duplicate scraping.
- **Workflow position**: Pipeline stage 1, always runs first, blocking.

### 22.2 Validation Agent (Pre-Analysis Gate)
- **Role**: Compliance/policy/supply gatekeeper.
- **Responsibility**: Stop clearly non-viable products before expensive analysis runs.
- **Inputs**: `ProductIdentity`.
- **Outputs**: `ValidationResult`.
- **Tools**: Policy-matching against `compliance_blocklist.md`, supplier API lookups.
- **Prompt**: See Section 7.
- **Memory**: None required; deterministic policy lookup preferred over LLM judgment where possible, LLM used only for ambiguous/gray-area cases.
- **Workflow position**: Stage 1.5, blocking — hard stop on Fail.

### 22.3 Market Saturation Agent
- Role/Responsibility/Inputs/Outputs/Tools/Prompt/Scoring: see Section 9.
- **Memory**: Stores last 3 runs per product-category for trend comparison across time (has saturation increased since last checked?).
- **Workflow position**: Stage 2, parallel.

### 22.4 Competitor Analysis Agent
- See Section 10. **Memory**: Maintains a rolling competitor-profile cache per niche to avoid re-scraping unchanged storefronts within 7 days. **Workflow**: Stage 2, parallel, consumes Saturation Agent's advertiser list as input.

### 22.5 Pricing Analysis Agent
- See Section 11. **Memory**: None beyond current run. **Workflow**: Stage 2, parallel, consumes Competitor Agent output.

### 22.6 Margin Analysis Agent
- See Section 12. **Memory**: None beyond current run; pulls category benchmarks from KB each time (benchmarks update independently). **Workflow**: Stage 2, parallel, consumes Pricing + FB Ads Agent outputs (needs CPA estimate).

### 22.7 Facebook Ads Analysis Agent
- See Section 13. **Memory**: Caches ad-library pulls per product for 48h (ad libraries don't change minute-to-minute). **Workflow**: Stage 2, parallel — high priority, since several other agents depend on its output (Margin, Creative Opportunity).

### 22.8 TikTok Trend Agent
- See Section 14. **Memory**: Stores trend-velocity history per product/hashtag for durability tracking across repeated runs. **Workflow**: Stage 2, parallel.

### 22.9 Amazon Review Mining Agent
- See Section 15. **Memory**: Caches scraped review corpora per ASIN for 7 days. **Workflow**: Stage 2, parallel.

### 22.10 Customer Psychology Agent
- See Section 16. **Memory**: None beyond current run. **Workflow**: Stage 2, parallel, consumes Review Mining Agent output + FB Ads hooks.

### 22.11 Creative Opportunity Agent
- See Section 17. **Memory**: None beyond current run. **Workflow**: Stage 2 (late), consumes Psychology Agent + FB Ads Agent outputs — runs after those two complete.

### 22.12 Risk Analysis Agent
- See Section 18. **Memory**: None beyond current run. **Workflow**: Stage 2 (late), consumes nearly all other module outputs as context.

### 22.13 Validation Agent (Post-Analysis Cross-Check)
- **Role**: Anti-hallucination/contradiction auditor (distinct from the pre-analysis gatekeeper in 22.2, despite similar name — consider renaming to `contradiction_auditor_agent` to avoid confusion).
- **Responsibility**: See Section 3.3.
- **Inputs**: All 10 domain agent outputs.
- **Outputs**: `AuditNotes{ contradictions[], uncited_claims[], confidence_adjustments[] }`.
- **Tools**: None beyond LLM reasoning over structured JSON inputs.
- **Memory**: None.
- **Workflow position**: Stage 3, blocking (must complete before Scoring Engine runs).

### 22.14 Scoring Engine (Deterministic — Not an LLM Agent)
- See Section 8. Implemented as code, not a prompt. Listed here for completeness of pipeline ownership.

### 22.15 Chief Analyst / Synthesizer Agent
- See Section 19. **Memory**: Given full run history for the product if this is a re-analysis (e.g., "saturation has increased since last week" callouts). **Workflow**: Stage 5, final, blocking — produces the user-facing report.

---

## Closing Note on Build Priority

Recommended build order for an engineering team: (1) Discovery + Validation gates, (2) Scoring Engine math (deterministic, testable independently of any LLM), (3) Facebook Ads + Amazon Review agents first (highest signal-to-effort ratio), (4) remaining domain agents, (5) Contradiction Auditor + Synthesizer last, once there's real data flowing to validate against.

This also happens to be a strong structure for a **Fiverr/productized-service offer**: even a partial build (Discovery + FB Ads + Margin + Scoring Engine) is a sellable "Product Validation Report" service on its own, before the full 10-agent system is complete.
