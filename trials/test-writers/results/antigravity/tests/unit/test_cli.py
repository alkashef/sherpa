import sys

import pytest

from src.cli import main


def test_slug_005_cli_main_prints_slug_and_returns_0(capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["Hello World"])
    captured = capsys.readouterr()
    assert code == 0
    assert captured.out == "hello-world\n"
    assert captured.err == ""


def test_slug_005_cli_main_respects_max_option(capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["The quick brown fox jumps", "--max", "15"])
    captured = capsys.readouterr()
    assert code == 0
    assert captured.out == "the-quick-brown\n"
    assert captured.err == ""


def test_slug_005_cli_main_reads_sys_argv_when_argv_is_none(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(sys, "argv", ["main.py", "Hello World"])
    code = main()
    captured = capsys.readouterr()
    assert code == 0
    assert captured.out == "hello-world\n"
    assert captured.err == ""


def test_slug_006_cli_main_empty_slug_returns_2(capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["!!!"])
    captured = capsys.readouterr()
    assert code == 2
    assert captured.out == ""
    assert captured.err == "error: the title has no letters or digits\n"


def test_slug_007_cli_main_max_zero_returns_2(capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["Hello", "--max", "0"])
    captured = capsys.readouterr()
    assert code == 2
    assert captured.out == ""
    assert captured.err == "error: --max must be an integer from 1 to 200\n"


def test_slug_007_cli_main_max_above_200_returns_2(capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["Hello", "--max", "201"])
    captured = capsys.readouterr()
    assert code == 2
    assert captured.out == ""
    assert captured.err == "error: --max must be an integer from 1 to 200\n"


def test_slug_007_cli_main_max_non_integer_returns_2(capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["Hello", "--max", "abc"])
    captured = capsys.readouterr()
    assert code == 2
    assert captured.out == ""
    assert captured.err == "error: --max must be an integer from 1 to 200\n"
