from decimal import Decimal, ROUND_HALF_UP

from .tax import Tax
from .tax_context import TaxContext
from .tax_result import TaxResult


class Lst(Tax):

    def __init__(self, country_code="UG"):
        super().__init__(country_code)
        self.code = 'LST'
        config = self.tax_configurations['tax_types'][self.code]
        self.brackets = config['brackets']
        self.installments = config['installments']
        self.installment_months = config['installment_months']

    def calculate(self, ctx: TaxContext) -> TaxResult:
        # 1. LST is paid in installments, so the payroll month is required
        if ctx.month is None:
            raise ValueError("LST needs ctx.month (1-12)")

        base = max(ctx.gross_monthly, Decimal("0"))

        # 2. Outside the installment months (July-October) nothing is deducted
        if ctx.month not in self.installment_months:
            return TaxResult(code=self.code, amount=Decimal("0"), taxable_base=base)

        # 3. Look up the annual amount from monthly gross pay
        annual = Decimal(str(self._find_bracket(base)['annual_amount']))

        # 4. Split it into equal installments, rounded to whole shillings
        installment = (annual / self.installments).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

        return TaxResult(code=self.code, amount=installment, taxable_base=base)

    def _find_bracket(self, income: Decimal) -> dict:
        """A bracket applies when lower < income <= upper. upper None means no cap."""
        for bracket in self.brackets:
            upper = bracket['upper']
            if income > bracket['lower'] and (upper is None or income <= upper):
                return bracket
        return self.brackets[0]  # income is 0