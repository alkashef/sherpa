import re

import pytest

from src.slug import make_slug


def test_slug_001_slug_holds_only_safe_characters() -> None:
    result = make_slug("Release 2.0: A-Z & 0-9!")
    assert re.fullmatch(r"[a-z0-9-]+", result) is not None
    assert result == "release-2-0-a-z-0-9"


def test_slug_001_ex_001_hello_world() -> None:
    assert make_slug("Hello, World!") == "hello-world"


def test_slug_002_ex_002_accents_become_plain_letters() -> None:
    assert make_slug("Crème Brûlée") == "creme-brulee"


def test_slug_002_ex_009_kelvin_sign_becomes_k() -> None:
    assert make_slug("50 \u212a") == "50-k"


def test_slug_002_ex_010_letters_without_ascii_form_are_dropped() -> None:
    assert make_slug("日本 Tokyo") == "tokyo"


def test_slug_003_ex_003_runs_of_symbols_become_one_hyphen() -> None:
    assert make_slug("  --Rock & Roll--  ") == "rock-roll"


def test_slug_003_underscores_become_single_hyphen() -> None:
    assert make_slug("foo_bar___baz") == "foo-bar-baz"


def test_slug_004_ex_004_cut_keeps_whole_words() -> None:
    assert make_slug("The quick brown fox jumps", max_length=15) == "the-quick-brown"


def test_slug_004_ex_005_long_first_word_is_cut() -> None:
    assert make_slug("Supercalifragilistic", max_length=5) == "super"


def test_slug_004_cut_drops_partial_word() -> None:
    assert make_slug("The quick brown fox jumps", max_length=17) == "the-quick-brown"


def test_slug_004_slug_at_exact_max_length_is_kept() -> None:
    assert make_slug("Hello World", max_length=11) == "hello-world"


def test_slug_004_default_max_length_is_60() -> None:
    title = "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu nu"
    assert make_slug(title) == "alpha-beta-gamma-delta-epsilon-zeta-eta-theta-iota-kappa"


def test_slug_006_empty_slug_raises_value_error() -> None:
    with pytest.raises(ValueError, match=r"^the title has no letters or digits$"):
        make_slug("!!!")


def test_slug_006_non_ascii_only_title_raises_value_error() -> None:
    with pytest.raises(ValueError, match=r"^the title has no letters or digits$"):
        make_slug("日本語")
