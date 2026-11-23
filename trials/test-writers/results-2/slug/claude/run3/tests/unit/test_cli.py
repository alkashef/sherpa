"""Unit tests of `src.cli.main`, called in the process (SLUG-005 to SLUG-007)."""

import pytest

from src.cli import main

_EMPTY_SLUG_ERROR = "error: the title has no letters or digits\n"
_MAX_ERROR = "error: --max must be an integer from 1 to 200\n"


def test_slug_005_main_prints_slug_and_returns_0(capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["Hello World"])
    captured = capsys.readouterr()
    assert (code, captured.out, captured.err) == (0, "hello-world\n", "")


def test_slug_005_main_uses_max_option(capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["The quick brown fox jumps", "--max", "15"])
    captured = capsys.readouterr()
    assert (code, captured.out, captured.err) == (0, "the-quick-brown\n", "")


def test_slug_006_main_returns_2_for_title_without_letters(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code = main(["!!!"])
    captured = capsys.readouterr()
    assert (code, captured.out, captured.err) == (2, "", _EMPTY_SLUG_ERROR)


def test_slug_007_main_returns_2_for_max_out_of_range(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code = main(["Hello", "--max", "201"])
    captured = capsys.readouterr()
    assert (code, captured.out, captured.err) == (2, "", _MAX_ERROR)
