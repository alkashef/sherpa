import subprocess
import sys
from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_NO_LETTERS_ERROR = "error: the title has no letters or digits\n"
_MAX_ERROR = "error: --max must be an integer from 1 to 200\n"


def _run_tool(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "main.py", *arguments],
        cwd=_PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=60,
    )


def test_slug_005_ex_006_prints_slug_and_exits_0() -> None:
    result = _run_tool("Hello World")
    assert result.stdout == "hello-world\n"
    assert result.returncode == 0


def test_slug_005_max_option_cuts_slug() -> None:
    result = _run_tool("The quick brown fox jumps", "--max", "15")
    assert result.stdout == "the-quick-brown\n"
    assert result.returncode == 0


def test_slug_005_default_maximum_length_is_60() -> None:
    result = _run_tool("x" * 61)
    assert result.stdout == "x" * 60 + "\n"
    assert result.returncode == 0


def test_slug_005_second_run_gives_same_result() -> None:
    first = _run_tool("Crème Brûlée")
    second = _run_tool("Crème Brûlée")
    assert first.stdout == second.stdout == "creme-brulee\n"
    assert first.returncode == second.returncode == 0


def test_slug_006_ex_007_title_without_letters_exits_2() -> None:
    result = _run_tool("!!!")
    assert result.stderr == _NO_LETTERS_ERROR
    assert result.stdout == ""
    assert result.returncode == 2


def test_slug_007_ex_008_max_out_of_range_exits_2() -> None:
    result = _run_tool("Hello", "--max", "0")
    assert result.stderr == _MAX_ERROR
    assert result.stdout == ""
    assert result.returncode == 2


@pytest.mark.parametrize("value", ["201", "-1", "abc", "1.5", ""])
def test_slug_007_invalid_max_exits_2(value: str) -> None:
    result = _run_tool("Hello", "--max", value)
    assert result.stderr == _MAX_ERROR
    assert result.stdout == ""
    assert result.returncode == 2


@pytest.mark.parametrize(("value", "expected"), [("1", "h\n"), ("200", "hello\n")])
def test_slug_007_max_at_limits_is_accepted(value: str, expected: str) -> None:
    result = _run_tool("Hello", "--max", value)
    assert result.stdout == expected
    assert result.returncode == 0
