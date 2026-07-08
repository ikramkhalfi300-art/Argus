# AI Product Research & Decision Intelligence Platform
## Implementation Roadmap — Engineering Execution Manual for OpenCode

*This document assumes the architecture in `AI_Product_Research_Platform_Architecture.md` is final and approved. Nothing here changes scoring logic, agent roles, folder structure, or the knowledge base design. This is execution planning only.*

---

## HOW TO READ THIS DOCUMENT

- **Phase** = a major capability milestone (weeks).
- **Milestone** = a coherent sub-system within a phase.
- **Sprint** = one unit of work, sized so an AI coding agent can complete it in a single implementation cycle without needing anything not yet built.
- **Review Gate** = mandatory human/senior-review checkpoint after every sprint. No sprint N+1 work begins until Sprint N's Review Gate passes.
- Sprints are ordered so **nothing depends on unbuilt code**. Where a sprint depends on a prior one, it is stated explicitly under "Dependencies."

---

# PART A — CRITICAL PATH & PARALLELIZATION MAP

### Critical Path (cannot be parallelized, blocks everything downstream)
```
Repo/Env Setup → DB Schema → Agent Output Contract → Scoring Engine Core
→ Discovery Agent → Validation Gate → FB Ads Agent → Margin Agent
→ Orchestration Engine → Contradiction Auditor → Synthesizer Agent → E2E Pipeline Test
```

### Parallelizable Work (can be built simultaneously by separate workstreams once their inputs exist)
- Once **Agent Output Contract** (Sprint 2.1.1) is done: all 10 domain agents can be developed in parallel by different workstreams, since each only needs the contract + its own KB files + its own data integration.
- **Knowledge Base authoring** (Phase 3) can run fully in parallel with Phase 2 (Scoring Engine) — different skillset, no code dependency.
- **Frontend** (Phase 7) can begin as soon as the Database schema (Sprint 0.1.2) and Report JSON shape (Sprint 6.1.3) are stable — it can be stubbed against mock report JSON well before agents are complete.
- **Data source integrations** (FB Ad Library, Amazon, TikTok, Supplier APIs) are independent of each other and can be built in parallel by different people/cycles.

### High-Risk Components
1. **Amazon scraping reliability** — most likely to break due to anti-bot measures; needs fallback/caching strategy from day one.
2. **FB Ad Library data completeness by geo** — historically inconsistent regional coverage; must be surfaced as a confidence flag, not silently ignored.
3. **Contradiction Auditor Agent** — the least "deterministic" piece of the anti-hallucination system; highest chance of false-positive/false-negative contradiction flags. Needs the largest test golden-set.
4. **Scoring Engine weight calibration** — weights are opinions until backtested against real historical winners/losers; treat initial weights as v0.1, expect recalibration.
5. **Margin Agent's dependency on CPA estimates** — CPA benchmarks decay over time as ad platforms change; must never be hardcoded without a "last updated" freshness check.

### Technical Debt Risks
- Building agent-specific scraping/caching logic ad hoc instead of a shared `integrations/` service layer → duplicate, inconsistent caching TTLs. **Mitigation: Sprint 4.1.x establishes a shared integration service pattern before any agent-specific scraping is written.**
- Skipping the Agent Output Contract and letting each agent return free-form JSON → breaks the Scoring Engine and Contradiction Auditor later. **Mitigation: Contract is Sprint 2.1.1, before any domain agent is built.**
- Treating Knowledge Base files as static after initial authoring → scoring drift as ad platforms/markets change without anyone noticing. **Mitigation: `last_updated` metadata + regression test suite (Phase 8) flags KB staleness.**

### Future Scalability Considerations
- Agent orchestration should be built on a workflow engine (queue-based, not a single synchronous script) from Sprint 6.1.1 onward, so adding agent #11, #12 later doesn't require re-architecture.
- Database schema should version each `report` as immutable (never overwrite a past run) to support backtesting and re-analysis comparison (per Section 22.15's "has saturation increased since last week" feature).
- Knowledge Base retrieval should be abstracted behind an interface (e.g., a `KnowledgeRetriever` service) so the underlying RAG/embedding implementation can be swapped without touching agent code.

---

# PART B — PHASE, MILESTONE & SPRINT BREAKDOWN

---

## PHASE 0 — FOUNDATION

### Milestone 0.1 — Environment, Repo & Data Layer Bootstrap

---

#### Sprint 0.1.1 — Repository & Folder Scaffolding

**Goal**: Create the full project skeleton exactly matching the approved architecture's folder structure, with no functional code yet.

**Why this sprint exists**: Every future sprint needs a stable, agreed folder location to write into. Doing this first avoids restructuring later.

**Dependencies**: None (first sprint).

**Files to create**: Empty/placeholder folders and `README.md` per top-level folder (`/docs`, `/knowledge`, `/prompts`, `/agents`, `/workflows`, `/database`, `/backend`, `/frontend`, `/scoring`, `/reports`, `/tests`), root `.env.example`, `.gitignore`, root `README.md` describing the project and linking to the architecture doc.

**Folder structure involved**: All top-level folders from Architecture Section 20.

**APIs**: None yet.

**Database changes**: None yet.

**Backend tasks**: Initialize backend project (language/framework choice locked in here — recommend Python for agent/AI-heavy backend + FastAPI, given ecosystem fit for LLM orchestration and existing familiarity). Set up dependency management file.

**Frontend tasks**: Initialize frontend project skeleton (React-based, matching stack conventions), no pages yet beyond a placeholder landing route.

**AI Agent tasks**: None yet — `/agents` and `/prompts` folders created empty with subfolder placeholders per Architecture Section 20/22.

**Knowledge Base tasks**: Create `/knowledge` subfolders (`market/`, `economics/`, `advertising/`, `psychology/`, `risk/`, `scoring/`, `_manifests/`) empty.

**Tests to write**: A single smoke test confirming backend boots and frontend builds successfully.

**Acceptance Criteria**: Repo clones fresh, backend starts with a health-check endpoint (`GET /health` returns 200), frontend builds and serves a placeholder page.

**Definition of Done**: Folder structure matches Architecture Section 20 exactly; smoke tests pass in CI.

**Estimated complexity**: Low.

**Common mistakes to avoid**: Do not add any business logic yet. Do not skip creating empty folders for later phases (e.g., `/reports`) — future sprints assume they exist.

**What must be reviewed before moving forward**: Folder structure sign-off against the architecture doc (line-by-line diff check by the human reviewer).

> ### ✅ REVIEW GATE 0.1.1
> Reviewer confirms: folder structure matches architecture exactly, health-check passes, no premature business logic present. **Sprint 0.1.2 cannot start until this is signed off.**

---

#### Sprint 0.1.2 — Database Schema (Core Tables)

**Goal**: Stand up the database with core tables needed by every later sprint: `products`, `runs`, `reports`, `agent_outputs`.

**Why this sprint exists**: All agents, scoring, and reporting need a persistence layer to write to and read from. Building this early avoids retrofitting schema changes later.

**Dependencies**: Sprint 0.1.1 (repo/backend skeleton).

**Files to create**: `/database/schema/001_core_tables.sql` (or ORM models equivalent), `/database/migrations/` initial migration, `/backend/services/db_service` connector module.

**Folder structure involved**: `/database/schema/`, `/database/migrations/`.

**APIs**: None public yet — internal DB connection module only.

**Database changes**:
- `products` table: `id, name, category, subcategory, normalized_keywords[], source_url, created_at`
- `runs` table: `id, product_id, status (pending/running/complete/failed), started_at, completed_at`
- `agent_outputs` table: `id, run_id, agent_name, output_json, confidence, created_at` — one row per agent per run
- `reports` table: `id, run_id, verdict, composite_score, memo_json, created_at` — immutable, one per completed run

**Backend tasks**: Implement DB connection/service layer; implement basic CRUD for each table (no business logic yet).

**Frontend tasks**: None this sprint.

**AI Agent tasks**: None this sprint.

**Knowledge Base tasks**: None this sprint.

**Tests to write**: CRUD unit tests for each table; migration up/down test.

**Acceptance Criteria**: Tables created via migration; CRUD operations verified via tests; `reports` table confirmed immutable (no update method exposed, only insert).

**Definition of Done**: All 4 core tables exist, migrations are reproducible from scratch, CRUD tests pass.

**Estimated complexity**: Low–Medium.

**Common mistakes to avoid**: Do not add agent-specific columns to `agent_outputs` (e.g., don't add a `saturation_score` column directly) — output must stay as generic JSON until the Agent Output Contract (Sprint 2.1.1) defines its shape, otherwise this table will need painful migrations later.

**What must be reviewed before moving forward**: Schema review against expected future needs (does `agent_outputs.output_json` structure anticipate the contract coming in Phase 2? Reviewer should sanity-check this is JSON/flexible, not rigid).

> ### ✅ REVIEW GATE 0.1.2
> Reviewer confirms: schema supports immutable reports, flexible agent_outputs JSON column, migrations are clean and reversible. **Sprint 0.1.3 cannot start until this is signed off.**

---

#### Sprint 0.1.3 — CI/CD & Test Harness Skeleton

**Goal**: Set up automated testing and deployment pipeline skeleton so every future sprint's tests run automatically.

**Why this sprint exists**: Without CI from the start, test discipline erodes as the project grows — this must exist before any real business logic is written.

**Dependencies**: Sprint 0.1.1, 0.1.2.

**Files to create**: CI config file (e.g., GitHub Actions workflow `.github/workflows/ci.yml`), `/tests/` subfolder skeletons (`agent_prompt_tests/`, `scoring_tests/`, `integration_tests/`, `regression_tests/`), a base test-runner config.

**Folder structure involved**: `/tests/*` per Architecture Section 20.

**APIs**: None.

**Database changes**: Add a test-database provisioning step in CI (isolated from dev/prod).

**Backend tasks**: Ensure backend test suite runs via a single command; wire into CI.

**Frontend tasks**: Ensure frontend build/test runs via a single command; wire into CI.

**AI Agent tasks**: None yet.

**Knowledge Base tasks**: None yet.

**Tests to write**: CI pipeline itself is the deliverable; include the smoke test from 0.1.1 and CRUD tests from 0.1.2 as the first real CI-run tests.

**Acceptance Criteria**: A pull request triggers CI; CI runs backend tests, frontend build, and reports pass/fail clearly.

**Definition of Done**: CI is green on the current main branch; branch protection rule requires CI pass before merge (see Part C, Git Strategy).

**Estimated complexity**: Low.

**Common mistakes to avoid**: Don't couple CI to production secrets/credentials — use test/mock credentials for all external API calls at this stage (no real integrations exist yet anyway).

**What must be reviewed before moving forward**: Confirm CI actually blocks merges on failure (test this by intentionally breaking a test in a throwaway branch).

> ### ✅ REVIEW GATE 0.1.3
> Reviewer confirms CI blocks bad merges, test folder structure is in place. **Phase 0 is now complete. Phase 1 may begin.**

---

## PHASE 1 — DISCOVERY & VALIDATION GATE (Pipeline Stage 1)

### Milestone 1.1 — Product Identity System

---

#### Sprint 1.1.1 — ProductIdentity Schema & Storage

**Goal**: Define and implement the `ProductIdentity` data contract exactly as specified in Architecture Section 6, and wire it to the `products` table.

**Why this sprint exists**: Every downstream agent consumes `ProductIdentity` — it must be locked down before any agent logic is written.

**Dependencies**: Sprint 0.1.2 (products table exists).

**Files to create**: `/backend/services/product_identity_service.py` (or equivalent), schema definition file (e.g., Pydantic model) shared across backend, `/database/migrations/002_product_identity_fields.sql` if the `products` table needs additional columns (`variants[]`, `detected_niche`, `image_refs[]`).

**Folder structure involved**: `/backend/services/`, `/database/migrations/`.

**APIs**: Internal service method `create_product_identity()`, `get_product_identity(id)` — not yet exposed via public API.

**Database changes**: Extend `products` table per Architecture Section 6's object shape if not already covered in Sprint 0.1.2.

**Backend tasks**: Implement identity object creation, validation (required fields present), and storage.

**Frontend tasks**: None this sprint.

**AI Agent tasks**: None yet — this is the data contract the Discovery Agent will populate in the next sprint.

**Knowledge Base tasks**: None this sprint.

**Tests to write**: Schema validation tests (reject incomplete identity objects); storage/retrieval round-trip test.

**Acceptance Criteria**: A `ProductIdentity` object matching Architecture Section 6's shape can be created, stored, and retrieved via the service layer.

**Definition of Done**: Schema matches spec exactly; tests pass in CI.

**Estimated complexity**: Low.

**Common mistakes to avoid**: Do not let this schema drift from what's documented in Architecture Section 6 — any field addition must be reflected back into the architecture doc as an addendum, not silently diverge.

**What must be reviewed before moving forward**: Field-by-field diff against Architecture Section 6.

> ### ✅ REVIEW GATE 1.1.1
> Reviewer confirms schema matches architecture exactly. **Sprint 1.1.2 cannot start until this is signed off.**

---

#### Sprint 1.1.2 — Discovery Agent (Text/URL Input Path)

**Goal**: Build the Discovery Agent's core path — given a product name or URL, produce a valid `ProductIdentity`.

**Why this sprint exists**: This is the pipeline's actual entry point; nothing else can be tested end-to-end without it. Image/vision path is deferred to the next sprint to keep this sprint small.

**Dependencies**: Sprint 1.1.1 (ProductIdentity contract).

**Files to create**: `/agents/discovery_agent.yaml` (agent config: model, tools, no image tool yet), `/prompts/discovery/discovery_agent_prompt.md` (prompt per Architecture Section 6, text/URL path only), `/backend/integrations/product_page_scraper.py`.

**Folder structure involved**: `/agents/`, `/prompts/discovery/`, `/backend/integrations/`.

**APIs**: `POST /api/discover` — accepts `{ input_type: "text"|"url", value: string }`, returns `ProductIdentity`.

**Database changes**: None beyond Sprint 1.1.1.

**Backend tasks**: Implement product-page scraper (title, price, images, description, variants); implement Discovery Agent LLM call wired to the scraped data for keyword/niche extraction; implement `/api/discover` endpoint.

**Frontend tasks**: None yet (API-only sprint).

**AI Agent tasks**: Implement Discovery Agent's LLM prompt exactly as documented in Architecture Section 6, restricted to text/URL inputs.

**Knowledge Base tasks**: None yet (Discovery Agent doesn't require KB retrieval per architecture).

**Tests to write**: Unit tests for scraper (mocked HTML fixtures); agent prompt golden-set test with 5–10 known products (text name + URL each) verifying reasonable category/keyword output; API endpoint integration test.

**Acceptance Criteria**: Given a real product URL, the endpoint returns a valid, populated `ProductIdentity` with plausible category/keywords. Given a bare product name, the same holds.

**Definition of Done**: All tests pass; manual spot-check of 5 real products confirms sane output.

**Estimated complexity**: Medium.

**Common mistakes to avoid**: Do not let the agent guess brand names it can't verify (explicit rule in the prompt, per architecture) — test this specifically with a golden-set case designed to tempt hallucination.

**What must be reviewed before moving forward**: Review actual LLM outputs against the golden set, not just that the code runs — a technically-working agent with bad outputs must fail this gate.

> ### ✅ REVIEW GATE 1.1.2
> Reviewer confirms golden-set outputs are qualitatively sound and hallucination-free. **Sprint 1.1.3 cannot start until this is signed off.**

---

#### Sprint 1.1.3 — Discovery Agent (Image Input + Niche-Shortlist Mode)

**Goal**: Extend Discovery Agent to accept image input (reverse image search + vision model) and open-ended niche queries (shortlist mode).

**Why this sprint exists**: Completes the Discovery Agent per full Architecture Section 6 spec; kept separate from 1.1.2 to keep each sprint small and independently testable.

**Dependencies**: Sprint 1.1.2.

**Files to create**: `/backend/integrations/reverse_image_search.py`, `/backend/integrations/vision_model_client.py`, update `/prompts/discovery/discovery_agent_prompt.md` with the niche-shortlist prompt variant.

**Folder structure involved**: `/backend/integrations/`.

**APIs**: Extend `POST /api/discover` to accept `{ input_type: "image", value: base64_or_url }` and `{ input_type: "niche_query", value: string, filters?: {} }` (returns array of `ProductIdentity` candidates for niche mode).

**Database changes**: None.

**Backend tasks**: Implement image ingestion + reverse-image-search integration; implement niche-shortlist path querying FB/TikTok ad libraries for candidate generation (may stub ad library calls with mocked data until Phase 4 integrations exist — see note below).

**Frontend tasks**: None yet.

**AI Agent tasks**: Extend Discovery Agent prompt/logic for image and niche-shortlist modes per Architecture Section 6.

**Knowledge Base tasks**: None.

**Tests to write**: Image-path golden-set test (5 product images); niche-shortlist test verifying it returns multiple distinct candidates, not duplicates.

**Acceptance Criteria**: Image input returns a valid `ProductIdentity`; niche query returns a deduplicated shortlist of plausible candidates.

**Definition of Done**: Tests pass; manual review of image + niche outputs for quality.

**Estimated complexity**: Medium–High (vision + reverse image search integration is the riskiest new piece here).

**Common mistakes to avoid**: Do not build a full FB/TikTok Ad Library integration just for this sprint — stub/mock it, since the real integration belongs to Phase 4 (Sprint 4.1.1). Building it early here creates duplicate, inconsistent integration code (a named tech debt risk in Part A).

**What must be reviewed before moving forward**: Confirm the niche-shortlist mock boundary is clearly marked (e.g., a TODO/config flag) so Phase 4 knows to replace it, not build alongside it.

> ### ✅ REVIEW GATE 1.1.3
> Reviewer confirms image path works, niche-shortlist mock boundary is clearly flagged for future replacement. **Milestone 1.1 complete. Milestone 1.2 may begin.**

---

### Milestone 1.2 — Validation Gate

---

#### Sprint 1.2.1 — Compliance Blocklist (Deterministic Check)

**Goal**: Build the deterministic (non-LLM) portion of the Validation Gate: matching a `ProductIdentity` against the compliance blocklist.

**Why this sprint exists**: Deterministic checks are cheaper, faster, and more reliable than LLM judgment for known-clear cases; only ambiguous cases should reach the LLM (next sprint).

**Dependencies**: Sprint 1.1.1 (ProductIdentity).

**Files to create**: `/knowledge/risk/compliance_blocklist.md` (initial authored content — categories, platforms, geos), `/backend/services/compliance_checker.py`.

**Folder structure involved**: `/knowledge/risk/`, `/backend/services/`.

**APIs**: Internal function `check_compliance(product_identity) → { flagged: bool, matched_rules: [] }`.

**Database changes**: None (blocklist lives in markdown, parsed at runtime or on a build step — decide and document which).

**Backend tasks**: Implement blocklist parser and matcher against product category/keywords.

**Frontend tasks**: None.

**AI Agent tasks**: None yet (this sprint is deterministic-only).

**Knowledge Base tasks**: Author `compliance_blocklist.md` with real categories (health claims, weapons-adjacent, adult, counterfeit-prone categories) per Meta/TikTok policy research.

**Tests to write**: Unit tests with known-clear and known-blocked product categories.

**Acceptance Criteria**: Known-blocked categories are correctly flagged; known-clear categories pass through.

**Definition of Done**: Tests pass; `compliance_blocklist.md` reviewed for real-world accuracy (not placeholder content).

**Estimated complexity**: Low–Medium.

**Common mistakes to avoid**: Don't hardcode blocklist logic in code — it must be markdown-driven so non-engineers (or Ikram herself) can update it without a code change, per the architecture's knowledge-system philosophy.

**What must be reviewed before moving forward**: Content accuracy review of the blocklist file itself against current Meta/TikTok policy pages.

> ### ✅ REVIEW GATE 1.2.1
> Reviewer confirms blocklist content is accurate and the matcher correctly flags/passes test cases. **Sprint 1.2.2 cannot start until this is signed off.**

---

#### Sprint 1.2.2 — Validation Agent (LLM Gray-Area Judgment + Supplier Check)

**Goal**: Build the LLM-driven portion of validation for gray-area cases, plus supplier availability checking.

**Why this sprint exists**: Completes the Validation Gate per Architecture Section 7 — deterministic check alone can't catch novel IP-infringement or ambiguous policy cases.

**Dependencies**: Sprint 1.2.1.

**Files to create**: `/agents/validation_agent.yaml`, `/prompts/validation/validation_agent_prompt.md` (per Architecture Section 7), `/backend/integrations/supplier_api_client.py` (can mock/stub real supplier APIs initially if none contracted yet — flag clearly).

**Folder structure involved**: `/agents/`, `/prompts/validation/`, `/backend/integrations/`.

**APIs**: `POST /api/validate` — accepts `product_identity`, returns `ValidationResult` per Architecture Section 7.

**Database changes**: Add `validation_results` table or extend `agent_outputs` (prefer the latter, consistent with generic schema philosophy from 0.1.2's warning).

**Backend tasks**: Implement Validation Agent LLM call for gray-area/IP-risk judgment; implement supplier availability check (stock, MOQ, shipping time threshold).

**Frontend tasks**: None yet.

**AI Agent tasks**: Implement Validation Agent prompt exactly per Architecture Section 7.

**Knowledge Base tasks**: None additional (uses `compliance_blocklist.md` from 1.2.1 for context).

**Tests to write**: Golden-set of gray-area products (some should flag, some shouldn't) with reasoning quality checked manually, not just pass/fail.

**Acceptance Criteria**: Gray-area golden-set is judged reasonably and consistently; supplier check correctly identifies MOQ/shipping-time issues on test fixtures.

**Definition of Done**: Tests pass; hard-veto integration confirmed (a Fail here must be capable of stopping the full pipeline later, per Architecture Section 2.3 — wire the status flag now even though full pipeline doesn't exist yet).

**Estimated complexity**: Medium.

**Common mistakes to avoid**: Don't let the LLM silently approve ambiguous cases — per architecture, ambiguous compliance must default to "Requires Manual Legal Review," never silent pass.

**What must be reviewed before moving forward**: Manual review of gray-area judgment quality (this is a case where automated test pass/fail isn't sufficient — a human must read the reasoning).

> ### ✅ REVIEW GATE 1.2.2
> Reviewer confirms gray-area reasoning quality is sound and defaults to caution appropriately. **Sprint 1.2.3 cannot start until this is signed off.**

---

#### Sprint 1.2.3 — Discovery→Validation Integration Test

**Goal**: Wire Discovery and Validation into a single callable pipeline stage and verify end-to-end.

**Why this sprint exists**: Confirms Stage 1 of the pipeline (Architecture Section 3.1) works as a unit before Phase 2 builds on top of it.

**Dependencies**: Sprints 1.1.1–1.1.3, 1.2.1–1.2.2.

**Files to create**: `/workflows/stage1_discovery_validation_workflow.yaml`, `/backend/api/pipeline_stage1_endpoint.py`.

**Folder structure involved**: `/workflows/`, `/backend/api/`.

**APIs**: `POST /api/pipeline/stage1` — accepts raw input, runs Discovery then Validation, returns combined result with a `proceed_to_analysis: bool` flag.

**Database changes**: Add `runs` table population logic — a call to this endpoint creates a `run` row with status tracking.

**Backend tasks**: Orchestrate the two-step call sequence; persist run status.

**Frontend tasks**: None yet.

**AI Agent tasks**: None new — integration only.

**Knowledge Base tasks**: None.

**Tests to write**: Full integration test: valid product → passes both stages; blocked-category product → stops at validation with correct reason; unidentifiable input → stops at discovery with correct reason.

**Acceptance Criteria**: All three integration test scenarios behave correctly and persist correct `run` status.

**Definition of Done**: Integration tests pass in CI; run status correctly reflects each stage's outcome.

**Estimated complexity**: Low–Medium.

**Common mistakes to avoid**: Don't let a Validation failure silently continue to a nonexistent Stage 2 — the `proceed_to_analysis` flag must be enforced by the caller (frontend/API layer), not just informational.

**What must be reviewed before moving forward**: Confirm all three test scenarios pass and run-status table is queryable and correct.

> ### ✅ REVIEW GATE 1.2.3
> Reviewer confirms Stage 1 pipeline works end-to-end with correct gating behavior. **Phase 1 complete. Phase 2 may begin.**

---

## PHASE 2 — SCORING ENGINE & DATA CONTRACTS

### Milestone 2.1 — Scoring Engine Core

---

#### Sprint 2.1.1 — Agent Output Contract (Critical — Unblocks All Domain Agents)

**Goal**: Define the standardized output schema every one of the 10 domain analysis agents must return, per pillar (Architecture Section 2.1 / Section 8).

**Why this sprint exists**: This is the single most important contract in the whole system — the Scoring Engine, Contradiction Auditor, and Synthesizer all depend on every agent returning a consistent shape. This must be locked before any domain agent (Phase 4/5) is built.

**Dependencies**: Sprint 0.1.2 (agent_outputs table exists).

**Files to create**: `/scoring/agent_output_contract.md` (or shared schema module, e.g., Pydantic model in `/backend/schemas/`), reference doc explaining every required field.

**Folder structure involved**: `/scoring/`, `/backend/schemas/`.

**APIs**: None (internal contract).

**Database changes**: None beyond confirming `agent_outputs.output_json` will store objects of this shape.

**Backend tasks**: Define the contract precisely:
```
AgentOutput {
  agent_name: string
  pillar: string            // which of the 7 pillars this feeds, or "risk"/"gate" for non-pillar agents
  sub_score: number (0-100)
  confidence: "Low"|"Medium"|"High"
  evidence: [ { claim: string, citation: string } ]   // every claim must cite its source
  data_completeness_pct: number  // % of expected data points actually retrieved
  raw_findings: object      // agent-specific structured data (free-form, but documented per agent)
}
```

**Frontend tasks**: None yet.

**AI Agent tasks**: None yet — this sprint is contract-only, no agent built.

**Knowledge Base tasks**: None.

**Tests to write**: Schema validation tests (reject any output missing `evidence` citations, reject invalid confidence values, reject out-of-range scores).

**Acceptance Criteria**: Contract is documented, implemented as an enforceable schema, and rejects malformed test payloads.

**Definition of Done**: Schema tests pass; contract doc is the canonical reference linked from every future agent sprint.

**Estimated complexity**: Low, but **highest-leverage sprint in the whole project** — reviewer should treat this with more scrutiny than its size suggests.

**Common mistakes to avoid**: Do not make `evidence`/citations optional — this is what prevents the Contradiction Auditor (Phase 6) from having nothing to check later. Do not let `raw_findings` become a dumping ground that downstream code has to special-case per agent without documentation.

**What must be reviewed before moving forward**: This contract must be reviewed against **every one of the 10 domain agent specs in the architecture doc** to confirm it can actually represent each one's output (e.g., can it represent Competitor Analysis's `gaps_identified[]`? Can it represent Margin's `breakeven_cpa`?).

> ### ✅ REVIEW GATE 2.1.1
> Reviewer confirms contract can represent all 10 agents' documented outputs without hacks. **This is the most important gate in Phase 2 — do not rush it. Sprint 2.1.2 cannot start until this is signed off.**

---

#### Sprint 2.1.2 — Deterministic Pillar Scoring Calculators

**Goal**: Implement the weighted composite scoring math (Architecture Section 2.1) as pure, testable code — no LLM involved.

**Why this sprint exists**: This is the auditable core of the whole platform's trustworthiness; must be built and tested against mock data before any real agent exists.

**Dependencies**: Sprint 2.1.1 (contract).

**Files to create**: `/scoring/pillar_calculators/composite_score.py`, `/scoring/weights_config/default_weights.yaml` (the 7 pillar weights from Architecture 2.1, configurable per Section 8's "possible improvements").

**Folder structure involved**: `/scoring/pillar_calculators/`, `/scoring/weights_config/`.

**APIs**: Internal function `calculate_composite_score(agent_outputs: [AgentOutput]) → { composite_score, pillar_breakdown }`.

**Database changes**: None.

**Backend tasks**: Implement weighted-sum math exactly per Architecture 2.1's table; implement proportional weight redistribution for missing-pillar data (per Architecture Section 8's edge-case rule).

**Frontend tasks**: None yet.

**AI Agent tasks**: None (deterministic code).

**Knowledge Base tasks**: None.

**Tests to write**: Unit tests using mock `AgentOutput` arrays: full data (all 7 pillars present) case; missing-pillar case (confirm redistribution math is correct); known input/output pairs calculated by hand to verify math.

**Acceptance Criteria**: Composite score matches hand-calculated expected values for at least 5 mock scenarios, including the missing-data redistribution case.

**Definition of Done**: All tests pass; weights are loaded from config, not hardcoded.

**Estimated complexity**: Medium (the redistribution math is the tricky part).

**Common mistakes to avoid**: Do not hardcode the 0.20/0.20/0.15/0.15/0.10/0.10/0.10 weights directly in code — must be config-driven per the architecture's "possible improvements" note about configurable weights.

**What must be reviewed before moving forward**: Reviewer manually re-derives 2 of the test cases by hand to confirm the math is right — this is worth the extra scrutiny given it's the trust core of the product.

> ### ✅ REVIEW GATE 2.1.2
> Reviewer independently verifies scoring math correctness. **Sprint 2.1.3 cannot start until this is signed off.**

---

#### Sprint 2.1.3 — Hard Veto Rules & Confidence Calculator

**Goal**: Implement the hard-veto override logic (Architecture Section 2.3) and the confidence-level calculator (Architecture Section 2.4).

**Why this sprint exists**: Vetoes must override the composite score regardless of how good it looks — this is a distinct, separately-testable piece of logic that must not be buried inside the composite score calculator.

**Dependencies**: Sprint 2.1.2.

**Files to create**: `/scoring/veto_rules/hard_vetoes.py`, `/scoring/pillar_calculators/confidence_calculator.py`.

**Folder structure involved**: `/scoring/veto_rules/`.

**APIs**: Internal function `check_hard_vetoes(agent_outputs) → { vetoed: bool, triggered_rules: [] }`; `calculate_confidence(agent_outputs) → "Low"|"Medium"|"High"`.

**Database changes**: None.

**Backend tasks**: Implement all 4 hard veto rules exactly per Architecture Section 2.3; implement confidence calculation based on `data_completeness_pct` aggregate across agent outputs.

**Frontend tasks**: None yet.

**AI Agent tasks**: None.

**Knowledge Base tasks**: None.

**Tests to write**: One test per veto rule (4 total) confirming it triggers correctly and overrides a high composite score; confidence calculator tests across low/medium/high completeness scenarios.

**Acceptance Criteria**: A mock scenario with composite score 85 but margin < 15% correctly returns NO-GO via veto override, not GO.

**Definition of Done**: All veto and confidence tests pass.

**Estimated complexity**: Low–Medium.

**Common mistakes to avoid**: Don't let veto logic live inside the composite score function — keep it a separate, explicit override step so it's auditable independently (matches architecture's explicit separation of Section 2.2 vs 2.3).

**What must be reviewed before moving forward**: Confirm veto override actually takes precedence in the final verdict logic (test the "high score but vetoed" scenario specifically).

> ### ✅ REVIEW GATE 2.1.3
> Reviewer confirms veto override behavior is correct and impossible to bypass. **Sprint 2.1.4 cannot start until this is signed off.**

---

#### Sprint 2.1.4 — Scoring Engine Golden-Dataset Test Suite

**Goal**: Build a comprehensive regression-proof test suite for the full Scoring Engine using realistic mock data covering many scenarios.

**Why this sprint exists**: The Scoring Engine will be touched again later (weight recalibration, Phase 8 backtesting) — a strong golden-dataset suite now prevents silent regressions later.

**Dependencies**: Sprints 2.1.1–2.1.3.

**Files to create**: `/tests/scoring_tests/golden_dataset.json` (10–15 realistic mock scenarios spanning GO/CONDITIONAL/NO-GO/vetoed cases), `/tests/scoring_tests/test_scoring_engine_full.py`.

**Folder structure involved**: `/tests/scoring_tests/`.

**APIs**: None new.

**Database changes**: None.

**Backend tasks**: None new — test authoring only.

**Frontend tasks**: None.

**AI Agent tasks**: None.

**Knowledge Base tasks**: None.

**Tests to write**: The golden dataset itself, covering: clean GO, clean NO-GO, borderline score near threshold (per Architecture Section 19's "sits right at the boundary" edge case), each of the 4 veto scenarios, missing-data/low-confidence scenario.

**Acceptance Criteria**: All golden-dataset scenarios produce the expected verdict + confidence + veto behavior.

**Definition of Done**: Full suite passes and is wired into CI as a required check for any future `/scoring` changes.

**Estimated complexity**: Medium (dataset design requires care, not much code).

**Common mistakes to avoid**: Don't only test "happy path" GO scenarios — the borderline and veto cases are where bugs actually hide.

**What must be reviewed before moving forward**: Reviewer checks that the golden dataset genuinely covers edge cases, not just repeats of the same scenario shape.

> ### ✅ REVIEW GATE 2.1.4
> Reviewer confirms golden dataset coverage is genuinely diverse. **Phase 2 complete. Phase 3 may begin (can run in parallel with Phase 4 workstream once Phase 3 knowledge author is available).**

---

## PHASE 3 — KNOWLEDGE BASE & RAG INFRASTRUCTURE
*(Can be developed in parallel with Phase 4/5 by a separate workstream — no code dependency between them beyond the retrieval interface in Sprint 3.1.2.)*

### Milestone 3.1 — KB Infrastructure & Content

---

#### Sprint 3.1.1 — Market & Economics Knowledge Files

**Goal**: Author the first batch of real Knowledge Base markdown files per Architecture Section 21.

**Why this sprint exists**: Domain agents in Phase 4/5 need real KB content to retrieve from, not placeholders — content quality directly determines agent output quality.

**Dependencies**: Sprint 0.1.1 (folder structure exists).

**Files to create**: `/knowledge/market/winning_products.md`, `/knowledge/market/market_saturation.md`, `/knowledge/market/seasonality_calendar.md`, `/knowledge/market/niche_taxonomy.md`, `/knowledge/economics/pricing.md`, `/knowledge/economics/margin_benchmarks.md`, `/knowledge/economics/shipping_and_fees.md`.

**Folder structure involved**: `/knowledge/market/`, `/knowledge/economics/`.

**APIs**: None yet.

**Database changes**: None.

**Backend tasks**: None yet (indexing comes in 3.1.2).

**Frontend tasks**: None.

**AI Agent tasks**: None yet.

**Knowledge Base tasks**: Write each file as explicit, numbered heuristics/thresholds (not prose), each with a `last_updated` date and short changelog section at the top, per Architecture Section 4.2.

**Tests to write**: A markdown-lint/structure test confirming every KB file has the required `last_updated` metadata header.

**Acceptance Criteria**: All 7 files exist with real, researched content (not lorem-ipsum placeholders) and pass the metadata-structure test.

**Definition of Done**: Content reviewed for factual accuracy/reasonableness by a human familiar with eCommerce economics.

**Estimated complexity**: Medium (research-heavy, not code-heavy).

**Common mistakes to avoid**: Don't write vague prose ("prices vary by category") — every file must contain concrete, actionable thresholds per Architecture Section 4.2's explicit requirement.

**What must be reviewed before moving forward**: Content-quality review, not just structural — a reviewer should be able to point to at least 3 concrete, usable heuristics per file.

> ### ✅ REVIEW GATE 3.1.1
> Reviewer confirms content is concrete and metadata structure is correct. **Sprint 3.1.2 cannot start until this is signed off.**

---

#### Sprint 3.1.2 — KB Retrieval/Indexing Pipeline + Agent Manifests

**Goal**: Build the retrieval infrastructure (embedding/indexing) and the per-agent manifest system (Architecture Section 4.3).

**Why this sprint exists**: Domain agents need a `KnowledgeRetriever` interface to call — building this now (against the content from 3.1.1) unblocks every future agent sprint from Phase 4 onward.

**Dependencies**: Sprint 3.1.1 (needs real content to index against).

**Files to create**: `/backend/services/knowledge_retriever.py` (interface + implementation), `/knowledge/_manifests/*.yaml` (one per agent, listing allowed KB files per Architecture Section 22 — can be authored even before the agent itself is built).

**Folder structure involved**: `/backend/services/`, `/knowledge/_manifests/`.

**APIs**: Internal function `retrieve_knowledge(agent_name: string, query: string) → [relevant_chunks]`.

**Database changes**: Add a vector store table or external vector DB connection (document which is chosen and why).

**Backend tasks**: Implement embedding pipeline for markdown files; implement manifest-based filtering so an agent only ever retrieves from its permitted files; implement re-indexing trigger when a KB file's `last_updated` changes.

**Frontend tasks**: None.

**AI Agent tasks**: None yet.

**Knowledge Base tasks**: Author manifest files for all agents listed in Architecture Section 22, even ones not yet built (manifests are cheap to write now, expensive to forget later).

**Tests to write**: Retrieval relevance test (query against `pricing.md`, confirm relevant chunks returned); manifest isolation test (confirm an agent's manifest correctly blocks retrieval from files it shouldn't access).

**Acceptance Criteria**: Retrieval returns relevant content for test queries; manifest isolation is enforced and testable.

**Definition of Done**: Tests pass; `KnowledgeRetriever` interface is documented for use by all future agent sprints.

**Estimated complexity**: Medium–High (embedding/indexing choice and re-indexing logic is the tricky part).

**Common mistakes to avoid**: Don't hardcode which files an agent can see inside the agent's own code — must go through the manifest system, per Architecture Section 4.3's explicit design reasoning (keeps agents swappable/narrow).

**What must be reviewed before moving forward**: Confirm manifest isolation actually works (test that FB Ads Agent's manifest cannot retrieve from `psychology.md`, for example).

> ### ✅ REVIEW GATE 3.1.2
> Reviewer confirms retrieval relevance and manifest isolation both work correctly. **Sprint 3.1.3 cannot start until this is signed off.**

---

#### Sprint 3.1.3 — Remaining Knowledge Base Files

**Goal**: Complete authoring of all remaining KB files (advertising, psychology, risk, scoring domains).

**Why this sprint exists**: Completes the full KB per Architecture Section 21 before Phase 4/5 agents need domain-specific content beyond market/economics.

**Dependencies**: Sprint 3.1.2 (indexing pipeline must exist to validate new content indexes correctly).

**Files to create**: `/knowledge/advertising/facebook_ads.md`, `/knowledge/advertising/tiktok_trends.md`, `/knowledge/advertising/marketing_angles.md`, `/knowledge/advertising/creative_rules.md`, `/knowledge/psychology/psychology.md`, `/knowledge/psychology/consumer_behavior.md`, `/knowledge/psychology/review_language_patterns.md`, `/knowledge/risk/supplier_risk_patterns.md`, `/knowledge/risk/legal_certification_requirements.md`, `/knowledge/scoring/product_scoring.md`, `/knowledge/scoring/competitor_analysis.md`.

**Folder structure involved**: `/knowledge/advertising/`, `/knowledge/psychology/`, `/knowledge/risk/`, `/knowledge/scoring/`.

**APIs**: None new.

**Database changes**: None.

**Backend tasks**: Re-run indexing pipeline against new content.

**Frontend tasks**: None.

**AI Agent tasks**: None yet.

**Knowledge Base tasks**: Author all remaining files with the same rigor as Sprint 3.1.1 (concrete heuristics, metadata headers).

**Tests to write**: Same metadata-structure test extended to all new files; spot-check retrieval relevance queries for 3–4 new files.

**Acceptance Criteria**: All KB files from Architecture Section 21 now exist with real content and index correctly.

**Definition of Done**: Content review passed; full KB is complete.

**Estimated complexity**: Medium (largest research-content sprint in the project).

**Common mistakes to avoid**: Don't let `product_scoring.md` drift from the actual Scoring Engine code built in Phase 2 — this file must mirror Architecture Section 2 exactly, and if a scoring recalibration ever happens later, this file must be updated in the same PR.

**What must be reviewed before moving forward**: Cross-check `product_scoring.md` word-for-word logic against the Phase 2 code.

> ### ✅ REVIEW GATE 3.1.3
> Reviewer confirms full KB completeness and `product_scoring.md`/code consistency. **Phase 3 complete.**

---

## PHASE 4 — HIGH-SIGNAL ANALYSIS AGENTS
*(FB Ads, Amazon Reviews, Pricing, Margin — chosen first per architecture's closing note: "highest signal-to-effort ratio")*

### Milestone 4.1 — Data Source Integrations

---

#### Sprint 4.1.1 — Shared Integration Service Pattern + FB Ad Library Integration

**Goal**: Establish the shared integration service pattern (to avoid the tech debt risk named in Part A), then build the first real integration: Facebook Ad Library.

**Why this sprint exists**: This is the pattern every future data integration (Amazon, TikTok, Supplier) will follow — get it right once here.

**Dependencies**: Sprint 0.1.1 (backend skeleton).

**Files to create**: `/backend/integrations/base_integration_service.py` (shared interface: caching, rate-limit handling, freshness flagging), `/backend/integrations/fb_ad_library_client.py`.

**Folder structure involved**: `/backend/integrations/`.

**APIs**: Internal function `fetch_fb_ads(keywords, geo, date_range) → { ads: [], data_freshness_days: int, coverage_note: string }`.

**Database changes**: Add a generic `integration_cache` table (`source, query_hash, response_json, fetched_at`) usable by all future integrations, not FB-specific.

**Backend tasks**: Implement base service with: cache-check-first logic, TTL config per source, rate-limit backoff, and a standardized "insufficient/partial data" flag per Architecture Section 5's edge-case rules. Implement FB Ad Library client on top of this base.

**Frontend tasks**: None yet.

**AI Agent tasks**: None yet (agent comes in Sprint 4.2.1).

**Knowledge Base tasks**: None.

**Tests to write**: Cache hit/miss tests; rate-limit/backoff simulation test; "zero results" and "partial geo coverage" edge case tests per Architecture Section 5.

**Acceptance Criteria**: FB Ad Library client returns real data for test queries, correctly caches, and correctly flags partial/stale data rather than silently passing it through as fresh.

**Definition of Done**: Tests pass; base integration pattern is documented for reuse by Sprints 4.1.2, 4.1.3, and 5.1.x/5.2.x.

**Estimated complexity**: Medium–High (external API/scraping reliability is inherently the hardest part of this whole project).

**Common mistakes to avoid**: Do not build FB-specific caching logic that isn't reusable — this is exactly the tech debt risk flagged in Part A. The base service must be genuinely source-agnostic.

**What must be reviewed before moving forward**: Confirm the base integration pattern is actually reusable (reviewer should be able to sketch how Amazon/TikTok/Supplier integrations would plug into it without copy-pasting FB-specific code).

> ### ✅ REVIEW GATE 4.1.1
> Reviewer confirms base pattern is genuinely reusable and FB integration handles partial/stale data correctly. **Sprint 4.1.2 cannot start until this is signed off.**

---

#### Sprint 4.1.2 — Amazon Review Integration

**Goal**: Build the Amazon scraping/review integration on top of the base pattern from 4.1.1.

**Why this sprint exists**: Second highest-signal data source per architecture; also the highest-risk integration (anti-bot measures), so build and stress-test it early.

**Dependencies**: Sprint 4.1.1 (base pattern).

**Files to create**: `/backend/integrations/amazon_review_client.py`.

**Folder structure involved**: `/backend/integrations/`.

**APIs**: Internal function `fetch_amazon_reviews(asin_or_search_term) → { reviews: [], avg_rating, review_volume, data_freshness_days }`.

**Database changes**: Reuses `integration_cache` table from 4.1.1.

**Backend tasks**: Implement scraper with resilience (retry, fallback to cache, explicit failure state rather than silent empty result) per the high-risk designation in Part A.

**Frontend tasks**: None.

**AI Agent tasks**: None yet.

**Knowledge Base tasks**: None.

**Tests to write**: Fixture-based scraping tests (mocked HTML); cache fallback test simulating a live scrape failure; authenticity red-flag detection stub (unnatural rating clustering) per Architecture Section 15's failure case.

**Acceptance Criteria**: Client returns real review data for test ASINs; gracefully degrades to cached/flagged-stale data on scrape failure rather than crashing or returning empty silently.

**Definition of Done**: Tests pass including the simulated-failure scenario.

**Estimated complexity**: High (named as a top project risk in Part A).

**Common mistakes to avoid**: Do not let scrape failures propagate as "zero reviews found" to downstream agents — that's indistinguishable from "genuinely no reviews exist" and will corrupt the Review Analysis Agent's scoring later. Must be a distinct error/stale state.

**What must be reviewed before moving forward**: Reviewer specifically tests the failure-degradation path, not just the happy path.

> ### ✅ REVIEW GATE 4.1.2
> Reviewer confirms failure states are distinguishable from genuine zero-data states. **Sprint 4.1.3 cannot start until this is signed off.**

---

#### Sprint 4.1.3 — Supplier/COGS Integration

**Goal**: Build supplier data integration (COGS, MOQ, shipping time, stock) needed by Margin and Pricing agents.

**Why this sprint exists**: Unblocks Margin Agent (Sprint 4.2.4), which cannot function without real COGS data.

**Dependencies**: Sprint 4.1.1 (base pattern).

**Files to create**: `/backend/integrations/supplier_client.py`.

**Folder structure involved**: `/backend/integrations/`.

**APIs**: Internal function `fetch_supplier_data(product_identity) → { cogs, moq, shipping_days, supplier_rating, source }`.

**Database changes**: Reuses `integration_cache`.

**Backend tasks**: Implement supplier API/scrape client per available supplier platform(s) decided at implementation time; document which platform(s) are actually integrated (e.g., AliExpress, CJ Dropshipping) versus deferred.

**Frontend tasks**: None.

**AI Agent tasks**: None.

**Knowledge Base tasks**: None.

**Tests to write**: Fixture-based tests for supplier data retrieval; MOQ/shipping-time threshold flagging test per Architecture Section 18's supplier risk rules.

**Acceptance Criteria**: Client returns COGS/MOQ/shipping data for test products with correct threshold flagging.

**Definition of Done**: Tests pass.

**Estimated complexity**: Medium.

**Common mistakes to avoid**: Don't assume single-supplier data is authoritative — architecture's Risk module (18) explicitly wants supplier-diversity awareness eventually; at minimum, tag which supplier a data point came from so future multi-supplier comparison isn't a rebuild.

**What must be reviewed before moving forward**: Confirm data includes supplier source attribution for future extensibility.

> ### ✅ REVIEW GATE 4.1.3
> Reviewer confirms supplier data is correctly sourced and attributed. **Milestone 4.1 complete. Milestone 4.2 may begin.**

---

### Milestone 4.2 — High-Signal Agents

---

#### Sprint 4.2.1 — Facebook Ads Analysis Agent

**Goal**: Build the full FB Ads Analysis Agent per Architecture Section 13.

**Why this sprint exists**: Highest-priority agent per architecture — several other agents (Margin, Creative Opportunity) depend on its output.

**Dependencies**: Sprints 2.1.1 (contract), 3.1.2–3.1.3 (KB + retrieval), 4.1.1 (FB integration).

**Files to create**: `/agents/analysis/fb_ads_agent.yaml`, `/prompts/analysis/fb_ads_agent_prompt.md` (per Architecture Section 13).

**Folder structure involved**: `/agents/analysis/`, `/prompts/analysis/`.

**APIs**: Internal function callable by the future orchestrator: `run_fb_ads_analysis(product_identity) → AgentOutput`.

**Database changes**: None (writes to `agent_outputs` via existing schema).

**Backend tasks**: Wire FB integration data + KB retrieval (`facebook_ads.md`, `creative_rules.md`, `marketing_angles.md` per its manifest) into the agent's prompt context; implement angle-clustering logic (may be LLM-driven or a hybrid with simple text-similarity clustering — document choice).

**Frontend tasks**: None yet.

**AI Agent tasks**: Implement the full agent prompt exactly per Architecture Section 13, returning output conforming to the Sprint 2.1.1 contract.

**Knowledge Base tasks**: None new (uses existing files).

**Tests to write**: Golden-set test with 5–10 real products with known ad presence, checking output conforms to contract and angle-clustering is qualitatively reasonable (human-reviewed, not just schema-valid).

**Acceptance Criteria**: Agent produces contract-conformant output with citations for every claim; angle clustering is judged reasonable by a human reviewer on the golden set.

**Definition of Done**: Tests pass; output correctly distinguishes "sustained profitable ads" from "high ad count but low diversity" scenarios per Architecture Section 13's scoring logic.

**Estimated complexity**: Medium–High (this is the first real domain agent — expect some iteration on prompt quality).

**Common mistakes to avoid**: Don't score based on raw ad count alone — architecture explicitly warns this rewards saturation, which is the wrong signal.

**What must be reviewed before moving forward**: Human review of golden-set outputs for qualitative reasoning quality, not just automated pass/fail.

> ### ✅ REVIEW GATE 4.2.1
> Reviewer confirms output quality and contract conformance. **Sprint 4.2.2 cannot start until this is signed off.**

---

#### Sprint 4.2.2 — Amazon Review Mining Agent

**Goal**: Build the Review Mining Agent per Architecture Section 15.

**Why this sprint exists**: Ground-truth product quality signal; second highest-priority agent per architecture's closing note.

**Dependencies**: Sprints 2.1.1, 3.1.2–3.1.3, 4.1.2 (Amazon integration).

**Files to create**: `/agents/analysis/review_mining_agent.yaml`, `/prompts/analysis/review_mining_agent_prompt.md`.

**Folder structure involved**: `/agents/analysis/`, `/prompts/analysis/`.

**APIs**: `run_review_analysis(product_identity) → AgentOutput`.

**Database changes**: None.

**Backend tasks**: Wire Amazon integration data + `review_language_patterns.md` KB into agent context; implement complaint/praise clustering.

**Frontend tasks**: None.

**AI Agent tasks**: Implement per Architecture Section 15, including the structural-defect vs. expectation-mismatch classification logic and the review-authenticity red-flag check.

**Knowledge Base tasks**: None new.

**Tests to write**: Golden-set test with known-good and known-bad-quality products; specific test for the "manipulated reviews" detection edge case per Architecture Section 15's failure case.

**Acceptance Criteria**: Output correctly distinguishes structural defects from expectation-mismatch on the golden set; authenticity-concern flag triggers correctly on a synthetic manipulated-review fixture.

**Definition of Done**: Tests pass; human review confirms complaint clustering is qualitatively sound.

**Estimated complexity**: Medium.

**Common mistakes to avoid**: Don't quote review text verbatim in outputs — paraphrase (this also matters for the eventual user-facing report's copyright hygiene). Don't let missing-Amazon-listing case silently return a zero score — must fall back to secondary sources or flag Low confidence per Architecture Section 15.

**What must be reviewed before moving forward**: Human review of classification quality on golden set.

> ### ✅ REVIEW GATE 4.2.2
> Reviewer confirms classification quality and fallback behavior. **Sprint 4.2.3 cannot start until this is signed off.**

---

#### Sprint 4.2.3 — Pricing Analysis Agent

**Goal**: Build the Pricing Analysis Agent per Architecture Section 11.

**Why this sprint exists**: Needed as an input to the Margin Agent (next sprint); also useful independently.

**Dependencies**: Sprints 2.1.1, 3.1.1 (`pricing.md`), 4.1.3 (supplier/COGS data). Note: full Competitor Agent (Phase 5) is not yet built — this sprint should consume whatever raw competitor pricing data is available directly (e.g., from a lightweight storefront price scrape done inline here), not block on Phase 5. Document this as a temporary direct-scrape approach to be replaced once Sprint 5.1.2 exists.

**Files to create**: `/agents/analysis/pricing_agent.yaml`, `/prompts/analysis/pricing_agent_prompt.md`, `/backend/integrations/storefront_price_scraper.py` (lightweight, temporary — see dependency note).

**Folder structure involved**: `/agents/analysis/`, `/prompts/analysis/`, `/backend/integrations/`.

**APIs**: `run_pricing_analysis(product_identity, cogs_data) → AgentOutput`.

**Database changes**: None.

**Backend tasks**: Implement lightweight competitor price scraping (title/price only, not full funnel teardown — that's Phase 5's job); wire `pricing.md` KB.

**Frontend tasks**: None.

**AI Agent tasks**: Implement per Architecture Section 11.

**Knowledge Base tasks**: None new.

**Tests to write**: Golden-set test verifying reasonable price-range recommendations against known market prices.

**Acceptance Criteria**: Recommended price ranges are reasonable given test market data; margin-implausibility flag triggers correctly on a synthetic low-price/high-COGS fixture.

**Definition of Done**: Tests pass; the "temporary direct-scrape" boundary is clearly marked in code comments/docs for Phase 5 replacement.

**Estimated complexity**: Medium.

**Common mistakes to avoid**: Don't build a full Competitor Analysis Agent here by accident — scope creep risk. Keep the price scrape minimal and clearly temporary.

**What must be reviewed before moving forward**: Confirm the temporary-scrape boundary is documented so Phase 5 doesn't duplicate or conflict with it.

> ### ✅ REVIEW GATE 4.2.3
> Reviewer confirms output quality and clean temporary-boundary documentation. **Sprint 4.2.4 cannot start until this is signed off.**

---

#### Sprint 4.2.4 — Margin Analysis Agent

**Goal**: Build the Margin Analysis Agent per Architecture Section 12 — the most economically critical agent in the system (feeds the hard veto).

**Why this sprint exists**: This agent's output directly triggers the system's most important hard veto (net margin < 15%); must be built and tested with extra rigor.

**Dependencies**: Sprints 4.2.1 (FB Ads Agent, for CPA estimate), 4.2.3 (Pricing Agent), 4.1.3 (supplier/COGS), 3.1.1 (`margin_benchmarks.md`, `shipping_and_fees.md`).

**Files to create**: `/agents/analysis/margin_agent.yaml`, `/prompts/analysis/margin_agent_prompt.md`.

**Folder structure involved**: `/agents/analysis/`, `/prompts/analysis/`.

**APIs**: `run_margin_analysis(product_identity, pricing_output, fb_ads_output, cogs_data) → AgentOutput`.

**Database changes**: None.

**Backend tasks**: Implement the exact margin formula from Architecture Section 12, showing step-by-step math in the output (not just a final number) so it's auditable in the eventual report.

**Frontend tasks**: None.

**AI Agent tasks**: Implement per Architecture Section 12, including the CPA-benchmark-fallback logic when FB Ads Agent has insufficient data.

**Knowledge Base tasks**: None new.

**Tests to write**: Golden-set covering: healthy margin case, thin-margin (15–25%) conditional case, sub-15% veto-triggering case, and a case with no FB Ads CPA data (fallback to benchmark, confidence flagged Low).

**Acceptance Criteria**: All 4 golden-set scenarios produce mathematically correct margin calculations and correctly flag their respective condition/veto/confidence states.

**Definition of Done**: Tests pass; math is independently re-derived by reviewer for at least 2 cases (same rigor as Scoring Engine review).

**Estimated complexity**: Medium–High (highest-stakes agent given its veto power).

**Common mistakes to avoid**: Don't silently use a stale or category-mismatched CPA benchmark without flagging it as an "estimated proxy" per Architecture Section 12's explicit failure-case handling.

**What must be reviewed before moving forward**: Independent hand-verification of margin math on 2+ golden-set cases.

> ### ✅ REVIEW GATE 4.2.4
> Reviewer independently re-derives margin math and confirms correctness. **Phase 4 complete.**

---

## PHASE 5 — REMAINING ANALYSIS AGENTS
*(Can be built in parallel across sub-workstreams: Milestone 5.1, 5.2, 5.3 have no dependencies on each other, only on Phase 2–4 outputs.)*

### Milestone 5.1 — Market & Competitive Agents

---

#### Sprint 5.1.1 — Market Saturation Agent

**Goal**: Build per Architecture Section 9.

**Dependencies**: Sprints 2.1.1, 3.1.1 (`market_saturation.md`), 4.1.1 (FB integration; TikTok integration deferred to 5.2.1 — this agent can run on FB data alone initially and be extended once TikTok integration exists).

**Files to create**: `/agents/analysis/saturation_agent.yaml`, `/prompts/analysis/saturation_agent_prompt.md`.

**Folder structure involved**: `/agents/analysis/`, `/prompts/analysis/`.

**APIs**: `run_saturation_analysis(product_identity) → AgentOutput`.

**Database changes**: Add lightweight time-series tracking (per-product saturation history) to support the agent's "last 3 runs" memory feature from Architecture Section 22.3.

**Backend tasks**: Implement advertiser-count trend analysis (90-day window) and market-stage classification.

**Frontend tasks**: None.

**AI Agent tasks**: Implement per Architecture Section 9.

**Knowledge Base tasks**: None new.

**Tests to write**: Golden-set covering each market stage (Emerging/Growing/Peak/Declining) with synthetic advertiser-count time series.

**Acceptance Criteria**: Correct stage classification on all 4 synthetic scenarios; differentiation-angle detection reasoning is sound.

**Definition of Done**: Tests pass.

**Estimated complexity**: Medium.

**Common mistakes to avoid**: Don't score saturation on raw advertiser count without the trend-direction component — architecture explicitly requires distinguishing Growing (rising) from Peak (flat) at similar counts.

**What must be reviewed before moving forward**: Confirm stage classification reasoning, not just final score.

> ### ✅ REVIEW GATE 5.1.1
> **Sprint 5.1.2 cannot start until this is signed off.**

---

#### Sprint 5.1.2 — Competitor Analysis Agent (+ Full Storefront Teardown)

**Goal**: Build per Architecture Section 10; also formally replaces the temporary price-scraper boundary flagged in Sprint 4.2.3.

**Dependencies**: Sprint 5.1.1 (consumes its advertiser list), Sprint 4.2.3 (replaces its temporary scraper).

**Files to create**: `/agents/analysis/competitor_agent.yaml`, `/prompts/analysis/competitor_agent_prompt.md`, `/backend/integrations/storefront_teardown_scraper.py` (full version: pricing, bundles, guarantees, review counts).

**Folder structure involved**: `/agents/analysis/`, `/prompts/analysis/`, `/backend/integrations/`.

**APIs**: `run_competitor_analysis(product_identity, saturation_output) → AgentOutput`.

**Database changes**: Reuses `integration_cache`; add 7-day cache TTL config per Architecture Section 22.4's memory spec.

**Backend tasks**: Implement full storefront teardown scraper; retire the temporary scraper from Sprint 4.2.3 and repoint Pricing Agent to this new one.

**Frontend tasks**: None.

**AI Agent tasks**: Implement per Architecture Section 10.

**Knowledge Base tasks**: None new (`competitor_analysis.md` already authored in Phase 3).

**Tests to write**: Golden-set covering weak-competitor (opportunity) and mature-competitor (barrier) scenarios; regression test confirming Pricing Agent (4.2.3) still works correctly with the new data source.

**Acceptance Criteria**: Gap-identification reasoning is sound on golden set; Pricing Agent regression test passes.

**Definition of Done**: Tests pass; temporary scraper from 4.2.3 is fully removed (not left as dead code).

**Estimated complexity**: Medium–High.

**Common mistakes to avoid**: Don't leave both scrapers running in parallel indefinitely — clean up the temporary one to avoid the tech-debt risk flagged in Part A.

**What must be reviewed before moving forward**: Confirm temporary scraper removal and Pricing Agent regression pass.

> ### ✅ REVIEW GATE 5.1.2
> **Milestone 5.1 complete. Milestone 5.2 may begin (in parallel with 5.1 if separate workstream capacity exists).**

---

### Milestone 5.2 — Trend & Psychology Agents

---

#### Sprint 5.2.1 — TikTok Trend Agent (+ TikTok Integration)

**Goal**: Build per Architecture Section 14, including the TikTok Creative Center integration deferred since Sprint 1.1.3.

**Dependencies**: Sprint 4.1.1 (base integration pattern to extend).

**Files to create**: `/backend/integrations/tiktok_creative_center_client.py`, `/agents/analysis/tiktok_agent.yaml`, `/prompts/analysis/tiktok_agent_prompt.md`.

**Folder structure involved**: `/backend/integrations/`, `/agents/analysis/`, `/prompts/analysis/`.

**APIs**: `run_tiktok_analysis(product_identity) → AgentOutput`.

**Database changes**: Trend-velocity history table (per Architecture Section 22.8's memory spec), similar pattern to Saturation Agent's time-series table.

**Backend tasks**: Implement TikTok integration on the base pattern; implement Google Trends fallback per Architecture Section 14's failure case.

**Frontend tasks**: None.

**AI Agent tasks**: Implement per Architecture Section 14, including commerce-intent vs. entertainment-virality classification.

**Knowledge Base tasks**: None new (`tiktok_trends.md` already authored).

**Tests to write**: Golden-set covering rising/peaking/declining trends and commerce-vs-entertainment classification; fallback test simulating TikTok access failure.

**Acceptance Criteria**: Correct classification on golden set; fallback correctly engages and lowers confidence.

**Definition of Done**: Tests pass. Also: retroactively wire this real integration into Sprint 1.1.3's niche-shortlist mock boundary (per that sprint's flagged TODO).

**Estimated complexity**: Medium–High.

**Common mistakes to avoid**: Don't score raw view-count velocity without the commerce-intent filter — architecture explicitly warns pure entertainment virality is a false signal.

**What must be reviewed before moving forward**: Confirm the Sprint 1.1.3 mock boundary was actually replaced, not left in place alongside the new real integration.

> ### ✅ REVIEW GATE 5.2.1
> **Sprint 5.2.2 cannot start until this is signed off.**

---

#### Sprint 5.2.2 — Customer Psychology Agent

**Goal**: Build per Architecture Section 16.

**Dependencies**: Sprint 4.2.2 (Review Mining Agent output), Sprint 4.2.1 (FB Ads Agent hooks), Sprint 3.1.3 (`psychology.md`, `consumer_behavior.md`).

**Files to create**: `/agents/analysis/psychology_agent.yaml`, `/prompts/analysis/psychology_agent_prompt.md`.

**Folder structure involved**: `/agents/analysis/`, `/prompts/analysis/`.

**APIs**: `run_psychology_analysis(product_identity, review_output, fb_ads_output) → AgentOutput`.

**Database changes**: None.

**Backend tasks**: Wire review + ad-hook data into agent context.

**Frontend tasks**: None.

**AI Agent tasks**: Implement per Architecture Section 16, including purchase-trigger classification and multi-persona detection.

**Knowledge Base tasks**: None new.

**Tests to write**: Golden-set covering clear-single-pain-point products and multi-persona products; low-data fallback test (new product, few reviews) confirming "Hypothesized, Unvalidated" flag per Architecture Section 16's failure case.

**Acceptance Criteria**: Correct classification and confidence-flagging on golden set.

**Definition of Done**: Tests pass.

**Estimated complexity**: Medium.

**Common mistakes to avoid**: Don't treat multi-persona products as a negative signal by default — architecture notes this can be a positive (more creative angles) depending on context.

**What must be reviewed before moving forward**: Human review of pain-point extraction quality — this is subjective and needs judgment, not just schema validation.

> ### ✅ REVIEW GATE 5.2.2
> **Milestone 5.2 complete. Milestone 5.3 may begin.**

---

### Milestone 5.3 — Creative & Risk Agents

---

#### Sprint 5.3.1 — Creative Opportunity Agent

**Goal**: Build per Architecture Section 17.

**Dependencies**: Sprint 5.2.2 (Psychology Agent), Sprint 4.2.1 (FB Ads Agent angle clusters).

**Files to create**: `/agents/analysis/creative_opportunity_agent.yaml`, `/prompts/analysis/creative_opportunity_agent_prompt.md`.

**Folder structure involved**: `/agents/analysis/`, `/prompts/analysis/`.

**APIs**: `run_creative_opportunity_analysis(product_identity, psychology_output, fb_ads_output) → AgentOutput`.

**Database changes**: None.

**Backend tasks**: Implement angle-gap cross-referencing logic (viable angles from psychology vs. crowded angles from FB Ads).

**Frontend tasks**: None.

**AI Agent tasks**: Implement per Architecture Section 17.

**Knowledge Base tasks**: None new (`creative_rules.md` already authored).

**Tests to write**: Golden-set covering: 4+ viable angle case (strong score), <2 viable angle case (must trigger the Section 2.3 hard veto flag correctly), all-crowded-angles case.

**Acceptance Criteria**: The <2-angle veto-trigger case is correctly flagged and wired to eventually reach the Scoring Engine's hard veto (Sprint 2.1.3) once orchestration exists (Phase 6).

**Definition of Done**: Tests pass.

**Estimated complexity**: Medium.

**Common mistakes to avoid**: Don't fabricate a forced differentiation angle when none genuinely exists — architecture explicitly requires honest "no clear differentiation angle identified" output in that case.

**What must be reviewed before moving forward**: Confirm the veto-trigger case output correctly matches the format Sprint 2.1.3's veto checker expects.

> ### ✅ REVIEW GATE 5.3.1
> **Sprint 5.3.2 cannot start until this is signed off.**

---

#### Sprint 5.3.2 — Risk Analysis Agent

**Goal**: Build per Architecture Section 18 — the last of the 10 domain agents.

**Dependencies**: Nearly all prior agents (this agent's architecture spec explicitly consumes aggregated data from across the system) — Sprints 4.2.1–4.2.4, 5.1.1–5.1.2, 5.2.1–5.2.2, 5.3.1, plus `compliance_blocklist.md` (1.2.1), `supplier_risk_patterns.md` and `legal_certification_requirements.md` (3.1.3), `seasonality_calendar.md` (3.1.1).

**Files to create**: `/agents/analysis/risk_agent.yaml`, `/prompts/analysis/risk_agent_prompt.md`.

**Folder structure involved**: `/agents/analysis/`, `/prompts/analysis/`.

**APIs**: `run_risk_analysis(product_identity, all_other_agent_outputs) → AgentOutput`.

**Database changes**: None.

**Backend tasks**: Implement the 5-category risk checklist review logic per Architecture Section 18.

**Frontend tasks**: None.

**AI Agent tasks**: Implement per Architecture Section 18, including the off-season detection edge case (must not penalize a seasonal product analyzed outside its season).

**Knowledge Base tasks**: None new.

**Tests to write**: Golden-set covering each risk category rated Severe individually; off-season edge case test; multi-moderate-risk stacking test.

**Acceptance Criteria**: Correct risk categorization and stacking on golden set; off-season case correctly flags "re-test near season" rather than penalizing.

**Definition of Done**: Tests pass. **This sprint completes all 10 domain agents — a full regression run of all agent golden-sets together should be executed once more here to confirm nothing broke across sprints.**

**Estimated complexity**: Medium–High (most cross-cutting agent, hardest to test in isolation).

**Common mistakes to avoid**: Don't let this agent's broad data dependency turn into a monolithic "do everything" agent — it should only assess risk, not re-derive scores that belong to other pillars.

**What must be reviewed before moving forward**: Full cross-agent regression run (all 10 golden-sets) confirming system-wide stability.

> ### ✅ REVIEW GATE 5.3.2
> Reviewer confirms full 10-agent regression passes. **Phase 5 complete. Phase 6 may begin.**

---

## PHASE 6 — ORCHESTRATION, AUDITOR, SYNTHESIZER

### Milestone 6.1 — Full Pipeline Assembly

---

#### Sprint 6.1.1 — Parallel Orchestration Engine (Stage 2)

**Goal**: Build the workflow engine that runs all 10 domain agents in parallel with correct dependency ordering (per Architecture Section 3.1's flow and the cross-agent dependencies noted throughout Phase 4/5).

**Why this sprint exists**: Until now, agents have been tested individually with manually-supplied mock inputs from "upstream" agents. This sprint wires them into a real, automatically-sequenced pipeline.

**Dependencies**: All of Phase 4 and Phase 5.

**Files to create**: `/workflows/full_analysis_workflow.yaml`, `/backend/services/orchestration_engine.py`.

**Folder structure involved**: `/workflows/`, `/backend/services/`.

**APIs**: `POST /api/pipeline/stage2` — accepts a `run_id` (from a Stage 1 pass), executes all 10 agents respecting dependency order (e.g., Margin waits on Pricing + FB Ads; Creative Opportunity waits on Psychology + FB Ads; Risk waits on nearly everything), returns aggregated `AgentOutput[]`.

**Database changes**: Update `runs.status` transitions to reflect per-agent progress (e.g., a `run_agent_status` table tracking each agent's state within a run).

**Backend tasks**: Implement a queue-based (not synchronous-script) orchestration per the scalability note in Part A; implement retry/timeout handling per agent; implement partial-failure handling (if one agent fails, does the run still produce a partial report, flagged accordingly, or hard-stop? — recommend: partial report with the failed agent's pillar marked "Insufficient Data," consistent with Architecture Section 8's missing-data handling).

**Frontend tasks**: None yet.

**AI Agent tasks**: None new — orchestration only.

**Knowledge Base tasks**: None.

**Tests to write**: Full-pipeline integration test with all 10 agents running against a real test product; dependency-ordering test (confirm Margin genuinely waits for Pricing+FB Ads); partial-failure test (simulate one agent failing, confirm graceful degradation).

**Acceptance Criteria**: A real product run produces all 10 `AgentOutput`s in correct dependency order within a reasonable time (architecture targets under 3 minutes); partial failure degrades gracefully.

**Definition of Done**: Tests pass; timing is measured and documented (even if not yet optimized to the 3-minute target — that's a Phase 8 concern).

**Estimated complexity**: High (this is the most architecturally complex backend sprint in the project).

**Common mistakes to avoid**: Don't build this as a single synchronous script that will need re-architecture later — use a queue/async pattern from the start per Part A's scalability note.

**What must be reviewed before moving forward**: Reviewer traces through one real run's logs to confirm dependency ordering actually happened correctly (not just that outputs eventually all arrived).

> ### ✅ REVIEW GATE 6.1.1
> **Sprint 6.1.2 cannot start until this is signed off.**

---

#### Sprint 6.1.2 — Contradiction Auditor Agent

**Goal**: Build per Architecture Section 3.3 — the anti-hallucination cross-check layer.

**Why this sprint exists**: Named as a high-risk component in Part A; needs its own dedicated sprint and largest golden-set given its importance.

**Dependencies**: Sprint 6.1.1 (needs real multi-agent output sets to audit).

**Files to create**: `/agents/validation/contradiction_auditor_agent.yaml`, `/prompts/validation/contradiction_auditor_prompt.md`.

**Folder structure involved**: `/agents/validation/`, `/prompts/validation/`.

**APIs**: `run_contradiction_audit(agent_outputs[]) → AuditNotes` per Architecture Section 22.13's output shape.

**Database changes**: Add `audit_notes` storage (extend `agent_outputs` pattern or a dedicated table).

**Backend tasks**: Wire all 10 agent outputs into the auditor's context.

**Frontend tasks**: None.

**AI Agent tasks**: Implement per Architecture Section 3.3/22.13 — must flag contradictions, uncited claims, and confidence inconsistencies without generating new analysis.

**Knowledge Base tasks**: None (this agent reasons over outputs, not raw KB).

**Tests to write**: Large golden-set (this is explicitly flagged as needing the biggest test set in Part A) — include synthetic contradiction cases (e.g., Pricing says premium-viable, Saturation says price-race), synthetic uncited-claim cases, and clean-consistent cases that should produce zero false-positive flags.

**Acceptance Criteria**: Correctly flags all synthetic contradiction/uncited-claim cases; produces zero false positives on the clean-consistent cases.

**Definition of Done**: Tests pass with special attention to false-positive rate (an overly trigger-happy auditor is as bad as a useless one).

**Estimated complexity**: High (highest ambiguity of any agent in the system — expect iteration).

**Common mistakes to avoid**: Don't let this agent generate new analysis or opinions — its job is strictly to audit, not to re-score or add findings, per Architecture Section 3.3's explicit scope limit.

**What must be reviewed before moving forward**: Reviewer specifically checks false-positive rate on clean cases — this is the metric most likely to erode trust in the system if wrong.

> ### ✅ REVIEW GATE 6.1.2
> **Sprint 6.1.3 cannot start until this is signed off.**

---

#### Sprint 6.1.3 — Chief Analyst / Synthesizer Agent + Report Generation

**Goal**: Build per Architecture Section 19 — the final human-facing memo generator.

**Why this sprint exists**: This is the actual product output users see; must faithfully reflect the deterministic Scoring Engine's verdict, never override it.

**Dependencies**: Sprint 6.1.2 (audit notes), Sprint 2.1.4 (Scoring Engine).

**Files to create**: `/agents/synthesizer/chief_analyst_agent.yaml`, `/prompts/synthesizer/chief_analyst_prompt.md`, `/backend/services/report_generator.py`.

**Folder structure involved**: `/agents/synthesizer/`, `/prompts/synthesizer/`, `/backend/services/`.

**APIs**: `POST /api/pipeline/synthesize` — accepts `run_id`, runs Scoring Engine + Synthesizer, writes to `reports` table, returns the memo per Architecture Section 19's structure.

**Database changes**: None beyond existing `reports` table (Sprint 0.1.2).

**Backend tasks**: Call Scoring Engine (Phase 2) to get the authoritative verdict; pass verdict + all agent outputs + audit notes to Synthesizer; persist final report as immutable.

**Frontend tasks**: None yet (report JSON shape is now stable — Phase 7 can now safely begin in parallel).

**AI Agent tasks**: Implement per Architecture Section 19, with the explicit constraint that memo tone/content must match the Scoring Engine's verdict exactly — enforce this as a code-level check (e.g., a post-generation assertion that the memo's stated verdict field matches the Scoring Engine's verdict), not just a prompt instruction, since this is safety-critical to system trustworthiness.

**Knowledge Base tasks**: None new.

**Tests to write**: Golden-set covering GO/CONDITIONAL/NO-GO/vetoed report generation; specific test asserting memo verdict field always matches Scoring Engine verdict (automated check, not just prompt-trust); borderline-score memo test confirming the "sits right at the boundary" language appears per Architecture Section 19's edge case.

**Acceptance Criteria**: All golden-set memos are well-structured, verdict-consistent, and appropriately toned (direct, non-hype, per Architecture's explicit style requirement).

**Definition of Done**: Tests pass including the automated verdict-consistency assertion.

**Estimated complexity**: Medium–High.

**Common mistakes to avoid**: Do not rely solely on prompt instructions to keep the memo's verdict consistent with the Scoring Engine — add a hard code-level check that fails the run if the LLM's stated verdict text contradicts the deterministic verdict, since this is the exact kind of drift that would silently erode trust in the system over time.

**What must be reviewed before moving forward**: Reviewer checks tone quality (does it actually sound like a skeptical analyst, or does it read like marketing copy?) on the golden set — this is a qualitative gate, not just a technical one.

> ### ✅ REVIEW GATE 6.1.3
> **Sprint 6.1.4 cannot start until this is signed off.**

---

#### Sprint 6.1.4 — Full End-to-End Pipeline Integration Test

**Goal**: Run the entire pipeline (Discovery → Validation → 10 parallel agents → Auditor → Scoring → Synthesizer) against multiple real products and confirm system-wide correctness.

**Why this sprint exists**: This is the first point where the complete system, as designed in the architecture doc, actually runs as one unit.

**Dependencies**: All of Phases 1–6.

**Files to create**: `/tests/integration_tests/full_pipeline_e2e_test.py`, `/tests/integration_tests/e2e_fixtures/` (5–10 real product test cases spanning expected GO/CONDITIONAL/NO-GO outcomes).

**Folder structure involved**: `/tests/integration_tests/`.

**APIs**: `POST /api/pipeline/run` — single entry point orchestrating all stages end-to-end (wraps the previously separate stage1/stage2/synthesize endpoints into one convenience call, while keeping the granular endpoints available for debugging).

**Database changes**: None new.

**Backend tasks**: Implement the single-entry-point wrapper; ensure run-status tracking reflects all stages correctly for observability.

**Frontend tasks**: None yet.

**AI Agent tasks**: None new — integration only.

**Knowledge Base tasks**: None.

**Tests to write**: Full E2E test suite across the 5–10 fixture products; timing benchmark against the 3-minute target from Architecture Section 3.2; a stress test running several products concurrently to check for resource contention issues in the orchestration engine.

**Acceptance Criteria**: All fixture products produce complete, correct, verdict-consistent reports; timing is measured and documented even if not yet fully optimized.

**Definition of Done**: E2E suite passes in CI; this becomes the permanent regression suite guarding against future changes anywhere in the system.

**Estimated complexity**: Medium (mostly integration/observability work at this point, not new logic).

**Common mistakes to avoid**: Don't treat this as "just glue code" — this is where subtle cross-agent bugs (wrong data reaching the wrong agent, race conditions in parallel execution) actually surface for the first time.

**What must be reviewed before moving forward**: Full manual read-through of at least 2 generated end-to-end reports by the reviewer, product-owner-style, asking "would I trust this memo with real money?"

> ### ✅ REVIEW GATE 6.1.4
> **Phase 6 complete. This is the single most important gate in the whole roadmap — the system, as architected, now genuinely works end-to-end. Phase 7 (Frontend, which can have been developing in parallel against mock data since Sprint 6.1.3) and Phase 8 may now begin.**

---

## PHASE 7 — FRONTEND / DASHBOARD
*(Can begin as early as Sprint 6.1.3 once the report JSON shape is stable, developed against mock report data in parallel with Phase 6's later sprints.)*

### Milestone 7.1 — Report Viewer & Submission UI

---

#### Sprint 7.1.1 — Product Submission UI + Run Status

**Goal**: Build the UI for submitting a product and watching pipeline progress.

**Dependencies**: Sprint 0.1.2 (DB), Sprint 1.2.3 (Stage 1 API) — can be built against mocked Stage 2 status initially.

**Files to create**: `/frontend/pages/submit.tsx` (or equivalent), `/frontend/components/RunStatusTracker.tsx`.

**Folder structure involved**: `/frontend/pages/`, `/frontend/components/`.

**APIs**: Consumes `/api/discover`, `/api/pipeline/stage1`, and a polling or websocket endpoint for run status.

**Database changes**: None.

**Backend tasks**: Expose a `GET /api/runs/{id}/status` endpoint if not already present from Sprint 6.1.1's per-agent status tracking.

**Frontend tasks**: Build submission form (text/URL/image input matching Discovery Agent's 3 input modes); build a live-updating status view showing each of the 10 agents' progress.

**AI Agent tasks**: None.

**Knowledge Base tasks**: None.

**Tests to write**: Component tests for the form and status tracker; a mocked-API integration test.

**Acceptance Criteria**: User can submit a product via any of the 3 input modes and see live progress through the pipeline stages.

**Definition of Done**: Tests pass; manual UX review confirms status updates are clear and non-confusing.

**Estimated complexity**: Medium.

**Common mistakes to avoid**: Don't let the UI imply false precision on progress (e.g., a fake progress bar) — reflect actual per-agent status per Architecture's honesty-first philosophy.

**What must be reviewed before moving forward**: UX review for clarity and honesty of status representation.

> ### ✅ REVIEW GATE 7.1.1

---

#### Sprint 7.1.2 — Investment Memo Report Viewer

**Goal**: Build the UI that renders the final Investment Memo per Architecture Section 19's structure.

**Dependencies**: Sprint 6.1.3 (stable report JSON shape), Sprint 7.1.1.

**Files to create**: `/frontend/pages/report/[id].tsx`, `/frontend/components/InvestmentMemo.tsx`, `/frontend/components/PillarBreakdown.tsx`.

**Folder structure involved**: `/frontend/pages/`, `/frontend/components/`.

**APIs**: `GET /api/reports/{id}`.

**Database changes**: None.

**Backend tasks**: Expose the report-fetch endpoint if not already present.

**Frontend tasks**: Render verdict banner (color-coded GO/CONDITIONAL/NO-GO), executive summary, pillar-by-pillar breakdown with evidence citations visible/expandable, risks/conditions section, recommended budget/angles (if GO).

**AI Agent tasks**: None.

**Knowledge Base tasks**: None.

**Tests to write**: Component tests rendering all 3 verdict states correctly; snapshot test against real Sprint 6.1.4 fixture reports.

**Acceptance Criteria**: All 3 verdict types render correctly and clearly; evidence/citations are genuinely inspectable, not just summarized away (matches Architecture's "every score must be explainable" principle).

**Definition of Done**: Tests pass; manual review confirms the report reads as trustworthy and non-hype in the UI, not just in the underlying text.

**Estimated complexity**: Medium.

**Common mistakes to avoid**: Don't bury the confidence level or data-completeness caveats in fine print — architecture requires these be surfaced prominently, especially for low-confidence results.

**What must be reviewed before moving forward**: Design/UX review specifically checking that low-confidence and NO-GO results are NOT visually de-emphasized relative to GO results (a subtle bias risk in dashboard design).

> ### ✅ REVIEW GATE 7.1.2

---

#### Sprint 7.1.3 — Historical Runs Dashboard

**Goal**: Build a dashboard listing past runs/reports for a user, supporting the re-analysis comparison feature noted in Architecture Section 22.15.

**Dependencies**: Sprint 7.1.2.

**Files to create**: `/frontend/pages/dashboard.tsx`, `/frontend/components/RunHistoryTable.tsx`.

**Folder structure involved**: `/frontend/pages/`, `/frontend/components/`.

**APIs**: `GET /api/reports?user_id=...` (list), plus a comparison endpoint if re-analysis diffing is included in this sprint's scope (can be deferred to a later iteration if time-boxed).

**Database changes**: None beyond existing schema (reports are already immutable/versioned per Sprint 0.1.2's design).

**Backend tasks**: Implement list/filter endpoint.

**Frontend tasks**: Build sortable/filterable history table; link each row to its Sprint 7.1.2 report view.

**AI Agent tasks**: None.

**Knowledge Base tasks**: None.

**Tests to write**: Component test for table rendering and filtering.

**Acceptance Criteria**: User can view all past runs and open any historical report.

**Definition of Done**: Tests pass.

**Estimated complexity**: Low–Medium.

**Common mistakes to avoid**: Don't allow past reports to be edited/overwritten from this view — immutability must hold throughout the UI, not just the database.

**What must be reviewed before moving forward**: Confirm no edit/delete path exists for historical reports.

> ### ✅ REVIEW GATE 7.1.3
> **Phase 7 complete.**

---

## PHASE 8 — HARDENING & RELEASE

### Milestone 8.1 — Testing, Calibration & Launch

---

#### Sprint 8.1.1 — Regression Suite Expansion + Backtesting

**Goal**: Expand test coverage and backtest the Scoring Engine's weights against real historical winner/loser products, per Part A's named risk about weight calibration.

**Dependencies**: Sprint 6.1.4 (full E2E pipeline).

**Files to create**: `/tests/regression_tests/backtest_suite.py`, `/knowledge/market/winning_products.md` updated with backtest findings (feedback loop into the KB itself).

**Folder structure involved**: `/tests/regression_tests/`, `/knowledge/market/`.

**APIs**: None new.

**Database changes**: None.

**Backend tasks**: Run the full pipeline against a curated set of 20–30 historically known winning and losing products; compare system verdicts against known real-world outcomes.

**Frontend tasks**: None.

**AI Agent tasks**: None new — this sprint evaluates existing agents, doesn't build new ones.

**Knowledge Base tasks**: Update `winning_products.md` and `product_scoring.md` with any calibration findings (document as a versioned changelog entry, not a silent edit).

**Tests to write**: The backtest suite itself, run as a scheduled (not necessarily per-PR) CI job given its cost/time.

**Acceptance Criteria**: System verdicts align directionally with known historical outcomes for the majority of the backtest set; documented discrepancies are analyzed and either explained or used to propose a weight adjustment (which itself requires a Review Gate before being applied, since it changes the Scoring Engine's behavior).

**Definition of Done**: Backtest report produced; any proposed weight changes go through the same Scoring Engine review rigor as Sprint 2.1.2/2.1.3.

**Estimated complexity**: Medium–High (mostly analysis effort, not new code).

**Common mistakes to avoid**: Don't silently tweak weights based on backtest results without documenting why — treat any weight change as a versioned, reviewed decision, per Architecture Section 8's "Possible Improvements" note about calibration.

**What must be reviewed before moving forward**: Any proposed weight changes require the same "independently re-derive the math" review as the original Scoring Engine sprints.

> ### ✅ REVIEW GATE 8.1.1

---

#### Sprint 8.1.2 — Performance, Caching & Load Testing

**Goal**: Optimize toward the architecture's 3-minute end-to-end target and confirm the system handles concurrent product runs.

**Dependencies**: Sprint 6.1.4.

**Files to create**: `/tests/integration_tests/load_test.py`, caching-tuning config updates across `/backend/integrations/`.

**Folder structure involved**: `/tests/integration_tests/`, `/backend/integrations/`.

**Backend tasks**: Profile the orchestration engine and integrations for bottlenecks (likely candidates: Amazon scraping, LLM call latency for the 10 parallel agents); tune cache TTLs; consider batching/parallelization improvements within the queue-based engine from Sprint 6.1.1.

**Frontend tasks**: None.

**AI Agent tasks**: None new.

**Knowledge Base tasks**: None.

**Tests to write**: Load test simulating 5–10 concurrent product runs; latency benchmark test against the 3-minute target.

**Acceptance Criteria**: System handles realistic concurrent load without failures; latency is measured and either meets target or has a documented, justified gap.

**Definition of Done**: Load test passes; performance report documented.

**Estimated complexity**: Medium–High.

**Common mistakes to avoid**: Don't sacrifice the "insufficient data" honesty flags for speed (e.g., don't skip retries in a way that silently degrades data quality just to hit a time target).

**What must be reviewed before moving forward**: Reviewer confirms no correctness/honesty tradeoffs were made purely for speed.

> ### ✅ REVIEW GATE 8.1.2

---

#### Sprint 8.1.3 — Production Release & Monitoring

**Goal**: Ship v1.0 to production with monitoring and a rollback plan.

**Dependencies**: Sprints 8.1.1, 8.1.2.

**Files to create**: `/docs/release_notes/v1.0.md`, monitoring/alerting config (error rates per agent, integration failure rates, veto-trigger rates for anomaly detection).

**Folder structure involved**: `/docs/release_notes/`.

**Backend tasks**: Deploy to production environment; wire monitoring/alerting per agent and per integration.

**Frontend tasks**: Deploy production build.

**AI Agent tasks**: None new.

**Knowledge Base tasks**: Final freshness audit — confirm every KB file's `last_updated` date is recent/reviewed before launch.

**Tests to write**: Production smoke test (health checks across all services).

**Acceptance Criteria**: Production deployment succeeds; monitoring dashboards show healthy baseline metrics; rollback procedure is documented and has been dry-run tested.

**Definition of Done**: v1.0 is live; release notes published; monitoring is actively watched for the first 48 hours per the release strategy (Part C).

**Estimated complexity**: Medium.

**Common mistakes to avoid**: Don't launch without a tested rollback path — given this system makes financial recommendations, a silent bug in production is a real-money-impacting risk, not just an inconvenience.

**What must be reviewed before moving forward**: Final go/no-go release review — literally applying the product's own "GO/NO-GO" philosophy to itself.

> ### ✅ REVIEW GATE 8.1.3
> **v1.0 shipped. Project roadmap complete.**

---

# PART C — SUPPORTING STRATEGIES

## 1. Complete Development Roadmap (Summary Table)

| Phase | Focus | Can Run in Parallel With |
|---|---|---|
| 0 | Foundation (repo, DB, CI) | — |
| 1 | Discovery & Validation Gate | — |
| 2 | Scoring Engine Core | Phase 3 |
| 3 | Knowledge Base | Phase 2, Phase 4 (partially) |
| 4 | High-signal Agents (FB Ads, Amazon, Pricing, Margin) | Phase 3 |
| 5 | Remaining Agents (Saturation, Competitor, TikTok, Psychology, Creative, Risk) | Sub-milestones 5.1/5.2/5.3 parallel to each other |
| 6 | Orchestration, Auditor, Synthesizer | — (critical path convergence point) |
| 7 | Frontend | Late Phase 6 onward |
| 8 | Hardening & Release | — |

## 2. Build Order (Condensed Critical Path)
1. Repo/DB/CI → 2. ProductIdentity + Discovery → 3. Validation Gate → 4. Agent Output Contract → 5. Scoring Engine (math, vetoes, confidence) → 6. Base Integration Pattern → 7. FB Ads + Amazon integrations → 8. FB Ads Agent + Review Agent → 9. Pricing + Margin Agents → 10. Remaining 6 agents (parallelizable) → 11. Orchestration Engine → 12. Contradiction Auditor → 13. Synthesizer → 14. Full E2E test → 15. Frontend → 16. Hardening → 17. Release.

## 3. Git Commit Strategy
- **Conventional Commits format**: `feat(agent-fb-ads): implement angle clustering`, `fix(scoring): correct veto override precedence`, `docs(knowledge): update pricing.md thresholds`, `test(scoring): add borderline golden-set case`.
- **One sprint = one or more small, reviewable commits**, never one giant commit per sprint — each commit should be independently understandable.
- Any change to `/scoring` or `/knowledge/scoring/product_scoring.md` must reference the corresponding Review Gate in the commit message (e.g., `feat(scoring): implement composite score [Sprint 2.1.2, Gate 2.1.2]`).
- KB content commits should include the file's changelog update in the same commit — never update content without updating its `last_updated` header.

## 4. Branch Strategy
- `main` — always production-deployable, protected, requires CI pass + review approval.
- `develop` — integration branch where completed, gate-passed sprints merge before a release cut.
- `sprint/{phase}.{milestone}.{sprint}-{short-name}` branches for each sprint (e.g., `sprint/4.2.4-margin-agent`) — one branch per sprint, merged into `develop` only after its Review Gate passes.
- `hotfix/*` branches off `main` for production issues post-release, per Sprint 8.1.3.
- No sprint branch is merged out of order relative to its stated dependencies — this mirrors the "nothing depends on unbuilt code" rule structurally in git history, not just in planning.

## 5. Folder-by-Folder Implementation Order
1. `/docs`, `/database`, `/tests` scaffolding (Phase 0)
2. `/backend` core services + `/database` schema (Phase 0–1)
3. `/scoring` (Phase 2) — built in isolation, testable without any agent
4. `/knowledge` (Phase 3) — built in parallel to `/scoring`
5. `/backend/integrations` (Phase 4.1) then `/agents` + `/prompts` per-agent (Phase 4.2–5.3)
6. `/workflows` (Phase 6) — ties `/agents`, `/scoring`, `/knowledge` together
7. `/frontend` (Phase 7) — last major folder, built against stable JSON contracts
8. `/reports` — populated automatically from Phase 6 onward, no manual folder work needed

## 6. Testing Strategy
- **Unit tests** for every deterministic function (Scoring Engine, veto rules, confidence calculator) — highest rigor, hand-verified by reviewers.
- **Golden-set tests** for every AI agent — human-reviewed for qualitative reasoning quality, not just schema conformance; this is non-negotiable per-agent given the system's trust-critical nature.
- **Integration tests** at each pipeline stage boundary (Stage 1, Stage 2, full E2E) — catches cross-component wiring bugs.
- **Regression tests** (Phase 8) — protect against silent drift when KB files, prompts, or weights are updated post-launch.
- **Backtests** against real historical products — the only test category that validates the system against ground truth outcomes rather than internal consistency.
- Test pyramid emphasis: given this is an AI-reasoning-heavy system, invest disproportionately in golden-set and backtest quality relative to a typical CRUD app — these catch the failure modes that actually matter here (bad reasoning, not broken code).

## 7. Release Strategy
- **v0.x internal releases** after each Phase completes (0.1 after Phase 1, 0.2 after Phase 2/3, etc.) — deployed to a staging environment only, never public.
- **v1.0** ships only after Phase 8 is fully complete, including backtesting and load testing — no shortcuts given the system's financial-decision-making nature.
- **Post-launch monitoring window**: first 48 hours actively watched per Sprint 8.1.3, with a pre-tested rollback plan ready to execute if veto-trigger rates or agent error rates look anomalous compared to backtest baselines.
- **Weight/KB recalibration releases** (v1.1+) are treated as their own mini-release cycle: proposal → backtest validation → Review Gate → versioned changelog entry → release — never a silent hotfix, since these changes affect the core trustworthiness of every future report.
