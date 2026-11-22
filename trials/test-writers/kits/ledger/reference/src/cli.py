"""The command line of the ledger (LEDG-001 to LEDG-007)."""

import os
import re
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

from src.money import format_amount, parse_amount
from src.store import Entry, load, save

CATEGORY = re.compile(r"[a-z]{1,20}")
CATEGORY_ERROR = "the category must be 1 to 20 lowercase letters"
DEFAULT_DATA = "data/ledger.json"
USAGE = "usage: python main.py add AMOUNT CATEGORY [--note TEXT] | total [--category C] | list"


def data_path() -> Path:
    """Return the path of the data file: LEDGER_DATA, or the default."""
    return Path(os.environ.get("LEDGER_DATA", DEFAULT_DATA))


def option(args: list[str], name: str) -> tuple[list[str], str | None]:
    """Return the arguments without an option and its value, and the value (None without it)."""
    if name not in args:
        return args, None
    index = args.index(name)
    value = args[index + 1] if index + 1 < len(args) else ""
    return args[:index] + args[index + 2 :], value


def add(args: list[str], path: Path, entries: list[Entry]) -> int:
    """Store one entry and print its ID."""
    args, note = option(args, "--note")
    if len(args) != 2:
        print(USAGE, file=sys.stderr)
        return 2
    try:
        cents = parse_amount(args[0])
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    if not CATEGORY.fullmatch(args[1]):
        print(f"error: {CATEGORY_ERROR}", file=sys.stderr)
        return 2
    created = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    entry = Entry(str(uuid.uuid4()), cents, args[1], note or "", created)
    save(path, [*entries, entry])
    print(entry.id)
    return 0


def total(args: list[str], entries: list[Entry]) -> int:
    """Print the total of the entries, of one category when one is given."""
    _, category = option(args, "--category")
    cents = sum(e.amount_cents for e in entries if category is None or e.category == category)
    print(format_amount(cents))
    return 0


def listing(entries: list[Entry]) -> int:
    """Print one line for each entry, in the order of entry."""
    for e in entries:
        print(f"{e.id}\t{format_amount(e.amount_cents)}\t{e.category}\t{e.note}")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Run one command and return the exit code."""
    args = sys.argv[1:] if argv is None else argv
    path = data_path()
    try:
        entries = load(path)
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 3
    if args[:1] == ["add"]:
        return add(args[1:], path, entries)
    if args[:1] == ["total"]:
        return total(args[1:], entries)
    if args[:1] == ["list"]:
        return listing(entries)
    print(USAGE, file=sys.stderr)
    return 2
