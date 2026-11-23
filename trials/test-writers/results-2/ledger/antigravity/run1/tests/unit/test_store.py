import dataclasses
import json
import os
import re
from pathlib import Path

import pytest

from src.store import Entry, load, save

LEDGER_ERROR = "the data file is not a valid ledger"
LEDGER_ERROR_PATTERN = f"^{re.escape(LEDGER_ERROR)}$"

VALID_ENTRY_DICT = {
    "id": "11111111-1111-4111-8111-111111111111",
    "amount_cents": 410,
    "category": "bus",
    "note": "",
    "created": "2026-11-23T10:00:00Z",
}


def _sample_entries() -> list[Entry]:
    first = Entry(
        "11111111-1111-4111-8111-111111111111",
        410,
        "bus",
        "",
        "2026-11-23T10:00:00Z",
    )
    second = Entry(
        "22222222-2222-4222-8222-222222222222",
        200,
        "food",
        "bread",
        "2026-11-23T10:05:00Z",
    )
    return [first, second]


def test_ledg_006_missing_file_is_an_empty_ledger(tmp_path: Path) -> None:
    path = tmp_path / "missing" / "ledger.json"
    assert load(path) == []
    assert not path.exists()


def test_ledg_006_save_and_load_preserves_order_and_stored_json(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "ledger.json"
    entries = _sample_entries()
    save(path, entries)
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw == {
        "entries": [
            VALID_ENTRY_DICT,
            {
                "id": "22222222-2222-4222-8222-222222222222",
                "amount_cents": 200,
                "category": "food",
                "note": "bread",
                "created": "2026-11-23T10:05:00Z",
            },
        ]
    }
    assert load(path) == entries


def test_ledg_006_entry_is_frozen_dataclass() -> None:
    entry = _sample_entries()[0]
    assert dataclasses.is_dataclass(entry)
    field_name = "note"
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(entry, field_name, "changed")


def test_ledg_006_save_failure_leaves_old_data_readable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "ledger.json"
    first, second = _sample_entries()
    save(path, [first])

    def fail_replace(src: str | os.PathLike[str], dst: str | os.PathLike[str]) -> None:
        raise OSError(f"cannot replace {dst} from {src}")

    monkeypatch.setattr(os, "replace", fail_replace)
    with pytest.raises(OSError, match=r".+"):
        save(path, [first, second])
    assert load(path) == [first]


def test_ledg_007_invalid_file_raises_value_error(tmp_path: Path) -> None:
    path = tmp_path / "ledger.json"
    path.write_text("not json", encoding="utf-8")
    with pytest.raises(ValueError, match=LEDGER_ERROR_PATTERN):
        load(path)


@pytest.mark.parametrize(
    "payload",
    [
        [],
        {},
        {"entries": [], "extra": 1},
        {"entries": {}},
        {"entries": ["bad"]},
        {"entries": [{k: v for k, v in VALID_ENTRY_DICT.items() if k != "note"}]},
        {"entries": [{**VALID_ENTRY_DICT, "extra": 1}]},
        {"entries": [{**VALID_ENTRY_DICT, "amount_cents": "410"}]},
        {"entries": [{**VALID_ENTRY_DICT, "amount_cents": True}]},
        {"entries": [{**VALID_ENTRY_DICT, "amount_cents": 0}]},
        {"entries": [{**VALID_ENTRY_DICT, "note": 42}]},
    ],
)
def test_ledg_007_invalid_ledger_shapes_raise_value_error(tmp_path: Path, payload: object) -> None:
    path = tmp_path / "ledger.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match=LEDGER_ERROR_PATTERN):
        load(path)
