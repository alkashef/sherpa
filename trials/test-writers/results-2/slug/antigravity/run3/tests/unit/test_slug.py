import re
import string

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.slug import make_slug


def _join_title(before: str, char: str, after: str) -> str:
    return f"{before}{char}{after}"


def _non_empty_titles() -> st.SearchStrategy[str]:
    alnum = st.sampled_from(string.ascii_letters + string.digits)
    return st.builds(_join_title, st.text(), alnum, st.text())


@given(title=_non_empty_titles(), max_length=st.integers(min_value=1, max_value=200))
@settings(max_examples=50, derandomize=True)
def test_slug_001_slug_holds_only_safe_characters(title: str, max_length: int) -> None:
    slug = make_slug(title, max_length=max_length)
    assert re.fullmatch(r"[a-z0-9-]+", slug) is not None


def test_slug_001_ex_001_hello_world() -> None:
    assert make_slug("Hello, World!") == "hello-world"


def test_slug_002_ex_002_accents_become_plain_letters() -> None:
    assert make_slug("Crème Brûlée") == "creme-brulee"


def test_slug_002_ex_009_kelvin_sign_becomes_k() -> None:
    assert make_slug("50 \u212a") == "50-k"


def test_slug_002_ex_010_letters_without_ascii_form_are_dropped() -> None:
    assert make_slug("日本 Tokyo") == "tokyo"


def test_slug_002_compatibility_ligature_becomes_plain_ascii() -> None:
    assert make_slug("\ufb01le") == "file"


def test_slug_003_ex_003_runs_of_symbols_become_one_hyphen() -> None:
    assert make_slug("  --Rock & Roll--  ") == "rock-roll"


def test_slug_003_underscores_become_hyphens() -> None:
    assert make_slug("hello_world__2026") == "hello-world-2026"


@given(title=_non_empty_titles(), max_length=st.integers(min_value=1, max_value=200))
@settings(max_examples=50, derandomize=True)
def test_slug_003_no_double_or_edge_hyphens(title: str, max_length: int) -> None:
    slug = make_slug(title, max_length=max_length)
    assert not slug.startswith("-")
    assert not slug.endswith("-")
    assert "--" not in slug


def test_slug_004_ex_004_cut_keeps_whole_words() -> None:
    assert make_slug("The quick brown fox jumps", max_length=15) == "the-quick-brown"


def test_slug_004_ex_005_long_first_word_is_cut() -> None:
    assert make_slug("Supercalifragilistic", max_length=5) == "super"


@pytest.mark.parametrize(
    ("title", "max_length", "expected"),
    [
        ("The quick brown fox jumps", 14, "the-quick"),
        ("The quick brown fox jumps", 16, "the-quick-brown"),
        ("alpha beta", 9, "alpha"),
        ("alpha beta", 10, "alpha-beta"),
        ("alpha beta", 11, "alpha-beta"),
    ],
)
def test_slug_004_word_cut_boundaries(title: str, max_length: int, expected: str) -> None:
    assert make_slug(title, max_length=max_length) == expected


@pytest.mark.parametrize(
    ("title", "max_length", "expected"),
    [
        ("Super", 1, "s"),
        ("Super", 4, "supe"),
        ("Super", 5, "super"),
        ("Super", 6, "super"),
    ],
)
def test_slug_004_first_word_cut_boundaries(title: str, max_length: int, expected: str) -> None:
    assert make_slug(title, max_length=max_length) == expected


@pytest.mark.parametrize(
    ("title", "expected"),
    [
        ("a" * 59, "a" * 59),
        ("a" * 60, "a" * 60),
        ("a" * 61, "a" * 60),
        ("word " * 13, "-".join(["word"] * 12)),
    ],
)
def test_slug_004_default_max_length_is_60(title: str, expected: str) -> None:
    assert make_slug(title) == expected


@given(title=_non_empty_titles(), max_length=st.integers(min_value=1, max_value=200))
@settings(max_examples=50, derandomize=True)
def test_slug_004_slug_never_exceeds_max_length(title: str, max_length: int) -> None:
    slug = make_slug(title, max_length=max_length)
    assert 1 <= len(slug) <= max_length


@pytest.mark.parametrize("title", ["", "!!!", "   ", "日本語"])
def test_slug_006_empty_slug_raises_value_error(title: str) -> None:
    with pytest.raises(ValueError, match=r"^the title has no letters or digits$"):
        make_slug(title)
