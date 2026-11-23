import re
from decimal import Decimal
from importlib import import_module

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

money = import_module("src.money")


def _assert_invalid_amount(text: str) -> None:
    message = "the amount must be a number from 0.01 to 1000000.00 with at most two decimals"
    with pytest.raises(ValueError, match=rf"^{re.escape(message)}\Z"):
        money.parse_amount(text)


def test_ledg_002_ex_002_three_decimals_are_refused() -> None:
    _assert_invalid_amount("12.345")


def test_ledg_002_ex_003_zero_is_refused() -> None:
    _assert_invalid_amount("0")


def test_ledg_002_ex_004_upper_limit() -> None:
    assert money.parse_amount("999999.99") == 99_999_999
    assert money.parse_amount("1000000.00") == 100_000_000
    _assert_invalid_amount("1000000.01")


@pytest.mark.parametrize(("text", "cents"), [("0.01", 1), ("0.02", 2), ("3", 300), ("4.1", 410)])
def test_ledg_002_valid_amount_in_cents(text: str, cents: int) -> None:
    result = money.parse_amount(text)
    assert type(result) is int
    assert result == cents


@pytest.mark.parametrize("text", ["", "five", "-0.01", "0.010", "NaN", "Infinity"])
def test_ledg_002_invalid_amount_is_refused(text: str) -> None:
    _assert_invalid_amount(text)


@given(amount=st.decimals(min_value=Decimal("0.01"), max_value=Decimal("1000000.00"), places=2))
@settings(max_examples=50, derandomize=True)
def test_ledg_002_valid_decimal_amount_preserves_every_cent(amount: Decimal) -> None:
    assert money.parse_amount(str(amount)) == amount * 100


@pytest.mark.parametrize(("cents", "expected"), [(0, "0.00"), (1, "0.01"), (1250, "12.50")])
def test_ledg_004_format_amount_has_two_decimals(cents: int, expected: str) -> None:
    assert money.format_amount(cents) == expected
