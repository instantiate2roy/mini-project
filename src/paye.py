from decimal import Decimal, ROUND_HALF_UP

from .tax import Tax
from .tax_context import TaxContext
from .tax_result import TaxResult


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
        """
        
        if ctx.residency not in self.schedules:
            raise ValueError(f"No PAYE schedule for residency '{ctx.residency}'")
        
        bands = self.schedules[ctx.residency]['bands']
 
        taxable_income = max(ctx.gross_monthly, Decimal("0")) #allowance not included
 
        band = self._determine_tax_band(bands, taxable_income)
 
        lower_limit = Decimal(str(band['lower']))
        rate = Decimal(str(band['rate']))
        base_tax = Decimal(str(band['base_tax']))
        tax = base_tax + rate * (taxable_income - lower_limit)
 
        #round to nearest whole number
        tax = tax.quantize(1, rounding=ROUND_HALF_UP)
 
        return TaxResult(code=self.code, amount=tax, taxable_base=taxable_income)
 
    def _determine_tax_band(self, bands: list[dict], income: Decimal) -> dict:
        """
        A band applies when lower < income <= upper. upper None means no cap.
        """
        for band in bands:
            upper = band['upper']
            if income > band['lower'] and (upper is None or income <= upper):
                return band
        return bands[0]
