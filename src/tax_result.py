from dataclasses import dataclass
from decimal import Decimal
 
 
@dataclass(frozen=True)
class TaxResult:
    code: str
    amount: Decimal
    taxable_base: Decimal
 