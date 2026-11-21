"""A stand-in for `claude -p`, used by the milestone runner tests. It never calls a model.

`claude.cmd` (written by the tests, first on PATH) runs this file. It reads the runner's prompt on
stdin, finds the session (test, build, review or repair), the milestone number and the title, and
acts by FAKE_CLAUDE_STATE. No session pushes.

    (unset)          the test session writes a failing test of the milestone and commits nothing;
                     the build session writes the code, deletes the milestone's row and block
                     from docs/plan.md and commits everything; the review session reports
                     `NO FINDINGS` and changes nothing
    "blocked"        the test session blocks the milestone, unless its block has an Approval
                     entry: it sets its Status to `blocked`, adds a Blocked entry to its block,
                     and commits nothing
    "blocked-build"  the build session writes the code, then blocks the milestone in the same way
    "idle"           does nothing
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
    "review-edits"   the review session changes a file of the code
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
    "test": r"Run /write-tests for milestone M(\d+) \((.*?)\) of docs/plan\.md",
    "build": r"Implement only milestone M(\d+) \((.*?)\) from docs/plan\.md",
    "review": r"Review milestone M(\d+) \((.*?)\): the diff",
    "repair": r"Repair the findings of the review of milestone M(\d+) \((.*?)\)\.",
}
FINDINGS = (
    "FINDING: medium | src/m<n>.py:1 | Comments | Say what the module is for.",
    "FINDING: low | src/m<n>.py:5 | Dead Code | Delete the name that nothing uses.",
)
REPAIR_STATES = ("findings", "repair-tamper")  # the repair session commits a repair


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
    """Append the kind, the milestone number and the prompt of this call to the sessions file."""
    record = {"kind": call.kind, "milestone": call.number, "prompt": call.prompt}
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
    # S603 is ignored on purpose: this fake runs only git, with arguments the test controls.
    return subprocess.run([shutil.which("git") or "git", *args], check=False).returncode  # noqa: S603


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
    write_test(call.number)
    return 0


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


ACTIONS = {"test": act_test, "build": act_build, "review": act_review, "repair": act_repair}


def read_call() -> Call | None:
    """Read the prompt on stdin and return the session it names, or None when it names none."""
    prompt = sys.stdin.buffer.read().decode("utf-8", "replace").replace("\r\n", "\n")
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
    call = read_call()
    if call is None:
        sys.stderr.write("fake claude: no milestone in the prompt\n")
        return 1
    log_session(call)
    return 0 if call.state == "idle" else ACTIONS[call.kind](call)


if __name__ == "__main__":
    raise SystemExit(main())
