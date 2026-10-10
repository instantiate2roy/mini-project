from decimal import Decimal, ROUND_HALF_UP

from .tax import Tax
from .tax_context import TaxContext
from .tax_result import TaxResult


class Vat(Tax):

    def __init__(self, country_code="UG"):
        super().__init__(country_code)
        self.code = 'VAT'
        config = self.tax_configurations['tax_types'][self.code]
        self.rates = config['rates']
        self.default_category = config['default_category']

    def calculate(self, ctx: TaxContext) -> TaxResult:
        # 1. Pick the category, falling back to the config default ("standard")
        category = ctx.vat_category or self.default_category
        if category not in self.rates:
            raise ValueError(f"Unknown VAT category '{category}'")

        # 2. Taxable value of the supply, excluding VAT
        taxable = max(ctx.amount, Decimal("0"))

        # 3. Exempt supplies have rate null: no VAT at all
        rate = self.rates[category]
        if rate is None:
            return TaxResult(code=self.code, amount=Decimal("0"), taxable_base=taxable)

        # 4. VAT = value x rate, rounded to whole shillings
        vat = (taxable * Decimal(str(rate))).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

        return TaxResult(code=self.code, amount=vat, taxable_base=taxable)