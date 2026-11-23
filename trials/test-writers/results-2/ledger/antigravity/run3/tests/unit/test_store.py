import json
import os
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from src.store import Entry, load, save

LEDGER_ERROR = r"^the data file is not a valid ledger$"
VALID_ID_1 = "550e8400-e29b-41d4-a716-446655440000"
VALID_ID_2 = "7c9e6679-7425-40de-944b-e07fc1f90ae7"
VALID_CREATED = "2026-11-23T10:00:00Z"


def _valid_entry_dict(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "id": VALID_ID_1,
        "amount_cents": 1250,
        "category": "food",
        "note": "lunch",
        "created": VALID_CREATED,
    }
    base.update(overrides)
    return base


def test_ledg_006_missing_file_is_an_empty_ledger(tmp_path: Path) -> None:
    assert load(tmp_path / "missing.json") == []


def test_ledg_006_save_and_load_round_trip_and_stored_format(tmp_path: Path) -> None:
    entry_1 = Entry(VALID_ID_1, 410, "bus", "", VALID_CREATED)
    entry_2 = Entry(VALID_ID_2, 200, "food", "bread", "2026-11-23T10:05:00Z")
    field_name = "note"
    with pytest.raises(FrozenInstanceError):
        setattr(entry_1, field_name, "changed")

    path = tmp_path / "nested" / "ledger.json"
    save(path, [entry_1, entry_2])

    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw == {
        "entries": [
            {
                "id": VALID_ID_1,
                "amount_cents": 410,
                "category": "bus",
                "note": "",
                "created": VALID_CREATED,
            },
            {
                "id": VALID_ID_2,
                "amount_cents": 200,
                "category": "food",
                "note": "bread",
                "created": "2026-11-23T10:05:00Z",
            },
        ]
    }
    assert load(path) == [entry_1, entry_2]


def test_ledg_006_atomic_save_keeps_old_data_on_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "ledger.json"
    old_entry = Entry(VALID_ID_1, 1250, "food", "lunch", VALID_CREATED)
    new_entry = Entry(VALID_ID_2, 500, "bus", "", "2026-11-23T11:00:00Z")
    save(path, [old_entry])

    def fail_replace(_src: object, _dst: object) -> None:
        raise OSError("simulated replace failure")

    monkeypatch.setattr(os, "replace", fail_replace)
    with pytest.raises(OSError, match="simulated replace failure"):
        save(path, [new_entry])

    assert load(path) == [old_entry]


def test_ledg_007_invalid_file_raises_value_error(tmp_path: Path) -> None:
    path = tmp_path / "ledger.json"
    path.write_text("not json", encoding="utf-8")

    with pytest.raises(ValueError, match=LEDGER_ERROR):
        load(path)


@pytest.mark.parametrize(
    "payload",
    [
        [],
        {},
        {"entries": [], "extra": 1},
        {"entries": "not-a-list"},
        {"entries": ["not-an-object"]},
        {"entries": [{k: v for k, v in _valid_entry_dict().items() if k != "note"}]},
        {"entries": [{**_valid_entry_dict(), "extra": 1}]},
        {"entries": [_valid_entry_dict(amount_cents=0)]},
        {"entries": [_valid_entry_dict(amount_cents=100_000_001)]},
        {"entries": [_valid_entry_dict(amount_cents="1250")]},
        {"entries": [_valid_entry_dict(amount_cents=True)]},
        {"entries": [_valid_entry_dict(category="Food")]},
        {"entries": [_valid_entry_dict(category="")]},
        {"entries": [_valid_entry_dict(category="a" * 21)]},
        {"entries": [_valid_entry_dict(id="not-a-uuid")]},
        {"entries": [_valid_entry_dict(note=123)]},
        {"entries": [_valid_entry_dict(created="not-a-timestamp")]},
    ],
)
def test_ledg_007_invalid_ledger_structures_raise_value_error(
    tmp_path: Path, payload: object
) -> None:
    path = tmp_path / "ledger.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match=LEDGER_ERROR):
        load(path)
