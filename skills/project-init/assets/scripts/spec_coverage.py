"""List which requirement IDs have a test, and check the requirement IDs of one milestone.

A requirement ID (AREA-NNN, such as PAY-001, or NFR-NNN) is the first cell of a table row of
docs/spec.md. Scenarios (SCN-NNN), acceptance examples (EX-NNN) and design decisions (DEC-NNN) are
not requirements, and a row with the status Withdrawn is skipped. Each requirement ID has one state:

- tested: a test under tests/ has the ID in its name. PAY-001 is `test_pay_001_...` in a
  `test_*.py` file, or a title such as `test("PAY-001 ...")` in a `*.test.js` file.
- manual: a `Manual:` entry of a milestone block, or the section "Human checks" of docs/plan.md,
  names the ID.
- planned: the Refs of a milestone block in docs/plan.md name the ID.
- missing: none of these.

Without an argument, it lists every requirement ID with its state. With `M<n>`, it checks the
requirement IDs in the Refs of that milestone's block: each must be in the spec, and be tested or
manual (docs/workflow.md, Execute). It only reads files.

Run:
    python scripts/spec_coverage.py [M<n>] [--root FOLDER]
"""

import argparse
import logging
import re
import sys
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger("spec_coverage")

ROOT = Path(__file__).resolve().parent.parent
SPEC_PATH = Path("docs") / "spec.md"
PLAN_PATH = Path("docs") / "plan.md"
TESTS_DIR = "tests"
PYTHON_TESTS = "test_*.py"
WEB_TESTS = ("*.test.js", "*.test.mjs", "*.test.ts")

# The IDs of docs/spec.md and docs/design.md that are not requirements: scenarios, acceptance
# examples and design decisions. Every other ID that starts a table row of the spec is one.
OTHER_PREFIXES = ("SCN", "EX", "DEC")
ANY_ID = r"[A-Z][A-Z0-9]*-\d{3,}"
SPEC_ID = re.compile(rf"\b{ANY_ID}\b")
SPEC_ROW = re.compile(rf"^\|\s*({ANY_ID})\s*\|")
PYTHON_TEST_NAME = re.compile(r"^\s*(?:async\s+)?def\s+(test_\w+)", re.MULTILINE)
WEB_TEST_NAME = re.compile(r"""\b(?:test|it)\(\s*(["'`])(.*?)\1""")
MANUAL_ENTRY = re.compile(rf"Manual:((?:[\s,`]|and|{ANY_ID})+)")
MILESTONE_ARGUMENT = re.compile(r"M(\d+)", re.IGNORECASE)
MILESTONE_HEADING = re.compile(r"^### M(\d+)\b")
HUMAN_CHECKS_HEADING = re.compile(r"^## Human checks", re.IGNORECASE)
ANY_HEADING = re.compile(r"^#{1,3} ")
ENTRY_START = re.compile(r"^- \*\*")
WITHDRAWN = "withdrawn"

STATE_TESTED = "tested"
STATE_MANUAL = "manual"
STATE_PLANNED = "planned"
STATE_MISSING = "missing"
STATE_UNKNOWN = "not in the spec"
COVERED_STATES = (STATE_TESTED, STATE_MANUAL)

EXIT_OK = 0
EXIT_NOT_COVERED = 1
EXIT_USAGE = 2


@dataclass(frozen=True)
class Coverage:
    """Holds what the spec, the tests and the plan say about the requirement IDs."""

    spec_ids: list[str]
    tested: set[str]
    manual: set[str]
    planned: set[str]

    def state(self, spec_id: str) -> str:
        """Return the state of one ID: tested, manual, planned, missing or not in the spec."""
        if spec_id not in self.spec_ids:
            return STATE_UNKNOWN
        if spec_id in self.tested:
            return STATE_TESTED
        if spec_id in self.manual:
            return STATE_MANUAL
        if spec_id in self.planned:
            return STATE_PLANNED
        return STATE_MISSING


def read_lines(path: Path) -> list[str]:
    """Return the lines of a UTF-8 file, or no lines when the file does not exist."""
    if not path.is_file():
        return []
    return path.read_text(encoding="utf-8-sig").splitlines()


def unique(ids: list[str]) -> list[str]:
    """Return the IDs in their order, without duplicates."""
    return list(dict.fromkeys(ids))


def is_requirement(spec_id: str) -> bool:
    """Tell whether an ID is a requirement: not a scenario, an example or a design decision."""
    return spec_id.split("-")[0] not in OTHER_PREFIXES


def requirement_ids(text: str) -> list[str]:
    """Return the requirement IDs that a text names, in their order, without duplicates."""
    return unique([spec_id for spec_id in SPEC_ID.findall(text) if is_requirement(spec_id)])


def spec_ids_of(spec_lines: list[str]) -> list[str]:
    """Return the ID of each requirement row of the spec, without withdrawn rows."""
    ids = []
    for line in spec_lines:
        match = SPEC_ROW.match(line)
        cells = [cell.strip().lower() for cell in line.split("|")]
        if match is not None and is_requirement(match[1]) and WITHDRAWN not in cells:
            ids.append(match[1])
    return unique(ids)


def test_names_in(tests_dir: Path) -> list[str]:
    """Return the name of every Python test function and the title of every web test."""
    names: list[str] = []
    if not tests_dir.is_dir():
        return names
    for path in sorted(tests_dir.rglob(PYTHON_TESTS)):
        names.extend(PYTHON_TEST_NAME.findall(path.read_text(encoding="utf-8-sig")))
    for pattern in WEB_TESTS:
        for path in sorted(tests_dir.rglob(pattern)):
            titles = WEB_TEST_NAME.findall(path.read_text(encoding="utf-8-sig"))
            names.extend(title for _, title in titles)
    return names


def name_has_id(name: str, spec_id: str) -> bool:
    """Tell whether a test name carries the ID: PAY-001 is `pay_001`, and FR-001 is not `nfr_001`.

    The name is compared in lower case with every other character as `_`, so `test_pay_001_x` and
    the title "PAY-001: x" both carry PAY-001.
    """
    token = spec_id.lower().replace("-", "_")
    plain = re.sub(r"[^a-z0-9]", "_", name.lower())
    return re.search(rf"(?<![a-z0-9]){token}(?![0-9])", plain) is not None


def tested_ids(spec_ids: list[str], test_names: list[str]) -> set[str]:
    """Return the requirement IDs that at least one test name carries."""
    return {
        spec_id for spec_id in spec_ids if any(name_has_id(name, spec_id) for name in test_names)
    }


def milestone_blocks(plan_lines: list[str]) -> dict[int, list[str]]:
    """Return the lines of each `### M<n>` block of the plan, by milestone number."""
    blocks: dict[int, list[str]] = {}
    current: list[str] | None = None
    for line in plan_lines:
        if ANY_HEADING.match(line):
            match = MILESTONE_HEADING.match(line)
            current = blocks.setdefault(int(match[1]), []) if match is not None else None
        if current is not None:
            current.append(line)
    return blocks


def entry_text(block: list[str], label: str) -> str:
    """Return the text of the `- **<label>:**` entry of a block, with its continuation lines."""
    start = f"- **{label}:**"
    lines: list[str] = []
    for line in block:
        if line.startswith(start):
            lines = [line]
        elif lines and (ENTRY_START.match(line) or not line.strip()):
            break
        elif lines:
            lines.append(line)
    return " ".join(lines)


def refs_ids(block: list[str]) -> list[str]:
    """Return the requirement IDs in the Refs entry of a milestone block."""
    return requirement_ids(entry_text(block, "Refs"))


def manual_ids(block: list[str]) -> list[str]:
    """Return the requirement IDs that the `Manual:` parts of the Tests first entry name."""
    parts = MANUAL_ENTRY.findall(entry_text(block, "Tests first"))
    return requirement_ids(" ".join(parts))


def human_check_ids(plan_lines: list[str]) -> list[str]:
    """Return the requirement IDs in the section "Human checks" of the plan."""
    lines: list[str] = []
    inside = False
    for line in plan_lines:
        if ANY_HEADING.match(line):
            inside = HUMAN_CHECKS_HEADING.match(line) is not None
        elif inside:
            lines.append(line)
    return requirement_ids(" ".join(lines))


def read_coverage(root: Path, blocks: dict[int, list[str]], plan_lines: list[str]) -> Coverage:
    """Read the spec and the tests under root, and join them with the plan's blocks."""
    spec_ids = spec_ids_of(read_lines(root / SPEC_PATH))
    manual = set(human_check_ids(plan_lines))
    planned: set[str] = set()
    for block in blocks.values():
        manual.update(manual_ids(block))
        planned.update(refs_ids(block))
    tested = tested_ids(spec_ids, test_names_in(root / TESTS_DIR))
    return Coverage(spec_ids, tested, manual, planned)


def list_all(coverage: Coverage) -> int:
    """Log every requirement ID with its state, then the count of each state. It always passes."""
    counts: dict[str, int] = {}
    for spec_id in coverage.spec_ids:
        state = coverage.state(spec_id)
        counts[state] = counts.get(state, 0) + 1
        logger.info("%-9s %s", spec_id, state)
    summary = ", ".join(f"{count} {state}" for state, count in sorted(counts.items()))
    logger.info("%d requirement IDs: %s.", len(coverage.spec_ids), summary or "none")
    return EXIT_OK


def check_milestone(coverage: Coverage, milestone_id: int, block: list[str]) -> int:
    """Log the state of each requirement ID in the block's Refs; fail when one is not covered."""
    ids = refs_ids(block)
    failed = []
    for spec_id in ids:
        state = coverage.state(spec_id)
        logger.info("%-9s %s", spec_id, state)
        if state not in COVERED_STATES:
            failed.append(spec_id)
    if failed:
        logger.error("M%d: no test and no Manual entry for %s.", milestone_id, ", ".join(failed))
        return EXIT_NOT_COVERED
    logger.info("M%d: %d requirement ID(s) in Refs, all tested or manual.", milestone_id, len(ids))
    return EXIT_OK


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    """Read the command line: an optional milestone (M<n>) and an optional root folder."""
    parser = argparse.ArgumentParser(
        description="List which requirement IDs have a test, or check those of one milestone."
    )
    parser.add_argument(
        "milestone", nargs="?", help="check only the Refs of this milestone, for example M3"
    )
    parser.add_argument(
        "--root", type=Path, default=ROOT, help="the folder that holds docs/ and tests/"
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """List every requirement ID, or check one milestone. Return the exit code."""
    arguments = parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)
    root = arguments.root.resolve()
    if not (root / SPEC_PATH).is_file():
        logger.error("%s is missing in %s.", SPEC_PATH.as_posix(), root)
        return EXIT_USAGE
    plan_lines = read_lines(root / PLAN_PATH)
    blocks = milestone_blocks(plan_lines)
    coverage = read_coverage(root, blocks, plan_lines)
    if arguments.milestone is None:
        return list_all(coverage)
    match = MILESTONE_ARGUMENT.fullmatch(arguments.milestone)
    if match is None or int(match[1]) not in blocks:
        logger.error("No block '### %s' in %s.", arguments.milestone, PLAN_PATH.as_posix())
        return EXIT_USAGE
    return check_milestone(coverage, int(match[1]), blocks[int(match[1])])


if __name__ == "__main__":
    sys.exit(main())
