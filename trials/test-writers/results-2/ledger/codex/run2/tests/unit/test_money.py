from importlib import import_module

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

money = import_module("src.money")


def _assert_invalid_amount(text: str) -> None:
    with pytest.raises(
        ValueError,
        match=r"^the amount must be a number from 0\.01 to "
        r"1000000\.00 with at most two decimals\Z",
    ):
        money.parse_amount(text)


def test_ledg_002_ex_002_three_decimals_are_refused() -> None:
    _assert_invalid_amount("12.345")


def test_ledg_002_ex_003_zero_is_refused() -> None:
    _assert_invalid_amount("0")


def test_ledg_002_ex_004_upper_limit() -> None:
    assert money.parse_amount("999999.99") == 99_999_999
    assert money.parse_amount("1000000.00") == 100_000_000
    _assert_invalid_amount("1000000.01")


@pytest.mark.parametrize(("text", "cents"), [("0.01", 1), ("0.02", 2), ("4.1", 410), ("3", 300)])
def test_ledg_002_valid_amount_in_cents(text: str, cents: int) -> None:
    assert money.parse_amount(text) == cents


@pytest.mark.parametrize("text", ["-0.01", "", "lunch", "1.000", "NaN", "Infinity"])
def test_ledg_002_invalid_amount(text: str) -> None:
    _assert_invalid_amount(text)


@settings(max_examples=50, derandomize=True)
@given(cents=st.integers(min_value=1, max_value=100_000_000))
def test_ledg_002_each_two_decimal_amount_parses_to_whole_cents(cents: int) -> None:
    euros, remainder = divmod(cents, 100)
    parsed = money.parse_amount(f"{euros}.{remainder:02d}")
    assert type(parsed) is int
    assert parsed == cents


@pytest.mark.parametrize(
    ("cents", "text"), [(0, "0.00"), (1, "0.01"), (410, "4.10"), (300, "3.00")]
)
def test_ledg_004_format_amount(cents: int, text: str) -> None:
    assert money.format_amount(cents) == text
