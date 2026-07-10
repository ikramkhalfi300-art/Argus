from pydantic import BaseModel, Field


class ValidationJudgment(BaseModel):
    """Structured output from the LLM gray-area compliance check."""
    is_flagged: bool
    flags: list[str] = Field(default_factory=list)
    reasoning: str


class SupplierAvailability(BaseModel):
    in_stock: bool
    moq: int
    shipping_days: int
    supplier_rating: float
    source: str


class ComplianceFlag(BaseModel):
    rule: str
    matched_categories: list[str] = Field(default_factory=list)
    matched_subcategories: list[str] = Field(default_factory=list)
    matched_keywords: list[str] = Field(default_factory=list)


class ValidationResult(BaseModel):
    is_valid: bool
    is_saleable_on_meta: bool
    is_saleable_on_tiktok: bool
    compliance_flags: list[ComplianceFlag] = Field(default_factory=list)
    llm_judgment: ValidationJudgment | None = None
    supplier_availability: SupplierAvailability | None = None
    requires_manual_review: bool = False
