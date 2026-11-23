import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from string import ascii_lowercase
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
    main = Path(__file__).resolve().parents[2] / "main.py"
    return subprocess.run(
        [sys.executable, str(main), *args],
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


def _add(folder: Path, *args: str, data_file: str | None = "ledger.json") -> str:
    output = _output(_run(folder, "add", *args, data_file=data_file))
    entry_id = output.removesuffix("\n")
    assert UUID(entry_id).version == 4
    assert output == f"{entry_id}\n"
    return entry_id


def _assert_amount_error(result: subprocess.CompletedProcess[str]) -> None:
    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == (
        "error: the amount must be a number from 0.01 to 1000000.00 with at most two decimals\n"
    )


def test_ledg_001_ex_001_add_prints_the_id_and_stores_the_entry(tmp_path: Path) -> None:
    entry_id = _add(tmp_path, "12.50", "food", "--note", "lunch")
    assert _output(_run(tmp_path, "list")) == f"{entry_id}\t12.50\tfood\tlunch\n"
    data = json.loads((tmp_path / "ledger.json").read_text(encoding="utf-8"))
    (entry,) = data["entries"]
    created = entry["created"]
    assert datetime.fromisoformat(created).utcoffset() == timedelta(0)
    assert isinstance(entry["amount_cents"], int)
    assert entry == {
        "id": entry_id,
        "amount_cents": 1250,
        "category": "food",
        "note": "lunch",
        "created": created,
    }


def test_ledg_001_ex_004_largest_amount_is_stored(tmp_path: Path) -> None:
    entry_id = _add(tmp_path, "1000000.00", "food")
    _assert_amount_error(_run(tmp_path, "add", "1000000.01", "food"))
    assert _output(_run(tmp_path, "list")) == f"{entry_id}\t1000000.00\tfood\t\n"


def test_ledg_002_ex_002_cli_refuses_three_decimals(tmp_path: Path) -> None:
    _add(tmp_path, "1", "bus")
    path = tmp_path / "ledger.json"
    original = path.read_bytes()
    _assert_amount_error(_run(tmp_path, "add", "12.345", "food"))
    assert path.read_bytes() == original


def test_ledg_002_ex_003_cli_refuses_zero(tmp_path: Path) -> None:
    _assert_amount_error(_run(tmp_path, "add", "0", "food"))
    assert _output(_run(tmp_path, "list")) == ""


@pytest.mark.parametrize("category", ["Food", "", "a" * 21, "café", "a1", "two words"])
def test_ledg_003_ex_005_uppercase_category_is_refused(tmp_path: Path, category: str) -> None:
    result = _run(tmp_path, "add", "5", category)
    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "error: the category must be 1 to 20 lowercase letters\n"
    assert _output(_run(tmp_path, "list")) == ""


@settings(max_examples=50, derandomize=True, deadline=None)
@given(category=st.text(alphabet=ascii_lowercase, min_size=1, max_size=20))
def test_ledg_003_lowercase_categories_are_stored(
    tmp_path_factory: pytest.TempPathFactory, category: str
) -> None:
    folder = tmp_path_factory.mktemp("category")
    entry_id = _add(folder, "1", category)
    assert _output(_run(folder, "list")) == f"{entry_id}\t1.00\t{category}\t\n"


@pytest.mark.parametrize("length", [1, 2, 19, 20])
def test_ledg_003_valid_category_lengths(tmp_path: Path, length: int) -> None:
    category = "a" * length
    entry_id = _add(tmp_path, "1", category)
    assert _output(_run(tmp_path, "list")) == f"{entry_id}\t1.00\t{category}\t\n"


def test_ledg_004_ex_006_total_and_total_of_a_category(tmp_path: Path) -> None:
    _add(tmp_path, "12.50", "food")
    _add(tmp_path, "7.25", "food")
    _add(tmp_path, "3", "bus")
    assert _output(_run(tmp_path, "total")) == "22.75\n"
    assert _output(_run(tmp_path, "total", "--category", "food")) == "19.75\n"
    assert _output(_run(tmp_path, "total", "--category", "books")) == "0.00\n"


def test_ledg_004_ex_007_empty_total(tmp_path: Path) -> None:
    assert _output(_run(tmp_path, "total")) == "0.00\n"


def test_ledg_005_ex_008_list_in_order_of_entry(tmp_path: Path) -> None:
    first = _add(tmp_path, "4.10", "bus")
    second = _add(tmp_path, "2", "food", "--note", "bread")
    assert first != second
    assert _output(_run(tmp_path, "list")) == f"{first}\t4.10\tbus\t\n{second}\t2.00\tfood\tbread\n"


def test_ledg_006_ex_009_add_makes_the_folder(tmp_path: Path) -> None:
    _add(tmp_path, "1", "food", data_file="new/ledger.json")
    assert (tmp_path / "new" / "ledger.json").is_file()
    assert _output(_run(tmp_path, "total", data_file="new/ledger.json")) == "1.00\n"


def test_ledg_006_default_data_file_in_working_folder(tmp_path: Path) -> None:
    entry_id = _add(tmp_path, "1", "food", data_file=None)
    path = tmp_path / "data" / "ledger.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert [entry["id"] for entry in data["entries"]] == [entry_id]


@pytest.mark.parametrize("args", [("total",), ("list",), ("add", "1", "food")])
def test_ledg_007_ex_010_invalid_data_file_exits_3(tmp_path: Path, args: tuple[str, ...]) -> None:
    path = tmp_path / "ledger.json"
    path.write_bytes(b"not json")
    result = _run(tmp_path, *args)
    assert result.returncode == 3
    assert result.stdout == ""
    assert result.stderr == "error: the data file is not a valid ledger\n"
    assert path.read_bytes() == b"not json"
