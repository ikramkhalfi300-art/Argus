from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Product
from app.schemas.product_identity import ProductIdentity


async def create_product_identity(db: AsyncSession, identity: ProductIdentity) -> Product:
    obj = Product(
        name=identity.name,
        category=identity.category,
        subcategory=identity.subcategory,
        variants=identity.variants,
        normalized_keywords=identity.normalized_keywords,
        detected_niche=identity.detected_niche,
        image_refs=identity.image_refs,
        source_url=identity.source_url,
    )
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


async def get_product_identity(db: AsyncSession, product_id: int) -> Product | None:
    return await db.get(Product, product_id)
