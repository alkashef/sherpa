"""End-to-end tests: run main.py as a process with a data file in a temporary folder.

Requirements LEDG-001 to LEDG-007 and examples EX-001 to EX-010 of docs/spec.md.
"""

import json
import os
import re
import subprocess
import sys
import uuid
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MAIN = ROOT / "main.py"
AMOUNT_ERROR = (
    "error: the amount must be a number from 0.01 to 1000000.00 with at most two decimals\n"
)
CATEGORY_ERROR = "error: the category must be 1 to 20 lowercase letters\n"
LEDGER_ERROR = "error: the data file is not a valid ledger\n"
UTC_TIME = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def run(args: list[str], cwd: Path, data: str | None) -> subprocess.CompletedProcess[str]:
    env = {key: value for key, value in os.environ.items() if key != "LEDGER_DATA"}
    if data is not None:
        env["LEDGER_DATA"] = data
    return subprocess.run(
        [sys.executable, str(MAIN), *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=60,
    )


@pytest.fixture
def data_file(tmp_path: Path) -> Path:
    return tmp_path / "ledger.json"


def ledger(data_file: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return run(list(args), ROOT, str(data_file))


def assert_uuid4(text: str) -> None:
    parsed = uuid.UUID(text)
    assert parsed.version == 4
    assert str(parsed) == text


def add(data_file: Path, *args: str) -> str:
    result = ledger(data_file, "add", *args)
    assert result.returncode == 0, result.stderr
    return result.stdout.removesuffix("\n")


# LEDG-001: add


def test_ledg_001_ex_001_add_prints_the_id_and_stores_the_entry(data_file: Path) -> None:
    result = ledger(data_file, "add", "12.50", "food", "--note", "lunch")
    assert result.returncode == 0
    assert result.stdout.endswith("\n")
    entry_id = result.stdout.removesuffix("\n")
    assert_uuid4(entry_id)
    listed = ledger(data_file, "list")
    assert listed.returncode == 0
    assert listed.stdout == f"{entry_id}\t12.50\tfood\tlunch\n"


def test_ledg_001_add_prints_nothing_on_standard_error(data_file: Path) -> None:
    result = ledger(data_file, "add", "12.50", "food", "--note", "lunch")
    assert result.returncode == 0
    assert result.stderr == ""


def test_ledg_001_stored_entry_has_all_fields_and_the_time_in_utc(data_file: Path) -> None:
    entry_id = add(data_file, "12.50", "food", "--note", "lunch")
    stored = json.loads(data_file.read_text(encoding="utf-8"))
    [entry] = stored["entries"]
    assert {key: entry[key] for key in ("id", "amount_cents", "category", "note")} == {
        "id": entry_id,
        "amount_cents": 1250,
        "category": "food",
        "note": "lunch",
    }
    assert UTC_TIME.match(entry["created"])


def test_ledg_001_note_is_empty_when_none(data_file: Path) -> None:
    add(data_file, "3", "bus")
    stored = json.loads(data_file.read_text(encoding="utf-8"))
    assert stored["entries"][0]["note"] == ""


def test_ledg_001_each_entry_gets_a_new_id(data_file: Path) -> None:
    first = add(data_file, "1", "food")
    second = add(data_file, "1", "food")
    assert first != second


def test_ledg_001_ex_004_largest_amount_is_stored(data_file: Path) -> None:
    entry_id = add(data_file, "1000000.00", "food")
    assert ledger(data_file, "list").stdout == f"{entry_id}\t1000000.00\tfood\t\n"


# LEDG-002: the amount


def test_ledg_002_ex_002_cli_refuses_three_decimals(data_file: Path) -> None:
    add(data_file, "1", "food")
    before = data_file.read_bytes()
    result = ledger(data_file, "add", "12.345", "food")
    assert result.returncode == 2
    assert result.stderr == AMOUNT_ERROR
    assert result.stdout == ""
    assert data_file.read_bytes() == before


def test_ledg_002_ex_003_cli_refuses_zero(data_file: Path) -> None:
    result = ledger(data_file, "add", "0", "food")
    assert result.returncode == 2
    assert result.stderr == AMOUNT_ERROR
    assert not data_file.exists()


def test_ledg_002_ex_004_amount_over_the_limit_is_refused(data_file: Path) -> None:
    entry_id = add(data_file, "1000000.00", "food")
    result = ledger(data_file, "add", "1000000.01", "food")
    assert result.returncode == 2
    assert result.stderr == AMOUNT_ERROR
    assert ledger(data_file, "list").stdout == f"{entry_id}\t1000000.00\tfood\t\n"


@pytest.mark.parametrize("amount", ["abc", "0.00", "-1"])
def test_ledg_002_cli_refuses_an_invalid_amount(data_file: Path, amount: str) -> None:
    result = ledger(data_file, "add", amount, "food")
    assert result.returncode == 2
    assert result.stderr == AMOUNT_ERROR
    assert not data_file.exists()


def test_ledg_002_cli_accepts_the_lower_limit(data_file: Path) -> None:
    entry_id = add(data_file, "0.01", "food")
    assert ledger(data_file, "list").stdout == f"{entry_id}\t0.01\tfood\t\n"


# LEDG-003: the category


def test_ledg_003_ex_005_uppercase_category_is_refused(data_file: Path) -> None:
    result = ledger(data_file, "add", "5", "Food")
    assert result.returncode == 2
    assert result.stderr == CATEGORY_ERROR
    assert result.stdout == ""
    assert not data_file.exists()


@pytest.mark.parametrize("category", ["", "a" * 21, "food1", "fast food", "café"])
def test_ledg_003_invalid_category_is_refused(data_file: Path, category: str) -> None:
    result = ledger(data_file, "add", "5", category)
    assert result.returncode == 2
    assert result.stderr == CATEGORY_ERROR
    assert not data_file.exists()


@pytest.mark.parametrize("category", ["a", "a" * 20])
def test_ledg_003_category_at_the_limits_is_accepted(data_file: Path, category: str) -> None:
    entry_id = add(data_file, "5", category)
    assert ledger(data_file, "list").stdout == f"{entry_id}\t5.00\t{category}\t\n"


def test_ledg_003_invalid_category_leaves_the_ledger_unchanged(data_file: Path) -> None:
    add(data_file, "1", "food")
    before = data_file.read_bytes()
    result = ledger(data_file, "add", "5", "Food")
    assert result.returncode == 2
    assert data_file.read_bytes() == before


# LEDG-004: total


def test_ledg_004_ex_006_total_and_total_of_a_category(data_file: Path) -> None:
    add(data_file, "12.50", "food")
    add(data_file, "7.25", "food")
    add(data_file, "3", "bus")
    total = ledger(data_file, "total")
    assert total.returncode == 0
    assert total.stdout == "22.75\n"
    food = ledger(data_file, "total", "--category", "food")
    assert food.returncode == 0
    assert food.stdout == "19.75\n"


def test_ledg_004_ex_007_empty_total(data_file: Path) -> None:
    result = ledger(data_file, "total")
    assert result.returncode == 0
    assert result.stdout == "0.00\n"


def test_ledg_004_total_of_a_category_with_no_entry(data_file: Path) -> None:
    add(data_file, "3", "bus")
    result = ledger(data_file, "total", "--category", "food")
    assert result.returncode == 0
    assert result.stdout == "0.00\n"


def test_ledg_004_second_total_gives_the_same_result(data_file: Path) -> None:
    add(data_file, "0.10", "food")
    add(data_file, "0.20", "food")
    first = ledger(data_file, "total")
    second = ledger(data_file, "total")
    assert first.stdout == "0.30\n"
    assert second.stdout == first.stdout


# LEDG-005: list


def test_ledg_005_ex_008_list_in_order_of_entry(data_file: Path) -> None:
    first = add(data_file, "4.10", "bus")
    second = add(data_file, "2", "food", "--note", "bread")
    result = ledger(data_file, "list")
    assert result.returncode == 0
    assert result.stdout == f"{first}\t4.10\tbus\t\n{second}\t2.00\tfood\tbread\n"


def test_ledg_005_empty_ledger_lists_nothing(data_file: Path) -> None:
    result = ledger(data_file, "list")
    assert result.returncode == 0
    assert result.stdout == ""


# LEDG-006: the data file


def test_ledg_006_ex_009_add_makes_the_folder(tmp_path: Path) -> None:
    relative = str(Path("new") / "ledger.json")
    added = run(["add", "1", "food"], tmp_path, relative)
    assert added.returncode == 0
    assert (tmp_path / "new" / "ledger.json").is_file()
    total = run(["total"], tmp_path, relative)
    assert total.stdout == "1.00\n"


def test_ledg_006_default_data_file_is_data_ledger_json(tmp_path: Path) -> None:
    added = run(["add", "1", "food"], tmp_path, None)
    assert added.returncode == 0
    assert (tmp_path / "data" / "ledger.json").is_file()
    assert run(["total"], tmp_path, None).stdout == "1.00\n"


def test_ledg_006_read_of_a_missing_file_makes_no_file(data_file: Path) -> None:
    assert ledger(data_file, "total").returncode == 0
    assert ledger(data_file, "list").returncode == 0
    assert not data_file.exists()


# LEDG-007: a data file that is not a valid ledger


def test_ledg_007_ex_010_invalid_data_file_exits_3(data_file: Path) -> None:
    data_file.write_text("not json", encoding="utf-8")
    result = ledger(data_file, "total")
    assert result.returncode == 3
    assert result.stderr == LEDGER_ERROR
    assert result.stdout == ""
    assert data_file.read_text(encoding="utf-8") == "not json"


@pytest.mark.parametrize("args", [["list"], ["add", "1", "food"], ["total", "--category", "food"]])
def test_ledg_007_invalid_data_file_changes_nothing(data_file: Path, args: list[str]) -> None:
    data_file.write_text("not json", encoding="utf-8")
    result = ledger(data_file, *args)
    assert result.returncode == 3
    assert result.stderr == LEDGER_ERROR
    assert data_file.read_text(encoding="utf-8") == "not json"
