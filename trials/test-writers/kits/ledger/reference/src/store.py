"""The data file of the ledger (LEDG-006, LEDG-007, DEC-003)."""

import json
import os
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

LEDGER_ERROR = "the data file is not a valid ledger"
FIELDS = {"id": str, "amount_cents": int, "category": str, "note": str, "created": str}


@dataclass(frozen=True)
class Entry:
    """One expense of the ledger."""

    id: str
    amount_cents: int
    category: str
    note: str
    created: str


def load(path: Path) -> list[Entry]:
    """Return the entries of the data file; a missing file is an empty ledger."""
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ValueError(LEDGER_ERROR) from error
    if not isinstance(data, dict) or set(data) != {"entries"}:
        raise ValueError(LEDGER_ERROR)
    entries = data["entries"]
    if not isinstance(entries, list) or not all(valid_entry(entry) for entry in entries):
        raise ValueError(LEDGER_ERROR)
    return [Entry(**entry) for entry in entries]


def valid_entry(entry: object) -> bool:
    """Tell whether an object of the data file is an entry: the five keys, each of its type."""
    if not isinstance(entry, dict) or set(entry) != set(FIELDS):
        return False
    return all(
        isinstance(entry[key], kind) and not isinstance(entry[key], bool)
        for key, kind in FIELDS.items()
    )


def save(path: Path, entries: list[Entry]) -> None:
    """Write the entries to a temporary file, then replace the data file with it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps({"entries": [asdict(entry) for entry in entries]}, indent=2)
    handle, temporary = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    with os.fdopen(handle, "w", encoding="utf-8") as file:
        file.write(text)
    os.replace(temporary, path)
