import pytest

from src.cli import main

NO_LETTERS_ERROR = "error: the title has no letters or digits\n"
MAX_ERROR = "error: --max must be an integer from 1 to 200\n"


def test_slug_005_main_prints_slug_and_returns_0(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["Hello World"])

    assert (capsys.readouterr().out, exit_code) == ("hello-world\n", 0)


def test_slug_005_main_uses_max_option(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["The quick brown fox jumps", "--max", "15"])

    assert (capsys.readouterr().out, exit_code) == ("the-quick-brown\n", 0)


def test_slug_006_main_reports_title_without_letters(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(["!!!"])
    captured = capsys.readouterr()

    assert (captured.out, captured.err, exit_code) == ("", NO_LETTERS_ERROR, 2)


@pytest.mark.parametrize("max_value", ["0", "201", "abc"])
def test_slug_007_main_reports_invalid_max(
    capsys: pytest.CaptureFixture[str], max_value: str
) -> None:
    exit_code = main(["Hello", "--max", max_value])
    captured = capsys.readouterr()

    assert (captured.out, captured.err, exit_code) == ("", MAX_ERROR, 2)
