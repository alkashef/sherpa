"""scripts/spec_coverage.py, as a new project gets it: which ID has a test, and consistency.

Each test writes a small docs/spec.md, docs/plan.md and tests/ into a temporary folder and runs
the script on it with --root. The tests of `--consistency` also write docs/design.md.
"""

import sys
from pathlib import Path

import build_instance as bi
import pytest
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

| ID | Requirement IDs | Situation and input | Expected result | Reviewed by |
| --- | --- | --- | --- | --- |
| EX-001 | PAY-001 | A balance of 1,000 and a payment of 400 | A balance of 600 | The clerk |
| EX-002 | PAY-002 | A balance of 100 and a payment of 400 | A refusal | Withdrawn |
"""
DESIGN = """# Design

## 1. Decisions

| ID | Status | Decision | Why |
| --- | --- | --- | --- |
| DEC-004 | Decided | A SQLite file holds the balances. | PAY-001 needs a local store. |

## 5. Test design

| Requirement | Level | Test tool | Real local part or fake |
| --- | --- | --- | --- |
| PAY-001, PAY-002 | unit | pytest | A SQLite file |
| NFR-001 | e2e | pytest | A local server |

## 6. Open design questions

| ID | Question | Who decides | Blocks what |
| --- | --- | --- | --- |
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
- **Tests first:** unit: `test_pay_001_ex_001_balance_falls`,
  `test_pay_002_overpayment_refused`.
- **Build:** add `record_payment`.

### M2 — Speed

- **Refs:** NFR-001.
- **Tests first:** Manual: NFR-001.

## Human checks

- NFR-001: time one answer on the user's machine.
"""
PYTHON_TESTS = (
    "def test_pay_001_ex_001_balance_falls() -> None:\n    assert True\n\n\n"
    "async def test_pay_002_overpayment_refused() -> None:\n    assert True\n"
)
# The same two tests, but no name carries the ID of the acceptance example EX-001.
TESTS_WITHOUT_EXAMPLE = PYTHON_TESTS.replace("_ex_001", "")
M1_TESTS_FIRST = "  `test_pay_002_overpayment_refused`."
NFR_LEVEL_ROW = "| NFR-001 | e2e | pytest | A local server |"
CONSISTENT = "The spec, the design and the plan are consistent."


def example(example_id: str, cites: str) -> str:
    """Return one more row for the table of acceptance examples, which ends SPEC."""
    return f"| {example_id} | {cites} | A situation | A result | The clerk |\n"


def project(
    root: Path, plan: str = PLAN, tests: str = "", *, spec: str = SPEC, design: str | None = None
) -> Path:
    """Write the spec, a plan and one Python test file under root, and return root.

    It writes docs/design.md only when it gets a design.
    """
    (root / "docs").mkdir()
    (root / "tests" / "unit").mkdir(parents=True)
    (root / "docs" / "spec.md").write_text(spec, encoding="utf-8")
    (root / "docs" / "plan.md").write_text(plan, encoding="utf-8")
    (root / "tests" / "unit" / "test_pay.py").write_text(tests, encoding="utf-8")
    if design is not None:
        (root / "docs" / "design.md").write_text(design, encoding="utf-8")
    return root


def coverage(root: Path, *args: str) -> tuple[int, list[str]]:
    """Run the script on root and return its exit code and its output lines."""
    result = run([sys.executable, str(SCRIPT), *args, "--root", str(root)])
    return result.returncode, (result.stdout + result.stderr).splitlines()


def consistency(root: Path) -> tuple[int, list[str]]:
    """Run the script with --consistency on root and return its exit code and its output lines."""
    return coverage(root, "--consistency")


def states(lines: list[str]) -> dict[str, str]:
    """Return the state the output gives each ID (`PAY-001   tested`)."""
    pairs = (line.split(maxsplit=1) for line in lines if line[:1].isupper() and "-" in line[:8])
    return {spec_id: state for spec_id, state in pairs}


def test_it_lists_each_requirement_and_each_example_with_its_state(tmp_path: Path) -> None:
    code, lines = coverage(project(tmp_path, tests=PYTHON_TESTS))
    assert code == 0
    assert lines == [
        "PAY-001   tested",
        "PAY-002   tested",
        "NFR-001   manual",
        "3 requirement IDs: 1 manual, 2 tested.",
        "EX-001    tested",
        "1 acceptance examples: 1 tested.",
    ]


def test_examples_decisions_and_withdrawn_rows_are_not_requirements(tmp_path: Path) -> None:
    _, lines = coverage(project(tmp_path))
    assert "3 requirement IDs: 1 manual, 2 planned." in lines
    assert set(states(lines)) == {"PAY-001", "PAY-002", "NFR-001", "EX-001"}


def test_a_requirement_without_a_test_is_planned_or_missing(tmp_path: Path) -> None:
    plan = PLAN.replace("- **Refs:** PAY-001, PAY-002, DEC-004.", "- **Refs:** PAY-001.")
    code, lines = coverage(project(tmp_path, plan=plan))
    assert code == 0
    assert states(lines) == {
        "PAY-001": "planned",
        "PAY-002": "missing",
        "NFR-001": "manual",
        "EX-001": "planned",
    }


def test_an_example_is_tested_manual_planned_or_missing(tmp_path: Path) -> None:
    # EX-003 has a Manual entry and EX-004 a human check. The Refs name PAY-002, which EX-005
    # cites. No Refs name PAY-003, which EX-006 cites.
    spec = SPEC + "".join(
        example(example_id, cites)
        for example_id, cites in (
            ("EX-003", "PAY-002"),
            ("EX-004", "NFR-001"),
            ("EX-005", "PAY-002, NFR-001"),
            ("EX-006", "PAY-003"),
        )
    )
    plan = PLAN.replace(M1_TESTS_FIRST, M1_TESTS_FIRST + " Manual: EX-003.")
    plan += "- EX-004: time one answer with a full database.\n"
    code, lines = coverage(project(tmp_path, plan=plan, tests=PYTHON_TESTS, spec=spec))
    assert code == 0
    assert lines[-6:] == [
        "EX-001    tested",
        "EX-003    manual",
        "EX-004    manual",
        "EX-005    planned",
        "EX-006    missing",
        "5 acceptance examples: 2 manual, 1 missing, 1 planned, 1 tested.",
    ]


def test_a_milestone_passes_when_each_requirement_and_example_has_a_test(tmp_path: Path) -> None:
    code, lines = coverage(project(tmp_path, tests=PYTHON_TESTS), "M1")
    assert code == 0
    assert lines == [
        "PAY-001   tested",
        "PAY-002   tested",
        "EX-001    tested",
        "M1: 2 requirement ID(s) in Refs, all tested or manual.",
        "M1: 1 acceptance example(s) cite them, all tested or manual.",
    ]


def test_a_milestone_fails_when_a_requirement_has_no_test(tmp_path: Path) -> None:
    tests = "def test_pay_001_ex_001_balance_falls() -> None:\n    assert True\n"
    code, lines = coverage(project(tmp_path, tests=tests), "M1")
    assert code == 1
    assert lines[-1] == "M1: no test and no Manual entry for PAY-002."


def test_a_milestone_fails_when_an_example_has_no_test(tmp_path: Path) -> None:
    code, lines = coverage(project(tmp_path, tests=TESTS_WITHOUT_EXAMPLE), "M1")
    assert code == 1
    assert "EX-001    planned" in lines
    assert lines[-1] == "M1: no test and no Manual entry for EX-001."


def test_one_message_names_each_requirement_and_example_without_a_test(tmp_path: Path) -> None:
    code, lines = coverage(project(tmp_path), "M1")
    assert code == 1
    assert lines[-1] == "M1: no test and no Manual entry for PAY-001, PAY-002, EX-001."


def test_a_manual_entry_stands_in_for_a_test(tmp_path: Path) -> None:
    code, lines = coverage(project(tmp_path), "M2")
    assert code == 0, lines
    assert lines[-1] == "M2: 0 acceptance example(s) cite them, all tested or manual."


def test_a_manual_entry_stands_in_for_the_test_of_an_example(tmp_path: Path) -> None:
    plan = PLAN.replace(M1_TESTS_FIRST, M1_TESTS_FIRST + " Manual: EX-001.")
    code, lines = coverage(project(tmp_path, plan=plan, tests=TESTS_WITHOUT_EXAMPLE), "M1")
    assert code == 0, lines
    assert "EX-001    manual" in lines


def test_a_human_check_stands_in_for_the_test_of_an_example(tmp_path: Path) -> None:
    plan = PLAN + "- EX-001: a clerk reads the new balance.\n"
    code, lines = coverage(project(tmp_path, plan=plan, tests=TESTS_WITHOUT_EXAMPLE), "M1")
    assert code == 0, lines
    assert "EX-001    manual" in lines


def test_a_milestone_checks_only_the_examples_that_cite_its_requirements(tmp_path: Path) -> None:
    # EX-002 cites PAY-002 but is withdrawn, and EX-003 cites a requirement of M2.
    spec = SPEC + example("EX-003", "NFR-001")
    code, lines = coverage(project(tmp_path, tests=PYTHON_TESTS, spec=spec), "M1")
    assert code == 0, lines
    assert set(states(lines)) == {"PAY-001", "PAY-002", "EX-001"}


def test_an_example_that_cites_two_requirements_counts_for_each_milestone(tmp_path: Path) -> None:
    spec = SPEC + example("EX-003", "PAY-002, NFR-001")
    code, lines = coverage(project(tmp_path, tests=PYTHON_TESTS, spec=spec), "M2")
    assert code == 1
    assert lines[-1] == "M2: no test and no Manual entry for EX-003."


def test_a_milestone_check_needs_only_its_block_the_spec_and_the_tests(tmp_path: Path) -> None:
    # The milestones runner gives the script such a folder: no design, and a plan of one block.
    block = PLAN[PLAN.index("### M1") : PLAN.index("### M2")]
    code, lines = coverage(project(tmp_path, plan=block, tests=PYTHON_TESTS), "M1")
    assert code == 0, lines
    code, lines = coverage(tmp_path, "M2")
    assert code == 2
    assert lines == ["No block '### M2' in docs/plan.md."]


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


def test_a_test_name_must_carry_the_whole_id_of_an_example(tmp_path: Path) -> None:
    # `index_001` does not carry EX-001, and EX-001 is not EX-0011.
    tests = (
        "def test_pay_001_index_001_other() -> None:\n    assert True\n\n\n"
        "def test_pay_002_ex_0011_other() -> None:\n    assert True\n"
    )
    _, lines = coverage(project(tmp_path, tests=tests))
    assert states(lines)["EX-001"] == "planned"


def test_a_web_test_carries_the_id_in_its_title(tmp_path: Path) -> None:
    root = project(tmp_path)
    web = "test('PAY-001 EX-001: it falls', () => {});\nit(\"pay-002 refuses\", () => {});\n"
    (root / "tests" / "unit" / "pay.test.js").write_text(web, encoding="utf-8")
    code, lines = coverage(root, "M1")
    assert code == 0, lines
    assert "EX-001    tested" in lines


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
    lines = result.stdout.splitlines()
    assert lines == ["0 requirement IDs: none.", "0 acceptance examples: none."]


def test_consistent_documents_pass(tmp_path: Path) -> None:
    code, lines = consistency(project(tmp_path, tests=PYTHON_TESTS, design=DESIGN))
    assert code == 0
    assert lines == [CONSISTENT]


def test_a_new_project_is_consistent(tmp_path: Path) -> None:
    build(tmp_path / "my-app", "--with", "python")
    command = [sys.executable, "scripts/spec_coverage.py", "--consistency"]
    result = run(command, tmp_path / "my-app")
    assert result.returncode == 0, result.stdout
    assert result.stdout.splitlines() == [CONSISTENT]


@pytest.mark.parametrize("name", ["PAY-009", "NFR-009"])
def test_the_table_of_test_levels_names_only_rows_of_the_spec(tmp_path: Path, name: str) -> None:
    # The first cell of a row names the requirement, also when the row gives no level.
    design = DESIGN.replace(NFR_LEVEL_ROW, NFR_LEVEL_ROW + f"\n| {name} | | pytest | A fake |")
    code, lines = consistency(project(tmp_path, design=design))
    assert code == 1
    assert lines == [
        f"docs/design.md names {name}, which is not a requirement row of docs/spec.md."
    ]


def test_a_text_of_the_design_that_looks_like_an_id_is_no_problem(tmp_path: Path) -> None:
    # Only the first cell of a row of the Test design table names a requirement of the design.
    design = DESIGN.replace(NFR_LEVEL_ROW, "| NFR-001 | e2e | pytest | A server with AES-256 |")
    design += "\nThe file hash is SHA-256. Dates are ISO-8601. See PAY-009, EX-009 and DEC-009.\n"
    code, lines = consistency(project(tmp_path, design=design))
    assert code == 0, lines
    assert lines == [CONSISTENT]


@pytest.mark.parametrize(
    ("entry", "name", "kind"),
    [
        ("- **Refs:** NFR-001.", "PAY-009", "a requirement row of docs/spec.md"),
        ("- **Refs:** NFR-001.", "DEC-009", "a decision row of docs/design.md"),
        (
            "- **Tests first:** Manual: NFR-001.",
            "EX-009",
            "an acceptance example row of docs/spec.md",
        ),
        (M1_TESTS_FIRST, "EX-009", "an acceptance example row of docs/spec.md"),
    ],
)
def test_the_refs_and_the_tests_first_of_a_block_name_only_rows(
    tmp_path: Path, entry: str, name: str, kind: str
) -> None:
    plan = PLAN.replace(entry, f"{entry[:-1]}, {name}.")
    code, lines = consistency(project(tmp_path, plan=plan, design=DESIGN))
    assert code == 1
    assert lines == [f"docs/plan.md names {name}, which is not {kind}."]


def test_an_id_in_another_place_of_the_plan_is_no_problem(tmp_path: Path) -> None:
    # Not checked: a test name, another entry of a block, and a line outside the blocks.
    plan = PLAN.replace("`test_pay_002_overpayment_refused`", "`test_pay_002_ex_009_refused`")
    plan = plan.replace(
        "add `record_payment`.", "add `record_payment` (SHA-256, PAY-009, DEC-009)."
    )
    plan += "- PAY-009, EX-009 and DEC-009: read the ISO-8601 date of the receipt.\n"
    code, lines = consistency(project(tmp_path, plan=plan, design=DESIGN))
    assert code == 0, lines


def test_a_withdrawn_row_of_the_spec_is_still_a_row(tmp_path: Path) -> None:
    design = DESIGN.replace(NFR_LEVEL_ROW, NFR_LEVEL_ROW + "\n| PAY-003 | unit | pytest | None |")
    plan = PLAN.replace("- **Refs:** NFR-001.", "- **Refs:** NFR-001, PAY-003.")
    plan = plan.replace("Manual: NFR-001.", "Manual: NFR-001, EX-002.")
    code, lines = consistency(project(tmp_path, plan=plan, design=design))
    assert code == 0, lines


def test_each_requirement_needs_a_test_level_in_the_design(tmp_path: Path) -> None:
    # PAY-003 is withdrawn: it has no row in the table and needs none.
    design = DESIGN.replace(NFR_LEVEL_ROW + "\n", "")
    code, lines = consistency(project(tmp_path, design=design))
    assert code == 1
    assert lines == [
        "NFR-001 has no test level (unit, e2e, ui or live) in the Test design table "
        "of docs/design.md."
    ]


def test_a_test_level_is_unit_e2e_ui_or_live(tmp_path: Path) -> None:
    design = DESIGN.replace("| NFR-001 | e2e |", "| NFR-001 | manual |")
    code, lines = consistency(project(tmp_path, design=design))
    assert code == 1
    assert lines[0].startswith("NFR-001 has no test level")
    design = DESIGN.replace("| PAY-001, PAY-002 | unit |", "| `PAY-001` and `PAY-002` | `ui` |")
    design = design.replace("| NFR-001 | e2e |", "| NFR-001 | live |")
    (tmp_path / "docs" / "design.md").write_text(design, encoding="utf-8")
    code, lines = consistency(tmp_path)
    assert code == 0, lines


def test_the_level_is_in_the_second_cell_of_a_row(tmp_path: Path) -> None:
    design = DESIGN.replace(NFR_LEVEL_ROW, "| NFR-001 | | | A live server |")
    code, lines = consistency(project(tmp_path, design=design))
    assert code == 1
    assert lines[0].startswith("NFR-001 has no test level")


def test_the_table_of_test_levels_is_in_the_section_test_design(tmp_path: Path) -> None:
    design = DESIGN.replace("## 5. Test design", "## 5. Test design\n\n### 5.1 Levels")
    code, lines = consistency(project(tmp_path, design=design))
    assert code == 0, lines
    design = DESIGN.replace("## 5. Test design", "## 5. Tools")
    (tmp_path / "docs" / "design.md").write_text(design, encoding="utf-8")
    code, lines = consistency(tmp_path)
    assert code == 1
    assert [line.split()[0] for line in lines] == ["PAY-001", "PAY-002", "NFR-001"]


def test_each_problem_is_on_its_own_line(tmp_path: Path) -> None:
    design = DESIGN.replace(NFR_LEVEL_ROW, "| PAY-009 | unit | pytest | A SQLite file |")
    plan = PLAN.replace("DEC-004", "DEC-009").replace("Refs:** NFR-001.", "Refs:** NFR-009.")
    plan = plan.replace("Manual: NFR-001.", "Manual: NFR-001, EX-009.")
    code, lines = consistency(project(tmp_path, plan=plan, design=design))
    assert code == 1
    assert lines == [
        "docs/design.md names PAY-009, which is not a requirement row of docs/spec.md.",
        "docs/plan.md names NFR-009, which is not a requirement row of docs/spec.md.",
        "docs/plan.md names EX-009, which is not an acceptance example row of docs/spec.md.",
        "docs/plan.md names DEC-009, which is not a decision row of docs/design.md.",
        "NFR-001 has no test level (unit, e2e, ui or live) in the Test design table "
        "of docs/design.md.",
    ]


def test_a_missing_design_is_a_problem(tmp_path: Path) -> None:
    root = project(tmp_path)
    code, lines = consistency(root)
    assert code == 1
    assert lines == [f"docs/design.md is missing in {root.resolve()}."]


def test_each_missing_file_is_a_problem_and_stops_the_other_checks(tmp_path: Path) -> None:
    # Without the spec, each ID of the design would be a problem. The script reports only the files.
    root = project(tmp_path, design=DESIGN)
    (root / "docs" / "spec.md").unlink()
    (root / "docs" / "plan.md").unlink()
    code, lines = consistency(root)
    assert code == 1
    assert lines == [
        f"docs/spec.md is missing in {root.resolve()}.",
        f"docs/plan.md is missing in {root.resolve()}.",
    ]


def test_consistency_and_a_milestone_do_not_go_together(tmp_path: Path) -> None:
    code, lines = coverage(project(tmp_path, design=DESIGN), "M1", "--consistency")
    assert code == 2
    assert "not allowed with argument" in lines[-1]
