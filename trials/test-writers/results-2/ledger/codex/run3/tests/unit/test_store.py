import json
from importlib import import_module
from pathlib import Path

import pytest

store = import_module("src.store")


def _entry_fields() -> dict[str, object]:
    return {
        "id": "76543210-abcd-4321-8abc-0123456789ab",
        "amount_cents": 410,
        "category": "bus",
        "note": "",
        "created": "2026-11-23T10:00:00Z",
    }


def _assert_invalid_file(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    with pytest.raises(ValueError, match=r"^the data file is not a valid ledger\Z"):
        store.load(path)


def test_ledg_006_missing_file_is_an_empty_ledger(tmp_path: Path) -> None:
    assert store.load(tmp_path / "new" / "ledger.json") == []


def test_ledg_006_save_writes_the_entry_fields(tmp_path: Path) -> None:
    entry = store.Entry(
        "76543210-abcd-4321-8abc-0123456789ab", 410, "bus", "", "2026-11-23T10:00:00Z"
    )
    path = tmp_path / "new" / "ledger.json"
    store.save(path, [entry])
    assert json.loads(path.read_text(encoding="utf-8")) == {"entries": [_entry_fields()]}
    assert store.load(path) == [entry]


def test_ledg_006_replacing_the_ledger_preserves_the_previous_file(tmp_path: Path) -> None:
    path = tmp_path / "ledger.json"
    previous_content = json.dumps({"entries": [_entry_fields()]})
    path.write_text(previous_content, encoding="utf-8")
    previous_file = tmp_path / "previous.json"
    previous_file.hardlink_to(path)
    store.save(path, [])
    assert json.loads(path.read_text(encoding="utf-8")) == {"entries": []}
    assert previous_file.read_text(encoding="utf-8") == previous_content


@pytest.mark.parametrize(
    "content",
    ["not json", "null", "[]", "{}", '{"entries": {}}', '{"entries": [], "extra": 1}'],
)
def test_ledg_007_invalid_file_raises_value_error(tmp_path: Path, content: str) -> None:
    _assert_invalid_file(tmp_path / "ledger.json", content)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("id", "not-a-uuid"),
        ("id", "76543210-abcd-1321-8abc-0123456789ab"),
        ("amount_cents", 0),
        ("amount_cents", 100_000_001),
        ("amount_cents", 4.5),
        ("amount_cents", True),
        ("category", "Bus"),
        ("note", None),
        ("created", "yesterday"),
        ("created", "2026-11-23T10:00:00"),
        ("extra", "unexpected"),
    ],
)
def test_ledg_007_invalid_entry_is_refused(tmp_path: Path, key: str, value: object) -> None:
    entry = _entry_fields()
    entry[key] = value
    content = json.dumps({"entries": [entry]})
    _assert_invalid_file(tmp_path / "ledger.json", content)


@pytest.mark.parametrize("missing", ["id", "amount_cents", "category", "note", "created"])
def test_ledg_007_incomplete_entry_is_refused(tmp_path: Path, missing: str) -> None:
    entry = _entry_fields()
    del entry[missing]
    _assert_invalid_file(tmp_path / "ledger.json", json.dumps({"entries": [entry]}))
