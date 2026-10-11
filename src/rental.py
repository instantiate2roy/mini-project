from decimal import Decimal, ROUND_HALF_UP

from .tax import Tax
from .tax_context import TaxContext
from .tax_result import TaxResult


class Rental(Tax):
    """
    Rental class
    Note: only applies to those based in UG, have to be residents
    """

    def __init__(self, country_code: str = "UG") -> None:
        super().__init__(country_code)
        self.code: str = 'RENTAL'
        config = self.tax_configurations['tax_types'][self.code]

        self.residency: str = config['residency']
        self.landlords: dict[str, dict[str, Decimal]] = {
            kind: {key: Decimal(str(value)) for key, value in rules.items()}
            for kind, rules in config['landlords'].items()
        }

    def calculate(self, ctx: TaxContext) -> TaxResult:
        """
        formula
        tax = chargeable rent x rate
        """

        self._validation(ctx)
        rules = self.landlords[ctx.landlord_type]
        
        rent = ctx.amount

        # expenses for componies are capped, no cap for individuals
        allowed_expenses = min(ctx.expenses, rent * rules['expense_cap'])

        # chargeable is anything above the tax free threshold
        chargeable = max(rent - allowed_expenses - rules['threshold'], Decimal("0"))

        tax = (chargeable * rules['rate']).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

        return TaxResult(code=self.code, amount=tax, taxable_base=chargeable)

    def _validation(self, ctx: TaxContext) -> None:
        """
        Run validation on tax context input
        """
        if ctx.residency != self.residency: #at the moment, the config only caters for residents
            raise ValueError(f"No rental tax rules configured for {ctx.residency}")
            
        if ctx.landlord_type not in self.landlords:
            raise ValueError(f"Unknown landlord type '{ctx.landlord_type}'")

        if ctx.amount < 0:
            raise ValueError(f"Rent can't be negative: {ctx.amount}")
        
        if ctx.expenses < 0:
            raise ValueError(f"Expenses can't be negative: {ctx.expenses}")
            

