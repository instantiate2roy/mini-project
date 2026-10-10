from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class TaxContext:
    """
    Inputs for a tax calculation.
    """

    gross_monthly: Decimal = Decimal("0")
    allowance: Decimal = Decimal("0") 
    residency: str = "resident"
    