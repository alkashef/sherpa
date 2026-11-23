import subprocess
import sys
from pathlib import Path

import pytest


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "main.py", *args],
        cwd=Path(__file__).resolve().parents[2],
        capture_output=True,
        text=True,
        check=False,
    )


def test_slug_005_ex_006_prints_slug_and_exits_0() -> None:
    for _ in range(2):
        result = _run_cli("Hello World")
        assert (result.returncode, result.stdout, result.stderr) == (0, "hello-world\n", "")


@pytest.mark.parametrize(("length", "expected_length"), [(59, 59), (60, 60), (61, 60)])
def test_slug_005_default_maximum_length(length: int, expected_length: int) -> None:
    result = _run_cli("A" * length)
    assert (result.returncode, result.stdout, result.stderr) == (
        0,
        "a" * expected_length + "\n",
        "",
    )


@pytest.mark.parametrize("max_length", [1, 2, 199, 200])
def test_slug_005_honors_valid_maximum_length(max_length: int) -> None:
    result = _run_cli("B" * 201, "--max", str(max_length))
    assert (result.returncode, result.stdout, result.stderr) == (0, "b" * max_length + "\n", "")


def test_slug_006_ex_007_title_without_letters_exits_2() -> None:
    result = _run_cli("!!!")
    assert (result.returncode, result.stdout, result.stderr) == (
        2,
        "",
        "error: the title has no letters or digits\n",
    )


@pytest.mark.parametrize("maximum", ["0", "201", "1.5", "ten"])
def test_slug_007_ex_008_max_out_of_range_exits_2(maximum: str) -> None:
    result = _run_cli("Hello", "--max", maximum)
    assert (result.returncode, result.stdout, result.stderr) == (
        2,
        "",
        "error: --max must be an integer from 1 to 200\n",
    )
