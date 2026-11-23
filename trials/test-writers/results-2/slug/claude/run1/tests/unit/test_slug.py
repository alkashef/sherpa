import re

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.slug import make_slug

SAFE_CHARACTERS = re.compile(r"[a-z0-9-]+")
CLEAN_HYPHENS = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
KELVIN_SIGN = chr(0x212A)
LATIN_SMALL_LIGATURE_FI = chr(0xFB01)


# SLUG-001


@given(title=st.text(), max_length=st.integers(min_value=1, max_value=200))
@settings(max_examples=50, derandomize=True)
def test_slug_001_slug_holds_only_safe_characters(title: str, max_length: int) -> None:
    slug = make_slug(f"Word {title}", max_length)

    assert SAFE_CHARACTERS.fullmatch(slug)


def test_slug_001_ex_001_hello_world() -> None:
    assert make_slug("Hello, World!") == "hello-world"


def test_slug_001_uppercase_becomes_lowercase() -> None:
    assert make_slug("ABC") == "abc"


def test_slug_001_digits_are_kept() -> None:
    assert make_slug("Top 10 Tips") == "top-10-tips"


# SLUG-002


def test_slug_002_ex_002_accents_become_plain_letters() -> None:
    assert make_slug("Crème Brûlée") == "creme-brulee"


def test_slug_002_ex_009_kelvin_sign_becomes_k() -> None:
    assert make_slug(f"50 {KELVIN_SIGN}") == "50-k"


def test_slug_002_ex_010_letters_without_ascii_form_are_dropped() -> None:
    assert make_slug("日本 Tokyo") == "tokyo"


def test_slug_002_ligature_compatibility_form_becomes_plain_letters() -> None:
    assert make_slug(f"{LATIN_SMALL_LIGATURE_FI}le") == "file"


# SLUG-003


def test_slug_003_ex_003_runs_of_symbols_become_one_hyphen() -> None:
    assert make_slug("  --Rock & Roll--  ") == "rock-roll"


def test_slug_003_underscore_becomes_hyphen() -> None:
    assert make_slug("snake_case") == "snake-case"


@given(title=st.text(), max_length=st.integers(min_value=1, max_value=200))
@settings(max_examples=50, derandomize=True)
def test_slug_003_slug_has_no_edge_or_double_hyphens(title: str, max_length: int) -> None:
    slug = make_slug(f"Word {title}", max_length)

    assert CLEAN_HYPHENS.fullmatch(slug)


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
def test_slug_004_slug_at_maximum_length_is_not_cut(max_length: int, expected: str) -> None:
    assert make_slug("Hello World", max_length) == expected


def test_slug_004_cut_does_not_end_with_hyphen() -> None:
    assert make_slug("Hello World", 6) == "hello"


def test_slug_004_maximum_length_1_keeps_first_character() -> None:
    assert make_slug("Hello", 1) == "h"


def test_slug_004_maximum_length_200_keeps_200_characters() -> None:
    assert make_slug("a" * 250, 200) == "a" * 200


def test_slug_004_default_maximum_length_is_60() -> None:
    assert make_slug(f"{'a' * 30} {'b' * 30}") == "a" * 30


def test_slug_004_slug_of_60_characters_is_not_cut_by_default() -> None:
    title = f"{'a' * 29} {'b' * 30}"

    assert make_slug(title) == f"{'a' * 29}-{'b' * 30}"


@given(title=st.text(), max_length=st.integers(min_value=1, max_value=200))
@settings(max_examples=50, derandomize=True)
def test_slug_004_slug_is_never_longer_than_maximum_length(title: str, max_length: int) -> None:
    slug = make_slug(f"Word {title}", max_length)

    assert len(slug) <= max_length


# SLUG-006


def test_slug_006_empty_slug_raises_value_error() -> None:
    with pytest.raises(ValueError, match=r"^the title has no letters or digits$"):
        make_slug("!!!")


@pytest.mark.parametrize("title", ["", "   ", "日本"])
def test_slug_006_title_without_ascii_letters_raises_value_error(title: str) -> None:
    with pytest.raises(ValueError, match=r"^the title has no letters or digits$"):
        make_slug(title)
