from datetime import date
from decimal import Decimal

from .tax import Tax
from .tax_context import TaxContext
from .tax_result import TaxResult
from .money import Money
from .error import InvalidContextError, InvalidIncomeError, NoScheduleForDateError, TaxConfigError


class Paye(Tax):
    """
    PAYE tax class
    """
    
    def __init__(self, country_code: str = "UG") -> None:
        super().__init__(country_code)
        self.code: str = 'PAYE'
        #populate tax schedules
        self.schedules: dict = self.tax_configurations['tax_types'][self.code]['tax_schedules']

    def calculate(self, ctx: TaxContext) -> TaxResult:
        """
        Formula
        paye = base tax + (rate x (income - lower band limit))
        income = gross monthly pay + allowances
        """
        
        self._validate(ctx)
        
        schedule = self.schedules[ctx.residency]

        bands = schedule['bands']
 
        taxable_income = ctx.gross_monthly + ctx.allowance #gross pay plus allowances
 
        band = self._determine_tax_band(bands, taxable_income.amount)
 
        lower_limit = Money(Decimal(str(band['lower'])))
        rate = Decimal(str(band['rate']))
        base_tax = Money(Decimal(str(band['base_tax'])))
        tax = base_tax + rate * (taxable_income - lower_limit)
 
        #round to nearest whole number
        return TaxResult(code=self.code, amount=tax, taxable_base=taxable_income)
 
    def _determine_tax_band(self, bands: list[dict], income: Decimal) -> dict:
        """
        A band applies when lower < income <= upper. upper None means no cap.
        """
        for band in bands:
            upper = band['upper']
            if income > band['lower'] and (upper is None or income <= upper):
                return band
        if income == 0:
            return bands[0]
        raise TaxConfigError(f"No PAYE band covers an income of {income}")

    def _validate(self, ctx:TaxContext)->None:
        """
        Validation
        """
        if ctx.residency not in self.schedules:
            raise InvalidContextError(f"No PAYE schedule for residency '{ctx.residency}'")
        
        schedule = self.schedules[ctx.residency]                
        
        # the schedule only applies from its start date
        if ctx.pay_date < date.fromisoformat(schedule['effective_from']):
            raise NoScheduleForDateError(f"No PAYE schedule for '{ctx.residency}' on {ctx.pay_date}; it starts {schedule['effective_from']}")
        
        if ctx.gross_monthly < Money.zero():
            raise InvalidIncomeError(f"Gross monthly pay can't be negative: {ctx.gross_monthly}")
        
        if ctx.allowance < Money.zero():
            raise InvalidIncomeError(f"Allowance can't be negative: {ctx.allowance}")