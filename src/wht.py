from decimal import Decimal, ROUND_HALF_UP

from .tax import Tax
from .tax_context import TaxContext
from .tax_result import TaxResult


class Wht(Tax): 

    def __init__(self, country_code="UG"):
        super().__init__(country_code)
        self.code = 'WHT'
        config = self.tax_configurations['tax_types'][self.code]
        self.rates = {name: Decimal(str(rate)) for name, rate in config['rates'].items()}

    def calculate(self, ctx: TaxContext) -> TaxResult:
        # 1. The payment type decides the rate, so it must be given and known
        if ctx.payment_type is None:
            raise ValueError("WHT needs ctx.payment_type, e.g. 'dividend'")
        if ctx.payment_type not in self.rates:
            raise ValueError(f"Unknown WHT payment type '{ctx.payment_type}'")

        # 2. The gross payment; for betting this is the winnings (payout minus stake)
        if ctx.amount < 0:
            raise ValueError(f"WHT payment can't be negative: {ctx.amount}")
        payment = ctx.amount

        # 3. Tax withheld = payment x rate, rounded to whole shillings
        tax = (payment * self.rates[ctx.payment_type]).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

        return TaxResult(code=self.code, amount=tax, taxable_base=payment)
