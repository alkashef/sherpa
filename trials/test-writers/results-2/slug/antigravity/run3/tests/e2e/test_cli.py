import subprocess
import sys
from pathlib import Path

import pytest


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    root = Path(__file__).resolve().parents[2]
    return subprocess.run(
        [sys.executable, str(root / "main.py"), *args],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def test_slug_005_ex_006_prints_slug_and_exits_0() -> None:
    result = _run_cli("Hello World")
    assert result.returncode == 0
    assert result.stdout == "hello-world\n"
    assert result.stderr == ""


@pytest.mark.parametrize(
    ("title", "expected"),
    [
        ("a" * 59, "a" * 59 + "\n"),
        ("a" * 60, "a" * 60 + "\n"),
        ("a" * 61, "a" * 60 + "\n"),
    ],
)
def test_slug_005_default_max_length_is_60(title: str, expected: str) -> None:
    result = _run_cli(title)
    assert result.returncode == 0
    assert result.stdout == expected
    assert result.stderr == ""


def test_slug_005_max_option_cuts_slug() -> None:
    result = _run_cli("The quick brown fox jumps", "--max", "15")
    assert result.returncode == 0
    assert result.stdout == "the-quick-brown\n"
    assert result.stderr == ""


@pytest.mark.parametrize(
    ("title", "max_arg", "expected"),
    [
        ("Hello", "1", "h\n"),
        ("Hello", "2", "he\n"),
        ("a" * 205, "199", "a" * 199 + "\n"),
        ("a" * 205, "200", "a" * 200 + "\n"),
    ],
)
def test_slug_005_max_boundary_values_succeed(title: str, max_arg: str, expected: str) -> None:
    result = _run_cli(title, "--max", max_arg)
    assert result.returncode == 0
    assert result.stdout == expected
    assert result.stderr == ""


def test_slug_005_second_run_gives_same_result() -> None:
    first = _run_cli("Hello World")
    second = _run_cli("Hello World")
    assert first.returncode == 0
    assert first.stdout == "hello-world\n"
    assert first.stderr == ""
    assert (second.returncode, second.stdout, second.stderr) == (
        first.returncode,
        first.stdout,
        first.stderr,
    )


def test_slug_006_ex_007_title_without_letters_exits_2() -> None:
    result = _run_cli("!!!")
    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "error: the title has no letters or digits\n"


@pytest.mark.parametrize("title", ["", "   "])
def test_slug_006_empty_title_exits_2(title: str) -> None:
    result = _run_cli(title)
    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "error: the title has no letters or digits\n"


def test_slug_007_ex_008_max_out_of_range_exits_2() -> None:
    result = _run_cli("Hello", "--max", "0")
    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "error: --max must be an integer from 1 to 200\n"


@pytest.mark.parametrize("bad_max", ["201", "-1", "abc", "10.5", ""])
def test_slug_007_invalid_max_values_exit_2(bad_max: str) -> None:
    result = _run_cli("Hello", "--max", bad_max)
    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "error: --max must be an integer from 1 to 200\n"
