import re

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.money import format_amount, parse_amount

AMOUNT_ERROR = "the amount must be a number from 0.01 to 1000000.00 with at most two decimals"
AMOUNT_ERROR_PATTERN = f"^{re.escape(AMOUNT_ERROR)}$"


def test_ledg_002_ex_002_three_decimals_are_refused() -> None:
    with pytest.raises(ValueError, match=AMOUNT_ERROR_PATTERN):
        parse_amount("12.345")


def test_ledg_002_ex_003_zero_is_refused() -> None:
    with pytest.raises(ValueError, match=AMOUNT_ERROR_PATTERN):
        parse_amount("0")


def test_ledg_002_ex_004_upper_limit() -> None:
    assert parse_amount("1000000.00") == 100_000_000
    with pytest.raises(ValueError, match=AMOUNT_ERROR_PATTERN):
        parse_amount("1000000.01")


def test_ledg_002_lower_limit_and_below() -> None:
    assert parse_amount("0.01") == 1
    with pytest.raises(ValueError, match=AMOUNT_ERROR_PATTERN):
        parse_amount("0.00")
    with pytest.raises(ValueError, match=AMOUNT_ERROR_PATTERN):
        parse_amount("-0.01")


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("1", 100),
        ("12.5", 1250),
        ("0.10", 10),
        ("12.50", 1250),
        ("1000000", 100_000_000),
    ],
)
def test_ledg_002_valid_whole_and_one_decimal_amounts(text: str, expected: int) -> None:
    assert parse_amount(text) == expected


@pytest.mark.parametrize("text", ["", "abc", "-5", "12.3.4", "12,50"])
def test_ledg_002_non_numeric_amounts_are_refused(text: str) -> None:
    with pytest.raises(ValueError, match=AMOUNT_ERROR_PATTERN):
        parse_amount(text)


@given(cents=st.integers(min_value=1, max_value=100_000_000))
@settings(max_examples=50)
def test_ledg_002_format_and_parse_round_trip(cents: int) -> None:
    formatted = format_amount(cents)
    assert re.fullmatch(r"\d+\.\d{2}", formatted)
    assert parse_amount(formatted) == cents


@given(
    whole=st.integers(min_value=0, max_value=999_999),
    frac=st.integers(min_value=0, max_value=999),
)
@settings(max_examples=50)
def test_ledg_002_three_or_more_decimals_always_refused(whole: int, frac: int) -> None:
    with pytest.raises(ValueError, match=AMOUNT_ERROR_PATTERN):
        parse_amount(f"{whole}.{frac:03d}")


@pytest.mark.parametrize(
    ("cents", "expected"),
    [
        (0, "0.00"),
        (1, "0.01"),
        (10, "0.10"),
        (1250, "12.50"),
        (100_000_000, "1000000.00"),
    ],
)
def test_ledg_004_format_amount_formats_cents_with_two_decimals(cents: int, expected: str) -> None:
    assert format_amount(cents) == expected
