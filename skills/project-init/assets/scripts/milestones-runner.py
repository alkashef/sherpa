"""Run the milestones of docs/plan.md one after another, each in its own branch.

Each milestone of the table "Milestones at a glance" runs in fresh sessions with the model and
effort its row names, following the loop of docs/workflow.md (Execute). The branch where the run
starts is the base branch. The runner reads the table from the plan of that branch
(`git show <base>:docs/plan.md`). For each milestone it makes the branch `milestone/M<n>` from the
base branch, and records the base branch in the git setting `branch.milestone/M<n>.base`.

1. The test session writes the milestone's tests in a temporary folder outside the project: the
   docs, the rules, the tool configs and tests/, but no src/ and no .git. The AI that
   config/test-writer.json names writes them (--test-writer overrides it): claude (the default,
   with the row's model and effort, through /write-tests), codex, antigravity or copilot (they
   read one AGENTS.md made from CLAUDE.md, the rules files and /write-tests). The runner copies
   tests/ back, with docs/plan.md and docs/design.md when they changed, and runs its own checks:
   ruff and mypy on tests/ in the folder, each new test file with --junitxml (a failure is valid
   when it is a wrong value, an error that src/ raised, or a missing module that the Owner entry
   names), and each older test file, which must pass. It never judges a writer by its exit code.
   With problems, the writer gets one round of repair in the same folder, with the type and the
   message of each problem. Then the runner writes the milestone's block and the SHA-256 of every
   file under tests/ (not __pycache__, and with CRLF line ends read as LF) to
   .claude/logs/M<n>-tests.json.
2. The build session makes the tests pass and may not edit tests/. It deletes the milestone's row
   and block from the plan and commits. It does not push.
3. The review session runs in a temporary git worktree of the branch, which the runner deletes
   after it: a change that the review makes only adds a warning to the log. It reports each
   finding as a `FINDING:` line that names the file of the fix. A finding about tests/ goes to a
   test session in the folder of the test writer; if it changed a test, a build session makes the
   tests pass and commits `M<n>: test repairs`. Any other finding goes to a repair session (it may
   not edit tests/ and commits `M<n>: review repairs`). Then a last review runs. A finding of the
   last review blocks the milestone when its severity is high, or medium with a requirement ID
   as its rule.
   The other findings stay: the table counts them. A milestone has at most two reviews in one
   run. After the user approves a block of the last review, the next run gives the decision and
   the findings of the block to the repairs, and no new review runs: when the repairs change
   nothing, the milestone merges; when they commit a change, the last review checks it, and its
   findings block as usual. The approval covers the code that the user saw.

After a build, rebuild or repair session, the runner does its own checks. It compares the hashes
of tests/. It runs `python scripts/spec_coverage.py M<n>` over a temporary copy of docs/spec.md
and tests/, with the saved block. It compares docs/spec.md with the base branch. A test file that
changed, was added or was removed, a failed coverage check or a changed spec means that the
session did not finish. A review that ended with an error did not finish either. The same holds
for a session that left its branch.

Then the runner merges: `git checkout <base>`, `git merge --ff-only milestone/M<n>`, `git push`
and `git branch -d milestone/M<n>`. If the fast-forward or the push fails, the run stops and the
branch stays. After the push, when the saved block has a Human test entry, the runner prints it
and waits. The answer `yes` continues the run. Any other answer, or no input, stops it.

A session blocks its milestone in the plan and commits nothing. The runner then restores
docs/plan.md in the milestone branch and commits the other changes there as `M<n>: partial work`
(with --no-verify: the hook checks the base branch, not this branch). It commits the blocked plan
alone on the base branch as `M<n>: blocked` (through the hook), pushes, and prints the block with
its question. A milestone that the last review blocks keeps its commits in its branch; the runner
writes the Blocked entry with the findings into the plan of the base branch, and commits and
pushes it in the same way. The user adds an Approval entry, sets the Status to `approved`,
commits, and runs again.

A branch `milestone/M<n>` that exists when its milestone starts is left from an earlier run. The
runner handles these states:

1. The row of the base plan is `blocked`: the run stops and waits for the approval.
2. The working tree is dirty (only with --resume): the sessions continue on the branch.
3. The last commit of the branch is `M<n>: partial work`: the runner rebases the branch on the
   base branch and puts the work back in the working tree (`git reset --mixed <base>`). The
   sessions continue from it. A rebase conflict stops the run.
4. The tree is clean and the row left the plan of the branch: the build commit exists. Only the
   runner's checks, the review and the merge run. When the row is `approved` and the base branch
   moved (a review blocked the milestone), the runner first rebases the branch on the base
   branch; a conflict in docs/plan.md takes the base plan without the milestone.
5. The tree is clean and the branch has no commit of its own: the branch moves to the base
   branch, and the milestone runs from its start.
6. The tree is clean and the branch has other commits: the sessions continue on the branch.

Sessions that continue skip the test session when the hashes file of the milestone exists.

Before the first milestone, the runner checks the conda environment, the settings file, the commit
hook, a clean git tree, the upstream of the base branch, .gitignore,
`python scripts/spec_coverage.py --consistency`, that `python` on the PATH of a session is the
project's environment, and that a test writer other than claude answers one short prompt. Each
session gets the folders of the conda environment first on its PATH. It stops at a row whose
Status is `blocked`. A session that did not finish is tried again (--retries, default 1) in a new
session that resumes from the changes the first one left; its prompt gets the reason why the
earlier try did not count. A retry repeats only that session. A session that runs over
--timeout-minutes counts as not finished. If the last try also fails, the run stops and HEAD
stays on the milestone branch; --resume starts the next run on a dirty tree. When the range is
done, the runner runs `python scripts/live_checks.py` and prints its last line; failed live
checks end the run with exit code 1.

The runner clears the screen and shows a table that it redraws every second: a row for each
milestone of the run that finished, then the one that runs now, then each planned milestone of the
range in very dark grey (`-` in Duration, Decisions and Findings, and `planned` in Result). Under
them, a Total row gives the total time under Duration, and a last row gives a progress bar over
the width of the table, the percent and the count of the milestones done. The Decisions column
counts the DECISION lines of the reports, and the Findings column counts the FINDING lines of the
last review. It logs each
session to .claude/logs/ (M<n>-test.log, M<n>-test-fix.log, M<n>.log, M<n>-review.log,
M<n>-review-tests.log, M<n>-rebuild.log, M<n>-repair.log and M<n>-review-last.log, with -<try>
for a retry), and appends a timing to .claude/logs/timings.csv.

The runner writes no code, no test and no text of the plan except the Blocked entry of a review:
the sessions do that. Its git work is the branch, the worktree of a review, the merge, the push
and the commits of a blocked milestone. The git pre-commit hook still runs every check and test on
each commit of a session. Each session starts with permission prompts off, so its guard rails are
the rules in .claude/settings.json, plus the --disallowedTools of its kind: the runner refuses to
start without that file.

One step of a milestone in chat (docs/workflow.md, Execute) uses the same guards:
`--tests-only M<n>` runs the test session in the current branch and commits nothing, and
`--review-only M<n>` runs the review in a worktree of HEAD and prints its findings. With
`--review-findings`, `--tests-only` repairs the findings about tests of the last review.

Run, after `conda activate {{PROJECT_NAME}}`:
    python scripts/milestones-runner.py [--start N] [--end N] [--retries N] [--resume]
        [--timeout-minutes N] [--test-writer NAME]
    python scripts/milestones-runner.py --tests-only M<n> [--review-findings]
    python scripts/milestones-runner.py --review-only M<n>
"""

import argparse
import csv
import ctypes
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field, replace
from functools import partial
from pathlib import Path
from types import TracebackType
from typing import Final, NoReturn, Self
from xml.etree import ElementTree

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
    "still be in tests/. First read them, then continue from there. Do not redo finished work."
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
SESSION_TEST_FIX: Final = "test-fix"  # the round of repair of a test session, after the checks
SESSION_REVIEW_TESTS: Final = "review-tests"  # a test session for the review findings on tests
SESSION_REBUILD: Final = "rebuild"  # a build session after the review-tests session changed tests
# A test session may not read the code: its tests come from the spec and the design. A Read rule
# with a path also covers Grep and Glob, and an Edit rule with a path also covers Write: claude
# warns about a Grep, Glob or Write rule with a path, because it matches nothing.
TEST_SESSION_DENIED: Final = ("Read(./src/**)",)
BUILD_SESSION_DENIED: Final = ("Edit(./tests/**)",)
REVIEW_SESSION_DENIED: Final = ("Edit", "Write", "NotebookEdit")  # it changes no file
DENIED_TOOLS: Final = {
    SESSION_TEST: TEST_SESSION_DENIED,
    SESSION_BUILD: BUILD_SESSION_DENIED,
    SESSION_REVIEW: REVIEW_SESSION_DENIED,
    SESSION_REPAIR: BUILD_SESSION_DENIED,
    SESSION_REVIEW_LAST: REVIEW_SESSION_DENIED,
    SESSION_TEST_FIX: TEST_SESSION_DENIED,
    SESSION_REVIEW_TESTS: TEST_SESSION_DENIED,
    SESSION_REBUILD: BUILD_SESSION_DENIED,
}
# The sessions that the test writer runs, in a folder without the code (docs/workflow.md).
WRITER_SESSIONS: Final = (SESSION_TEST, SESSION_TEST_FIX, SESSION_REVIEW_TESTS)
WRITER_CLAUDE: Final = "claude"
WRITER_CODEX: Final = "codex"
WRITER_ANTIGRAVITY: Final = "antigravity"
WRITER_COPILOT: Final = "copilot"
TEST_WRITERS: Final = (WRITER_CLAUDE, WRITER_ANTIGRAVITY, WRITER_CODEX, WRITER_COPILOT)
WRITER_PROGRAMS: Final = {
    WRITER_CLAUDE: "claude",
    WRITER_CODEX: "codex",
    WRITER_ANTIGRAVITY: "agy",
    WRITER_COPILOT: "copilot",
}
WRITER_SIGN_IN: Final = {  # what the user does once, so that the writer runs with nobody there
    WRITER_CLAUDE: "claude",
    WRITER_CODEX: "codex login, or set CODEX_API_KEY",
    WRITER_ANTIGRAVITY: "one interactive agy session, or set GEMINI_API_KEY",
    WRITER_COPILOT: "set COPILOT_GITHUB_TOKEN to a fine-grained token",
}
WRITER_FILE: Final = "config/test-writer.json"  # the writer that /project-init recorded
START_CHECK_PROMPT: Final = "Reply with the single word ok."
START_CHECK_SECONDS: Final = 300
# What the folder of a test session holds: no src/ and no .git. tests/ is copied too.
FOLDER_FILES: Final = (
    "docs/spec.md",
    "docs/design.md",
    "docs/plan.md",
    "docs/workflow.md",
    "scripts/spec_coverage.py",
    "scripts/check.py",
    "scripts/run-check.sh",
    ".coveragerc",
    "ruff.toml",
    "mypy.ini",
    "pytest.ini",
    "requirements.txt",
    "package.json",
    "tsconfig.json",
    "eslint.config.js",
    ".prettierrc.json",
    ".stylelintrc.json",
)
CLAUDE_FOLDER_FILES: Final = ("CLAUDE.md", ".claude/settings.json")
CLAUDE_FOLDER_DIRS: Final = (".claude/rules", ".claude/skills/write-tests")
COPIED_BACK_DOCS: Final = ("docs/plan.md", "docs/design.md")  # an auto-decision, or a block
CACHE_DIRS: Final = frozenset({"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"})
# mypy reads the tests in the folder without the code, so an import of the code finds nothing.
MYPY_TEST_OPTIONS: Final = (
    "--disable-error-code",
    "import-not-found",
    "--disable-error-code",
    "import-untyped",
    "--disable-error-code",
    "no-any-return",
)
VALID_FAILURE: Final = "AssertionError"  # a test that fails because a value is wrong
IMPORT_FAILURES: Final = ("ModuleNotFoundError", "ImportError", "AttributeError")
MISSING_MODULE: Final = re.compile(
    r"No module named '([\w.]+)'|cannot import name '\w+' from '([\w.]+)'"
    r"|module '([\w.]+)' has no attribute"
)
EXCEPTION_LINE: Final = re.compile(r"^E\s+([A-Za-z_][\w.]*(?:Error|Exception|Exit)): ?(.*)$")
RAISED_AT: Final = re.compile(r"^(\S+):\d+: ([A-Za-z_][\w.]*)$")  # pytest: `path:line: Error`
MISSING_FIXTURE: Final = re.compile(r"fixture '(\w+)' not found")
OWNER_PATH: Final = re.compile(r"\b((?:src|main)[\w/.\-]*)")
# A finding blocks the merge when its severity is high, or medium with a requirement as its rule.
REQUIREMENT_RULE: Final = re.compile(r"^(?!DEC-|EX-|SCN-)[A-Z][A-Z0-9]*-\d{3,}\b")
SEVERITY_HIGH: Final = "high"
SEVERITY_MEDIUM: Final = "medium"
FILE_CELL: Final = 1  # the cells of a FINDING line: severity, file and line, rule, remedy
RULE_CELL: Final = 2
STATUS_APPROVED: Final = "approved"
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
LIVE_DIR: Final = "live"  # tests/live/ holds the live checks: no milestone runs them
PYTEST_NO_TESTS: Final = 5  # the exit code of pytest when it collected no test
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
DURATION_COLUMN: Final = 4  # the Total row puts the total time here, and `Total` to its left
OUTCOME_PLANNED: Final = "planned"  # in the table: a milestone of the range that has not started
BAR_DONE: Final = "█"
BAR_OPEN: Final = "░"
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
    """The command-line arguments. A start or end of None means the whole table.

    tests_only and review_only name the one milestone of a chat step (docs/workflow.md), or are
    None for a whole run. test_writer overrides config/test-writer.json when it is not empty.
    """

    start: int | None
    end: int | None
    retries: int
    resume: bool
    timeout_minutes: int
    tests_only: int | None = None
    review_only: int | None = None
    review_findings: bool = False
    test_writer: str = ""


@dataclass(frozen=True)
class Writer:
    """The AI that writes the tests: its name, model and effort (config/test-writer.json).

    An empty model or effort means the CLI's own default, or, for Claude, the value of the row.
    """

    name: str
    model: str = ""
    effort: str = ""


@dataclass(frozen=True)
class Failure:
    """Why one test failed: its name, the type and message of its error, and where it was raised."""

    test: str
    kind: str
    message: str
    raised_in: str = ""


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
class Launch:
    """How a session starts: its command, its folder, its standard input and its environment.

    environment None means the environment of the runner.
    """

    command: list[str]
    folder: Path
    stdin: str
    environment: dict[str, str] | None = None


@dataclass(frozen=True)
class SavedTests:
    """What the runner keeps after a test session: the milestone's block, the hashes of tests/."""

    block: list[str]
    hashes: dict[str, str]


@dataclass(frozen=True)
class TestsCheck:
    """What the runner's checks of new tests need.

    folder is the folder of the writer, reference the commit that the new tests are compared with,
    owners the modules of the Owner entry, and needs_tests whether no change of tests/ is a fault.
    """

    root: Path
    folder: Path
    reference: str
    owners: tuple[str, ...]
    needs_tests: bool


@dataclass(frozen=True)
class Verdict:
    """The judgement of a finished run: its outcome and, for a failure, the reason."""

    outcome: str
    reason: str


@dataclass(frozen=True)
class Job:
    """One session of a milestone: its kind, the text of its prompt, and the judge of a try.

    prompt takes two arguments: whether the try resumes earlier work, and why the earlier try did
    not count. judge takes the run of a try and returns its verdict. folder is where the session
    runs (None: the project). writer is the AI of a test session (None: claude, with the row's
    model and effort).
    """

    kind: str
    prompt: Callable[[bool, str], str]
    judge: Callable[[ClaudeRun], Verdict]
    folder: Path | None = None
    writer: Writer | None = None


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
    findings counts the findings that its last review kept. block is the milestone's block as
    the plan had it before the test session. decision is the Approval entry of the user, when an
    earlier review blocked the milestone. blocking holds the findings of the last review that
    block the merge. retest is True when the user approved a block about a test that looked
    wrong: a test session gets the decision before the build goes on. approved holds the
    findings of a block by the last review that the user approved: they go to the repairs with
    the decision, and only a change after the approval gets a review (RUN-08).
    """

    row: Row
    watch: Stopwatch
    attempt: int = 1
    decisions: int = 0
    findings: int = 0
    saved: SavedTests | None = None
    started_at: str = field(default_factory=_now)
    block: list[str] = field(default_factory=list)
    decision: tuple[str, ...] = ()
    blocking: list[str] = field(default_factory=list)
    retest: bool = False
    approved: tuple[str, ...] = ()


@dataclass
class RunState:
    """What this run has done so far: the milestones to run, the total timer and the results.

    running is the milestone that runs now, or None between two milestones. planned holds the
    rows of the range that were open when the run started.
    """

    total: int
    stopwatch: Stopwatch
    results: list[Result] = field(default_factory=list)
    running: Running | None = None
    planned: list[Row] = field(default_factory=list)

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
        """Return the text in "green", "yellow", "red" or "grey"; unchanged when colors are off.

        Grey is the very dark grey of the 256-color palette (238), for a planned milestone.
        """
        if not self.use_color:
            return text
        code = {"green": "32", "yellow": "33", "red": "31", "grey": "38;5;238"}[color]
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
    writer: Writer = field(default_factory=lambda: Writer(WRITER_CLAUDE))
    environment: dict[str, str] = field(default_factory=dict)


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


def last_block_entry(block: Sequence[str], label: str) -> list[str]:
    """Return the last `- **<label>:**` entry of a block, as block_entry reads it.

    A milestone that was blocked again after an approval has a second Blocked entry and, once the
    user approves it, a second Approval entry: the last ones hold the question and the answer.
    """
    start = f"- **{label}:**"
    starts = [i for i, line in enumerate(block) if line.startswith(start)]
    return block_entry(block[starts[-1] :], label) if starts else []


def milestone(number: int) -> str:
    """Return how a message names a milestone the first time: its kind, ID and file (D1)."""
    return f"milestone M{number} in {PLAN_PATH}"


def milestone_at_start(number: int) -> str:
    """Return how a message that starts with a milestone names it (D1)."""
    return f"Milestone M{number} in {PLAN_PATH}"


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
        return f"The row of {milestone(row.id)} has no Model or no Effort."
    if row.model not in VALID_MODELS and not MODEL_ID.fullmatch(row.model):
        return (
            f"The Model '{row.model}' of {milestone(row.id)} is not one of "
            f"{', '.join(VALID_MODELS)} "
            "or a full model ID such as claude-sonnet-5-5."
        )
    if row.effort not in VALID_EFFORTS:
        efforts = ", ".join(VALID_EFFORTS)
        return f"The Effort '{row.effort}' of {milestone(row.id)} is not one of {efforts}."
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
    "(d) commit only the files this milestone changed, the tests of the test session too, in",
    "one commit with the message `M<n>: <title>`; do not push and do not merge: the runner",
    "does that;",
    "(e) if the pre-commit hook refuses the commit, fix the cause; never bypass the hook;",
    "(f) stop the milestone only if it needs a new or changed requirement in",
    "docs/spec.md, an action that CLAUDE.md 'Git and destructive actions' forbids, a new",
    "flow of user data to an external service, real user data, a secret in a committed",
    "file, a dependency that docs/design.md does not name in a Decided decision (use the",
    "standard library first; the check and test tools of the project, such as pytest,",
    "pytest-cov and hypothesis, are approved), or a change to a test in tests/ that you find",
    "wrong, and no",
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
    "(k) write and change files with the Edit and Write tools, not through the shell: a shell",
    "can write a file in another encoding than UTF-8;",
    "(l) end with the report in CLAUDE.md 'Communication and reporting'. In it, write each",
    "decision of (i) as its own line: `DECISION: <what> | <why> | <DEC-NNN or none>`.",
)
TEST_INTRO: Final = ("Run /write-tests for milestone M<n> (<title>) of docs/plan.md.",)
WRITER_TEST_INTRO: Final = (
    "Write the failing tests of milestone M<n> (<title>) of docs/plan.md, as AGENTS.md says.",
)
TEST_CONTEXT: Final = (
    "This is the test session (docs/workflow.md, Execute); a build session",
    "writes the code afterwards and may not change your tests.",
    "This folder holds no src/ and no .git, on purpose: the tests come from the spec and the",
    "design. The runner copies tests/ back to the project and checks them.",
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
    "user data, or a dependency that docs/design.md does not name in a Decided decision (the",
    "check and test tools of the project, such as pytest, pytest-cov, hypothesis and",
    "Playwright, are approved), and",
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
    "(g) write and change files with the file tools (Edit and Write), not through the shell;",
    "(h) end with the report of /write-tests. In it, write each decision of (c) as its own",
    "line: `DECISION: <what> | <why> | <DEC-NNN or none>`.",
)
TEST_FIX_INTRO: Final = (
    "The runner checked the tests of milestone M<n> (<title>) that you wrote, and found the",
    "problems below. Repair them in tests/. Each problem gives the type and the message of an",
    "error, and no line of the code. A new test may fail only because the behavior is",
    "missing: a wrong value (an AssertionError), or a missing module that the Owner entry of",
    "the milestone names. Each older test must pass.",
    "This is an unattended run: nobody can answer questions.",
)
REVIEW_TESTS_INTRO: Final = (
    "Repair the review findings about the tests of milestone M<n> (<title>).",
    "The code of the milestone is built. The review found faults in tests/, or a missing test.",
    "A missing test that you add may fail: a build session makes it pass afterwards.",
    "This folder holds no src/ and no .git, on purpose: the tests come from the spec and the",
    "design. The runner copies tests/ back to the project and checks them.",
    "This is an unattended run: nobody can answer questions.",
)
REVIEW_TESTS_RULES: Final = (
    "Rules:",
    "(a) commit nothing;",
    "(b) change only files under tests/. Never read the code in src/, also not through the",
    "shell;",
    "(c) write and change files with the file tools (Edit and Write), not through the shell;",
    "(d) never call a live external service. A test uses a real local part where one exists",
    "and a fake only for an external service;",
    "(e) end with one line for each finding: `REPAIRED: <finding>`, or",
    "`REJECTED: <finding> | <why>` for a finding that is wrong.",
)
WRONG_TEST_RULE: Final = (
    "(<x>) a test in tests/ that looks wrong is a blocker: do not change it, do not edit "
    "docs/plan.md, commit nothing, and end the report with one line "
    "`BLOCKED: <the test> | <why it looks wrong> | <the question for the user>`."
)
REBUILD_INTRO: Final = (
    "The tests of milestone M<n> (<title>) changed after the review: a test session repaired",
    "the review findings about the tests. Make the tests pass, and change no file in tests/.",
    "A new test that already passes needs no change of the code.",
    "Run the Gate: `python scripts/check.py` must pass. Then commit all the changes, the",
    "changed tests too, with the message `M<n>: test repairs`; do not push and do not",
    "merge: the runner does that.",
    "You work in the branch milestone/M<n>: stay on it.",
    "This is an unattended run: nobody can answer questions.",
)
REBUILD_RULES: Final = (
    "Rules:",
    "(a) never edit docs/spec.md, and do not change behavior that it states;",
    "(b) if the pre-commit hook refuses the commit, fix the cause; never bypass the hook;",
    "(c) a tool call that a settings rule denies is not allowed: do not retry it or work",
    "around it;",
    "(d) a public function that you add goes into Interfaces of docs/design.md as a decision:",
    "a DEC-NNN with the Status Proposed and 'auto-decided in M<n>, review' in its Why;",
    "(e) write and change files with the Edit and Write tools, not through the shell;",
    WRONG_TEST_RULE.replace("<x>", "f"),
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
    "<file> is the file where the fix goes: a finding about a test, or a missing test, names a",
    "file in tests/. A fault against a requirement that no test catches is a missing test:",
    "name the test file that must catch it, and write the requirement ID as the rule.",
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
    "around it;",
    "(i) a public function that you add goes into Interfaces of docs/design.md as a decision",
    "(a DEC-NNN with the Status Proposed and 'auto-decided in M<n>, review' in its Why), so",
    "that a test writer can test it from the design;",
    "(j) write and change files with the Edit and Write tools, not through the shell;",
    WRONG_TEST_RULE.replace("<x>", "k"),
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


def build_test_prompt(
    row: Row, resume: bool = False, reason: str = "", writer: str = WRITER_CLAUDE
) -> str:
    """Return the text sent to the test session; a try that resumes gets the retry notes.

    Claude runs /write-tests. Another writer reads the same rules in AGENTS.md.
    """
    intro = TEST_INTRO if writer == WRITER_CLAUDE else WRITER_TEST_INTRO
    notes = retry_notes(TEST_RESUME_NOTE, resume, reason)
    parts = (_fill(intro, row), _fill(TEST_CONTEXT, row), *notes, _fill(TEST_RULES, row))
    return " ".join(parts)


def fix_tests_prompt(
    row: Row, problems: Sequence[str], resume: bool = False, reason: str = ""
) -> str:
    """Return the text of the round of repair of a test session, with the problems of the checks.

    The round runs once, in the same folder, so it takes no retry notes (resume and reason).
    """
    del resume, reason
    intro = " ".join((_fill(TEST_FIX_INTRO, row), "The problems:"))
    return "\n".join((intro, *problems, _fill(TEST_RULES, row)))


def review_tests_prompt(
    row: Row, findings: Sequence[str], resume: bool = False, reason: str = ""
) -> str:
    """Return the text of the test session that repairs the review findings about the tests."""
    notes = retry_notes(TEST_RESUME_NOTE, resume, reason)
    intro = " ".join((_fill(REVIEW_TESTS_INTRO, row), *notes, "The findings:"))
    return "\n".join((intro, *findings, _fill(REVIEW_TESTS_RULES, row)))


def rebuild_prompt(row: Row, resume: bool = False, reason: str = "") -> str:
    """Return the text of the build session that runs after the review-tests session."""
    notes = retry_notes(RESUME_NOTE, resume, reason)
    return " ".join((_fill(REBUILD_INTRO, row), *notes, _fill(REBUILD_RULES, row)))


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
        Its program is a name: run_claude finds it on the PATH of the session.
    """
    return [
        "claude",
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


def writer_command(writer: Writer, row: Row, kind: str, prompt: str) -> tuple[list[str], str]:
    """Return the command of a test writer's session, and the text it reads on standard input.

    Each writer runs with its permission prompts off. Claude and Codex read the prompt on
    standard input; Antigravity and Copilot take it as an argument. The model ID of Antigravity
    holds its effort (gemini-4-neon-high), so the command does not repeat it.

    Args:
        writer: The test writer, with its model and effort (empty: the CLI's default).
        row: The milestone; Claude takes its model and effort when the writer names none.
        kind: The kind of the session, for the tools that Claude is denied.
        prompt: The text of the session.

    Returns:
        The command, and the text for standard input ("" when the prompt is an argument).
    """
    if writer.name == WRITER_CLAUDE:
        chosen = replace(row, model=writer.model or row.model, effort=writer.effort or row.effort)
        return session_command(chosen, kind), prompt
    program = WRITER_PROGRAMS[writer.name]
    model = ["--model", writer.model] if writer.model else []
    if writer.name == WRITER_CODEX:
        effort = ["-c", f"model_reasoning_effort={writer.effort}"] if writer.effort else []
        # --ignore-user-config drops the sandbox setting of Windows; without it, Codex refuses
        # every shell command and still ends with 0 (the trial of November 21, 2026).
        windows = ["-c", 'windows.sandbox="unelevated"'] if sys.platform == "win32" else []
        options = ["--sandbox", "workspace-write", "--skip-git-repo-check", "--ignore-user-config"]
        command = [program, "exec", *model, *effort, *options, "--ephemeral", *windows, "-"]
        return command, prompt
    if writer.name == WRITER_ANTIGRAVITY:
        return [program, "-p", prompt, *model, "--dangerously-skip-permissions"], ""
    effort = ["--effort", writer.effort] if writer.effort else []
    return [program, "-p", prompt, "--allow-all-tools", "--no-ask-user", *model, *effort], ""


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


# --- the test writer and its folder -------------------------------------------------------------


def load_writer(root: Path, override: str) -> Writer:
    """Return the test writer: config/test-writer.json, or Claude when the file is missing.

    Args:
        root: The repository root.
        override: The name that --test-writer gave, or "". Another writer than the file's takes
            the default model and effort of its CLI.

    Raises:
        RunStoppedError: If the name is not a known writer.
    """
    path = root / WRITER_FILE
    data = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    recorded = Writer(
        str(data.get("writer", WRITER_CLAUDE)),
        str(data.get("model", "")),
        str(data.get("effort", "")),
    )
    writer = recorded if override in {"", recorded.name} else Writer(override)
    if writer.name not in TEST_WRITERS:
        raise _error(
            f"The test writer '{writer.name}' is not one of {', '.join(TEST_WRITERS)}. "
            f"Correct {WRITER_FILE}, or choose one with --test-writer."
        )
    return writer


def new_folder(prefix: str) -> Path:
    """Make a new folder in the temporary folder of the system, with the usual permissions.

    `tempfile.mkdtemp` makes a folder that only the current user can open (also on Windows,
    since Python 3.12). The sandbox of a test writer can run as another user: in the second
    trial of the writers, Codex could not read such a folder.
    """
    folder = Path(tempfile.gettempdir()) / f"{prefix}{uuid.uuid4().hex[:12]}"
    folder.mkdir()
    return folder


def _copy_file(source: Path, target: Path) -> None:
    """Copy one file, and make its folder first."""
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)


def _is_cache(relative: Path) -> bool:
    """Tell whether a path is inside a cache folder (__pycache__, .pytest_cache and others)."""
    return any(part in CACHE_DIRS for part in relative.parts)


def _files_below(folder: Path) -> set[Path]:
    """Return the path of every file below a folder, from that folder, without the caches."""
    if not folder.is_dir():
        return set()
    found = (path.relative_to(folder) for path in folder.rglob("*") if path.is_file())
    return {relative for relative in found if not _is_cache(relative)}


def mirror_folder(source: Path, target: Path) -> None:
    """Make the files below target the same as the files below source, caches left out."""
    wanted, existing = _files_below(source), _files_below(target)
    for relative in existing - wanted:
        (target / relative).unlink()
    for relative in sorted(wanted):
        new = (source / relative).read_bytes()
        old = (target / relative).read_bytes() if relative in existing else None
        if new != old:
            _copy_file(source / relative, target / relative)


def _without_frontmatter(text: str) -> str:
    """Return a Markdown text without its `---` frontmatter."""
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            return text[end + 4 :].lstrip("\n")
    return text


def _one_level_down(text: str) -> str:
    """Return a Markdown text with each heading one level lower (`#` becomes `##`)."""
    return "\n".join(f"#{line}" if line.startswith("#") else line for line in _split_lines(text))


def agents_text(root: Path) -> str:
    """Return AGENTS.md for a test writer that is not Claude: the same rules in one file.

    It holds CLAUDE.md, every rules file and /write-tests of the project, under a short head.
    Codex, Antigravity and Copilot read AGENTS.md.
    """
    head = [
        "# AGENTS.md",
        "",
        "You write the tests of one milestone of this project. This folder holds the spec, the",
        "design, the plan, the rules, the tool configs and tests/. It holds no src/ and no",
        ".git, on purpose: the tests come from the spec and the design, not from the code.",
        "",
        "- Put every import at the top of a test file.",
        "- A ModuleNotFoundError for a module that the Owner entry of the milestone names is a",
        "  valid failure: that code does not exist yet.",
        "- Write and change files with your file tools, not through the shell.",
        "- Commit nothing. The runner copies tests/ back to the project and checks the tests.",
        "",
        "The rules below are the project's CLAUDE.md, its rules files and its skill /write-tests.",
    ]
    parts = ["\n".join(head)]
    sources = [root / "CLAUDE.md", *sorted((root / ".claude" / "rules").glob("*.md"))]
    sources.append(root / ".claude" / "skills" / "write-tests" / "SKILL.md")
    for source in (path for path in sources if path.is_file()):
        title = source.relative_to(root).as_posix()
        body = _without_frontmatter(source.read_text(encoding="utf-8-sig")).strip()
        parts.append(f"## {title}\n\n{_one_level_down(body)}")
    return "\n\n".join(parts) + "\n"


def make_test_folder(root: Path, writer: Writer) -> Path:
    """Make the folder of a test session outside the project: no src/ and no .git.

    It holds the docs, the scripts that check the tests, the tool configs, tests/ and the files
    that the writer reads: for Claude its CLAUDE.md, rules, settings and /write-tests, for the
    others one AGENTS.md. The caller deletes the folder.

    Returns:
        The path of the new folder.
    """
    folder = new_folder("sherpa-tests-")
    for name in FOLDER_FILES:
        if (root / name).is_file():
            _copy_file(root / name, folder / name)
    mirror_folder(root / "tests", folder / "tests")
    if writer.name == WRITER_CLAUDE:
        for name in CLAUDE_FOLDER_FILES:
            if (root / name).is_file():
                _copy_file(root / name, folder / name)
        for name in CLAUDE_FOLDER_DIRS:
            mirror_folder(root / name, folder / name)
    else:
        (folder / "AGENTS.md").write_text(agents_text(root), encoding="utf-8", newline="\n")
    return folder


def copy_back(folder: Path, root: Path) -> None:
    """Copy tests/ of the folder back to the project, and the plan and the design if they changed.

    Only these files come back: a change to the spec, or to any other file, stays in the folder.
    """
    mirror_folder(folder / "tests", root / "tests")
    for name in COPIED_BACK_DOCS:
        source, target = folder / name, root / name
        if source.is_file() and source.read_bytes() != target.read_bytes():
            _copy_file(source, target)


# --- the runner's checks of new tests ------------------------------------------------------------


def changed_test_files(root: Path, reference: str) -> list[str]:
    """Return the files under tests/ that differ from a commit: changed, added or removed.

    Args:
        root: The repository root.
        reference: The commit to compare with: the base branch for a test session, HEAD for the
            review-tests session.
    """
    diff = _git(root, "diff", "--name-only", reference, "--", "tests")
    new = _git(root, "ls-files", "--others", "--exclude-standard", "--", "tests")
    return sorted({*_output_lines(diff.stdout), *_output_lines(new.stdout)})


def _is_test_file(name: str) -> bool:
    """Tell whether a path is a Python test file that a normal run collects (not tests/live/)."""
    parts = Path(name).parts
    return Path(name).name.startswith("test_") and name.endswith(".py") and LIVE_DIR not in parts


def owner_modules(block: Sequence[str]) -> list[str]:
    """Return the dotted modules that the Owner entry of a block names, such as `src.store`."""
    text = " ".join(block_entry(block, "Owner"))
    names = (Path(path.rstrip("/.,;:`")) for path in OWNER_PATH.findall(text))
    return sorted({".".join(name.with_suffix("").parts) for name in names if name.parts})


def owned(module: str, owners: Sequence[str]) -> bool:
    """Tell whether a module is an Owner module, a module in one, or a package that holds one."""
    return any(
        module == owner or module.startswith(f"{owner}.") or owner.startswith(f"{module}.")
        for owner in owners
    )


def read_failures(report: Path) -> list[Failure]:
    """Return why each test of a JUnit XML report failed or could not run.

    The type of an error comes from the last `E   <Type>: <message>` line of its text, or from
    the last `<path>:<line>: <Type>` line, where pytest also names the file that raised it.
    """
    failures: list[Failure] = []
    for case in ElementTree.parse(report).getroot().iter("testcase"):
        for problem in [*case.iter("failure"), *case.iter("error")]:
            name = "::".join(filter(None, (case.get("classname"), case.get("name"))))
            failures.append(_failure(name, problem.get("message", ""), problem.text or ""))
    return failures


def _failure(test: str, message: str, text: str) -> Failure:
    """Build the Failure of one test from the message and the text of its report."""
    lines = _split_lines(text)
    fixture = MISSING_FIXTURE.search(f"{message}\n{text}")
    if fixture is not None:
        return Failure(test, "FixtureNotFound", f"fixture '{fixture[1]}' not found")
    raised = [match for match in map(RAISED_AT.match, lines) if match]
    errors = [match for match in map(EXCEPTION_LINE.match, lines) if match]
    kind = errors[-1][1] if errors else (raised[-1][2] if raised else "")
    detail = errors[-1][2] if errors else message
    if not kind and message.startswith("assert"):
        kind = VALID_FAILURE
    where = raised[-1][1].replace("\\", "/") if raised else ""
    return Failure(test, kind or "Error", detail.strip(), where)


def failure_problem(failure: Failure, owners: Sequence[str]) -> str | None:
    """Return why a failure of a new test is not valid, or None when it is valid.

    Valid: a wrong value (an AssertionError), an error that the code in src/ raised, or a missing
    module, name or attribute of a module that the Owner entry names. Anything else is a fault
    of the test: a syntax error, a missing fixture, a NameError or a TypeError in the test, an
    import of a missing test helper.
    """
    if failure.kind == VALID_FAILURE or failure.raised_in.startswith("src/"):
        return None
    missing = MISSING_MODULE.search(failure.message)
    module = next((name for name in missing.groups() if name), "") if missing else ""
    if failure.kind in IMPORT_FAILURES and module and owned(module, owners):
        return None
    return f"{failure.test}: {failure.kind}: {failure.message}"


def _tool_problem(command: Sequence[str], cwd: Path, title: str) -> list[str]:
    """Run a check tool; return its title and output when it fails, or no line when it passes."""
    done = _run(command, cwd)
    return [] if done.returncode == 0 else [f"{title} failed:", *_all_output(done)]


def lint_problems(folder: Path) -> list[str]:
    """Run ruff and mypy on tests/ in the folder without the code (a project with ruff.toml).

    mypy finds no module of the code there, so a test that imports the code is not an error.
    """
    if not (folder / "ruff.toml").is_file() or not (folder / "tests").is_dir():
        return []
    tool = [sys.executable, "-m"]
    return [
        *_tool_problem([*tool, "ruff", "check", "tests"], folder, "ruff check tests"),
        *_tool_problem([*tool, "ruff", "format", "--check", "tests"], folder, "ruff format"),
        *_tool_problem([*tool, "mypy", "tests", *MYPY_TEST_OPTIONS], folder, "mypy tests"),
    ]


def new_test_problems(root: Path, new: Sequence[str], owners: Sequence[str]) -> list[str]:
    """Run the new test files with --junitxml; return each failure whose reason is not valid."""
    if not new:
        return []
    with tempfile.TemporaryDirectory() as scratch:
        report = Path(scratch) / "new-tests.xml"
        command = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"]
        done = _run([*command, f"--junitxml={report}", *new], root)
        if not report.is_file():
            return ["pytest did not run the new tests:", *_all_output(done)[-TAIL_LINES:]]
        failures = read_failures(report)
    problems = (failure_problem(failure, owners) for failure in failures)
    return [problem for problem in problems if problem is not None]


def old_test_problems(root: Path, new: Sequence[str]) -> list[str]:
    """Run every older test file; return the end of the output when one fails."""
    tests = root / "tests"
    every = (path.relative_to(root).as_posix() for path in tests.rglob("test_*.py"))
    old = sorted(name for name in every if _is_test_file(name) and name not in new)
    if not old:
        return []
    done = _run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", *old], root)
    if done.returncode in {0, PYTEST_NO_TESTS}:
        return []
    return [
        "An older test fails, and every older test must pass:",
        *_all_output(done)[-TAIL_LINES:],
    ]


def written_tests_problems(check: TestsCheck) -> list[str]:
    """Return the problems of the tests that a writer session left, after the copy back.

    The runner judges a test session only by these checks, never by the exit code of the
    writer: ruff and mypy on tests/ in the folder, then in the project each new test file with
    the reason of each failure, and each older test file, which must pass.
    """
    changed = changed_test_files(check.root, check.reference)
    if check.needs_tests and not changed:
        return ["The test session wrote no test: tests/ is the same as before."]
    new = [name for name in changed if _is_test_file(name) and (check.root / name).is_file()]
    return [
        *lint_problems(check.folder),
        *new_test_problems(check.root, new, check.owners),
        *old_test_problems(check.root, new),
    ]


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
    add_chat_options(parser)
    args = parser.parse_args(argv)
    check_options(parser, args)
    return Options(
        start=args.start,
        end=args.end,
        retries=args.retries,
        resume=args.resume,
        timeout_minutes=args.timeout_minutes,
        tests_only=milestone_number(parser, args.tests_only),
        review_only=milestone_number(parser, args.review_only),
        review_findings=args.review_findings,
        test_writer=args.test_writer,
    )


def check_options(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    """Refuse options that do not go together; argparse prints the message and exits with 2."""
    if args.retries < 0:
        parser.error("--retries must be 0 or more.")
    if args.timeout_minutes < 1:
        parser.error("--timeout-minutes must be 1 or more.")
    one = args.tests_only or args.review_only
    if one is not None and (args.start is not None or args.end is not None or args.resume):
        parser.error("--tests-only and --review-only take no --start, --end or --resume.")
    if args.review_findings and args.tests_only is None:
        parser.error("--review-findings needs --tests-only.")


def add_chat_options(parser: argparse.ArgumentParser) -> None:
    """Add the options of one step in chat (docs/workflow.md, Execute), and the test writer."""
    steps = parser.add_mutually_exclusive_group()
    steps.add_argument(
        "--tests-only",
        metavar="M<n>",
        help="run only the test session of the milestone, in the current branch",
    )
    steps.add_argument(
        "--review-only",
        metavar="M<n>",
        help="run only the review of the milestone, in a worktree of HEAD",
    )
    parser.add_argument(
        "--review-findings",
        action="store_true",
        help="with --tests-only: repair the findings about tests of the last --review-only",
    )
    parser.add_argument(
        "--test-writer",
        default="",
        choices=["", *TEST_WRITERS],
        help=f"the AI that writes the tests (default: {WRITER_FILE}, else claude)",
    )


def milestone_number(parser: argparse.ArgumentParser, value: str | None) -> int | None:
    """Return the number of a milestone given as M<n> or <n>, or None when it was not given."""
    if value is None:
        return None
    match = re.fullmatch(r"[Mm]?(\d+)", value.strip())
    if match is None:
        parser.error(f"'{value}' is not a milestone such as M3.")
    return int(match[1])


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


def _run(
    args: Sequence[str], cwd: Path, environment: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    """Run a command in the repository and return its result, or stop the run if it cannot start.

    The command gets no input, so it cannot take the answer that the user types for a human test.
    environment None means the environment of the runner.
    """
    try:
        return subprocess.run(
            list(args),
            cwd=cwd,
            env=environment,
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


def environment_folders(prefix: Path) -> list[Path]:
    """Return the folders of a conda environment that `conda activate` puts first on the PATH."""
    if sys.platform != "win32":
        return [prefix / "bin"]
    library = prefix / "Library"
    return [
        prefix,
        library / "mingw-w64" / "bin",
        library / "usr" / "bin",
        library / "bin",
        prefix / "Scripts",
        prefix / "bin",
    ]


def session_environment() -> dict[str, str]:
    """Return the environment of each session: the folders of this conda environment come first.

    So a session, and the shells of a test writer, find the Python, the tools and the packages
    of the project's environment, also when the terminal that started the runner did not
    activate it.
    """
    folders = [str(folder) for folder in environment_folders(Path(sys.prefix))]
    path = os.pathsep.join([*folders, os.environ.get("PATH", "")])
    return {**os.environ, "PATH": path}


def check_session_python(environment: dict[str, str]) -> None:
    """Check that `python` on the PATH of a session is the Python of this environment.

    Raises:
        RunStoppedError: If `python` is not found, or it runs from another environment.
    """
    python = shutil.which("python", path=environment["PATH"])
    found = ""
    if python is not None:
        done = _run([python, "-c", "import sys; print(sys.prefix)"], Path.cwd(), environment)
        found = done.stdout.strip()
    if not found or Path(found).resolve() != Path(sys.prefix).resolve():
        raise _error(
            f"`python` on the PATH of a session runs from '{found or 'nowhere'}', not from the "
            f"conda env '{ENV_NAME}' ({sys.prefix}). Activate the environment, then run again."
        )


def check_writer(root: Path, writer: Writer, environment: dict[str, str]) -> None:
    """Send one short prompt to a test writer that is not Claude, before the first milestone.

    A missing sign-in, a missing program or an unknown model stops the run here, not in the
    first test session. The answer must hold the word "ok": the exit code alone proves nothing.

    Raises:
        RunStoppedError: If the writer did not answer with "ok".
    """
    if writer.name == WRITER_CLAUDE:
        return
    row = Row(0, "start check", "", "", "open")
    command, stdin = writer_command(writer, row, SESSION_TEST, START_CHECK_PROMPT)
    with tempfile.TemporaryDirectory() as folder:
        run = _claude_process(
            Launch(command, Path(folder), stdin, environment), START_CHECK_SECONDS
        )
    if "ok" not in " ".join(run.lines).lower():
        raise RunStoppedError(
            f"ERROR: the test writer {writer.name} did not answer the start check. "
            f"Sign in once ({WRITER_SIGN_IN[writer.name]}), check the model in {WRITER_FILE}, "
            "or choose another writer with --test-writer:",
            [" ".join(command[:2]), *run.lines[-TAIL_LINES:]],
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


def planned_cells(row: Row) -> tuple[str, ...]:
    """Return the cells of the table row of a milestone that has not started."""
    return (f"M{row.id}", row.title, row.model, row.effort, "-", "-", "-", OUTCOME_PLANNED)


def planned_rows(state: RunState) -> list[Row]:
    """Return the rows of the range that neither finished nor run now, in table order."""
    started = {result.id for result in state.results}
    if state.running is not None:
        started.add(state.running.row.id)
    return [row for row in state.planned if row.id not in started]


def total_cells(state: RunState) -> tuple[str, ...]:
    """Return the cells of the Total row: the total time under Duration, `Total` to its left."""
    cells = [""] * len(TABLE_HEADER)
    cells[DURATION_COLUMN - 1] = "Total"
    cells[DURATION_COLUMN] = format_duration(state.stopwatch.elapsed())
    return tuple(cells)


def progress_line(state: RunState, inner_width: int) -> str:
    """Return the last line of the table: a bar over its width, then "71%  5/7".

    The bar counts only the milestones that finished with the outcome done.
    """
    done = state.done_count()
    right = f"{percent(done, state.total)}%  {done}/{state.total}"
    width = max(inner_width - 3 - len(right), 1)
    filled = round(width * done / state.total) if state.total > 0 else 0
    return "│ " + BAR_DONE * filled + BAR_OPEN * (width - filled) + " " + right + " │"


def table_lines(state: RunState, console: Console, max_width: int) -> list[str]:
    """Return the table of this run: the finished milestones, the running one, the planned ones.

    The planned rows are very dark grey. Under them come a Total row with the total time, and a
    row with a progress bar.

    Args:
        state: The results so far, the milestone that runs now, the planned rows, the total timer
            and the total.
        console: Paints each row in the color of its outcome.
        max_width: The most characters of a line; a longer Title is cut.

    Returns:
        The lines of the table, from its top border to its bottom border.
    """
    records = [(result_cells(result), outcome_color(result.outcome)) for result in state.results]
    if state.running is not None:
        records.append((running_cells(state.running), outcome_color(OUTCOME_RUNNING)))
    records += [(planned_cells(row), "grey") for row in planned_rows(state)]
    total = total_cells(state)
    widths = column_widths([TABLE_HEADER, total, *(cells for cells, _ in records)], max_width)
    inner_width = sum(width + 2 for width in widths) + len(widths) - 1
    return [
        border_line(widths, "┌", "┬", "┐"),
        row_line(TABLE_HEADER, widths),
        border_line(widths, "├", "┼", "┤"),
        *(console.paint(row_line(cells, widths), color) for cells, color in records),
        border_line(widths, "├", "┼", "┤"),
        row_line(total, widths),
        border_line(widths, "├", "┴", "┤"),
        progress_line(state, inner_width),
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


def found_program(command: Sequence[str], environment: dict[str, str]) -> list[str]:
    """Return the command with the full path of its program, found on the PATH of the session."""
    program = shutil.which(command[0], path=environment.get("PATH")) or command[0]
    return [program, *command[1:]]


def _claude_process(launch: Launch, timeout: float) -> ClaudeRun:
    """Run a session with its prompt on standard input; a run over `timeout` seconds is cut off.

    A writer that takes its prompt as an argument gets an empty standard input.
    """
    command = found_program(launch.command, launch.environment or {})
    try:
        done = subprocess.run(
            command,
            cwd=launch.folder,
            env=launch.environment,
            input=launch.stdin,
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
            f"[runner] the session was stopped after {timeout / 60:.0f} minutes.",
        ]
        return ClaudeRun(lines, TIMEOUT_EXIT_CODE, timed_out=True)
    except OSError as exc:
        raise _error(f"`{command[0]}` could not run: {exc}") from exc
    return ClaudeRun(_output_lines(done.stdout), done.returncode)


def log_file_name(row: Row, kind: str, number: int) -> str:
    """Return the log name of a try: M<n>.log for a build session, M<n>-<kind>.log for the others.

    A retry gets -<try> before the extension, such as M3-review-2.log.
    """
    stem = f"M{row.id}" if kind == SESSION_BUILD else f"M{row.id}-{kind}"
    return f"{stem}.log" if number == 1 else f"{stem}-{number}.log"


def write_log(paths: Paths, name: str, lines: Sequence[str]) -> None:
    """Write the lines of a session to its log in .claude/logs/."""
    paths.log_dir.mkdir(parents=True, exist_ok=True)
    (paths.log_dir / name).write_text("".join(f"{line}\n" for line in lines), encoding="utf-8")


def run_claude(session: Session, row: Row, attempt: Attempt, job: Job) -> ClaudeRun:
    """Run one try of one session of a milestone and save its output to its log.

    Args:
        session: The run: its files and the environment of the sessions.
        row: The milestone; its model and effort go to claude.
        attempt: Which try this is, whether it resumes earlier work, its time limit, and why the
            earlier try did not count.
        job: The session: its kind, its prompt, its folder and its writer.

    Returns:
        The output lines (standard output and error together), the exit code and the log name.

    Raises:
        RunStoppedError: If the program of the session cannot be found or started.
    """
    prompt = job.prompt(attempt.resume, attempt.reason)
    if job.writer is None:
        command, stdin = session_command(row, job.kind), prompt
    else:
        command, stdin = writer_command(job.writer, row, job.kind, prompt)
    launch = Launch(command, job.folder or session.paths.root, stdin, session.environment or None)
    run = _claude_process(launch, attempt.timeout_seconds)
    log_name = log_file_name(row, job.kind, attempt.number)
    write_log(session.paths, log_name, run.lines)
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


def judge_review(run: ClaudeRun) -> Verdict:
    """Return done for a review that ended well; failed, with why, if it did not.

    The review runs in a worktree of its own, so a change that it makes cannot reach the branch.
    """
    reason = None
    if run.timed_out:
        reason = "the review session ran over the time limit."
    elif run.exit_code != 0:
        reason = f"the review session ended with exit code {run.exit_code}."
    return Verdict(OUTCOME_DONE, "") if reason is None else Verdict(OUTCOME_FAILED, reason)


def judge_repair(session: Session, running: Running, kind: str, run: ClaudeRun) -> Verdict:
    """Return the verdict of a repair or rebuild session: blocked, done or failed.

    Blocked: its report has a `BLOCKED:` line (a test that looks wrong); the line is the question
    of the block. Done: git is clean and the runner's own checks pass. The exit code does not
    count. A repair that commits nothing, because it rejected every finding, is done.
    """
    blocked = blocked_lines(run.lines)
    if blocked:
        running.blocking = blocked
        return Verdict(OUTCOME_BLOCKED, f"the {kind} session found a test that looks wrong.")
    return work_verdict(session, running, kind)


def blocked_lines(lines: Sequence[str]) -> list[str]:
    """Return the lines of a report that block the milestone (`BLOCKED: ...`)."""
    return [line.strip() for line in lines if re.match(r"^\W*BLOCKED:", line.strip())]


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


def claude_try(session: Session, row: Row, job: Job, attempt: Attempt) -> tuple[ClaudeRun, Verdict]:
    """Run one try of a session in the project, and judge it."""
    run = run_claude(session, row, attempt, job)
    return run, judge_try(session, row, job, run)


def build_job(session: Session, running: Running) -> Job:
    """Return the build session of the milestone."""
    prompt = partial(build_prompt, running.row)
    return Job(SESSION_BUILD, prompt, partial(judge_build, session, running))


def rebuild_job(session: Session, running: Running) -> Job:
    """Return the build session that makes the tests pass after the review-tests session."""
    prompt = partial(rebuild_prompt, running.row)
    return Job(SESSION_REBUILD, prompt, partial(judge_repair, session, running, SESSION_REBUILD))


def decision_note(running: Running) -> list[str]:
    """Return the line that gives a repair the user's decision on an earlier block, if any."""
    if not running.decision:
        return []
    return [f"The user's decision on an earlier review: {' '.join(running.decision)}"]


def repair_job(session: Session, running: Running, findings: Sequence[str]) -> Job:
    """Return the repair session of the milestone, for the FINDING lines about the code."""
    prompt = partial(repair_prompt, running.row, [*decision_note(running), *findings])
    return Job(SESSION_REPAIR, prompt, partial(judge_repair, session, running, SESSION_REPAIR))


# --- the test session ----------------------------------------------------------------------------


@dataclass(frozen=True)
class WriterTask:
    """One session of the test writer: its kind, its prompt, and how its tests are checked.

    prompt takes the resume flag and the reason of the earlier try. reference is the commit that
    the new tests are compared with. blocks tells whether the session may block the milestone.
    folder is the folder of the writer, once writer_try made it.
    """

    kind: str
    prompt: Callable[[bool, str], str]
    reference: str
    blocks: bool
    folder: Path = field(default_factory=Path)


def writer_job(kind: str, prompt: Callable[[bool, str], str], folder: Path, writer: Writer) -> Job:
    """Return a session of the test writer in its folder.

    The runner judges it by its own checks of the tests (writer_try), so the judge of the job
    only looks at the time limit and the exit code, and nothing reads that verdict.
    """
    return Job(kind, prompt, judge_review, folder, writer)


def merged_run(first: ClaudeRun, second: ClaudeRun) -> ClaudeRun:
    """Return one run with the lines of two sessions; the second one gives the exit and the log."""
    return replace(second, lines=[*first.lines, *second.lines])


def writer_try(
    session: Session, running: Running, task: WriterTask, attempt: Attempt
) -> tuple[ClaudeRun, Verdict]:
    """Run one try of a test writer's session in a folder without the code, and judge it.

    The folder exists for this try only. The exit code of the writer never counts.
    """
    folder = make_test_folder(session.paths.root, session.writer)
    try:
        return writer_rounds(session, running, replace(task, folder=folder), attempt)
    finally:
        shutil.rmtree(folder, ignore_errors=True)


def writer_rounds(
    session: Session, running: Running, task: WriterTask, attempt: Attempt
) -> tuple[ClaudeRun, Verdict]:
    """Run the writer in its folder, copy tests/ back, check them, and give one round of repair.

    Returns:
        The run (the lines of both rounds), and the verdict: blocked, done, or failed with the
        problems that are left.
    """
    root, row = session.paths.root, running.row
    job = writer_job(task.kind, task.prompt, task.folder, session.writer)
    run = run_claude(session, row, attempt, job)
    copy_back(task.folder, root)
    if task.blocks and is_blocked(session.paths, row):
        return run, blocked_verdict(session)
    owners = tuple(owner_modules(running.block))
    check = TestsCheck(root, task.folder, task.reference, owners, task.blocks)
    problems = written_tests_problems(check)
    if problems and not run.timed_out:
        fix = writer_job(
            SESSION_TEST_FIX, partial(fix_tests_prompt, row, problems), task.folder, session.writer
        )
        run = merged_run(run, run_claude(session, row, replace(attempt, resume=False), fix))
        copy_back(task.folder, root)
        problems = written_tests_problems(check)
    return run, writer_verdict(task.kind, run, problems)


def writer_verdict(kind: str, run: ClaudeRun, problems: Sequence[str]) -> Verdict:
    """Return the verdict of a writer's session: the time limit, then the problems that are left."""
    if run.timed_out:
        return Verdict(OUTCOME_FAILED, f"the {kind} session ran over the time limit.")
    if problems:
        return Verdict(
            OUTCOME_FAILED, "the runner's checks of the tests failed: " + " ".join(problems)
        )
    return Verdict(OUTCOME_DONE, "")


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
    problem = rebase_on(root, base, row)
    if problem is not None:
        details = [
            f"Rebase it by hand: git rebase {base} {branch}",
            "Keep the message of its last commit, then run the runner again.",
            *problem,
        ]
        raise RunStoppedError(
            f"ERROR: the partial work of {milestone(row.id)} does not apply on {base}.", details
        )
    _git_must(root, "reset", "--mixed", base)


def plan_without_milestone(lines: Sequence[str], milestone_id: int) -> list[str]:
    """Return the plan without the milestone's row and its `### M<n>` block, as a build commit."""
    kept: list[str] = []
    inside = False
    for line in lines:
        if re.match(r"^#{1,3} ", line):
            inside = re.match(rf"^### M{milestone_id}\b", line) is not None
        row = parse_row(line)
        if not inside and (row is None or row.id != milestone_id):
            kept.append(line)
    return kept


def rebase_built(root: Path, base: str, row: Row) -> None:
    """Rebase a built milestone branch on the base branch, after the user approved its block.

    The base branch has the commit `M<n>: blocked` and the approval. They change the row and the
    block of the milestone, which the build commit deleted, so docs/plan.md conflicts. The
    runner takes the plan of the base branch without the milestone, as the build commit means.

    Raises:
        RunStoppedError: If another file conflicts. The rebase is aborted first.
    """
    branch = branch_name(row.id)
    problem = rebase_on(root, base, row)
    if problem is not None:
        details = [f"Rebase it by hand: git rebase {base} {branch}", *problem]
        raise RunStoppedError(
            f"ERROR: the branch {branch} of {milestone(row.id)} does not apply on {base}.",
            details,
        )


def rebase_on(root: Path, base: str, row: Row) -> list[str] | None:
    """Rebase the milestone branch on the base branch; a conflict of docs/plan.md is resolved.

    The plan conflicts when the base branch changed the row and the block of the milestone (a
    block and its approval) and the build commit deleted them. The runner then takes the plan
    of the base branch without the milestone, as the build commit means.

    Returns:
        None when the rebase finished, or the output of git when another file conflicts. The
        rebase is aborted first.
    """
    done = _git(root, "rebase", base)
    while done.returncode != 0:
        conflicts = _output_lines(_git(root, "diff", "--name-only", "--diff-filter=U").stdout)
        if conflicts != [PLAN_PATH]:
            _git(root, "rebase", "--abort")
            return _all_output(done)
        ours = _git(root, "show", f":2:{PLAN_PATH}").stdout
        plan = plan_without_milestone(_split_lines(ours), row.id)
        (root / PLAN_PATH).write_text("\n".join(plan), encoding="utf-8", newline="\n")
        _git_must(root, "add", PLAN_PATH)
        done = _git(root, "-c", "core.editor=true", "rebase", "--continue")
    return None


def add_worktree(root: Path) -> Path:
    """Add a worktree of HEAD outside the project, for one review. The caller removes it."""
    folder = new_folder("sherpa-review-") / "tree"
    _git_must(root, "worktree", "add", "--detach", str(folder), "HEAD")
    return folder


def remove_worktree(root: Path, folder: Path, head: str) -> list[str]:
    """Remove a review worktree and its folder.

    Returns:
        One warning line when the review changed a file or made a commit there, else no line.
    """
    changed = bool(_git(folder, "status", "--porcelain").stdout.strip())
    moved = git_head(folder) != head
    _git(root, "worktree", "remove", "--force", str(folder))
    shutil.rmtree(folder.parent, ignore_errors=True)
    _git(root, "worktree", "prune")
    if not changed and not moved:
        return []
    return ["[runner] WARNING: the review changed its worktree. The runner deleted the changes."]


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
        if row.status == STATUS_APPROVED and commits_ahead(root, branch, base) > 0:
            rebase_built(root, base, row)
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
        f"ERROR: {milestone(row.id)} is not merged: git merge --ff-only {branch} failed.", details
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
    return RunStoppedError(f"ERROR: {milestone(row.id)} is merged, but git push failed.", details)


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
        f"{milestone_at_start(row.id)} waits for your approval. Add an Approval entry to "
        "its block, set its Status to `approved`, commit, and run again:"
    )
    return RunStoppedError(message, milestone_block(plan_lines, row.id), "yellow")


def blocked_plan_refused(
    base: str, row: Row, step: str, done: subprocess.CompletedProcess[str]
) -> RunStoppedError:
    """Build the stop for a blocked plan that git did not commit or push on the base branch.

    Args:
        base: The base branch.
        row: The blocked milestone.
        step: The git command that failed: `commit` (the pre-commit hook refused it) or `push`.
        done: The result of that command.

    Returns:
        The stop: where the work is, how to finish the step by hand, then the output of git.
    """
    commit = f'git commit -m "M{row.id}: blocked"'
    finish = f"{commit}, and then: git push" if step == "commit" else "git push"
    state = "staged and not committed" if step == "commit" else "committed and not pushed"
    details = [
        f"The work of M{row.id} is safe in the branch {branch_name(row.id)}.",
        f"{PLAN_PATH} with the blocked row is {state} on {base}.",
        f"Correct the cause that the output below names. Then run: {finish}",
        f"Then answer the question of M{row.id}: add an Approval entry to its block in "
        f"{PLAN_PATH}, set its Status to `approved`, commit, and run the runner again.",
        *_all_output(done),
    ]
    return RunStoppedError(
        f"ERROR: {milestone(row.id)} is blocked, but `git {step}` failed on {base}.", details
    )


def block_milestone(session: Session, row: Row) -> NoReturn:
    """Do the git work of a milestone that a session blocked, then stop the run with its question.

    The session changed the plan and committed nothing. The plan goes back to its committed state
    in the milestone branch, and the other changes are committed there as `M<n>: partial work`,
    with --no-verify: the hook checks the base branch, not this branch. The blocked plan is
    committed alone on the base branch as `M<n>: blocked`, through the hook, and pushed.

    Raises:
        RunStoppedError: Always. It carries the question of the milestone, or a git failure. When
            the commit or the push of the plan fails, it says how to finish that step by hand.
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
    for step in (("commit", "-m", f"M{row.id}: blocked"), ("push",)):
        done = _git(root, *step)
        if done.returncode != 0:
            raise blocked_plan_refused(session.base, row, step[0], done)
    raise waiting_for_approval(_read_lines(paths.plan), row)


def finding_cells(finding: str) -> list[str]:
    """Return the cells of a FINDING line: severity, file and line, rule, remedy."""
    text = re.sub(r"^\W*FINDING:", "", finding.strip())
    return [cell.strip(" *`") for cell in text.split("|")]


def finding_file(finding: str) -> str:
    """Return the file that a FINDING line names, with forward slashes."""
    cells = finding_cells(finding)
    return cells[FILE_CELL].split(":")[0].replace("\\", "/") if len(cells) > FILE_CELL else ""


def is_test_finding(finding: str) -> bool:
    """Tell whether the fix of a finding goes into tests/: then a test session repairs it."""
    return finding_file(finding).startswith("tests/")


def blocks_merge(finding: str) -> bool:
    """Tell whether a finding of the last review blocks the merge (RUN-09).

    A high finding blocks, and so does a medium finding whose rule is a requirement ID. A low
    finding never blocks: the review skill gives low to a small loss of readability only.
    """
    cells = finding_cells(finding)
    severity = cells[0].lower() if cells else ""
    rule = cells[RULE_CELL] if len(cells) > RULE_CELL else ""
    on_requirement = REQUIREMENT_RULE.match(rule) is not None
    return severity == SEVERITY_HIGH or (severity == SEVERITY_MEDIUM and on_requirement)


def requirement_note(finding: str) -> str:
    """Return " (requirement X in docs/spec.md)" when the rule of a finding is a requirement ID."""
    cells = finding_cells(finding)
    match = REQUIREMENT_RULE.match(cells[RULE_CELL]) if len(cells) > RULE_CELL else None
    return f" (requirement {match[0]} in docs/{SPEC_FILE})" if match else ""


def review_block_entry(findings: Sequence[str]) -> list[str]:
    """Return the Blocked entry of a milestone that the review stage stopped, in the template.

    The lines are FINDING lines of the last review, or the BLOCKED line of a repair or rebuild
    session that found a test that looks wrong.
    """
    from_review = all("FINDING:" in finding for finding in findings)
    reason = (
        "The last review found a fault that blocks the merge (docs/workflow.md, Execute, step 9)."
        if from_review
        else "A session after the review found a test that looks wrong (docs/workflow.md, step 5)."
    )
    return [
        f"- **Blocked:** {reason}",
        *(f"  - {finding}{requirement_note(finding)}" for finding in findings),
        "  - The code and the tests are kept in the milestone branch. To continue, approve one "
        "of these:",
        "    1. Merge it as it is: the finding is wrong, or it can wait."
        if from_review
        else "    1. Keep the test as it is: the code must pass it.",
        "    2. Repair it in this way: <your instruction>.",
    ]


def plan_with_block(lines: Sequence[str], milestone_id: int, entry: Sequence[str]) -> list[str]:
    """Return the plan with the milestone's Status blocked and the entry at the end of its block."""
    out = [
        re.sub(r"\|[^|]*\|\s*$", f"| {STATUS_BLOCKED} |", line)
        if (row := parse_row(line)) is not None and row.id == milestone_id
        else line
        for line in lines
    ]
    heading = next(i for i, line in enumerate(out) if re.match(rf"^### M{milestone_id}\b", line))
    end = next((i for i in range(heading + 1, len(out)) if re.match(r"^#{1,3} ", out[i])), len(out))
    while end > heading + 1 and not out[end - 1].strip():
        end -= 1
    return [*out[:end], *entry, *out[end:]]


def block_after_review(session: Session, running: Running) -> NoReturn:
    """Block a milestone that the last review stopped, then stop the run with its question.

    The milestone branch keeps the build and its repairs, committed. Work that a session left
    uncommitted goes into a commit `M<n>: partial work` (with --no-verify), and docs/plan.md goes
    back to its committed state. On the base branch the runner sets the Status of the row to
    blocked, adds the Blocked entry with the lines that block the merge, commits `M<n>: blocked`
    through the hook, and pushes.

    Raises:
        RunStoppedError: Always. It carries the question, or how to finish a failed commit or push.
    """
    paths, root, row = session.paths, session.paths.root, running.row
    _git_must(root, "checkout", "HEAD", "--", PLAN_PATH)
    if not git_is_clean(root):
        _git_must(root, "add", "-A")
        _git_must(root, "commit", "--no-verify", "-m", f"M{row.id}: {PARTIAL_WORK}")
    _git_must(root, "checkout", session.base)
    entry = review_block_entry(running.blocking)
    plan = plan_with_block(_read_lines(paths.plan), row.id, entry)
    paths.plan.write_text("\n".join(plan), encoding="utf-8", newline="\n")
    _git_must(root, "add", PLAN_PATH)
    for step in (("commit", "-m", f"M{row.id}: blocked"), ("push",)):
        done = _git(root, *step)
        if done.returncode != 0:
            raise blocked_plan_refused(session.base, row, step[0], done)
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
    raise RunStoppedError(f"{milestone_at_start(row.id)} stopped: {verdict.reason}", [*tail, hint])


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


def review_decision(session: Session, row: Row) -> tuple[str, ...]:
    """Return the Approval entry of a milestone that the user approved after its review stage.

    The block came from the last review (FINDING lines) or from a session after the review that
    found a test that looks wrong (a BLOCKED line). No lines for any other milestone.
    """
    blocked = approved_block(session, row)
    if not any("FINDING:" in line or "BLOCKED:" in line for line in blocked):
        return ()
    block = milestone_block(base_plan_lines(session.paths.root, session.base), row.id)
    return tuple(last_block_entry(block, "Approval"))


def approved_block(session: Session, row: Row) -> list[str]:
    """Return the last Blocked entry of an approved milestone in the base plan; no lines if none."""
    if row.status != STATUS_APPROVED:
        return []
    block = milestone_block(base_plan_lines(session.paths.root, session.base), row.id)
    return last_block_entry(block, "Blocked")


def retests(session: Session, row: Row, decision: Sequence[str]) -> bool:
    """Tell whether an approved block came from a session that found a test that looks wrong."""
    return bool(decision) and any("BLOCKED:" in line for line in approved_block(session, row))


def approved_findings(session: Session, row: Row, decision: Sequence[str]) -> tuple[str, ...]:
    """Return the FINDING lines of an approved block by the last review; none for another block."""
    if not decision:
        return ()
    blocked = approved_block(session, row)
    return tuple(line[line.index("FINDING:") :].strip() for line in blocked if "FINDING:" in line)


def run_attempts(
    session: Session,
    running: Running,
    try_once: Callable[[Attempt], tuple[ClaudeRun, Verdict]],
    resume: bool = False,
) -> tuple[ClaudeRun, Verdict]:
    """Run one session of the milestone, with the live table, until it is done or blocked.

    A try that did not finish is repeated, as a resume, up to `--retries` times. The prompt of
    the new try gets the reason of the verdict. The table shows a retry in the Result column of
    the running row.
    """
    number, reason = 1, ""
    running.attempt = number
    while True:
        attempt = Attempt(number, resume, session.options.timeout_minutes * 60, reason)
        with LiveTable(session.console, lambda: current_table(session)):
            run, verdict = try_once(attempt)
        if verdict.outcome != OUTCOME_FAILED or number > session.options.retries:
            return run, verdict
        number, resume, reason = number + 1, True, verdict.reason
        running.attempt = number


def run_claude_session(
    session: Session, running: Running, job: Job, resume: bool = False
) -> tuple[ClaudeRun, Verdict]:
    """Run a claude session of the milestone in the project, with its retries."""
    return run_attempts(session, running, partial(claude_try, session, running.row, job), resume)


def run_test_session(session: Session, running: Running, resume: bool) -> tuple[ClaudeRun, Verdict]:
    """Read the milestone's block, run the test session, then save it with the hashes of tests/.

    The test writer works in a folder without the code (writer_try). The old hashes file is
    deleted first, so the file exists only after a test session finished.
    """
    paths, row = session.paths, running.row
    running.block = milestone_block(_read_lines(paths.plan), row.id)
    paths.tests_file(row.id).unlink(missing_ok=True)
    prompt = partial(build_test_prompt, row, writer=session.writer.name)
    task = WriterTask(SESSION_TEST, prompt, session.base, blocks=True)
    run, verdict = run_attempts(
        session, running, partial(writer_try, session, running, task), resume
    )
    running.decisions += len(decision_lines(run.lines))
    if verdict.outcome == OUTCOME_DONE:
        running.saved = SavedTests(running.block, snapshot_tests(paths.root))
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
        running: The milestone. Its `saved`, `block` and `decisions` are filled in.
        entry: ENTRY_FRESH runs both sessions. ENTRY_RESUME skips the test session when the
            hashes file of the milestone exists. ENTRY_BUILT runs no session: the build commit
            exists, and only the runner's own checks judge it.

    Returns:
        The run of the last session (an empty run for ENTRY_BUILT), and its verdict.
    """
    paths, row = session.paths, running.row
    resume = entry != ENTRY_FRESH
    running.saved = load_tests(paths.tests_file(row.id)) if resume else None
    if running.saved is not None:
        running.block = list(running.saved.block)
    if entry == ENTRY_BUILT:
        return ClaudeRun([], 0), built_verdict(session, running)
    build_resumes = running.saved is not None
    run, verdict = tests_before_build(session, running, resume)
    if verdict.outcome != OUTCOME_DONE:
        return run, verdict
    run, verdict = run_claude_session(session, running, build_job(session, running), build_resumes)
    running.decisions += len(decision_lines(run.lines))
    return run, verdict


def tests_before_build(
    session: Session, running: Running, resume: bool
) -> tuple[ClaudeRun, Verdict]:
    """Run the test session when its tests are not saved yet, or the retest of an approval."""
    if running.saved is None:
        return run_test_session(session, running, resume)
    if running.retest:
        return retest(session, running)
    return ClaudeRun([], 0), Verdict(OUTCOME_DONE, "")


def retest(session: Session, running: Running) -> tuple[ClaudeRun, Verdict]:
    """Give the user's decision on a test that looked wrong to a test session, before the build.

    The milestone was blocked after its review because a session found a test that looks wrong,
    and the user approved a way on. Only a test session may change tests/, so it gets the
    decision, then the runner saves the new hashes of tests/.
    """
    root, row = session.paths.root, running.row
    decision = [f"The user's decision on the test that looked wrong: {' '.join(running.decision)}"]
    prompt = partial(review_tests_prompt, row, decision)
    task = WriterTask(SESSION_REVIEW_TESTS, prompt, session.base, blocks=False)
    run, verdict = run_attempts(session, running, partial(writer_try, session, running, task))
    if verdict.outcome == OUTCOME_DONE:
        running.saved = SavedTests(running.block, snapshot_tests(root))
        save_tests(session.paths.tests_file(row.id), running.saved)
    return run, verdict


def review_try(
    session: Session, running: Running, kind: str, attempt: Attempt
) -> tuple[ClaudeRun, Verdict]:
    """Run one try of a review in a worktree of HEAD, outside the project, and judge it.

    The runner deletes the worktree after the review, so a change that the review makes cannot
    reach the branch. Such a change only adds a warning line to the log.
    """
    root = session.paths.root
    head = git_head(root)
    folder = add_worktree(root)
    job = Job(kind, partial(review_prompt, running.row, session.base), judge_review, folder)
    try:
        run = run_claude(session, running.row, attempt, job)
    finally:
        warning = remove_worktree(root, folder, head)
    if warning:
        run = replace(run, lines=[*run.lines, *warning])
        write_log(session.paths, run.log_name, run.lines)
    in_chat = session.options.review_only is not None
    return run, judge_review(run) if in_chat else judge_try(session, running.row, job, run)


def run_review(session: Session, running: Running, kind: str) -> tuple[ClaudeRun, Verdict]:
    """Run a review of the milestone (SESSION_REVIEW or SESSION_REVIEW_LAST), with its retries."""
    return run_attempts(session, running, partial(review_try, session, running, kind))


def repair_tests(
    session: Session, running: Running, findings: Sequence[str]
) -> tuple[ClaudeRun, Verdict]:
    """Send the review findings about the tests to a test session; if it changed a test, rebuild.

    The test session runs in the folder of the test writer and gets only these findings. When it
    changed tests/, a build session makes the tests pass and commits `M<n>: test repairs`.
    """
    root, row = session.paths.root, running.row
    prompt = partial(review_tests_prompt, row, [*decision_note(running), *findings])
    task = WriterTask(SESSION_REVIEW_TESTS, prompt, "HEAD", blocks=False)
    run, verdict = run_attempts(session, running, partial(writer_try, session, running, task))
    running.decisions += len(decision_lines(run.lines))
    if verdict.outcome != OUTCOME_DONE or not changed_test_files(root, "HEAD"):
        return run, verdict
    running.saved = SavedTests(running.block, snapshot_tests(root))
    save_tests(session.paths.tests_file(row.id), running.saved)
    return run_claude_session(session, running, rebuild_job(session, running))


def repair_findings(
    session: Session, running: Running, findings: Sequence[str]
) -> tuple[ClaudeRun, Verdict]:
    """Route each finding by the file of its fix: tests/ to a test session, the rest to a repair."""
    test_findings = [finding for finding in findings if is_test_finding(finding)]
    code_findings = [finding for finding in findings if not is_test_finding(finding)]
    run, verdict = ClaudeRun([], 0), Verdict(OUTCOME_DONE, "")
    if test_findings:
        run, verdict = repair_tests(session, running, test_findings)
    if verdict.outcome == OUTCOME_DONE and code_findings:
        job = repair_job(session, running, code_findings)
        run, verdict = run_claude_session(session, running, job)
    return run, verdict


def review_milestone(session: Session, running: Running) -> tuple[ClaudeRun, Verdict]:
    """Review the diff of the milestone branch; with findings, repair them and review once more.

    A finding about tests/ goes to a test session, any other finding to the repair session. After
    the last review, a finding that blocks the merge blocks the milestone; the other findings
    stay: `running.findings` counts them. A milestone gets at most two reviews. A milestone whose
    block by the last review the user approved takes review_approved instead.

    Returns:
        The run of the last session, and its verdict: done, failed, or blocked.
    """
    if running.approved:
        return review_approved(session, running)
    run, verdict = run_review(session, running, SESSION_REVIEW)
    findings = finding_lines(run.lines)
    if verdict.outcome != OUTCOME_DONE or not findings:
        return run, verdict
    run, verdict = repair_findings(session, running, findings)
    if verdict.outcome != OUTCOME_DONE:
        return run, verdict
    return last_review(session, running)


def review_approved(session: Session, running: Running) -> tuple[ClaudeRun, Verdict]:
    """Give the decision and the findings of an approved block to the repairs (RUN-08).

    The approval covers the code that the user saw. When the repairs change nothing (the user
    chose to merge), the milestone merges with no new review, and the approved findings stay.
    When they commit a change, the last review checks it, and its findings block as usual.

    Returns:
        The run of the last session, and its verdict: done, failed, or blocked.
    """
    root = session.paths.root
    head = git_head(root)
    run, verdict = repair_findings(session, running, running.approved)
    if verdict.outcome != OUTCOME_DONE:
        return run, verdict
    if git_head(root) == head:
        running.findings = len(running.approved)
        return run, verdict
    return last_review(session, running)


def last_review(session: Session, running: Running) -> tuple[ClaudeRun, Verdict]:
    """Run the last review: a finding that blocks the merge blocks the milestone."""
    run, verdict = run_review(session, running, SESSION_REVIEW_LAST)
    if verdict.outcome != OUTCOME_DONE:
        return run, verdict
    last = finding_lines(run.lines)
    running.findings = len(last)
    running.blocking = [finding for finding in last if blocks_merge(finding)]
    if running.blocking:
        return run, Verdict(OUTCOME_BLOCKED, "the last review found a fault that blocks the merge.")
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
    console.say(
        f"{milestone_at_start(row.id)} is merged and pushed. Do its human test now:", "yellow"
    )
    for line in steps:
        console.say(line)
    console.say("Type yes when the test passed, then press Enter:")
    answer = console.ask()
    if answer is None or answer.strip().lower() != ANSWER_YES:
        details = [
            "Give a fault to /sherpa: it becomes a fix milestone.",
            "Run the runner again to continue with the next milestone.",
        ]
        message = f"The human test of {milestone(row.id)} is not confirmed."
        raise RunStoppedError(message, details, "yellow")


def run_milestone(session: Session, row: Row) -> None:
    """Run one milestone in its branch, time it, and check that it finished.

    Raises:
        RunStoppedError: If the milestone is blocked or did not finish, if the merge or the push
            failed, or if the user did not confirm its human test.
    """
    decision = review_decision(session, row)
    running = Running(
        row,
        Stopwatch(),
        decision=decision,
        retest=retests(session, row, decision),
        approved=approved_findings(session, row, decision),
    )
    session.state.running = running
    try:
        run, verdict = run_stages(session, running)
    except RunStoppedError:
        close_milestone(session, running, OUTCOME_FAILED)
        raise
    close_milestone(session, running, verdict.outcome)
    finish_milestone(session, running, run, verdict)


def finish_milestone(session: Session, running: Running, run: ClaudeRun, verdict: Verdict) -> None:
    """Block, stop, or ask the human test, by the verdict of the milestone.

    Raises:
        RunStoppedError: If the milestone is blocked or did not finish, or the user did not
            confirm its human test.
    """
    if verdict.outcome == OUTCOME_BLOCKED and running.blocking:
        block_after_review(session, running)
    if verdict.outcome == OUTCOME_BLOCKED:
        block_milestone(session, running.row)
    if verdict.outcome != OUTCOME_DONE:
        stop_for(running.row, verdict, run)
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
    writer, environment = check_sessions(paths.root, options)
    state.planned = [row for row in rows_in_range(rows, first, last) if row.status != "done"]
    state.total = len(state.planned)
    return Session(paths, console, state, first, last, options, base, writer, environment)


def check_sessions(root: Path, options: Options) -> tuple[Writer, dict[str, str]]:
    """Return the test writer and the environment of the sessions, after their start checks."""
    environment = session_environment()
    check_session_python(environment)
    writer = load_writer(root, options.test_writer)
    check_writer(root, writer, environment)
    return writer, environment


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
            done = f"Milestones M{session.first} to M{session.last} in {PLAN_PATH} are done."
            console.say(done, "green")
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


# --- one step in chat ----------------------------------------------------------------------------


def chat_base(root: Path) -> str:
    """Return the base branch of a chat step: the one git records for the branch, else main."""
    current = git_branch(root)
    recorded = _git(root, "config", "--get", f"branch.{current}.base").stdout.strip()
    return recorded or "main"


def chat_lines(root: Path, plan: Path, base: str, number: int) -> list[str]:
    """Return the plan that has the milestone: the working tree, or else the base branch.

    In chat, the build commit deletes the milestone from the plan before the review.

    Raises:
        RunStoppedError: If neither plan has a row for the milestone.
    """
    lines = _read_lines(plan)
    if plan_row(lines, number) is not None:
        return lines
    done = _git(root, "show", f"{base}:{PLAN_PATH}")
    lines = _split_lines(done.stdout) if done.returncode == 0 else []
    if plan_row(lines, number) is None:
        raise _error(f"{PLAN_PATH} has no row M{number}, also not on the branch {base}.")
    return lines


def chat_session(options: Options, console: Console, paths: Paths) -> Session:
    """Check the environment and return the session of one chat step."""
    check_tools(paths)
    environment = session_environment()
    check_session_python(environment)
    writer = load_writer(paths.root, options.test_writer)
    state = RunState(total=1, stopwatch=Stopwatch())
    base = chat_base(paths.root)
    return Session(paths, console, state, 0, 0, options, base, writer, environment)


def chat_running(session: Session, number: int) -> Running:
    """Return the milestone of a chat step, with its row and its block."""
    lines = chat_lines(session.paths.root, session.paths.plan, session.base, number)
    row = plan_row(lines, number) or Row(number, "", "", "", "open")
    problem = row_problem(row)
    if problem is not None:
        raise _error(problem)
    return Running(row, Stopwatch(), block=milestone_block(lines, number))


def last_review_findings(paths: Paths, number: int) -> list[str]:
    """Return the findings about tests of the last --review-only of the milestone, from its log."""
    log = paths.log_dir / f"M{number}-{SESSION_REVIEW}.log"
    lines = _read_lines(log) if log.is_file() else []
    return [finding for finding in finding_lines(lines) if is_test_finding(finding)]


def chat_task(session: Session, running: Running) -> WriterTask | None:
    """Return the writer's session of --tests-only, or None when the review left nothing to do.

    With --review-findings it repairs the findings about tests of the last --review-only.
    """
    row = running.row
    if session.options.review_findings:
        findings = last_review_findings(session.paths, row.id)
        if not findings:
            return None
        prompt = partial(review_tests_prompt, row, findings)
        return WriterTask(SESSION_REVIEW_TESTS, prompt, "HEAD", blocks=False)
    check_writer(session.paths.root, session.writer, session.environment)
    prompt = partial(build_test_prompt, row, writer=session.writer.name)
    return WriterTask(SESSION_TEST, prompt, "HEAD", blocks=True)


def tests_only(session: Session, number: int) -> int:
    """Run the test session of one milestone for a chat step, and print its result.

    The session runs in the folder of the test writer, with the runner's checks and one round of
    repair, as in an unattended run. Nothing is committed.

    Returns:
        0 when the tests are written and pass the runner's checks, 1 otherwise.
    """
    console, running = session.console, chat_running(session, number)
    task = chat_task(session, running)
    if task is None:
        console.say(f"The last review of {milestone(number)} has no finding about tests.", "green")
        return 0
    run, verdict = run_attempts(session, running, partial(writer_try, session, running, task))
    return tests_result(console, number, run, verdict)


def tests_result(console: Console, number: int, run: ClaudeRun, verdict: Verdict) -> int:
    """Print the end of the report and the verdict of --tests-only. Return the exit code."""
    for line in run.lines[-TAIL_LINES:]:
        console.say(line)
    if verdict.outcome == OUTCOME_BLOCKED:
        console.say(f"{milestone_at_start(number)} is blocked: read its Blocked entry.", "yellow")
        return 1
    if verdict.outcome != OUTCOME_DONE:
        console.say(f"{milestone_at_start(number)}: {verdict.reason}", "red")
        return 1
    console.say(f"The tests of {milestone(number)} are written and pass the checks.", "green")
    return 0


def review_only(session: Session, number: int) -> int:
    """Run the review of one milestone for a chat step, in a worktree of HEAD, and print it.

    Returns:
        0 when the review ran (with or without findings), 1 when it did not.
    """
    console, running = session.console, chat_running(session, number)
    run, verdict = run_review(session, running, SESSION_REVIEW)
    if verdict.outcome != OUTCOME_DONE:
        console.say(f"The review of {milestone(number)} did not run: {verdict.reason}", "red")
        return 1
    findings = finding_lines(run.lines)
    for finding in findings or ["NO FINDINGS"]:
        console.say(finding)
    if any(is_test_finding(finding) for finding in findings):
        command = f"python scripts/milestones-runner.py --tests-only M{number} --review-findings"
        console.say(f"Findings about tests go to a test session: {command}", "yellow")
    return 0


def run_chat_step(
    options: Options, console: Console, paths: Paths, step: Callable[[Session], int]
) -> int:
    """Run --tests-only or --review-only; print a stop instead of a traceback. Return the code."""
    try:
        return step(chat_session(options, console, paths))
    except RunStoppedError as stop:
        console.say(stop.message, stop.color)
        for line in stop.details:
            console.say(line)
        return 1


def main(argv: Sequence[str] | None = None) -> int:
    """Run one chat step, or clear the screen and run the milestones with the live table.

    Args:
        argv: The command-line arguments; None means sys.argv.

    Returns:
        0 when the range (or the chat step) is done, 1 when a milestone, a human test or the live
        checks stopped the run, 130 after Ctrl+C.
    """
    options = parse_args(argv)
    console = start_console()
    paths = Paths(Path(__file__).resolve().parent.parent)
    if options.tests_only is not None:
        return run_chat_step(
            options, console, paths, partial(tests_only, number=options.tests_only)
        )
    if options.review_only is not None:
        step = partial(review_only, number=options.review_only)
        return run_chat_step(options, console, paths, step)
    console.clear_screen()
    state = RunState(total=0, stopwatch=Stopwatch())
    return run_guarded(options, console, paths, state)


if __name__ == "__main__":
    sys.exit(main())
