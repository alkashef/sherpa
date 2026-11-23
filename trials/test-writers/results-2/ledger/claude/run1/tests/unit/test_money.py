import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.money import format_amount, parse_amount

AMOUNT_ERROR = "the amount must be a number from 0.01 to 1000000.00 with at most two decimals"


def test_ledg_002_ex_002_three_decimals_are_refused() -> None:
    with pytest.raises(ValueError, match=AMOUNT_ERROR):
        parse_amount("12.345")


def test_ledg_002_ex_003_zero_is_refused() -> None:
    with pytest.raises(ValueError, match=AMOUNT_ERROR):
        parse_amount("0")


def test_ledg_002_ex_004_upper_limit() -> None:
    assert parse_amount("1000000.00") == 100000000
    with pytest.raises(ValueError, match=AMOUNT_ERROR):
        parse_amount("1000000.01")


@pytest.mark.parametrize(
    ("text", "cents"),
    [
        ("12.50", 1250),
        ("7.25", 725),
        ("3", 300),
        ("4.10", 410),
        ("4.1", 410),
        ("0.01", 1),
        ("999999.99", 99999999),
        ("1000000", 100000000),
    ],
)
def test_ledg_002_valid_amount_gives_cents(text: str, cents: int) -> None:
    assert parse_amount(text) == cents


@pytest.mark.parametrize(
    "text",
    ["0.00", "0.009", "-5", "-0.01", "abc", "", "12,50", "1000001", "nan", "inf"],
)
def test_ledg_002_invalid_amount_is_refused(text: str) -> None:
    with pytest.raises(ValueError, match=AMOUNT_ERROR):
        parse_amount(text)


@pytest.mark.parametrize(
    ("cents", "text"),
    [(1250, "12.50"), (300, "3.00"), (410, "4.10"), (1, "0.01"), (0, "0.00")],
)
def test_ledg_004_format_amount_has_two_decimals(cents: int, text: str) -> None:
    assert format_amount(cents) == text


def test_ledg_004_format_amount_of_the_largest_amount() -> None:
    assert format_amount(100000000) == "1000000.00"


@settings(max_examples=50)
@given(st.integers(min_value=1, max_value=100000000))
def test_ledg_002_every_valid_amount_round_trips(cents: int) -> None:
    assert parse_amount(format_amount(cents)) == cents
