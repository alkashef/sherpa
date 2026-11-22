"""The data file of the ledger (LEDG-006, LEDG-007, DEC-003)."""

import json
import os
import re
import tempfile
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

LEDGER_ERROR = "the data file is not a valid ledger"
FIELDS = {"id": str, "amount_cents": int, "category": str, "note": str, "created": str}
MAX_CENTS = 100_000_000
CATEGORY = re.compile(r"[a-z]{1,20}")
UUID_VERSION = 4
UTC_TIME = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z")


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
    """Tell whether an object of the data file is an entry of the data model of the design.

    The five keys, each of its type, and the limits of the data model: a UUID 4, an amount of 1
    to 100000000 cents, a category of 1 to 20 letters from a to z, and a time in UTC.
    """
    if not isinstance(entry, dict) or set(entry) != set(FIELDS):
        return False
    if not all(
        isinstance(entry[key], kind) and not isinstance(entry[key], bool)
        for key, kind in FIELDS.items()
    ):
        return False
    return (
        uuid4_text(entry["id"])
        and 1 <= entry["amount_cents"] <= MAX_CENTS
        and CATEGORY.fullmatch(entry["category"]) is not None
        and utc_text(entry["created"])
    )


def utc_text(text: str) -> bool:
    """Tell whether a text is a time of ISO 8601 in UTC, such as 2026-11-23T10:00:00Z."""
    if UTC_TIME.fullmatch(text) is None:
        return False
    try:
        datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def uuid4_text(text: str) -> bool:
    """Tell whether a text is a UUID of version 4, in its usual form."""
    try:
        value = uuid.UUID(text)
    except ValueError:
        return False
    return value.version == UUID_VERSION and str(value) == text.lower()


def save(path: Path, entries: list[Entry]) -> None:
    """Write the entries to a temporary file, then replace the data file with it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps({"entries": [asdict(entry) for entry in entries]}, indent=2)
    handle, temporary = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    with os.fdopen(handle, "w", encoding="utf-8") as file:
        file.write(text)
    os.replace(temporary, path)
