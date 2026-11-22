"""Amounts of money as whole cents (LEDG-002, LEDG-004, DEC-002)."""

import re

AMOUNT_ERROR = "the amount must be a number from 0.01 to 1000000.00 with at most two decimals"
MAX_CENTS = 100_000_000
AMOUNT = re.compile(r"(\d+)(?:\.(\d{1,2}))?")


def parse_amount(text: str) -> int:
    """Return the amount of a text in cents; raise ValueError when it is not valid."""
    match = AMOUNT.fullmatch(text)
    if match is None:
        raise ValueError(AMOUNT_ERROR)
    cents = int(match[1]) * 100 + int((match[2] or "0").ljust(2, "0"))
    if not 1 <= cents <= MAX_CENTS:
        raise ValueError(AMOUNT_ERROR)
    return cents


def format_amount(cents: int) -> str:
    """Return an amount of cents as text with two decimals."""
    return f"{cents // 100}.{cents % 100:02d}"
