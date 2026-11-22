import subprocess
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _run_tool(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "main.py", *args],
        cwd=_PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
        check=False,
    )


def test_slug_005_ex_006_prints_slug_and_exits_0():
    result = _run_tool("Hello World")

    assert result.stdout == "hello-world\n"
    assert result.returncode == 0


def test_slug_006_ex_007_title_without_letters_exits_2():
    result = _run_tool("!!!")

    assert result.stderr == "error: the title has no letters or digits\n"
    assert result.stdout == ""
    assert result.returncode == 2


def test_slug_007_ex_008_max_out_of_range_exits_2():
    result = _run_tool("Hello", "--max", "0")

    assert result.stderr == "error: --max must be an integer from 1 to 200\n"
    assert result.stdout == ""
    assert result.returncode == 2
