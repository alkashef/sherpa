import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from uuid import UUID

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st


def _run(
    folder: Path, *args: str, data_file: str | None = "ledger.json"
) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    if data_file is None:
        environment.pop("LEDGER_DATA", None)
    else:
        environment["LEDGER_DATA"] = str(folder / data_file)
    script = Path(__file__).resolve().parents[2] / "main.py"
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=folder,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )


def _success(result: subprocess.CompletedProcess[str]) -> str:
    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    return result.stdout


def _add(folder: Path, amount: str, category: str, *options: str) -> str:
    output = _success(_run(folder, "add", amount, category, *options))
    entry_id = output.removesuffix("\n")
    parsed = UUID(entry_id)
    assert parsed.version == 4
    assert str(parsed) == entry_id.lower()
    assert output == f"{entry_id}\n"
    return entry_id


def _assert_refused(result: subprocess.CompletedProcess[str], code: int, message: str) -> None:
    assert (result.returncode, result.stdout, result.stderr) == (code, "", f"error: {message}\n")


def _assert_amount_refused(folder: Path, amount: str) -> None:
    path = folder / "ledger.json"
    before = path.read_bytes()
    result = _run(folder, "add", amount, "food")
    _assert_refused(
        result, 2, "the amount must be a number from 0.01 to 1000000.00 with at most two decimals"
    )
    assert path.read_bytes() == before


def test_ledg_001_ex_001_add_prints_the_id_and_stores_the_entry(tmp_path: Path) -> None:
    entry_id = _add(tmp_path, "12.50", "food", "--note", "lunch")
    ledger = json.loads((tmp_path / "ledger.json").read_text(encoding="utf-8"))
    [entry] = ledger["entries"]
    assert datetime.fromisoformat(entry["created"]).utcoffset() == timedelta(0)
    assert entry == {
        "id": entry_id,
        "amount_cents": 1250,
        "category": "food",
        "note": "lunch",
        "created": entry["created"],
    }
    assert _success(_run(tmp_path, "list")) == f"{entry_id}\t12.50\tfood\tlunch\n"


def test_ledg_001_ex_004_largest_amount_is_stored(tmp_path: Path) -> None:
    entry_id = _add(tmp_path, "1000000.00", "food")
    _assert_amount_refused(tmp_path, "1000000.01")
    assert _success(_run(tmp_path, "list")) == f"{entry_id}\t1000000.00\tfood\t\n"


def test_ledg_002_ex_002_cli_refuses_three_decimals(tmp_path: Path) -> None:
    _add(tmp_path, "4.10", "bus")
    _assert_amount_refused(tmp_path, "12.345")


def test_ledg_002_ex_003_cli_refuses_zero(tmp_path: Path) -> None:
    _add(tmp_path, "4.10", "bus")
    _assert_amount_refused(tmp_path, "0")


def _assert_category_refused(tmp_path: Path, category: str) -> None:
    _add(tmp_path, "4.10", "bus")
    path = tmp_path / "ledger.json"
    before = path.read_bytes()
    result = _run(tmp_path, "add", "5", category)
    _assert_refused(result, 2, "the category must be 1 to 20 lowercase letters")
    assert path.read_bytes() == before


def test_ledg_003_ex_005_uppercase_category_is_refused(tmp_path: Path) -> None:
    _assert_category_refused(tmp_path, "Food")


@pytest.mark.parametrize("category", ["", "a" * 21, "café", "a1", "a-b"])
def test_ledg_003_invalid_category_is_refused(tmp_path: Path, category: str) -> None:
    _assert_category_refused(tmp_path, category)


@pytest.mark.parametrize("category", ["a", "ab", "a" * 19, "a" * 20])
def test_ledg_003_category_length_limits_are_accepted(tmp_path: Path, category: str) -> None:
    entry_id = _add(tmp_path, "5", category)
    assert _success(_run(tmp_path, "list")) == f"{entry_id}\t5.00\t{category}\t\n"


@given(category=st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=20))
@settings(max_examples=50, derandomize=True, deadline=None)
def test_ledg_003_lowercase_categories_are_stored(
    tmp_path_factory: pytest.TempPathFactory, category: str
) -> None:
    folder = tmp_path_factory.mktemp("category")
    entry_id = _add(folder, "5", category)
    assert _success(_run(folder, "list")) == f"{entry_id}\t5.00\t{category}\t\n"


def test_ledg_004_ex_006_total_and_total_of_a_category(tmp_path: Path) -> None:
    _add(tmp_path, "12.50", "food")
    _add(tmp_path, "7.25", "food")
    _add(tmp_path, "3", "bus")
    assert _success(_run(tmp_path, "total")) == "22.75\n"
    assert _success(_run(tmp_path, "total", "--category", "food")) == "19.75\n"
    assert _success(_run(tmp_path, "total", "--category", "books")) == "0.00\n"


def test_ledg_004_ex_007_empty_total(tmp_path: Path) -> None:
    assert _success(_run(tmp_path, "total")) == "0.00\n"


def test_ledg_005_ex_008_list_in_order_of_entry(tmp_path: Path) -> None:
    first = _add(tmp_path, "4.10", "bus")
    second = _add(tmp_path, "2", "food", "--note", "bread")
    assert first != second
    expected = f"{first}\t4.10\tbus\t\n{second}\t2.00\tfood\tbread\n"
    assert _success(_run(tmp_path, "list")) == expected
    assert _success(_run(tmp_path, "list")) == expected


def test_ledg_006_ex_009_add_makes_the_folder(tmp_path: Path) -> None:
    data_file = "new/ledger.json"
    _success(_run(tmp_path, "add", "1", "food", data_file=data_file))
    assert (tmp_path / data_file).is_file()
    assert _success(_run(tmp_path, "total", data_file=data_file)) == "1.00\n"


def test_ledg_006_default_data_file_is_relative_to_working_folder(tmp_path: Path) -> None:
    _success(_run(tmp_path, "add", "1", "food", data_file=None))
    ledger = json.loads((tmp_path / "data" / "ledger.json").read_text(encoding="utf-8"))
    [entry] = ledger["entries"]
    assert entry["amount_cents"] == 100
    assert _success(_run(tmp_path, "total", data_file=None)) == "1.00\n"


@pytest.mark.parametrize("args", [("total",), ("list",), ("add", "1", "food")])
def test_ledg_007_ex_010_invalid_data_file_exits_3(tmp_path: Path, args: tuple[str, ...]) -> None:
    path = tmp_path / "ledger.json"
    path.write_bytes(b"not json")
    _assert_refused(_run(tmp_path, *args), 3, "the data file is not a valid ledger")
    assert path.read_bytes() == b"not json"
