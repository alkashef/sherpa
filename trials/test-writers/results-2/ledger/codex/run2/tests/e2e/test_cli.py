import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import UUID

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st


def _run(
    folder: Path, *args: str, data_file: str | None = "ledger.json"
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    if data_file is None:
        env.pop("LEDGER_DATA", None)
    else:
        env["LEDGER_DATA"] = str(folder / data_file)
    script = Path(__file__).resolve().parents[2] / "main.py"
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=folder,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _output(result: subprocess.CompletedProcess[str]) -> str:
    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    return result.stdout


def _entry_id(result: subprocess.CompletedProcess[str]) -> str:
    output = _output(result)
    entry_id = output.removesuffix("\n")
    assert UUID(entry_id).version == 4
    assert output == f"{entry_id}\n"
    return entry_id


def _assert_amount_error(result: subprocess.CompletedProcess[str]) -> None:
    assert result.stderr == (
        "error: the amount must be a number from 0.01 to 1000000.00 with at most two decimals\n"
    )
    assert result.returncode == 2
    assert result.stdout == ""


def _assert_category_error(result: subprocess.CompletedProcess[str]) -> None:
    assert result.stderr == "error: the category must be 1 to 20 lowercase letters\n"
    assert result.returncode == 2
    assert result.stdout == ""


def test_ledg_001_ex_001_add_prints_the_id_and_stores_the_entry(tmp_path: Path) -> None:
    entry_id = _entry_id(_run(tmp_path, "add", "12.50", "food", "--note", "lunch"))
    assert _output(_run(tmp_path, "list")) == f"{entry_id}\t12.50\tfood\tlunch\n"
    data = json.loads((tmp_path / "ledger.json").read_text(encoding="utf-8"))
    [entry] = data["entries"]
    created = entry["created"]
    assert datetime.fromisoformat(created).utcoffset() == timedelta(0)
    assert entry == {
        "id": entry_id,
        "amount_cents": 1250,
        "category": "food",
        "note": "lunch",
        "created": created,
    }


def test_ledg_001_ex_004_largest_amount_is_stored(tmp_path: Path) -> None:
    entry_id = _entry_id(_run(tmp_path, "add", "1000000.00", "food"))
    expected = f"{entry_id}\t1000000.00\tfood\t\n"
    assert _output(_run(tmp_path, "list")) == expected
    _assert_amount_error(_run(tmp_path, "add", "1000000.01", "food"))
    assert _output(_run(tmp_path, "list")) == expected


def test_ledg_002_ex_002_cli_refuses_three_decimals(tmp_path: Path) -> None:
    entry_id = _entry_id(_run(tmp_path, "add", "3", "bus"))
    _assert_amount_error(_run(tmp_path, "add", "12.345", "food"))
    assert _output(_run(tmp_path, "list")) == f"{entry_id}\t3.00\tbus\t\n"


def test_ledg_002_ex_003_cli_refuses_zero(tmp_path: Path) -> None:
    _assert_amount_error(_run(tmp_path, "add", "0", "food"))
    assert _output(_run(tmp_path, "list")) == ""


def test_ledg_003_ex_005_uppercase_category_is_refused(tmp_path: Path) -> None:
    _assert_category_error(_run(tmp_path, "add", "5", "Food"))
    assert _output(_run(tmp_path, "list")) == ""


@pytest.mark.parametrize("category", ["a", "ab", "a" * 19, "a" * 20])
def test_ledg_003_valid_category_lengths(tmp_path: Path, category: str) -> None:
    entry_id = _entry_id(_run(tmp_path, "add", "1", category))
    assert _output(_run(tmp_path, "list")) == f"{entry_id}\t1.00\t{category}\t\n"


@pytest.mark.parametrize("category", ["", "a" * 21, "bus2", "two words", "café", "a_b", "a\n"])
def test_ledg_003_invalid_categories(tmp_path: Path, category: str) -> None:
    _assert_category_error(_run(tmp_path, "add", "1", category))
    assert _output(_run(tmp_path, "list")) == ""


@settings(max_examples=50, derandomize=True, deadline=None)
@given(category=st.text(alphabet="abcdefghijklmnopqrstuvwxyzAB39-_ é", max_size=22))
def test_ledg_003_only_valid_categories_are_stored(category: str) -> None:
    with TemporaryDirectory() as directory:
        folder = Path(directory)
        added = _run(folder, "add", "1", category)
        if 1 <= len(category) <= 20 and all("a" <= letter <= "z" for letter in category):
            entry_id = _entry_id(added)
            assert _output(_run(folder, "list")) == f"{entry_id}\t1.00\t{category}\t\n"
        else:
            _assert_category_error(added)
            assert _output(_run(folder, "list")) == ""


def test_ledg_004_ex_006_total_and_total_of_a_category(tmp_path: Path) -> None:
    for amount, category in [("12.50", "food"), ("7.25", "food"), ("3", "bus")]:
        _entry_id(_run(tmp_path, "add", amount, category))
    assert _output(_run(tmp_path, "total")) == "22.75\n"
    assert _output(_run(tmp_path, "total", "--category", "food")) == "19.75\n"
    assert _output(_run(tmp_path, "total", "--category", "books")) == "0.00\n"
    assert _output(_run(tmp_path, "total")) == "22.75\n"


def test_ledg_004_ex_007_empty_total(tmp_path: Path) -> None:
    assert _output(_run(tmp_path, "total")) == "0.00\n"


def test_ledg_005_ex_008_list_in_order_of_entry(tmp_path: Path) -> None:
    first = _entry_id(_run(tmp_path, "add", "4.10", "bus"))
    second = _entry_id(_run(tmp_path, "add", "2", "food", "--note", "bread"))
    assert first != second
    assert _output(_run(tmp_path, "list")) == f"{first}\t4.10\tbus\t\n{second}\t2.00\tfood\tbread\n"
    data = json.loads((tmp_path / "ledger.json").read_text(encoding="utf-8"))
    assert data["entries"][0]["note"] == ""


def test_ledg_006_ex_009_add_makes_the_folder(tmp_path: Path) -> None:
    path = "new/ledger.json"
    _entry_id(_run(tmp_path, "add", "1", "food", data_file=path))
    assert (tmp_path / path).is_file()
    assert _output(_run(tmp_path, "total", data_file=path)) == "1.00\n"


def test_ledg_006_default_data_file_is_relative_to_working_folder(tmp_path: Path) -> None:
    entry_id = _entry_id(_run(tmp_path, "add", "2", "food", data_file=None))
    path = tmp_path / "data" / "ledger.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert [entry["id"] for entry in data["entries"]] == [entry_id]


@pytest.mark.parametrize("args", [("total",), ("list",), ("add", "1", "food")])
def test_ledg_007_ex_010_invalid_data_file_exits_3(tmp_path: Path, args: tuple[str, ...]) -> None:
    path = tmp_path / "ledger.json"
    path.write_bytes(b"not json")
    result = _run(tmp_path, *args)
    assert result.stderr == "error: the data file is not a valid ledger\n"
    assert result.returncode == 3
    assert result.stdout == ""
    assert path.read_bytes() == b"not json"
