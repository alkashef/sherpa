import re
import string

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.slug import make_slug


def _titles_with_ascii_alnum() -> st.SearchStrategy[str]:
    alnum = string.ascii_letters + string.digits
    return st.tuples(
        st.text(max_size=30),
        st.text(alphabet=alnum, min_size=1, max_size=20),
        st.text(max_size=30),
    ).map("".join)


@given(
    title=_titles_with_ascii_alnum(),
    max_length=st.integers(min_value=1, max_value=200),
)
@settings(max_examples=50, derandomize=True)
def test_slug_001_slug_holds_only_safe_characters(title: str, max_length: int) -> None:
    slug = make_slug(title, max_length=max_length)

    assert slug != ""
    assert re.fullmatch(r"[a-z0-9-]+", slug) is not None


def test_slug_001_ex_001_hello_world() -> None:
    assert make_slug("Hello, World!") == "hello-world"


def test_slug_001_keeps_digits_and_lowercases_letters() -> None:
    assert make_slug("HTTP 200 OK") == "http-200-ok"


def test_slug_002_ex_002_accents_become_plain_letters() -> None:
    assert make_slug("Crème Brûlée") == "creme-brulee"


def test_slug_002_ex_009_kelvin_sign_becomes_k() -> None:
    assert make_slug("50 \u212a") == "50-k"


def test_slug_002_ex_010_letters_without_ascii_form_are_dropped() -> None:
    assert make_slug("日本 Tokyo") == "tokyo"


def test_slug_002_compatibility_ligature_and_umlaut_become_ascii() -> None:
    assert make_slug("\ufb01le \u00dcber") == "file-uber"


def test_slug_003_ex_003_runs_of_symbols_become_one_hyphen() -> None:
    assert make_slug("  --Rock & Roll--  ") == "rock-roll"


def test_slug_003_underscores_and_punctuation_become_one_hyphen() -> None:
    assert make_slug("foo___bar...baz") == "foo-bar-baz"


@given(
    title=_titles_with_ascii_alnum(),
    max_length=st.integers(min_value=1, max_value=200),
)
@settings(max_examples=50, derandomize=True)
def test_slug_003_slug_has_no_edge_or_repeated_hyphens(title: str, max_length: int) -> None:
    slug = make_slug(title, max_length=max_length)

    assert not slug.startswith("-")
    assert not slug.endswith("-")
    assert "--" not in slug


def test_slug_004_ex_004_cut_keeps_whole_words() -> None:
    assert make_slug("The quick brown fox jumps", max_length=15) == "the-quick-brown"


def test_slug_004_ex_005_long_first_word_is_cut() -> None:
    assert make_slug("Supercalifragilistic", max_length=5) == "super"


def test_slug_004_default_max_length_keeps_60_chars() -> None:
    title = " ".join(["word"] * 11 + ["abcde"])

    slug = make_slug(title)

    assert len(slug) == 60
    assert slug == "-".join(["word"] * 11 + ["abcde"])


def test_slug_004_default_max_length_cuts_over_60_chars() -> None:
    title = " ".join(["word"] * 11 + ["abcdef"])

    slug = make_slug(title)

    assert slug == "-".join(["word"] * 11)


def test_slug_004_cut_one_below_word_boundary_drops_word() -> None:
    assert make_slug("The quick brown fox jumps", max_length=14) == "the-quick"


def test_slug_004_cut_on_hyphen_boundary_keeps_preceding_words() -> None:
    assert make_slug("The quick brown fox jumps", max_length=16) == "the-quick-brown"


def test_slug_004_cut_mid_word_keeps_preceding_words() -> None:
    assert make_slug("The quick brown fox jumps", max_length=17) == "the-quick-brown"


def test_slug_004_long_first_word_with_following_words_is_cut() -> None:
    assert make_slug("Supercalifragilistic expialidocious", max_length=5) == "super"


def test_slug_004_min_max_length_of_one() -> None:
    assert make_slug("Alpha Beta", max_length=1) == "a"


def test_slug_004_max_length_of_200() -> None:
    title = "a" * 200

    assert make_slug(title, max_length=200) == title


@given(
    title=_titles_with_ascii_alnum(),
    max_length=st.integers(min_value=1, max_value=200),
)
@settings(max_examples=50, derandomize=True)
def test_slug_004_slug_never_exceeds_max_length(title: str, max_length: int) -> None:
    slug = make_slug(title, max_length=max_length)

    assert 1 <= len(slug) <= max_length
    assert not slug.startswith("-")
    assert not slug.endswith("-")


def test_slug_006_empty_slug_raises_value_error() -> None:
    with pytest.raises(ValueError, match=r"^the title has no letters or digits$"):
        make_slug("!!!")


def test_slug_006_empty_title_raises_value_error() -> None:
    with pytest.raises(ValueError, match=r"^the title has no letters or digits$"):
        make_slug("")


def test_slug_006_non_ascii_only_title_raises_value_error() -> None:
    with pytest.raises(ValueError, match=r"^the title has no letters or digits$"):
        make_slug("日本語")
