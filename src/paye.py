from decimal import Decimal, ROUND_HALF_UP

from .tax import Tax
from .tax_context import TaxContext
from .tax_result import TaxResult


class Paye(Tax):
    
    def __init__(self, country_code = "UG"):
        super().__init__(country_code)
        self.code='PAYE'
        self.schedules = self.tax_configurations['tax_types'][self.code]['tax_schedules']

    def calculate(self, ctx: TaxContext) -> TaxResult:
        # 1. Pick the bands for the employee's residency
        if ctx.residency not in self.schedules:
            raise ValueError(f"No PAYE schedule for residency '{ctx.residency}'")
        bands = self.schedules[ctx.residency]['bands']
 
        # 2. Taxable income (allowance not included yet)
        taxable = max(ctx.gross_monthly, Decimal("0"))
 
        # 3. Find the band the income falls in
        band = self._find_band(bands, taxable)
 
        # 4. tax = base_tax + rate x (income - lower)
        lower = Decimal(str(band['lower']))
        rate = Decimal(str(band['rate']))
        base_tax = Decimal(str(band['base_tax']))
        tax = base_tax + rate * (taxable - lower)
 
        # 5. Round to whole shillings
        tax = tax.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
 
        return TaxResult(code=self.code, amount=tax, taxable_base=taxable)
 
    def _find_band(self, bands: list, income: Decimal) -> dict:
        """
        A band applies when lower < income <= upper. upper None means no cap.
        """
        for band in bands:
            upper = band['upper']
            if income > band['lower'] and (upper is None or income <= upper):
                return band
        return bands[0]
