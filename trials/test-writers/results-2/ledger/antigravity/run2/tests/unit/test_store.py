import dataclasses
import json
import re
from pathlib import Path

import pytest

from src.store import Entry, load, save

LEDGER_ERROR = "the data file is not a valid ledger"
LEDGER_ERROR_PATTERN = f"^{re.escape(LEDGER_ERROR)}$"

VALID_ENTRY_DICT = {
    "id": "11111111-1111-4111-8111-111111111111",
    "amount_cents": 1250,
    "category": "food",
    "note": "lunch",
    "created": "2026-11-23T10:00:00Z",
}


def test_ledg_006_missing_file_is_an_empty_ledger(tmp_path: Path) -> None:
    missing = tmp_path / "does-not-exist" / "ledger.json"
    assert load(missing) == []


def test_ledg_006_entry_is_frozen_dataclass() -> None:
    entry = Entry(
        "11111111-1111-4111-8111-111111111111",
        1250,
        "food",
        "lunch",
        "2026-11-23T10:00:00Z",
    )
    assert dataclasses.is_dataclass(entry)
    field_name = "note"
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(entry, field_name, "dinner")


def test_ledg_006_save_and_load_roundtrip_and_stored_json_format(tmp_path: Path) -> None:
    data_file = tmp_path / "nested" / "ledger.json"
    entries = [
        Entry(
            "11111111-1111-4111-8111-111111111111",
            410,
            "bus",
            "",
            "2026-11-23T10:00:00Z",
        ),
        Entry(
            "22222222-2222-4222-8222-222222222222",
            200,
            "food",
            "bread",
            "2026-11-23T10:05:00Z",
        ),
    ]
    save(data_file, entries)

    raw = json.loads(data_file.read_text(encoding="utf-8"))
    assert raw == {
        "entries": [
            {
                "id": "11111111-1111-4111-8111-111111111111",
                "amount_cents": 410,
                "category": "bus",
                "note": "",
                "created": "2026-11-23T10:00:00Z",
            },
            {
                "id": "22222222-2222-4222-8222-222222222222",
                "amount_cents": 200,
                "category": "food",
                "note": "bread",
                "created": "2026-11-23T10:05:00Z",
            },
        ]
    }
    assert load(data_file) == entries


def test_ledg_006_save_overwrites_cleanly_without_leftover_files(tmp_path: Path) -> None:
    data_file = tmp_path / "ledger.json"
    first = Entry(
        "11111111-1111-4111-8111-111111111111",
        100,
        "food",
        "tea",
        "2026-11-23T10:00:00Z",
    )
    second = Entry(
        "22222222-2222-4222-8222-222222222222",
        250,
        "bus",
        "",
        "2026-11-23T10:01:00Z",
    )
    save(data_file, [first])
    save(data_file, [first, second])

    assert load(data_file) == [first, second]
    assert list(tmp_path.iterdir()) == [data_file]


def test_ledg_007_invalid_file_raises_value_error(tmp_path: Path) -> None:
    data_file = tmp_path / "ledger.json"
    data_file.write_text("not json", encoding="utf-8")

    with pytest.raises(ValueError, match=LEDGER_ERROR_PATTERN):
        load(data_file)


def test_ledg_007_invalid_utf8_bytes_raise_value_error(tmp_path: Path) -> None:
    data_file = tmp_path / "ledger.json"
    data_file.write_bytes(b"\xff\xfe")

    with pytest.raises(ValueError, match=LEDGER_ERROR_PATTERN):
        load(data_file)


@pytest.mark.parametrize(
    "payload",
    [
        [],
        {},
        {"entries": [], "extra": 1},
        {"entries": "not a list"},
        {"entries": ["not an object"]},
        {"entries": [{k: v for k, v in VALID_ENTRY_DICT.items() if k != "note"}]},
        {"entries": [{**VALID_ENTRY_DICT, "extra": "unexpected"}]},
        {"entries": [{**VALID_ENTRY_DICT, "amount_cents": "1250"}]},
        {"entries": [{**VALID_ENTRY_DICT, "amount_cents": True}]},
        {"entries": [{**VALID_ENTRY_DICT, "amount_cents": 0}]},
        {"entries": [{**VALID_ENTRY_DICT, "amount_cents": 100_000_001}]},
        {"entries": [{**VALID_ENTRY_DICT, "note": 123}]},
    ],
)
def test_ledg_007_invalid_ledger_structures_raise_value_error(
    tmp_path: Path, payload: object
) -> None:
    data_file = tmp_path / "ledger.json"
    data_file.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match=LEDGER_ERROR_PATTERN):
        load(data_file)
