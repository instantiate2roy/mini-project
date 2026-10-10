from decimal import Decimal, ROUND_HALF_UP

from .tax import Tax
from .tax_context import TaxContext
from .tax_result import TaxResult


class Cit(Tax):

    def __init__(self, country_code="UG"):
        super().__init__(country_code)
        self.code = 'CIT'
        config = self.tax_configurations['tax_types'][self.code]
        self.rate = Decimal(str(config['rate']))
        self.residency = config['residency']

    def calculate(self, ctx: TaxContext) -> TaxResult:
        # 1. Only the configured residency is supported (Uganda: resident companies)
        if ctx.residency != self.residency:
            raise ValueError(f"No CIT rate configured for residency '{ctx.residency}'")

        # 2. Chargeable income for the year; a loss means no tax
        chargeable = max(ctx.amount, Decimal("0"))

        # 3. CIT = chargeable income x rate, rounded to whole shillings
        tax = (chargeable * self.rate).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

        return TaxResult(code=self.code, amount=tax, taxable_base=chargeable)