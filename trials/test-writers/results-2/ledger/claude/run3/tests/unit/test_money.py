"""Unit tests of src/money.py: the text of an amount to cents, and back (LEDG-002, DEC-002)."""

import re

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.money import format_amount, parse_amount

AMOUNT_ERROR = re.escape(
    "the amount must be a number from 0.01 to 1000000.00 with at most two decimals"
)


def test_ledg_002_ex_002_three_decimals_are_refused() -> None:
    with pytest.raises(ValueError, match=AMOUNT_ERROR):
        parse_amount("12.345")


def test_ledg_002_ex_003_zero_is_refused() -> None:
    with pytest.raises(ValueError, match=AMOUNT_ERROR):
        parse_amount("0")


def test_ledg_002_ex_004_upper_limit() -> None:
    assert parse_amount("1000000.00") == 100_000_000


def test_ledg_002_ex_004_one_cent_over_the_upper_limit_is_refused() -> None:
    with pytest.raises(ValueError, match=AMOUNT_ERROR):
        parse_amount("1000000.01")


def test_ledg_002_lower_limit() -> None:
    assert parse_amount("0.01") == 1


def test_ledg_002_one_cent_under_the_lower_limit_is_refused() -> None:
    with pytest.raises(ValueError, match=AMOUNT_ERROR):
        parse_amount("0.00")


@pytest.mark.parametrize(
    ("text", "cents"),
    [("12.50", 1250), ("12.5", 1250), ("7.25", 725), ("3", 300), ("0.10", 10)],
)
def test_ledg_002_valid_amount_gives_cents(text: str, cents: int) -> None:
    assert parse_amount(text) == cents


@pytest.mark.parametrize(
    "text",
    ["", "abc", "-5.00", "-0.01", "1000001", "0.001", "1.2.3", "nan", "inf"],
)
def test_ledg_002_invalid_amount_is_refused(text: str) -> None:
    with pytest.raises(ValueError, match=AMOUNT_ERROR):
        parse_amount(text)


@settings(max_examples=50)
@given(st.integers(min_value=1, max_value=100_000_000))
def test_ledg_002_every_amount_in_range_with_two_decimals_is_accepted(cents: int) -> None:
    assert parse_amount(f"{cents // 100}.{cents % 100:02d}") == cents


@settings(max_examples=50)
@given(st.integers(min_value=1, max_value=100_000_000))
def test_ledg_002_every_amount_with_three_decimals_is_refused(cents: int) -> None:
    with pytest.raises(ValueError, match=AMOUNT_ERROR):
        parse_amount(f"{cents // 100}.{cents % 100:02d}1")


@pytest.mark.parametrize(
    ("cents", "text"),
    [(1250, "12.50"), (300, "3.00"), (5, "0.05"), (0, "0.00"), (100_000_000, "1000000.00")],
)
def test_ledg_004_format_amount_gives_two_decimals(cents: int, text: str) -> None:
    assert format_amount(cents) == text


@settings(max_examples=50)
@given(st.integers(min_value=1, max_value=100_000_000))
def test_ledg_004_format_amount_round_trips_through_parse_amount(cents: int) -> None:
    assert parse_amount(format_amount(cents)) == cents
