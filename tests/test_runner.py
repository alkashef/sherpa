"""scripts/milestones-runner.py, as a new project gets it: its parts, and whole runs.

The whole runs use a fake `claude` (tests/fake_claude.py) that plays the test session and the
build session of each milestone, and finishes, blocks, or skips it, in a project set up by
init_project.py, with the real git hooks.
"""

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest
from helpers import Sandbox, build, logged_calls, run, shim

FAKE_CLAUDE = Path(__file__).resolve().with_name("fake_claude.py")
FAKE_BUILD = "Edit(./tests/**)"  # only a build session is denied this tool
M1_TEST = "from src.m1 import value\n\n\ndef test_m1_value() -> None:\n    assert value() == 1\n"
PLAN = """# Plan — project-init

**Next milestone number: M3**

## Milestones at a glance

| Milestone | Description | Model | Effort | Status |
| --- | --- | --- | --- | --- |
| **M1** First | Does one thing | sonnet | low | open |
| **M2** Second | Does another | haiku | medium | open |

## Milestones

### M1 — First

- **Refs:** R1.

### M2 — Second

- **Refs:** R2.
"""


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
    (sandbox.folder / "docs" / "plan.md").write_text(PLAN, encoding="utf-8")
    sandbox.git("commit", "-am", "Plan M1 and M2")
    sandbox.git("push")
    return sandbox


def run_runner(sandbox: Sandbox, *options: str) -> tuple[int, str]:
    """Run the project's milestone runner and return its exit code and output."""
    command = [sys.executable, "scripts/milestones-runner.py", *options]
    result = run(command, sandbox.folder, sandbox.env)
    return result.returncode, result.stdout + result.stderr


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
    assert runner.parse_row(filled) == runner.Row(7, "Login", "sonnet", "high", "open")


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
    assert "<n>" not in prompt
    assert "A previous session" not in prompt
    assert "A previous session" in runner.build_prompt(row, True)


def test_test_prompt_starts_the_test_skill_and_keeps_out_of_the_code(built: Path) -> None:
    runner = load_runner(built)
    prompt = runner.build_test_prompt(runner.Row(3, "Login", "sonnet", "low", "open"))
    assert "Run /write-tests for milestone M3 (Login) of docs/plan.md" in prompt
    assert "read the code in src/" in prompt
    assert "commit nothing" in prompt
    assert "<n>" not in prompt


def test_each_session_is_denied_the_other_sessions_files(built: Path) -> None:
    runner = load_runner(built)
    row = runner.Row(3, "Login", "sonnet", "low", "open")
    test_command = runner.session_command(row, runner.SESSION_TEST)
    build_command = runner.session_command(row, runner.SESSION_BUILD)
    assert test_command[test_command.index("--disallowedTools") + 1 :] == [
        "Read(./src/**)",
        "Grep(./src/**)",
        "Glob(./src/**)",
    ]
    assert build_command[build_command.index("--disallowedTools") + 1 :] == [
        "Edit(./tests/**)",
        "Write(./tests/**)",
    ]


def test_no_prompt_names_another_projects_files(built: Path) -> None:
    runner = load_runner(built)
    row = runner.Row(3, "Login", "sonnet", "low", "open")
    prompts = runner.build_prompt(row, True) + runner.build_test_prompt(row, True)
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
    assert "Range M1 to M2 is done." in output
    assert planned.git("log", "-2", "--format=%s").splitlines() == ["M2: Second", "M1: First"]
    assert planned.remote_head() == planned.git("rev-parse", "HEAD")
    calls = logged_calls(planned.folder.parent / "claude.log")
    models = [(call[call.index("--model") + 1], call[call.index("--effort") + 1]) for call in calls]
    # Two sessions for each milestone: the test session, then the build session.
    assert models == [("sonnet", "low")] * 2 + [("haiku", "medium")] * 2
    assert [FAKE_BUILD in call for call in calls] == [False, True, False, True]
    logs = planned.folder / ".claude" / "logs"
    assert len((logs / "timings.csv").read_text("utf-8").splitlines()) == 3
    assert {"M1-test.log", "M1.log", "M1-tests.json"} <= {p.name for p in logs.iterdir()}
    assert "tests/unit/test_m1.py" in planned.git("show", "--name-only", "--format=", "HEAD~1")
    # The Decisions column of the table counts the DECISION line of each build session.
    assert "│ 1 " in output


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
    assert "M1 waits for your approval." in output
    assert "### M1 — First" in output
    assert "which database?" in output
    assert planned.git("log", "-1", "--format=%s") == "M1: blocked"
    assert planned.remote_head() == planned.git("rev-parse", "HEAD")
    # The test session blocked it, so no build session ran.
    assert len(logged_calls(planned.folder.parent / "claude.log")) == 1


def test_runner_waits_at_a_blocked_row(planned: Sandbox) -> None:
    planned.env["FAKE_CLAUDE_STATE"] = "blocked"
    run_runner(planned)
    code, output = run_runner(planned)
    assert code == 1
    assert "M1 waits for your approval." in output
    assert len(logged_calls(planned.folder.parent / "claude.log")) == 1


def test_approved_milestone_runs_again_and_the_run_goes_on(planned: Sandbox) -> None:
    planned.env["FAKE_CLAUDE_STATE"] = "blocked"
    run_runner(planned)
    approve(planned, "Use SQLite.")
    planned.env["FAKE_CLAUDE_STATE"] = ""
    code, output = run_runner(planned)
    assert code == 0, output
    assert planned.git("log", "-3", "--format=%s").splitlines() == [
        "M2: Second",
        "M1: First",
        "Approve M1",
    ]
    assert planned.remote_head() == planned.git("rev-parse", "HEAD")


def test_runner_stops_when_a_milestone_does_not_finish(planned: Sandbox) -> None:
    planned.env["FAKE_CLAUDE_STATE"] = "idle"
    code, output = run_runner(planned)
    assert code == 1
    assert "M1 stopped: its row is still in the plan table" in output
    assert "run again with --resume" in output
    # One test session, then the build session and its one retry.
    calls = logged_calls(planned.folder.parent / "claude.log")
    assert [FAKE_BUILD in call for call in calls] == [False, True, True]


def test_a_session_that_did_not_finish_is_tried_again(planned: Sandbox) -> None:
    planned.env["FAKE_CLAUDE_STATE"] = "retry"
    code, output = run_runner(planned, "--end", "1")
    assert code == 0, output
    assert planned.git("log", "-1", "--format=%s") == "M1: First"
    assert (planned.folder / ".claude" / "logs" / "M1-2.log").is_file()


def test_resume_continues_with_the_build_session(planned: Sandbox) -> None:
    planned.env["FAKE_CLAUDE_STATE"] = "retry"
    code, output = run_runner(planned, "--retries", "0", "--end", "1")
    assert code == 1
    assert "M1 stopped" in output
    # The test session left its test in the tree, so a plain run refuses to start.
    assert (planned.folder / "tests" / "unit" / "test_m1.py").read_text("utf-8") == M1_TEST
    code, output = run_runner(planned, "--end", "1")
    assert code == 1
    assert "git status is not clean" in output
    code, output = run_runner(planned, "--end", "1", "--resume")
    assert code == 0, output
    assert planned.git("log", "-1", "--format=%s") == "M1: First"
    # The first run: a test session and a build session. The resumed run: a build session only.
    calls = logged_calls(planned.folder.parent / "claude.log")
    assert [FAKE_BUILD in call for call in calls] == [False, True, True]


def test_a_build_session_that_changes_a_test_does_not_count(planned: Sandbox) -> None:
    planned.env["FAKE_CLAUDE_STATE"] = "tamper"
    code, output = run_runner(planned, "--retries", "0")
    assert code == 1
    assert "the build session changed files in tests/: tests/unit/test_m1.py" in output


def test_a_milestone_that_changes_the_spec_does_not_count(planned: Sandbox) -> None:
    planned.env["FAKE_CLAUDE_STATE"] = "spec"
    code, output = run_runner(planned, "--retries", "0")
    assert code == 1
    assert "a session changed the spec: docs/spec.md" in output


def test_runner_refuses_a_dirty_tree(planned: Sandbox) -> None:
    (planned.folder / "notes.txt").write_text("x", encoding="utf-8")
    code, output = run_runner(planned)
    assert code == 1
    assert "git status is not clean" in output
    assert logged_calls(planned.folder.parent / "claude.log") == []


def test_a_pinned_model_id_is_accepted(built: Path) -> None:
    runner = load_runner(built)
    for model in ("sonnet", "claude-sonnet-5-5", "claude-opus-4-1-20250805"):
        assert runner.row_problem(runner.Row(1, "A", model, "low", "open")) is None, model
    for model in ("claude-gpt-4", "claude-sonnet", "sonnet-5-5", "claude-sonnet-5 5"):
        assert "Model" in runner.row_problem(runner.Row(1, "A", model, "low", "open")), model


def test_the_table_shows_each_milestone_and_the_total(built: Path) -> None:
    runner = load_runner(built)
    state = runner.RunState(total=2, stopwatch=runner.Stopwatch(lambda: 0.0))
    state.results.append(runner.Result(1, "First", "sonnet", "low", "", 65.0, "done", 2))
    state.running = runner.Running(runner.Row(2, "Second", "opus", "max", "open"), state.stopwatch)
    lines = runner.table_lines(state, runner.Console(use_color=False), 100)
    cells = [cell.strip() for cell in lines[3].strip("│").split("│")]
    assert cells == ["M1", "First", "sonnet", "low", "01:05", "2", "done"]
    assert "running" in lines[4]
    assert "50%  1/2" in lines[-2]
    assert len({len(line) for line in lines}) == 1


def test_a_long_title_is_cut_to_fit_the_terminal(built: Path) -> None:
    runner = load_runner(built)
    state = runner.RunState(total=1, stopwatch=runner.Stopwatch(lambda: 0.0))
    state.results.append(runner.Result(1, "T" * 80, "sonnet", "low", "", 1.0, "done", 0))
    lines = runner.table_lines(state, runner.Console(use_color=False), 70)
    assert max(len(line) for line in lines) <= 70
    assert "…" in lines[3]


def test_decision_lines_are_counted(built: Path) -> None:
    runner = load_runner(built)
    report = ["Done.", "DECISION: a | b | DEC-007", "- **DECISION: c | d | none**", "No decision."]
    assert len(runner.decision_lines(report)) == 2


def test_changed_tests_lists_edited_added_and_removed_files(built: Path) -> None:
    runner = load_runner(built)
    before = {"tests/a.py": "1", "tests/b.py": "2", "tests/c.py": "3"}
    after = {"tests/a.py": "1", "tests/b.py": "9", "tests/d.py": "4"}
    assert runner.changed_tests(before, after) == ["tests/b.py", "tests/c.py", "tests/d.py"]


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
    assert runner.parse_row(row_line) == runner.Row(
        3, "Record a payment", "sonnet", "medium", "open"
    )
    assert runner.row_problem(runner.parse_row(row_line)) is None
    assert runner.milestone_block(lines, 3)[0] == "### M3 — Record a payment"


def test_the_write_plan_guide_names_every_model_and_effort(built: Path) -> None:
    runner = load_runner(built)
    guide = plan_guide(built)
    values = [*runner.VALID_MODELS, *runner.VALID_EFFORTS]
    assert [value for value in values if f"`{value}`" not in guide] == []
