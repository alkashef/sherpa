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


@pytest.mark.parametrize("raw", ["0", "0.00"])
def test_ledg_002_ex_003_zero_is_refused(raw: str) -> None:
    with pytest.raises(ValueError, match=AMOUNT_ERROR_PATTERN):
        parse_amount(raw)


def test_ledg_002_ex_004_upper_limit() -> None:
    assert parse_amount("999999.99") == 99_999_999
    assert parse_amount("1000000.00") == 100_000_000
    assert parse_amount("1000000") == 100_000_000
    with pytest.raises(ValueError, match=AMOUNT_ERROR_PATTERN):
        parse_amount("1000000.01")


def test_ledg_002_lower_limit_and_neighbors() -> None:
    with pytest.raises(ValueError, match=AMOUNT_ERROR_PATTERN):
        parse_amount("0.00")
    assert parse_amount("0.01") == 1
    assert parse_amount("0.02") == 2


@pytest.mark.parametrize(
    ("raw", "expected_cents"),
    [
        ("1", 100),
        ("0.1", 10),
        ("0.10", 10),
        ("12.5", 1250),
        ("12.50", 1250),
        ("19.99", 1999),
    ],
)
def test_ledg_002_valid_amounts_return_exact_cents(raw: str, expected_cents: int) -> None:
    assert parse_amount(raw) == expected_cents


@pytest.mark.parametrize(
    "raw",
    [
        "-0.01",
        "-5",
        "abc",
        "",
        "1.2.3",
        "1,50",
        "NaN",
        "inf",
    ],
)
def test_ledg_002_invalid_amounts_raise_value_error(raw: str) -> None:
    with pytest.raises(ValueError, match=AMOUNT_ERROR_PATTERN):
        parse_amount(raw)


@pytest.mark.parametrize(
    ("cents", "expected_text"),
    [
        (0, "0.00"),
        (1, "0.01"),
        (10, "0.10"),
        (1250, "12.50"),
        (100_000_000, "1000000.00"),
    ],
)
def test_ledg_004_format_amount_outputs_two_decimals(cents: int, expected_text: str) -> None:
    assert format_amount(cents) == expected_text


@given(cents=st.integers(min_value=1, max_value=100_000_000))
@settings(max_examples=50)
def test_ledg_002_roundtrip_all_valid_cents(cents: int) -> None:
    formatted = format_amount(cents)
    assert re.fullmatch(r"\d+\.\d{2}", formatted) is not None
    assert parse_amount(formatted) == cents


@given(
    cents=st.one_of(
        st.integers(min_value=-100_000_000, max_value=0),
        st.integers(min_value=100_000_001, max_value=1_000_000_000),
    )
)
@settings(max_examples=50)
def test_ledg_002_out_of_range_amounts_are_refused(cents: int) -> None:
    sign = "-" if cents < 0 else ""
    whole, frac = divmod(abs(cents), 100)
    raw = f"{sign}{whole}.{frac:02d}"
    with pytest.raises(ValueError, match=AMOUNT_ERROR_PATTERN):
        parse_amount(raw)
