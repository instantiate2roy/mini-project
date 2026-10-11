from dataclasses import dataclass, field, fields
from datetime import date
from .error import InvalidIncomeError
from .money import Money


@dataclass(frozen=True)
class TaxContext:
    """
    Inputs for a tax calculation.
    """
    gross_monthly: Money = Money.zero()
    allowance: Money = Money.zero() 
    residency: str = "resident"
    month: int | None = None
    amount: Money = Money.zero()
    vat_category: str | None = None
    payment_type: str | None = None         
    landlord_type: str = "individual"       
    expenses: Money = Money.zero()        
    pay_date: date = field(default_factory=date.today)  # PAYE picks the schedule in force on this date

    def __post_init__(self) -> None:
        """
        Every amount must be Money, so a plain number or float is caught here, not deep inside a tax
        """
        for f in fields(self):
            value = getattr(self, f.name)
            if f.type == "Money" or f.type is Money:
                if not isinstance(value, Money):
                    raise InvalidIncomeError(f"{f.name} must be Money, not {type(value).__name__}")
