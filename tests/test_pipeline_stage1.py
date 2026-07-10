"""Integration tests for POST /api/pipeline/stage1 (all modes mocked, CI-safe).

Three required scenarios from Sprint 1.2.3 spec:
  1. Valid clean product → passes both stages, proceed_to_analysis: true
  2. Blocked-category product → stops at validation with compliance flag,
     proceed_to_analysis: false
  3. Unidentifiable/garbage input → stops at discovery, never reaches validation

Additional coverage:
  - LLM error during validation → proceed_to_analysis: false (fail-safe)
  - Niche-shortlist mode → per-candidate validation
  - Run status tracking in DB
"""

import os

import httpx
import pytest
from httpx import ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.schemas.product_identity import ProductIdentity
from app.schemas.validation_result import ValidationJudgment


@pytest.fixture(name="db_session")
async def db_session_fixture():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        db_url = "sqlite+aiosqlite://"
    engine = create_async_engine(db_url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
def override_get_db(db_session):
    async def _override():
        yield db_session
    app.dependency_overrides[get_db] = _override
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def mock_validation_clean(monkeypatch):
    """LLM judgment that clears the product."""
    async def mock_judgment(*args, **kwargs):
        return ValidationJudgment(
            is_flagged=False, flags=[],
            reasoning="No compliance issues detected.",
        )
    monkeypatch.setattr(
        "app.api.pipeline_stage1.run_validation_judgment", mock_judgment
    )
    yield


@pytest.fixture
def mock_validation_blocked(monkeypatch):
    """LLM judgment that flags the product."""
    async def mock_judgment(*args, **kwargs):
        return ValidationJudgment(
            is_flagged=True, flags=["dietary_supplement"],
            reasoning="Dietary supplements are restricted on both platforms.",
        )
    monkeypatch.setattr(
        "app.api.pipeline_stage1.run_validation_judgment", mock_judgment
    )
    yield


@pytest.fixture
def mock_discovery_clean(monkeypatch):
    """Discovery agent returns a clean kitchen product."""
    async def mock_analyze(*args, **kwargs):
        return ProductIdentity(
            name="Cotton Kitchen Apron",
            category="Kitchen Tools & Accessories",
            subcategory="Aprons",
            normalized_keywords=["kitchen apron", "cooking"],
        )
    monkeypatch.setattr(
        "app.api.pipeline_stage1.analyze_product", mock_analyze
    )
    yield


@pytest.fixture
def mock_discovery_blocked(monkeypatch):
    """Discovery agent returns a supplement (will be caught by validation)."""
    async def mock_analyze(*args, **kwargs):
        return ProductIdentity(
            name="Whey Protein Powder",
            category="Dietary Supplements",
            subcategory="Protein Powders",
            normalized_keywords=["protein", "muscle recovery"],
        )
    monkeypatch.setattr(
        "app.api.pipeline_stage1.analyze_product", mock_analyze
    )
    yield


@pytest.fixture
def mock_discovery_fail(monkeypatch):
    """Discovery agent raises an exception (unidentifiable input)."""
    async def mock_analyze(*args, **kwargs):
        raise RuntimeError("Could not identify product from input")
    monkeypatch.setattr(
        "app.api.pipeline_stage1.analyze_product", mock_analyze
    )
    yield


@pytest.fixture
def mock_niche_shortlist(monkeypatch):
    """Niche discovery returns multiple candidates."""
    async def mock_niche(*args, **kwargs):
        return [
            ProductIdentity(
                name="Eco-Friendly Bamboo Toothbrush",
                category="Kitchen Tools & Accessories",
                subcategory="Kitchen Utensils",
                normalized_keywords=["bamboo toothbrush", "eco-friendly"],
            ),
            ProductIdentity(
                name="Reusable Silicone Food Bags",
                category="Kitchen Tools & Accessories",
                subcategory="Food Storage",
                normalized_keywords=["silicone bags", "reusable storage"],
            ),
        ]
    monkeypatch.setattr(
        "app.api.pipeline_stage1.analyze_niche_shortlist", mock_niche
    )
    yield


class TestPipelineStage1:
    """Three required scenarios + edge cases."""

    async def _post(self, payload: dict) -> httpx.Response:
        async with httpx.AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            return await client.post("/api/pipeline/stage1", json=payload)

    # ── Scenario 1: Valid clean product ────────────────────────────────────

    @pytest.mark.asyncio
    async def test_scenario1_clean_product_passes(
        self, override_get_db, mock_discovery_clean, mock_validation_clean
    ):
        """A clean kitchen product should pass both stages with proceed_to_analysis=true."""
        resp = await self._post({
            "input_type": "text",
            "value": "cotton kitchen apron",
        })
        assert resp.status_code == 200
        data = resp.json()

        assert data["proceed_to_analysis"] is True, (
            f"Clean product should proceed, got: {data}"
        )
        assert data["status"] == "validation_complete"
        assert data["input_type"] == "text"
        assert data["identity"]["name"] == "Cotton Kitchen Apron"
        assert data["validation"] is not None
        assert data["validation"]["is_valid"] is True
        assert len(data["validation"]["compliance_flags"]) == 0
        assert data["run_id"] is not None
        assert data["error"] is None

    # ── Scenario 2: Blocked-category product ───────────────────────────────

    @pytest.mark.asyncio
    async def test_scenario2_blocked_product_stops_at_validation(
        self, override_get_db, mock_discovery_blocked, mock_validation_blocked
    ):
        """A blocked supplement should fail validation with proceed_to_analysis=false
        and include the compliance flag."""
        resp = await self._post({
            "input_type": "text",
            "value": "whey protein",
        })
        assert resp.status_code == 200
        data = resp.json()

        assert data["proceed_to_analysis"] is False, (
            f"Blocked product must NOT proceed, got: {data}"
        )
        assert data["status"] == "validation_complete"
        assert data["identity"]["name"] == "Whey Protein Powder"
        assert data["validation"] is not None
        assert data["validation"]["is_valid"] is False
        assert len(data["validation"]["compliance_flags"]) > 0
        first_flag = data["validation"]["compliance_flags"][0]
        assert "Dietary Supplements" in first_flag["rule"]
        assert data["run_id"] is not None
        assert data["error"] is None

    # ── Scenario 3: Unidentifiable / garbage input ─────────────────────────

    @pytest.mark.asyncio
    async def test_scenario3_garbage_input_stops_at_discovery(
        self, override_get_db, mock_discovery_fail
    ):
        """An unidentifiable input should fail at discovery and never reach validation."""
        resp = await self._post({
            "input_type": "text",
            "value": "asdfghjkl123",
        })
        assert resp.status_code == 200
        data = resp.json()

        assert data["proceed_to_analysis"] is False
        assert data["status"] == "failed_at_discovery"
        assert data["error"] is not None
        assert "Could not identify product" in data["error"]
        # These should be absent since discovery never completed
        assert data["identity"] is None
        assert data["validation"] is None
        assert data["run_id"] is None

    # ── Edge case: LLM error during validation (fail-safe) ─────────────────

    @pytest.mark.asyncio
    async def test_validation_llm_error_defaults_to_no_go(
        self, override_get_db, mock_discovery_clean, monkeypatch
    ):
        """If the LLM call fails, validation defaults to a hard no-go."""

        async def mock_llm_crash(*args, **kwargs):
            raise RuntimeError("API unavailable")

        monkeypatch.setattr(
            "app.api.pipeline_stage1.run_validation_judgment", mock_llm_crash
        )

        resp = await self._post({
            "input_type": "text",
            "value": "cotton kitchen apron",
        })
        assert resp.status_code == 200
        data = resp.json()

        assert data["proceed_to_analysis"] is False, (
            f"LLM crash must result in no-go, got: {data}"
        )
        assert data["status"] == "failed_at_validation"
        assert data["error"] is not None
        assert "API unavailable" in data["error"]

    # ── Niche-shortlist mode ───────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_niche_shortlist_validates_each_candidate(
        self, override_get_db, mock_niche_shortlist, mock_validation_clean
    ):
        """Niche-shortlist validates each candidate independently."""
        resp = await self._post({
            "input_type": "niche_query",
            "value": "eco-friendly kitchen products",
        })
        assert resp.status_code == 200
        data = resp.json()

        assert data["status"] == "validation_complete"
        assert data["input_type"] == "niche_query"
        assert data["candidates"] is not None
        assert len(data["candidates"]) == 2

        for c in data["candidates"]:
            assert c["identity"]["name"]
            assert c["validation"] is not None
            assert c["validation"]["is_valid"] is True
            assert c["proceed_to_analysis"] is True

        # No single identity/validation at top level for niche mode
        assert data["identity"] is None
        assert data["validation"] is None
        assert data["run_id"] is None  # niche does not persist

    # ── Niche shortlist with mixed validation results ──────────────────────

    @pytest.mark.asyncio
    async def test_niche_shortlist_mixed_results(
        self, override_get_db, mock_niche_shortlist, monkeypatch
    ):
        """If some candidates fail validation, only those have proceed_to_analysis=false."""

        call_count = 0

        async def conditional_judgment(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            # First candidate passes, second fails
            if call_count == 1:
                return ValidationJudgment(
                    is_flagged=False, flags=[], reasoning="Clean."
                )
            else:
                return ValidationJudgment(
                    is_flagged=True, flags=["health_claim"],
                    reasoning="Flagged.",
                )

        monkeypatch.setattr(
            "app.api.pipeline_stage1.run_validation_judgment", conditional_judgment
        )

        resp = await self._post({
            "input_type": "niche_query",
            "value": "some niche",
        })
        assert resp.status_code == 200
        data = resp.json()

        assert data["candidates"] is not None
        assert len(data["candidates"]) == 2

        # First passes, second fails
        assert data["candidates"][0]["proceed_to_analysis"] is True
        assert data["candidates"][0]["validation"]["is_valid"] is True

        assert data["candidates"][1]["proceed_to_analysis"] is False
        assert data["candidates"][1]["validation"]["is_valid"] is False

        # Overall proceed_to_analysis is true (at least one candidate is valid)
        assert data["proceed_to_analysis"] is True

    # ── Run status is queryable ────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_run_status_persisted_correctly(
        self, override_get_db, db_session, mock_discovery_clean, mock_validation_clean
    ):
        """After a successful pipeline run, the run and agent outputs exist in DB."""
        resp = await self._post({
            "input_type": "text",
            "value": "cotton kitchen apron",
        })
        assert resp.status_code == 200
        data = resp.json()
        run_id = data["run_id"]
        assert run_id is not None

        from app.models import AgentOutput, Run
        from sqlalchemy import select

        # Check run exists and has correct status
        run = await db_session.get(Run, run_id)
        assert run is not None
        assert run.status.value == "validation_complete"

        # Check agent outputs exist for both stages
        result = await db_session.execute(
            select(AgentOutput).where(AgentOutput.run_id == run_id)
        )
        outputs = result.scalars().all()
        agent_names = {o.agent_name for o in outputs}
        assert "discovery_agent" in agent_names
        assert "validation_agent" in agent_names
