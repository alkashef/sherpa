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


@pytest.mark.parametrize(
    ("args", "expected"),
    [
        (("Hello World",), "hello-world\n"),
        (("A" * 61,), "a" * 60 + "\n"),
        (("Hello World", "--max", "1"), "h\n"),
        (("A" * 201, "--max", "200"), "a" * 200 + "\n"),
    ],
    ids=["example", "default-60", "minimum-1", "maximum-200"],
)
def test_slug_005_ex_006_prints_slug_and_exits_0(args: tuple[str, ...], expected: str) -> None:
    result = _run_cli(*args)

    assert result.returncode == 0, result.stderr
    assert result.stdout == expected


def test_slug_006_ex_007_title_without_letters_exits_2() -> None:
    result = _run_cli("!!!")

    assert result.stderr == "error: the title has no letters or digits\n"
    assert result.stdout == ""
    assert result.returncode == 2


@pytest.mark.parametrize("value", ["0", "201", "1.5"])
def test_slug_007_ex_008_max_out_of_range_exits_2(value: str) -> None:
    result = _run_cli("Hello", "--max", value)

    assert result.stderr == "error: --max must be an integer from 1 to 200\n"
    assert result.stdout == ""
    assert result.returncode == 2
