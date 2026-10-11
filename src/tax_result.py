from dataclasses import dataclass
from .money import Money
 
 
@dataclass(frozen=True)
class TaxResult:
    """
    template for the tax result object
    """
    code: str
    amount: Money
    taxable_base: Money
    employer_amount: Money = Money.zero()