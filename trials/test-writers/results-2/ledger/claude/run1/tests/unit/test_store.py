import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from src.store import Entry, load, save

LEDGER_ERROR = "the data file is not a valid ledger"
LUNCH = Entry(
    id="0b6f1d2e-3c4a-4b5d-8e6f-7a8b9c0d1e2f",
    amount_cents=1250,
    category="food",
    note="lunch",
    created="2026-11-23T10:00:00Z",
)
BUS = Entry(
    id="1c7a2e3f-4d5b-4c6e-9f70-8b9c0d1e2f3a",
    amount_cents=300,
    category="bus",
    note="",
    created="2026-11-23T11:30:00Z",
)
LUNCH_RECORD = {
    "id": "0b6f1d2e-3c4a-4b5d-8e6f-7a8b9c0d1e2f",
    "amount_cents": 1250,
    "category": "food",
    "note": "lunch",
    "created": "2026-11-23T10:00:00Z",
}


def test_ledg_006_missing_file_is_an_empty_ledger(tmp_path: Path) -> None:
    path = tmp_path / "ledger.json"
    assert load(path) == []
    assert not path.exists()


def test_ledg_006_saved_entries_load_in_order_of_entry(tmp_path: Path) -> None:
    path = tmp_path / "ledger.json"
    save(path, [LUNCH, BUS])
    assert load(path) == [LUNCH, BUS]


def test_ledg_006_save_replaces_the_old_entries(tmp_path: Path) -> None:
    path = tmp_path / "ledger.json"
    save(path, [LUNCH])
    save(path, [LUNCH, BUS])
    assert load(path) == [LUNCH, BUS]


def test_ledg_006_save_makes_the_folder(tmp_path: Path) -> None:
    path = tmp_path / "new" / "deeper" / "ledger.json"
    save(path, [LUNCH])
    assert path.is_file()
    assert load(path) == [LUNCH]


def test_ledg_006_stored_form_of_an_entry(tmp_path: Path) -> None:
    path = tmp_path / "ledger.json"
    save(path, [LUNCH])
    assert json.loads(path.read_text(encoding="utf-8")) == {"entries": [LUNCH_RECORD]}


def test_ledg_006_load_reads_a_file_in_the_stored_form(tmp_path: Path) -> None:
    path = tmp_path / "ledger.json"
    path.write_text(json.dumps({"entries": [LUNCH_RECORD]}), encoding="utf-8")
    assert load(path) == [LUNCH]


def test_ledg_006_save_leaves_only_the_data_file(tmp_path: Path) -> None:
    path = tmp_path / "ledger.json"
    save(path, [LUNCH])
    save(path, [LUNCH, BUS])
    assert [child.name for child in tmp_path.iterdir()] == ["ledger.json"]


def test_ledg_006_entry_is_frozen() -> None:
    attribute = "note"
    with pytest.raises(FrozenInstanceError):
        setattr(LUNCH, attribute, "dinner")
    assert LUNCH.note == "lunch"


@pytest.mark.parametrize(
    "content",
    [
        "not json",
        "",
        "[]",
        '{"entries": "food"}',
        '{"other": []}',
        '{"entries": [], "other": 1}',
        json.dumps({"entries": [{k: v for k, v in LUNCH_RECORD.items() if k != "note"}]}),
        json.dumps({"entries": [{**LUNCH_RECORD, "extra": 1}]}),
        json.dumps({"entries": [{**LUNCH_RECORD, "amount_cents": "1250"}]}),
        json.dumps({"entries": ["food"]}),
    ],
)
def test_ledg_007_invalid_file_raises_value_error(tmp_path: Path, content: str) -> None:
    path = tmp_path / "ledger.json"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(ValueError, match=LEDGER_ERROR):
        load(path)


def test_ledg_007_invalid_file_is_unchanged_by_load(tmp_path: Path) -> None:
    path = tmp_path / "ledger.json"
    path.write_text("not json", encoding="utf-8")
    with pytest.raises(ValueError, match=LEDGER_ERROR):
        load(path)
    assert path.read_text(encoding="utf-8") == "not json"
