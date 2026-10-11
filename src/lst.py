from decimal import Decimal
from .tax import Tax
from .tax_context import TaxContext
from .tax_result import TaxResult
from .money import Money
from .error import InvalidContextError, InvalidIncomeError, TaxConfigError


class Lst(Tax):
    """
    LST tax class
    Note: 
    - LST is paid in installments, so the payroll month is required
    - installment months are from July and October
    """

    def __init__(self, country_code: str = "UG") -> None:
        super().__init__(country_code)
        self.code: str = 'LST'

        config = self.tax_configurations['tax_types'][self.code]
        #populate the tax brackets, installments, and installment months
        self.brackets: list[dict] = config['brackets']
        self.installments: int = config['installments']
        self.installment_months: list[int] = config['installment_months']
        

    def calculate(self, ctx: TaxContext) -> TaxResult:
        """
        formula
        installment = annual amount / number of installments 
        Note:the installments are the 4 months from july and october
        """

        self._validate(ctx)

        base = ctx.gross_monthly

        #only consider months between July-October
        if ctx.month not in self.installment_months:
            return TaxResult(code=self.code, amount=Money.zero(), taxable_base=base)
        
        annual_amount = Money(Decimal(str(self._determine_bracket(base.amount)['annual_amount'])))

        installment = annual_amount / self.installments

        return TaxResult(code=self.code, amount=installment, taxable_base=base)

    def _determine_bracket(self, income: Decimal) -> dict:
        """
        A bracket applies when lower < income <= upper. upper None means no cap.
        """
        for bracket in self.brackets:
            upper = bracket['upper']
            if income > bracket['lower'] and (upper is None or income <= upper):
                return bracket
        if income == 0:
            return self.brackets[0]
        raise TaxConfigError(f"No LST bracket covers an income of {income}")

    def _validate(self, ctx:TaxContext)-> None:
        """
        Validate tax context
        """
        if ctx.month is None:
            raise InvalidContextError("LST needs ctx.month (1-12)")
        if not 1 <= ctx.month <= 12:
            raise InvalidContextError(f"LST month must be 1-12, not {ctx.month}")
        if ctx.gross_monthly < Money.zero():
            raise InvalidIncomeError(f"Gross monthly pay can't be negative: {ctx.gross_monthly}")