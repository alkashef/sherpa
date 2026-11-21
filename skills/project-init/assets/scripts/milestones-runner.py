"""Run the milestones of docs/plan.md one after another, each in its own branch.

Each milestone of the table "Milestones at a glance" runs in fresh `claude -p` sessions with the
model and effort its row names, following the loop of docs/workflow.md (Execute). The branch where
the run starts is the base branch. The runner reads the table from the plan of that branch
(`git show <base>:docs/plan.md`). For each milestone it makes the branch `milestone/M<n>` from the
base branch, and records the base branch in the git setting `branch.milestone/M<n>.base`. The
sessions work in the milestone branch:

1. The test session runs /write-tests. It writes the milestone's tests and may not read the code
   in src/. Before it, the runner reads the milestone's block from the plan. After it, the runner
   writes that block and the SHA-256 of every file under tests/ (not __pycache__, and with CRLF
   line ends read as LF) to .claude/logs/M<n>-tests.json.
2. The build session makes the tests pass and may not edit tests/. It deletes the milestone's row
   and block from the plan and commits. It does not push.
3. The review session changes no file. It reviews the diff of the branch and reports each finding
   as a `FINDING:` line. With findings, a repair session repairs them (it may not edit tests/ and
   commits as `M<n>: review repairs`), then a last review runs. The findings of the last review
   stay: the table counts them, and they do not stop the milestone. A milestone has at most two
   reviews in one run.

After a build session and after a repair session, the runner does its own checks. It compares the
hashes of tests/. It runs `python scripts/spec_coverage.py M<n>` over a temporary copy of
docs/spec.md and tests/, with the saved block. It compares docs/spec.md with the base branch. A
test file that changed, was added or was removed, a failed coverage check or a changed spec means
that the session did not finish. A review session that changed a file, made a commit or ended
with an error did not finish either. The same holds for a session that left its branch.

Then the runner merges: `git checkout <base>`, `git merge --ff-only milestone/M<n>`, `git push`
and `git branch -d milestone/M<n>`. If the fast-forward or the push fails, the run stops and the
branch stays. After the push, when the saved block has a Human test entry, the runner prints it
and waits. The answer `yes` continues the run. Any other answer, or no input, stops it.

A session blocks its milestone in the plan and commits nothing. The runner then restores
docs/plan.md in the milestone branch and commits the other changes there as `M<n>: partial work`
(with --no-verify: the hook checks the base branch, not this branch). It commits the blocked plan
alone on the base branch as `M<n>: blocked` (through the hook), pushes, and prints the block with
its question. The user adds an Approval entry, sets the Status to `approved`, commits, and runs
again.

A branch `milestone/M<n>` that exists when its milestone starts is left from an earlier run. The
runner handles these states:

1. The row of the base plan is `blocked`: the run stops and waits for the approval.
2. The working tree is dirty (only with --resume): the sessions continue on the branch.
3. The last commit of the branch is `M<n>: partial work`: the runner rebases the branch on the
   base branch and puts the work back in the working tree (`git reset --mixed <base>`). The
   sessions continue from it. A rebase conflict stops the run.
4. The tree is clean and the row left the plan of the branch: the build commit exists. Only the
   runner's checks, the review and the merge run.
5. The tree is clean and the branch has no commit of its own: the branch moves to the base
   branch, and the milestone runs from its start.
6. The tree is clean and the branch has other commits: the sessions continue on the branch.

Sessions that continue skip the test session when the hashes file of the milestone exists.

Before the first milestone, the runner checks the conda environment, the settings file, the commit
hook, a clean git tree, the upstream of the base branch, .gitignore and
`python scripts/spec_coverage.py --consistency`. It stops at a row whose Status is `blocked`. A
session that did not finish is tried again (--retries, default 1) in a new session that resumes
from the changes the first one left; its prompt gets the reason why the earlier try did not
count. A retry repeats only that session. A session that runs over --timeout-minutes counts as
not finished. If the last try also fails, the run stops and HEAD stays on the milestone branch;
--resume starts the next run on a dirty tree. When the range is done, the runner runs
`python scripts/live_checks.py` and prints its last line; failed live checks end the run with
exit code 1.

The runner clears the screen and shows a table that it redraws every second: a row for each
milestone of the run (the one that runs now last), and a footer with the total time, the percent
and the count of the milestones done. The Decisions column counts the DECISION lines of the
reports, and the Findings column counts the FINDING lines of the last review. It logs each
session to .claude/logs/ (M<n>-test.log, M<n>.log, M<n>-review.log, M<n>-repair.log and
M<n>-review-last.log, with -<try> for a retry), and appends a timing to
.claude/logs/timings.csv.

The runner writes no code, no test and no text of the plan: the claude sessions do that. Its git
work is the branch, the merge, the push and the two commits of a blocked milestone. The git
pre-commit hook still runs every check and test on each commit of a session. Each session starts
with permission prompts off, so its guard rails are the rules in .claude/settings.json, plus the
--disallowedTools of its kind: the runner refuses to start without that file.

Run, after `conda activate {{PROJECT_NAME}}`:
    python scripts/milestones-runner.py [--start N] [--end N] [--retries N] [--resume]
        [--timeout-minutes N]
"""

import argparse
import csv
import ctypes
import hashlib
import io
import json
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field, replace
from functools import partial
from pathlib import Path
from types import TracebackType
from typing import Final, NoReturn, Self

# The rules of a run (docs/workflow.md).
ENV_NAME: Final = "{{PROJECT_NAME}}"
SPEC_FILE: Final = "spec.md"  # the name of the spec in docs/
VALID_MODELS: Final = ("haiku", "sonnet", "opus")  # aliases: the latest model of the family
MODEL_ID: Final = re.compile(r"claude-(haiku|sonnet|opus)-\d[a-z0-9-]*")  # a pinned version
VALID_EFFORTS: Final = ("low", "medium", "high", "xhigh", "max")
RESUME_NOTE: Final = (
    "A previous session worked on this milestone and did not finish. Its changes may still be in "
    "the working tree, or in a commit of this branch. First run git status, git diff and "
    "git log -5, then continue from there. Do not redo finished work. If the block has a Blocked "
    "entry and no Approval entry answers it, only finish stopping the milestone, as in rule (f)."
)
TEST_RESUME_NOTE: Final = (
    "A previous test session worked on this milestone and did not finish. Its test files may "
    "still be in tests/. First run git status and read them, then continue from there. Do not "
    "redo finished work."
)
REVIEW_RESUME_NOTE: Final = (
    "An earlier review session of this milestone did not count. Do the whole review again."
)
REPAIR_RESUME_NOTE: Final = (
    "An earlier repair session worked on these findings and did not finish. Its changes may "
    "still be in the working tree, or in a commit of this branch. First run git status, git diff "
    "and git log -5, then continue from there. Do not redo finished work."
)
SESSION_TEST: Final = "test"  # the session that writes the milestone's tests
SESSION_BUILD: Final = "build"  # the session that makes them pass
SESSION_REVIEW: Final = "review"  # the session that reviews the diff of the milestone branch
SESSION_REPAIR: Final = "repair"  # the session that repairs the findings of the review
SESSION_REVIEW_LAST: Final = "review-last"  # the second review, after the repair
# A test session may not read the code: its tests come from the spec and the design.
TEST_SESSION_DENIED: Final = ("Read(./src/**)", "Grep(./src/**)", "Glob(./src/**)")
BUILD_SESSION_DENIED: Final = ("Edit(./tests/**)", "Write(./tests/**)")
REVIEW_SESSION_DENIED: Final = ("Edit", "Write", "MultiEdit", "NotebookEdit")  # it changes no file
DENIED_TOOLS: Final = {
    SESSION_TEST: TEST_SESSION_DENIED,
    SESSION_BUILD: BUILD_SESSION_DENIED,
    SESSION_REVIEW: REVIEW_SESSION_DENIED,
    SESSION_REPAIR: BUILD_SESSION_DENIED,
    SESSION_REVIEW_LAST: REVIEW_SESSION_DENIED,
}
BRANCH_PREFIX: Final = "milestone/M"  # the branch of milestone 3 is milestone/M3
MILESTONE_BRANCH: Final = re.compile(r"milestone/M\d+")
PARTIAL_WORK: Final = "partial work"  # the commit `M<n>: partial work` of a blocked milestone
ENTRY_FRESH: Final = "fresh"  # the milestone runs from its start
ENTRY_RESUME: Final = "resume"  # the sessions continue from the work an earlier run left
ENTRY_BUILT: Final = "built"  # the build commit exists: only the checks, the review, the merge
PLAN_PATH: Final = "docs/plan.md"  # the plan, as git names it
BYTE_ORDER_MARK: Final = chr(0xFEFF)  # can start a UTF-8 file; it is not part of the text
ANSWER_YES: Final = "yes"  # the answer that confirms a human test
LIVE_SCRIPT: Final = "live_checks.py"  # in scripts/: runs the live checks after the milestones
LIVE_NOT_RUN: Final = 3  # its exit code when it ran no live check
LOCKED_PATHS: Final = (f"docs/{SPEC_FILE}",)  # a milestone may not change these
SKIPPED_DIR: Final = "__pycache__"
IGNORE_ENTRIES: Final = (".claude/logs/",)
HOOKS_PATH: Final = ".githooks"  # the value of git's core.hooksPath that turns the commit hook on
TAIL_LINES: Final = 30
DEFAULT_RETRIES: Final = 1  # extra tries of a milestone whose session did not finish
DEFAULT_TIMEOUT_MINUTES: Final = 90  # the longest one claude session may run
REFRESH_SECONDS: Final = 1.0
TIMEOUT_EXIT_CODE: Final = 124  # the exit code of a session the runner cut off (as GNU timeout)
OUTCOME_DONE: Final = "done"
OUTCOME_FAILED: Final = "failed"
OUTCOME_BLOCKED: Final = "blocked"
OUTCOME_RUNNING: Final = "running"  # shown in the table for the milestone that runs now
TABLE_HEADER: Final = (
    "ID",
    "Title",
    "Model",
    "Effort",
    "Duration",
    "Decisions",
    "Findings",
    "Result",
)
TITLE_COLUMN: Final = 1  # the column that is cut when the table is wider than the terminal
MIN_TITLE_WIDTH: Final = 10
STATUS_BLOCKED: Final = "blocked"  # in the Status column: the milestone waits for an approval


@dataclass(frozen=True)
class Row:
    """One row of the table "Milestones at a glance" (the last four cells in lower case).

    human_test is the cell of the column Human test: yes or no.
    """

    id: int
    title: str
    model: str
    effort: str
    status: str
    human_test: str = "no"


@dataclass(frozen=True)
class Result:
    """How one milestone of this run ended (outcome: done, failed or blocked).

    findings counts the findings that the last review of the milestone kept.
    """

    id: int
    title: str
    model: str
    effort: str
    started_at: str
    seconds: float
    outcome: str
    decisions: int
    findings: int = 0


@dataclass(frozen=True)
class Options:
    """The command-line arguments. A start or end of None means the whole table."""

    start: int | None
    end: int | None
    retries: int
    resume: bool
    timeout_minutes: int


@dataclass(frozen=True)
class Attempt:
    """One try at a session: its number from 1, whether it resumes work, its time limit.

    reason says why the earlier try did not count. It is empty for a first try.
    """

    number: int
    resume: bool
    timeout_seconds: float
    reason: str = ""


@dataclass(frozen=True)
class Paths:
    """The files the runner reads and writes, below the repository root."""

    root: Path

    @property
    def plan(self) -> Path:
        """docs/plan.md."""
        return self.root / "docs" / "plan.md"

    @property
    def log_dir(self) -> Path:
        """.claude/logs, with one log per milestone."""
        return self.root / ".claude" / "logs"

    @property
    def gitignore(self) -> Path:
        """.gitignore."""
        return self.root / ".gitignore"

    @property
    def settings(self) -> Path:
        """.claude/settings.json, the rules that guard an unattended session."""
        return self.root / ".claude" / "settings.json"

    @property
    def timings(self) -> Path:
        """.claude/logs/timings.csv."""
        return self.log_dir / "timings.csv"

    def tests_file(self, milestone_id: int) -> Path:
        """.claude/logs/M<n>-tests.json: the hashes of tests/ after the test session."""
        return self.log_dir / f"M{milestone_id}-tests.json"


@dataclass(frozen=True)
class ClaudeRun:
    """The output lines and the exit code of one `claude -p` run; timed_out if it was cut off."""

    lines: list[str]
    exit_code: int
    timed_out: bool = False
    log_name: str = ""


@dataclass(frozen=True)
class SavedTests:
    """What the runner keeps after a test session: the milestone's block, the hashes of tests/."""

    block: list[str]
    hashes: dict[str, str]


@dataclass(frozen=True)
class Verdict:
    """The judgement of a finished run: its outcome and, for a failure, the reason."""

    outcome: str
    reason: str


@dataclass(frozen=True)
class Job:
    """One session of a milestone: its kind, the text of its prompt, and the judge of a try.

    prompt takes two arguments: whether the try resumes earlier work, and why the earlier try did
    not count. judge takes the run of a try and returns its verdict.
    """

    kind: str
    prompt: Callable[[bool, str], str]
    judge: Callable[[ClaudeRun], Verdict]


class RunStoppedError(Exception):
    """The run must stop. main() prints the message and the detail lines, then the summary."""

    def __init__(self, message: str, details: Sequence[str] = (), color: str = "red") -> None:
        """Keep the first line, the lines under it, and the color of the first line."""
        super().__init__(message)
        self.message = message
        self.details = tuple(details)
        self.color = color


class Stopwatch:
    """Counts the seconds since it was made."""

    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        """Start counting now. A test passes its own clock."""
        self._clock = clock
        self._start = clock()

    def elapsed(self) -> float:
        """Return the seconds counted so far."""
        return self._clock() - self._start


def _now() -> str:
    """Return the local date and time, as timings.csv keeps it."""
    return time.strftime("%Y-%m-%d %H:%M:%S")


@dataclass
class Running:
    """The milestone that runs now: its row, its timer, its try and what was counted so far.

    saved is what its test session left: the block of the milestone and the hashes of tests/.
    findings counts the findings that its last review kept.
    """

    row: Row
    watch: Stopwatch
    attempt: int = 1
    decisions: int = 0
    findings: int = 0
    saved: SavedTests | None = None
    started_at: str = field(default_factory=_now)


@dataclass
class RunState:
    """What this run has done so far: the milestones to run, the total timer and the results.

    running is the milestone that runs now, or None between two milestones.
    """

    total: int
    stopwatch: Stopwatch
    results: list[Result] = field(default_factory=list)
    running: Running | None = None

    def done_count(self) -> int:
        """Return how many milestones of this run finished with the outcome done."""
        return sum(1 for result in self.results if result.outcome == OUTCOME_DONE)


def read_answer() -> str | None:
    """Return the line that the user types, or None when the input has ended."""
    try:
        return input()
    except EOFError:
        return None


@dataclass(frozen=True)
class Console:
    """Prints to the terminal: ANSI colors when use_color is True, plain text when it is False.

    ask reads the answer of the user to a question. A test passes its own function.
    """

    use_color: bool
    ask: Callable[[], str | None] = field(default=read_answer)

    def paint(self, text: str, color: str) -> str:
        """Return the text in "green", "yellow" or "red"; unchanged when colors are off."""
        if not self.use_color:
            return text
        code = {"green": "32", "yellow": "33", "red": "31"}[color]
        return f"\x1b[{code}m{text}\x1b[0m"

    def say(self, text: str = "", color: str | None = None) -> None:
        """Print one permanent line."""
        print(text if color is None else self.paint(text, color), flush=True)

    def clear_screen(self) -> None:
        """Clear the screen and put the cursor at the top (only on a terminal with colors)."""
        if self.use_color:
            sys.stdout.write("\x1b[2J\x1b[H")
            sys.stdout.flush()

    def draw(self, lines: Sequence[str]) -> None:
        """Show the lines from the top of the screen, replacing the last drawing (plain: print)."""
        if not self.use_color:
            for line in lines:
                print(line)
            sys.stdout.flush()
            return
        body = "".join(f"{line}\x1b[K\n" for line in lines)
        sys.stdout.write("\x1b[H" + body + "\x1b[J")
        sys.stdout.flush()


@dataclass(frozen=True)
class Session:
    """Everything one run needs: the files, the terminal, the state, the range and the base branch.

    base is the branch where the run started. Each milestone branch is merged into it.
    """

    paths: Paths
    console: Console
    state: RunState
    first: int
    last: int
    options: Options
    base: str


class LiveTable:
    """Redraws the table every second from a thread. Use it in a `with` block.

    Without colors (not a terminal) it draws nothing; the table is printed when a milestone ends.
    """

    def __init__(self, console: Console, render: Callable[[], list[str]]) -> None:
        """Keep the console and the function that returns the lines of the table."""
        self._console = console
        self._render = render
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._loop, daemon=True)

    def __enter__(self) -> Self:
        """Start the thread."""
        self._thread.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Stop the thread, also after an error."""
        self._stop.set()
        self._thread.join()

    def _loop(self) -> None:
        """Draw, then wait one second or until stop; repeat. Ends at once when colors are off."""
        while self._console.use_color:
            self._console.draw(self._render())
            if self._stop.wait(REFRESH_SECONDS):
                return


# --- reading the plan ----------------------------------------------------------------------------


def _split_lines(text: str) -> list[str]:
    """Split on CRLF, LF or CR only (str.splitlines also splits on form feeds and more)."""
    return re.split(r"\r\n|\r|\n", text)


def _read_lines(path: Path) -> list[str]:
    """Return the lines of a UTF-8 file (a byte order mark is dropped)."""
    return _split_lines(path.read_text(encoding="utf-8-sig"))


def parse_row(line: str) -> Row | None:
    """Read one table row: | **M<n>** Title | Description | Model | Effort | Human test | Status |.

    Args:
        line: One line of the plan.

    Returns:
        The row, or None when the line is not a milestone row with these six cells.
    """
    match = re.match(
        r"^\|\s*\*\*M(?P<id>\d+)\*\*\s*(?P<title>[^|]*?)\s*\|\s*(?P<text>.*)\|\s*(?P<model>[^|]*?)\s*"
        r"\|\s*(?P<effort>[^|]*?)\s*\|\s*(?P<human>[^|]*?)\s*\|\s*(?P<status>[^|]*?)\s*\|\s*$",
        line,
        re.IGNORECASE,
    )
    if match is None:
        return None
    return Row(
        id=int(match["id"]),
        title=match["title"].replace("**", "").strip(),
        model=match["model"].strip().lower(),
        effort=match["effort"].strip().lower(),
        status=match["status"].strip().lower(),
        human_test=match["human"].strip().lower(),
    )


def parse_plan_rows(lines: Sequence[str]) -> list[Row]:
    """Return the rows of the table "Milestones at a glance", in the order of the file.

    Args:
        lines: The lines of docs/plan.md.

    Returns:
        The rows between that heading and the next heading of level 1 to 3.
    """
    rows: list[Row] = []
    in_table = False
    for line in lines:
        if re.match(r"^## Milestones at a glance", line, re.IGNORECASE):
            in_table = True
        elif in_table and re.match(r"^#{1,3} ", line):
            break
        elif in_table:
            row = parse_row(line)
            if row is not None:
                rows.append(row)
    return rows


def plan_has_row(lines: Sequence[str], milestone_id: int) -> bool:
    """Tell whether the table "Milestones at a glance" still has a row for the milestone.

    A finished milestone leaves the table: its commit deletes its block and its row
    (docs/workflow.md).

    Args:
        lines: The lines of docs/plan.md.
        milestone_id: The milestone number.

    Returns:
        True when the table has the row of that milestone.
    """
    return any(row.id == milestone_id for row in parse_plan_rows(lines))


def plan_row(lines: Sequence[str], milestone_id: int) -> Row | None:
    """Return the milestone's row of the table "Milestones at a glance", or None if it left."""
    return next((row for row in parse_plan_rows(lines) if row.id == milestone_id), None)


def milestone_block(lines: Sequence[str], milestone_id: int) -> list[str]:
    """Return the lines of the milestone's `### M<n>` block, up to the next heading."""
    block: list[str] = []
    inside = False
    for line in lines:
        if re.match(r"^#{1,3} ", line):
            inside = re.match(rf"^### M{milestone_id}\b", line) is not None
        if inside:
            block.append(line)
    return block


def block_entry(block: Sequence[str], label: str) -> list[str]:
    """Return the text of the `- **<label>:**` entry of a block, with its continuation lines.

    Args:
        block: The lines of a milestone block.
        label: The name of the entry, such as "Human test".

    Returns:
        The text after the label, then each line up to the next entry or the next empty line. No
        lines when the block has no such entry, or the entry has no text.
    """
    start = f"- **{label}:**"
    lines: list[str] = []
    for line in block:
        if not lines and line.startswith(start):
            lines = [line[len(start) :].strip()]
        elif lines and (line.startswith("- **") or not line.strip()):
            break
        elif lines:
            lines.append(line.rstrip())
    return lines if any(line.strip() for line in lines) else []


def rows_in_range(rows: Sequence[Row], first: int, last: int) -> list[Row]:
    """Return the rows numbered first to last, in table order (not numeric order)."""
    return [row for row in rows if first <= row.id <= last]


def next_open_row(rows: Sequence[Row]) -> Row | None:
    """Return the first row, in table order, whose status is not "done"."""
    return next((row for row in rows if row.status != "done"), None)


def resolve_range(rows: Sequence[Row], start: int | None, end: int | None) -> tuple[int, int]:
    """Return the first and last milestone number; a missing start or end means the whole table."""
    ids = [row.id for row in rows]
    return (
        min(ids, default=0) if start is None else start,
        max(ids, default=0) if end is None else end,
    )


def range_problem(first: int, last: int) -> str | None:
    """Return why the range is refused (a start after the end), or None."""
    if first > last:
        return f"--start ({first}) is greater than --end ({last})."
    return None


def row_problem(row: Row) -> str | None:
    """Return why the model or effort of the row cannot be used, or None."""
    if not row.model or not row.effort:
        return f"M{row.id} has no Model or no Effort in the table."
    if row.model not in VALID_MODELS and not MODEL_ID.fullmatch(row.model):
        return (
            f"M{row.id}: Model '{row.model}' is not one of {', '.join(VALID_MODELS)} "
            "or a full model ID such as claude-sonnet-5-5."
        )
    if row.effort not in VALID_EFFORTS:
        return f"M{row.id}: Effort '{row.effort}' is not one of {', '.join(VALID_EFFORTS)}."
    return None


# --- the prompts of the sessions -----------------------------------------------------------------

BUILD_INTRO: Final = (
    "Implement only milestone M<n> (<title>) from docs/plan.md.",
    "Follow its block, the loop in docs/workflow.md (steps 4 to 6) and CLAUDE.md.",
    "This is the build session: a test session has already written the milestone's tests.",
    "Make them pass, and change no file in tests/.",
    "Before the first edit, read the sections of docs/design.md that the Refs of the block name.",
    "You work in the branch milestone/M<n>: stay on it.",
    "This is an unattended run: nobody can answer questions.",
)
BUILD_RULES: Final = (
    "Rules:",
    "(a) never edit docs/spec.md: a settings rule denies that edit in an unattended run;",
    "(b) in docs/plan.md, when the gate passes, delete the block of M<n> and its row in",
    'the table "Milestones at a glance", and edit nothing else in the plan;',
    "(c) do that edit before the commit so the commit includes it;",
    "(d) commit only the files this milestone changed, with the message `M<n>: <title>`; do not",
    "push and do not merge: the runner does that;",
    "(e) if the pre-commit hook refuses the commit, fix the cause; never bypass the hook;",
    "(f) stop the milestone only if it needs a new or changed requirement in",
    "docs/spec.md, an action that CLAUDE.md 'Git and destructive actions' forbids, a new",
    "flow of user data to an external service, real user data, a secret in a committed",
    "file, a dependency that docs/design.md does not name in a Decided decision (use the",
    "standard library first), or a change to a test in tests/ that you find wrong, and no",
    "Approval entry in the block permits it. To stop: set",
    "its Status in the table to `blocked`, add a Blocked entry with the reason and the",
    "exact question to its block (template in docs/workflow.md), change nothing else and",
    "commit nothing. Do not undo your work: the runner keeps it in the milestone branch;",
    "(g) an Approval entry in the block is the user's decision: it permits exactly what it",
    "says, even an action these rules or CLAUDE.md otherwise forbid, and nothing more;",
    "(h) a tool call that a settings rule denies is not allowed in an unattended run: do",
    "not retry it or work around it. Choose another way, or stop as in (f) if none;",
    "(i) everything else may change without a question: a design decision (also a Decided",
    "one), a module, an interface, a setting. Decide the most conservative option and",
    "carry on. If docs/spec.md and docs/design.md disagree, the spec wins: fix the",
    "design. When the decision changes the design, add a DEC-NNN (the next free number)",
    "to docs/design.md with the Status Proposed, and write 'auto-decided in M<n>, review'",
    "in its Why. When it replaces a Decided decision, set that one to Superseded. Never",
    "renumber an ID;",
    "(j) never call a live external service (an LLM, a paid API, a production database),",
    "never use real user data, and do not start the app for a person. A test uses a real",
    "local part where one exists (a database file in a temporary folder, a server that it",
    "starts on 127.0.0.1) and a fake only for an external service. No milestone session runs",
    "the tests in tests/live/. The Gate is",
    "`python scripts/check.py` and `python scripts/spec_coverage.py M<n>`. A check that",
    "needs a live service is a live check, and one that needs a person is the human test of",
    "the milestone: neither is yours;",
    "(k) end with the report in CLAUDE.md 'Communication and reporting'. In it, write each",
    "decision of (i) as its own line: `DECISION: <what> | <why> | <DEC-NNN or none>`.",
)
TEST_INTRO: Final = (
    "Run /write-tests for milestone M<n> (<title>) of docs/plan.md.",
    "This is the test session (docs/workflow.md, Execute); a build session",
    "writes the code afterwards and may not change your tests.",
    "You work in the branch milestone/M<n>: stay on it.",
    "This is an unattended run: nobody can answer questions.",
)
TEST_RULES: Final = (
    "Rules:",
    "(a) commit nothing, also not to block the milestone (d);",
    "(b) change only files under tests/, docs/design.md for an auto-decision (c), and",
    "docs/plan.md only to block the milestone (d). Never edit docs/spec.md, and never",
    "read the code in src/, also not through the shell;",
    "(c) for anything else that is open, such as a gap in docs/design.md, a Decided",
    "decision that the tests cannot follow, or a detail of a library, decide the most",
    "conservative option and carry on. When the decision changes the design, add a",
    "DEC-NNN (the next free number) to docs/design.md with the Status Proposed, and write",
    "'auto-decided in M<n>, review' in its Why. When it replaces a Decided decision, set",
    "that one to Superseded. Never renumber an ID;",
    "(d) stop the milestone only if its tests need a new or changed requirement in",
    "docs/spec.md, an action that CLAUDE.md 'Git and destructive actions' forbids, real",
    "user data, or a dependency that docs/design.md does not name in a Decided decision,",
    "and",
    "no Approval entry in the block permits it. To stop: set its Status in the table to",
    "`blocked`, add a Blocked entry with the reason and the exact question to its block",
    "(template in docs/workflow.md), change nothing else and commit nothing. Do not undo",
    "your work: the runner keeps it in the milestone branch;",
    "(e) a tool call that a settings rule denies is not allowed: do not retry it or work",
    "around it;",
    "(f) never call a live external service and do not start the app for a person. A test",
    "uses a real local part where one exists (a database file in a temporary folder, a",
    "server that it starts on 127.0.0.1) and a fake only for an external service. A test of",
    "the level `live` goes to tests/live/: write it, but do not run it;",
    "(g) end with the report of /write-tests. In it, write each decision of (c) as its own",
    "line: `DECISION: <what> | <why> | <DEC-NNN or none>`.",
)
REVIEW_INTRO: Final = (
    "Review milestone M<n> (<title>): the diff `git diff <base>...HEAD` of this branch.",
    "First run the built-in /code-review skill on that diff if this Claude Code has it.",
    "If it does not, write `BUILT-IN REVIEW: not available`.",
    "Then run /code-review-sherpa on the same diff.",
    "Change no file and commit nothing.",
    "This is an unattended run: nobody can answer questions.",
)
REVIEW_RULES: Final = (
    "Report each finding of the two reviews as its own line:",
    "`FINDING: <high|medium|low> | <file>:<line> | <rule or smell> | <remedy>`.",
    "Write `NO FINDINGS` when there is none.",
)
REPAIR_INTRO: Final = (
    "Repair the findings of the review of milestone M<n> (<title>).",
    "You work in the branch milestone/M<n>: stay on it.",
    "This is an unattended run: nobody can answer questions.",
)
REPAIR_RULES: Final = (
    "Rules:",
    "(a) repair each finding with the smallest change;",
    "(b) do not change behavior that docs/spec.md states;",
    "(c) change no file in tests/, and never edit docs/spec.md;",
    "(d) a finding that is wrong is not repaired: write `REJECTED: <finding> | <why>` for it;",
    "(e) run the Gate: `python scripts/check.py` must pass;",
    "(f) commit your changes with the message `M<n>: review repairs`; do not push and do not",
    "merge: the runner does that. When you rejected every finding, commit nothing;",
    "(g) if the pre-commit hook refuses the commit, fix the cause; never bypass the hook;",
    "(h) a tool call that a settings rule denies is not allowed: do not retry it or work",
    "around it.",
)


def _fill(sentences: Sequence[str], row: Row) -> str:
    """Join the sentences of a prompt and put the milestone's number and title in."""
    return " ".join(sentences).replace("<n>", str(row.id)).replace("<title>", row.title)


def retry_notes(note: str, resume: bool, reason: str) -> tuple[str, ...]:
    """Return the sentences for a session that continues earlier work.

    Args:
        note: The note of the session kind for a try that resumes.
        resume: True when the try resumes the work of an earlier session.
        reason: Why the earlier try did not count; empty when no try failed in this run.

    Returns:
        Nothing for a first try. Otherwise the note, then the reason when there is one.
    """
    if not resume:
        return ()
    return (note, f"The earlier try did not count: {reason}") if reason else (note,)


def build_prompt(row: Row, resume: bool = False, reason: str = "") -> str:
    """Return the text sent to the build session; a try that resumes gets the retry notes."""
    notes = retry_notes(RESUME_NOTE, resume, reason)
    return " ".join((_fill(BUILD_INTRO, row), *notes, _fill(BUILD_RULES, row)))


def build_test_prompt(row: Row, resume: bool = False, reason: str = "") -> str:
    """Return the text sent to the test session; a try that resumes gets the retry notes."""
    notes = retry_notes(TEST_RESUME_NOTE, resume, reason)
    return " ".join((_fill(TEST_INTRO, row), *notes, _fill(TEST_RULES, row)))


def review_prompt(row: Row, base: str, resume: bool = False, reason: str = "") -> str:
    """Return the text sent to a review session of the diff between `base` and the branch."""
    notes = retry_notes(REVIEW_RESUME_NOTE, resume, reason)
    intro = _fill(REVIEW_INTRO, row).replace("<base>", base)
    return " ".join((intro, *notes, *REVIEW_RULES))


def repair_prompt(row: Row, findings: Sequence[str], resume: bool = False, reason: str = "") -> str:
    """Return the text sent to the repair session, with the FINDING lines of the review."""
    notes = retry_notes(REPAIR_RESUME_NOTE, resume, reason)
    intro = " ".join((_fill(REPAIR_INTRO, row), *notes, "The findings:"))
    return "\n".join((intro, *findings, _fill(REPAIR_RULES, row)))


def session_command(row: Row, kind: str) -> list[str]:
    """Return the claude command of one session of a milestone, with the tools its kind denies.

    Args:
        row: The milestone; its model and effort go to claude.
        kind: SESSION_TEST (may not read the code in src/), SESSION_BUILD or SESSION_REPAIR (may
            not edit tests/), SESSION_REVIEW or SESSION_REVIEW_LAST (may not edit any file).

    Returns:
        The command; --disallowedTools comes last, because it takes every argument after it.
    """
    program = shutil.which("claude") or "claude"
    return [
        program,
        "-p",
        "--model",
        row.model,
        "--effort",
        row.effort,
        "--permission-mode",
        "bypassPermissions",
        "--disallowedTools",
        *DENIED_TOOLS[kind],
    ]


# --- the tests a test session wrote --------------------------------------------------------------


def snapshot_tests(root: Path) -> dict[str, str]:
    """Return the SHA-256 of every file under root/tests, keyed by its path from root.

    Args:
        root: The repository root (the folder that holds tests/).

    A CRLF line end is hashed as LF. Git stores a text file with LF (.gitattributes) and checks it
    out again with LF, for example when the runner puts the work of a blocked milestone back. So
    a file that a session wrote with CRLF must not count as changed after that.

    Returns:
        Path (with / separators) to hex digest, sorted by path; files in __pycache__ are skipped.
    """
    hashes = {}
    for path in sorted((root / "tests").rglob("*")):
        relative = path.relative_to(root)
        if path.is_file() and SKIPPED_DIR not in relative.parts:
            content = path.read_bytes().replace(b"\r\n", b"\n")
            hashes[relative.as_posix()] = hashlib.sha256(content).hexdigest()
    return hashes


def changed_tests(before: dict[str, str], after: dict[str, str]) -> list[str]:
    """Return the paths whose hash changed, that were added, or that were removed, sorted."""
    paths = before.keys() | after.keys()
    return sorted(path for path in paths if before.get(path) != after.get(path))


def save_tests(path: Path, saved: SavedTests) -> None:
    """Write the milestone's block and the hashes to the milestone's hashes file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {"block": saved.block, "hashes": saved.hashes}
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def load_tests(path: Path) -> SavedTests | None:
    """Return what a finished test session left in the hashes file, or None if there is none."""
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return SavedTests(block=data["block"], hashes=data["hashes"])


def coverage_problem(root: Path, milestone_id: int, block: Sequence[str]) -> str | None:
    """Run `python scripts/spec_coverage.py M<n>` with the block read before the test session.

    The build session deletes the block from the plan, so the script reads a temporary tree: a
    copy of docs/spec.md and tests/, and a plan that holds only that block. The script reads the
    requirement IDs of its Refs and the `Manual:` parts of its Tests first.

    Returns:
        Why the check failed, with its output, or None when it passed.
    """
    with tempfile.TemporaryDirectory() as folder:
        copy = Path(folder)
        (copy / "docs").mkdir()
        shutil.copyfile(root / "docs" / SPEC_FILE, copy / "docs" / SPEC_FILE)
        shutil.copytree(root / "tests", copy / "tests", ignore=shutil.ignore_patterns(SKIPPED_DIR))
        (copy / "docs" / "plan.md").write_text("\n".join(block) + "\n", encoding="utf-8")
        script = root / "scripts" / "spec_coverage.py"
        done = _run([sys.executable, str(script), f"M{milestone_id}", "--root", folder], root)
    if done.returncode == 0:
        return None
    return f"python scripts/spec_coverage.py M{milestone_id} failed:\n{done.stdout.strip()}"


def tests_problem(paths: Paths, row: Row, saved: SavedTests, kind: str) -> str | None:
    """Return why a session of `kind` does not count: tests/ changed, or coverage failed."""
    changed = changed_tests(saved.hashes, snapshot_tests(paths.root))
    if changed:
        return f"the {kind} session changed files in tests/: {', '.join(changed)}."
    return coverage_problem(paths.root, row.id, saved.block)


# --- arguments, environment and git --------------------------------------------------------------


def parse_args(argv: Sequence[str] | None = None) -> Options:
    """Read the command line.

    Args:
        argv: The arguments; None means sys.argv.

    Returns:
        The options. Without --start and --end the whole table is run.
    """
    parser = argparse.ArgumentParser(
        description="Run the milestones of docs/plan.md, one claude session each."
    )
    parser.add_argument(
        "--start", type=int, default=None, help="first milestone number (default: the first row)"
    )
    parser.add_argument(
        "--end", type=int, default=None, help="last milestone number (default: the last row)"
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=DEFAULT_RETRIES,
        help=f"extra tries of a milestone that did not finish (default: {DEFAULT_RETRIES})",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="start on a dirty git tree: the first milestone continues the changes it left",
    )
    parser.add_argument(
        "--timeout-minutes",
        type=int,
        default=DEFAULT_TIMEOUT_MINUTES,
        help=f"longest time of one claude session (default: {DEFAULT_TIMEOUT_MINUTES})",
    )
    args = parser.parse_args(argv)
    if args.retries < 0:
        parser.error("--retries must be 0 or more.")
    if args.timeout_minutes < 1:
        parser.error("--timeout-minutes must be 1 or more.")
    return Options(
        start=args.start,
        end=args.end,
        retries=args.retries,
        resume=args.resume,
        timeout_minutes=args.timeout_minutes,
    )


def in_project_env(prefix: str) -> bool:
    """Tell whether a Python prefix (sys.prefix) is the project's conda environment."""
    return Path(prefix).name.lower() == ENV_NAME.lower()


def missing_ignore_entries(existing: Sequence[str]) -> list[str]:
    """Return the entries of IGNORE_ENTRIES that are not a line of .gitignore (case-insensitive)."""
    known = {line.lower() for line in existing}
    return [entry for entry in IGNORE_ENTRIES if entry.lower() not in known]


def add_ignore_entries(gitignore: Path) -> bool:
    """Append the missing entries to .gitignore.

    Args:
        gitignore: The path of .gitignore.

    Returns:
        True when it had to add a line.
    """
    text = gitignore.read_text(encoding="utf-8-sig") if gitignore.exists() else ""
    missing = missing_ignore_entries(_split_lines(text))
    if not missing:
        return False
    # Start on a new line, so the first entry does not join a last line without a line end.
    start = "\n" if text and not text.endswith(("\n", "\r")) else ""
    with gitignore.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(start + "\n".join(missing) + "\n")
    return True


def _run(args: Sequence[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    """Run a command in the repository and return its result, or stop the run if it cannot start.

    The command gets no input, so it cannot take the answer that the user types for a human test.
    """
    try:
        return subprocess.run(
            list(args),
            cwd=cwd,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except OSError as exc:
        raise _error(f"`{args[0]}` could not run: {exc}") from exc


def _error(message: str) -> RunStoppedError:
    """Build the stop for a plain error: "ERROR: <message>" in red."""
    return RunStoppedError(f"ERROR: {message}")


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Run git in the repository and return its result."""
    return _run(["git", *args], root)


def _all_output(done: subprocess.CompletedProcess[str]) -> list[str]:
    """Return the lines that a finished command printed: standard output, then standard error."""
    return _output_lines((done.stdout + done.stderr).strip())


def _git_must(root: Path, *args: str) -> str:
    """Run git and return its output; stop the run, with the output of git, if it fails."""
    done = _git(root, *args)
    if done.returncode != 0:
        raise RunStoppedError(f"ERROR: `git {' '.join(args)}` failed:", _all_output(done))
    return done.stdout.strip()


def git_is_clean(root: Path) -> bool:
    """Tell whether `git status --porcelain` succeeds and lists nothing."""
    done = _git(root, "status", "--porcelain")
    return done.returncode == 0 and not done.stdout.strip()


def git_has_upstream(root: Path, branch: str) -> bool:
    """Tell whether the branch has an upstream, so that git push works."""
    done = _git(root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", branch + "@{u}")
    return done.returncode == 0


def git_hook_is_on(root: Path) -> bool:
    """Tell whether git runs this project's pre-commit hook (core.hooksPath is .githooks)."""
    done = _git(root, "config", "--get", "core.hooksPath")
    return done.returncode == 0 and done.stdout.strip().rstrip("/") == HOOKS_PATH


def git_head(root: Path) -> str:
    """Return the ID of the commit that HEAD points to."""
    return _git(root, "rev-parse", "HEAD").stdout.strip()


def git_branch(root: Path) -> str:
    """Return the name of the branch that HEAD is on; "" when HEAD is on no branch."""
    done = _git(root, "symbolic-ref", "--short", "-q", "HEAD")
    return done.stdout.strip() if done.returncode == 0 else ""


def branch_name(milestone_id: int) -> str:
    """Return the name of the branch of a milestone: milestone/M<n>."""
    return f"{BRANCH_PREFIX}{milestone_id}"


def branch_exists(root: Path, branch: str) -> bool:
    """Tell whether the repository has a local branch with this name."""
    return _git(root, "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}").returncode == 0


def base_branch(root: Path) -> str:
    """Return the base branch of the run: the branch where the run starts.

    When HEAD is on a milestone branch, an earlier run stopped there. The base branch is then the
    one that the earlier run recorded in the git setting `branch.<milestone branch>.base`.

    Raises:
        RunStoppedError: If HEAD is on no branch, or the milestone branch has no recorded base.
    """
    current = git_branch(root)
    if not current:
        raise _error("HEAD is on no branch. Check out the branch that the milestones go to.")
    if MILESTONE_BRANCH.fullmatch(current) is None:
        return current
    base = _git(root, "config", "--get", f"branch.{current}.base").stdout.strip()
    if not base:
        raise _error(
            f"HEAD is on {current}, and git does not know its base branch. "
            "Check out the branch that the milestones go to, then run again."
        )
    return base


def base_plan_lines(root: Path, base: str) -> list[str]:
    """Return the lines of docs/plan.md as the base branch has it committed.

    On a milestone branch the build session deletes the milestone's row, so the working tree does
    not say which milestone comes next.

    Raises:
        RunStoppedError: If the base branch has no docs/plan.md.
    """
    done = _git(root, "show", f"{base}:{PLAN_PATH}")
    if done.returncode != 0:
        raise _error(f"{PLAN_PATH} is not committed on the branch {base}. Commit the plan first.")
    return _split_lines(done.stdout.removeprefix(BYTE_ORDER_MARK))


def commits_ahead(root: Path, base: str, branch: str) -> int:
    """Return how many commits the branch has that the base branch does not have."""
    return int(_git_must(root, "rev-list", "--count", f"{base}..{branch}") or "0")


def last_subject(root: Path, branch: str) -> str:
    """Return the first line of the message of the last commit of the branch."""
    return _git_must(root, "log", "-1", "--format=%s", branch)


def locked_problem(root: Path, base: str) -> str | None:
    """Return why a milestone does not count: the spec differs from `base`.

    Args:
        root: The repository root.
        base: The base branch of the run.

    Returns:
        The reason with the changed files (committed, uncommitted or new), or None.
    """
    diff = _git(root, "diff", "--name-only", base, "--", *LOCKED_PATHS)
    new = _git(root, "ls-files", "--others", "--exclude-standard", "--", *LOCKED_PATHS)
    if diff.returncode != 0 or new.returncode != 0:
        return "git could not compare the spec with the base branch."
    changed = sorted({*_output_lines(diff.stdout), *_output_lines(new.stdout)})
    if changed:
        return f"a session changed the spec: {', '.join(changed)}."
    return None


def check_range(first: int, last: int) -> None:
    """Refuse a range whose start is after its end.

    Args:
        first: The first milestone number.
        last: The last milestone number.

    Raises:
        RunStoppedError: If the range is refused.
    """
    problem = range_problem(first, last)
    if problem is not None:
        raise _error(problem)


def check_tools(paths: Paths) -> None:
    """Check what a session needs: the conda environment, the settings file and the commit hook.

    Raises:
        RunStoppedError: If the conda env is wrong, the settings file is missing, or the commit
            hook is off.
    """
    if not in_project_env(sys.prefix):
        raise _error(
            f"Python runs from '{sys.prefix}', not from the conda env '{ENV_NAME}'. "
            f"Run 'conda activate {ENV_NAME}' first."
        )
    if not paths.settings.is_file():
        raise _error(
            ".claude/settings.json is missing. Its rules guard a session that runs with "
            "permission prompts off (docs/workflow.md), so the run does not start without it."
        )
    if not git_hook_is_on(paths.root):
        raise _error(
            "The pre-commit hook is off, so a commit would not run the checks. "
            f"Turn it on with: git config core.hooksPath {HOOKS_PATH}"
        )


def check_git(paths: Paths, base: str, allow_dirty: bool) -> None:
    """Check git before the first milestone: a clean tree, an upstream, the ignored log folder.

    Raises:
        RunStoppedError: If git is not clean (unless allow_dirty), the base branch has no
            upstream, or .gitignore had to be changed.
    """
    if not allow_dirty and not git_is_clean(paths.root):
        raise _error(
            "git status is not clean. Commit or stash your changes first, "
            "or run with --resume to continue the changes a failed milestone left."
        )
    if not git_has_upstream(paths.root, base):
        raise _error(
            f"The branch {base} has no upstream, so git push cannot work. "
            f"Set one with: git push -u origin {base}"
        )
    if add_ignore_entries(paths.gitignore):
        raise _error(
            f".gitignore was missing {', '.join(IGNORE_ENTRIES)}; the lines are added now. "
            "Commit .gitignore, then run again."
        )


def check_consistency(root: Path) -> None:
    """Run `python scripts/spec_coverage.py --consistency`: the IDs of the three documents agree.

    Raises:
        RunStoppedError: If the script finds a problem. The stop shows the output of the script.
    """
    script = root / "scripts" / "spec_coverage.py"
    done = _run([sys.executable, str(script), "--consistency"], root)
    if done.returncode != 0:
        raise RunStoppedError(
            "ERROR: python scripts/spec_coverage.py --consistency failed. Correct the spec, the "
            "design or the plan, commit, then run again:",
            _all_output(done),
        )


def preflight(paths: Paths, base: str, allow_dirty: bool) -> None:
    """Check the environment before the first milestone; allow_dirty (--resume) skips the git check.

    Args:
        paths: The repository files.
        base: The base branch of the run. It must have an upstream.
        allow_dirty: True when the first milestone may start on a tree with uncommitted changes.

    Raises:
        RunStoppedError: If a check of check_tools, check_git or check_consistency fails.
    """
    check_tools(paths)
    check_git(paths, base, allow_dirty)
    check_consistency(paths.root)


# --- time and display ----------------------------------------------------------------------------


def format_duration(seconds: float) -> str:
    """Return mm:ss, or h:mm:ss from one hour on (the seconds are cut, not rounded)."""
    hours, rest = divmod(int(seconds), 3600)
    minutes, secs = divmod(rest, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def percent(done: int, total: int) -> int:
    """Return 100 * done / total, rounded (0 when total is 0)."""
    return round(100 * done / total) if total > 0 else 0


def outcome_color(outcome: str) -> str:
    """Return green for done, yellow for blocked and running, red for failed."""
    return {OUTCOME_DONE: "green", OUTCOME_BLOCKED: "yellow", OUTCOME_RUNNING: "yellow"}.get(
        outcome, "red"
    )


def result_cells(result: Result) -> tuple[str, ...]:
    """Return the cells of the table row of a finished milestone."""
    return (
        f"M{result.id}",
        result.title,
        result.model,
        result.effort,
        format_duration(result.seconds),
        str(result.decisions),
        str(result.findings),
        result.outcome,
    )


def running_cells(running: Running) -> tuple[str, ...]:
    """Return the cells of the table row of the milestone that runs now (Result: running/retry)."""
    row = running.row
    outcome = OUTCOME_RUNNING if running.attempt == 1 else f"retry {running.attempt - 1}"
    return (
        f"M{row.id}",
        row.title,
        row.model,
        row.effort,
        format_duration(running.watch.elapsed()),
        "-",
        "-",
        outcome,
    )


def fit_text(text: str, width: int) -> str:
    """Return the text cut to `width` characters, with "…" at the end when it was cut."""
    return text if len(text) <= width else text[: width - 1] + "…"


def column_widths(cells: Sequence[Sequence[str]], max_width: int) -> list[int]:
    """Return the width of each column; the Title column shrinks if the table is wider than max."""
    widths = [max(len(row[index]) for row in cells) for index in range(len(TABLE_HEADER))]
    excess = sum(widths) + 3 * len(widths) + 1 - max_width
    if excess > 0:
        title = widths[TITLE_COLUMN]
        widths[TITLE_COLUMN] = max(min(MIN_TITLE_WIDTH, title), title - excess)
    return widths


def border_line(widths: Sequence[int], left: str, middle: str, right: str) -> str:
    """Return a horizontal line of the table, e.g. "├───┼───┤"."""
    return left + middle.join("─" * (width + 2) for width in widths) + right


def row_line(cells: Sequence[str], widths: Sequence[int]) -> str:
    """Return one row of the table, each cell padded (or cut) to the width of its column."""
    padded = (fit_text(cell, width).ljust(width) for cell, width in zip(cells, widths, strict=True))
    return "│ " + " │ ".join(padded) + " │"


def footer_line(state: RunState, inner_width: int) -> str:
    """Return the last line of the table: the total time on the left, "71%  5/7" on the right."""
    done = state.done_count()
    left = f"Total {format_duration(state.stopwatch.elapsed())}"
    right = f"{percent(done, state.total)}%  {done}/{state.total}"
    gap = max(inner_width - 2 - len(left) - len(right), 1)
    return "│ " + left + " " * gap + right + " │"


def table_lines(state: RunState, console: Console, max_width: int) -> list[str]:
    """Return the table of this run: a row for each finished milestone, the running one last.

    Args:
        state: The results so far, the milestone that runs now, the total timer and the total.
        console: Paints each row in the color of its outcome.
        max_width: The most characters of a line; a longer Title is cut.

    Returns:
        The lines of the table, from its top border to its bottom border.
    """
    records = [(result_cells(result), outcome_color(result.outcome)) for result in state.results]
    if state.running is not None:
        records.append((running_cells(state.running), outcome_color(OUTCOME_RUNNING)))
    widths = column_widths([TABLE_HEADER, *(cells for cells, _ in records)], max_width)
    inner_width = sum(width + 2 for width in widths) + len(widths) - 1
    return [
        border_line(widths, "┌", "┬", "┐"),
        row_line(TABLE_HEADER, widths),
        border_line(widths, "├", "┼", "┤"),
        *(console.paint(row_line(cells, widths), color) for cells, color in records),
        border_line(widths, "├", "┴", "┤"),
        footer_line(state, inner_width),
        "└" + "─" * inner_width + "┘",
    ]


def current_table(session: Session) -> list[str]:
    """Return the table of the run as it is now, at the width of the terminal."""
    max_width = shutil.get_terminal_size().columns - 1
    return table_lines(session.state, session.console, max_width)


def enable_ansi() -> bool:
    """Turn on ANSI colors in the console.

    Returns:
        True when colors work; False when output is not a terminal or Windows refuses.
    """
    if not sys.stdout.isatty():
        return False
    if sys.platform != "win32":
        return True
    stdout_handle, virtual_terminal = -11, 0x0004
    try:
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(stdout_handle)
        mode = ctypes.c_ulong()
        if not kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            return False
        return bool(kernel32.SetConsoleMode(handle, mode.value | virtual_terminal))
    except (AttributeError, OSError):
        return False


def start_console() -> Console:
    """Switch standard output to UTF-8 and return a Console with colors if they work."""
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8")
    return Console(use_color=enable_ansi())


# --- running a session ---------------------------------------------------------------------------


def _output_lines(text: str) -> list[str]:
    """Split the output of a run into lines, without the line ends at its end."""
    stripped = text.rstrip("\r\n")
    return _split_lines(stripped) if stripped else []


def _claude_process(command: Sequence[str], root: Path, prompt: str, timeout: float) -> ClaudeRun:
    """Run claude with the prompt on standard input; a run over `timeout` seconds is cut off."""
    try:
        done = subprocess.run(
            list(command),
            cwd=root,
            input=prompt,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        # Not re-raised: running over the time limit is a verdict (failed), so it is retried.
        cut_off = (
            exc.stdout.decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else exc.stdout
        )
        lines = [
            *_output_lines(cut_off or ""),
            f"[runner] claude was stopped after {timeout / 60:.0f} minutes.",
        ]
        return ClaudeRun(lines, TIMEOUT_EXIT_CODE, timed_out=True)
    except OSError as exc:
        raise _error(f"claude could not run: {exc}") from exc
    return ClaudeRun(_output_lines(done.stdout), done.returncode)


def log_file_name(row: Row, kind: str, number: int) -> str:
    """Return the log name of a try: M<n>.log for a build session, M<n>-<kind>.log for the others.

    A retry gets -<try> before the extension, such as M3-review-2.log.
    """
    stem = f"M{row.id}" if kind == SESSION_BUILD else f"M{row.id}-{kind}"
    return f"{stem}.log" if number == 1 else f"{stem}-{number}.log"


def run_claude(paths: Paths, row: Row, attempt: Attempt, job: Job) -> ClaudeRun:
    """Run one try of one session of a milestone in `claude -p` and save its output to its log.

    Args:
        paths: The repository files.
        row: The milestone; its model and effort go to claude.
        attempt: Which try this is, whether it resumes earlier work, its time limit, and why the
            earlier try did not count.
        job: The session: its kind and its prompt.

    Returns:
        The output lines (standard output and error together), the exit code and the log name.

    Raises:
        RunStoppedError: If the claude program cannot be found or started.
    """
    paths.log_dir.mkdir(parents=True, exist_ok=True)
    prompt = job.prompt(attempt.resume, attempt.reason)
    command = session_command(row, job.kind)
    run = _claude_process(command, paths.root, prompt, attempt.timeout_seconds)
    log_name = log_file_name(row, job.kind, attempt.number)
    (paths.log_dir / log_name).write_text(
        "".join(f"{line}\n" for line in run.lines), encoding="utf-8"
    )
    return replace(run, log_name=log_name)


# --- judging a session ---------------------------------------------------------------------------


def work_problem(session: Session, running: Running, kind: str) -> str | None:
    """Return why the work of a build or repair session does not count, or None.

    These are the runner's own checks: the hashes of tests/, the spec coverage with the saved
    block, and docs/spec.md compared with the base branch.
    """
    saved = running.saved
    problem = None if saved is None else tests_problem(session.paths, running.row, saved, kind)
    return problem or locked_problem(session.paths.root, session.base)


def work_verdict(session: Session, running: Running, kind: str) -> Verdict:
    """Return done when git is clean and the runner's own checks pass; failed, with why, if not."""
    if not git_is_clean(session.paths.root):
        return Verdict(OUTCOME_FAILED, "git status is not clean.")
    problem = work_problem(session, running, kind)
    return Verdict(OUTCOME_DONE, "") if problem is None else Verdict(OUTCOME_FAILED, problem)


def is_blocked(paths: Paths, row: Row) -> bool:
    """Tell whether the plan in the working tree says that the milestone is blocked."""
    after = plan_row(_read_lines(paths.plan), row.id)
    return after is not None and after.status == STATUS_BLOCKED


def blocked_verdict(session: Session) -> Verdict:
    """Return blocked, or failed when the session that blocked its milestone changed the spec."""
    problem = locked_problem(session.paths.root, session.base)
    return Verdict(OUTCOME_BLOCKED, "") if problem is None else Verdict(OUTCOME_FAILED, problem)


def judge_build(session: Session, running: Running, run: ClaudeRun) -> Verdict:
    """Return the verdict of a build session: done, blocked, or failed with the reason.

    Blocked: the row of the milestone says so. Done: the row left the plan, git is clean, and the
    runner's own checks pass. Nothing is pushed yet: the runner pushes after the merge.
    """
    paths, row = session.paths, running.row
    if is_blocked(paths, row):
        return blocked_verdict(session)
    if plan_has_row(_read_lines(paths.plan), row.id):
        cause = (
            "it ran over the time limit" if run.timed_out else f"claude exit code {run.exit_code}"
        )
        return Verdict(
            OUTCOME_FAILED,
            "its row is still in the plan table and not blocked, so the commit that finishes "
            f"it was not made ({cause}).",
        )
    return work_verdict(session, running, SESSION_BUILD)


def judge_test_session(session: Session, running: Running, run: ClaudeRun) -> Verdict:
    """Return blocked (its row says so), failed (cut off or a claude error) or done.

    A test session commits nothing: its tests, or the plan that blocks the milestone, stay in the
    working tree.
    """
    if is_blocked(session.paths, running.row):
        return blocked_verdict(session)
    if run.timed_out:
        return Verdict(OUTCOME_FAILED, "the test session ran over the time limit.")
    if run.exit_code != 0:
        return Verdict(OUTCOME_FAILED, f"the test session ended with exit code {run.exit_code}.")
    return Verdict(OUTCOME_DONE, "")


def judge_review(root: Path, head: str, run: ClaudeRun) -> Verdict:
    """Return done for a review that ended well and changed nothing; failed, with why, if not.

    Args:
        root: The repository root.
        head: The commit that HEAD pointed to before the review.
        run: The run of the review session.
    """
    reason = None
    if run.timed_out:
        reason = "the review session ran over the time limit."
    elif run.exit_code != 0:
        reason = f"the review session ended with exit code {run.exit_code}."
    elif git_head(root) != head:
        reason = "the review session made a commit. A review changes nothing."
    elif not git_is_clean(root):
        reason = "the review session changed files: git status is not clean."
    return Verdict(OUTCOME_DONE, "") if reason is None else Verdict(OUTCOME_FAILED, reason)


def judge_repair(session: Session, running: Running, run: ClaudeRun) -> Verdict:
    """Return done when git is clean and the runner's own checks pass after a repair session.

    The output and the exit code of the run do not count. A repair that commits nothing, because
    it rejected every finding, is done.
    """
    del run
    return work_verdict(session, running, SESSION_REPAIR)


def judge_try(session: Session, row: Row, job: Job, run: ClaudeRun) -> Verdict:
    """Judge one try of a session; a session that left the milestone branch does not count."""
    branch = branch_name(row.id)
    if git_branch(session.paths.root) != branch:
        return Verdict(
            OUTCOME_FAILED,
            f"the session left the branch {branch}. Check it out again: the sessions of a "
            "milestone work there.",
        )
    return job.judge(run)


def write_tests_job(session: Session, running: Running) -> Job:
    """Return the test session of the milestone."""
    prompt = partial(build_test_prompt, running.row)
    return Job(SESSION_TEST, prompt, partial(judge_test_session, session, running))


def build_job(session: Session, running: Running) -> Job:
    """Return the build session of the milestone."""
    prompt = partial(build_prompt, running.row)
    return Job(SESSION_BUILD, prompt, partial(judge_build, session, running))


def review_job(session: Session, running: Running, kind: str) -> Job:
    """Return a review session of the milestone (kind: SESSION_REVIEW or SESSION_REVIEW_LAST).

    The judge compares HEAD with the commit that HEAD points to now, before the review.
    """
    root = session.paths.root
    prompt = partial(review_prompt, running.row, session.base)
    return Job(kind, prompt, partial(judge_review, root, git_head(root)))


def repair_job(session: Session, running: Running, findings: Sequence[str]) -> Job:
    """Return the repair session of the milestone, for the FINDING lines of its review."""
    prompt = partial(repair_prompt, running.row, findings)
    return Job(SESSION_REPAIR, prompt, partial(judge_repair, session, running))


# --- the branch of a milestone -------------------------------------------------------------------


def restore_partial_work(root: Path, base: str, row: Row) -> None:
    """Put the partial work of a blocked milestone back in the working tree, on the base branch.

    HEAD is on the milestone branch, whose last commit is `M<n>: partial work`. The branch is
    rebased on the base branch, then moved to it with `git reset --mixed`: the work stays in the
    working tree, not committed.

    Raises:
        RunStoppedError: If the rebase stops with a conflict. The rebase is aborted first.
    """
    branch = branch_name(row.id)
    done = _git(root, "rebase", base)
    if done.returncode != 0:
        _git(root, "rebase", "--abort")
        details = [
            f"Rebase it by hand: git rebase {base} {branch}",
            "Keep the message of its last commit, then run the runner again.",
            *_all_output(done),
        ]
        raise RunStoppedError(
            f"ERROR: the partial work of M{row.id} in {branch} does not apply on {base}.", details
        )
    _git_must(root, "reset", "--mixed", base)


def leftover_entry(session: Session, row: Row) -> str:
    """Check out the milestone branch that an earlier run left, and return how to continue.

    Returns:
        ENTRY_RESUME for a dirty tree, for partial work (put back in the working tree first) and
        for a branch with other commits. ENTRY_BUILT when the row left the plan of the branch.
        ENTRY_FRESH for a branch with no commit of its own, after it moved to the base branch.
    """
    root, base, branch = session.paths.root, session.base, branch_name(row.id)
    dirty = not git_is_clean(root)
    _git_must(root, "checkout", branch)
    if dirty:
        return ENTRY_RESUME
    if last_subject(root, branch) == f"M{row.id}: {PARTIAL_WORK}":
        restore_partial_work(root, base, row)
        return ENTRY_RESUME
    if not plan_has_row(_read_lines(session.paths.plan), row.id):
        return ENTRY_BUILT
    if commits_ahead(root, base, branch) > 0:
        return ENTRY_RESUME
    _git_must(root, "merge", "--ff-only", base)
    return ENTRY_FRESH


def enter_branch(session: Session, row: Row) -> str:
    """Check out the branch of the milestone, new or left by an earlier run.

    A new branch starts at the base branch, and git records the base branch for it. Uncommitted
    changes (only with --resume) go with the checkout.

    Returns:
        How the milestone starts: ENTRY_FRESH, ENTRY_RESUME or ENTRY_BUILT.

    Raises:
        RunStoppedError: If HEAD is on another branch than the base branch or the milestone
            branch, or a git command fails.
    """
    root, base, branch = session.paths.root, session.base, branch_name(row.id)
    current = git_branch(root)
    if current not in {base, branch}:
        raise _error(
            f"HEAD is on {current}, but the next milestone is M{row.id}. "
            f"Check out {base}, then run again."
        )
    if branch_exists(root, branch):
        return leftover_entry(session, row)
    _git_must(root, "checkout", "-b", branch, base)
    _git_must(root, "config", f"branch.{branch}.base", base)
    return ENTRY_FRESH if git_is_clean(root) else ENTRY_RESUME


def merge_refused(base: str, row: Row, done: subprocess.CompletedProcess[str]) -> RunStoppedError:
    """Build the stop for a fast-forward that git refused: what the user must do, git's output."""
    branch = branch_name(row.id)
    details = [
        f"{base} has commits that {branch} does not have. Run: git rebase {base} {branch}",
        f"Then run the runner again: it checks, reviews and merges M{row.id}.",
        *_all_output(done),
    ]
    return RunStoppedError(
        f"ERROR: M{row.id} is not merged: git merge --ff-only {branch} failed.", details
    )


def push_refused(
    base: str, running: Running, done: subprocess.CompletedProcess[str]
) -> RunStoppedError:
    """Build the stop for a push that failed: what the user must do, git's output.

    The milestone is merged into the base branch, so the run did not ask its human test. The stop
    shows that test.
    """
    row, branch = running.row, branch_name(running.row.id)
    steps = human_test_steps(running)
    note = [f"The runner did not ask the human test of M{row.id}. Do it after the push:", *steps]
    details = [
        f"{base} has the commits of M{row.id}, but the remote does not. {branch} stays.",
        "Correct the cause, then run: git push",
        f"Then run: git branch -d {branch}",
        "Then run the runner again: it continues with the next milestone.",
        *(note if steps else []),
        *_all_output(done),
    ]
    return RunStoppedError(f"ERROR: M{row.id} is merged, but git push failed.", details)


def merge_milestone(session: Session, running: Running) -> None:
    """Move the base branch to the milestone branch, push it, and delete the milestone branch.

    Raises:
        RunStoppedError: If the fast-forward or the push fails. The milestone branch stays, and
            the stop says what the user must do.
    """
    root, base, row = session.paths.root, session.base, running.row
    branch = branch_name(row.id)
    _git_must(root, "checkout", base)
    merged = _git(root, "merge", "--ff-only", branch)
    if merged.returncode != 0:
        raise merge_refused(base, row, merged)
    pushed = _git(root, "push")
    if pushed.returncode != 0:
        raise push_refused(base, running, pushed)
    _git_must(root, "branch", "-d", branch)


def waiting_for_approval(plan_lines: Sequence[str], row: Row) -> RunStoppedError:
    """Build the stop for a blocked milestone: what to do, then its block with the question."""
    message = (
        f"M{row.id} waits for your approval. In docs/plan.md, add an Approval entry to its "
        "block, set its Status to `approved`, commit, and run again:"
    )
    return RunStoppedError(message, milestone_block(plan_lines, row.id), "yellow")


def block_milestone(session: Session, row: Row) -> NoReturn:
    """Do the git work of a milestone that a session blocked, then stop the run with its question.

    The session changed the plan and committed nothing. The plan goes back to its committed state
    in the milestone branch, and the other changes are committed there as `M<n>: partial work`,
    with --no-verify: the hook checks the base branch, not this branch. The blocked plan is
    committed alone on the base branch as `M<n>: blocked`, through the hook, and pushed.

    Raises:
        RunStoppedError: Always. It carries the question of the milestone, or a git failure.
    """
    paths, root = session.paths, session.paths.root
    blocked_plan = paths.plan.read_bytes()
    _git_must(root, "checkout", "HEAD", "--", PLAN_PATH)
    if not git_is_clean(root):
        _git_must(root, "add", "-A")
        _git_must(root, "commit", "--no-verify", "-m", f"M{row.id}: {PARTIAL_WORK}")
    _git_must(root, "checkout", session.base)
    paths.plan.write_bytes(blocked_plan)
    _git_must(root, "add", PLAN_PATH)
    _git_must(root, "commit", "-m", f"M{row.id}: blocked")
    _git_must(root, "push")
    raise waiting_for_approval(_read_lines(paths.plan), row)


# --- running a milestone -------------------------------------------------------------------------


def stop_for(row: Row, verdict: Verdict, run: ClaudeRun) -> NoReturn:
    """Stop the run because the milestone did not finish.

    Raises:
        RunStoppedError: Always. It carries the reason, the last lines of output of the last
            session (when one ran), and how to continue.
    """
    intro = f"Last {TAIL_LINES} lines of output (full log: .claude/logs/{run.log_name}):"
    tail = [intro, *run.lines[-TAIL_LINES:]] if run.log_name else []
    hint = (
        f"Its work stays in the branch {branch_name(row.id)}. To continue from it, run again "
        "with --resume."
    )
    raise RunStoppedError(f"M{row.id} stopped: {verdict.reason}", [*tail, hint])


def append_timing(path: Path, result: Result) -> None:
    """Append a row (ID, model, effort, start, seconds, result) to the CSV; new: a header first."""
    path.parent.mkdir(parents=True, exist_ok=True)
    is_new = not path.exists()
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        if is_new:
            writer.writerow(["id", "model", "effort", "start", "seconds", "result"])
        writer.writerow(
            [
                f"M{result.id}",
                result.model,
                result.effort,
                result.started_at,
                f"{result.seconds:.1f}",
                result.outcome,
            ]
        )


def record_result(session: Session, result: Result) -> None:
    """Keep the result and add it to timings.csv (only a warning if that fails)."""
    session.state.results.append(result)
    try:
        append_timing(session.paths.timings, result)
    except OSError as exc:
        session.console.say(f"WARNING: could not write {session.paths.timings}: {exc}", "yellow")


def decision_lines(lines: Sequence[str]) -> list[str]:
    """Return the lines of a report that record an automatic decision (`DECISION: ...`)."""
    return [line.strip() for line in lines if re.match(r"^\W*DECISION:", line.strip())]


def finding_lines(lines: Sequence[str]) -> list[str]:
    """Return the lines of a review that report a finding (`FINDING: ...`)."""
    return [line.strip() for line in lines if re.match(r"^\W*FINDING:", line.strip())]


def human_test_steps(running: Running) -> list[str]:
    """Return the lines of the Human test entry of the saved block; no lines when it has none."""
    return block_entry(running.saved.block, "Human test") if running.saved is not None else []


def prepare_milestone(session: Session, row: Row) -> None:
    """Check what the milestone needs before claude starts.

    Raises:
        RunStoppedError: If it waits for an approval, or its model or effort cannot be used.
    """
    if row.status == STATUS_BLOCKED:
        raise waiting_for_approval(base_plan_lines(session.paths.root, session.base), row)
    problem = row_problem(row)
    if problem is not None:
        raise _error(problem)


def run_attempts(
    session: Session, running: Running, job: Job, resume: bool = False
) -> tuple[ClaudeRun, Verdict]:
    """Run one session of the milestone, with the live table, until it is done or blocked.

    A try that did not finish is repeated, as a resume, up to `--retries` times. The prompt of
    the new try gets the reason of the verdict. The table shows a retry in the Result column of
    the running row.
    """
    row = running.row
    number, reason = 1, ""
    running.attempt = number
    while True:
        attempt = Attempt(number, resume, session.options.timeout_minutes * 60, reason)
        with LiveTable(session.console, lambda: current_table(session)):
            run = run_claude(session.paths, row, attempt, job)
        verdict = judge_try(session, row, job, run)
        if verdict.outcome != OUTCOME_FAILED or number > session.options.retries:
            return run, verdict
        number, resume, reason = number + 1, True, verdict.reason
        running.attempt = number


def run_test_session(session: Session, running: Running, resume: bool) -> tuple[ClaudeRun, Verdict]:
    """Read the milestone's block, run the test session, then save it with the hashes of tests/.

    The old hashes file is deleted first, so the file exists only after a test session finished.
    """
    paths, row = session.paths, running.row
    block = milestone_block(_read_lines(paths.plan), row.id)
    paths.tests_file(row.id).unlink(missing_ok=True)
    run, verdict = run_attempts(session, running, write_tests_job(session, running), resume)
    running.decisions += len(decision_lines(run.lines))
    if verdict.outcome == OUTCOME_DONE:
        running.saved = SavedTests(block, snapshot_tests(paths.root))
        save_tests(paths.tests_file(row.id), running.saved)
    return run, verdict


def built_verdict(session: Session, running: Running) -> Verdict:
    """Judge the build commit that an earlier run left: the runner's own checks must pass.

    Raises:
        RunStoppedError: If the hashes file of the milestone is missing. The runner cannot tell
            then whether the build session changed a test.
    """
    if running.saved is None:
        row, branch = running.row, branch_name(running.row.id)
        raise _error(
            f".claude/logs/M{row.id}-tests.json is missing, so the tests of {branch} cannot be "
            f"checked. Check out {session.base}, delete the branch with "
            f"`git branch -D {branch}`, then run again: M{row.id} runs from its start."
        )
    return work_verdict(session, running, SESSION_BUILD)


def run_sessions(session: Session, running: Running, entry: str) -> tuple[ClaudeRun, Verdict]:
    """Run the test session, then the build session, as the entry of the milestone needs.

    Args:
        session: The run.
        running: The milestone. Its `saved` and `decisions` are filled in.
        entry: ENTRY_FRESH runs both sessions. ENTRY_RESUME skips the test session when the
            hashes file of the milestone exists. ENTRY_BUILT runs no session: the build commit
            exists, and only the runner's own checks judge it.

    Returns:
        The run of the last session (an empty run for ENTRY_BUILT), and its verdict.
    """
    paths, row = session.paths, running.row
    resume = entry != ENTRY_FRESH
    running.saved = load_tests(paths.tests_file(row.id)) if resume else None
    if entry == ENTRY_BUILT:
        return ClaudeRun([], 0), built_verdict(session, running)
    build_resumes = running.saved is not None
    if running.saved is None:
        run, verdict = run_test_session(session, running, resume)
        if verdict.outcome != OUTCOME_DONE:
            return run, verdict
    run, verdict = run_attempts(session, running, build_job(session, running), build_resumes)
    running.decisions += len(decision_lines(run.lines))
    return run, verdict


def review_milestone(session: Session, running: Running) -> tuple[ClaudeRun, Verdict]:
    """Review the diff of the milestone branch; with findings, repair them and review once more.

    The findings of the last review stay: `running.findings` counts them, and the milestone goes
    on. A milestone gets at most two reviews.

    Returns:
        The run of the last session, and its verdict.
    """
    first = review_job(session, running, SESSION_REVIEW)
    run, verdict = run_attempts(session, running, first)
    findings = finding_lines(run.lines)
    if verdict.outcome != OUTCOME_DONE or not findings:
        return run, verdict
    run, verdict = run_attempts(session, running, repair_job(session, running, findings))
    if verdict.outcome != OUTCOME_DONE:
        return run, verdict
    last = review_job(session, running, SESSION_REVIEW_LAST)
    run, verdict = run_attempts(session, running, last)
    if verdict.outcome == OUTCOME_DONE:
        running.findings = len(finding_lines(run.lines))
    return run, verdict


def run_stages(session: Session, running: Running) -> tuple[ClaudeRun, Verdict]:
    """Run the milestone in its branch: the sessions, the review, then the merge and the push.

    Returns:
        The run of the last session, and its verdict. The review runs only after a done build,
        and the merge only after a done review.
    """
    entry = enter_branch(session, running.row)
    run, verdict = run_sessions(session, running, entry)
    if verdict.outcome == OUTCOME_DONE:
        run, verdict = review_milestone(session, running)
    if verdict.outcome == OUTCOME_DONE:
        merge_milestone(session, running)
    return run, verdict


def close_milestone(session: Session, running: Running, outcome: str) -> None:
    """Record how the milestone ended, and draw the table with its row."""
    row = running.row
    result = Result(
        row.id,
        row.title,
        row.model,
        row.effort,
        running.started_at,
        running.watch.elapsed(),
        outcome,
        running.decisions,
        running.findings,
    )
    session.state.running = None
    record_result(session, result)
    session.console.draw(current_table(session))


def ask_human_test(session: Session, running: Running) -> None:
    """Print the human test of a merged milestone, and wait for the answer of the user.

    No live table is drawn while the runner waits: the table is drawn only while a session runs.

    Raises:
        RunStoppedError: If the answer is not `yes` (in any case), or the input has ended.
    """
    row, console = running.row, session.console
    steps = human_test_steps(running)
    if not steps:
        return
    console.say(f"M{row.id} is merged and pushed. Do its human test now:", "yellow")
    for line in steps:
        console.say(line)
    console.say("Type yes when the test passed, then press Enter:")
    answer = console.ask()
    if answer is None or answer.strip().lower() != ANSWER_YES:
        details = [
            "Give a fault to /sdd: it becomes a fix milestone.",
            "Run the runner again to continue with the next milestone.",
        ]
        raise RunStoppedError(f"The human test of M{row.id} is not confirmed.", details, "yellow")


def run_milestone(session: Session, row: Row) -> None:
    """Run one milestone in its branch, time it, and check that it finished.

    Raises:
        RunStoppedError: If the milestone is blocked or did not finish, if the merge or the push
            failed, or if the user did not confirm its human test.
    """
    running = Running(row, Stopwatch())
    session.state.running = running
    try:
        run, verdict = run_stages(session, running)
    except RunStoppedError:
        close_milestone(session, running, OUTCOME_FAILED)
        raise
    close_milestone(session, running, verdict.outcome)
    if verdict.outcome == OUTCOME_BLOCKED:
        block_milestone(session, row)
    if verdict.outcome != OUTCOME_DONE:
        stop_for(row, verdict, run)
    ask_human_test(session, running)


def run_live_checks(session: Session) -> None:
    """Run `python scripts/live_checks.py`, when the project has it, and print its last line.

    The script ends with 0 when the live checks passed and with 3 when it ran none.

    Raises:
        RunStoppedError: If the script ends with another code. The stop shows its output.
    """
    root = session.paths.root
    script = root / "scripts" / LIVE_SCRIPT
    if not script.is_file():
        return
    done = _run([sys.executable, str(script)], root)
    lines = _output_lines(done.stdout)
    summary = lines[-1] if lines else f"python scripts/{LIVE_SCRIPT} printed no result."
    if done.returncode not in {0, LIVE_NOT_RUN}:
        raise RunStoppedError(summary, [*_output_lines(done.stderr), *lines[:-1]])
    session.console.say(summary, "green" if done.returncode == 0 else "yellow")


def unread_rows(lines: Sequence[str]) -> list[str]:
    """Return the lines that start as a milestone row (`| **M<n>**`) but are not a row of six cells.

    A plan from before the column Human test has rows of five cells. The runner reads none of
    them, so it must refuse the plan and not report an empty range as done.
    """
    starts = (line for line in lines if re.match(r"^\|\s*\*\*M\d+\*\*", line))
    return [line for line in starts if parse_row(line) is None]


def check_rows(lines: Sequence[str]) -> None:
    """Refuse a plan that has a milestone row the runner cannot read.

    Raises:
        RunStoppedError: If a row does not have the six cells of docs/workflow.md.
    """
    unread = unread_rows(lines)
    if unread:
        raise RunStoppedError(
            "ERROR: docs/plan.md has a milestone row that the runner cannot read. A row has six "
            "cells: Milestone, Description, Model, Effort, Human test, Status.",
            unread,
        )


def _range_rows(session: Session) -> list[Row]:
    """Return the rows of the range as the plan of the base branch has them now."""
    rows = parse_plan_rows(base_plan_lines(session.paths.root, session.base))
    return rows_in_range(rows, session.first, session.last)


def open_session(options: Options, console: Console, paths: Paths, state: RunState) -> Session:
    """Find the base branch, read its plan, resolve the range, and check the environment.

    Raises:
        RunStoppedError: If the plan is missing, the base branch is not known, a row cannot be
            read, the range is refused, or a check of preflight fails.
    """
    if not paths.plan.is_file():
        raise _error("docs/plan.md is missing. Write the plan with /write-plan first.")
    base = base_branch(paths.root)
    plan_lines = base_plan_lines(paths.root, base)
    check_rows(plan_lines)
    rows = parse_plan_rows(plan_lines)
    first, last = resolve_range(rows, options.start, options.end)
    check_range(first, last)
    preflight(paths, base, options.resume)
    state.total = sum(1 for row in rows_in_range(rows, first, last) if row.status != "done")
    return Session(paths, console, state, first, last, options, base)


def run_all(options: Options, console: Console, paths: Paths, state: RunState) -> None:
    """Run every milestone of the range whose status is not done, in table order.

    When the range is done, the live checks run.

    Args:
        options: The command-line options.
        console: The terminal.
        paths: The repository files.
        state: Filled in as milestones finish; main() prints the summary from it.

    Raises:
        RunStoppedError: At the first problem that a retry did not solve.
    """
    session = open_session(options, console, paths, state)
    while True:
        row = next_open_row(_range_rows(session))
        if row is None:
            console.say(f"Range M{session.first} to M{session.last} is done.", "green")
            run_live_checks(session)
            return
        prepare_milestone(session, row)
        run_milestone(session, row)


def run_guarded(options: Options, console: Console, paths: Paths, state: RunState) -> int:
    """Run the range; print a stop or an interrupt instead of a traceback. Return the exit code."""
    try:
        run_all(options, console, paths, state)
    except RunStoppedError as stop:
        console.say(stop.message, stop.color)
        for line in stop.details:
            console.say(line)
        return 1
    except KeyboardInterrupt:
        console.say("Interrupted.", "yellow")
        return 130
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Clear the screen, then run the milestones with the live table of the run.

    Args:
        argv: The command-line arguments; None means sys.argv.

    Returns:
        0 when the range is done, 1 when a milestone, a human test or the live checks stopped the
        run, 130 after Ctrl+C.
    """
    options = parse_args(argv)
    console = start_console()
    console.clear_screen()
    paths = Paths(Path(__file__).resolve().parent.parent)
    state = RunState(total=0, stopwatch=Stopwatch())
    return run_guarded(options, console, paths, state)


if __name__ == "__main__":
    sys.exit(main())
