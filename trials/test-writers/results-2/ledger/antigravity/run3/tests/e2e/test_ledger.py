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
DATA_FILE_ERROR = "error: the data file is not a valid ledger\n"


def _run_ledger(
    args: list[str],
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


def _assert_utc_iso8601(timestamp: str) -> None:
    assert "T" in timestamp
    parsed = datetime.fromisoformat(timestamp)
    assert parsed.utcoffset() == timedelta(0)


def _assert_single_stored_entry(data_file: Path, expected: dict[str, object]) -> None:
    stored = json.loads(data_file.read_text(encoding="utf-8"))
    assert len(stored["entries"]) == 1
    entry = stored["entries"][0]
    assert set(entry) == {"id", "amount_cents", "category", "note", "created"}
    for key, value in expected.items():
        assert entry[key] == value
    _assert_utc_iso8601(entry["created"])


def test_ledg_001_ex_001_add_prints_the_id_and_stores_the_entry(tmp_path: Path) -> None:
    data_file = tmp_path / "ledger.json"
    add_result = _run_ledger(["add", "12.50", "food", "--note", "lunch"], data_file)
    assert add_result.returncode == 0
    assert add_result.stderr == ""
    entry_id = _assert_uuid4_line(add_result.stdout)
    _assert_single_stored_entry(
        data_file,
        {"id": entry_id, "amount_cents": 1250, "category": "food", "note": "lunch"},
    )

    list_result = _run_ledger(["list"], data_file)
    assert list_result.returncode == 0
    assert list_result.stderr == ""
    assert list_result.stdout == f"{entry_id}\t12.50\tfood\tlunch\n"


def test_ledg_001_add_without_note_defaults_to_empty(tmp_path: Path) -> None:
    data_file = tmp_path / "ledger.json"
    add_result = _run_ledger(["add", "4.10", "bus"], data_file)
    assert add_result.returncode == 0
    assert add_result.stderr == ""
    entry_id = _assert_uuid4_line(add_result.stdout)

    list_result = _run_ledger(["list"], data_file)
    assert list_result.returncode == 0
    assert list_result.stderr == ""
    assert list_result.stdout == f"{entry_id}\t4.10\tbus\t\n"


def test_ledg_001_ex_004_largest_amount_is_stored(tmp_path: Path) -> None:
    data_file = tmp_path / "ledger.json"
    ok_result = _run_ledger(["add", "1000000.00", "food"], data_file)
    assert ok_result.returncode == 0
    assert ok_result.stderr == ""
    _assert_uuid4_line(ok_result.stdout)

    over_result = _run_ledger(["add", "1000000.01", "food"], data_file)
    assert over_result.returncode == 2
    assert over_result.stdout == ""
    assert over_result.stderr == AMOUNT_ERROR

    total_result = _run_ledger(["total"], data_file)
    assert total_result.returncode == 0
    assert total_result.stdout == "1000000.00\n"


def test_ledg_002_ex_002_cli_refuses_three_decimals(tmp_path: Path) -> None:
    data_file = tmp_path / "ledger.json"
    seed = _run_ledger(["add", "12.50", "food"], data_file)
    assert seed.returncode == 0
    before = data_file.read_text(encoding="utf-8")

    result = _run_ledger(["add", "12.345", "food"], data_file)
    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == AMOUNT_ERROR
    assert data_file.read_text(encoding="utf-8") == before


def test_ledg_002_ex_003_cli_refuses_zero(tmp_path: Path) -> None:
    data_file = tmp_path / "ledger.json"
    result = _run_ledger(["add", "0", "food"], data_file)
    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == AMOUNT_ERROR
    assert not data_file.exists()


def test_ledg_003_ex_005_uppercase_category_is_refused(tmp_path: Path) -> None:
    data_file = tmp_path / "ledger.json"
    result = _run_ledger(["add", "5", "Food"], data_file)
    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == CATEGORY_ERROR
    assert not data_file.exists()


@pytest.mark.parametrize("category", ["a", "a" * 19, "a" * 20])
def test_ledg_003_valid_category_lengths_are_accepted(tmp_path: Path, category: str) -> None:
    data_file = tmp_path / "ledger.json"
    result = _run_ledger(["add", "1", category], data_file)
    assert result.returncode == 0
    assert result.stderr == ""
    _assert_uuid4_line(result.stdout)


@pytest.mark.parametrize(
    "category",
    ["", "a" * 21, "food1", "fast-food", "fast_food", "café"],
)
def test_ledg_003_invalid_categories_are_refused(tmp_path: Path, category: str) -> None:
    data_file = tmp_path / "ledger.json"
    result = _run_ledger(["add", "5", category], data_file)
    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == CATEGORY_ERROR
    assert not data_file.exists()


def test_ledg_004_ex_006_total_and_total_of_a_category(tmp_path: Path) -> None:
    data_file = tmp_path / "ledger.json"
    assert _run_ledger(["add", "12.50", "food"], data_file).returncode == 0
    assert _run_ledger(["add", "7.25", "food"], data_file).returncode == 0
    assert _run_ledger(["add", "3", "bus"], data_file).returncode == 0

    all_total = _run_ledger(["total"], data_file)
    assert all_total.returncode == 0
    assert all_total.stderr == ""
    assert all_total.stdout == "22.75\n"

    food_total_1 = _run_ledger(["total", "--category", "food"], data_file)
    food_total_2 = _run_ledger(["total", "--category", "food"], data_file)
    assert food_total_1.returncode == 0
    assert food_total_1.stderr == ""
    assert food_total_1.stdout == "19.75\n"
    assert food_total_2.stdout == food_total_1.stdout


def test_ledg_004_ex_007_empty_total(tmp_path: Path) -> None:
    data_file = tmp_path / "ledger.json"
    result = _run_ledger(["total"], data_file)
    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout == "0.00\n"
    assert not data_file.exists()


def test_ledg_004_exact_cents_and_unknown_category_total(tmp_path: Path) -> None:
    data_file = tmp_path / "ledger.json"
    assert _run_ledger(["add", "0.10", "food"], data_file).returncode == 0
    assert _run_ledger(["add", "0.20", "food"], data_file).returncode == 0

    food_total = _run_ledger(["total", "--category", "food"], data_file)
    assert food_total.returncode == 0
    assert food_total.stdout == "0.30\n"

    other_total = _run_ledger(["total", "--category", "bus"], data_file)
    assert other_total.returncode == 0
    assert other_total.stderr == ""
    assert other_total.stdout == "0.00\n"


def test_ledg_005_ex_008_list_in_order_of_entry(tmp_path: Path) -> None:
    data_file = tmp_path / "ledger.json"
    first = _run_ledger(["add", "4.10", "bus"], data_file)
    second = _run_ledger(["add", "2", "food", "--note", "bread"], data_file)
    assert first.returncode == 0
    assert second.returncode == 0
    id_1 = _assert_uuid4_line(first.stdout)
    id_2 = _assert_uuid4_line(second.stdout)
    assert id_1 != id_2

    expected = f"{id_1}\t4.10\tbus\t\n{id_2}\t2.00\tfood\tbread\n"
    list_1 = _run_ledger(["list"], data_file)
    list_2 = _run_ledger(["list"], data_file)
    assert list_1.returncode == 0
    assert list_1.stderr == ""
    assert list_1.stdout == expected
    assert list_2.stdout == expected


def test_ledg_005_list_empty_ledger_prints_nothing(tmp_path: Path) -> None:
    data_file = tmp_path / "ledger.json"
    result = _run_ledger(["list"], data_file)
    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout == ""


def test_ledg_006_ex_009_add_makes_the_folder(tmp_path: Path) -> None:
    data_file = tmp_path / "new" / "ledger.json"
    add_result = _run_ledger(["add", "1", "food"], data_file)
    assert add_result.returncode == 0
    assert add_result.stderr == ""
    assert data_file.is_file()

    total_result = _run_ledger(["total"], data_file)
    assert total_result.returncode == 0
    assert total_result.stderr == ""
    assert total_result.stdout == "1.00\n"


def test_ledg_006_default_data_file_path_when_env_unset(tmp_path: Path) -> None:
    add_result = _run_ledger(["add", "1.50", "tea"], data_file=None, cwd=tmp_path)
    assert add_result.returncode == 0
    assert add_result.stderr == ""
    assert (tmp_path / "data" / "ledger.json").is_file()

    total_result = _run_ledger(["total"], data_file=None, cwd=tmp_path)
    assert total_result.returncode == 0
    assert total_result.stderr == ""
    assert total_result.stdout == "1.50\n"


def test_ledg_007_ex_010_invalid_data_file_exits_3(tmp_path: Path) -> None:
    data_file = tmp_path / "ledger.json"
    data_file.write_text("not json", encoding="utf-8")

    result = _run_ledger(["total"], data_file)
    assert result.returncode == 3
    assert result.stdout == ""
    assert result.stderr == DATA_FILE_ERROR
    assert data_file.read_text(encoding="utf-8") == "not json"


@pytest.mark.parametrize("args", [["add", "5", "food"], ["list"]])
def test_ledg_007_add_and_list_on_invalid_data_file_exit_3(tmp_path: Path, args: list[str]) -> None:
    data_file = tmp_path / "ledger.json"
    data_file.write_text("not json", encoding="utf-8")

    result = _run_ledger(args, data_file)
    assert result.returncode == 3
    assert result.stdout == ""
    assert result.stderr == DATA_FILE_ERROR
    assert data_file.read_text(encoding="utf-8") == "not json"
