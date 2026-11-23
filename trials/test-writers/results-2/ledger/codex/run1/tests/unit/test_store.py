import json
import multiprocessing
import sys
from pathlib import Path

import pytest

from src.store import Entry, load, save


@pytest.fixture
def stored_entry() -> dict[str, object]:
    return {
        "id": "14870c00-1405-4cea-b22c-a7b1323370db",
        "amount_cents": 1250,
        "category": "food",
        "note": "lunch",
        "created": "2026-11-23T10:00:00Z",
    }


def _assert_invalid_ledger(path: Path) -> None:
    with pytest.raises(ValueError, match=r"^the data file is not a valid ledger\Z"):
        load(path)


def test_ledg_006_missing_file_is_an_empty_ledger(tmp_path: Path) -> None:
    assert load(tmp_path / "missing.json") == []


@pytest.mark.parametrize(
    "content",
    ["not json", "[]", "{}", '{"entries": {}}', '{"entries": [], "extra": 0}', '{"entries": [{}]}'],
)
def test_ledg_007_invalid_file_raises_value_error(tmp_path: Path, content: str) -> None:
    path = tmp_path / "ledger.json"
    path.write_text(content, encoding="utf-8")
    _assert_invalid_ledger(path)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("id", "invalid"),
        ("id", "14870c00-1405-1cea-b22c-a7b1323370db"),
        ("amount_cents", 0),
        ("amount_cents", 100_000_001),
        ("amount_cents", "1250"),
        ("amount_cents", 12.5),
        ("amount_cents", True),
        ("category", "Food"),
        ("category", ""),
        ("category", "a" * 21),
        ("note", None),
        ("created", "yesterday"),
        ("created", "2026-11-23T10:00:00"),
        ("extra", ""),
    ],
)
def test_ledg_007_invalid_entry_is_refused(
    tmp_path: Path, stored_entry: dict[str, object], field: str, value: object
) -> None:
    path = tmp_path / "ledger.json"
    invalid_entry = {**stored_entry, field: value}
    path.write_text(json.dumps({"entries": [invalid_entry]}), encoding="utf-8")
    _assert_invalid_ledger(path)


def test_ledg_006_save_writes_the_entry(tmp_path: Path, stored_entry: dict[str, object]) -> None:
    path = tmp_path / "new" / "ledger.json"
    entry = Entry(
        "14870c00-1405-4cea-b22c-a7b1323370db", 1250, "food", "lunch", "2026-11-23T10:00:00Z"
    )
    save(path, [entry])
    assert json.loads(path.read_text(encoding="utf-8")) == {"entries": [stored_entry]}
    assert load(path) == [entry]


def _interrupt_save_at_replacement(path: Path) -> None:
    def interrupt(event: str, args: tuple[object, ...]) -> None:
        if event == "os.rename" and args[1] == str(path):
            sys.exit(42)

    sys.addaudithook(interrupt)
    save(path, [])


def test_ledg_006_interrupted_save_preserves_old_data(
    tmp_path: Path, stored_entry: dict[str, object]
) -> None:
    path = tmp_path / "ledger.json"
    original = json.dumps({"entries": [stored_entry]}).encode("utf-8")
    path.write_bytes(original)
    process = multiprocessing.get_context("spawn").Process(
        target=_interrupt_save_at_replacement, args=(path,)
    )
    process.start()
    process.join()
    assert process.exitcode == 42
    assert path.read_bytes() == original
