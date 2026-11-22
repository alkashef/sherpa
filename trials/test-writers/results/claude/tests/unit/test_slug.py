import re

import pytest

from src.slug import make_slug


def test_slug_001_slug_holds_only_safe_characters():
    title = "Ünïcödé Tést № 42 ½ — Straße © 2026 / Ça va? 日本"

    slug = make_slug(title)

    assert re.fullmatch(r"[a-z0-9-]+", slug) is not None


def test_slug_001_ex_001_hello_world():
    assert make_slug("Hello, World!") == "hello-world"


def test_slug_002_ex_002_accents_become_plain_letters():
    assert make_slug("Crème Brûlée") == "creme-brulee"


def test_slug_002_ex_009_kelvin_sign_becomes_k():
    assert make_slug("50 \N{KELVIN SIGN}") == "50-k"


def test_slug_002_ex_010_letters_without_ascii_form_are_dropped():
    assert make_slug("日本 Tokyo") == "tokyo"


def test_slug_003_ex_003_runs_of_symbols_become_one_hyphen():
    assert make_slug("  --Rock & Roll--  ") == "rock-roll"


def test_slug_004_ex_004_cut_keeps_whole_words():
    assert make_slug("The quick brown fox jumps", max_length=15) == "the-quick-brown"


def test_slug_004_ex_005_long_first_word_is_cut():
    assert make_slug("Supercalifragilistic", max_length=5) == "super"


def test_slug_006_empty_slug_raises_value_error():
    with pytest.raises(ValueError, match=r"^the title has no letters or digits$"):
        make_slug("!!!")
