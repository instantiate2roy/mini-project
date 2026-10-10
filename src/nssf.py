from decimal import Decimal, ROUND_HALF_UP

from .tax import Tax
from .tax_context import TaxContext
from .tax_result import TaxResult


class Nssf(Tax):

    def __init__(self, country_code="UG"):
        super().__init__(country_code)
        self.code = 'NSSF'
        config = self.tax_configurations['tax_types'][self.code]
        self.employee_rate = Decimal(str(config['employee_rate']))
        self.employer_rate = Decimal(str(config['employer_rate']))
        self.cap = None if config['cap'] is None else Decimal(str(config['cap']))

    def calculate(self, ctx: TaxContext) -> TaxResult:
        # 1. Contribution base is gross monthly pay (allowance not included yet)
        base = max(ctx.gross_monthly, Decimal("0"))

        # 2. Apply the cap if the config sets one (Uganda: no cap)
        if self.cap is not None:
            base = min(base, self.cap)

        # 3. Employee and employer shares, rounded to whole shillings
        employee = (base * self.employee_rate).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        employer = (base * self.employer_rate).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

        return TaxResult(code=self.code, amount=employee, taxable_base=base, employer_amount=employer)