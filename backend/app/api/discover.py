from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.discovery_agent import analyze_product
from app.database import get_db
from integrations.product_page_scraper import scrape_product_page
from app.schemas.product_identity import ProductIdentity
from app.services.product_identity_service import create_product_identity

router = APIRouter()


class DiscoverRequest(BaseModel):
    input_type: str = Field(..., pattern="^(text|url)$")
    value: str = Field(..., min_length=1)


class DiscoverResponse(BaseModel):
    id: int
    identity: ProductIdentity


@router.post("/api/discover", response_model=DiscoverResponse)
async def discover(req: DiscoverRequest, db: AsyncSession = Depends(get_db)):
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

    product = await create_product_identity(db, identity)
    return DiscoverResponse(id=product.id, identity=identity)
