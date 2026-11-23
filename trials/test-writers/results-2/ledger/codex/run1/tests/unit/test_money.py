import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.money import format_amount, parse_amount


def _assert_invalid_amount(text: str) -> None:
    message = r"^the amount must be a number from 0\.01 to 1000000\.00 with at most two decimals\Z"
    with pytest.raises(ValueError, match=message):
        parse_amount(text)


def test_ledg_002_ex_002_three_decimals_are_refused() -> None:
    _assert_invalid_amount("12.345")


def test_ledg_002_ex_003_zero_is_refused() -> None:
    _assert_invalid_amount("0")


def test_ledg_002_ex_004_upper_limit() -> None:
    assert parse_amount("999999.99") == 99_999_999
    assert parse_amount("1000000.00") == 100_000_000
    _assert_invalid_amount("1000000.01")


@pytest.mark.parametrize(("text", "cents"), [("0.01", 1), ("0.02", 2), ("4.1", 410), ("2", 200)])
def test_ledg_002_valid_amount_in_cents(text: str, cents: int) -> None:
    assert parse_amount(text) == cents


@pytest.mark.parametrize("text", ["", "lunch", "-0.01", "NaN", "Infinity", "12.340"])
def test_ledg_002_invalid_amount_is_refused(text: str) -> None:
    _assert_invalid_amount(text)


@settings(max_examples=50, derandomize=True)
@given(cents=st.integers(min_value=1, max_value=100_000_000))
def test_ledg_002_valid_two_decimal_amounts_preserve_cents(cents: int) -> None:
    euros, remainder = divmod(cents, 100)
    assert parse_amount(f"{euros}.{remainder:02d}") == cents


@pytest.mark.parametrize(
    ("cents", "text"), [(0, "0.00"), (1, "0.01"), (200, "2.00"), (1250, "12.50")]
)
def test_ledg_004_format_amount_has_two_decimals(cents: int, text: str) -> None:
    assert format_amount(cents) == text
