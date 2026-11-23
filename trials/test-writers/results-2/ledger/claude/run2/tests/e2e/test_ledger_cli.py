import json
import os
import subprocess
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAIN = ROOT / "main.py"

AMOUNT_ERROR = (
    "error: the amount must be a number from 0.01 to 1000000.00 with at most two decimals\n"
)
CATEGORY_ERROR = "error: the category must be 1 to 20 lowercase letters\n"
LEDGER_ERROR = "error: the data file is not a valid ledger\n"
ENTRY_KEYS = {"id", "amount_cents", "category", "note", "created"}


def _run(
    args: list[str], data: str | Path | None, cwd: Path = ROOT
) -> subprocess.CompletedProcess[str]:
    env = {key: value for key, value in os.environ.items() if key != "LEDGER_DATA"}
    if data is not None:
        env["LEDGER_DATA"] = str(data)
    return subprocess.run(
        [sys.executable, str(MAIN), *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
        check=False,
    )


def _add(data: Path, *args: str) -> str:
    result = _run(["add", *args], data)
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def test_ledg_001_ex_001_add_prints_the_id_and_stores_the_entry(tmp_path: Path) -> None:
    data = tmp_path / "ledger.json"
    result = _run(["add", "12.50", "food", "--note", "lunch"], data)
    assert result.returncode == 0
    assert result.stdout.endswith("\n")
    entry_id = result.stdout[:-1]
    assert str(uuid.UUID(entry_id)) == entry_id
    assert uuid.UUID(entry_id).version == 4
    listed = _run(["list"], data)
    assert listed.stdout == f"{entry_id}\t12.50\tfood\tlunch\n"


def test_ledg_001_stored_entry_has_the_five_keys(tmp_path: Path) -> None:
    data = tmp_path / "ledger.json"
    entry_id = _add(data, "3", "bus")
    stored = json.loads(data.read_text(encoding="utf-8"))
    assert list(stored) == ["entries"]
    [entry] = stored["entries"]
    assert set(entry) == ENTRY_KEYS
    assert entry["id"] == entry_id
    assert entry["amount_cents"] == 300
    assert entry["category"] == "bus"
    assert entry["note"] == ""


def test_ledg_001_time_of_the_entry_is_iso_8601_in_utc(tmp_path: Path) -> None:
    data = tmp_path / "ledger.json"
    _add(data, "3", "bus")
    created = json.loads(data.read_text(encoding="utf-8"))["entries"][0]["created"]
    assert created.endswith("Z")
    assert datetime.fromisoformat(created).utcoffset() == timedelta(0)
    assert datetime.fromisoformat(created).tzinfo is not None


def test_ledg_001_each_entry_gets_a_new_id(tmp_path: Path) -> None:
    data = tmp_path / "ledger.json"
    first = _add(data, "1", "food")
    second = _add(data, "1", "food")
    assert first != second


def test_ledg_001_ex_004_largest_amount_is_stored(tmp_path: Path) -> None:
    data = tmp_path / "ledger.json"
    stored = _run(["add", "1000000.00", "food"], data)
    refused = _run(["add", "1000000.01", "food"], data)
    assert stored.returncode == 0
    assert refused.returncode == 2
    assert refused.stderr == AMOUNT_ERROR
    assert _run(["total"], data).stdout == "1000000.00\n"


def test_ledg_002_ex_002_cli_refuses_three_decimals(tmp_path: Path) -> None:
    data = tmp_path / "ledger.json"
    _add(data, "1", "food")
    before = data.read_bytes()
    result = _run(["add", "12.345", "food"], data)
    assert result.returncode == 2
    assert result.stderr == AMOUNT_ERROR
    assert result.stdout == ""
    assert data.read_bytes() == before


def test_ledg_002_ex_003_cli_refuses_zero(tmp_path: Path) -> None:
    data = tmp_path / "ledger.json"
    result = _run(["add", "0", "food"], data)
    assert result.returncode == 2
    assert result.stderr == AMOUNT_ERROR
    assert _run(["list"], data).stdout == ""


def test_ledg_002_cli_refuses_text_that_is_not_a_number(tmp_path: Path) -> None:
    data = tmp_path / "ledger.json"
    result = _run(["add", "abc", "food"], data)
    assert result.returncode == 2
    assert result.stderr == AMOUNT_ERROR
    assert _run(["list"], data).stdout == ""


def test_ledg_003_ex_005_uppercase_category_is_refused(tmp_path: Path) -> None:
    data = tmp_path / "ledger.json"
    result = _run(["add", "5", "Food"], data)
    assert result.returncode == 2
    assert result.stderr == CATEGORY_ERROR
    assert result.stdout == ""
    assert _run(["list"], data).stdout == ""


def test_ledg_003_category_of_twenty_letters_is_stored(tmp_path: Path) -> None:
    data = tmp_path / "ledger.json"
    result = _run(["add", "5", "a" * 20], data)
    assert result.returncode == 0
    assert _run(["total", "--category", "a" * 20], data).stdout == "5.00\n"


def test_ledg_003_category_of_twenty_one_letters_is_refused(tmp_path: Path) -> None:
    data = tmp_path / "ledger.json"
    result = _run(["add", "5", "a" * 21], data)
    assert result.returncode == 2
    assert result.stderr == CATEGORY_ERROR
    assert _run(["list"], data).stdout == ""


def test_ledg_003_category_of_one_letter_is_stored(tmp_path: Path) -> None:
    data = tmp_path / "ledger.json"
    assert _run(["add", "5", "a"], data).returncode == 0


def test_ledg_003_empty_category_is_refused(tmp_path: Path) -> None:
    data = tmp_path / "ledger.json"
    result = _run(["add", "5", ""], data)
    assert result.returncode == 2
    assert result.stderr == CATEGORY_ERROR


def test_ledg_003_category_with_a_digit_is_refused(tmp_path: Path) -> None:
    data = tmp_path / "ledger.json"
    result = _run(["add", "5", "food1"], data)
    assert result.returncode == 2
    assert result.stderr == CATEGORY_ERROR


def test_ledg_003_category_with_a_letter_outside_a_to_z_is_refused(tmp_path: Path) -> None:
    data = tmp_path / "ledger.json"
    result = _run(["add", "5", "café"], data)
    assert result.returncode == 2
    assert result.stderr == CATEGORY_ERROR


def test_ledg_004_ex_006_total_and_total_of_a_category(tmp_path: Path) -> None:
    data = tmp_path / "ledger.json"
    _add(data, "12.50", "food")
    _add(data, "7.25", "food")
    _add(data, "3", "bus")
    total = _run(["total"], data)
    food = _run(["total", "--category", "food"], data)
    assert (total.returncode, total.stdout) == (0, "22.75\n")
    assert (food.returncode, food.stdout) == (0, "19.75\n")


def test_ledg_004_ex_007_empty_total(tmp_path: Path) -> None:
    result = _run(["total"], tmp_path / "ledger.json")
    assert result.returncode == 0
    assert result.stdout == "0.00\n"


def test_ledg_004_total_of_a_category_without_entries(tmp_path: Path) -> None:
    data = tmp_path / "ledger.json"
    _add(data, "3", "bus")
    result = _run(["total", "--category", "food"], data)
    assert result.returncode == 0
    assert result.stdout == "0.00\n"


def test_ledg_004_second_total_gives_the_same_result(tmp_path: Path) -> None:
    data = tmp_path / "ledger.json"
    _add(data, "0.10", "food")
    _add(data, "0.20", "food")
    assert _run(["total"], data).stdout == "0.30\n"
    assert _run(["total"], data).stdout == "0.30\n"


def test_ledg_005_ex_008_list_in_order_of_entry(tmp_path: Path) -> None:
    data = tmp_path / "ledger.json"
    first = _add(data, "4.10", "bus")
    second = _add(data, "2", "food", "--note", "bread")
    result = _run(["list"], data)
    assert result.returncode == 0
    assert result.stdout == f"{first}\t4.10\tbus\t\n{second}\t2.00\tfood\tbread\n"


def test_ledg_005_list_of_an_empty_ledger_prints_nothing(tmp_path: Path) -> None:
    result = _run(["list"], tmp_path / "ledger.json")
    assert result.returncode == 0
    assert result.stdout == ""


def test_ledg_006_ex_009_add_makes_the_folder(tmp_path: Path) -> None:
    result = _run(["add", "1", "food"], "new/ledger.json", cwd=tmp_path)
    assert result.returncode == 0
    assert (tmp_path / "new" / "ledger.json").is_file()
    total = _run(["total"], "new/ledger.json", cwd=tmp_path)
    assert total.stdout == "1.00\n"


def test_ledg_006_default_data_file_is_data_ledger_json(tmp_path: Path) -> None:
    result = _run(["add", "1", "food"], None, cwd=tmp_path)
    assert result.returncode == 0
    assert (tmp_path / "data" / "ledger.json").is_file()
    assert _run(["total"], None, cwd=tmp_path).stdout == "1.00\n"


def test_ledg_007_ex_010_invalid_data_file_exits_3(tmp_path: Path) -> None:
    data = tmp_path / "ledger.json"
    data.write_text("not json", encoding="utf-8")
    result = _run(["total"], data)
    assert result.returncode == 3
    assert result.stderr == LEDGER_ERROR
    assert data.read_text(encoding="utf-8") == "not json"


def test_ledg_007_add_to_an_invalid_data_file_changes_nothing(tmp_path: Path) -> None:
    data = tmp_path / "ledger.json"
    data.write_text("not json", encoding="utf-8")
    result = _run(["add", "1", "food"], data)
    assert result.returncode == 3
    assert result.stderr == LEDGER_ERROR
    assert result.stdout == ""
    assert data.read_text(encoding="utf-8") == "not json"


def test_ledg_007_list_of_an_invalid_data_file_exits_3(tmp_path: Path) -> None:
    data = tmp_path / "ledger.json"
    data.write_text('{"entries": 5}', encoding="utf-8")
    result = _run(["list"], data)
    assert result.returncode == 3
    assert result.stderr == LEDGER_ERROR
