import re
from importlib import import_module

import pytest


def _make_slug(title: str, **options: int) -> str:
    return import_module("src.slug").make_slug(title, **options)


def test_slug_001_slug_holds_only_safe_characters() -> None:
    slug = _make_slug("Draft_42: A/B + C\t(100%)!")

    assert re.fullmatch(r"[a-z0-9-]+", slug)


def test_slug_001_ex_001_hello_world() -> None:
    assert _make_slug("Hello, World!") == "hello-world"


@pytest.mark.parametrize(
    ("title", "expected"),
    [("Crème Brûlée", "creme-brulee"), ("O\ufb03ce Café", "office-cafe")],
)
def test_slug_002_ex_002_accents_become_plain_letters(title: str, expected: str) -> None:
    assert _make_slug(title) == expected


def test_slug_002_ex_009_kelvin_sign_becomes_k() -> None:
    assert _make_slug("50 \u212a") == "50-k"


@pytest.mark.parametrize(("title", "expected"), [("日本 Tokyo", "tokyo"), ("A日本B", "ab")])
def test_slug_002_ex_010_letters_without_ascii_form_are_dropped(title: str, expected: str) -> None:
    assert _make_slug(title) == expected


def test_slug_003_ex_003_runs_of_symbols_become_one_hyphen() -> None:
    assert _make_slug("  --Rock & Roll--  ") == "rock-roll"


@pytest.mark.parametrize(("maximum", "expected"), [(15, "the-quick-brown"), (13, "the-quick")])
def test_slug_004_ex_004_cut_keeps_whole_words(maximum: int, expected: str) -> None:
    assert _make_slug("The quick brown fox jumps", max_length=maximum) == expected


def test_slug_004_ex_005_long_first_word_is_cut() -> None:
    assert _make_slug("Supercalifragilistic", max_length=5) == "super"


def test_slug_006_empty_slug_raises_value_error() -> None:
    with pytest.raises(ValueError, match=r"^the title has no letters or digits\Z"):
        _make_slug("!!!")
