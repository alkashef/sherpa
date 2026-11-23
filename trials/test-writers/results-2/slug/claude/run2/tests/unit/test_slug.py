import re
import string

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.slug import make_slug

_SAFE_CHARACTERS = re.compile(r"[a-z0-9-]+")
_HYPHEN_JOINED_WORDS = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")

# Any text with one ASCII letter in it: NFKD keeps ASCII letters, so the slug is never empty.
_TITLES_WITH_A_LETTER = st.tuples(
    st.text(max_size=80),
    st.sampled_from(string.ascii_letters),
    st.text(max_size=80),
).map("".join)


@settings(max_examples=50)
@given(title=_TITLES_WITH_A_LETTER)
def test_slug_001_slug_holds_only_safe_characters(title: str) -> None:
    assert _SAFE_CHARACTERS.fullmatch(make_slug(title))


def test_slug_001_ex_001_hello_world() -> None:
    assert make_slug("Hello, World!") == "hello-world"


def test_slug_002_ex_002_accents_become_plain_letters() -> None:
    assert make_slug("Crème Brûlée") == "creme-brulee"


def test_slug_002_ex_009_kelvin_sign_becomes_k() -> None:
    kelvin_sign = chr(0x212A)
    assert make_slug(f"50 {kelvin_sign}") == "50-k"


def test_slug_002_ex_010_letters_without_ascii_form_are_dropped() -> None:
    assert make_slug("日本 Tokyo") == "tokyo"


def test_slug_003_ex_003_runs_of_symbols_become_one_hyphen() -> None:
    assert make_slug("  --Rock & Roll--  ") == "rock-roll"


@settings(max_examples=50)
@given(title=_TITLES_WITH_A_LETTER)
def test_slug_003_no_double_or_edge_hyphens(title: str) -> None:
    assert _HYPHEN_JOINED_WORDS.fullmatch(make_slug(title))


def test_slug_004_ex_004_cut_keeps_whole_words() -> None:
    assert make_slug("The quick brown fox jumps", 15) == "the-quick-brown"


def test_slug_004_ex_005_long_first_word_is_cut() -> None:
    assert make_slug("Supercalifragilistic", 5) == "super"


def test_slug_004_cut_one_below_word_end_drops_last_word() -> None:
    assert make_slug("The quick brown fox jumps", 14) == "the-quick"


def test_slug_004_cut_one_above_word_end_keeps_whole_words() -> None:
    assert make_slug("The quick brown fox jumps", 16) == "the-quick-brown"


def test_slug_004_slug_shorter_than_maximum_is_kept() -> None:
    assert make_slug("Hello World", 11) == "hello-world"


def test_slug_004_default_maximum_length_is_60() -> None:
    assert make_slug("x" * 61) == "x" * 60


def test_slug_004_default_keeps_slug_of_60() -> None:
    assert make_slug("x" * 60) == "x" * 60


def test_slug_004_maximum_length_1() -> None:
    assert make_slug("Hello", 1) == "h"


def test_slug_004_maximum_length_200() -> None:
    assert make_slug("x" * 201, 200) == "x" * 200


@settings(max_examples=50)
@given(title=_TITLES_WITH_A_LETTER, max_length=st.integers(min_value=1, max_value=200))
def test_slug_004_slug_never_longer_than_maximum(title: str, max_length: int) -> None:
    slug = make_slug(title, max_length)
    assert 1 <= len(slug) <= max_length
    assert _HYPHEN_JOINED_WORDS.fullmatch(slug)


@pytest.mark.parametrize("title", ["!!!", "", "   ", "日本"])
def test_slug_006_empty_slug_raises_value_error(title: str) -> None:
    with pytest.raises(ValueError, match=r"^the title has no letters or digits$"):
        make_slug(title)
