import re

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.slug import make_slug


@settings(max_examples=50, derandomize=True)
@given(prefix=st.text(), suffix=st.text(), max_length=st.integers(min_value=1, max_value=200))
def test_slug_001_slug_holds_only_safe_characters(
    prefix: str, suffix: str, max_length: int
) -> None:
    title = f"{prefix}7{suffix}"
    slug = make_slug(title, max_length)
    assert re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug)
    assert len(slug) <= max_length


def test_slug_001_ex_001_hello_world() -> None:
    assert make_slug("Hello, World!") == "hello-world"


def test_slug_002_ex_002_accents_become_plain_letters() -> None:
    assert make_slug("Crème Brûlée") == "creme-brulee"


def test_slug_002_ex_009_kelvin_sign_becomes_k() -> None:
    assert make_slug("50 \N{KELVIN SIGN}") == "50-k"


def test_slug_002_ex_010_letters_without_ascii_form_are_dropped() -> None:
    assert make_slug("日本 Tokyo") == "tokyo"


def test_slug_002_drops_letters_without_ascii_form_inside_a_word() -> None:
    assert make_slug("a日本b") == "ab"


def test_slug_002_expands_compatibility_ligature() -> None:
    assert make_slug("o\N{LATIN SMALL LIGATURE FFI}ce") == "office"


def test_slug_003_ex_003_runs_of_symbols_become_one_hyphen() -> None:
    assert make_slug("  --Rock & Roll--  ") == "rock-roll"


def test_slug_004_ex_004_cut_keeps_whole_words() -> None:
    assert make_slug("The quick brown fox jumps", 15) == "the-quick-brown"


@pytest.mark.parametrize(
    ("max_length", "expected"),
    [(8, "red"), (9, "red-green"), (10, "red-green")],
)
def test_slug_004_stops_at_last_complete_word(max_length: int, expected: str) -> None:
    assert make_slug("Red green x", max_length) == expected


def test_slug_004_ex_005_long_first_word_is_cut() -> None:
    assert make_slug("Supercalifragilistic", 5) == "super"


@pytest.mark.parametrize("title", ["", "!!!", "日本"])
def test_slug_006_empty_slug_raises_value_error(title: str) -> None:
    with pytest.raises(ValueError, match=r"^the title has no letters or digits\Z"):
        make_slug(title)
