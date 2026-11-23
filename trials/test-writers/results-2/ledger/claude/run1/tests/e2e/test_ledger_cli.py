import json
import os
import re
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MAIN = PROJECT_ROOT / "main.py"
AMOUNT_ERROR = (
    "error: the amount must be a number from 0.01 to 1000000.00 with at most two decimals\n"
)
CATEGORY_ERROR = "error: the category must be 1 to 20 lowercase letters\n"
LEDGER_ERROR = "error: the data file is not a valid ledger\n"
UTC_TIME = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def run_ledger(
    args: list[str], data: Path | None, cwd: Path = PROJECT_ROOT
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
        check=False,
        timeout=60,
    )


def add_entry(data: Path, *args: str) -> str:
    result = run_ledger(["add", *args], data)
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def stored_records(data: Path) -> list[dict[str, object]]:
    content = json.loads(data.read_text(encoding="utf-8"))
    records: list[dict[str, object]] = content["entries"]
    return records


def test_ledg_001_ex_001_add_prints_the_id_and_stores_the_entry(tmp_path: Path) -> None:
    data = tmp_path / "ledger.json"
    result = run_ledger(["add", "12.50", "food", "--note", "lunch"], data)
    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout.endswith("\n")
    entry_id = result.stdout[:-1]
    assert uuid.UUID(entry_id).version == 4
    assert str(uuid.UUID(entry_id)) == entry_id
    listed = run_ledger(["list"], data)
    assert listed.returncode == 0
    assert listed.stdout == f"{entry_id}\t12.50\tfood\tlunch\n"


def test_ledg_001_ex_001_stored_entry_has_the_five_values(tmp_path: Path) -> None:
    data = tmp_path / "ledger.json"
    entry_id = add_entry(data, "12.50", "food", "--note", "lunch")
    records = stored_records(data)
    assert len(records) == 1
    record = records[0]
    assert set(record) == {"id", "amount_cents", "category", "note", "created"}
    assert record["id"] == entry_id
    assert record["amount_cents"] == 1250
    assert record["category"] == "food"
    assert record["note"] == "lunch"
    created = record["created"]
    assert isinstance(created, str)
    assert UTC_TIME.match(created)
    assert datetime.fromisoformat(created).utcoffset() is not None


def test_ledg_001_note_is_empty_when_none_is_given(tmp_path: Path) -> None:
    data = tmp_path / "ledger.json"
    add_entry(data, "3", "bus")
    assert stored_records(data)[0]["note"] == ""


def test_ledg_001_each_entry_gets_a_new_id(tmp_path: Path) -> None:
    data = tmp_path / "ledger.json"
    first = add_entry(data, "1", "food")
    second = add_entry(data, "1", "food")
    assert first != second


def test_ledg_001_ex_004_largest_amount_is_stored(tmp_path: Path) -> None:
    data = tmp_path / "ledger.json"
    first = run_ledger(["add", "1000000.00", "food"], data)
    assert first.returncode == 0
    second = run_ledger(["add", "1000000.01", "food"], data)
    assert second.returncode == 2
    assert second.stderr == AMOUNT_ERROR
    assert second.stdout == ""
    listed = run_ledger(["list"], data)
    assert listed.stdout == f"{first.stdout.strip()}\t1000000.00\tfood\t\n"


def test_ledg_002_ex_002_cli_refuses_three_decimals(tmp_path: Path) -> None:
    data = tmp_path / "ledger.json"
    add_entry(data, "5", "food")
    before = data.read_bytes()
    result = run_ledger(["add", "12.345", "food"], data)
    assert result.returncode == 2
    assert result.stderr == AMOUNT_ERROR
    assert result.stdout == ""
    assert data.read_bytes() == before


def test_ledg_002_ex_003_cli_refuses_zero(tmp_path: Path) -> None:
    data = tmp_path / "ledger.json"
    result = run_ledger(["add", "0", "food"], data)
    assert result.returncode == 2
    assert result.stderr == AMOUNT_ERROR
    assert run_ledger(["list"], data).stdout == ""


def test_ledg_002_cli_refuses_text_that_is_not_a_number(tmp_path: Path) -> None:
    data = tmp_path / "ledger.json"
    result = run_ledger(["add", "abc", "food"], data)
    assert result.returncode == 2
    assert result.stderr == AMOUNT_ERROR
    assert run_ledger(["list"], data).stdout == ""


def test_ledg_002_cli_accepts_the_smallest_amount(tmp_path: Path) -> None:
    data = tmp_path / "ledger.json"
    add_entry(data, "0.01", "food")
    assert run_ledger(["total"], data).stdout == "0.01\n"


def test_ledg_003_ex_005_uppercase_category_is_refused(tmp_path: Path) -> None:
    data = tmp_path / "ledger.json"
    result = run_ledger(["add", "5", "Food"], data)
    assert result.returncode == 2
    assert result.stderr == CATEGORY_ERROR
    assert result.stdout == ""
    assert run_ledger(["list"], data).stdout == ""


def test_ledg_003_twenty_letters_are_accepted(tmp_path: Path) -> None:
    data = tmp_path / "ledger.json"
    add_entry(data, "5", "a" * 20)
    assert stored_records(data)[0]["category"] == "a" * 20


def test_ledg_003_one_letter_is_accepted(tmp_path: Path) -> None:
    data = tmp_path / "ledger.json"
    add_entry(data, "5", "a")
    assert stored_records(data)[0]["category"] == "a"


def test_ledg_003_twenty_one_letters_are_refused(tmp_path: Path) -> None:
    data = tmp_path / "ledger.json"
    result = run_ledger(["add", "5", "a" * 21], data)
    assert result.returncode == 2
    assert result.stderr == CATEGORY_ERROR
    assert run_ledger(["list"], data).stdout == ""


def test_ledg_003_empty_category_is_refused(tmp_path: Path) -> None:
    data = tmp_path / "ledger.json"
    result = run_ledger(["add", "5", ""], data)
    assert result.returncode == 2
    assert result.stderr == CATEGORY_ERROR
    assert run_ledger(["list"], data).stdout == ""


def test_ledg_003_category_with_a_digit_is_refused(tmp_path: Path) -> None:
    data = tmp_path / "ledger.json"
    result = run_ledger(["add", "5", "food2"], data)
    assert result.returncode == 2
    assert result.stderr == CATEGORY_ERROR


def test_ledg_003_category_with_a_letter_outside_a_to_z_is_refused(tmp_path: Path) -> None:
    data = tmp_path / "ledger.json"
    result = run_ledger(["add", "5", "café"], data)
    assert result.returncode == 2
    assert result.stderr == CATEGORY_ERROR


def test_ledg_004_ex_006_total_and_total_of_a_category(tmp_path: Path) -> None:
    data = tmp_path / "ledger.json"
    add_entry(data, "12.50", "food")
    add_entry(data, "7.25", "food")
    add_entry(data, "3", "bus")
    total = run_ledger(["total"], data)
    assert total.returncode == 0
    assert total.stdout == "22.75\n"
    food = run_ledger(["total", "--category", "food"], data)
    assert food.returncode == 0
    assert food.stdout == "19.75\n"


def test_ledg_004_ex_007_empty_total(tmp_path: Path) -> None:
    data = tmp_path / "ledger.json"
    result = run_ledger(["total"], data)
    assert result.returncode == 0
    assert result.stdout == "0.00\n"


def test_ledg_004_total_of_a_category_with_no_entry(tmp_path: Path) -> None:
    data = tmp_path / "ledger.json"
    add_entry(data, "3", "bus")
    result = run_ledger(["total", "--category", "food"], data)
    assert result.returncode == 0
    assert result.stdout == "0.00\n"


def test_ledg_005_ex_008_list_in_order_of_entry(tmp_path: Path) -> None:
    data = tmp_path / "ledger.json"
    first = add_entry(data, "4.10", "bus")
    second = add_entry(data, "2", "food", "--note", "bread")
    result = run_ledger(["list"], data)
    assert result.returncode == 0
    assert result.stdout == f"{first}\t4.10\tbus\t\n{second}\t2.00\tfood\tbread\n"


def test_ledg_005_list_of_an_empty_ledger(tmp_path: Path) -> None:
    data = tmp_path / "ledger.json"
    result = run_ledger(["list"], data)
    assert result.returncode == 0
    assert result.stdout == ""


def test_ledg_005_second_list_gives_the_same_result(tmp_path: Path) -> None:
    data = tmp_path / "ledger.json"
    add_entry(data, "4.10", "bus")
    assert run_ledger(["list"], data).stdout == run_ledger(["list"], data).stdout


def test_ledg_006_ex_009_add_makes_the_folder(tmp_path: Path) -> None:
    data = tmp_path / "new" / "ledger.json"
    result = run_ledger(["add", "1", "food"], data)
    assert result.returncode == 0
    assert data.is_file()
    assert run_ledger(["total"], data).stdout == "1.00\n"


def test_ledg_006_default_data_file_is_in_the_folder_where_it_runs(tmp_path: Path) -> None:
    result = run_ledger(["add", "1", "food"], None, cwd=tmp_path)
    assert result.returncode == 0
    default = tmp_path / "data" / "ledger.json"
    assert default.is_file()
    assert run_ledger(["total"], default).stdout == "1.00\n"


def test_ledg_007_ex_010_invalid_data_file_exits_3(tmp_path: Path) -> None:
    data = tmp_path / "ledger.json"
    data.write_text("not json", encoding="utf-8")
    result = run_ledger(["total"], data)
    assert result.returncode == 3
    assert result.stderr == LEDGER_ERROR
    assert result.stdout == ""
    assert data.read_text(encoding="utf-8") == "not json"


def test_ledg_007_add_to_an_invalid_data_file_changes_nothing(tmp_path: Path) -> None:
    data = tmp_path / "ledger.json"
    data.write_text("not json", encoding="utf-8")
    result = run_ledger(["add", "1", "food"], data)
    assert result.returncode == 3
    assert result.stderr == LEDGER_ERROR
    assert result.stdout == ""
    assert data.read_text(encoding="utf-8") == "not json"


def test_ledg_007_list_of_an_invalid_data_file_exits_3(tmp_path: Path) -> None:
    data = tmp_path / "ledger.json"
    data.write_text('{"entries": "food"}', encoding="utf-8")
    result = run_ledger(["list"], data)
    assert result.returncode == 3
    assert result.stderr == LEDGER_ERROR
    assert result.stdout == ""
    assert data.read_text(encoding="utf-8") == '{"entries": "food"}'
