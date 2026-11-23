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
    slug = make_slug(f"{prefix}7{suffix}", max_length)

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


def test_slug_002_letters_without_ascii_form_inside_word_are_dropped() -> None:
    assert make_slug("Go日本Now") == "gonow"


def test_slug_003_ex_003_runs_of_symbols_become_one_hyphen() -> None:
    assert make_slug("  --Rock & Roll--  ") == "rock-roll"


@pytest.mark.parametrize(
    ("max_length", "expected"),
    [(14, "the-quick"), (15, "the-quick-brown"), (16, "the-quick-brown")],
)
def test_slug_004_ex_004_cut_keeps_whole_words(max_length: int, expected: str) -> None:
    assert make_slug("The quick brown fox jumps", max_length) == expected


def test_slug_004_ex_005_long_first_word_is_cut() -> None:
    assert make_slug("Supercalifragilistic", 5) == "super"


@pytest.mark.parametrize(("length", "expected_length"), [(59, 59), (60, 60), (61, 60)])
def test_slug_004_default_maximum_length(length: int, expected_length: int) -> None:
    assert make_slug("A" * length) == "a" * expected_length


@pytest.mark.parametrize("title", ["!!!", "", "日本"])
def test_slug_006_empty_slug_raises_value_error(title: str) -> None:
    with pytest.raises(ValueError, match=r"^the title has no letters or digits\Z"):
        make_slug(title)
