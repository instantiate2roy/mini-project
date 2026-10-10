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
    month: int | None = None
    amount: Decimal = Decimal("0")
    vat_category: str | None = None
    payment_type: str | None = None         
    landlord_type: str = "individual"       
    expenses: Decimal = Decimal("0")        