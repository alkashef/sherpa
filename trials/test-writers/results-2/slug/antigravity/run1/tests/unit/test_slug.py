import re
import string

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.slug import make_slug


@given(
    prefix=st.text(),
    core=st.text(alphabet=string.ascii_letters + string.digits, min_size=1),
    suffix=st.text(),
)
@settings(max_examples=50)
def test_slug_001_slug_holds_only_safe_characters(prefix: str, core: str, suffix: str) -> None:
    slug = make_slug(prefix + core + suffix)
    assert re.fullmatch(r"[a-z0-9-]+", slug) is not None


def test_slug_001_ex_001_hello_world() -> None:
    assert make_slug("Hello, World!") == "hello-world"


def test_slug_001_keeps_digits_and_lowercases_ascii() -> None:
    assert make_slug("Python 312 Release") == "python-312-release"


def test_slug_002_ex_002_accents_become_plain_letters() -> None:
    assert make_slug("Crème Brûlée") == "creme-brulee"


def test_slug_002_ex_009_kelvin_sign_becomes_k() -> None:
    assert make_slug("50 \u212a") == "50-k"


def test_slug_002_ex_010_letters_without_ascii_form_are_dropped() -> None:
    assert make_slug("日本 Tokyo") == "tokyo"


def test_slug_003_ex_003_runs_of_symbols_become_one_hyphen() -> None:
    assert make_slug("  --Rock & Roll--  ") == "rock-roll"


def test_slug_003_underscores_become_hyphens() -> None:
    assert make_slug("foo_bar___baz") == "foo-bar-baz"


@given(
    prefix=st.text(),
    core=st.text(alphabet=string.ascii_letters + string.digits, min_size=1),
    suffix=st.text(),
)
@settings(max_examples=50)
def test_slug_003_no_edge_or_repeated_hyphens(prefix: str, core: str, suffix: str) -> None:
    slug = make_slug(prefix + core + suffix)
    assert not slug.startswith("-")
    assert not slug.endswith("-")
    assert "--" not in slug


def test_slug_004_ex_004_cut_keeps_whole_words() -> None:
    assert make_slug("The quick brown fox jumps", max_length=15) == "the-quick-brown"


def test_slug_004_ex_005_long_first_word_is_cut() -> None:
    assert make_slug("Supercalifragilistic", max_length=5) == "super"


def test_slug_004_default_max_length_is_60() -> None:
    assert make_slug("a" * 61) == "a" * 60


def test_slug_004_exact_max_length_is_not_cut() -> None:
    assert make_slug("one two three", max_length=13) == "one-two-three"


def test_slug_004_one_below_length_drops_last_word() -> None:
    assert make_slug("one two three", max_length=12) == "one-two"


def test_slug_004_one_above_length_keeps_full_slug() -> None:
    assert make_slug("one two three", max_length=14) == "one-two-three"


def test_slug_004_cut_at_hyphen_drops_trailing_hyphen() -> None:
    assert make_slug("the quick brown fox", max_length=16) == "the-quick-brown"


def test_slug_004_max_length_one_keeps_single_character() -> None:
    assert make_slug("hello", max_length=1) == "h"


def test_slug_004_max_length_200_cuts_at_200() -> None:
    assert make_slug("a" * 205, max_length=200) == "a" * 200


@given(
    prefix=st.text(),
    core=st.text(alphabet=string.ascii_letters + string.digits, min_size=1),
    suffix=st.text(),
    max_length=st.integers(min_value=1, max_value=200),
)
@settings(max_examples=50)
def test_slug_004_slug_never_exceeds_max_length(
    prefix: str, core: str, suffix: str, max_length: int
) -> None:
    slug = make_slug(prefix + core + suffix, max_length=max_length)
    assert 1 <= len(slug) <= max_length


def test_slug_006_empty_slug_raises_value_error() -> None:
    with pytest.raises(ValueError, match=r"^the title has no letters or digits$"):
        make_slug("!!!")


def test_slug_006_empty_string_raises_value_error() -> None:
    with pytest.raises(ValueError, match=r"^the title has no letters or digits$"):
        make_slug("")


def test_slug_006_non_ascii_only_raises_value_error() -> None:
    with pytest.raises(ValueError, match=r"^the title has no letters or digits$"):
        make_slug("日本語")
