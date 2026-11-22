"""A stand-in for `claude -p`, used by the milestone runner tests. It never calls a model.

`claude.cmd` (written by the tests, first on PATH) runs this file, and so can `codex.cmd`,
`agy.cmd` and `copilot.cmd`: the fake also plays the other test writers. It reads the runner's
prompt on stdin, or after `-p` when that is not an option, finds the session (test, test-fix,
build, review, repair, review-tests or rebuild), the milestone number and the title, and acts by
FAKE_CLAUDE_STATE. It answers the start check of a test writer with `ok`. No session pushes. A
test session works in the folder of the test writer, which has no git.

    (unset)          the test session writes a failing test of the milestone and commits nothing;
                     the build session writes the code, deletes the milestone's row and block
                     from docs/plan.md and commits everything; the review session reports
                     `NO FINDINGS` and changes nothing
    "blocked"        the test session blocks the milestone, unless its block has an Approval
                     entry: it sets its Status to `blocked`, adds a Blocked entry to its block,
                     and commits nothing
    "blocked-build"  the build session writes the code, then blocks the milestone in the same way
    "idle"           does nothing
    "bad-test"       the test session writes a test that imports a test helper that does not
                     exist;
                     the test-fix session writes the right test
    "bad-test-stays" as "bad-test", but the test-fix session does nothing
    "review-tests"   the first review reports a finding about the test of the milestone; the
                     review-tests session adds a second test; the rebuild session commits
                     `M<n>: test repairs`; a later review reports no finding
    "blocking"       each review reports one high finding about the code; the repair session
                     changes the code and commits `M<n>: review repairs`
    "retry"          the first build session of a milestone does nothing; a later one finishes it
    "tamper"         the build session also changes the test that the test session wrote
    "spec"           the build session also changes docs/spec.md
    "no-remote"      the build session also points `origin` at a folder that does not exist, so
                     a later push fails
    "wanders"        the build session also checks out `main` when its commit is made
    "findings"       the first review of a milestone reports two findings; the repair session
                     changes the code and commits `M<n>: review repairs`; a later review reports
                     one finding
    "rejected"       each review reports two findings; the repair session rejects them and
                     commits nothing
    "repair-tamper"  as "findings", but the repair session also changes the test
    "review-edits"   the review session changes a file of the code (in its worktree)
    "review-error"   the review session ends with exit code 1

Every call's arguments are appended to FAKE_CLAUDE_LOG, one JSON list per line. The kind, the
milestone number and the prompt of every call are appended to `claude-sessions.jsonl` in the
folder of that log, one JSON object per line.
"""

import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

PLAN = Path("docs/plan.md")
SPEC = Path("docs/spec.md")
QUESTION = "- **Blocked:** Needs a decision: which database?"
SESSIONS_LOG = "claude-sessions.jsonl"
PROMPTS = {
    "test": r"(?:Run /write-tests for|Write the failing tests of) milestone M(\d+) \((.*?)\) of",
    "test-fix": r"The runner checked the tests of milestone M(\d+) \((.*?)\) that you wrote",
    "build": r"Implement only milestone M(\d+) \((.*?)\) from docs/plan\.md",
    "review": r"Review milestone M(\d+) \((.*?)\): the diff",
    "repair": r"Repair the findings of the review of milestone M(\d+) \((.*?)\)\.",
    "review-tests": r"Repair the review findings about the tests of milestone M(\d+) \((.*?)\)\.",
    "rebuild": r"The tests of milestone M(\d+) \((.*?)\) changed after the review",
}
START_CHECK = "Reply with the single word ok."
TEST_FINDING = "FINDING: medium | tests/unit/test_m<n>.py:4 | Weak Test | Also check the type."
HIGH_FINDING = "FINDING: high | src/m<n>.py:7 | Error Handling | Raise on a bad value."
FINDINGS = (
    "FINDING: medium | src/m<n>.py:1 | Comments | Say what the module is for.",
    "FINDING: low | src/m<n>.py:5 | Dead Code | Delete the name that nothing uses.",
)
REPAIR_STATES = ("findings", "repair-tamper", "blocking")  # the repair session commits a repair


@dataclass(frozen=True)
class Call:
    """One call of the fake: the state the test set, and the session the prompt names.

    earlier counts the sessions of this kind that this milestone had before this call.
    """

    state: str
    kind: str
    number: int
    title: str
    earlier: int
    prompt: str


def log_path() -> Path:
    """Return the file that keeps the arguments of every call."""
    return Path(os.environ["FAKE_CLAUDE_LOG"])


def sessions_path() -> Path:
    """Return the file that keeps the kind, the milestone and the prompt of every call."""
    return log_path().with_name(SESSIONS_LOG)


def earlier_sessions(kind: str, number: int) -> int:
    """Return how many sessions of this kind were logged for the milestone before this call."""
    if not sessions_path().exists():
        return 0
    lines = sessions_path().read_text("utf-8").splitlines()
    sessions = [json.loads(line) for line in lines]
    return sum(s["kind"] == kind and s["milestone"] == number for s in sessions)


def log_call(args: list[str]) -> None:
    """Append the arguments of this call to the log file."""
    with log_path().open("a", encoding="utf-8") as log:
        log.write(json.dumps(args) + "\n")


def log_session(call: Call) -> None:
    """Append the kind, the milestone, the prompt and the folder of this call to the sessions file.

    The folder facts show where the session ran: its path, and whether it holds src/, .git and
    AGENTS.md.
    """
    here = Path.cwd()
    record = {
        "kind": call.kind,
        "milestone": call.number,
        "prompt": call.prompt,
        "folder": str(here),
        "src": (here / "src").exists(),
        "git": (here / ".git").exists(),
        "agents": (here / "AGENTS.md").exists(),
    }
    with sessions_path().open("a", encoding="utf-8") as log:
        log.write(json.dumps(record) + "\n")


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
    return subprocess.run([shutil.which("git") or "git", *args], check=False).returncode


def commit(message: str) -> int:
    """Stage every change and commit it with the message. Nothing is pushed."""
    for args in (["add", "-A"], ["commit", "-m", message]):
        code = git(*args)
        if code != 0:
            return code
    return 0


def waits_for_approval(call: Call, blocking_state: str) -> bool:
    """Tell whether this session blocks its milestone: the state says so, and no Approval exists."""
    return call.state == blocking_state and "**Approval:**" not in PLAN.read_text("utf-8")


def block(number: int) -> int:
    """Block the milestone: write the question into the plan, and commit nothing."""
    PLAN.write_text(with_question(PLAN.read_text("utf-8"), number), encoding="utf-8")
    return 0


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


def write_bad_test(number: int) -> None:
    """Write a test that imports a test helper that does not exist: a fault of the test itself."""
    text = (
        f"from tests.unit.helpers_m{number} import expected_value\n\n\n"
        f"def test_m{number}_value() -> None:\n    assert expected_value() == {number}\n"
    )
    test_path(number).write_text(text, encoding="utf-8")


def add_second_test(number: int) -> None:
    """Add a second test of src/m<n>.py to the test file of the milestone."""
    with test_path(number).open("a", encoding="utf-8") as test:
        test.write(f"\n\ndef test_m{number}_value_is_an_int() -> None:\n")
        test.write("    assert isinstance(value(), int)\n")


def weaken_test(number: int) -> None:
    """Change the test of a milestone, as a session that may not do so."""
    weaker = test_path(number).read_text("utf-8").replace("==", ">=")
    test_path(number).write_text(weaker, encoding="utf-8")


def write_code(number: int, note: str = "") -> None:
    """Write src/m<n>.py so that the milestone's test passes; the note goes into its docstring."""
    Path("src/__init__.py").write_text('"""Source."""\n', encoding="utf-8")
    text = (
        f'"""Milestone {number}{note}."""\n\n\n'
        f'def value() -> int:\n    """Return the milestone number."""\n    return {number}\n'
    )
    Path(f"src/m{number}.py").write_text(text, encoding="utf-8")


def act_test(call: Call) -> int:
    """Do the test session: block the milestone, or write its failing test. Commit nothing."""
    if waits_for_approval(call, "blocked"):
        return block(call.number)
    if call.state in ("bad-test", "bad-test-stays"):
        write_bad_test(call.number)
    else:
        write_test(call.number)
    return 0


def act_test_fix(call: Call) -> int:
    """Do the round of repair of a test session: write the right test, or nothing."""
    if call.state == "bad-test":
        write_test(call.number)
    return 0


def act_review_tests(call: Call) -> int:
    """Do the test session for the review findings about the tests: add a second test."""
    add_second_test(call.number)
    sys.stdout.write(f"REPAIRED: {TEST_FINDING.replace('<n>', str(call.number))}\n")
    return 0


def act_rebuild(call: Call) -> int:
    """Do the build session after the review-tests session: commit the changed tests."""
    return commit(f"M{call.number}: test repairs")


def break_rule(call: Call) -> None:
    """Do what the state adds to a build session, before its commit."""
    if call.state == "tamper":
        weaken_test(call.number)
    if call.state == "spec":
        SPEC.write_text(SPEC.read_text("utf-8") + "\nA new requirement.\n", encoding="utf-8")
    if call.state == "no-remote":
        git("remote", "set-url", "origin", str(Path.cwd().parent / "no-remote.git"))


def act_build(call: Call) -> int:
    """Do the build session: the code, the plan, and what the state adds; commit, do not push."""
    number = call.number
    if call.state == "retry" and call.earlier == 0:
        return 0
    write_code(number)
    if waits_for_approval(call, "blocked-build"):
        return block(number)
    break_rule(call)
    PLAN.write_text(without_milestone(PLAN.read_text("utf-8"), number), encoding="utf-8")
    code = commit(f"M{number}: {call.title}")
    if call.state == "wanders":
        git("checkout", "main")
    sys.stdout.write("DECISION: keep the value in a function | the simplest way | none\n")
    sys.stdout.write(f"- **TLDR: M{number} is done.**\n")
    return code


def reported_findings(call: Call) -> list[str]:
    """Return the FINDING lines that this review reports, by the state and the earlier reviews."""
    findings = [line.replace("<n>", str(call.number)) for line in FINDINGS]
    if call.state == "rejected":
        return findings
    if call.state == "review-tests":
        return [TEST_FINDING.replace("<n>", str(call.number))] if call.earlier == 0 else []
    if call.state == "blocking":
        return [HIGH_FINDING.replace("<n>", str(call.number))]
    if call.state in REPAIR_STATES:
        return findings if call.earlier == 0 else findings[:1]
    return []


def act_review(call: Call) -> int:
    """Do the review session: report the findings of the state; change a file only if it says so."""
    sys.stdout.write("BUILT-IN REVIEW: not available\n")
    if call.state == "review-error":
        return 1
    if call.state == "review-edits":
        with Path(f"src/m{call.number}.py").open("a", encoding="utf-8") as code:
            code.write("# reviewed\n")
    findings = reported_findings(call)
    sys.stdout.write("\n".join(findings or ["NO FINDINGS"]) + "\n")
    return 0


def act_repair(call: Call) -> int:
    """Do the repair session: reject every finding, or change the code and commit the repair."""
    if call.state not in REPAIR_STATES:
        for finding in re.findall(r"^FINDING:.*$", call.prompt, re.MULTILINE):
            sys.stdout.write(f"REJECTED: {finding} | the code is right\n")
        return 0
    write_code(call.number, note=", after the review")
    if call.state == "repair-tamper":
        weaken_test(call.number)
    return commit(f"M{call.number}: review repairs")


ACTIONS = {
    "test": act_test,
    "test-fix": act_test_fix,
    "build": act_build,
    "review": act_review,
    "repair": act_repair,
    "review-tests": act_review_tests,
    "rebuild": act_rebuild,
}


def read_prompt(args: list[str]) -> str:
    """Return the prompt: the argument after `-p` when it is not an option, else stdin."""
    if "-p" in args:
        index = args.index("-p") + 1
        if index < len(args) and not args[index].startswith("-"):
            return args[index].replace("\r\n", "\n")
    return sys.stdin.buffer.read().decode("utf-8", "replace").replace("\r\n", "\n")


def read_call(prompt: str) -> Call | None:
    """Return the session that the prompt names, or None when it names none."""
    state = os.environ.get("FAKE_CLAUDE_STATE", "")
    for kind, pattern in PROMPTS.items():
        match = re.search(pattern, prompt)
        if match is not None:
            number = int(match[1])
            return Call(state, kind, number, match[2], earlier_sessions(kind, number), prompt)
    return None


def main() -> int:
    """Log the call, then act on the session and the milestone named in the prompt."""
    log_call(sys.argv[1:])
    prompt = read_prompt(sys.argv[1:])
    if START_CHECK in prompt:
        sys.stdout.write("ok\n")
        return 0
    call = read_call(prompt)
    if call is None:
        sys.stderr.write("fake claude: no milestone in the prompt\n")
        return 1
    log_session(call)
    return 0 if call.state == "idle" else ACTIONS[call.kind](call)


if __name__ == "__main__":
    raise SystemExit(main())
