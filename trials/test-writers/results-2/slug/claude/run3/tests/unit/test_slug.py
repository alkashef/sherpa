"""Unit tests of `src.slug.make_slug` (SLUG-001 to SLUG-004, SLUG-006)."""

import re

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.slug import make_slug

_SAFE_CHARACTERS = re.compile(r"[a-z0-9-]+")
_WORDS_AND_SINGLE_HYPHENS = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
_EMPTY_SLUG_MESSAGE = "the title has no letters or digits"
_KELVIN_SIGN = chr(0x212A)


def _slug_or_none(title: str, max_length: int) -> str | None:
    """Return the slug, or None when the title gives an empty slug (SLUG-006)."""
    try:
        slug: str = make_slug(title, max_length)
    except ValueError:
        return None
    return slug


# SLUG-001


@settings(max_examples=50)
@given(title=st.text(), max_length=st.integers(min_value=1, max_value=200))
def test_slug_001_slug_holds_only_safe_characters(title: str, max_length: int) -> None:
    slug = _slug_or_none(title, max_length)
    if slug is not None:
        assert _SAFE_CHARACTERS.fullmatch(slug)


def test_slug_001_ex_001_hello_world() -> None:
    assert make_slug("Hello, World!") == "hello-world"


def test_slug_001_uppercase_letters_become_lowercase() -> None:
    assert make_slug("ABC Def 123") == "abc-def-123"


# SLUG-002


def test_slug_002_ex_002_accents_become_plain_letters() -> None:
    assert make_slug("Crème Brûlée") == "creme-brulee"


def test_slug_002_ex_009_kelvin_sign_becomes_k() -> None:
    assert make_slug(f"50 {_KELVIN_SIGN}") == "50-k"


def test_slug_002_ex_010_letters_without_ascii_form_are_dropped() -> None:
    assert make_slug("日本 Tokyo") == "tokyo"


# SLUG-003


def test_slug_003_ex_003_runs_of_symbols_become_one_hyphen() -> None:
    assert make_slug("  --Rock & Roll--  ") == "rock-roll"


@settings(max_examples=50)
@given(title=st.text(), max_length=st.integers(min_value=1, max_value=200))
def test_slug_003_slug_has_no_edge_or_double_hyphens(title: str, max_length: int) -> None:
    slug = _slug_or_none(title, max_length)
    if slug is not None:
        assert _WORDS_AND_SINGLE_HYPHENS.fullmatch(slug)


# SLUG-004


def test_slug_004_ex_004_cut_keeps_whole_words() -> None:
    assert make_slug("The quick brown fox jumps", 15) == "the-quick-brown"


def test_slug_004_ex_005_long_first_word_is_cut() -> None:
    assert make_slug("Supercalifragilistic", 5) == "super"


@pytest.mark.parametrize(
    ("max_length", "expected"),
    [
        (10, "hello"),
        (11, "hello-world"),
        (12, "hello-world"),
    ],
)
def test_slug_004_slug_at_maximum_length_is_kept(max_length: int, expected: str) -> None:
    assert make_slug("Hello World", max_length) == expected


def test_slug_004_cut_leaves_no_trailing_hyphen() -> None:
    assert make_slug("Hello World", 6) == "hello"


def test_slug_004_maximum_length_1_keeps_first_character() -> None:
    assert make_slug("Hello", 1) == "h"


def test_slug_004_maximum_length_200_keeps_200_characters() -> None:
    assert make_slug("a" * 201, 200) == "a" * 200


def test_slug_004_default_maximum_length_is_60() -> None:
    assert make_slug("a" * 61) == "a" * 60


def test_slug_004_default_keeps_slug_of_60_characters() -> None:
    assert make_slug("a" * 60) == "a" * 60


@settings(max_examples=50)
@given(title=st.text(), max_length=st.integers(min_value=1, max_value=200))
def test_slug_004_slug_fits_maximum_length(title: str, max_length: int) -> None:
    slug = _slug_or_none(title, max_length)
    if slug is not None:
        assert len(slug) <= max_length


# SLUG-006


@pytest.mark.parametrize("title", ["!!!", "", "   ", "日本"])
def test_slug_006_empty_slug_raises_value_error(title: str) -> None:
    with pytest.raises(ValueError, match=f"^{_EMPTY_SLUG_MESSAGE}$"):
        make_slug(title)
