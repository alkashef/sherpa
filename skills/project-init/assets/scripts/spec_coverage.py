"""List which requirement IDs and acceptance examples have a test, and check the documents.

A requirement ID (AREA-NNN, such as PAY-001, or NFR-NNN) is the first cell of a table row of
docs/spec.md. An acceptance example (EX-NNN) is also a row of docs/spec.md. Its second cell cites
its requirement IDs. Scenarios (SCN-NNN), acceptance examples and design decisions (DEC-NNN) are
not requirements. A row with a cell `Withdrawn` is skipped. Each requirement ID and each
acceptance example has one state:

- tested: a test under tests/ has the ID in its name. PAY-001 is `test_pay_001_...` in a
  `test_*.py` file, or a title such as `test("PAY-001 ...")` in a `*.test.js` file. EX-003 is
  `test_pay_001_ex_003_...`, or a title such as `test("PAY-001 EX-003 ...")`.
- manual: a `Manual:` entry of a milestone block, or the section "Human checks" of docs/plan.md,
  names the ID.
- planned: the Refs of a milestone block in docs/plan.md name the requirement ID. An acceptance
  example is planned when the Refs name a requirement ID that it cites.
- missing: none of these.

The script has three modes. It only reads files.

- Without an argument, it lists every requirement ID and every acceptance example with its state.
- With `M<n>`, it checks the requirement IDs in the Refs of that milestone's block. Each must be
  in the spec, and be tested or manual (docs/workflow.md, Execute). Each acceptance example that
  cites one of these requirement IDs must also be tested or manual.
- With `--consistency`, it compares docs/spec.md, docs/design.md and docs/plan.md. It prints each
  problem on its own line, and exits with 1 when it finds one. It checks an ID only in the places
  below, so a text such as "SHA-256" in the design is not an ID. The problems:
  - One of the three files is missing. The other checks then do not run.
  - The Refs entry of a milestone block names a requirement ID that is not a row of the spec.
  - The first cell of a row of the design's table "Test design" names such a requirement ID.
  - The Refs entry of a milestone block names a design decision that is not a row of the design.
  - The Tests first entry of a milestone block names an acceptance example (as `EX-003`, also in
    a `Manual:` part) that is not a row of the spec. An example ID in a test name does not count.
  - A requirement ID of the spec has no test level. The table in the design's section "Test
    design" gives the level. The first cell of a row names the requirement IDs, and the second
    cell names `unit`, `e2e`, `ui` or `live`. A withdrawn requirement needs no level.

  For these checks, a withdrawn row of the spec is still a row.

Run:
    python scripts/spec_coverage.py [M<n> | --consistency] [--root FOLDER]
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
DESIGN_PATH = Path("docs") / "design.md"
PLAN_PATH = Path("docs") / "plan.md"
TESTS_DIR = "tests"
PYTHON_TESTS = "test_*.py"
WEB_TESTS = ("*.test.js", "*.test.mjs", "*.test.ts")

# The IDs of docs/spec.md and docs/design.md that are not requirements: scenarios, acceptance
# examples and design decisions. Every other ID that starts a table row of the spec is one.
EXAMPLE_PREFIX = "EX"
DECISION_PREFIX = "DEC"
OTHER_PREFIXES = ("SCN", EXAMPLE_PREFIX, DECISION_PREFIX)
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

# The design's section "5. Test design" ends at the next heading of its level. Its table gives each
# requirement a test level, in the second cell of a row.
TEST_DESIGN_HEADING = re.compile(r"^## (?:\d+\.\s*)?Test design", re.IGNORECASE)
SECTION_HEADING = re.compile(r"^#{1,2} ")
TEST_LEVEL = re.compile(r"\b(?:unit|e2e|ui|live)\b", re.IGNORECASE)

# What a named ID must be. Each text ends the message of a consistency problem.
REQUIREMENT_ROW = "a requirement row of docs/spec.md"
EXAMPLE_ROW = "an acceptance example row of docs/spec.md"
DECISION_ROW = "a decision row of docs/design.md"

STATE_TESTED = "tested"
STATE_MANUAL = "manual"
STATE_PLANNED = "planned"
STATE_MISSING = "missing"
STATE_UNKNOWN = "not in the spec"
COVERED_STATES = (STATE_TESTED, STATE_MANUAL)

EXIT_OK = 0
EXIT_NOT_COVERED = 1
EXIT_INCONSISTENT = 1
EXIT_USAGE = 2


@dataclass(frozen=True)
class Coverage:
    """Holds what the spec, the tests and the plan say about the requirements and the examples.

    Attributes:
        spec_ids: The requirement IDs of the spec, without withdrawn rows.
        examples: The requirement IDs that each acceptance example cites, by example ID.
        tested: The requirement and example IDs that a test name carries.
        manual: The IDs that a `Manual:` entry or the section "Human checks" names.
        planned: The requirement IDs in the Refs of the plan, and the examples that cite one.
    """

    spec_ids: list[str]
    examples: dict[str, list[str]]
    tested: set[str]
    manual: set[str]
    planned: set[str]

    def state(self, spec_id: str) -> str:
        """Return the state of one ID: tested, manual, planned, missing or not in the spec."""
        if spec_id not in self.spec_ids and spec_id not in self.examples:
            return STATE_UNKNOWN
        if spec_id in self.tested:
            return STATE_TESTED
        if spec_id in self.manual:
            return STATE_MANUAL
        if spec_id in self.planned:
            return STATE_PLANNED
        return STATE_MISSING

    def examples_citing(self, requirements: list[str]) -> list[str]:
        """Return the acceptance examples that cite at least one of the requirement IDs."""
        return [
            example for example, cited in self.examples.items() if set(cited) & set(requirements)
        ]


def read_lines(path: Path) -> list[str]:
    """Return the lines of a UTF-8 file, or no lines when the file does not exist."""
    if not path.is_file():
        return []
    return path.read_text(encoding="utf-8-sig").splitlines()


def unique(ids: list[str]) -> list[str]:
    """Return the IDs in their order, without duplicates."""
    return list(dict.fromkeys(ids))


def prefix_of(spec_id: str) -> str:
    """Return the part of an ID before its number: PAY for PAY-001."""
    return spec_id.split("-")[0]


def is_requirement(spec_id: str) -> bool:
    """Tell whether an ID is a requirement: not a scenario, an example or a design decision."""
    return prefix_of(spec_id) not in OTHER_PREFIXES


def named_ids(text: str) -> list[str]:
    """Return every ID that a text names, in their order, without duplicates."""
    return unique(SPEC_ID.findall(text))


def requirement_ids(text: str) -> list[str]:
    """Return the requirement IDs that a text names, in their order, without duplicates."""
    return [spec_id for spec_id in named_ids(text) if is_requirement(spec_id)]


def ids_with_prefix(text: str, prefix: str) -> list[str]:
    """Return the IDs with one prefix, such as EX or DEC, that a text names."""
    return [spec_id for spec_id in named_ids(text) if prefix_of(spec_id) == prefix]


def cells_of(line: str) -> list[str]:
    """Return the cells of a table row that starts with `|`."""
    return [cell.strip() for cell in line.split("|")[1:]]


def id_rows(lines: list[str]) -> list[list[str]]:
    """Return the cells of each table row whose first cell is an ID."""
    return [cells_of(line) for line in lines if SPEC_ROW.match(line)]


def is_withdrawn(cells: list[str]) -> bool:
    """Tell whether one cell of a table row is `Withdrawn`."""
    return WITHDRAWN in [cell.lower() for cell in cells]


def spec_ids_of(spec_lines: list[str]) -> list[str]:
    """Return the ID of each requirement row of the spec, without withdrawn rows."""
    rows = [cells for cells in id_rows(spec_lines) if not is_withdrawn(cells)]
    return unique([cells[0] for cells in rows if is_requirement(cells[0])])


def examples_of(spec_lines: list[str]) -> dict[str, list[str]]:
    """Return the requirement IDs that each acceptance example of the spec cites, by example ID.

    An acceptance example is a table row whose first cell is an EX ID. Its second cell holds the
    requirement IDs. A withdrawn row is skipped.
    """
    rows = [cells for cells in id_rows(spec_lines) if not is_withdrawn(cells)]
    return {
        cells[0]: requirement_ids(cells[1])
        for cells in rows
        if prefix_of(cells[0]) == EXAMPLE_PREFIX
    }


def section_lines(lines: list[str], start: re.Pattern[str], end: re.Pattern[str]) -> list[str]:
    """Return the lines below each heading that matches start, up to the next end heading."""
    section: list[str] = []
    inside = False
    for line in lines:
        if end.match(line):
            inside = start.match(line) is not None
        elif inside:
            section.append(line)
    return section


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
    """Return the IDs, of requirements or examples, that at least one test name carries."""
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
    """Return the IDs that the `Manual:` parts of the Tests first entry name."""
    parts = MANUAL_ENTRY.findall(entry_text(block, "Tests first"))
    return named_ids(" ".join(parts))


def human_check_ids(plan_lines: list[str]) -> list[str]:
    """Return the IDs that the section "Human checks" of the plan names."""
    lines = section_lines(plan_lines, HUMAN_CHECKS_HEADING, ANY_HEADING)
    return named_ids(" ".join(lines))


def read_coverage(root: Path, blocks: dict[int, list[str]], plan_lines: list[str]) -> Coverage:
    """Read the spec and the tests under root, and join them with the plan's blocks."""
    spec_lines = read_lines(root / SPEC_PATH)
    spec_ids = spec_ids_of(spec_lines)
    examples = examples_of(spec_lines)
    manual = set(human_check_ids(plan_lines))
    planned: set[str] = set()
    for block in blocks.values():
        manual.update(manual_ids(block))
        planned.update(refs_ids(block))
    planned.update([example for example, cited in examples.items() if planned & set(cited)])
    tested = tested_ids([*spec_ids, *examples], test_names_in(root / TESTS_DIR))
    return Coverage(spec_ids, examples, tested, manual, planned)


def list_states(coverage: Coverage, ids: list[str], label: str) -> None:
    """Log each ID with its state, then the count of each state under the label."""
    counts: dict[str, int] = {}
    for spec_id in ids:
        state = coverage.state(spec_id)
        counts[state] = counts.get(state, 0) + 1
        logger.info("%-9s %s", spec_id, state)
    summary = ", ".join(f"{count} {state}" for state, count in sorted(counts.items()))
    logger.info("%d %s: %s.", len(ids), label, summary or "none")


def list_all(coverage: Coverage) -> int:
    """Log every requirement ID, then every acceptance example, with its state. It always passes."""
    list_states(coverage, coverage.spec_ids, "requirement IDs")
    list_states(coverage, list(coverage.examples), "acceptance examples")
    return EXIT_OK


def check_milestone(coverage: Coverage, milestone_id: int, block: list[str]) -> int:
    """Log the state of each requirement ID in the block's Refs, and of each example that cites one.

    Returns:
        The exit code: 1 when a requirement ID or an example is not tested and not manual.
    """
    ids = refs_ids(block)
    examples = coverage.examples_citing(ids)
    failed = []
    for spec_id in [*ids, *examples]:
        state = coverage.state(spec_id)
        logger.info("%-9s %s", spec_id, state)
        if state not in COVERED_STATES:
            failed.append(spec_id)
    if failed:
        logger.error("M%d: no test and no Manual entry for %s.", milestone_id, ", ".join(failed))
        return EXIT_NOT_COVERED
    logger.info("M%d: %d requirement ID(s) in Refs, all tested or manual.", milestone_id, len(ids))
    logger.info(
        "M%d: %d acceptance example(s) cite them, all tested or manual.",
        milestone_id,
        len(examples),
    )
    return EXIT_OK


def missing_files(root: Path) -> list[str]:
    """Return a problem for each of the spec, the design and the plan that root does not hold."""
    paths = (SPEC_PATH, DESIGN_PATH, PLAN_PATH)
    return [
        f"{path.as_posix()} is missing in {root}." for path in paths if not (root / path).is_file()
    ]


def unknown_names(source: Path, named: list[str], rows: list[str], kind: str) -> list[str]:
    """Return a problem for each named ID that is not the ID of a row.

    Args:
        source: The file that names the IDs.
        named: The IDs that the file names.
        rows: The ID of each table row that a named ID can be.
        kind: What a named ID must be, for the message.
    """
    return [
        f"{source.as_posix()} names {name}, which is not {kind}."
        for name in named
        if name not in rows
    ]


def entry_texts(blocks: dict[int, list[str]], label: str) -> str:
    """Return the text of the `- **<label>:**` entry of every milestone block, as one text."""
    return " ".join(entry_text(block, label) for block in blocks.values())


def plan_problems(
    blocks: dict[int, list[str]], spec_rows: list[str], design_rows: list[str]
) -> list[str]:
    """Return a problem for each ID in a fixed place of the plan that is not the ID of a row.

    The Refs entry of a block names requirement IDs and design decisions. Its Tests first entry
    names acceptance examples, as IDs such as EX-003. An example ID in a test name does not count.

    Args:
        blocks: The lines of each milestone block of the plan.
        spec_rows: The ID of each table row of the spec.
        design_rows: The ID of each table row of the design.
    """
    requirements = unique([spec_id for block in blocks.values() for spec_id in refs_ids(block)])
    examples = ids_with_prefix(entry_texts(blocks, "Tests first"), EXAMPLE_PREFIX)
    decisions = ids_with_prefix(entry_texts(blocks, "Refs"), DECISION_PREFIX)
    problems = unknown_names(PLAN_PATH, requirements, spec_rows, REQUIREMENT_ROW)
    problems += unknown_names(PLAN_PATH, examples, spec_rows, EXAMPLE_ROW)
    return problems + unknown_names(PLAN_PATH, decisions, design_rows, DECISION_ROW)


def level_rows(design_lines: list[str]) -> list[list[str]]:
    """Return the cells of each table row in the design's section "Test design"."""
    section = section_lines(design_lines, TEST_DESIGN_HEADING, SECTION_HEADING)
    return [cells_of(line) for line in section if line.startswith("|")]


def design_problems(levels: list[list[str]], spec_rows: list[str]) -> list[str]:
    """Return a problem for each requirement ID of the Test design table that the spec lacks.

    Args:
        levels: The cells of each row of the Test design table. The first cell names the IDs.
        spec_rows: The ID of each table row of the spec.
    """
    named = requirement_ids(" ".join(cells[0] for cells in levels))
    return unknown_names(DESIGN_PATH, named, spec_rows, REQUIREMENT_ROW)


def leveled_ids(levels: list[list[str]]) -> set[str]:
    """Return the requirement IDs that a row of the Test design table gives a level."""
    ids: set[str] = set()
    for cells in levels:
        if len(cells) > 1 and TEST_LEVEL.search(cells[1]):
            ids.update(requirement_ids(cells[0]))
    return ids


def level_problems(spec_ids: list[str], levels: list[list[str]]) -> list[str]:
    """Return a problem for each requirement ID of the spec that has no test level in the design."""
    leveled = leveled_ids(levels)
    return [
        f"{spec_id} has no test level (unit, e2e, ui or live) in the Test design table "
        f"of {DESIGN_PATH.as_posix()}."
        for spec_id in spec_ids
        if spec_id not in leveled
    ]


def consistency_problems(root: Path) -> list[str]:
    """Return each problem between the spec, the design and the plan under root.

    A missing file is the only problem that it returns, because the other checks need all three.
    """
    missing = missing_files(root)
    if missing:
        return missing
    spec_lines = read_lines(root / SPEC_PATH)
    design_lines = read_lines(root / DESIGN_PATH)
    blocks = milestone_blocks(read_lines(root / PLAN_PATH))
    spec_rows = [cells[0] for cells in id_rows(spec_lines)]
    design_rows = [cells[0] for cells in id_rows(design_lines)]
    levels = level_rows(design_lines)
    problems = design_problems(levels, spec_rows)
    problems += plan_problems(blocks, spec_rows, design_rows)
    return problems + level_problems(spec_ids_of(spec_lines), levels)


def check_consistency(root: Path) -> int:
    """Log each problem between the spec, the design and the plan. Fail when there is one."""
    problems = consistency_problems(root)
    for problem in problems:
        logger.error("%s", problem)
    if problems:
        return EXIT_INCONSISTENT
    logger.info("The spec, the design and the plan are consistent.")
    return EXIT_OK


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    """Read the command line: a milestone (M<n>) or --consistency, and an optional root folder."""
    parser = argparse.ArgumentParser(
        description=(
            "List which requirement IDs and acceptance examples have a test, check those of one "
            "milestone, or compare the spec, the design and the plan."
        )
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "milestone", nargs="?", help="check only the Refs of this milestone, for example M3"
    )
    mode.add_argument(
        "--consistency",
        action="store_true",
        help="check that the IDs of the spec, the design and the plan agree",
    )
    parser.add_argument(
        "--root", type=Path, default=ROOT, help="the folder that holds docs/ and tests/"
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """List every ID, check one milestone, or compare the documents. Return the exit code."""
    arguments = parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)
    root = arguments.root.resolve()
    if arguments.consistency:
        return check_consistency(root)
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
