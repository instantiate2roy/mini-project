from decimal import Decimal

from .tax import Tax
from .tax_context import TaxContext
from .tax_result import TaxResult
from .money import Money
from .error import InvalidContextError, InvalidIncomeError


class Vat(Tax):
    """
    VAT class
    """

    def __init__(self, country_code: str = "UG") -> None:
        super().__init__(country_code)
        self.code: str = 'VAT'
        config = self.tax_configurations['tax_types'][self.code]

        self.rates: dict[str, Decimal | None] = config['rates']    # the config is read with parse_float=Decimal
        self.default_category: str = config['default_category']

    def calculate(self, ctx: TaxContext) -> TaxResult:
        """
        Formula
        vat =  value x rate
        """
        
        category = ctx.vat_category or self.default_category #if no vat category, use standard
        if category not in self.rates:
            raise InvalidContextError(f"Unknown VAT category '{category}'")

        # taxable excluding VAT
        if ctx.amount < Money.zero():
            raise InvalidIncomeError(f"VAT amount can't be negative: {ctx.amount}")
        taxable = ctx.amount

        
        rate = self.rates[category]
        if rate is None: #if rate null: no VAT at all, means exemption from VAT
            return TaxResult(code=self.code, amount=Money.zero(), taxable_base=taxable)

        vat = taxable * Decimal(str(rate))

        return TaxResult(code=self.code, amount=vat, taxable_base=taxable)