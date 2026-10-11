"""Tests for Money, the error hierarchy, the Tax base class, NSSF, LST, VAT and corporate income tax."""
import dataclasses
from decimal import Decimal

import pytest

from src.cit import Cit
from src.error import InvalidContextError, InvalidIncomeError, NoScheduleForDateError, TaxConfigError, TaxError
from src.lst import Lst
from src.money import Money
from src.nssf import Nssf
from src.tax import Tax
from src.tax_context import TaxContext
from src.vat import Vat


# Money

@pytest.mark.parametrize('amount, rounded', [
    (Decimal('0.5'), 1),      # halves round away from zero
    (Decimal('-0.5'), -1),
    (Decimal('2.5'), 3),
    (Decimal('2.4'), 2),
])
def test_money_rounds_to_whole_shillings(amount, rounded):
    assert Money(amount).amount == rounded


@pytest.mark.parametrize('amount', [1.5, '1000', None])
def test_money_rejects_floats_and_other_types(amount):
    with pytest.raises(TypeError):
        Money(amount)


def test_money_arithmetic_returns_rounded_money():
    assert Money(1000) + Money(500) == Money(1500)
    assert Money(5) - Money(7) == Money(-2)
    assert Money(1000) * Decimal('0.18') == Money(180)
    assert Decimal('2') * Money(3) == Money(6)            # __rmul__
    assert Money(10) / 3 == Money(3)                        # 3.33 rounds to 3
    assert sum([Money(1), Money(2)]) == Money(3)            # sum starts from 0, so __radd__ is needed


@pytest.mark.parametrize('operation', [
    lambda: Money(1) * 1.5,                  # float rate
    lambda: Money(1) * Money(1),             # money times money has no meaning
    lambda: Money(1) / 0.5,
    lambda: Money(1) + 5,                    # plain number
])
def test_money_rejects_floats_and_mixed_types_in_arithmetic(operation):
    with pytest.raises(TypeError):
        operation()


def test_money_in_different_currencies_cannot_be_combined():
    with pytest.raises(ValueError, match='Currency mismatch'):
        Money(1) + Money(1, 'USD')


def test_money_comparison_and_display():
    assert Money(1) < Money(2)
    assert Money(2) >= Money(2)                              # total_ordering fills in the other comparisons
    assert repr(Money(Decimal('1000'))) == "Money('1000', 'UGX')"
    assert str(Money(1_000_000)) == 'UGX 1,000,000'
    assert f'{Money(1_000_000):,.0f}' == '1,000,000'


def test_money_is_immutable():
    with pytest.raises(dataclasses.FrozenInstanceError):
        Money(1).amount = Decimal(5)


# Error hierarchy

@pytest.mark.parametrize('error, also', [
    (InvalidIncomeError, ValueError),
    (NoScheduleForDateError, LookupError),
    (InvalidContextError, ValueError),
    (TaxConfigError, Exception),
])
def test_every_error_is_a_tax_error(error, also):
    assert issubclass(error, TaxError) and issubclass(error, also)


# Tax base class

def test_tax_is_abstract():
    with pytest.raises(TypeError):
        Tax()


def test_unknown_country_is_rejected():
    with pytest.raises(TaxConfigError, match="Country 'KE' not found"):
        Vat('KE')


def test_missing_config_file_is_reported(monkeypatch, tmp_path):
    monkeypatch.setattr(Tax, 'tax_config_file', tmp_path / 'missing.json')
    with pytest.raises(TaxConfigError, match='Tax config not found'):
        Vat('UG')


# NSSF: 5% employee, 10% employer, both on gross pay

def test_nssf_employee_and_employer_shares():
    result = Nssf().calculate(TaxContext(gross_monthly=Money(1_000_000)))
    assert (result.amount, result.employer_amount) == (Money(50_000), Money(100_000))


def test_nssf_rounds_half_shillings_up():
    assert Nssf().calculate(TaxContext(gross_monthly=Money(10))).amount == Money(1)      # 5% x 10 = 0.5


# Local Service Tax: annual amount by income bracket, paid in 4 instalments from July to October

@pytest.mark.parametrize('gross, instalment', [
    (100_000, 0),           # top of the nil bracket
    (100_001, 1_250),       # 5,000 a year / 4
    (1_000_000, 22_500),    # 90,000 a year / 4
    (1_500_000, 25_000),    # top bracket: 100,000 a year / 4
])
def test_lst_instalment_by_bracket(gross, instalment):
    assert Lst().calculate(TaxContext(gross_monthly=Money(gross), month=7)).amount == Money(instalment)


@pytest.mark.parametrize('month', [1, 6, 11, 12])
def test_no_lst_outside_july_to_october(month):
    assert Lst().calculate(TaxContext(gross_monthly=Money(1_500_000), month=month)).amount == Money.zero()


def test_lst_needs_the_payroll_month():
    with pytest.raises(InvalidContextError, match='LST needs ctx.month'):
        Lst().calculate(TaxContext(gross_monthly=Money(1_500_000)))


# VAT: standard 18%, zero-rated 0%, exempt has no VAT

@pytest.mark.parametrize('category, vat', [
    ('standard', 1_800_000),
    ('zero_rated', 0),
    ('exempt', 0),
    (None, 1_800_000),      # no category means standard-rated
])
def test_vat_by_supply_category(category, vat):
    assert Vat().calculate(TaxContext(amount=Money(10_000_000), vat_category=category)).amount == Money(vat)


def test_vat_rounds_to_whole_shillings():
    assert Vat().calculate(TaxContext(amount=Money(3))).amount == Money(1)               # 18% x 3 = 0.54


def test_unknown_vat_category_is_rejected():
    with pytest.raises(InvalidContextError, match="Unknown VAT category 'luxury'"):
        Vat().calculate(TaxContext(amount=Money(1), vat_category='luxury'))


def test_net_vat_matches_the_notebook_example():
    # Sales: 10,000,000 + 4,500,000 standard; purchases: 5,000,000 + 1,200,000 standard
    vat = Vat()
    output = sum(vat.calculate(TaxContext(amount=Money(a))).amount for a in (10_000_000, 4_500_000))
    input_ = sum(vat.calculate(TaxContext(amount=Money(a))).amount for a in (5_000_000, 1_200_000))
    assert (output, input_, output - input_) == (Money(2_610_000), Money(1_116_000), Money(1_494_000))


# Corporate income tax: 30% of chargeable income for resident companies

def test_cit_on_chargeable_income():
    # revenue 880,000,000 minus allowable deductions 435,000,000
    assert Cit().calculate(TaxContext(amount=Money(445_000_000))).amount == Money(133_500_000)


def test_cit_on_a_loss_is_zero():
    assert Cit().calculate(TaxContext(amount=Money(-5_000_000))).amount == Money.zero()


def test_cit_only_applies_to_resident_companies():
    with pytest.raises(InvalidContextError, match='tax residents'):
        Cit().calculate(TaxContext(amount=Money(1), residency='non_resident'))


# Errors: amounts must be Money, and bad input is never ignored

@pytest.mark.parametrize('field, value', [
    ('gross_monthly', Decimal(1_000)),     # a plain Decimal, not Money
    ('amount', 1_000),
    ('expenses', 1_000.5),                 # a float
])
def test_tax_context_only_accepts_money(field, value):
    with pytest.raises(InvalidIncomeError, match=f'{field} must be Money'):
        TaxContext(**{field: value})


@pytest.mark.parametrize('tax, ctx', [
    (Nssf(), TaxContext(gross_monthly=Money(-1))),
    (Lst(), TaxContext(gross_monthly=Money(-1), month=7)),
    (Vat(), TaxContext(amount=Money(-1))),
])
def test_negative_amounts_are_rejected(tax, ctx):
    with pytest.raises(InvalidIncomeError, match="can't be negative"):
        tax.calculate(ctx)


def test_income_outside_every_lst_bracket_is_a_config_error():
    lst = Lst()
    lst.brackets = [{'lower': 0, 'upper': 100_000, 'annual_amount': 0}]
    with pytest.raises(TaxConfigError, match='No LST bracket covers an income of 200000'):
        lst.calculate(TaxContext(gross_monthly=Money(200_000), month=7))


def test_lst_month_must_be_1_to_12():
    with pytest.raises(InvalidContextError, match='1-12, not 13'):
        Lst().calculate(TaxContext(gross_monthly=Money(1_500_000), month=13))
