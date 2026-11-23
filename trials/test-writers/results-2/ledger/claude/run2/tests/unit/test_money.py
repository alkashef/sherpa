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


def test_ledg_002_ex_004_above_upper_limit_is_refused() -> None:
    with pytest.raises(ValueError, match=AMOUNT_ERROR_PATTERN):
        parse_amount("1000000.01")


def test_ledg_002_lower_limit() -> None:
    assert parse_amount("0.01") == 1


def test_ledg_002_below_lower_limit_is_refused() -> None:
    with pytest.raises(ValueError, match=AMOUNT_ERROR_PATTERN):
        parse_amount("0.00")


@pytest.mark.parametrize(
    ("text", "cents"),
    [
        ("12.50", 1250),
        ("12.5", 1250),
        ("7.25", 725),
        ("3", 300),
        ("4.10", 410),
        ("2", 200),
        ("999999.99", 99_999_999),
    ],
)
def test_ledg_002_valid_amount_becomes_cents(text: str, cents: int) -> None:
    assert parse_amount(text) == cents


@pytest.mark.parametrize(
    "text",
    ["abc", "", "-1", "-0.01", "12,50", "1.2.3", "nan", "inf", "2000000"],
)
def test_ledg_002_text_that_is_not_a_valid_amount_is_refused(text: str) -> None:
    with pytest.raises(ValueError, match=AMOUNT_ERROR_PATTERN):
        parse_amount(text)


@pytest.mark.parametrize(
    ("cents", "text"),
    [
        (1250, "12.50"),
        (300, "3.00"),
        (410, "4.10"),
        (1, "0.01"),
        (0, "0.00"),
        (2275, "22.75"),
        (100_000_000, "1000000.00"),
    ],
)
def test_dec_002_format_amount_gives_two_decimals(cents: int, text: str) -> None:
    assert format_amount(cents) == text


@settings(max_examples=50)
@given(st.integers(min_value=1, max_value=100_000_000))
def test_ledg_002_every_amount_in_range_is_accepted(cents: int) -> None:
    assert parse_amount(format_amount(cents)) == cents


@settings(max_examples=50)
@given(
    st.integers(min_value=0, max_value=999_999),
    st.integers(min_value=0, max_value=99),
    st.integers(min_value=1, max_value=9),
)
def test_ledg_002_every_amount_with_three_decimals_is_refused(
    whole: int, first_two: int, third: int
) -> None:
    text = f"{whole}.{first_two:02d}{third}"
    with pytest.raises(ValueError, match=AMOUNT_ERROR_PATTERN):
        parse_amount(text)
