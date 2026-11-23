import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
NO_LETTERS_ERROR = "error: the title has no letters or digits\n"
MAX_ERROR = "error: --max must be an integer from 1 to 200\n"


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "main.py", *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=60,
    )


# SLUG-005


def test_slug_005_ex_006_prints_slug_and_exits_0() -> None:
    result = _run("Hello World")

    assert (result.stdout, result.returncode) == ("hello-world\n", 0)


def test_slug_005_max_option_sets_maximum_length() -> None:
    result = _run("The quick brown fox jumps", "--max", "15")

    assert (result.stdout, result.returncode) == ("the-quick-brown\n", 0)


def test_slug_005_default_maximum_length_is_60() -> None:
    result = _run(f"{'a' * 30} {'b' * 30}")

    assert (result.stdout, result.returncode) == (f"{'a' * 30}\n", 0)


@pytest.mark.parametrize(("max_value", "expected"), [("1", "h\n"), ("200", "hello\n")])
def test_slug_005_max_at_limits_is_accepted(max_value: str, expected: str) -> None:
    result = _run("Hello", "--max", max_value)

    assert (result.stdout, result.returncode) == (expected, 0)


def test_slug_005_second_run_gives_same_result() -> None:
    first = _run("Crème Brûlée")
    second = _run("Crème Brûlée")

    assert (first.stdout, second.stdout) == ("creme-brulee\n", "creme-brulee\n")


# SLUG-006


def test_slug_006_ex_007_title_without_letters_exits_2() -> None:
    result = _run("!!!")

    assert (result.stdout, result.stderr, result.returncode) == ("", NO_LETTERS_ERROR, 2)


# SLUG-007


def test_slug_007_ex_008_max_out_of_range_exits_2() -> None:
    result = _run("Hello", "--max", "0")

    assert (result.stdout, result.stderr, result.returncode) == ("", MAX_ERROR, 2)


@pytest.mark.parametrize("max_value", ["201", "-1", "abc", "1.5", ""])
def test_slug_007_invalid_max_exits_2(max_value: str) -> None:
    result = _run("Hello", "--max", max_value)

    assert (result.stdout, result.stderr, result.returncode) == ("", MAX_ERROR, 2)
