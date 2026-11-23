import subprocess
import sys
from pathlib import Path

import pytest


def _run_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "main.py", *arguments],
        cwd=Path(__file__).resolve().parents[2],
        capture_output=True,
        text=True,
        check=False,
    )


def test_slug_005_ex_006_prints_slug_and_exits_0() -> None:
    for _ in range(2):
        result = _run_cli("Hello World")
        assert (result.returncode, result.stdout, result.stderr) == (0, "hello-world\n", "")


def test_slug_005_default_maximum_length_is_60() -> None:
    result = _run_cli("X" * 61)
    assert (result.returncode, result.stdout, result.stderr) == (0, "x" * 60 + "\n", "")


@pytest.mark.parametrize("max_length", [1, 2, 199, 200])
def test_slug_005_accepts_valid_maximum_length(max_length: int) -> None:
    result = _run_cli("X" * 201, "--max", str(max_length))
    assert (result.returncode, result.stdout, result.stderr) == (0, "x" * max_length + "\n", "")


def test_slug_006_ex_007_title_without_letters_exits_2() -> None:
    result = _run_cli("!!!")
    assert (result.returncode, result.stdout, result.stderr) == (
        2,
        "",
        "error: the title has no letters or digits\n",
    )


@pytest.mark.parametrize("value", ["0", "201", "many", "1.5"])
def test_slug_007_ex_008_max_out_of_range_exits_2(value: str) -> None:
    result = _run_cli("Hello", "--max", value)
    assert (result.returncode, result.stdout, result.stderr) == (
        2,
        "",
        "error: --max must be an integer from 1 to 200\n",
    )
