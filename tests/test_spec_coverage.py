"""scripts/spec_coverage.py, as a new project gets it: which requirement ID has a test.

Each test writes a small docs/spec.md, docs/plan.md and tests/ into a temporary folder and runs
the script on it with --root.
"""

import sys
from pathlib import Path

import build_instance as bi
from helpers import build, run

SCRIPT = bi.assets_dir() / "scripts" / "spec_coverage.py"
SPEC = """# Spec

## 4. Functional requirements

| ID | EARS requirement | Priority | Status |
| --- | --- | --- | --- |
| PAY-001 | When a clerk records a payment, the system shall lower the balance. | Must | Confirmed |
| PAY-002 | If the payment is too high, then the system shall refuse it. | Must | Confirmed |
| PAY-003 | The system shall print a receipt. | Could | Withdrawn |

## 5. Non-functional requirements

| ID | EARS requirement | Priority | Status |
| --- | --- | --- | --- |
| NFR-001 | The system shall answer within 2 seconds. | Should | Confirmed |

## 6. Acceptance examples

| ID | Requirement IDs | Situation and input | Expected result |
| --- | --- | --- | --- |
| EX-001 | PAY-001 | A balance of 1,000 and a payment of 400 | A balance of 600 |
"""
PLAN = """# Plan

## Milestones at a glance

| Milestone | Description | Model | Effort | Status |
| --- | --- | --- | --- | --- |
| **M1** Pay | A clerk records a payment | sonnet | medium | open |
| **M2** Speed | The answer is fast | sonnet | medium | open |

## Milestones

### M1 — Pay

- **Refs:** PAY-001, PAY-002, DEC-004.
- **Owner:** `src/payments/record.py`.
- **Tests first:** unit: `test_pay_001_balance_falls`,
  `test_pay_002_overpayment_refused`.
- **Build:** add `record_payment`.

### M2 — Speed

- **Refs:** NFR-001.
- **Tests first:** Manual: NFR-001.

## Human checks

- NFR-001: time one answer on the user's machine.
"""
PYTHON_TESTS = (
    "def test_pay_001_balance_falls() -> None:\n    assert True\n\n\n"
    "async def test_pay_002_overpayment_refused() -> None:\n    assert True\n"
)


def project(root: Path, plan: str = PLAN, tests: str = "") -> Path:
    """Write the spec, a plan and one Python test file under root, and return root."""
    (root / "docs").mkdir()
    (root / "tests" / "unit").mkdir(parents=True)
    (root / "docs" / "spec.md").write_text(SPEC, encoding="utf-8")
    (root / "docs" / "plan.md").write_text(plan, encoding="utf-8")
    (root / "tests" / "unit" / "test_pay.py").write_text(tests, encoding="utf-8")
    return root


def coverage(root: Path, *args: str) -> tuple[int, list[str]]:
    """Run the script on root and return its exit code and its output lines."""
    result = run([sys.executable, str(SCRIPT), *args, "--root", str(root)])
    return result.returncode, (result.stdout + result.stderr).splitlines()


def states(lines: list[str]) -> dict[str, str]:
    """Return the state the output gives each ID (`PAY-001   tested`)."""
    pairs = (line.split(maxsplit=1) for line in lines if line[:1].isupper() and "-" in line[:8])
    return {spec_id: state for spec_id, state in pairs}


def test_it_lists_each_requirement_with_its_state(tmp_path: Path) -> None:
    code, lines = coverage(project(tmp_path, tests=PYTHON_TESTS))
    assert code == 0
    assert states(lines) == {"PAY-001": "tested", "PAY-002": "tested", "NFR-001": "manual"}
    assert lines[-1] == "3 requirement IDs: 1 manual, 2 tested."


def test_examples_decisions_and_withdrawn_rows_are_not_requirements(tmp_path: Path) -> None:
    _, lines = coverage(project(tmp_path))
    assert set(states(lines)) == {"PAY-001", "PAY-002", "NFR-001"}


def test_a_requirement_without_a_test_is_planned_or_missing(tmp_path: Path) -> None:
    plan = PLAN.replace("- **Refs:** PAY-001, PAY-002, DEC-004.", "- **Refs:** PAY-001.")
    code, lines = coverage(project(tmp_path, plan=plan))
    assert code == 0
    assert states(lines) == {"PAY-001": "planned", "PAY-002": "missing", "NFR-001": "manual"}


def test_a_milestone_passes_when_each_of_its_requirements_has_a_test(tmp_path: Path) -> None:
    code, lines = coverage(project(tmp_path, tests=PYTHON_TESTS), "M1")
    assert code == 0
    assert lines[-1] == "M1: 2 requirement ID(s) in Refs, all tested or manual."


def test_a_milestone_fails_when_a_requirement_has_no_test(tmp_path: Path) -> None:
    tests = "def test_pay_001_balance_falls() -> None:\n    assert True\n"
    code, lines = coverage(project(tmp_path, tests=tests), "M1")
    assert code == 1
    assert lines[-1] == "M1: no test and no Manual entry for PAY-002."


def test_a_manual_entry_stands_in_for_a_test(tmp_path: Path) -> None:
    code, lines = coverage(project(tmp_path), "M2")
    assert code == 0, lines


def test_a_requirement_that_is_not_in_the_spec_fails_its_milestone(tmp_path: Path) -> None:
    plan = PLAN.replace("- **Refs:** NFR-001.", "- **Refs:** NFR-001, PAY-009.")
    code, lines = coverage(project(tmp_path, plan=plan), "M2")
    assert code == 1
    assert "PAY-009   not in the spec" in lines


def test_a_test_name_must_carry_the_whole_id(tmp_path: Path) -> None:
    # NFR-001 is not PAY-001's neighbor FR-001, and PAY-001 is not PAY-0011.
    tests = (
        "def test_xpay_001_other() -> None:\n    assert True\n\n\n"
        "def test_pay_0011_other() -> None:\n    assert True\n"
    )
    _, lines = coverage(project(tmp_path, tests=tests))
    assert states(lines)["PAY-001"] == "planned"


def test_a_web_test_carries_the_id_in_its_title(tmp_path: Path) -> None:
    root = project(tmp_path)
    web = "test('PAY-001: the balance falls', () => {});\nit(\"pay-002 refuses\", () => {});\n"
    (root / "tests" / "unit" / "pay.test.js").write_text(web, encoding="utf-8")
    code, lines = coverage(root, "M1")
    assert code == 0, lines


def test_a_missing_spec_or_block_is_a_usage_error(tmp_path: Path) -> None:
    root = project(tmp_path)
    code, lines = coverage(root, "M7")
    assert code == 2
    assert lines == ["No block '### M7' in docs/plan.md."]
    (root / "docs" / "spec.md").unlink()
    code, lines = coverage(root)
    assert code == 2
    assert lines[0].startswith("docs/spec.md is missing")


def test_a_new_project_has_no_requirement_and_passes(tmp_path: Path) -> None:
    build(tmp_path / "my-app", "--with", "python")
    result = run([sys.executable, "scripts/spec_coverage.py"], tmp_path / "my-app")
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "0 requirement IDs: none."
