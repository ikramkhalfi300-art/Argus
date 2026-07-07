from typing import Any

from pydantic import BaseModel, Field


class ProductIdentity(BaseModel):
    name: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1)
    subcategory: str = Field(..., min_length=1)
    variants: list[Any] = Field(default_factory=list)
    normalized_keywords: list[str] = Field(default_factory=list)
    detected_niche: str = ""
    image_refs: list[str] = Field(default_factory=list)
    source_url: str | None = None
