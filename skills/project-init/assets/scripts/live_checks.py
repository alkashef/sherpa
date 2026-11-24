"""Run the live checks: the tests under tests/live/ that call a live external service.

A live check calls a paid API, an LLM or a remote database with a test account. The normal test
runs skip tests/live/, and a milestone gate never runs it. This script runs that folder, and only
with the approval of the user.

The approval is in docs/plan.md, under the heading `## Live checks`:

    - **Approval:** <the user's words>
    - **Budget ceiling:** <amount>

The two entries must exist. An empty entry does not count. An entry that holds a placeholder in
angle brackets does not count. The tests get the ceiling in the environment variable
LIVE_BUDGET_CEILING. They must stop before they pass it.

The Python tests are the `test_*.py` files. pytest runs them, without the coverage floor. The
JavaScript tests are the `*.test.js` files. `node --test` runs them.

The script prints one summary line on standard output, as its last line. The output of a failed
test run goes to standard error. The summary lines and their exit codes:

    0  Live checks: passed.
    1  Live checks: failed.
    3  Live checks: not run (no test in tests/live/).
    3  Live checks: not run (docs/plan.md has no approval with a budget ceiling).

The script itself changes no file: pytest writes no cache, and Python writes no bytecode.

Run:
    python scripts/live_checks.py [--root FOLDER]
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLAN_PATH = Path("docs") / "plan.md"
LIVE_DIR = Path("tests") / "live"
PYTHON_TESTS = "test_*.py"
WEB_TESTS = "*.test.js"
CEILING_VARIABLE = "LIVE_BUDGET_CEILING"

LIVE_HEADING = re.compile(r"^## Live checks\b", re.IGNORECASE)
SECTION_HEADING = re.compile(r"^#{1,2} ")
LIST_ITEM = re.compile(r"^- ")  # the next entry, or a line `- <requirement ID>: <test name>`
PLACEHOLDER = re.compile(r"<[^<>]*>")

EXIT_PASSED = 0
EXIT_FAILED = 1
EXIT_NOT_RUN = 3

PASSED = "Live checks: passed."
FAILED = "Live checks: failed."
NO_TEST = f"Live checks: not run (no test in {LIVE_DIR.as_posix()}/)."
NO_APPROVAL = (
    f"Live checks: not run ({PLAN_PATH.as_posix()} has no approval with a budget ceiling)."
)


def read_lines(path: Path) -> list[str]:
    """Return the lines of a UTF-8 file, or no lines when the file does not exist."""
    if not path.is_file():
        return []
    return path.read_text(encoding="utf-8-sig").splitlines()


def live_section(plan_lines: list[str]) -> list[str]:
    """Return the lines of the plan under the heading `## Live checks`."""
    lines: list[str] = []
    inside = False
    for line in plan_lines:
        if SECTION_HEADING.match(line):
            inside = LIVE_HEADING.match(line) is not None
        elif inside:
            lines.append(line)
    return lines


def entry_value(section: list[str], label: str) -> str:
    """Return the text after `- **<label>:**` in a section, with its continuation lines.

    The entry ends at a blank line or at the next item of the list.
    """
    start = f"- **{label}:**"
    parts: list[str] = []
    for line in section:
        if not parts and line.startswith(start):
            parts = [line[len(start) :]]
        elif parts and (LIST_ITEM.match(line) or not line.strip()):
            break
        elif parts:
            parts.append(line)
    return " ".join(part.strip() for part in parts).strip()


def is_filled(value: str) -> bool:
    """Tell whether an entry has a text, and no placeholder in angle brackets."""
    return bool(value) and PLACEHOLDER.search(value) is None


def budget_ceiling(root: Path) -> str | None:
    """Return the budget ceiling of the plan, or None when the plan has no approval with one."""
    section = live_section(read_lines(root / PLAN_PATH))
    approval = entry_value(section, "Approval")
    ceiling = entry_value(section, "Budget ceiling")
    return ceiling if is_filled(approval) and is_filled(ceiling) else None


def live_tests(root: Path, pattern: str) -> list[str]:
    """Return the live test files whose name matches the pattern, as paths from root."""
    paths = (root / LIVE_DIR).rglob(pattern)
    return sorted(path.relative_to(root).as_posix() for path in paths)


def live_commands(root: Path) -> dict[str, list[str]]:
    """Return the command for each kind of live test that tests/live/ holds, by tool name.

    pytest gets the folder by name, because pytest.ini keeps the normal run out of it. No
    coverage option is given, so the 80% floor does not apply.
    """
    commands: dict[str, list[str]] = {}
    if live_tests(root, PYTHON_TESTS):
        options = ["-q", "-p", "no:cacheprovider"]
        commands["pytest"] = [sys.executable, "-m", "pytest", *options, LIVE_DIR.as_posix()]
    web_tests = live_tests(root, WEB_TESTS)
    if web_tests:
        commands["node --test"] = [shutil.which("node") or "node", "--test", *web_tests]
    return commands


def run(command: list[str], root: Path, ceiling: str) -> tuple[int, str]:
    """Run a command in root, with the budget ceiling. Return its exit code and its output."""
    settings = {"NO_COLOR": "1", "FORCE_COLOR": "0", "PYTHONDONTWRITEBYTECODE": "1"}
    try:
        result = subprocess.run(
            command,
            cwd=root,
            env={**os.environ, **settings, CEILING_VARIABLE: ceiling},
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except OSError as error:
        return EXIT_FAILED, f"`{command[0]}` could not run: {error}"
    return result.returncode, (result.stdout + result.stderr).strip()


def failures_of(commands: dict[str, list[str]], root: Path, ceiling: str) -> list[str]:
    """Run each command. Return the output of each one that failed, under the name of its tool."""
    failures: list[str] = []
    for name, command in commands.items():
        code, output = run(command, root, ceiling)
        if code:
            failures.append(f"`{name}` failed:\n{output}")
    return failures


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    """Read the command line: an optional root folder."""
    parser = argparse.ArgumentParser(description="Run the live checks under tests/live/.")
    parser.add_argument(
        "--root", type=Path, default=ROOT, help="the folder that holds docs/ and tests/"
    )
    return parser.parse_args(argv)


def check(root: Path) -> tuple[int, str]:
    """Run the live checks of root when it has some and an approval. Return code and summary."""
    commands = live_commands(root)
    if not commands:
        return EXIT_NOT_RUN, NO_TEST
    ceiling = budget_ceiling(root)
    if ceiling is None:
        return EXIT_NOT_RUN, NO_APPROVAL
    failures = failures_of(commands, root, ceiling)
    if failures:
        print("\n\n".join(failures), file=sys.stderr, flush=True)
        return EXIT_FAILED, FAILED
    return EXIT_PASSED, PASSED


def main(argv: list[str] | None = None) -> int:
    """Run the live checks, print the summary line last, and return the exit code."""
    code, summary = check(parse_args(argv).root.resolve())
    print(summary)
    return code


if __name__ == "__main__":
    sys.exit(main())
