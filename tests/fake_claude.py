"""A stand-in for `claude -p`, used by the milestone runner tests. It never calls a model.

`claude.cmd` (written by the tests, first on PATH) runs this file. It reads the runner's prompt on
stdin, finds the session (test or build), the milestone number and the title, and acts by
FAKE_CLAUDE_STATE:

    (unset)    the test session writes a failing test of the milestone and commits nothing; the
               build session writes the code, deletes the milestone's row and block from
               docs/plan.md, commits everything, and pushes
    "blocked"  blocks it, unless its block has an Approval entry: sets its Status to `blocked`,
               adds a Blocked entry to its block, commits docs/plan.md alone, and pushes
    "idle"     does nothing
    "retry"    the first build session does nothing; a later one finishes the milestone
    "tamper"   the build session also changes the test that the test session wrote
    "spec"     the build session also changes docs/spec.md

Every call's arguments are appended to FAKE_CLAUDE_LOG, one JSON list per line.
"""

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

PLAN = Path("docs/plan.md")
SPEC = Path("docs/spec.md")
QUESTION = "- **Blocked:** Needs a decision: which database?"
BUILD_MARK = "Edit(./tests/**)"  # only a build session is denied this tool
TEST_PROMPT = r"Run /write-tests for milestone M(\d+) \((.*?)\) of docs/plan\.md"
BUILD_PROMPT = r"Implement only milestone M(\d+) \((.*?)\) from docs/plan\.md"


def log_path() -> Path:
    """Return the file that keeps the arguments of every call."""
    return Path(os.environ["FAKE_CLAUDE_LOG"])


def earlier_builds() -> int:
    """Return how many build sessions were logged before this call."""
    if not log_path().exists():
        return 0
    return sum(BUILD_MARK in line for line in log_path().read_text("utf-8").splitlines())


def log_call(args: list[str]) -> None:
    """Append the arguments of this call to the log file."""
    with log_path().open("a", encoding="utf-8") as log:
        log.write(json.dumps(args) + "\n")


def without_milestone(plan: str, number: int) -> str:
    """Return the plan without the milestone's table row and its `### M<n>` block."""
    kept: list[str] = []
    in_block = False
    for line in plan.splitlines():
        if line.startswith(("### ", "## ")):
            in_block = line.startswith(f"### M{number} ")
        if not in_block and not line.startswith(f"| **M{number}**"):
            kept.append(line)
    return "\n".join(kept) + "\n"


def with_question(plan: str, number: int) -> str:
    """Return the plan with the milestone's Status set to blocked and a Blocked entry added."""
    lines = plan.splitlines()
    for i, line in enumerate(lines):
        if line.startswith(f"| **M{number}**"):
            lines[i] = re.sub(r"\|\s*\w+\s*\|\s*$", "| blocked |", line)
    heading = next(i for i, line in enumerate(lines) if line.startswith(f"### M{number} "))
    end = next((i for i in range(heading + 1, len(lines)) if lines[i].startswith("#")), len(lines))
    while end > heading and not lines[end - 1].strip():
        end -= 1
    lines.insert(end, QUESTION)
    return "\n".join(lines) + "\n"


def git(*args: str) -> int:
    """Run git and return its exit code."""
    # S603 is ignored on purpose: this fake runs only git, with arguments the test controls.
    return subprocess.run([shutil.which("git") or "git", *args], check=False).returncode  # noqa: S603


def commit(paths: list[str], message: str) -> int:
    """Stage the paths, commit them with the message, and push."""
    for args in (["add", *paths], ["commit", "-m", message], ["push"]):
        code = git(*args)
        if code != 0:
            return code
    return 0


def block(plan: str, number: int) -> int:
    """Block the milestone: write the question into the plan, commit the plan alone, and push."""
    PLAN.write_text(with_question(plan, number), encoding="utf-8")
    return commit([str(PLAN)], f"M{number}: blocked")


def test_path(number: int) -> Path:
    """Return the test file of a milestone."""
    return Path(f"tests/unit/test_m{number}.py")


def write_test(number: int) -> None:
    """Write a test of src/m<n>.py, which does not exist yet, so the test fails."""
    text = (
        f"from src.m{number} import value\n\n\n"
        f"def test_m{number}_value() -> None:\n    assert value() == {number}\n"
    )
    test_path(number).write_text(text, encoding="utf-8")


def write_code(number: int) -> None:
    """Write src/m<n>.py so that the milestone's test passes."""
    Path("src/__init__.py").write_text('"""Source."""\n', encoding="utf-8")
    text = (
        f'"""Milestone {number}."""\n\n\n'
        f'def value() -> int:\n    """Return the milestone number."""\n    return {number}\n'
    )
    Path(f"src/m{number}.py").write_text(text, encoding="utf-8")


def build(state: str, number: int, title: str) -> int:
    """Do the build session: the code, the plan, and what the state adds; commit and push."""
    write_code(number)
    if state == "tamper":
        weaker = test_path(number).read_text("utf-8").replace("==", ">=")
        test_path(number).write_text(weaker, encoding="utf-8")
    if state == "spec":
        SPEC.write_text(SPEC.read_text("utf-8") + "\nA new requirement.\n", encoding="utf-8")
    PLAN.write_text(without_milestone(PLAN.read_text("utf-8"), number), encoding="utf-8")
    code = commit(["-A"], f"M{number}: {title}")
    sys.stdout.write("DECISION: keep the value in a function | the simplest way | none\n")
    sys.stdout.write(f"- **TLDR: M{number} is done.**\n")
    return code


def act(state: str, is_build: bool, milestone: tuple[int, str], builds_before: int) -> int:
    """Block, finish, or skip one session of the milestone, by the state the test set."""
    number, title = milestone
    plan = PLAN.read_text(encoding="utf-8")
    if state == "idle" or (state == "retry" and is_build and builds_before == 0):
        return 0
    if state == "blocked" and "**Approval:**" not in plan:
        return block(plan, number)
    if is_build:
        return build(state, number, title)
    write_test(number)
    return 0


def main() -> int:
    """Log the call, then act on the session and the milestone named in the prompt."""
    builds_before = earlier_builds()
    log_call(sys.argv[1:])
    prompt = sys.stdin.read()
    match = re.search(BUILD_PROMPT, prompt)
    is_build = match is not None
    match = match or re.search(TEST_PROMPT, prompt)
    if match is None:
        sys.stderr.write("fake claude: no milestone in the prompt\n")
        return 1
    state = os.environ.get("FAKE_CLAUDE_STATE", "")
    return act(state, is_build, (int(match[1]), match[2]), builds_before)


if __name__ == "__main__":
    raise SystemExit(main())
