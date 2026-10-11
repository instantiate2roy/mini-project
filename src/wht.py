from decimal import Decimal

from .tax import Tax
from .tax_context import TaxContext
from .tax_result import TaxResult
from .money import Money
from .error import InvalidContextError, InvalidIncomeError


class Wht(Tax): 
    """
    Withholding tax class
    """

    def __init__(self, country_code: str = "UG") -> None:
        super().__init__(country_code)
        self.code: str = 'WHT'

        config = self.tax_configurations['tax_types'][self.code]
        self.rates: dict[str, Decimal] = {name: Decimal(str(rate)) for name, rate in config['rates'].items()}

    def calculate(self, ctx: TaxContext) -> TaxResult:
        """
        formula for taxing winnings
        with holding tax = (payment or winnings) x rate
        """
        self._validation(ctx)

        payment = ctx.amount

        tax = payment * self.rates[ctx.payment_type]

        return TaxResult(code=self.code, amount=tax, taxable_base=payment)

    def _validation(self, ctx: TaxContext) -> None:
        """
        Validation
        """
        if ctx.payment_type is None or ctx.payment_type not in self.rates:
            raise InvalidContextError(f"Missing or Unknown WHT payment type '{ctx.payment_type}'")
        
        # no negative gross payment/payout
        if ctx.amount < Money.zero():
            raise InvalidIncomeError(f"WHT payment can't be negative: {ctx.amount}")
