import pytest
from emi import amortisation_schedule, emi


def test_known_value():
    assert round(emi(1_000_000, 9, 20), 2) == 8997.26


def test_higher_rate_costs_more():
    assert emi(1_000_000, 10, 20) > emi(1_000_000, 9, 20)


def test_zero_rate():
    assert emi(1_200_000, 0, 10) == 10_000


def test_bad_tenure():
    with pytest.raises(ValueError):
        emi(100_000, 9, 0)


def test_schedule_closes_to_the_paisa():
    rows = amortisation_schedule(1_000_000, 9, 20)
    assert len(rows) == 240 and rows[-1]["balance"] == 0.0
    assert round(sum(r["principal"] for r in rows), 2) == 1_000_000.00
