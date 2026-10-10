from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from functools import total_ordering


# dataclass provides __init__, ==, hashing and immutability (frozen=True).
# total_ordering builds >, <= and >= from __lt__.
@total_ordering
@dataclass(frozen=True)
class Money:
    """
    An amount of money, stored as a Decimal along with its currency (UGX by default).

    Amounts are rounded to whole shillings as soon as they're created,
    with halves rounded away from zero, so 0.5 becomes 1 and -0.5 becomes -1.
    Adding, subtracting, multiplying or dividing always gives a new Money,
    so every result is rounded the same way.
    """

    amount: Decimal
    currency: str = "UGX"

    def __post_init__(self):
        if isinstance(self.amount, float) or not isinstance(self.amount, (Decimal, int)):
            raise TypeError(f"Money needs a Decimal or int, not {type(self.amount).__name__}")

        # round to whole shillings, halves away from zero
        rounded = Decimal(self.amount).quantize(1, rounding=ROUND_HALF_UP)

        # the class is frozen, so this is the only place the amount can be set
        object.__setattr__(self, "amount", rounded)

    @classmethod
    def zero(cls, currency: str = "UGX") -> Money:
        """
        A zero amount, e.g. Money.zero()
        """
        return cls(Decimal("0"), currency)

    def _check_same_currency(self, other: Money) -> None:
        if not isinstance(other, Money):
            raise TypeError(f"Can't combine Money with {type(other).__name__}")
        if other.currency != self.currency:
            raise ValueError(f"Currency mismatch: {self.currency} and {other.currency}")

    def __add__(self, other: Money) -> Money:
        self._check_same_currency(other)
        return Money(self.amount + other.amount, self.currency)

    def __radd__(self, other) -> Money:
        """
        sum() starts adding from 0, so 0 + Money has to work
        """
        if other == 0:
            return self
        return self.__add__(other)

    def __sub__(self, other: Money) -> Money:
        self._check_same_currency(other)
        return Money(self.amount - other.amount, self.currency)

    def __mul__(self, factor: Decimal | int) -> Money:
        """
        You can multiply by a rate, but not by another Money or a float
        """
        if isinstance(factor, float) or not isinstance(factor, (Decimal, int)):
            raise TypeError(f"Money can only be multiplied by a Decimal or int, not {type(factor).__name__}")
        return Money(self.amount * factor, self.currency)

    __rmul__ = __mul__

    def __truediv__(self, divisor: Decimal | int) -> Money:
        if isinstance(divisor, float) or not isinstance(divisor, (Decimal, int)):
            raise TypeError(f"Money can only be divided by a Decimal or int, not {type(divisor).__name__}")
        return Money(self.amount / divisor, self.currency)

    def __lt__(self, other: Money) -> bool:
        self._check_same_currency(other)
        return self.amount < other.amount

    def __repr__(self) -> str:
        """
        Shows the exact value, for debugging
        """
        return f"Money('{self.amount}', '{self.currency}')"

    def __str__(self) -> str:
        """
        Readable form, e.g. UGX 1,000,000
        """
        return f"{self.currency} {self.amount:,}"

    def __format__(self, spec: str) -> str:
        """
        Lets f"{m:,.0f}" and pandas formatting work just like on a plain number
        """
        return format(self.amount, spec) if spec else str(self)