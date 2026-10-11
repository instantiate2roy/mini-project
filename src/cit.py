from decimal import Decimal, ROUND_HALF_UP

from .tax import Tax
from .tax_context import TaxContext
from .tax_result import TaxResult


class Cit(Tax):
    """
    CIT tax class
    note: 
    - CIT is only for companies based in UG, so residency check is needed
    - is only applied on income for the year; a loss means no tax
    """

    def __init__(self, country_code: str = "UG") -> None:
        super().__init__(country_code)
        self.code: str = 'CIT'
        config = self.tax_configurations['tax_types'][self.code]
        
        #extract rate, and residency
        self.rate: Decimal = Decimal(str(config['rate']))
        self.residency: str = config['residency']
         

    def calculate(self, ctx: TaxContext) -> TaxResult:
        """
        Tax formula
        cit = chargeable income * tax rate
        """
        
        #CIT only applies for companies based in UG
        if ctx.residency != self.residency:
            raise ValueError(f"CIT only applies for for tax residents")

        #if value is negative, take 0 as the chargeable
        chargeable_income = max(ctx.amount, Decimal("0"))

        tax = (chargeable_income * self.rate).quantize(Decimal("1"), rounding=ROUND_HALF_UP) #round off to nearest hold number

        return TaxResult(code=self.code, amount=tax, taxable_base=chargeable_income)