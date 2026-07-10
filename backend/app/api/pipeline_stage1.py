import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.discovery_agent import analyze_product, analyze_product_image, analyze_niche_shortlist
from app.agents.validation_agent import run_validation_judgment
from app.database import get_db
from app.schemas.product_identity import ProductIdentity
from app.schemas.validation_result import (
    ComplianceFlag,
    SupplierAvailability,
    ValidationResult,
    ValidationJudgment,
)
from app.services.compliance_checker import check_compliance
from app.services.db_service import create_agent_output, create_run, update_run_status
from app.services.product_identity_service import create_product_identity
from integrations.product_page_scraper import scrape_product_page
from integrations.supplier_client import fetch_supplier_data as fetch_supplier

logger = logging.getLogger("pipeline_stage1")

router = APIRouter()


class Stage1Request(BaseModel):
    input_type: str = Field(..., pattern="^(text|url|image|niche_query)$")
    value: str = Field(..., min_length=1)


class CandidateResult(BaseModel):
    identity: ProductIdentity
    validation: ValidationResult | None = None
    proceed_to_analysis: bool = False


class Stage1Response(BaseModel):
    run_id: int | None = None
    status: str
    input_type: str
    identity: ProductIdentity | None = None
    validation: ValidationResult | None = None
    candidates: list[CandidateResult] | None = None
    proceed_to_analysis: bool = False
    error: str | None = None


async def _validate_product(product: ProductIdentity) -> ValidationResult:
    """Run the full validation gate for a single ProductIdentity.

    Calls the same underlying services as POST /api/validate
    (deterministic blocklist, LLM gray-area judgment, supplier check).
    """
    compliance_result = check_compliance(product)
    compliance_flags = [
        ComplianceFlag(
            rule=r["rule"],
            matched_categories=r.get("matched_categories", []),
            matched_subcategories=r.get("matched_subcategories", []),
            matched_keywords=r.get("matched_keywords", []),
        )
        for r in compliance_result.matched_rules
    ]

    try:
        judgment = await run_validation_judgment(product)
    except Exception as e:
        logger.warning("LLM judgment failed: %s", e)
        raise RuntimeError(f"Validation service error: {e}") from e

    try:
        supplier_data = await fetch_supplier(product.name, product.category)
        supplier_avail = (
            SupplierAvailability(
                in_stock=supplier_data.in_stock,
                moq=supplier_data.moq,
                shipping_days=supplier_data.shipping_days,
                supplier_rating=supplier_data.supplier_rating,
                source=supplier_data.source,
            )
            if supplier_data
            else None
        )
    except Exception:
        supplier_avail = None

    deterministic_flagged = compliance_result.flagged
    llm_flagged = judgment.is_flagged
    any_compliance_flag = deterministic_flagged or llm_flagged
    is_valid = not any_compliance_flag

    requires_manual_review = judgment.reasoning and "manual" in judgment.reasoning.lower()
    if llm_flagged and not deterministic_flagged:
        requires_manual_review = True

    return ValidationResult(
        is_valid=is_valid,
        is_saleable_on_meta=is_valid,
        is_saleable_on_tiktok=is_valid,
        compliance_flags=compliance_flags,
        llm_judgment=judgment,
        supplier_availability=supplier_avail,
        requires_manual_review=requires_manual_review,
    )


@router.post("/api/pipeline/stage1", response_model=Stage1Response)
async def pipeline_stage1(req: Stage1Request, db: AsyncSession = Depends(get_db)):
    # ── Niche-shortlist path (no DB persistence — user hasn't selected a product) ──
    if req.input_type == "niche_query":
        try:
            candidates = await analyze_niche_shortlist(req.value)
        except Exception as e:
            logger.error("Niche discovery failed: %s", e)
            return Stage1Response(
                status="failed_at_discovery",
                input_type="niche_query",
                error=f"Discovery failed: {e}",
                proceed_to_analysis=False,
            )

        results: list[CandidateResult] = []
        for c in candidates:
            try:
                val = await _validate_product(c)
                proceed = val.is_valid
            except Exception as e:
                logger.warning("Validation failed for niche candidate '%s': %s", c.name, e)
                val = None
                proceed = False

            results.append(
                CandidateResult(identity=c, validation=val, proceed_to_analysis=proceed)
            )

        any_valid = any(r.proceed_to_analysis for r in results)
        return Stage1Response(
            status="validation_complete",
            input_type="niche_query",
            candidates=results,
            proceed_to_analysis=any_valid,
        )

    # ── Single-product path (text / url / image) ──

    # Step 1 — Discovery
    try:
        if req.input_type == "image":
            identity = await analyze_product_image(req.value)
            scraped_data = None
        else:
            scraped_data = None
            if req.input_type == "url":
                try:
                    page = await scrape_product_page(req.value)
                    scraped_data = {
                        "title": page.title,
                        "price": page.price,
                        "images": page.images,
                        "description": page.description,
                        "variants": page.variants,
                        "html_text": page.html_text[:5000],
                    }
                except Exception:
                    scraped_data = None

            identity = await analyze_product(
                input_type=req.input_type,
                value=req.value,
                scraped_data=scraped_data,
            )
    except Exception as e:
        logger.error("Discovery failed for input '%s': %s", req.value, e)
        return Stage1Response(
            status="failed_at_discovery",
            input_type=req.input_type,
            error=f"Discovery failed: {e}",
            proceed_to_analysis=False,
        )

    # Step 2 — Persist product and create run
    try:
        product = await create_product_identity(db, identity)
    except Exception as e:
        logger.error("Failed to persist product identity: %s", e)
        return Stage1Response(
            status="failed_at_discovery",
            input_type=req.input_type,
            error=f"Failed to persist product: {e}",
            proceed_to_analysis=False,
        )

    try:
        run = await create_run(db, product_id=product.id)
        run_id = run.id
    except Exception as e:
        logger.error("Failed to create run: %s", e)
        run_id = None

    if run_id:
        await update_run_status(db, run_id, "discovery_complete")

    # Step 3 — Validation
    try:
        validation = await _validate_product(identity)
    except Exception as e:
        logger.error("Validation failed for product '%s': %s", identity.name, e)
        if run_id:
            await update_run_status(db, run_id, "failed_at_validation")
        return Stage1Response(
            run_id=run_id,
            status="failed_at_validation",
            input_type=req.input_type,
            identity=identity,
            error=f"Validation failed: {e}",
            proceed_to_analysis=False,
        )

    proceed = validation.is_valid

    # Step 4 — Store agent outputs
    if run_id:
        try:
            await create_agent_output(
                db, run_id=run_id, agent_name="discovery_agent",
                output_json=identity.model_dump(),
            )
            await create_agent_output(
                db, run_id=run_id, agent_name="validation_agent",
                output_json=validation.model_dump(),
            )
            await update_run_status(db, run_id, "validation_complete")
        except Exception as e:
            logger.warning("Failed to persist agent outputs: %s", e)

    return Stage1Response(
        run_id=run_id,
        status="validation_complete",
        input_type=req.input_type,
        identity=identity,
        validation=validation,
        proceed_to_analysis=proceed,
    )
