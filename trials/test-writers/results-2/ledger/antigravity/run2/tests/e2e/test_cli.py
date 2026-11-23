import json
import os
import subprocess
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
MAIN_PY = ROOT / "main.py"

AMOUNT_ERR = (
    "error: the amount must be a number from 0.01 to 1000000.00 with at most two decimals\n"
)
CATEGORY_ERR = "error: the category must be 1 to 20 lowercase letters\n"
LEDGER_ERR = "error: the data file is not a valid ledger\n"


def run_cli(
    args: list[str],
    *,
    data_file: Path | str | None = None,
    cwd: Path = ROOT,
) -> subprocess.CompletedProcess[str]:
    env = {k: v for k, v in os.environ.items() if k != "LEDGER_DATA"}
    if data_file is not None:
        env["LEDGER_DATA"] = str(data_file)
    return subprocess.run(
        [sys.executable, str(MAIN_PY), *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def assert_uuid4(text: str) -> None:
    parsed = uuid.UUID(text)
    assert parsed.version == 4
    assert str(parsed) == text


def assert_iso_utc(text: str) -> None:
    assert "T" in text
    parsed = datetime.fromisoformat(text)
    assert parsed.tzinfo == UTC


def assert_stored_entry(
    data_file: Path,
    *,
    entry_id: str,
    amount_cents: int,
    category: str,
    note: str,
) -> None:
    stored = json.loads(data_file.read_text(encoding="utf-8"))
    assert list(stored) == ["entries"]
    assert len(stored["entries"]) == 1
    entry = stored["entries"][0]
    assert set(entry) == {"id", "amount_cents", "category", "note", "created"}
    assert {k: v for k, v in entry.items() if k != "created"} == {
        "id": entry_id,
        "amount_cents": amount_cents,
        "category": category,
        "note": note,
    }
    assert isinstance(entry["created"], str)
    assert_iso_utc(entry["created"])


def test_ledg_001_ex_001_add_prints_the_id_and_stores_the_entry(tmp_path: Path) -> None:
    data_file = tmp_path / "ledger.json"
    added = run_cli(["add", "12.50", "food", "--note", "lunch"], data_file=data_file)

    assert added.returncode == 0
    assert added.stderr == ""
    assert added.stdout.endswith("\n")
    entry_id = added.stdout[:-1]
    assert_uuid4(entry_id)
    assert_stored_entry(
        data_file,
        entry_id=entry_id,
        amount_cents=1250,
        category="food",
        note="lunch",
    )

    listed = run_cli(["list"], data_file=data_file)
    assert listed.returncode == 0
    assert listed.stderr == ""
    assert listed.stdout == f"{entry_id}\t12.50\tfood\tlunch\n"


def test_ledg_001_ex_004_largest_amount_is_stored(tmp_path: Path) -> None:
    data_file = tmp_path / "ledger.json"
    first = run_cli(["add", "1000000.00", "food"], data_file=data_file)
    assert first.returncode == 0
    assert first.stderr == ""
    assert_uuid4(first.stdout.rstrip("\n"))

    snapshot = data_file.read_text(encoding="utf-8")
    second = run_cli(["add", "1000000.01", "food"], data_file=data_file)
    assert second.returncode == 2
    assert second.stdout == ""
    assert second.stderr == AMOUNT_ERR
    assert data_file.read_text(encoding="utf-8") == snapshot


def test_ledg_001_add_without_note_stores_empty_note(tmp_path: Path) -> None:
    data_file = tmp_path / "ledger.json"
    added = run_cli(["add", "5.00", "food"], data_file=data_file)

    assert added.returncode == 0
    assert added.stderr == ""
    entry_id = added.stdout.rstrip("\n")
    assert_uuid4(entry_id)
    stored = json.loads(data_file.read_text(encoding="utf-8"))
    assert stored["entries"][0]["note"] == ""
    assert_iso_utc(stored["entries"][0]["created"])


def test_ledg_001_two_adds_produce_distinct_uuid4_ids(tmp_path: Path) -> None:
    data_file = tmp_path / "ledger.json"
    first = run_cli(["add", "1.00", "food"], data_file=data_file)
    second = run_cli(["add", "2.00", "food"], data_file=data_file)

    assert first.returncode == 0
    assert second.returncode == 0
    first_id = first.stdout.rstrip("\n")
    second_id = second.stdout.rstrip("\n")
    assert_uuid4(first_id)
    assert_uuid4(second_id)
    assert first_id != second_id


def test_ledg_002_ex_002_cli_refuses_three_decimals(tmp_path: Path) -> None:
    data_file = tmp_path / "ledger.json"
    seed = run_cli(["add", "5.00", "food"], data_file=data_file)
    assert seed.returncode == 0
    before = data_file.read_text(encoding="utf-8")

    result = run_cli(["add", "12.345", "food"], data_file=data_file)
    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == AMOUNT_ERR
    assert data_file.read_text(encoding="utf-8") == before


def test_ledg_002_ex_003_cli_refuses_zero(tmp_path: Path) -> None:
    data_file = tmp_path / "ledger.json"
    result = run_cli(["add", "0", "food"], data_file=data_file)

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == AMOUNT_ERR
    assert not data_file.exists()


def test_ledg_003_ex_005_uppercase_category_is_refused(tmp_path: Path) -> None:
    data_file = tmp_path / "ledger.json"
    result = run_cli(["add", "5", "Food"], data_file=data_file)

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == CATEGORY_ERR
    assert not data_file.exists()


@pytest.mark.parametrize(
    ("category", "expected_code"),
    [
        ("", 2),
        ("a", 0),
        ("a" * 20, 0),
        ("a" * 21, 2),
    ],
)
def test_ledg_003_category_length_limits(tmp_path: Path, category: str, expected_code: int) -> None:
    data_file = tmp_path / "ledger.json"
    result = run_cli(["add", "1", category], data_file=data_file)

    assert result.returncode == expected_code
    if expected_code == 0:
        assert result.stderr == ""
        assert_uuid4(result.stdout.rstrip("\n"))
    else:
        assert result.stdout == ""
        assert result.stderr == CATEGORY_ERR
        assert not data_file.exists()


@pytest.mark.parametrize("category", ["food1", "fast-food", "fast_food", "café", "fast food"])
def test_ledg_003_invalid_category_characters_are_refused(tmp_path: Path, category: str) -> None:
    data_file = tmp_path / "ledger.json"
    result = run_cli(["add", "1", category], data_file=data_file)

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == CATEGORY_ERR
    assert not data_file.exists()


def test_ledg_004_ex_006_total_and_total_of_a_category(tmp_path: Path) -> None:
    data_file = tmp_path / "ledger.json"
    assert run_cli(["add", "12.50", "food"], data_file=data_file).returncode == 0
    assert run_cli(["add", "7.25", "food"], data_file=data_file).returncode == 0
    assert run_cli(["add", "3", "bus"], data_file=data_file).returncode == 0

    all_total = run_cli(["total"], data_file=data_file)
    assert all_total.returncode == 0
    assert all_total.stderr == ""
    assert all_total.stdout == "22.75\n"

    food_total = run_cli(["total", "--category", "food"], data_file=data_file)
    assert food_total.returncode == 0
    assert food_total.stderr == ""
    assert food_total.stdout == "19.75\n"


def test_ledg_004_ex_007_empty_total(tmp_path: Path) -> None:
    data_file = tmp_path / "missing" / "ledger.json"
    result = run_cli(["total"], data_file=data_file)

    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout == "0.00\n"
    assert not data_file.exists()


def test_ledg_004_total_for_unknown_category_is_zero(tmp_path: Path) -> None:
    data_file = tmp_path / "ledger.json"
    assert run_cli(["add", "5.00", "food"], data_file=data_file).returncode == 0

    result = run_cli(["total", "--category", "travel"], data_file=data_file)
    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout == "0.00\n"


def test_ledg_004_total_is_idempotent_with_exact_cents(tmp_path: Path) -> None:
    data_file = tmp_path / "ledger.json"
    assert run_cli(["add", "0.10", "food"], data_file=data_file).returncode == 0
    assert run_cli(["add", "0.20", "food"], data_file=data_file).returncode == 0

    first = run_cli(["total"], data_file=data_file)
    second = run_cli(["total"], data_file=data_file)
    assert first.returncode == 0
    assert first.stderr == ""
    assert first.stdout == "0.30\n"
    assert second.returncode == 0
    assert second.stderr == ""
    assert second.stdout == "0.30\n"


def test_ledg_005_ex_008_list_in_order_of_entry(tmp_path: Path) -> None:
    data_file = tmp_path / "ledger.json"
    first = run_cli(["add", "4.10", "bus"], data_file=data_file)
    second = run_cli(["add", "2", "food", "--note", "bread"], data_file=data_file)
    assert first.returncode == 0
    assert second.returncode == 0

    first_id = first.stdout.rstrip("\n")
    second_id = second.stdout.rstrip("\n")
    listed = run_cli(["list"], data_file=data_file)
    assert listed.returncode == 0
    assert listed.stderr == ""
    assert listed.stdout == f"{first_id}\t4.10\tbus\t\n{second_id}\t2.00\tfood\tbread\n"


def test_ledg_005_list_on_empty_ledger_prints_nothing(tmp_path: Path) -> None:
    data_file = tmp_path / "ledger.json"
    listed = run_cli(["list"], data_file=data_file)

    assert listed.returncode == 0
    assert listed.stderr == ""
    assert listed.stdout == ""
    assert not data_file.exists()


def test_ledg_006_ex_009_add_makes_the_folder(tmp_path: Path) -> None:
    added = run_cli(["add", "1", "food"], data_file="new/ledger.json", cwd=tmp_path)
    assert added.returncode == 0
    assert added.stderr == ""
    assert (tmp_path / "new" / "ledger.json").is_file()

    total = run_cli(["total"], data_file="new/ledger.json", cwd=tmp_path)
    assert total.returncode == 0
    assert total.stderr == ""
    assert total.stdout == "1.00\n"


def test_ledg_006_default_data_file_path(tmp_path: Path) -> None:
    added = run_cli(["add", "2.50", "coffee"], data_file=None, cwd=tmp_path)
    assert added.returncode == 0
    assert added.stderr == ""
    assert (tmp_path / "data" / "ledger.json").is_file()

    total = run_cli(["total"], data_file=None, cwd=tmp_path)
    assert total.returncode == 0
    assert total.stderr == ""
    assert total.stdout == "2.50\n"


def test_ledg_007_ex_010_invalid_data_file_exits_3(tmp_path: Path) -> None:
    data_file = tmp_path / "ledger.json"
    data_file.write_text("not json", encoding="utf-8")

    result = run_cli(["total"], data_file=data_file)
    assert result.returncode == 3
    assert result.stdout == ""
    assert result.stderr == LEDGER_ERR
    assert data_file.read_text(encoding="utf-8") == "not json"


@pytest.mark.parametrize("args", [["add", "1", "food"], ["list"]])
def test_ledg_007_add_and_list_on_invalid_data_file_exit_3(tmp_path: Path, args: list[str]) -> None:
    data_file = tmp_path / "ledger.json"
    data_file.write_text("not json", encoding="utf-8")

    result = run_cli(args, data_file=data_file)
    assert result.returncode == 3
    assert result.stdout == ""
    assert result.stderr == LEDGER_ERR
    assert data_file.read_text(encoding="utf-8") == "not json"
