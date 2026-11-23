"""Unit tests of src/store.py: the data file (LEDG-006, LEDG-007, DEC-003)."""

import json
import re
from pathlib import Path

import pytest

from src.store import Entry, load, save

LEDGER_ERROR = re.escape("the data file is not a valid ledger")

FIRST = Entry(
    id="0b6f3c1e-2a4d-4e8f-9b1a-3c5d7e9f1a2b",
    amount_cents=1250,
    category="food",
    note="lunch",
    created="2026-11-23T10:00:00Z",
)
SECOND = Entry(
    id="5d2e8a4c-7b1f-4c3e-8a6d-9f0b2c4e6a8d",
    amount_cents=300,
    category="bus",
    note="",
    created="2026-11-23T11:30:00Z",
)
VALID_ENTRY = {
    "id": FIRST.id,
    "amount_cents": 1250,
    "category": "food",
    "note": "lunch",
    "created": "2026-11-23T10:00:00Z",
}


def test_ledg_006_missing_file_is_an_empty_ledger(tmp_path: Path) -> None:
    assert load(tmp_path / "ledger.json") == []


def test_ledg_006_save_then_load_gives_the_entries_in_order(tmp_path: Path) -> None:
    path = tmp_path / "ledger.json"
    save(path, [FIRST, SECOND])
    assert load(path) == [FIRST, SECOND]


def test_ledg_006_stored_form_of_an_entry(tmp_path: Path) -> None:
    path = tmp_path / "ledger.json"
    save(path, [FIRST])
    assert json.loads(path.read_text(encoding="utf-8")) == {"entries": [VALID_ENTRY]}


def test_ledg_006_save_makes_the_folder(tmp_path: Path) -> None:
    path = tmp_path / "new" / "deeper" / "ledger.json"
    save(path, [FIRST])
    assert load(path) == [FIRST]


def test_ledg_006_save_replaces_the_old_entries(tmp_path: Path) -> None:
    path = tmp_path / "ledger.json"
    save(path, [FIRST])
    save(path, [FIRST, SECOND])
    assert load(path) == [FIRST, SECOND]


def test_ledg_006_save_leaves_only_the_data_file(tmp_path: Path) -> None:
    path = tmp_path / "ledger.json"
    save(path, [FIRST])
    save(path, [FIRST, SECOND])
    assert [child.name for child in tmp_path.iterdir()] == ["ledger.json"]


def test_ledg_006_empty_entries_load_as_an_empty_ledger(tmp_path: Path) -> None:
    path = tmp_path / "ledger.json"
    path.write_text('{"entries": []}', encoding="utf-8")
    assert load(path) == []


def test_ledg_007_invalid_file_raises_value_error(tmp_path: Path) -> None:
    path = tmp_path / "ledger.json"
    path.write_text("not json", encoding="utf-8")
    with pytest.raises(ValueError, match=LEDGER_ERROR):
        load(path)


@pytest.mark.parametrize(
    "content",
    [
        "",
        "[]",
        "{}",
        '{"entries": 5}',
        '{"entries": [], "other": 1}',
        '{"entries": ["food"]}',
        json.dumps({"entries": [{k: v for k, v in VALID_ENTRY.items() if k != "note"}]}),
        json.dumps({"entries": [{**VALID_ENTRY, "other": 1}]}),
        json.dumps({"entries": [{**VALID_ENTRY, "amount_cents": "1250"}]}),
    ],
)
def test_ledg_007_content_that_is_not_a_ledger_raises_value_error(
    tmp_path: Path, content: str
) -> None:
    path = tmp_path / "ledger.json"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(ValueError, match=LEDGER_ERROR):
        load(path)


def test_ledg_007_load_of_an_invalid_file_changes_nothing(tmp_path: Path) -> None:
    path = tmp_path / "ledger.json"
    path.write_text("not json", encoding="utf-8")
    with pytest.raises(ValueError, match=LEDGER_ERROR):
        load(path)
    assert path.read_text(encoding="utf-8") == "not json"
