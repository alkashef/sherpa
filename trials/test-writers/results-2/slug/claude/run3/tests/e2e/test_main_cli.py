"""End-to-end tests: run `python main.py TITLE [--max N]` as a process (SLUG-005 to SLUG-007)."""

import subprocess
import sys
from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_EMPTY_SLUG_ERROR = "error: the title has no letters or digits\n"
_MAX_ERROR = "error: --max must be an integer from 1 to 200\n"


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    """Run main.py from the project root with the given arguments."""
    return subprocess.run(
        [sys.executable, "main.py", *args],
        cwd=_PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=60,
    )


def _outcome(result: subprocess.CompletedProcess[str]) -> tuple[int, str, str]:
    return result.returncode, result.stdout, result.stderr


# SLUG-005


def test_slug_005_ex_006_prints_slug_and_exits_0() -> None:
    assert _outcome(_run("Hello World")) == (0, "hello-world\n", "")


def test_slug_005_max_option_cuts_slug() -> None:
    result = _run("The quick brown fox jumps", "--max", "15")
    assert _outcome(result) == (0, "the-quick-brown\n", "")


def test_slug_005_default_maximum_length_is_60() -> None:
    assert _outcome(_run("a" * 61)) == (0, "a" * 60 + "\n", "")


@pytest.mark.parametrize(("max_value", "expected"), [("1", "h\n"), ("200", "hello\n")])
def test_slug_005_max_at_limits_is_accepted(max_value: str, expected: str) -> None:
    assert _outcome(_run("Hello", "--max", max_value)) == (0, expected, "")


def test_slug_005_second_run_gives_same_result() -> None:
    expected = (0, "creme-brulee\n", "")
    assert [_outcome(_run("Crème Brûlée")) for _ in range(2)] == [expected, expected]


# SLUG-006


def test_slug_006_ex_007_title_without_letters_exits_2() -> None:
    assert _outcome(_run("!!!")) == (2, "", _EMPTY_SLUG_ERROR)


# SLUG-007


def test_slug_007_ex_008_max_out_of_range_exits_2() -> None:
    assert _outcome(_run("Hello", "--max", "0")) == (2, "", _MAX_ERROR)


@pytest.mark.parametrize("max_value", ["201", "-1", "abc", "1.5", ""])
def test_slug_007_invalid_max_exits_2(max_value: str) -> None:
    assert _outcome(_run("Hello", "--max", max_value)) == (2, "", _MAX_ERROR)
