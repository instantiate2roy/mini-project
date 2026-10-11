from dataclasses import dataclass
from decimal import Decimal
 
 
@dataclass(frozen=True)
class TaxResult:
    """
    template for the tax result object
    """
    code: str
    amount: Decimal
    taxable_base: Decimal
    employer_amount: Decimal = Decimal("0")