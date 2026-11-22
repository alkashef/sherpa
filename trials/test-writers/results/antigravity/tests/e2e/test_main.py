import subprocess
import sys
from pathlib import Path


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    project_root = Path(__file__).resolve().parents[2]
    main_script = project_root / "main.py"
    return subprocess.run(
        [sys.executable, str(main_script), *args],
        cwd=project_root,
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


def test_slug_005_max_option_limits_output_length() -> None:
    result = _run_cli("The quick brown fox jumps", "--max", "15")
    assert result.returncode == 0
    assert result.stdout == "the-quick-brown\n"
    assert result.stderr == ""


def test_slug_006_ex_007_title_without_letters_exits_2() -> None:
    result = _run_cli("!!!")
    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "error: the title has no letters or digits\n"


def test_slug_007_ex_008_max_out_of_range_exits_2() -> None:
    result = _run_cli("Hello", "--max", "0")
    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "error: --max must be an integer from 1 to 200\n"


def test_slug_007_max_above_200_exits_2() -> None:
    result = _run_cli("Hello", "--max", "201")
    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "error: --max must be an integer from 1 to 200\n"


def test_slug_007_max_negative_exits_2() -> None:
    result = _run_cli("Hello", "--max", "-5")
    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "error: --max must be an integer from 1 to 200\n"


def test_slug_007_max_non_integer_exits_2() -> None:
    result = _run_cli("Hello", "--max", "abc")
    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "error: --max must be an integer from 1 to 200\n"


def test_slug_007_max_boundary_1_is_accepted() -> None:
    result = _run_cli("Hello", "--max", "1")
    assert result.returncode == 0
    assert result.stdout == "h\n"
    assert result.stderr == ""


def test_slug_007_max_boundary_200_is_accepted() -> None:
    result = _run_cli("Hello", "--max", "200")
    assert result.returncode == 0
    assert result.stdout == "hello\n"
    assert result.stderr == ""
