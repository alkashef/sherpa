import json
from importlib import import_module
from pathlib import Path

import pytest

store = import_module("src.store")


def _entry_fields() -> dict[str, object]:
    return {
        "id": "40d60ca3-6e57-48c4-a006-a72d23f69317",
        "amount_cents": 410,
        "category": "bus",
        "note": "",
        "created": "2026-11-23T10:00:00Z",
    }


def test_ledg_006_missing_file_is_an_empty_ledger(tmp_path: Path) -> None:
    assert store.load(tmp_path / "missing.json") == []


def test_ledg_006_save_writes_the_entry_fields(tmp_path: Path) -> None:
    path = tmp_path / "new" / "ledger.json"
    fields = _entry_fields()
    store.save(path, [store.Entry(**fields)])
    assert json.loads(path.read_text(encoding="utf-8")) == {"entries": [fields]}


def test_ledg_006_load_reads_stored_entries_in_order(tmp_path: Path) -> None:
    first = _entry_fields()
    second = first | {"id": "a084e594-0308-40b1-b2b6-9124e73caa70", "note": "return"}
    path = tmp_path / "ledger.json"
    path.write_text(json.dumps({"entries": [first, second]}), encoding="utf-8")
    assert store.load(path) == [store.Entry(**first), store.Entry(**second)]


def test_ledg_006_save_replaces_the_previous_file(tmp_path: Path) -> None:
    path = tmp_path / "ledger.json"
    old_contents = b'{"entries":[]}'
    path.write_bytes(old_contents)
    previous = tmp_path / "previous.json"
    previous.hardlink_to(path)
    fields = _entry_fields()
    store.save(path, [store.Entry(**fields)])
    assert previous.read_bytes() == old_contents
    assert json.loads(path.read_text(encoding="utf-8")) == {"entries": [fields]}


def _assert_invalid_file(path: Path) -> None:
    with pytest.raises(ValueError, match=r"^the data file is not a valid ledger\Z"):
        store.load(path)


@pytest.mark.parametrize(
    "contents",
    ["not json", "[]", "{}", '{"entries": {}}', '{"entries": [], "extra": 1}', '{"entries": [42]}'],
)
def test_ledg_007_invalid_file_raises_value_error(tmp_path: Path, contents: str) -> None:
    path = tmp_path / "ledger.json"
    path.write_text(contents, encoding="utf-8")
    _assert_invalid_file(path)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("amount_cents", 0),
        ("amount_cents", 100_000_001),
        ("amount_cents", True),
        ("amount_cents", 4.1),
        ("amount_cents", "410"),
        ("id", "invalid"),
        ("id", "40d60ca3-6e57-18c4-a006-a72d23f69317"),
        ("category", "Bus"),
        ("category", 12),
        ("note", None),
        ("created", "yesterday"),
        ("created", "2026-11-23T10:00:00"),
        ("extra", "unexpected"),
    ],
)
def test_ledg_007_invalid_entry_field(tmp_path: Path, field: str, value: object) -> None:
    fields = _entry_fields() | {field: value}
    path = tmp_path / "ledger.json"
    path.write_text(json.dumps({"entries": [fields]}), encoding="utf-8")
    _assert_invalid_file(path)


@pytest.mark.parametrize("field", ["id", "amount_cents", "category", "note", "created"])
def test_ledg_007_missing_entry_field(tmp_path: Path, field: str) -> None:
    fields = _entry_fields()
    del fields[field]
    path = tmp_path / "ledger.json"
    path.write_text(json.dumps({"entries": [fields]}), encoding="utf-8")
    _assert_invalid_file(path)
