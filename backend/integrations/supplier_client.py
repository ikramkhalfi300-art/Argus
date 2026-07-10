"""
Mock supplier client for Sprint 1.2.2.

TODO: Replace with real supplier API integration (e.g. AliExpress, CJ Dropshipping).
See Implementation_Roadmap.md Sprint 4.1.3 for the real integration sprint.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class SupplierAvailability:
    in_stock: bool
    moq: int
    shipping_days: int
    supplier_rating: float
    source: str


_MOCK_SUPPLIER: dict[str, SupplierAvailability] = {
    "default": SupplierAvailability(
        in_stock=True,
        moq=10,
        shipping_days=7,
        supplier_rating=4.2,
        source="Mock Supplier API",
    ),
}


async def fetch_supplier_data(
    product_name: str,
    category: str,
) -> Optional[SupplierAvailability]:
    """Return mock supplier data.

    Real implementation (Sprint 4.1.3) will query a supplier API
    (e.g. AliExpress, CJ Dropshipping) and return real COGS/MOQ/shipping
    data.  This stub always returns the same default fixture.
    """
    return _MOCK_SUPPLIER["default"]
