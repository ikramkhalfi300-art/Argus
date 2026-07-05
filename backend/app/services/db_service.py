from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AgentOutput, Confidence, Product, Report, Run


# --- Products ---

async def create_product(db: AsyncSession, *, name, category, subcategory, normalized_keywords=None, source_url=None):
    obj = Product(
        name=name,
        category=category,
        subcategory=subcategory,
        normalized_keywords=normalized_keywords or [],
        source_url=source_url,
    )
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


async def get_product(db: AsyncSession, product_id: int):
    return await db.get(Product, product_id)


async def list_products(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(Product).offset(skip).limit(limit))
    return result.scalars().all()


# --- Runs ---

async def create_run(db: AsyncSession, *, product_id: int):
    obj = Run(product_id=product_id)
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


async def get_run(db: AsyncSession, run_id: int):
    return await db.get(Run, run_id)


async def list_runs(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(Run).offset(skip).limit(limit))
    return result.scalars().all()


# --- Agent Outputs ---

async def create_agent_output(db: AsyncSession, *, run_id: int, agent_name: str, output_json=None, confidence=None):
    obj = AgentOutput(
        run_id=run_id,
        agent_name=agent_name,
        output_json=output_json or {},
        confidence=confidence,
    )
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


async def get_agent_output(db: AsyncSession, agent_output_id: int):
    return await db.get(AgentOutput, agent_output_id)


async def list_agent_outputs(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(AgentOutput).offset(skip).limit(limit))
    return result.scalars().all()


# --- Reports (INSERT-ONLY — no update, no delete) ---

async def create_report(db: AsyncSession, *, run_id: int, verdict: str, composite_score: float, memo_json=None):
    obj = Report(
        run_id=run_id,
        verdict=verdict,
        composite_score=composite_score,
        memo_json=memo_json or {},
    )
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


async def get_report(db: AsyncSession, report_id: int):
    return await db.get(Report, report_id)


async def list_reports(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(Report).offset(skip).limit(limit))
    return result.scalars().all()
