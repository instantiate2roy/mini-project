from decimal import Decimal, ROUND_HALF_UP

from .tax import Tax
from .tax_context import TaxContext
from .tax_result import TaxResult


class Nssf(Tax):
    """
    NSSF tax class
    """

    def __init__(self, country_code: str = "UG") -> None:
        super().__init__(country_code)
        self.code: str = 'NSSF'

        config = self.tax_configurations['tax_types'][self.code]

        #populate the employee, employer and pre tax values
        self.employee_rate: Decimal = Decimal(str(config['employee_rate']))
        self.employer_rate: Decimal = Decimal(str(config['employer_rate']))
        self.pre_tax_for_paye: bool = config['pre_tax_for_paye']
        
    def calculate(self, ctx: TaxContext) -> TaxResult:
        """
        Formula
        nssf 
        employee portion =  gross monthly pay * employe rate
        employer portion = gross monthly pay *  employer rate
        """
        base = max(ctx.gross_monthly, Decimal("0")) #allow is not included

        employee = (base * self.employee_rate).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        employer = (base * self.employer_rate).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

        return TaxResult(code=self.code, amount=employee, taxable_base=base, employer_amount=employer)