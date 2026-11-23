import json
import os
import re
from pathlib import Path

import pytest

from src.store import Entry, load, save

LEDGER_ERROR_PATTERN = f"^{re.escape('the data file is not a valid ledger')}$"

FIRST = Entry(
    id="0b6f3c1e-4d2a-4f6b-9c8d-1a2b3c4d5e6f",
    amount_cents=1250,
    category="food",
    note="lunch",
    created="2026-11-23T10:00:00Z",
)
SECOND = Entry(
    id="7e9d8c7b-6a5f-4e3d-8c2b-1a0f9e8d7c6b",
    amount_cents=300,
    category="bus",
    note="",
    created="2026-11-23T11:30:00Z",
)

VALID_ENTRY = {
    "id": "0b6f3c1e-4d2a-4f6b-9c8d-1a2b3c4d5e6f",
    "amount_cents": 1250,
    "category": "food",
    "note": "lunch",
    "created": "2026-11-23T10:00:00Z",
}


def test_ledg_006_missing_file_is_an_empty_ledger(tmp_path: Path) -> None:
    assert load(tmp_path / "ledger.json") == []


def test_ledg_006_saved_entries_load_in_order_of_entry(tmp_path: Path) -> None:
    path = tmp_path / "ledger.json"
    save(path, [FIRST, SECOND])
    assert load(path) == [FIRST, SECOND]


def test_ledg_006_save_makes_the_folder(tmp_path: Path) -> None:
    path = tmp_path / "new" / "deeper" / "ledger.json"
    save(path, [FIRST])
    assert path.is_file()


def test_ledg_006_stored_form_of_an_entry(tmp_path: Path) -> None:
    path = tmp_path / "ledger.json"
    save(path, [FIRST])
    assert json.loads(path.read_text(encoding="utf-8")) == {"entries": [VALID_ENTRY]}


def test_ledg_006_empty_ledger_is_stored_as_empty_list(tmp_path: Path) -> None:
    path = tmp_path / "ledger.json"
    save(path, [])
    assert json.loads(path.read_text(encoding="utf-8")) == {"entries": []}


def test_ledg_007_invalid_file_raises_value_error(tmp_path: Path) -> None:
    path = tmp_path / "ledger.json"
    path.write_text("not json", encoding="utf-8")
    with pytest.raises(ValueError, match=LEDGER_ERROR_PATTERN):
        load(path)


@pytest.mark.parametrize(
    "content",
    [
        "",
        "[]",
        "{}",
        '{"entries": 5}',
        '{"entries": [], "other": 1}',
        json.dumps({"entries": [{k: v for k, v in VALID_ENTRY.items() if k != "note"}]}),
        json.dumps({"entries": [{**VALID_ENTRY, "extra": "x"}]}),
        json.dumps({"entries": [{**VALID_ENTRY, "amount_cents": "1250"}]}),
        json.dumps({"entries": ["not an entry"]}),
    ],
)
def test_ledg_007_other_content_is_not_a_valid_ledger(tmp_path: Path, content: str) -> None:
    path = tmp_path / "ledger.json"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(ValueError, match=LEDGER_ERROR_PATTERN):
        load(path)


def test_ledg_007_valid_file_written_by_hand_loads(tmp_path: Path) -> None:
    path = tmp_path / "ledger.json"
    path.write_text(json.dumps({"entries": [VALID_ENTRY]}), encoding="utf-8")
    assert load(path) == [FIRST]


def test_dec_003_save_leaves_only_the_data_file(tmp_path: Path) -> None:
    path = tmp_path / "ledger.json"
    save(path, [FIRST])
    save(path, [FIRST, SECOND])
    assert [child.name for child in tmp_path.iterdir()] == ["ledger.json"]


def test_dec_003_interrupted_save_keeps_the_old_ledger(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "ledger.json"
    save(path, [FIRST])

    def _replace_fails(source: object, target: object) -> None:
        raise OSError("the write stopped")

    monkeypatch.setattr(os, "replace", _replace_fails)
    # Any message: the store may add context to the error and re-raise it.
    with pytest.raises(OSError, match=r"."):
        save(path, [FIRST, SECOND])
    monkeypatch.undo()
    assert load(path) == [FIRST]
