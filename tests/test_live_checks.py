"""scripts/live_checks.py, as a new project gets it: the tests under tests/live/.

Each test writes a small docs/plan.md and tests/ into a temporary folder, with the pytest.ini and
the package.json that a new project gets. Then it runs the script on the folder with --root. The
tests that need node or npm are skipped when the tool is not installed.
"""

import shutil
import sys
from pathlib import Path

import build_instance as bi
import pytest
from helpers import run

SCRIPT = bi.assets_dir() / "scripts" / "live_checks.py"
CONFIGS = ("pytest.ini", "package.json")
NO_TEST = "Live checks: not run (no test in tests/live/)."
NO_APPROVAL = "Live checks: not run (docs/plan.md has no approval with a budget ceiling)."
PASSED = "Live checks: passed."
FAILED = "Live checks: failed."

APPROVAL = "- **Approval:** Yes, run the live checks with the test account."
CEILING = "- **Budget ceiling:** 5 USD"
PLAN = f"""# Plan

## Milestones at a glance

| Milestone | Description | Model | Effort | Status |
| --- | --- | --- | --- | --- |

## Live checks

{APPROVAL}
{CEILING}

## Human checks

- NFR-001: time one answer on the user's machine.
"""
NO_SECTION = "# Plan\n\n## Milestones\n\nNone planned.\n"

PASSING = "def test_the_service_answers() -> None:\n    assert True\n"
FAILING = "def test_the_service_answers() -> None:\n    assert False\n"
READS_CEILING = (
    "import os\n\n\n"
    "def test_the_ceiling_is_given() -> None:\n"
    '    assert os.environ["LIVE_BUDGET_CEILING"] == "5"\n'
    '    assert os.environ["LIVE_BUDGET_CURRENCY"] == "USD"\n'
)
NO_AMOUNT = (
    "Live checks: not run (the budget ceiling in docs/plan.md is not an amount and a currency,"
    " such as 5 USD)."
)
WEB_PASSING = 'import test from "node:test";\n\ntest("the service answers", () => {});\n'
WEB_FAILING = (
    'import assert from "node:assert";\nimport test from "node:test";\n\n'
    'test("the service answers", () => {\n  assert.fail("the live test ran");\n});\n'
)

needs_node = pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
needs_npm = pytest.mark.skipif(shutil.which("npm") is None, reason="npm is not installed")


def project(root: Path, plan: str = PLAN, files: dict[str, str] | None = None) -> Path:
    """Write the plan, the tool configs and the given files under root, and return root."""
    (root / "docs").mkdir()
    (root / "docs" / "plan.md").write_text(plan, encoding="utf-8")
    for name in CONFIGS:
        shutil.copy(bi.assets_dir() / name, root / name)
    for name, text in (files or {}).items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return root


def live_checks(root: Path) -> tuple[int, list[str], str]:
    """Run the script on root. Return its exit code, its output lines and its error output."""
    result = run([sys.executable, str(SCRIPT), "--root", str(root)])
    return result.returncode, result.stdout.splitlines(), result.stderr


def snapshot(root: Path) -> dict[str, bytes | None]:
    """Return every path under root, with the content of each file."""
    paths = sorted(root.rglob("*"))
    return {p.relative_to(root).as_posix(): p.read_bytes() if p.is_file() else None for p in paths}


def test_it_does_not_run_when_tests_live_does_not_exist(tmp_path: Path) -> None:
    code, lines, _ = live_checks(project(tmp_path))
    assert (code, lines) == (3, [NO_TEST])


def test_it_does_not_run_when_tests_live_holds_no_test(tmp_path: Path) -> None:
    files = {"tests/live/conftest.py": "", "tests/unit/test_pay.py": FAILING}
    code, lines, _ = live_checks(project(tmp_path, files=files))
    assert (code, lines) == (3, [NO_TEST])


def test_it_does_not_run_when_the_plan_has_no_live_checks_section(tmp_path: Path) -> None:
    # The live test fails, so exit code 1 would show that it ran.
    root = project(tmp_path, plan=NO_SECTION, files={"tests/live/test_api.py": FAILING})
    code, lines, errors = live_checks(root)
    assert (code, lines, errors) == (3, [NO_APPROVAL], "")


def test_it_does_not_run_when_the_plan_does_not_exist(tmp_path: Path) -> None:
    root = project(tmp_path, files={"tests/live/test_api.py": FAILING})
    (root / "docs" / "plan.md").unlink()
    code, lines, _ = live_checks(root)
    assert (code, lines) == (3, [NO_APPROVAL])


@pytest.mark.parametrize(
    ("entry", "replacement"),
    [
        (APPROVAL, ""),
        (APPROVAL, "- **Approval:**"),
        (APPROVAL, "- **Approval:** <the user's words>"),
        (CEILING, ""),
        (CEILING, "- **Budget ceiling:**   "),
        (CEILING, "- **Budget ceiling:** <amount>"),
        (CEILING, "- **Budget ceiling:** <amount> USD"),
        ("## Live checks", "## Other checks"),
    ],
)
def test_an_absent_empty_or_placeholder_entry_is_no_approval(
    tmp_path: Path, entry: str, replacement: str
) -> None:
    plan = PLAN.replace(entry, replacement)
    root = project(tmp_path, plan=plan, files={"tests/live/test_api.py": FAILING})
    code, lines, errors = live_checks(root)
    assert (code, lines, errors) == (3, [NO_APPROVAL], "")


def test_entries_under_another_heading_are_no_approval(tmp_path: Path) -> None:
    plan = NO_SECTION + f"\n{APPROVAL}\n{CEILING}\n\n## Live checks\n\nNone approved.\n"
    root = project(tmp_path, plan=plan, files={"tests/live/test_api.py": FAILING})
    code, lines, _ = live_checks(root)
    assert (code, lines) == (3, [NO_APPROVAL])


def test_it_passes_when_the_live_tests_pass(tmp_path: Path) -> None:
    root = project(tmp_path, files={"tests/live/test_api.py": PASSING})
    code, lines, errors = live_checks(root)
    assert (code, lines, errors) == (0, [PASSED], "")


def test_it_fails_with_the_output_of_the_failed_tests(tmp_path: Path) -> None:
    files = {"tests/live/test_api.py": FAILING, "tests/live/deep/test_more.py": PASSING}
    code, lines, errors = live_checks(project(tmp_path, files=files))
    assert (code, lines) == (1, [FAILED])
    assert errors.startswith("`pytest` failed:\n")
    assert "tests/live/test_api.py::test_the_service_answers" in errors
    assert "1 failed, 1 passed" in errors


def test_the_tests_get_the_budget_ceiling(tmp_path: Path) -> None:
    root = project(tmp_path, files={"tests/live/test_api.py": READS_CEILING})
    code, lines, errors = live_checks(root)
    assert (code, lines) == (0, [PASSED]), errors


def test_an_entry_can_continue_on_the_next_line(tmp_path: Path) -> None:
    plan = PLAN.replace(APPROVAL, "- **Approval:**\n  Yes, run them.").replace(
        CEILING, "- **Budget ceiling:**\n  5 USD"
    )
    root = project(tmp_path, plan=plan, files={"tests/live/test_api.py": READS_CEILING})
    code, lines, errors = live_checks(root)
    assert (code, lines) == (0, [PASSED]), errors


def test_the_list_of_live_tests_is_not_part_of_the_ceiling(tmp_path: Path) -> None:
    # The eighth real run: the template of docs/workflow.md lists `- <requirement ID>: <test
    # name>` under the ceiling, and the ceiling took that line too.
    plan = PLAN.replace(CEILING, f"{CEILING}\n- PAY-001: `test_pay_001_the_service_answers`")
    root = project(tmp_path, plan=plan, files={"tests/live/test_api.py": READS_CEILING})
    code, lines, errors = live_checks(root)
    assert (code, lines) == (0, [PASSED]), errors


@pytest.mark.parametrize("ceiling", ["five dollars", "$5", "USD 5", "5 usd", "5"])
def test_a_ceiling_that_is_not_an_amount_and_a_currency_is_not_run(
    tmp_path: Path, ceiling: str
) -> None:
    # RUN-17: in the eighth real run, the ceiling had no form, and a test read it as a number.
    plan = PLAN.replace(CEILING, f"- **Budget ceiling:** {ceiling}")
    root = project(tmp_path, plan=plan, files={"tests/live/test_api.py": FAILING})
    code, lines, errors = live_checks(root)
    assert (code, lines, errors) == (3, [NO_AMOUNT], "")


@pytest.mark.parametrize(
    ("ceiling", "amount", "currency"),
    [("0 USD. The model runs on this machine.", "0", "USD"), ("2.50 EUR", "2.50", "EUR")],
)
def test_the_tests_get_the_amount_and_the_currency(
    tmp_path: Path, ceiling: str, amount: str, currency: str
) -> None:
    reads = (
        "import os\n\n\ndef test_the_budget_is_given() -> None:\n"
        f'    assert os.environ["LIVE_BUDGET_CEILING"] == "{amount}"\n'
        f'    assert os.environ["LIVE_BUDGET_CURRENCY"] == "{currency}"\n'
    )
    plan = PLAN.replace(CEILING, f"- **Budget ceiling:** {ceiling}")
    root = project(tmp_path, plan=plan, files={"tests/live/test_api.py": reads})
    code, lines, errors = live_checks(root)
    assert (code, lines) == (0, [PASSED]), errors


def test_the_live_run_has_no_coverage_floor(tmp_path: Path) -> None:
    # No test runs src/pay.py. With the 80% floor, the run would fail.
    files = {"tests/live/test_api.py": PASSING, "src/pay.py": "def pay() -> int:\n    return 1\n"}
    code, lines, errors = live_checks(project(tmp_path, files=files))
    assert (code, lines) == (0, [PASSED]), errors


def test_it_runs_only_the_tests_in_tests_live(tmp_path: Path) -> None:
    files = {"tests/live/test_api.py": PASSING, "tests/unit/test_pay.py": FAILING}
    code, lines, errors = live_checks(project(tmp_path, files=files))
    assert (code, lines) == (0, [PASSED]), errors


@pytest.mark.parametrize("live_test", [PASSING, FAILING])
def test_it_changes_no_file(tmp_path: Path, live_test: str) -> None:
    root = project(tmp_path, files={"tests/live/test_api.py": live_test})
    before = snapshot(root)
    live_checks(root)
    assert snapshot(root) == before


def test_a_normal_pytest_run_skips_tests_live(tmp_path: Path) -> None:
    files = {"tests/unit/test_pay.py": PASSING, "tests/live/test_api.py": FAILING}
    root = project(tmp_path, files=files)
    result = run([sys.executable, "-m", "pytest", "-q"], root)
    assert result.returncode == 0, result.stdout
    assert "1 passed" in result.stdout
    # It also skips the folder when pytest starts in tests/.
    result = run([sys.executable, "-m", "pytest", "-q"], root / "tests")
    assert result.returncode == 0, result.stdout


def test_a_normal_pytest_run_passes_without_tests_live(tmp_path: Path) -> None:
    root = project(tmp_path, files={"tests/unit/test_pay.py": PASSING})
    result = run([sys.executable, "-m", "pytest", "-q"], root)
    assert result.returncode == 0, result.stdout
    assert "1 passed" in result.stdout


@needs_node
def test_it_runs_the_javascript_live_tests(tmp_path: Path) -> None:
    root = project(tmp_path, files={"tests/live/api.test.js": WEB_PASSING})
    code, lines, errors = live_checks(root)
    assert (code, lines) == (0, [PASSED]), errors


@needs_node
def test_a_failed_javascript_live_test_fails_the_run(tmp_path: Path) -> None:
    files = {"tests/live/test_api.py": PASSING, "tests/live/api.test.js": WEB_FAILING}
    code, lines, errors = live_checks(project(tmp_path, files=files))
    assert (code, lines) == (1, [FAILED])
    assert errors.startswith("`node --test` failed:\n")
    assert "the live test ran" in errors


@needs_npm
def test_the_npm_test_script_skips_tests_live(tmp_path: Path) -> None:
    files = {
        "tests/unit/pay.test.js": WEB_PASSING,
        "tests/e2e/ui/page.test.js": WEB_PASSING,
        "tests/live/api.test.js": WEB_FAILING,
    }
    root = project(tmp_path, files=files)
    result = run([str(shutil.which("npm")), "run", "test"], root)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "pass 2" in result.stdout
    assert "fail 0" in result.stdout
