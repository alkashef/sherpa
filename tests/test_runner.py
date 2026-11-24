"""scripts/milestones-runner.py, as a new project gets it: its parts, and whole runs.

The whole runs use a fake `claude` (tests/fake_claude.py) that plays the test session, the build
session, the review sessions and the repair session of each milestone, and finishes, blocks, or
skips it, in a project set up by init_project.py, with the real git hooks.
"""

import importlib.util
import json
import os
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from helpers import Sandbox, build, logged_calls, run, shim

FAKE_CLAUDE = Path(__file__).resolve().with_name("fake_claude.py")
DENIED_TO_TEST = ["Read(./src/**)"]
DENIED_TO_BUILD = ["Edit(./tests/**)"]
DENIED_TO_REVIEW = ["Edit", "Write", "NotebookEdit"]
M1_TEST = "from src.m1 import value\n\n\ndef test_m1_value() -> None:\n    assert value() == 1\n"
M1_SESSIONS = ["test M1", "build M1", "review M1"]
M2_SESSIONS = ["test M2", "build M2", "review M2"]
M1_FINDINGS = [  # what the fake review reports in the state "findings"
    "FINDING: medium | src/m1.py:1 | Comments | Say what the module is for.",
    "FINDING: low | src/m1.py:5 | Dead Code | Delete the name that nothing uses.",
]
PLAN = """# Plan — project-init

**Next milestone number: M3**

## Milestones at a glance

| Milestone | Description | Model | Effort | Human test | Status |
| --- | --- | --- | --- | --- | --- |
| **M1** First | Does one thing | sonnet | low | no | open |
| **M2** Second | Does another | haiku | medium | no | open |

## Milestones

### M1 — First

- **Refs:** R1.
- **Owner:** `src/m1.py`.

### M2 — Second

- **Refs:** R2.
- **Owner:** `src/m2.py`.
"""
HUMAN_TEST = "- **Human test:** Start the app and open the first page.\n  The page shows 1."
NO_MILESTONES = PLAN[: PLAN.index("| **M1**")] + "\n## Milestones\n\nNone planned.\n"
LIVE_APPROVAL = "\n## Live checks\n\n- **Approval:** Run them.\n- **Budget ceiling:** 1 USD\n"


def load_runner(project: Path) -> ModuleType:
    """Import the runner a built project got."""
    path = project / "scripts" / "milestones-runner.py"
    spec = importlib.util.spec_from_file_location("milestones_runner", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["milestones_runner"] = module  # dataclasses look their module up while defined
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def built(tmp_path: Path) -> Path:
    """A project built with the python module, named my-app."""
    build(tmp_path / "my-app", "--with", "python")
    return tmp_path / "my-app"


def commit_plan(sandbox: Sandbox, plan: str, message: str) -> None:
    """Write docs/plan.md, commit every change with the message, and push."""
    (sandbox.folder / "docs" / "plan.md").write_text(plan, encoding="utf-8")
    sandbox.git("add", "-A")
    sandbox.git("commit", "-m", message)
    sandbox.git("push")


@pytest.fixture
def planned(sandbox: Sandbox) -> Sandbox:
    """A pushed project named after this repository's environment, with two planned milestones.

    The runner refuses to start outside the project's environment; the tests run in this
    repository's environment, `sherpa`, so the project takes that name.
    """
    result = sandbox.init("--name", "sherpa", "--with", "python", "--no-conda")
    assert result.returncode == 0, result.stderr
    shim(sandbox.fake_bin, "claude", FAKE_CLAUDE)
    root = sandbox.folder.parent
    sandbox.env.update(
        {
            "FAKE_CLAUDE_LOG": str(root / "claude.log"),
            # The pre-commit hook finds Python through the active environment.
            "CONDA_DEFAULT_ENV": "sherpa",
            "CONDA_PREFIX": sys.prefix,
        }
    )
    commit_plan(sandbox, PLAN, "Plan M1 and M2")
    return sandbox


def run_runner(sandbox: Sandbox, *options: str, typed: str = "") -> tuple[int, str]:
    """Run the project's milestone runner and return its exit code and output.

    `typed` is what the user types; the default is no input at all.
    """
    command = [sys.executable, "scripts/milestones-runner.py", *options]
    result = run(command, sandbox.folder, sandbox.env, stdin=typed)
    return result.returncode, result.stdout + result.stderr


def sessions(sandbox: Sandbox) -> list[dict[str, Any]]:
    """Return the kind, the milestone, the prompt and the folder of each session of the fake."""
    log = sandbox.folder.parent / "claude-sessions.jsonl"
    if not log.exists():
        return []
    return [json.loads(line) for line in log.read_text("utf-8").splitlines()]


def kinds(sandbox: Sandbox) -> list[str]:
    """Return every session the fake claude played, in order, such as "build M1"."""
    return [f"{session['kind']} M{session['milestone']}" for session in sessions(sandbox)]


def denied_tools(call: list[str]) -> list[str]:
    """Return the tools that one call of claude was denied."""
    return call[call.index("--disallowedTools") + 1 :]


def table_cells(output: str, milestone: str) -> list[str]:
    """Return the cells of the last table row of a milestone that the runner printed."""
    rows = [line for line in output.splitlines() if line.startswith(f"│ {milestone} ")]
    return [cell.strip() for cell in rows[-1].strip("│").split("│")]


def subjects(sandbox: Sandbox, *revision: str) -> list[str]:
    """Return the first line of each commit message, the newest first."""
    return sandbox.git("log", "--format=%s", *revision).splitlines()


def branches(sandbox: Sandbox) -> list[str]:
    """Return the names of the local branches."""
    return sandbox.git("branch", "--format=%(refname:short)").splitlines()


def plan_rows(runner: ModuleType, project: Path) -> list[object]:
    """Return the rows of the project's plan table, as the runner reads them."""
    lines = (project / "docs" / "plan.md").read_text(encoding="utf-8").splitlines()
    rows: list[object] = runner.parse_plan_rows(lines)
    return rows


def test_new_plan_has_the_table_the_runner_reads(built: Path) -> None:
    runner = load_runner(built)
    assert "## Milestones at a glance" in (built / "docs" / "plan.md").read_text("utf-8")
    assert plan_rows(runner, built) == []


def test_workflow_row_template_is_a_row_the_runner_reads(built: Path) -> None:
    runner = load_runner(built)
    workflow = (built / "docs" / "workflow.md").read_text(encoding="utf-8")
    [template] = [line for line in workflow.splitlines() if line.startswith("| **M<n>**")]
    filled = template.replace("<n>", "7").replace("<title>", "Login")
    filled = filled.replace("<model>", "sonnet").replace("<effort>", "high")
    filled = filled.replace("<yes or no>", "yes")
    assert runner.parse_row(filled) == runner.Row(7, "Login", "sonnet", "high", "open", "yes")


def test_a_row_has_six_cells(built: Path) -> None:
    runner = load_runner(built)
    row = runner.parse_row("| **M4** Pay | Takes a payment | Opus | Max | No | Approved |")
    assert row == runner.Row(4, "Pay", "opus", "max", "approved", "no")
    # A row of the old table, with no Human test cell, is not a milestone row.
    assert runner.parse_row("| **M4** Pay | Takes a payment | opus | max | open |") is None
    assert [row.human_test for row in runner.parse_plan_rows(PLAN.splitlines())] == ["no", "no"]


def test_new_gitignore_has_the_runner_entries(built: Path) -> None:
    runner = load_runner(built)
    lines = (built / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert runner.missing_ignore_entries(lines) == []


def test_runner_checks_the_project_environment(built: Path) -> None:
    runner = load_runner(built)
    assert runner.in_project_env("C:/miniconda3/envs/my-app")
    assert not runner.in_project_env("C:/miniconda3/envs/other")


def test_unusable_model_or_effort_is_named(built: Path) -> None:
    runner = load_runner(built)
    assert "Model 'gpt'" in runner.row_problem(runner.Row(1, "A", "gpt", "low", "open"))
    assert "Effort 'huge'" in runner.row_problem(runner.Row(1, "A", "opus", "huge", "open"))
    assert runner.row_problem(runner.Row(1, "A", "opus", "max", "open")) is None


def test_prompt_names_the_milestone_and_its_commit(built: Path) -> None:
    runner = load_runner(built)
    row = runner.Row(3, "Login", "sonnet", "low", "open")
    prompt = runner.build_prompt(row, False)
    assert "milestone M3 (Login) from docs/plan.md" in prompt
    assert "`M3: Login`" in prompt
    assert "Approval entry" in prompt
    assert "change no file in tests/" in prompt
    assert "the loop in docs/workflow.md (steps 4 to 6)" in prompt
    assert "read the sections of docs/design.md that the Refs of the block name" in prompt
    assert "<n>" not in prompt
    assert "A previous session" not in prompt
    assert "A previous session" in runner.build_prompt(row, True)
    # An approved milestone continues from its partial work: its Blocked entry has an answer.
    assert "a Blocked entry and no Approval entry answers it" in runner.build_prompt(row, True)


def test_the_build_session_does_not_push_and_keeps_the_work_of_a_blocked_milestone(
    built: Path,
) -> None:
    runner = load_runner(built)
    prompt = runner.build_prompt(runner.Row(3, "Login", "sonnet", "low", "open"))
    assert "do not push and do not merge: the runner does that" in prompt
    assert "change nothing else and commit nothing. Do not undo your work" in prompt
    assert "a fake only for an external service" in prompt
    assert "No milestone session runs the tests in tests/live/" in prompt
    for old in ("run git push", "undo your other changes", "`M3: blocked`"):
        assert old not in prompt, old


def test_test_prompt_starts_the_test_skill_and_keeps_out_of_the_code(built: Path) -> None:
    runner = load_runner(built)
    prompt = runner.build_test_prompt(runner.Row(3, "Login", "sonnet", "low", "open"))
    assert "Run /write-tests for milestone M3 (Login) of docs/plan.md" in prompt
    assert "read the code in src/" in prompt
    assert "commit nothing, also not to block the milestone" in prompt
    assert "change nothing else and commit nothing. Do not undo your work" in prompt
    assert "a fake only for an external service" in prompt
    assert "goes to tests/live/: write it, but do not run it" in prompt
    assert "<n>" not in prompt
    for old in ("git push", "delete the files you added", "`M3: blocked`"):
        assert old not in prompt, old


def test_review_prompt_names_the_diff_and_the_two_reviews(built: Path) -> None:
    runner = load_runner(built)
    prompt = runner.review_prompt(runner.Row(3, "Login", "sonnet", "low", "open"), "main")
    assert "Review milestone M3 (Login): the diff `git diff main...HEAD`" in prompt
    assert prompt.index("/code-review skill") < prompt.index("/code-review-sherpa")
    assert "`BUILT-IN REVIEW: not available`" in prompt
    assert "Change no file and commit nothing." in prompt
    assert "nobody can answer" in prompt
    assert "`FINDING: <high|medium|low> | <file>:<line> | <rule or smell> | <remedy>`" in prompt
    assert "Wrong behavior against a requirement is high, never low" in prompt
    assert "`NO FINDINGS`" in prompt


def test_repair_prompt_gives_the_findings_and_the_rules(built: Path) -> None:
    runner = load_runner(built)
    findings = ["FINDING: low | src/a.py:3 | Dead Code | Delete it.", "FINDING: high | b | c | d"]
    prompt = runner.repair_prompt(runner.Row(3, "Login", "sonnet", "low", "open"), findings)
    assert "Repair the findings of the review of milestone M3 (Login)." in prompt
    assert set(findings) < set(prompt.splitlines())
    assert "the smallest change" in prompt
    assert "do not change behavior that docs/spec.md states" in prompt
    assert "change no file in tests/, and never edit docs/spec.md" in prompt
    assert "`REJECTED: <finding> | <why>`" in prompt
    assert "`python scripts/check.py` must pass" in prompt
    assert "`M3: review repairs`; do not push" in prompt


def test_a_retry_gets_the_reason_after_the_resume_note(built: Path) -> None:
    runner = load_runner(built)
    row = runner.Row(3, "Login", "sonnet", "low", "open")
    why = "git status is not clean."
    prompts = {
        runner.RESUME_NOTE: runner.build_prompt(row, True, why),
        runner.TEST_RESUME_NOTE: runner.build_test_prompt(row, True, why),
        runner.REVIEW_RESUME_NOTE: runner.review_prompt(row, "main", True, why),
        runner.REPAIR_RESUME_NOTE: runner.repair_prompt(row, [], True, why),
    }
    for note, prompt in prompts.items():
        assert f"{note} The earlier try did not count: {why}" in prompt, note
    # A run that starts with --resume has no failed try yet, so it has no reason.
    assert "The earlier try did not count" not in runner.build_prompt(row, True)
    assert "The earlier try did not count" not in runner.build_prompt(row, False)


def test_each_session_is_denied_the_tools_of_its_kind(built: Path) -> None:
    runner = load_runner(built)
    row = runner.Row(3, "Login", "sonnet", "low", "open")
    denied = {kind: denied_tools(runner.session_command(row, kind)) for kind in runner.DENIED_TOOLS}
    assert denied == {
        runner.SESSION_TEST: DENIED_TO_TEST,
        runner.SESSION_BUILD: DENIED_TO_BUILD,
        runner.SESSION_REVIEW: DENIED_TO_REVIEW,
        runner.SESSION_REPAIR: DENIED_TO_BUILD,
        runner.SESSION_REVIEW_LAST: DENIED_TO_REVIEW,
        runner.SESSION_TEST_FIX: DENIED_TO_TEST,
        runner.SESSION_REVIEW_TESTS: DENIED_TO_TEST,
        runner.SESSION_REBUILD: DENIED_TO_BUILD,
        runner.SESSION_RETEST: DENIED_TO_TEST,
    }


def test_each_claude_session_loads_only_the_settings_of_the_project(built: Path) -> None:
    # The sixth real run: a plugin hook of the user's own settings sent findings to a session.
    runner = load_runner(built)
    row = runner.Row(3, "Login", "sonnet", "low", "open")
    for kind in runner.DENIED_TOOLS:
        command = runner.session_command(row, kind)
        index = command.index("--setting-sources")
        assert command[index + 1] == "project,local", kind
        assert index < command.index("--disallowedTools"), kind
        # RUN-16: no MCP server of the user's account, such as a mail or chat connector.
        assert command.index("--strict-mcp-config") < command.index("--disallowedTools"), kind


def test_a_session_loads_the_mcp_servers_of_its_folder_only(built: Path, tmp_path: Path) -> None:
    runner = load_runner(built)
    command = runner.session_command(runner.Row(3, "Login", "sonnet", "low", "open"), "build")
    assert runner.with_project_mcp(command, tmp_path) == command
    (tmp_path / ".mcp.json").write_text('{"mcpServers": {}}\n', encoding="utf-8")
    loaded = runner.with_project_mcp(command, tmp_path)
    strict = loaded.index("--strict-mcp-config")
    assert loaded[strict + 1 : strict + 3] == ["--mcp-config", str(tmp_path / ".mcp.json")]
    assert loaded.index("--mcp-config") < loaded.index("--disallowedTools")
    # The command of another test writer has no --strict-mcp-config, and stays as it is.
    other = ["codex", "exec", "-"]
    assert runner.with_project_mcp(other, tmp_path) == other


def test_each_session_kind_has_its_log(built: Path) -> None:
    runner = load_runner(built)
    row = runner.Row(3, "Login", "sonnet", "low", "open")
    names = [runner.log_file_name(row, kind, 1) for kind in runner.DENIED_TOOLS]
    assert names == [
        "M3-test.log",
        "M3.log",
        "M3-review.log",
        "M3-repair.log",
        "M3-review-last.log",
        "M3-test-fix.log",
        "M3-review-tests.log",
        "M3-rebuild.log",
        "M3-retest.log",
    ]
    assert runner.log_file_name(row, runner.SESSION_BUILD, 2) == "M3-2.log"
    assert runner.log_file_name(row, runner.SESSION_REVIEW_LAST, 2) == "M3-review-last-2.log"


def test_no_prompt_names_another_projects_files(built: Path) -> None:
    runner = load_runner(built)
    row = runner.Row(3, "Login", "sonnet", "low", "open")
    prompts = runner.build_prompt(row, True) + runner.build_test_prompt(row, True)
    prompts += runner.review_prompt(row, "main", True) + runner.repair_prompt(row, [], True)
    assert "docs/spec.md" in prompts
    assert "DEC-NNN" in prompts
    for word in ("specs.md", "docs/ui", "Ollama", "embedding", "D-NN"):
        assert word not in prompts, word


def test_milestone_block_ends_at_the_next_heading(built: Path) -> None:
    runner = load_runner(built)
    block = runner.milestone_block(PLAN.splitlines(), 1)
    assert block[0] == "### M1 — First"
    assert "- **Refs:** R1." in block
    assert "### M2 — Second" not in block


def test_a_block_entry_is_read_with_its_continuation_lines(built: Path) -> None:
    runner = load_runner(built)
    block = [
        "### M1 — First",
        "",
        "- **Gate:** the checks pass.",
        "- **Human test:** Start the app.",
        "  1. Open the first page.",
        "  2. The page shows 1.",
        "- **Blocked:** a question.",
    ]
    steps = ["Start the app.", "  1. Open the first page.", "  2. The page shows 1."]
    assert runner.block_entry(block, "Human test") == steps
    assert runner.block_entry(block, "Gate") == ["the checks pass."]
    assert runner.block_entry(block, "Approval") == []
    assert runner.block_entry(["- **Human test:**", "", "- **Gate:** x"], "Human test") == []


def test_gitignore_entries_start_on_a_new_line(built: Path, tmp_path: Path) -> None:
    runner = load_runner(built)
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text("node_modules/", encoding="utf-8")
    assert runner.add_ignore_entries(gitignore)
    lines = gitignore.read_text(encoding="utf-8").splitlines()
    assert lines == ["node_modules/", ".claude/logs/"]
    assert not runner.add_ignore_entries(gitignore)


def test_runner_finishes_every_open_milestone(planned: Sandbox) -> None:
    code, output = run_runner(planned)
    assert code == 0, output
    assert "Milestones M1 to M2 in docs/plan.md are done." in output
    assert subjects(planned, "-2") == ["M2: Second", "M1: First"]
    calls = logged_calls(planned.folder.parent / "claude.log")
    models = [(call[call.index("--model") + 1], call[call.index("--effort") + 1]) for call in calls]
    # Three sessions for each milestone: the test session, the build session, the review session.
    assert kinds(planned) == M1_SESSIONS + M2_SESSIONS
    assert models == [("sonnet", "low")] * 3 + [("haiku", "medium")] * 3
    assert [denied_tools(call) for call in calls] == [
        DENIED_TO_TEST,
        DENIED_TO_BUILD,
        DENIED_TO_REVIEW,
    ] * 2
    logs = planned.folder / ".claude" / "logs"
    assert len((logs / "timings.csv").read_text("utf-8").splitlines()) == 3
    assert {"M1-test.log", "M1.log", "M1-review.log", "M1-tests.json"} <= {
        p.name for p in logs.iterdir()
    }
    assert "tests/unit/test_m1.py" in planned.git("show", "--name-only", "--format=", "HEAD~1")
    # The table counts the DECISION line of each build session, and no finding.
    assert table_cells(output, "M1")[5:] == ["1", "0", "done"]
    # The project has no live check, and the run still ends with 0.
    assert "Live checks: not run (no test in tests/live/)." in output


def test_each_milestone_is_merged_from_its_branch_and_pushed_by_the_runner(
    planned: Sandbox,
) -> None:
    code, output = run_runner(planned)
    assert code == 0, output
    # The fake sessions never push, so the runner pushed the base branch.
    assert planned.remote_head() == planned.git("rev-parse", "HEAD")
    # A fast-forward makes no merge commit, and the milestone branches are deleted.
    assert planned.git("log", "--merges", "--format=%s") == ""
    assert branches(planned) == ["main"]
    assert planned.git("config", "--get-regexp", "^branch\\.main\\.") != ""
    assert "milestone/" not in planned.git("config", "--list")
    assert_session_folders(planned)


def assert_session_folders(planned: Sandbox) -> None:
    """Check that the build session worked in the branch of its milestone, the test session in a
    folder without the code, and the review in a worktree of the branch."""
    for session in sessions(planned):
        branch = f"You work in the branch milestone/M{session['milestone']}"
        if session["kind"] == "build":
            assert branch in session["prompt"]
            assert session["folder"] == str(planned.folder)
        elif session["kind"] == "test":
            assert "This folder holds no src/ and no .git" in session["prompt"]
            assert (session["src"], session["git"]) == (False, False)
        else:
            assert "`git diff main...HEAD`" in session["prompt"]
            assert session["folder"] != str(planned.folder)


def approve(sandbox: Sandbox, decision: str) -> None:
    """Do what the user does: add an Approval entry to M1, set it to approved, and commit."""
    plan = sandbox.folder / "docs" / "plan.md"
    text = plan.read_text(encoding="utf-8").replace("| blocked |", "| approved |")
    text = text.replace("which database?", f"which database?\n- **Approval:** {decision}")
    plan.write_text(text, encoding="utf-8")
    sandbox.git("commit", "-am", "Approve M1")


def test_blocked_milestone_is_committed_and_stops_the_run(planned: Sandbox) -> None:
    planned.env["FAKE_CLAUDE_STATE"] = "blocked"
    code, output = run_runner(planned)
    assert code == 1
    assert "Milestone M1 in docs/plan.md waits for your approval." in output
    assert "### M1 — First" in output
    assert "which database?" in output
    # The session committed nothing: the runner committed the plan on the base branch, and pushed.
    assert planned.git("rev-parse", "--abbrev-ref", "HEAD") == "main"
    assert subjects(planned, "-1") == ["M1: blocked"]
    assert planned.git("show", "--name-only", "--format=", "HEAD") == "docs/plan.md"
    assert planned.remote_head() == planned.git("rev-parse", "HEAD")
    assert planned.git("status", "--porcelain") == ""
    # The test session changed only the plan, so its branch has no partial work.
    assert subjects(planned, "-1", "milestone/M1") == ["Plan M1 and M2"]
    # The test session blocked it, so no build session ran.
    assert kinds(planned) == ["test M1"]
    assert table_cells(output, "M1")[-1] == "blocked"


def test_runner_waits_at_a_blocked_row(planned: Sandbox) -> None:
    planned.env["FAKE_CLAUDE_STATE"] = "blocked"
    run_runner(planned)
    code, output = run_runner(planned)
    assert code == 1
    assert "Milestone M1 in docs/plan.md waits for your approval." in output
    assert "which database?" in output
    assert kinds(planned) == ["test M1"]


def test_approved_milestone_runs_again_and_the_run_goes_on(planned: Sandbox) -> None:
    planned.env["FAKE_CLAUDE_STATE"] = "blocked"
    run_runner(planned)
    approve(planned, "Use SQLite.")
    planned.env["FAKE_CLAUDE_STATE"] = ""
    code, output = run_runner(planned)
    assert code == 0, output
    assert subjects(planned, "-3") == ["M2: Second", "M1: First", "Approve M1"]
    assert planned.remote_head() == planned.git("rev-parse", "HEAD")
    assert branches(planned) == ["main"]
    # Its branch had no work of its own, so the milestone ran from its start.
    assert kinds(planned) == ["test M1", *M1_SESSIONS, *M2_SESSIONS]


def test_a_blocked_milestone_keeps_its_work_in_its_branch(planned: Sandbox) -> None:
    planned.env["FAKE_CLAUDE_STATE"] = "blocked-build"
    code, output = run_runner(planned)
    assert code == 1
    assert "Milestone M1 in docs/plan.md waits for your approval." in output
    assert kinds(planned) == ["test M1", "build M1"]
    # The base branch got the blocked plan alone, and it is pushed.
    assert planned.git("rev-parse", "--abbrev-ref", "HEAD") == "main"
    assert subjects(planned, "-2") == ["M1: blocked", "Plan M1 and M2"]
    assert planned.git("show", "--name-only", "--format=", "HEAD") == "docs/plan.md"
    assert planned.remote_head() == planned.git("rev-parse", "HEAD")
    # The milestone branch got the other changes, and not the plan.
    assert subjects(planned, "-2", "milestone/M1") == ["M1: partial work", "Plan M1 and M2"]
    kept = planned.git("show", "--name-only", "--format=", "milestone/M1").splitlines()
    assert kept == ["src/__init__.py", "src/m1.py", "tests/unit/test_m1.py"]
    assert not (planned.folder / "src" / "m1.py").exists()


def test_a_refused_commit_of_the_blocked_plan_says_how_to_finish(planned: Sandbox) -> None:
    # A lint error on the base branch makes the pre-commit hook refuse each commit there.
    (planned.folder / "src" / "bad.py").write_text("import os\n", encoding="utf-8")
    planned.git("add", "-A")
    planned.git("commit", "--no-verify", "-m", "A lint error")
    planned.git("push")
    planned.env["FAKE_CLAUDE_STATE"] = "blocked-build"
    code, output = run_runner(planned)
    assert code == 1
    for line in [
        "ERROR: milestone M1 in docs/plan.md is blocked, but `git commit` failed on main.",
        "The work of M1 is safe in the branch milestone/M1.",
        "docs/plan.md with the blocked row is staged and not committed on main.",
        'Then run: git commit -m "M1: blocked", and then: git push',
        "failed   ruff check",  # the output of the hook
    ]:
        assert line in output
    # The plan waits on the base branch, and the work is in the milestone branch.
    assert planned.git("rev-parse", "--abbrev-ref", "HEAD") == "main"
    assert subjects(planned, "-1") == ["A lint error"]
    assert planned.git("status", "--porcelain") == "M  docs/plan.md"
    assert subjects(planned, "-1", "milestone/M1") == ["M1: partial work"]


def test_an_approved_milestone_continues_from_its_partial_work(planned: Sandbox) -> None:
    planned.env["FAKE_CLAUDE_STATE"] = "blocked-build"
    run_runner(planned)
    approve(planned, "Use SQLite.")
    planned.env["FAKE_CLAUDE_STATE"] = ""
    code, output = run_runner(planned, "--end", "1")
    assert code == 0, output
    # The test session had finished. A test session got the decision first (RUN-12), and it
    # changed nothing, because the decision asks for no change of a test.
    assert kinds(planned) == ["test M1", "build M1", "retest M1", "build M1", "review M1"]
    assert "The decision:\nUse SQLite.\nRules:" in sessions(planned)[2]["prompt"]
    assert "A previous session worked on this milestone" in sessions(planned)[3]["prompt"]
    # The partial work went into the commit of the milestone, on top of the approval.
    assert subjects(planned, "-3") == ["M1: First", "Approve M1", "M1: blocked"]
    assert "M1: partial work" not in subjects(planned)
    changed = planned.git("show", "--name-only", "--format=", "HEAD").splitlines()
    assert {"src/m1.py", "tests/unit/test_m1.py", "docs/plan.md"} <= set(changed)
    assert planned.remote_head() == planned.git("rev-parse", "HEAD")
    assert branches(planned) == ["main"]


def test_an_approved_build_block_about_a_test_changes_the_test_first(planned: Sandbox) -> None:
    # RUN-12: in the fifth real run the build session found a wrong test and blocked. After the
    # approval only a build session ran, and it may not change a test, so it stopped again.
    planned.env["FAKE_CLAUDE_STATE"] = "blocked-build"
    run_runner(planned)
    approve(planned, "Add the type test.")
    planned.env["FAKE_CLAUDE_STATE"] = ""
    code, output = run_runner(planned, "--end", "1")
    assert code == 0, output
    assert kinds(planned) == ["test M1", "build M1", "retest M1", "build M1", "review M1"]
    tests = planned.git("show", "HEAD:tests/unit/test_m1.py")
    assert "test_m1_value_is_an_int" in tests
    assert branches(planned) == ["main"]


def test_the_retest_prompt_changes_a_test_only_as_the_decision_says(built: Path) -> None:
    runner = load_runner(built)
    row = runner.Row(3, "Login", "sonnet", "low", "approved")
    prompt = runner.retest_prompt(row, ["Use SQLite."])
    assert prompt.startswith("Change the tests of milestone M3 (Login) as the user decided.")
    assert "When the decision asks for no change of a test,\nchange nothing." not in prompt
    assert "When the decision asks for no change of a test, change nothing." in prompt
    assert "The decision:\nUse SQLite.\nRules:" in prompt
    assert "`NO CHANGE`" in prompt
    assert "Never read the code in src/" in prompt
    assert "<n>" not in prompt


def test_runner_stops_when_a_milestone_does_not_finish(planned: Sandbox) -> None:
    planned.env["FAKE_CLAUDE_STATE"] = "idle"
    code, output = run_runner(planned)
    assert code == 1
    # The writer ends with 0 and writes nothing: only the runner's own checks judge it.
    assert (
        "M1 in docs/plan.md stopped: the runner's checks of the tests failed: The test session"
        in output
    )
    assert "run again with --resume" in output
    # The test session and its round of repair, then one retry of both.
    assert kinds(planned) == ["test M1", "test-fix M1"] * 2
    # The run stops on the branch of the milestone, and git knows its base branch.
    assert planned.git("rev-parse", "--abbrev-ref", "HEAD") == "milestone/M1"
    assert planned.git("config", "branch.milestone/M1.base") == "main"
    assert subjects(planned, "-1", "main") == ["Plan M1 and M2"]


def test_a_session_that_did_not_finish_is_tried_again_with_the_reason(planned: Sandbox) -> None:
    planned.env["FAKE_CLAUDE_STATE"] = "retry"
    code, output = run_runner(planned, "--end", "1")
    assert code == 0, output
    assert subjects(planned, "-1") == ["M1: First"]
    assert (planned.folder / ".claude" / "logs" / "M1-2.log").is_file()
    assert kinds(planned) == ["test M1", "build M1", "build M1", "review M1"]
    first, retry = (session["prompt"] for session in sessions(planned)[1:3])
    reason = "The earlier try did not count: its row is still in the plan table and not blocked"
    assert reason not in first
    assert reason in retry
    assert retry.index("A previous session worked on this milestone") < retry.index(reason)


def test_resume_continues_with_the_build_session(planned: Sandbox) -> None:
    planned.env["FAKE_CLAUDE_STATE"] = "retry"
    code, output = run_runner(planned, "--retries", "0", "--end", "1")
    assert code == 1
    assert "Milestone M1 in docs/plan.md stopped" in output
    # The test session left its test in the tree, so a plain run refuses to start.
    assert (planned.folder / "tests" / "unit" / "test_m1.py").read_text("utf-8") == M1_TEST
    code, output = run_runner(planned, "--end", "1")
    assert code == 1
    assert "git status is not clean" in output
    code, output = run_runner(planned, "--end", "1", "--resume")
    assert code == 0, output
    assert subjects(planned, "-1") == ["M1: First"]
    assert planned.remote_head() == planned.git("rev-parse", "HEAD")
    assert branches(planned) == ["main"]
    # The first run: a test session and a build session. The resumed run: no test session.
    assert kinds(planned) == ["test M1", "build M1", "build M1", "review M1"]


def test_the_next_milestone_comes_from_the_plan_of_the_base_branch(planned: Sandbox) -> None:
    planned.env["FAKE_CLAUDE_STATE"] = "review-error"
    code, output = run_runner(planned, "--retries", "0")
    assert code == 1
    assert (
        "Milestone M1 in docs/plan.md stopped: the review session ended with exit code 1." in output
    )
    # The run stopped in the branch of M1, where the build commit deleted the row of M1.
    assert planned.git("rev-parse", "--abbrev-ref", "HEAD") == "milestone/M1"
    assert "**M1**" not in (planned.folder / "docs" / "plan.md").read_text("utf-8")
    assert subjects(planned, "-1", "main") == ["Plan M1 and M2"]
    planned.env["FAKE_CLAUDE_STATE"] = ""
    code, output = run_runner(planned)
    assert code == 0, output
    # The build commit of M1 exists: only its review and its merge ran, then M2 from its start.
    assert kinds(planned) == [*M1_SESSIONS, "review M1", *M2_SESSIONS]
    assert subjects(planned, "-2") == ["M2: Second", "M1: First"]
    assert planned.remote_head() == planned.git("rev-parse", "HEAD")
    assert branches(planned) == ["main"]


def commit_file(sandbox: Sandbox, path: str, text: str, message: str) -> None:
    """Do what a user does by hand: write a file and commit it, without the checks of the hook."""
    (sandbox.folder / path).write_text(text, encoding="utf-8")
    sandbox.git("add", "-A")
    sandbox.git("commit", "--no-verify", "-m", message)


def test_a_base_branch_that_moved_stops_the_merge_and_says_what_to_do(planned: Sandbox) -> None:
    planned.env["FAKE_CLAUDE_STATE"] = "review-error"
    run_runner(planned, "--retries", "0", "--end", "1")
    planned.git("checkout", "main")
    commit_file(planned, "notes.md", "A note.\n", "Add a note")
    planned.env["FAKE_CLAUDE_STATE"] = ""
    code, output = run_runner(planned, "--end", "1")
    assert code == 1
    merge = "git merge --ff-only milestone/M1 failed."
    assert f"ERROR: milestone M1 in docs/plan.md is not merged: {merge}" in output
    assert "Run: git rebase main milestone/M1" in output
    # The user does what the message says, and the next run merges the milestone.
    planned.git("rebase", "main", "milestone/M1")
    code, output = run_runner(planned, "--end", "1")
    assert code == 0, output
    assert subjects(planned, "-2") == ["M1: First", "Add a note"]
    assert branches(planned) == ["main"]


def test_partial_work_that_does_not_apply_stops_the_run(planned: Sandbox) -> None:
    planned.env["FAKE_CLAUDE_STATE"] = "blocked-build"
    run_runner(planned)
    approve(planned, "Use SQLite.")
    # The user also commits a file that the partial work adds, with another text.
    commit_file(planned, "src/m1.py", '"""Another start."""\n', "Start m1 by hand")
    code, output = run_runner(planned, "--end", "1")
    assert code == 1
    assert (
        "ERROR: the partial work of milestone M1 in docs/plan.md does not apply on main." in output
    )
    assert "git rebase main milestone/M1" in output
    # The rebase is aborted: the branch still holds the partial work, and no session ran.
    assert planned.git("status", "--porcelain") == ""
    assert subjects(planned, "-1", "milestone/M1") == ["M1: partial work"]
    assert kinds(planned) == ["test M1", "build M1"]


def test_a_session_that_leaves_the_milestone_branch_does_not_count(planned: Sandbox) -> None:
    planned.env["FAKE_CLAUDE_STATE"] = "wanders"
    code, output = run_runner(planned, "--retries", "0", "--end", "1")
    assert code == 1
    assert (
        "Milestone M1 in docs/plan.md stopped: the session left the branch milestone/M1." in output
    )
    assert kinds(planned) == ["test M1", "build M1"]


def test_a_milestone_branch_with_no_recorded_base_is_refused(planned: Sandbox) -> None:
    planned.git("checkout", "-b", "milestone/M7")
    code, output = run_runner(planned)
    assert code == 1
    assert "HEAD is on milestone/M7, and git does not know its base branch." in output
    assert logged_calls(planned.folder.parent / "claude.log") == []


def test_a_build_session_that_changes_a_test_does_not_count(planned: Sandbox) -> None:
    planned.env["FAKE_CLAUDE_STATE"] = "tamper"
    code, output = run_runner(planned, "--retries", "0")
    assert code == 1
    assert "the build session changed files in tests/: tests/unit/test_m1.py" in output
    assert kinds(planned) == ["test M1", "build M1"]
    assert subjects(planned, "-1", "main") == ["Plan M1 and M2"]


def test_a_milestone_that_changes_the_spec_does_not_count(planned: Sandbox) -> None:
    planned.env["FAKE_CLAUDE_STATE"] = "spec"
    code, output = run_runner(planned, "--retries", "0")
    assert code == 1
    assert "a session changed the spec: docs/spec.md" in output
    assert kinds(planned) == ["test M1", "build M1"]


def decide_the_stack(sandbox: Sandbox) -> str:
    """Do what /write-design does when the user confirms DEC-001: set it Decided, commit, push.

    Returns:
        The row of DEC-001.
    """
    design = sandbox.folder / "docs" / "design.md"
    text = design.read_text("utf-8").replace("| DEC-001 | Proposed |", "| DEC-001 | Decided |")
    design.write_text(text, encoding="utf-8")
    sandbox.git("add", "-A")
    sandbox.git("commit", "-m", "Decide the stack")
    sandbox.git("push")
    [row] = [line for line in text.splitlines() if line.startswith("| DEC-001 | Decided |")]
    return row


def test_a_session_that_changes_a_decided_decision_is_tried_again(planned: Sandbox) -> None:
    row = decide_the_stack(planned)
    planned.env["FAKE_CLAUDE_STATE"] = "decided"
    code, output = run_runner(planned, "--end", "1")
    assert code == 0, output
    assert kinds(planned) == ["test M1", "build M1", "build M1", "review M1"]
    retry = sessions(planned)[2]["prompt"]
    assert "a session changed what the user decided in docs/design.md: DEC-001." in retry
    assert "set its Status to Superseded, change nothing else in its row" in retry
    assert row in (planned.folder / "docs" / "design.md").read_text("utf-8").splitlines()


DESIGN_BEFORE = (
    "| ID | Status | Decision | Why |",
    "| --- | --- | --- | --- |",
    "| DEC-001 | Decided | `urllib.request` | The standard library is enough |",
    "| DEC-002 | Proposed | JSON | TBD |",
)
DEC_001 = DESIGN_BEFORE[2]
DEC_002 = DESIGN_BEFORE[3]
NEW_ROW = "| DEC-003 | Proposed | `http.client` | auto-decided in M2, review |"


@pytest.mark.parametrize(
    ("rows", "changed"),
    [
        ((DEC_001, DEC_002), []),
        ((DEC_001.replace("| DEC-001 | Decided |", "|  DEC-001  |  `Decided`  |"), DEC_002), []),
        ((DEC_001.replace("Decided", "Superseded"), DEC_002, NEW_ROW), []),
        ((DEC_001, DEC_002.replace("JSON", "YAML")), []),
        ((DEC_001.replace("urllib.request", "http.client"), DEC_002), ["DEC-001"]),
        (
            (DEC_001.replace("Decided", "Superseded").replace("urllib", "http"), DEC_002),
            ["DEC-001"],
        ),
        ((DEC_001.replace("Decided", "Proposed"), DEC_002), ["DEC-001"]),
        ((DEC_002,), ["DEC-001"]),
        ((DEC_001, DEC_002.replace("Proposed", "Decided")), ["DEC-002"]),
        ((DEC_001, DEC_002, NEW_ROW.replace("Proposed", "Decided")), ["DEC-003"]),
    ],
)
def test_only_the_user_makes_or_changes_a_decided_decision(
    built: Path, rows: tuple[str, ...], changed: list[str]
) -> None:
    runner = load_runner(built)
    assert runner.changed_decisions(DESIGN_BEFORE, [*DESIGN_BEFORE[:2], *rows]) == changed


def test_the_repair_and_rebuild_prompts_keep_the_decided_decisions(built: Path) -> None:
    runner = load_runner(built)
    row = runner.Row(3, "Login", "sonnet", "low", "open")
    rule = "A Decided decision is the user's: in its row, change only the Status"
    assert rule in runner.repair_prompt(row, [])
    assert rule in runner.rebuild_prompt(row)


def test_runner_refuses_a_milestone_whose_refs_name_a_proposed_decision(
    planned: Sandbox,
) -> None:
    # The design of a new project holds DEC-001 with the Status Proposed.
    plan = PLAN.replace("- **Refs:** R2.", "- **Refs:** R2, DEC-001.")
    commit_plan(planned, plan, "Name a Proposed decision")
    code, output = run_runner(planned)
    assert code == 1
    assert "python scripts/spec_coverage.py --consistency failed" in output
    assert "names DEC-001 in the Refs of milestone M2, but DEC-001 is Proposed" in output
    assert "The user must confirm it as Decided with /write-design first." in output
    assert logged_calls(planned.folder.parent / "claude.log") == []


def test_runner_refuses_a_dirty_tree(planned: Sandbox) -> None:
    (planned.folder / "notes.txt").write_text("x", encoding="utf-8")
    code, output = run_runner(planned)
    assert code == 1
    assert "git status is not clean" in output
    assert logged_calls(planned.folder.parent / "claude.log") == []


def test_runner_refuses_documents_that_do_not_agree(planned: Sandbox) -> None:
    commit_plan(planned, PLAN.replace("R1.", "PAY-001."), "Name a requirement the spec lacks")
    code, output = run_runner(planned)
    assert code == 1
    assert "python scripts/spec_coverage.py --consistency failed" in output
    assert "docs/plan.md names PAY-001, which is not a requirement row of docs/spec.md." in output
    assert logged_calls(planned.folder.parent / "claude.log") == []
    assert branches(planned) == ["main"]


def test_findings_are_repaired_and_the_last_review_counts_what_stays(planned: Sandbox) -> None:
    planned.env["FAKE_CLAUDE_STATE"] = "findings"
    code, output = run_runner(planned, "--end", "1")
    assert code == 0, output
    assert kinds(planned) == [*M1_SESSIONS, "repair M1", "review M1"]
    calls = logged_calls(planned.folder.parent / "claude.log")
    assert [denied_tools(call) for call in calls[2:]] == [
        DENIED_TO_REVIEW,
        DENIED_TO_BUILD,
        DENIED_TO_REVIEW,
    ]
    assert {call[call.index("--model") + 1] for call in calls} == {"sonnet"}
    # The repair session got the two findings of the first review.
    repair = sessions(planned)[3]["prompt"].splitlines()
    assert [line for line in repair if line.startswith("FINDING:")] == M1_FINDINGS
    # The last review kept one finding: the table counts it, and the milestone still finished.
    assert table_cells(output, "M1")[5:] == ["1", "1", "done"]
    assert subjects(planned, "-2") == ["M1: review repairs", "M1: First"]
    assert planned.remote_head() == planned.git("rev-parse", "HEAD")
    assert branches(planned) == ["main"]
    logs = {p.name for p in (planned.folder / ".claude" / "logs").iterdir()}
    assert {"M1-review.log", "M1-repair.log", "M1-review-last.log"} <= logs


def test_a_repair_that_rejects_every_finding_commits_nothing(planned: Sandbox) -> None:
    planned.env["FAKE_CLAUDE_STATE"] = "rejected"
    code, output = run_runner(planned, "--end", "1")
    assert code == 0, output
    assert kinds(planned) == [*M1_SESSIONS, "repair M1", "review M1"]
    assert subjects(planned, "-2") == ["M1: First", "Plan M1 and M2"]
    assert table_cells(output, "M1")[5:] == ["1", "2", "done"]
    repair_log = planned.folder / ".claude" / "logs" / "M1-repair.log"
    assert repair_log.read_text("utf-8").count("REJECTED: FINDING:") == 2


def test_a_review_that_changes_a_file_cannot_change_the_branch(planned: Sandbox) -> None:
    planned.env["FAKE_CLAUDE_STATE"] = "review-edits"
    code, output = run_runner(planned, "--end", "1")
    assert code == 0, output
    # The review ran in a worktree that the runner deleted: the change did not reach the branch.
    assert kinds(planned) == M1_SESSIONS
    assert "# reviewed" not in (planned.folder / "src" / "m1.py").read_text("utf-8")
    log = (planned.folder / ".claude" / "logs" / "M1-review.log").read_text("utf-8")
    assert "WARNING: the review changed its worktree" in log
    assert subjects(planned, "-1") == ["M1: First"]
    assert planned.git("worktree", "list").count("\n") == 0


def test_a_repair_session_that_changes_a_test_does_not_count(planned: Sandbox) -> None:
    planned.env["FAKE_CLAUDE_STATE"] = "repair-tamper"
    code, output = run_runner(planned, "--retries", "0", "--end", "1")
    assert code == 1
    assert "the repair session changed files in tests/: tests/unit/test_m1.py" in output
    assert kinds(planned) == [*M1_SESSIONS, "repair M1"]
    assert subjects(planned, "-1", "main") == ["Plan M1 and M2"]


def test_a_failed_push_keeps_the_branch_and_says_what_to_do(planned: Sandbox) -> None:
    planned.env["FAKE_CLAUDE_STATE"] = "no-remote"
    code, output = run_runner(planned)
    assert code == 1
    assert "ERROR: milestone M1 in docs/plan.md is merged, but git push failed." in output
    assert "git branch -d milestone/M1" in output
    assert planned.git("rev-parse", "--abbrev-ref", "HEAD") == "main"
    assert subjects(planned, "-1") == ["M1: First"]
    assert "milestone/M1" in branches(planned)
    assert kinds(planned) == M1_SESSIONS
    assert table_cells(output, "M1")[-1] == "failed"


def human_plan() -> str:
    """Return the plan with a human test for M1, in its row and in its block."""
    plan = PLAN.replace("sonnet | low | no |", "sonnet | low | yes |")
    return plan.replace("- **Refs:** R1.", f"- **Refs:** R1.\n{HUMAN_TEST}")


def test_a_confirmed_human_test_lets_the_run_go_on(planned: Sandbox) -> None:
    commit_plan(planned, human_plan(), "Give M1 a human test")
    code, output = run_runner(planned, typed="  YES \n")
    assert code == 0, output
    assert "Milestone M1 in docs/plan.md is merged and pushed. Do its human test now:" in output
    assert "Start the app and open the first page.\n  The page shows 1.\n" in output
    assert "Milestones M1 to M2 in docs/plan.md are done." in output
    assert kinds(planned) == M1_SESSIONS + M2_SESSIONS


@pytest.mark.parametrize("typed", ["no\n", ""])
def test_a_human_test_that_is_not_confirmed_stops_the_run(planned: Sandbox, typed: str) -> None:
    commit_plan(planned, human_plan(), "Give M1 a human test")
    code, output = run_runner(planned, typed=typed)
    assert code == 1
    assert "The human test of milestone M1 in docs/plan.md is not confirmed." in output
    assert "/sherpa: it becomes a fix milestone" in output
    assert "Run the runner again to continue with the next milestone." in output
    # The question comes after the merge and the push, and the next milestone did not start.
    assert subjects(planned, "-1") == ["M1: First"]
    assert planned.remote_head() == planned.git("rev-parse", "HEAD")
    assert kinds(planned) == M1_SESSIONS
    assert table_cells(output, "M1")[-1] == "done"


def human_test_session(runner: ModuleType, project: Path, answers: list[str | None]) -> object:
    """Return a session whose console takes the next of the answers for each question."""
    console = runner.Console(use_color=False, ask=lambda: answers.pop(0))
    state = runner.RunState(total=1, stopwatch=runner.Stopwatch(lambda: 0.0))
    options = runner.Options(None, None, 1, False, 90)
    return runner.Session(runner.Paths(project), console, state, 1, 1, options, "main")


def test_the_question_of_a_human_test_takes_an_injected_answer(
    built: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    runner = load_runner(built)
    row = runner.Row(1, "First", "sonnet", "low", "open", "yes")
    block = ["### M1 — First", "", *HUMAN_TEST.splitlines()]
    running = runner.Running(row, runner.Stopwatch(), saved=runner.SavedTests(block, {}))
    runner.ask_human_test(human_test_session(runner, built, [" Yes "]), running)
    assert "Type yes when the test passed" in capsys.readouterr().out
    for answer in ("y", None):
        with pytest.raises(runner.RunStoppedError) as stop:
            runner.ask_human_test(human_test_session(runner, built, [answer]), running)
        assert stop.value.color == "yellow"
    # A milestone with no Human test entry asks nothing: no answer is taken.
    plain = runner.Running(row, runner.Stopwatch(), saved=runner.SavedTests(block[:1], {}))
    runner.ask_human_test(human_test_session(runner, built, []), plain)


def add_live_check(sandbox: Sandbox, ceiling: str, plan: str) -> None:
    """Give the project a plan with no milestone, and one live check.

    The live check passes when the budget ceiling that it gets is `ceiling`.
    """
    live = sandbox.folder / "tests" / "live"
    live.mkdir()
    check = f'assert os.environ["LIVE_BUDGET_CEILING"] == "{ceiling}"'
    test = f"import os\n\n\ndef test_live_service() -> None:\n    {check}\n"
    (live / "test_live_service.py").write_text(test, encoding="utf-8")
    commit_plan(sandbox, plan, "Add a live check")


def test_the_live_checks_run_when_the_range_is_done(planned: Sandbox) -> None:
    add_live_check(planned, "1", NO_MILESTONES + LIVE_APPROVAL)
    code, output = run_runner(planned)
    assert code == 0, output
    assert output.strip().splitlines()[-2:] == [
        "Milestones M0 to M0 in docs/plan.md are done.",
        "Live checks: passed.",
    ]


def test_live_checks_without_an_approval_are_not_run(planned: Sandbox) -> None:
    add_live_check(planned, "1", NO_MILESTONES)
    code, output = run_runner(planned)
    assert code == 0, output
    assert "Live checks: not run (docs/plan.md has no approval with a budget ceiling)." in output


def test_failed_live_checks_end_the_run_with_an_error(planned: Sandbox) -> None:
    add_live_check(planned, "2", NO_MILESTONES + LIVE_APPROVAL)
    code, output = run_runner(planned)
    assert code == 1
    assert "Milestones M0 to M0 in docs/plan.md are done." in output
    assert "Live checks: failed." in output
    assert "test_live_service" in output


def test_a_pinned_model_id_is_accepted(built: Path) -> None:
    runner = load_runner(built)
    for model in ("sonnet", "claude-sonnet-5-5", "claude-opus-4-1-20250805"):
        assert runner.row_problem(runner.Row(1, "A", model, "low", "open")) is None, model
    for model in ("claude-gpt-4", "claude-sonnet", "sonnet-5-5", "claude-sonnet-5 5"):
        assert "Model" in runner.row_problem(runner.Row(1, "A", model, "low", "open")), model


def test_the_table_shows_each_milestone_and_the_total(built: Path) -> None:
    runner = load_runner(built)
    state = runner.RunState(total=2, stopwatch=runner.Stopwatch(lambda: 0.0))
    state.results.append(runner.Result(1, "First", "sonnet", "low", "", 65.0, "done", 2, 3))
    state.running = runner.Running(runner.Row(2, "Second", "opus", "max", "open"), state.stopwatch)
    lines = runner.table_lines(state, runner.Console(use_color=False), 100)
    header = [cell.strip() for cell in lines[1].strip("│").split("│")]
    assert header[5:] == ["Decisions", "Findings", "Result"]
    cells = [cell.strip() for cell in lines[3].strip("│").split("│")]
    assert cells == ["M1", "First", "sonnet", "low", "01:05", "2", "3", "done"]
    assert "running" in lines[4]
    total = [cell.strip() for cell in lines[6].strip("│").split("│")]
    assert total == ["", "", "", "Total", "00:00", "", "", ""]
    assert lines[-2].rstrip("│ ").endswith("50%  1/2")
    assert len({len(line) for line in lines}) == 1


def test_the_planned_milestones_are_grey_rows_and_the_bar_counts_the_done_ones(
    built: Path,
) -> None:
    runner = load_runner(built)
    rows = [runner.Row(n, f"Step {n}", "sonnet", "low", "open") for n in (1, 2, 3, 4)]
    state = runner.RunState(total=4, stopwatch=runner.Stopwatch(lambda: 0.0), planned=rows)
    state.results.append(runner.Result(1, "Step 1", "sonnet", "low", "", 5.0, "done", 0))
    state.running = runner.Running(rows[1], state.stopwatch)
    plain = runner.table_lines(state, runner.Console(use_color=False), 120)
    planned = [line for line in plain if "planned" in line]
    assert [line.split("│")[1].strip() for line in planned] == ["M3", "M4"]
    assert [cell.strip() for cell in planned[0].strip("│").split("│")][4:] == [
        "-",
        "-",
        "-",
        "planned",
    ]
    bar = plain[-2]
    assert bar.endswith(" 25%  1/4 │")
    assert bar.count("█") * 3 == pytest.approx(bar.count("░"), abs=2)
    colored = runner.table_lines(state, runner.Console(use_color=True), 120)
    assert sum("\x1b[38;5;238m" in line for line in colored) == 2


def test_a_long_title_is_cut_to_fit_the_terminal(built: Path) -> None:
    runner = load_runner(built)
    state = runner.RunState(total=1, stopwatch=runner.Stopwatch(lambda: 0.0))
    state.results.append(runner.Result(1, "T" * 80, "sonnet", "low", "", 1.0, "done", 0))
    lines = runner.table_lines(state, runner.Console(use_color=False), 90)
    assert max(len(line) for line in lines) <= 90
    assert "…" in lines[3]


def test_decision_lines_are_counted(built: Path) -> None:
    runner = load_runner(built)
    report = ["Done.", "DECISION: a | b | DEC-007", "- **DECISION: c | d | none**", "No decision."]
    assert len(runner.decision_lines(report)) == 2


def test_finding_lines_are_counted(built: Path) -> None:
    runner = load_runner(built)
    review = [
        "BUILT-IN REVIEW: not available",
        "FINDING: high | src/a.py:3 | Dead Code | Delete it.",
        "- **FINDING: low | src/b.py:9 | Comments | Delete the comment.**",
        "No finding in the tests.",
    ]
    assert len(runner.finding_lines(review)) == 2
    assert runner.finding_lines(["NO FINDINGS"]) == []


def test_changed_tests_lists_edited_added_and_removed_files(built: Path) -> None:
    runner = load_runner(built)
    before = {"tests/a.py": "1", "tests/b.py": "2", "tests/c.py": "3"}
    after = {"tests/a.py": "1", "tests/b.py": "9", "tests/d.py": "4"}
    assert runner.changed_tests(before, after) == ["tests/b.py", "tests/c.py", "tests/d.py"]


def test_a_test_file_is_hashed_with_lf_line_ends(built: Path) -> None:
    runner = load_runner(built)
    test = built / "tests" / "unit" / "test_a.py"
    test.write_bytes(b"def test_a() -> None:\r\n    assert True\r\n")
    before = runner.snapshot_tests(built)
    assert "tests/unit/test_a.py" in before
    # Git checks the file out again with LF, as after a blocked milestone: it did not change.
    test.write_bytes(b"def test_a() -> None:\n    assert True\n")
    assert runner.changed_tests(before, runner.snapshot_tests(built)) == []
    test.write_bytes(b"def test_a() -> None:\n    assert 1\n")
    assert runner.changed_tests(before, runner.snapshot_tests(built)) == ["tests/unit/test_a.py"]


def test_runner_checks_the_requirement_ids_of_the_block(built: Path) -> None:
    runner = load_runner(built)
    spec = built / "docs" / "spec.md"
    spec.write_text(spec.read_text("utf-8") + "\n| PAY-001 | The system shall pay. |\n", "utf-8")
    block = ["### M1 — Pay", "", "- **Refs:** PAY-001, DEC-002.", "- **Tests first:** unit: x."]
    problem = runner.coverage_problem(built, 1, block)
    assert "spec_coverage.py M1 failed" in problem
    assert "no test and no Manual entry for PAY-001" in problem
    test = built / "tests" / "unit" / "test_pay.py"
    test.write_text("def test_pay_001_pays() -> None:\n    assert True\n", encoding="utf-8")
    assert runner.coverage_problem(built, 1, block) is None


def test_a_milestone_may_not_change_the_spec(built: Path) -> None:
    runner = load_runner(built)
    assert runner.LOCKED_PATHS == ("docs/spec.md",)
    assert runner.Paths(built).settings.is_file()


def plan_guide(project: Path) -> str:
    """Return the text of the milestone guide that /write-plan reads."""
    guide = project / ".claude" / "skills" / "write-plan" / "references" / "milestone-guide.md"
    return guide.read_text(encoding="utf-8")


def test_the_write_plan_example_is_a_row_and_block_the_runner_reads(built: Path) -> None:
    runner = load_runner(built)
    lines = plan_guide(built).splitlines()
    [row_line] = [line for line in lines if line.startswith("| **M3**")]
    row = runner.parse_row(row_line)
    assert (row.id, row.title, row.model, row.effort, row.status) == (
        3,
        "Record a payment",
        "sonnet",
        "medium",
        "open",
    )
    assert row.human_test in {"yes", "no"}
    assert runner.row_problem(row) is None
    block = runner.milestone_block(lines, 3)
    assert block[0] == "### M3 — Record a payment"
    # The row says whether the block has a Human test entry for the runner to print.
    assert bool(runner.block_entry(block, "Human test")) == (row.human_test == "yes")


def test_the_write_plan_guide_names_every_model_and_effort(built: Path) -> None:
    runner = load_runner(built)
    guide = plan_guide(built)
    values = [*runner.VALID_MODELS, *runner.VALID_EFFORTS]
    assert [value for value in values if f"`{value}`" not in guide] == []


def test_a_plan_with_a_row_of_five_cells_is_refused(built: Path) -> None:
    # A plan from before the column Human test. Without this check the runner reads no row and
    # reports an empty range as done.
    runner = load_runner(built)
    old = "| **M4** Pay | Takes a payment | opus | max | open |"
    new = "| **M5** Refund | Gives it back | opus | max | no | open |"
    assert runner.unread_rows(["## Milestones at a glance", old, new]) == [old]
    runner.check_rows([new])
    with pytest.raises(runner.RunStoppedError, match="six cells"):
        runner.check_rows([old, new])


# --- the test writer, its folder and its checks (USER-17, rank 15) -------------------------------


def test_the_test_session_runs_in_a_folder_without_the_code(planned: Sandbox) -> None:
    code, output = run_runner(planned, "--end", "1")
    assert code == 0, output
    [test] = [session for session in sessions(planned) if session["kind"] == "test"]
    assert test["folder"] != str(planned.folder)
    assert (test["src"], test["git"], test["agents"]) == (False, False, False)
    # The folder is deleted after the session, and the test came back to the project.
    assert not Path(test["folder"]).exists()
    assert "tests/unit/test_m1.py" in planned.git("show", "--name-only", "--format=", "HEAD")


def test_a_test_that_fails_for_a_wrong_reason_gets_one_round_of_repair(planned: Sandbox) -> None:
    planned.env["FAKE_CLAUDE_STATE"] = "bad-test"
    code, output = run_runner(planned, "--end", "1")
    assert code == 0, output
    assert kinds(planned) == ["test M1", "test-fix M1", "build M1", "review M1"]
    fix = sessions(planned)[1]["prompt"]
    assert "ModuleNotFoundError: No module named 'tests.unit.helpers_m1'" in fix
    assert "Each problem gives the type and the message of an error, and no line of the code" in fix
    assert (planned.folder / "tests" / "unit" / "test_m1.py").read_text("utf-8") == M1_TEST


def test_a_test_that_stays_wrong_stops_the_milestone(planned: Sandbox) -> None:
    planned.env["FAKE_CLAUDE_STATE"] = "bad-test-stays"
    code, output = run_runner(planned, "--end", "1", "--retries", "0")
    assert code == 1
    assert (
        "Milestone M1 in docs/plan.md stopped: the runner's checks of the tests failed:" in output
    )
    assert "No module named 'tests.unit.helpers_m1'" in output
    assert kinds(planned) == ["test M1", "test-fix M1"]


def test_another_test_writer_gets_agents_md_and_its_own_command(planned: Sandbox) -> None:
    shim(planned.fake_bin, "codex", FAKE_CLAUDE)
    code, output = run_runner(planned, "--end", "1", "--test-writer", "codex")
    assert code == 0, output
    [test] = [session for session in sessions(planned) if session["kind"] == "test"]
    assert test["agents"] is True
    assert (
        "Write the failing tests of milestone M1 (First) of docs/plan.md, as AGENTS.md"
        in (test["prompt"])
    )
    calls = logged_calls(planned.folder.parent / "claude.log")
    codex = [call for call in calls if call[:1] == ["exec"]]
    # The start check, then the test session; the build and the review stay with claude.
    assert len(codex) == 2
    assert {"--sandbox", "workspace-write", "--skip-git-repo-check", "-"} <= set(codex[1])
    assert kinds(planned) == M1_SESSIONS


def test_the_writer_recorded_in_the_config_is_used(planned: Sandbox) -> None:
    shim(planned.fake_bin, "agy", FAKE_CLAUDE)
    config = {"writer": "antigravity", "model": "gemini-4-neon-high", "effort": "high"}
    commit_file(planned, "config/test-writer.json", json.dumps(config), "Choose Antigravity")
    planned.git("push")
    code, output = run_runner(planned, "--end", "1")
    assert code == 0, output
    calls = logged_calls(planned.folder.parent / "claude.log")
    agy = [call for call in calls if "--dangerously-skip-permissions" in call]
    assert len(agy) == 2
    assert agy[1][agy[1].index("--model") + 1] == "gemini-4-neon-high"


def test_review_findings_about_tests_go_to_a_test_session(planned: Sandbox) -> None:
    planned.env["FAKE_CLAUDE_STATE"] = "review-tests"
    code, output = run_runner(planned, "--end", "1")
    assert code == 0, output
    assert kinds(planned) == [*M1_SESSIONS, "review-tests M1", "rebuild M1", "review M1"]
    review_tests = sessions(planned)[3]
    assert "FINDING: medium | tests/unit/test_m1.py:4 | Weak Test" in review_tests["prompt"]
    assert review_tests["src"] is False
    assert subjects(planned, "-2") == ["M1: test repairs", "M1: First"]
    assert "test_m1_value_is_an_int" in planned.git("show", "HEAD:tests/unit/test_m1.py")


def approve_review_block(sandbox: Sandbox, decision: str) -> None:
    """Do what the user does after a review blocked M1: approve the last block, and commit."""
    plan = sandbox.folder / "docs" / "plan.md"
    text = plan.read_text(encoding="utf-8").replace("| blocked |", "| approved |")
    head, last, tail = text.rpartition("    2. Repair it in this way: <your instruction>.")
    plan.write_text(f"{head}{last}\n- **Approval:** {decision}{tail}", encoding="utf-8")
    sandbox.git("commit", "-am", "Approve M1")


def test_a_high_finding_of_the_last_review_blocks_the_merge(planned: Sandbox) -> None:
    planned.env["FAKE_CLAUDE_STATE"] = "blocking"
    code, output = run_runner(planned, "--end", "1")
    assert code == 1
    assert "Milestone M1 in docs/plan.md waits for your approval." in output
    assert "FINDING: high | src/m1.py:7 | Error Handling" in output
    assert kinds(planned) == [*M1_SESSIONS, "repair M1", "review M1"]
    # The base branch got the blocked plan; the branch keeps the build and its repair.
    assert subjects(planned, "-1") == ["M1: blocked"]
    assert planned.remote_head() == planned.git("rev-parse", "HEAD")
    assert subjects(planned, "-2", "milestone/M1") == ["M1: review repairs", "M1: First"]
    plan = (planned.folder / "docs" / "plan.md").read_text("utf-8")
    assert "| **M1** First | Does one thing | sonnet | low | no | blocked |" in plan


def test_an_approved_review_block_is_merged_on_the_next_run(planned: Sandbox) -> None:
    planned.env["FAKE_CLAUDE_STATE"] = "blocking"
    run_runner(planned, "--end", "1")
    approve_review_block(planned, "Merge it as it is.")
    code, output = run_runner(planned, "--end", "1")
    assert code == 0, output
    # The build exists: the runner rebased the branch on the approval, and gave the decision and
    # the finding of the block to a repair session. No new review ran (RUN-08).
    assert kinds(planned)[5:] == ["repair M1"]
    repair = sessions(planned)[5]["prompt"]
    assert "The user's decision on an earlier review: Merge it as it is." in repair
    assert "FINDING: high | src/m1.py:7 | Error Handling | Raise on a bad value." in repair
    # The repair changed nothing, so it made no commit, and the code the user saw merged.
    assert subjects(planned, "-3") == ["M1: review repairs", "M1: First", "Approve M1"]
    plan = (planned.folder / "docs" / "plan.md").read_text("utf-8")
    assert "**M1**" not in plan
    assert "### M1" not in plan
    assert branches(planned) == ["main"]


def block_m1_twice(planned: Sandbox) -> str:
    """Let the last review block M1, approve a repair, and run again; return the output."""
    planned.env["FAKE_CLAUDE_STATE"] = "blocking-repair"
    run_runner(planned, "--end", "1")
    approve_review_block(planned, "Repair it in this way: raise on a bad value.")
    code, output = run_runner(planned, "--end", "1")
    assert code == 1
    return output


def test_a_repair_after_an_approval_gets_a_last_review_that_can_block_again(
    planned: Sandbox,
) -> None:
    output = block_m1_twice(planned)
    # The repair changed the code after the approval, so the last review checked the change, and
    # its high finding blocked the milestone again.
    assert "Milestone M1 in docs/plan.md waits for your approval." in output
    assert kinds(planned)[5:] == ["repair M1", "review M1"]
    assert subjects(planned, "-1", "milestone/M1") == ["M1: review repairs"]
    plan = (planned.folder / "docs" / "plan.md").read_text("utf-8")
    assert plan.count("- **Blocked:**") == 2


def test_the_next_approval_answers_the_last_block(planned: Sandbox) -> None:
    block_m1_twice(planned)
    approve_review_block(planned, "Merge it as it is.")
    code, output = run_runner(planned, "--end", "1")
    assert code == 0, output
    assert kinds(planned)[7:] == ["repair M1"]
    repair = sessions(planned)[7]["prompt"]
    assert "The user's decision on an earlier review: Merge it as it is." in repair
    assert "Repair it in this way" not in repair
    assert branches(planned) == ["main"]


def test_the_last_entry_of_a_block_is_read(built: Path) -> None:
    runner = load_runner(built)
    block = [
        "### M1 — First",
        "- **Blocked:** one",
        "- **Approval:** first",
        "- **Blocked:** two",
        "  - FINDING: high | src/a.py:1 | Dead Code | Delete it.",
        "- **Approval:** second",
    ]
    assert runner.last_block_entry(block, "Blocked") == [
        "two",
        "  - FINDING: high | src/a.py:1 | Dead Code | Delete it.",
    ]
    assert runner.last_block_entry(block, "Approval") == ["second"]
    assert runner.last_block_entry(block, "Human test") == []


def test_after_an_approved_wrong_test_the_last_review_blocks_as_usual(planned: Sandbox) -> None:
    planned.env["FAKE_CLAUDE_STATE"] = "wrong-test"
    run_runner(planned, "--end", "1")
    approve_review_block(planned, "Keep the test.")
    planned.env["FAKE_CLAUDE_STATE"] = "blocking"
    code, output = run_runner(planned, "--end", "1")
    # The approval answered a question about a test, not a finding of the review (RUN-08).
    assert code == 1
    assert "Milestone M1 in docs/plan.md waits for your approval." in output
    assert "FINDING: high | src/m1.py:7 | Error Handling" in output
    assert kinds(planned)[5:] == [
        "retest M1",
        "build M1",
        "review M1",
        "repair M1",
        "review M1",
    ]


@pytest.mark.parametrize(
    ("finding", "blocks"),
    [
        ("FINDING: high | src/a.py:3 | Dead Code | Delete it.", True),
        ("FINDING: medium | src/a.py:3 | PAY-001 | Refuse the refund.", True),
        ("- **FINDING: medium | tests/a.py:9 | NFR-002 | Add the test.**", True),
        ("- **FINDING: low | tests/a.py:9 | NFR-002 | Add the test.**", False),
        ("FINDING: low | src/a.py:3 | SLUG-005 | Name the case.", False),
        ("FINDING: medium | src/a.py:3 | DEC-004 | Follow the decision.", False),
        ("FINDING: medium | src/a.py:3 | Comments | Say why.", False),
        ("FINDING: low | src/a.py:3 | Comments | Delete the comment.", False),
    ],
)
def test_a_finding_blocks_when_it_is_high_or_medium_on_a_requirement(
    built: Path, finding: str, blocks: bool
) -> None:
    runner = load_runner(built)
    assert runner.blocks_merge(finding) is blocks


def test_a_finding_goes_to_the_session_of_the_file_it_names(built: Path) -> None:
    runner = load_runner(built)
    assert runner.is_test_finding("FINDING: low | tests/unit/test_a.py:3 | Weak Test | x")
    assert runner.is_test_finding("FINDING: low | tests\\unit\\test_a.py:3 | Weak Test | x")
    assert not runner.is_test_finding("FINDING: low | src/a.py:3 | Dead Code | x")


def test_the_blocked_entry_of_a_review_names_the_kind_and_the_file(built: Path) -> None:
    runner = load_runner(built)
    finding = "FINDING: medium | src/a.py:3 | PAY-001 | Refuse the refund."
    plan = runner.plan_with_block(PLAN.splitlines(), 1, runner.review_block_entry([finding]))
    block = runner.milestone_block(plan, 1)
    blocked = runner.block_entry(block, "Blocked")
    assert f"  - {finding} (requirement PAY-001 in docs/spec.md)" in blocked
    assert runner.parse_plan_rows(plan)[0].status == "blocked"
    assert runner.milestone_block(plan, 2) == runner.milestone_block(PLAN.splitlines(), 2)


def test_a_plan_without_a_milestone_keeps_the_others(built: Path) -> None:
    runner = load_runner(built)
    plan = runner.plan_without_milestone(PLAN.splitlines(), 1)
    assert [row.id for row in runner.parse_plan_rows(plan)] == [2]
    assert runner.milestone_block(plan, 1) == []
    assert runner.milestone_block(plan, 2)[0] == "### M2 — Second"


@pytest.mark.parametrize(
    "case",
    [
        ("t::a", "assert 1 == 2", "tests\\unit\\test_a.py:5: AssertionError", True),
        ("t", "collection failure", "E   ModuleNotFoundError: No module named 'src.m1'", True),
        ("t", "collection failure", "E   ImportError: cannot import name 'f' from 'src.m1'", True),
        ("t::a", "KeyError: 'x'", "src\\m1.py:9: KeyError", True),
        ("t", "collection failure", "E   ModuleNotFoundError: No module named 'tests.help'", False),
        ("t::a", "failed on setup with \"fixture 'db' not found\"", "", False),
        ("t::a", "NameError", "E   NameError: name 'x' is not defined", False),
        (
            "t::a",
            "TypeError",
            "E   TypeError: f() takes 1 argument\ntests/a.py:3: TypeError",
            False,
        ),
        ("t", "collection failure", "E   SyntaxError: '(' was never closed", False),
    ],
)
def test_a_new_test_may_fail_only_because_the_behavior_is_missing(
    built: Path, case: tuple[str, str, str, bool]
) -> None:
    runner = load_runner(built)
    test, message, text, valid = case
    failure = runner._failure(test, message, text)
    problem = runner.failure_problem(failure, ["src.m1"])
    assert (problem is None) is valid, problem


def test_the_owner_entry_gives_the_modules_of_the_milestone(built: Path) -> None:
    runner = load_runner(built)
    block = ["### M1 — Pay", "- **Owner:** `src/store/` and `src/pay.py`, `main.py`."]
    assert runner.owner_modules(block) == ["main", "src.pay", "src.store"]
    assert runner.owned("src.store.files", ["src.store"])
    assert runner.owned("src", ["src.store"])
    assert not runner.owned("src.other", ["src.store"])


def test_the_runner_reads_the_failures_of_a_junit_report(built: Path, tmp_path: Path) -> None:
    runner = load_runner(built)
    report = tmp_path / "report.xml"
    report.write_text(
        '<testsuites><testsuite><testcase classname="tests.unit.test_a" name="test_x">'
        '<failure message="assert 1 == 2">tests/unit/test_a.py:5: AssertionError</failure>'
        '</testcase><testcase classname="" name="tests.unit.test_b">'
        "<error message=\"collection failure\">E   NameError: name 'y' is not defined</error>"
        "</testcase></testsuite></testsuites>",
        encoding="utf-8",
    )
    failures = runner.read_failures(report)
    assert [(f.test, f.kind) for f in failures] == [
        ("tests.unit.test_a::test_x", "AssertionError"),
        ("tests.unit.test_b", "NameError"),
    ]


@pytest.mark.parametrize("writer", ["claude", "codex", "antigravity", "copilot"])
def test_each_writer_runs_with_its_prompts_off(built: Path, writer: str) -> None:
    runner = load_runner(built)
    row = runner.Row(3, "Login", "sonnet", "low", "open")
    command, stdin = runner.writer_command(
        runner.Writer(writer, "model-x", "high"), row, runner.SESSION_TEST, "the prompt"
    )
    expected = {
        "claude": ["--permission-mode", "bypassPermissions"],
        "codex": ["--sandbox", "workspace-write"],
        "antigravity": ["--dangerously-skip-permissions"],
        "copilot": ["--allow-all-tools", "--no-ask-user"],
    }[writer]
    assert all(option in command for option in expected)
    assert command[command.index("--model") + 1] == "model-x"
    # Claude and Codex read the prompt on standard input; the others take it as an argument.
    assert (stdin == "the prompt") is (writer in {"claude", "codex"})
    assert ("the prompt" in command) is (writer in {"antigravity", "copilot"})


def test_agents_md_holds_the_rules_of_the_project(built: Path) -> None:
    runner = load_runner(built)
    text = runner.agents_text(built)
    assert text.startswith("# AGENTS.md\n")
    assert "## CLAUDE.md" in text
    assert "## .claude/rules/python.md" in text
    assert "## .claude/skills/write-tests/SKILL.md" in text
    assert "a missing module that the Owner entry" not in text  # that is the fix prompt
    assert "Put every import at the top of a test file." in text
    assert "paths:" not in text  # the frontmatter of the rules files is left out


def test_an_unknown_test_writer_is_refused(built: Path) -> None:
    runner = load_runner(built)
    assert runner.load_writer(built, "") == runner.Writer("claude", "", "")
    (built / "config" / "test-writer.json").write_text('{"writer": "gpt"}', encoding="utf-8")
    with pytest.raises(runner.RunStoppedError, match="not one of"):
        runner.load_writer(built, "")
    assert runner.load_writer(built, "codex") == runner.Writer("codex")


def test_the_sessions_get_the_folders_of_the_environment_first(built: Path) -> None:
    runner = load_runner(built)
    environment = runner.session_environment()
    first = environment["PATH"].split(os.pathsep)[0]
    assert Path(first) == runner.environment_folders(Path(sys.prefix))[0]
    runner.check_session_python(environment)


# --- one step in chat (C2) ------------------------------------------------------------------------


def test_tests_only_writes_the_tests_of_one_milestone_in_chat(planned: Sandbox) -> None:
    planned.git("switch", "-c", "milestone/M1")
    code, output = run_runner(planned, "--tests-only", "M1")
    assert code == 0, output
    assert "The tests of milestone M1 in docs/plan.md are written and pass the checks." in output
    assert (planned.folder / "tests" / "unit" / "test_m1.py").read_text("utf-8") == M1_TEST
    assert subjects(planned, "-1") == ["Plan M1 and M2"]
    assert kinds(planned) == ["test M1"]


def test_review_only_reviews_in_a_worktree_and_routes_test_findings(planned: Sandbox) -> None:
    planned.git("switch", "-c", "milestone/M1")
    run_runner(planned, "--tests-only", "M1")
    m1_code = '"""M1."""\n\n\ndef value() -> int:\n    """1."""\n    return 1\n'
    commit_file(planned, "src/m1.py", m1_code, "M1: First")
    planned.env["FAKE_CLAUDE_STATE"] = "review-tests"
    code, output = run_runner(planned, "--review-only", "M1")
    assert code == 0, output
    assert "FINDING: medium | tests/unit/test_m1.py:4 | Weak Test" in output
    assert "--tests-only M1 --review-findings" in output
    code, output = run_runner(planned, "--tests-only", "M1", "--review-findings")
    assert code == 0, output
    assert kinds(planned) == ["test M1", "review M1", "review-tests M1"]
    assert "test_m1_value_is_an_int" in (
        planned.folder / "tests" / "unit" / "test_m1.py"
    ).read_text("utf-8")


def test_a_session_after_the_review_that_finds_a_wrong_test_blocks_the_milestone(
    planned: Sandbox,
) -> None:
    planned.env["FAKE_CLAUDE_STATE"] = "wrong-test"
    code, output = run_runner(planned, "--end", "1")
    assert code == 1
    assert "A session after the review found a test that looks wrong" in output
    assert "BLOCKED: tests/unit/test_m1.py | the type check looks wrong | Keep the test?" in output
    assert kinds(planned) == [*M1_SESSIONS, "review-tests M1", "rebuild M1"]
    # The rebuild left its work uncommitted: the runner kept it as partial work in the branch.
    assert subjects(planned, "-2", "milestone/M1") == ["M1: partial work", "M1: First"]
    assert subjects(planned, "-1") == ["M1: blocked"]


def test_an_approved_wrong_test_goes_to_a_test_session_then_the_build(planned: Sandbox) -> None:
    planned.env["FAKE_CLAUDE_STATE"] = "wrong-test"
    run_runner(planned, "--end", "1")
    approve_review_block(planned, "Keep the test.")
    code, output = run_runner(planned, "--end", "1")
    assert code == 0, output
    # The decision went to a test session first, then the build went on from the partial work.
    assert kinds(planned)[5:] == ["retest M1", "build M1", "review M1"]
    assert "The decision:\nKeep the test.\nRules:" in sessions(planned)[5]["prompt"]
    assert subjects(planned, "-2") == ["M1: First", "Approve M1"]
    assert "**M1**" not in (planned.folder / "docs" / "plan.md").read_text("utf-8")
    assert branches(planned) == ["main"]


def test_a_repair_or_rebuild_session_reports_a_wrong_test_as_a_blocked_line(built: Path) -> None:
    runner = load_runner(built)
    row = runner.Row(3, "Login", "sonnet", "low", "open")
    line = "`BLOCKED: <the test> | <why it looks wrong> | <the question for the user>`"
    assert line in runner.repair_prompt(row, [])
    assert line in runner.rebuild_prompt(row)
    assert runner.blocked_lines(["Done.", "- **BLOCKED: a | b | c**", "BLOCKED: d | e | f"]) == [
        "- **BLOCKED: a | b | c**",
        "BLOCKED: d | e | f",
    ]
