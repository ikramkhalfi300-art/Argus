import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("validate_api")

from app.agents.validation_agent import run_validation_judgment
from app.database import get_db
from app.schemas.product_identity import ProductIdentity
from app.schemas.validation_result import (
    ComplianceFlag,
    SupplierAvailability,
    ValidationJudgment,
    ValidationResult,
)
from app.services.compliance_checker import check_compliance
from app.services.db_service import create_agent_output
from integrations.supplier_client import fetch_supplier_data as fetch_supplier

router = APIRouter()


class ValidateRequest(BaseModel):
    product: ProductIdentity


@router.post("/api/validate", response_model=ValidationResult)
async def validate(req: ValidateRequest, db: AsyncSession = Depends(get_db)):
    product = req.product

    # Step 1: deterministic compliance check (Sprint 1.2.1)
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

    # Step 2: LLM gray-area judgment
    try:
        judgment = await run_validation_judgment(product)
    except Exception as e:
        logger.warning("LLM judgment failed, defaulting to manual review: %s", e)
        judgment = ValidationJudgment(
            is_flagged=True,
            flags=["llm_error"],
            reasoning="LLM judgment unavailable — requires manual legal review",
        )

    # Step 3: supplier check (mock)
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

    # Step 4: combine into result
    deterministic_flagged = compliance_result.flagged
    llm_flagged = judgment.is_flagged

    any_compliance_flag = deterministic_flagged or llm_flagged
    is_valid = not any_compliance_flag

    # Edge case: policy ambiguity defaults to Requires Manual Legal Review
    requires_manual_review = judgment.reasoning and "manual" in judgment.reasoning.lower()

    if llm_flagged and not deterministic_flagged:
        requires_manual_review = True

    result = ValidationResult(
        is_valid=is_valid,
        is_saleable_on_meta=is_valid,
        is_saleable_on_tiktok=is_valid,
        compliance_flags=compliance_flags,
        llm_judgment=judgment,
        supplier_availability=supplier_avail,
        requires_manual_review=requires_manual_review,
    )

    # Step 5: store as agent_output
    try:
        await create_agent_output(
            db,
            run_id=0,
            agent_name="validation_agent",
            output_json=result.model_dump(),
        )
    except Exception:
        pass

    return result
