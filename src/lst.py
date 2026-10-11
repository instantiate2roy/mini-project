from decimal import Decimal, ROUND_HALF_UP

from .tax import Tax
from .tax_context import TaxContext
from .tax_result import TaxResult


class Lst(Tax):
    """
    LST tax class
    Note: 
    - LST is paid in installments, so the payroll month is required
    - installment months are from July and October
    """

    def __init__(self, country_code="UG"):
        super().__init__(country_code)
        self.code = 'LST'

        config = self.tax_configurations['tax_types'][self.code]
        #populate the tax brackets, installments, and installment months
        self.brackets, self.installments, self.installment_months  = [config['brackets']
                                                                      , config['installments']
                                                                      , config['installment_months']]
        

    def calculate(self, ctx: TaxContext) -> TaxResult:
        """
        formula
        installment = annual amount / number of installments 
        Note:the installments are the 4 months from july and october
        """
        
        #the payroll month is required
        if ctx.month is None:
            raise ValueError("LST needs ctx.month (1-12)")

        #if value is negative, take 0 as the base
        base = max(ctx.gross_monthly, Decimal("0"))

        # only consider months between July-October
        if ctx.month not in self.installment_months:
            return TaxResult(code=self.code, amount=Decimal("0"), taxable_base=base)

        
        annual_amount = Decimal(str(self._determine_bracket(base)['annual_amount']))

        installment = (annual_amount / self.installments).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

        return TaxResult(code=self.code, amount=installment, taxable_base=base)

    def _determine_bracket(self, income: Decimal) -> dict:
        """
        A bracket applies when lower < income <= upper. upper None means no cap.
        """
        for bracket in self.brackets:
            upper = bracket['upper']
            if income > bracket['lower'] and (upper is None or income <= upper):
                return bracket
        return self.brackets[0]