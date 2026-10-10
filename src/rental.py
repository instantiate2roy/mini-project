from decimal import Decimal, ROUND_HALF_UP

from .tax import Tax
from .tax_context import TaxContext
from .tax_result import TaxResult


class Rental(Tax):

    def __init__(self, country_code="UG"):
        super().__init__(country_code)
        self.code = 'RENTAL'
        config = self.tax_configurations['tax_types'][self.code]
        self.residency = config['residency']
        self.landlords = {
            kind: {key: Decimal(str(value)) for key, value in rules.items()}
            for kind, rules in config['landlords'].items()
        }

    def calculate(self, ctx: TaxContext) -> TaxResult:
        # 1. Only resident landlords are covered (rules for non-residents are unclear)
        if ctx.residency != self.residency:
            raise ValueError(f"No rental tax rules configured for residency '{ctx.residency}'")
        if ctx.landlord_type not in self.landlords:
            raise ValueError(f"Unknown landlord type '{ctx.landlord_type}'")
        rules = self.landlords[ctx.landlord_type]

        # 2. Gross rent for the year and the costs of earning it
        if ctx.amount < 0:
            raise ValueError(f"Rent can't be negative: {ctx.amount}")
        if ctx.expenses < 0:
            raise ValueError(f"Expenses can't be negative: {ctx.expenses}")
        rent = ctx.amount

        # 3. Expenses count only up to the cap: none for individuals, 50% of rent for companies
        allowed_expenses = min(ctx.expenses, rent * rules['expense_cap'])

        # 4. Chargeable rent is what's left above the tax-free threshold
        chargeable = max(rent - allowed_expenses - rules['threshold'], Decimal("0"))

        # 5. Tax = chargeable rent x rate, rounded to whole shillings
        tax = (chargeable * rules['rate']).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

        return TaxResult(code=self.code, amount=tax, taxable_base=chargeable)
