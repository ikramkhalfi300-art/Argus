# Seasonality Calendar — Category-by-Category Demand Windows

> This file documents seasonal demand windows by category for use by the Risk Analysis Agent
> (per Architecture Section 18 — seasonality risk assessment), the Discovery Agent (timing-aware
> product evaluation), and the Seasonality Calendar fallback in the Scoring Engine.
>
> Windows are based on general industry knowledge of seasonal eCommerce patterns (calendar-driven
> events, holiday shopping cycles, weather-driven demand). These are common-knowledge ranges, not
> project-derived measurements from Google Trends or ad-spend data. Exact peaks vary by geo and year.
> Peak window = the period when demand is typically highest. Pre-season = when early-buyer intent
> begins to rise. Post-season = when demand typically drops after the peak.

**last_updated**: 2026-07-09

**Changelog**:
- 2026-07-09: Initial version — 15 category groups with seasonal windows, timing rules, and edge cases.

---

## Category Group A: Fitness & Wellness

| Subcategory | Pre-Season | Peak Window | Post-Season | Notes |
|---|---|---|---|---|
| Home gym equipment, resistance bands, weights | Dec 26–Jan 1 | Jan 1–Feb 15 | Feb 15–Mar 15 | New Year resolution peak; begins rising Dec 26, drops sharply after Feb 15 |
| Posture correctors, ergonomic accessories | Jan 1–Jan 15 | Jan 15–Mar 1 | Mar 1–Apr 1 | More gradual build than gym equipment; extends into March |
| Massage guns, foam rollers, recovery tools | Late Dec | Jan 1–Feb 15 | Feb 15–Mar 15 | Tracks resolution peak closely |
| Yoga mats, Pilates accessories | Jan 1 | Jan 15–Mar 1 | Mar 1–Apr 1 | Extends slightly longer than gym equipment — lower-intensity resolution goal |
| Weighted blankets, sleep aids | Oct | Nov–Jan | Feb | Dual season: holiday gifts (Nov-Dec) + wellness (Jan) |

**Annual off-season low**: Jun–Oct for most categories except travel-mini massage tools (peak May–Jul).

---

## Category Group B: Travel & Summer

| Subcategory | Pre-Season | Peak Window | Post-Season | Notes |
|---|---|---|---|---|
| Travel organizers, packing cubes | Apr 15–May 1 | May 1–Jun 30 | Jul 15–Aug 1 | Peak is pre-summer travel; drops once people have already traveled |
| Luggage, carry-on bags | Mar–Apr | Apr–Jun | Jul | Longer pre-season — luggage is a considered purchase, not impulse |
| Sun protection, UV accessories | Apr 15 | May 15–Jul 31 | Aug 15 | Extends through late summer |
| Portable fans, cooling gear | May | Jun–Aug | Sep | Hot-weather driven, varies by geo |
| Car organizers, road trip accessories | Apr | May–Aug | Sep | Longer peak due to road trip season spread across months |
| Beach/pool accessories | May 1 | Jun–Jul 31 | Aug 15 | Clear summer peak; very low demand Oct–Mar |

---

## Category Group C: Back-to-School & Office

| Subcategory | Pre-Season | Peak Window | Post-Season | Notes |
|---|---|---|---|---|
| Desk organizers, study accessories | Jul 1–Jul 31 | Aug 1–Sep 15 | Sep 15–Oct 1 | Broad BTS window; exact timing varies by region (US: Aug peak, EU: Sep) |
| Lunch containers, bento boxes | Jul 15 | Aug 1–Sep 15 | Sep 15–Oct 1 | Tracks BTS timing |
| Backpack accessories, laptop sleeves | Jul 1 | Jul 15–Sep 1 | Sep 1–Oct 1 | Slightly earlier peak than desk organizers |
| Home office ergonomics (standing desk converters, monitor arms) | Aug | Sep–Oct | Nov | Extends past BTS into general office upgrade season |

---

## Category Group D: Holiday & Gift (Highest Volume)

| Subcategory | Pre-Season | Peak Window | Post-Season | Notes |
|---|---|---|---|---|
| Novelty/gag gifts | Oct 1 | Nov 1–Dec 15 | Dec 26 | Long pre-season from early ad buyers |
| Personalized/gift items | Oct 15 | Nov 15–Dec 10 | Dec 20 | Shorter window; production time matters for personalization |
| Stocking stuffers (sub-$15) | Nov 1 | Nov 15–Dec 20 | Dec 26 | Compressed peak, high volume |
| Home/decor (holiday-specific) | Oct 15 | Nov 1–Dec 15 | Jan 1–Jan 15 | Long window; some demand extends into post-holiday markdowns |
| Gift sets, curated boxes | Oct 15 | Nov 15–Dec 15 | Dec 20 | Peak is last 4 weeks before Christmas |
| Advent calendars | Sep | Oct–Nov | Dec 1 | Production + shipping timeline critical; must be in-stock by Oct |

**Annual off-season low**: Jan–Sep for holiday-specific items. Some decor products have a secondary mini-peak (Easter, Valentine's) — see Category Group E.

---

## Category Group E: Event-Driven (Valentine's, Mother's Day, etc.)

| Subcategory | Pre-Season | Peak Window | Post-Season | Notes |
|---|---|---|---|---|
| Valentine's gifts (jewelry, romantic items) | Jan 20 | Feb 1–Feb 12 | Feb 14 | Compressed peak; shipping cutoff matters |
| Mother's Day gifts (general) | Apr 15 | Apr 25–May 8 | May 10 | US/Canada: 2nd Sunday in May; UK: Mothering Sunday in March |
| Father's Day gifts | May 15 | Jun 1–Jun 15 | Jun 18 | US: 3rd Sunday in June |
| Halloween costumes, decor | Sep 1 | Sep 15–Oct 25 | Nov 1 | Long peak; decor extends longer than costumes |
| Easter baskets, spring decor | Feb 15 | Mar 1–Mar 31 | Apr 1 | Exact timing varies annually |

---

## Category Group F: Weather-Driven

| Subcategory | Pre-Season | Peak Window | Post-Season | Notes |
|---|---|---|---|---|
| Winter gear (hand warmers, heated items, snow accessories) | Oct | Nov–Jan | Feb | Driven by weather, not calendar; can extend if cold persists |
| Rain/umbrella accessories | Year-round | Regional | Regional | Weather-dependent, not calendar-driven — harder to plan |
| Allergy relief (air purifiers, HEPA filters) | Feb | Mar–May | Jun | Spring allergy season; varies by region |
| Pest control, bug repellent | Mar | Apr–Aug | Sep | Warm-weather driven; extends longer in warmer climates |

---

## Category Group G: Home & Kitchen

| Subcategory | Pre-Season | Peak Window | Post-Season | Notes |
|---|---|---|---|---|
| Kitchen gadgets (general) | Nov (holiday boost) | Nov–Dec (gift season) | Jan | Moderate seasonality — year-round baseline demand, Nov-Dec spike |
| Baking tools | Oct | Nov–Dec | Jan | Holiday baking peak; minimal seasonality rest of year |
| Grill/smoker accessories | Mar | Apr–Jul | Aug–Sep | Spring grilling season; varies by climate region |
| Home organization, storage | Jan (resolution) + Sep (fall reset) | Jan + Sep | Feb + Oct | Bimodal pattern; less seasonal than category-driven |
| Air fryer accessories | Nov (holiday) | Nov–Dec | Jan | Tracks kitchen-gadget gift buying patterns |

---

## Rule 1: Off-Season Analysis Flagging

If a product is analyzed outside its peak window (more than 4 months from the start of the pre-season), the Risk Analysis Agent must flag the report as "Off-Season Analysis — Re-test Near Peak Window for Accurate Demand Assessment."

Per Architecture Section 18 (edge case): "Seasonal product analyzed outside its season — system must flag 'off-season analysis, re-test 60 days before peak season' rather than penalizing it as permanently low-demand."

**Implementation note for Risk Agent**: This flag is informational, not a score penalty. The demand-strength pillar still scores based on available ad data, but the final report surfaces the timing caveat prominently.

---

## Rule 2: Multi-Season Products

Some products span multiple seasonal windows (e.g., a travel organizer that peaks in May for summer but also sells in Nov for holiday travel). For these:

1. If the product is within 3 months of ANY seasonal peak, score using the nearest peak's demand data
2. If the product is more than 3 months from ALL seasonal peaks, apply the Off-Season flag (Rule 1)
3. If the product has no identifiable seasonality (year-round baseline), skip seasonal flagging entirely

**Products with year-round baseline demand** (low seasonality): Pet accessories, phone accessories, basic kitchen tools, cleaning products, general home goods. These should not be flagged for seasonality unless the specific subcategory tracks an event.
