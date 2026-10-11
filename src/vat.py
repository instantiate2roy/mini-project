from decimal import Decimal, ROUND_HALF_UP

from .tax import Tax
from .tax_context import TaxContext
from .tax_result import TaxResult


class Vat(Tax):
    """
    VAT class
    """

    def __init__(self, country_code="UG"):
        super().__init__(country_code)
        self.code = 'VAT'
        config = self.tax_configurations['tax_types'][self.code]

        self.rates, self.default_category = [config['rates'], config['default_category']]

    def calculate(self, ctx: TaxContext) -> TaxResult:
        """
        Formula
        vat =  value x rate
        """
        
        category = ctx.vat_category or self.default_category #if no vat category, use standard
        if category not in self.rates:
            raise ValueError(f"Unknown VAT category '{category}'")

        # taxable excluding VAT
        taxable = max(ctx.amount, Decimal("0"))

        
        rate = self.rates[category]
        if rate is None: #if rate null: no VAT at all, means exemption from VAT
            return TaxResult(code=self.code, amount=Decimal("0"), taxable_base=taxable)

        vat = (taxable * Decimal(str(rate))).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

        return TaxResult(code=self.code, amount=vat, taxable_base=taxable)