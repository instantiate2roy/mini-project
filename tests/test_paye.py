"""Tests for PAYE: fixed values at every band edge, plus property-based tests with hypothesis."""
from decimal import Decimal

import pytest
from hypothesis import example, given, strategies as st

from src.paye import Paye
from src.tax_context import TaxContext

PAYE = Paye('UG')       # loaded once; hypothesis runs each property test many times


def paye_for(income, residency: str = 'resident') -> Decimal:
    """PAYE for one month's income."""
    return PAYE.calculate(TaxContext(gross_monthly=Decimal(income), residency=residency)).amount


# Boundary tests at every band edge.
# 1 shilling past an edge adds only 0.2 to 0.4 shillings of tax, which rounds away,
# so each pair (edge, edge + 1) gives the same whole-shilling result.

@pytest.mark.parametrize('income, expected', [
    (335_000,    0),           # top of the nil band
    (335_001,    0),           # first shilling taxed at 20%: 0.20 rounds to 0
    (410_000,    15_000),      # top of the 20% band: 20% x 75,000
    (485_000,    33_750),      # top of the 25% band: 15,000 + 25% x 75,000
    (10_000_000, 2_888_250),   # top of the 30% band: 33,750 + 30% x 9,515,000
    (10_000_001, 2_888_250),   # first shilling at 30% + 10%: 0.40 rounds to 0
])
def test_resident_paye_at_band_edges(income, expected):
    assert paye_for(income) == expected


@pytest.mark.parametrize('income, expected', [
    (335_000,    33_500),      # 10% from the first shilling: no nil band
    (335_001,    33_500),      # 33,500 + 0.20 rounds to 33,500
    (410_000,    48_500),      # top of the 20% band: 33,500 + 20% x 75,000
    (485_000,    71_000),      # inside the 30% band: 48,500 + 30% x 75,000
    (10_000_000, 2_925_500),   # top of the 30% band: 48,500 + 30% x 9,590,000
    (10_000_001, 2_925_500),   # 2,925,500 + 0.40 rounds to 2,925,500
])
def test_non_resident_paye_at_band_edges(income, expected):
    assert paye_for(income, 'non_resident') == expected


def test_first_shilling_of_each_band_uses_the_new_rate():
    # 10 shillings past each edge, so the extra tax is big enough to survive rounding
    assert paye_for(335_010) == 2              # 20% x 10
    assert paye_for(410_010) == 15_000 + 3     # 25% x 10 = 2.5, rounds up to 3
    assert paye_for(485_010) == 33_750 + 3     # 30% x 10
    assert paye_for(10_000_010) == 2_888_250 + 4   # 40% x 10


# Property-based tests: hypothesis tries many incomes, including the edges and 0.
# Incomes are whole shillings or have cents, up to UGX 1 billion a month.

incomes = st.one_of(
    st.integers(min_value=0, max_value=1_000_000_000).map(Decimal),
    st.decimals(min_value=0, max_value=1_000_000_000, places=2,
                allow_nan=False, allow_infinity=False),
)
residencies = st.sampled_from(['resident', 'non_resident'])

# incomes just below a band edge, so a small raise crosses it
BAND_EDGES = [335_000, 410_000, 485_000, 10_000_000]
near_edges = st.builds(
    lambda edge, gap: Decimal(edge - gap),
    st.sampled_from(BAND_EDGES),
    st.integers(min_value=0, max_value=100_000),
)


@given(income=incomes, residency=residencies)
def test_paye_is_never_negative(income, residency):
    assert paye_for(income, residency) >= 0


@given(income=st.one_of(incomes, near_edges), raise_by=st.integers(min_value=1, max_value=100_000),
       residency=residencies)
@example(income=Decimal(335_000), raise_by=1, residency='resident')
@example(income=Decimal(410_000), raise_by=1, residency='resident')
@example(income=Decimal(485_000), raise_by=1, residency='resident')
@example(income=Decimal(10_000_000), raise_by=1, residency='resident')
@example(income=Decimal(335_000), raise_by=1, residency='non_resident')
@example(income=Decimal(410_000), raise_by=1, residency='non_resident')
@example(income=Decimal(10_000_000), raise_by=1, residency='non_resident')
def test_paye_never_goes_down_when_income_goes_up(income, raise_by, residency):
    # a small raise from just below a band edge crosses it, which is where
    # a mistake in the config would make tax jump down
    assert paye_for(income, residency) <= paye_for(income + raise_by, residency)


@given(income=incomes, residency=residencies)
def test_paye_never_exceeds_income(income, residency):
    assert paye_for(income, residency) <= income
