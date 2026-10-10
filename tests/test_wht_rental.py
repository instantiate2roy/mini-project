"""Tests for withholding tax and rental income tax: fixed examples, errors, and hypothesis properties."""
from decimal import Decimal

import pytest
from hypothesis import example, given, strategies as st

from src.rental import Rental
from src.tax_context import TaxContext
from src.wht import Wht

WHT = Wht('UG')
RENTAL = Rental('UG')


def wht_for(payment, payment_type: str) -> Decimal:
    return WHT.calculate(TaxContext(amount=Decimal(payment), payment_type=payment_type)).amount


def rental_for(rent, landlord_type: str = 'individual', expenses=0) -> Decimal:
    ctx = TaxContext(amount=Decimal(rent), landlord_type=landlord_type, expenses=Decimal(expenses))
    return RENTAL.calculate(ctx).amount


# Withholding tax: one rate per payment type, checked on a payment of 1,000,000

@pytest.mark.parametrize('payment_type, expected', [
    ('dividend',                      150_000),   # 15%
    ('dividend_listed_to_individual', 100_000),   # 10%
    ('interest',                      150_000),   # 15%
    ('debenture_interest_abroad',      50_000),   # 5%
    ('royalty_non_resident',          150_000),   # 15%
    ('betting_winnings',              150_000),   # 15% of payout minus stake
    ('telecom_commission',            100_000),   # 10%
    ('insurance_commission',          100_000),   # 10%
    ('public_entertainer',             60_000),   # 6%
])
def test_wht_rate_for_each_payment_type(payment_type, expected):
    assert wht_for(1_000_000, payment_type) == expected


def test_wht_rounds_to_whole_shillings():
    assert wht_for(25, 'public_entertainer') == 2     # 6% x 25 = 1.5, rounds up
    assert wht_for(8, 'public_entertainer') == 0      # 0.48 rounds down


def test_wht_needs_a_known_payment_type():
    with pytest.raises(ValueError, match='needs ctx.payment_type'):
        WHT.calculate(TaxContext(amount=Decimal(1_000)))
    with pytest.raises(ValueError, match="Unknown WHT payment type 'salary'"):
        wht_for(1_000, 'salary')


def test_wht_rejects_a_negative_payment():
    with pytest.raises(ValueError, match="can't be negative"):
        wht_for(-1, 'dividend')


# Rental income tax for individuals: 12% of annual rent above 2,820,000

@pytest.mark.parametrize('rent, expected', [
    (0,          0),
    (2_820_000,  0),          # exactly at the threshold
    (2_820_001,  0),          # 12% x 1 = 0.12 rounds to 0
    (2_820_010,  1),          # 12% x 10 = 1.2 rounds to 1
    (10_000_000, 861_600),    # URA's example: 12% x (10,000,000 - 2,820,000)
])
def test_individual_rental_tax_around_the_threshold(rent, expected):
    assert rental_for(rent) == expected


def test_individuals_cant_deduct_expenses():
    assert rental_for(10_000_000, expenses=4_000_000) == rental_for(10_000_000)


# Rental income tax for companies: 30% after expenses, capped at 50% of rent

@pytest.mark.parametrize('expenses, expected', [
    (0,          3_000_000),   # no expenses: 30% x 10,000,000
    (3_000_000,  2_100_000),   # under the cap: 30% x 7,000,000
    (5_000_000,  1_500_000),   # exactly at the cap: 30% x 5,000,000
    (7_000_000,  1_500_000),   # over the cap: only 5,000,000 counts
])
def test_company_rental_tax_with_the_expense_cap(expenses, expected):
    assert rental_for(10_000_000, 'company', expenses) == expected


@pytest.mark.parametrize('ctx, message', [
    (TaxContext(amount=Decimal(1), residency='non_resident'), "residency 'non_resident'"),
    (TaxContext(amount=Decimal(1), landlord_type='trust'), "landlord type 'trust'"),
    (TaxContext(amount=Decimal(-1)), "Rent can't be negative"),
    (TaxContext(amount=Decimal(1), expenses=Decimal(-1)), "Expenses can't be negative"),
])
def test_rental_tax_rejects_bad_input(ctx, message):
    with pytest.raises(ValueError, match=message):
        RENTAL.calculate(ctx)


# Property-based tests

amounts = st.one_of(
    st.integers(min_value=0, max_value=10_000_000_000).map(Decimal),
    st.decimals(min_value=0, max_value=10_000_000_000, places=2,
                allow_nan=False, allow_infinity=False),
)
payment_types = st.sampled_from(sorted(WHT.rates))
landlord_types = st.sampled_from(['individual', 'company'])
raises = st.integers(min_value=1, max_value=1_000_000)


@given(payment=amounts, payment_type=payment_types)
def test_wht_is_never_negative_and_never_more_than_the_payment(payment, payment_type):
    tax = wht_for(payment, payment_type)
    assert 0 <= tax <= payment


@given(payment=amounts, raise_by=raises, payment_type=payment_types)
def test_wht_never_goes_down_when_the_payment_goes_up(payment, raise_by, payment_type):
    assert wht_for(payment, payment_type) <= wht_for(payment + raise_by, payment_type)


@given(rent=amounts, expenses=amounts, landlord_type=landlord_types)
def test_rental_tax_is_never_negative_and_never_more_than_the_rent(rent, expenses, landlord_type):
    tax = rental_for(rent, landlord_type, expenses)
    assert 0 <= tax <= rent


@given(rent=amounts, raise_by=raises, expenses=amounts, landlord_type=landlord_types)
@example(rent=Decimal(2_820_000), raise_by=1, expenses=Decimal(0), landlord_type='individual')
def test_rental_tax_never_goes_down_when_rent_goes_up(rent, raise_by, expenses, landlord_type):
    assert rental_for(rent, landlord_type, expenses) <= rental_for(rent + raise_by, landlord_type, expenses)


@given(rent=amounts, expenses=amounts)
def test_company_pays_between_15_and_30_percent_of_rent(rent, expenses):
    # expenses can cut chargeable rent by at most half, so tax is 15% to 30% of rent
    tax = rental_for(rent, 'company', expenses)
    assert rent * Decimal('0.15') - 1 <= tax <= rent * Decimal('0.30') + 1
