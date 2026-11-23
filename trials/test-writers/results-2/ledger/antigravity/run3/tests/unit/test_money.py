import re

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.money import format_amount, parse_amount

AMOUNT_ERROR = r"^the amount must be a number from 0\.01 to 1000000\.00 with at most two decimals$"


def test_ledg_002_ex_002_three_decimals_are_refused() -> None:
    with pytest.raises(ValueError, match=AMOUNT_ERROR):
        parse_amount("12.345")


@pytest.mark.parametrize("text", ["0", "0.00"])
def test_ledg_002_ex_003_zero_is_refused(text: str) -> None:
    with pytest.raises(ValueError, match=AMOUNT_ERROR):
        parse_amount(text)


def test_ledg_002_ex_004_upper_limit() -> None:
    assert parse_amount("999999.99") == 99_999_999
    assert parse_amount("1000000.00") == 100_000_000
    assert parse_amount("1000000") == 100_000_000
    with pytest.raises(ValueError, match=AMOUNT_ERROR):
        parse_amount("1000000.01")


def test_ledg_002_lower_limit() -> None:
    assert parse_amount("0.01") == 1
    assert parse_amount("0.02") == 2
    with pytest.raises(ValueError, match=AMOUNT_ERROR):
        parse_amount("-0.01")


@pytest.mark.parametrize(
    ("text", "expected_cents"),
    [
        ("1", 100),
        ("3", 300),
        ("0.1", 10),
        ("12.5", 1250),
        ("12.50", 1250),
        ("4.10", 410),
    ],
)
def test_ledg_002_valid_amounts_parse_to_cents(text: str, expected_cents: int) -> None:
    assert parse_amount(text) == expected_cents


@pytest.mark.parametrize(
    "text",
    [
        "",
        "abc",
        "-5",
        "12,50",
        "1.2.3",
        "0.001",
        "1.000",
        "nan",
        "inf",
    ],
)
def test_ledg_002_invalid_amount_strings_are_refused(text: str) -> None:
    with pytest.raises(ValueError, match=AMOUNT_ERROR):
        parse_amount(text)


@pytest.mark.parametrize(
    ("cents", "expected_text"),
    [
        (0, "0.00"),
        (1, "0.01"),
        (10, "0.10"),
        (1250, "12.50"),
        (2275, "22.75"),
        (100_000_000, "1000000.00"),
    ],
)
def test_ledg_004_format_amount_outputs_two_decimals(cents: int, expected_text: str) -> None:
    assert format_amount(cents) == expected_text


@settings(max_examples=50, derandomize=True)
@given(st.integers(min_value=1, max_value=100_000_000))
def test_ledg_002_round_trip_valid_amounts(cents: int) -> None:
    text = format_amount(cents)
    assert re.fullmatch(r"\d+\.\d{2}", text) is not None
    assert parse_amount(text) == cents


@settings(max_examples=50, derandomize=True)
@given(
    st.one_of(
        st.integers(max_value=0),
        st.integers(min_value=100_000_001),
    )
)
def test_ledg_002_out_of_range_amounts_are_refused(cents: int) -> None:
    sign = "-" if cents < 0 else ""
    whole, frac = divmod(abs(cents), 100)
    text = f"{sign}{whole}.{frac:02d}"
    with pytest.raises(ValueError, match=AMOUNT_ERROR):
        parse_amount(text)
