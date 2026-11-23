import json
import os
import subprocess
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MAIN_SCRIPT = PROJECT_ROOT / "main.py"

AMOUNT_ERROR = (
    "error: the amount must be a number from 0.01 to 1000000.00 with at most two decimals\n"
)
CATEGORY_ERROR = "error: the category must be 1 to 20 lowercase letters\n"
LEDGER_ERROR = "error: the data file is not a valid ledger\n"


def _run_ledger(
    args: list[str],
    *,
    data_file: Path | None = None,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    if data_file is None:
        env.pop("LEDGER_DATA", None)
    else:
        env["LEDGER_DATA"] = str(data_file)
    return subprocess.run(
        [sys.executable, str(MAIN_SCRIPT), *args],
        cwd=cwd or PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def _assert_uuid4_line(stdout: str) -> str:
    assert stdout.endswith("\n")
    entry_id = stdout[:-1]
    parsed = uuid.UUID(entry_id)
    assert parsed.version == 4
    assert str(parsed) == entry_id
    return entry_id


def test_ledg_001_ex_001_add_prints_the_id_and_stores_the_entry(tmp_path: Path) -> None:
    data_file = tmp_path / "ledger.json"
    added = _run_ledger(["add", "12.50", "food", "--note", "lunch"], data_file=data_file)
    assert added.returncode == 0
    assert added.stderr == ""
    entry_id = _assert_uuid4_line(added.stdout)

    listed = _run_ledger(["list"], data_file=data_file)
    assert listed.returncode == 0
    assert listed.stderr == ""
    assert listed.stdout == f"{entry_id}\t12.50\tfood\tlunch\n"


def test_ledg_001_add_without_note_stores_empty_note_and_utc_timestamp(tmp_path: Path) -> None:
    data_file = tmp_path / "ledger.json"
    first = _run_ledger(["add", "5", "food"], data_file=data_file)
    second = _run_ledger(["add", "5", "food"], data_file=data_file)
    assert first.returncode == 0
    assert second.returncode == 0
    first_id = _assert_uuid4_line(first.stdout)
    second_id = _assert_uuid4_line(second.stdout)
    assert first_id != second_id

    entries = json.loads(data_file.read_text(encoding="utf-8"))["entries"]
    assert entries[0]["note"] == ""
    created = datetime.fromisoformat(entries[0]["created"])
    assert created.tzinfo is not None
    assert created.utcoffset() == timedelta(0)


def test_ledg_001_ex_004_largest_amount_is_stored(tmp_path: Path) -> None:
    data_file = tmp_path / "ledger.json"
    accepted = _run_ledger(["add", "1000000.00", "food"], data_file=data_file)
    assert accepted.returncode == 0
    assert accepted.stderr == ""
    _assert_uuid4_line(accepted.stdout)

    refused = _run_ledger(["add", "1000000.01", "food"], data_file=data_file)
    assert refused.returncode == 2
    assert refused.stdout == ""
    assert refused.stderr == AMOUNT_ERROR

    total = _run_ledger(["total"], data_file=data_file)
    assert total.returncode == 0
    assert total.stdout == "1000000.00\n"


def test_ledg_002_ex_002_cli_refuses_three_decimals(tmp_path: Path) -> None:
    data_file = tmp_path / "ledger.json"
    seed = _run_ledger(["add", "5", "food"], data_file=data_file)
    assert seed.returncode == 0
    before = data_file.read_text(encoding="utf-8")

    result = _run_ledger(["add", "12.345", "food"], data_file=data_file)
    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == AMOUNT_ERROR
    assert data_file.read_text(encoding="utf-8") == before


def test_ledg_002_ex_003_cli_refuses_zero(tmp_path: Path) -> None:
    data_file = tmp_path / "ledger.json"
    result = _run_ledger(["add", "0", "food"], data_file=data_file)
    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == AMOUNT_ERROR
    assert not data_file.exists()


def test_ledg_003_ex_005_uppercase_category_is_refused(tmp_path: Path) -> None:
    data_file = tmp_path / "ledger.json"
    result = _run_ledger(["add", "5", "Food"], data_file=data_file)
    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == CATEGORY_ERROR
    assert not data_file.exists()


@pytest.mark.parametrize("category", ["a", "a" * 20])
def test_ledg_003_category_length_limits_accepted(tmp_path: Path, category: str) -> None:
    data_file = tmp_path / "ledger.json"
    result = _run_ledger(["add", "1", category], data_file=data_file)
    assert result.returncode == 0
    assert result.stderr == ""
    _assert_uuid4_line(result.stdout)


@pytest.mark.parametrize("category", ["", "a" * 21, "food1", "my_food"])
def test_ledg_003_invalid_category_limits_and_characters_refused(
    tmp_path: Path, category: str
) -> None:
    data_file = tmp_path / "ledger.json"
    result = _run_ledger(["add", "1", category], data_file=data_file)
    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == CATEGORY_ERROR
    assert not data_file.exists()


def test_ledg_004_ex_006_total_and_total_of_a_category(tmp_path: Path) -> None:
    data_file = tmp_path / "ledger.json"
    assert _run_ledger(["add", "12.50", "food"], data_file=data_file).returncode == 0
    assert _run_ledger(["add", "7.25", "food"], data_file=data_file).returncode == 0
    assert _run_ledger(["add", "3", "bus"], data_file=data_file).returncode == 0

    all_total = _run_ledger(["total"], data_file=data_file)
    assert all_total.returncode == 0
    assert all_total.stderr == ""
    assert all_total.stdout == "22.75\n"

    food_total = _run_ledger(["total", "--category", "food"], data_file=data_file)
    assert food_total.returncode == 0
    assert food_total.stderr == ""
    assert food_total.stdout == "19.75\n"


def test_ledg_004_ex_007_empty_total(tmp_path: Path) -> None:
    data_file = tmp_path / "ledger.json"
    result = _run_ledger(["total"], data_file=data_file)
    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout == "0.00\n"
    assert not data_file.exists()


def test_ledg_004_total_for_unknown_category_and_exact_cents(tmp_path: Path) -> None:
    data_file = tmp_path / "ledger.json"
    assert _run_ledger(["add", "0.10", "food"], data_file=data_file).returncode == 0
    assert _run_ledger(["add", "0.20", "food"], data_file=data_file).returncode == 0

    first = _run_ledger(["total"], data_file=data_file)
    second = _run_ledger(["total"], data_file=data_file)
    assert first.returncode == 0
    assert first.stdout == "0.30\n"
    assert second.stdout == first.stdout

    missing = _run_ledger(["total", "--category", "bus"], data_file=data_file)
    assert missing.returncode == 0
    assert missing.stdout == "0.00\n"


def test_ledg_005_ex_008_list_in_order_of_entry(tmp_path: Path) -> None:
    data_file = tmp_path / "ledger.json"
    first = _run_ledger(["add", "4.10", "bus"], data_file=data_file)
    second = _run_ledger(["add", "2", "food", "--note", "bread"], data_file=data_file)
    assert first.returncode == 0
    assert second.returncode == 0
    first_id = _assert_uuid4_line(first.stdout)
    second_id = _assert_uuid4_line(second.stdout)

    listed = _run_ledger(["list"], data_file=data_file)
    assert listed.returncode == 0
    assert listed.stderr == ""
    assert listed.stdout == f"{first_id}\t4.10\tbus\t\n{second_id}\t2.00\tfood\tbread\n"


def test_ledg_005_list_on_empty_ledger_prints_nothing(tmp_path: Path) -> None:
    data_file = tmp_path / "ledger.json"
    listed = _run_ledger(["list"], data_file=data_file)
    assert listed.returncode == 0
    assert listed.stderr == ""
    assert listed.stdout == ""


def test_ledg_006_ex_009_add_makes_the_folder(tmp_path: Path) -> None:
    data_file = tmp_path / "new" / "ledger.json"
    added = _run_ledger(["add", "1", "food"], data_file=data_file)
    assert added.returncode == 0
    assert added.stderr == ""
    assert data_file.is_file()

    total = _run_ledger(["total"], data_file=data_file)
    assert total.returncode == 0
    assert total.stdout == "1.00\n"


def test_ledg_006_default_data_file_when_env_unset(tmp_path: Path) -> None:
    added = _run_ledger(["add", "1", "food"], data_file=None, cwd=tmp_path)
    assert added.returncode == 0
    assert added.stderr == ""
    assert (tmp_path / "data" / "ledger.json").is_file()

    total = _run_ledger(["total"], data_file=None, cwd=tmp_path)
    assert total.returncode == 0
    assert total.stdout == "1.00\n"


def test_ledg_007_ex_010_invalid_data_file_exits_3(tmp_path: Path) -> None:
    data_file = tmp_path / "ledger.json"
    data_file.write_text("not json", encoding="utf-8")

    result = _run_ledger(["total"], data_file=data_file)
    assert result.returncode == 3
    assert result.stdout == ""
    assert result.stderr == LEDGER_ERROR
    assert data_file.read_text(encoding="utf-8") == "not json"


@pytest.mark.parametrize("command", [["add", "1", "food"], ["list"]])
def test_ledg_007_invalid_data_file_exits_3_on_add_and_list(
    tmp_path: Path, command: list[str]
) -> None:
    data_file = tmp_path / "ledger.json"
    data_file.write_text("not json", encoding="utf-8")

    result = _run_ledger(command, data_file=data_file)
    assert result.returncode == 3
    assert result.stdout == ""
    assert result.stderr == LEDGER_ERROR
    assert data_file.read_text(encoding="utf-8") == "not json"
