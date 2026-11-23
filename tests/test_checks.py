"""The checks a new project gets: scripts/check.py, the Claude Code edit hook, the pre-commit hook.

These run the real ruff and mypy from this repository's environment against a built project.
"""

import importlib.util
import json
import re
import sys
from pathlib import Path
from types import ModuleType

import build_instance as bi
import pytest
from helpers import Sandbox, build, git_path, run

BAD = "import os\n"  # an unused import, and no module docstring
GOOD = '"""A module."""\n'
CALC = '"""Arithmetic."""\n\n\ndef add(a: int, b: int) -> int:\n    """Add."""\n    return a + b\n'
CIRCLE = '"""Shapes."""\n\n\nclass Circle:\n    """A circle."""\n'
SHAPES = CIRCLE + '\n\nclass Square:\n    """A square."""\n'
TWO_CLASSES = "src/shapes.py defines 2 classes: Circle, Square. Keep one class in a file."
LATE_IMPORT = (
    '"""A module."""\n\n\n'
    'def dump() -> str:\n    """Dump."""\n    import json\n\n    return json.dumps({})\n'
)
SORTED_IMPORTS = "import pytest\n\nfrom src.slug import make_slug\n\nassert (pytest, make_slug)\n"
UNSORTED_IMPORTS = "import pytest\nfrom src.slug import make_slug\n\nassert (pytest, make_slug)\n"
PROCESS_TEST = (  # a test that runs a process, as an end-to-end test of a command line does
    "import subprocess\nimport sys\n\n\n"
    "def test_python_runs_as_a_process() -> None:\n"
    '    done = subprocess.run([sys.executable, "-c", "print(1)"], check=False)\n'
    "    assert done.returncode == 0\n"
)
BOUNDARIES = "### 2.4 Module boundaries\n\n| Module | May import |\n| --- | --- |\n"


@pytest.fixture
def project(sandbox: Sandbox) -> Sandbox:
    """A Python project set up by init_project.py, kept local, with no conda environment."""
    result = sandbox.init("--with", "python", "--no-github", "--no-conda")
    assert result.returncode == 0, result.stderr
    return sandbox


def check(folder: Path, *args: str, stdin: str | None = None) -> tuple[int, str]:
    """Run the project's scripts/check.py with this environment's Python (it has ruff and mypy)."""
    result = run([sys.executable, str(folder / "scripts" / "check.py"), *args], folder, stdin=stdin)
    return result.returncode, result.stdout + result.stderr


def edited(path: Path) -> str:
    """Return the JSON a Claude Code PostToolUse hook gets after an edit to this file."""
    return json.dumps({"tool_name": "Edit", "tool_input": {"file_path": str(path)}})


def load_check() -> ModuleType:
    """Import the check.py that new projects get."""
    spec = importlib.util.spec_from_file_location("check", bi.assets_dir() / "scripts/check.py")
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_init_turns_on_the_pre_commit_hook(project: Sandbox) -> None:
    assert project.git("config", "core.hooksPath") == ".githooks"
    for script in [".githooks/pre-commit", "scripts/run-check.sh"]:
        assert project.git("ls-files", "-s", script).startswith("100755"), script


def test_shell_scripts_have_lf_endings(tmp_path: Path) -> None:
    build(tmp_path / "my-app")
    for script in [".githooks/pre-commit", "scripts/run-check.sh"]:
        assert b"\r" not in (tmp_path / "my-app" / script).read_bytes(), script
    assert 'name="my-app"' in (tmp_path / "my-app" / "scripts/run-check.sh").read_text("utf-8")


def test_checks_pass_on_a_new_project(project: Sandbox) -> None:
    code, output = check(project.folder)
    assert code == 0, output
    # One line for each check of the stack, with its result. A skipped line gives the reason.
    lines = output.splitlines()
    assert lines[:6] == [
        "skipped  UTF-8 text (no staged file)",
        "passed   plain docs",
        "passed   ruff check",
        "passed   ruff format",
        "skipped  mypy (no Python in src/)",
        "skipped  one class per file (no Python in src/)",
    ]
    assert lines[6].startswith("skipped  module boundaries (")
    assert lines[7:] == ["skipped  pytest (no test_*.py in tests/)", "All checks passed."]


def test_a_staged_file_that_is_not_utf8_fails(project: Sandbox) -> None:
    # Windows PowerShell 5.1 writes in the ANSI code page: "café" becomes the byte 0xE9.
    notes = project.folder / "docs" / "notes.md"
    notes.write_bytes(b"caf\xe9\n")
    project.git("add", "-A")
    code, output = check(project.folder)
    assert code == 2
    assert "failed   UTF-8 text" in output
    assert "docs/notes.md is not valid UTF-8, or it holds the character U+FFFD" in output
    notes.write_text("caf\N{REPLACEMENT CHARACTER}\n", encoding="utf-8")
    project.git("add", "-A")
    assert "failed   UTF-8 text" in check(project.folder)[1]
    notes.write_text("caf\N{LATIN SMALL LETTER E WITH ACUTE}\n", encoding="utf-8")
    project.git("add", "-A")
    code, output = check(project.folder)
    assert code == 0, output
    assert "passed   UTF-8 text" in output


def test_a_project_with_no_stack_says_that_no_check_applied(tmp_path: Path) -> None:
    build(tmp_path / "plain")
    assert check(tmp_path / "plain") == (0, "No check applied.\n")


def test_checks_fail_on_a_lint_error(project: Sandbox) -> None:
    (project.folder / "src" / "bad.py").write_text(BAD, encoding="utf-8")
    code, output = check(project.folder)
    assert code == 2
    assert "failed   ruff check" in output
    assert "All checks passed." not in output
    assert "bad.py" in output


def imports_sorted(folder: Path) -> bool:
    """Tell whether ruff, with the config of the project and no cache, accepts the imports."""
    command = [sys.executable, "-m", "ruff", "check", "--no-cache", "--select", "I", "tests"]
    return run(command, folder).returncode == 0


def test_src_is_first_party_before_and_after_the_code_exists(project: Sandbox) -> None:
    test = project.folder / "tests" / "unit" / "test_slug.py"
    test.write_text(SORTED_IMPORTS, encoding="utf-8")
    assert imports_sorted(project.folder)  # src/slug.py does not exist yet
    write_module(project.folder, "src/slug.py")
    assert imports_sorted(project.folder)
    test.write_text(UNSORTED_IMPORTS, encoding="utf-8")
    assert not imports_sorted(project.folder)
    (project.folder / "src" / "slug.py").unlink()
    assert not imports_sorted(project.folder)


def test_an_import_inside_a_function_fails(project: Sandbox) -> None:
    (project.folder / "src" / "late.py").write_text(LATE_IMPORT, encoding="utf-8")
    code, output = check(project.folder)
    assert code == 2
    assert "failed   ruff check" in output
    assert "import-outside-top-level" in output  # the name of PLC0415


def test_edited_file_is_fixed_and_the_rest_reported(project: Sandbox) -> None:
    path = project.folder / "src" / "ugly.py"
    path.write_text("import os\nx=1\n", encoding="utf-8")
    code, output = check(project.folder, "--edited", stdin=edited(path))
    # Claude Code shows the reason of a `block` decision to Claude.
    assert code == 0
    decision = json.loads(output)
    assert decision["decision"] == "block"
    assert "Missing docstring in public module" in decision["reason"]
    assert path.read_text(encoding="utf-8") == "x = 1\n"


def test_clean_edit_and_other_files_pass(project: Sandbox) -> None:
    clean = project.folder / "src" / "clean.py"
    clean.write_text(GOOD, encoding="utf-8")
    for path in [clean, project.folder / "README.md", project.folder.parent / "elsewhere.py"]:
        assert check(project.folder, "--edited", stdin=edited(path)) == (0, ""), path


def test_a_second_class_in_a_source_file_fails(project: Sandbox) -> None:
    (project.folder / "src" / "circle.py").write_text(CIRCLE, encoding="utf-8")
    _, output = check(project.folder)
    assert "passed   one class per file" in output
    (project.folder / "src" / "shapes.py").write_text(SHAPES, encoding="utf-8")
    code, output = check(project.folder)
    assert code == 2
    assert "failed   one class per file" in output
    assert f"`one class per file` failed:\n{TWO_CLASSES}" in output


def test_edit_reports_a_second_class_in_a_source_file_only(project: Sandbox) -> None:
    source = project.folder / "src" / "shapes.py"
    source.write_text(SHAPES, encoding="utf-8")
    code, output = check(project.folder, "--edited", stdin=edited(source))
    assert code == 0
    decision = json.loads(output)
    assert decision["decision"] == "block"
    assert TWO_CLASSES in decision["reason"]
    helper = project.folder / "tests" / "unit" / "shapes.py"
    helper.write_text(SHAPES, encoding="utf-8")
    assert check(project.folder, "--edited", stdin=edited(helper)) == (0, "")


def test_missing_tool_is_named() -> None:
    reason = load_check().why_not_runnable([sys.executable, "-m", "no_such_tool"])
    assert "`no-such-tool` not installed" in reason


def write_tested_module(folder: Path, expected: int) -> None:
    """Write src/calc.py and a test of it that passes when `expected` is 3."""
    (folder / "src" / "__init__.py").write_text('"""Source."""\n', encoding="utf-8")
    (folder / "src" / "calc.py").write_text(CALC, encoding="utf-8")
    test = (
        "from src.calc import add\n\n\n"
        f"def test_add() -> None:\n    assert add(1, 2) == {expected}\n"
    )
    (folder / "tests" / "unit" / "test_calc.py").write_text(test, encoding="utf-8")


def test_checks_run_the_tests_once_there_are_some(project: Sandbox) -> None:
    write_tested_module(project.folder, 3)
    code, output = check(project.folder)
    assert code == 0, output
    write_tested_module(project.folder, 4)
    code, output = check(project.folder)
    assert code == 2
    assert "`pytest -q --cov=src --cov-branch --cov-fail-under=80` failed" in output
    assert "test_add" in output


def test_a_test_may_run_a_process(project: Sandbox) -> None:
    write_tested_module(project.folder, 3)
    test = project.folder / "tests" / "e2e" / "test_process.py"
    test.write_text(PROCESS_TEST, encoding="utf-8")
    code, output = check(project.folder)
    assert code == 0, output


MAIN = (
    '"""Entry point."""\n\nimport sys\n\nfrom src.calc import add\n\n'
    'sys.stdout.write(f"{add(1, 2)}\\n")\n'
)
MAIN_TEST = (  # the only test that reaches src/calc.py runs main.py as a process
    "import subprocess\nimport sys\n\n\n"
    "def test_main_prints_the_sum() -> None:\n"
    '    command = [sys.executable, "main.py"]\n'
    "    done = subprocess.run(command, capture_output=True, text=True, check=False)\n"
    '    assert done.stdout.strip() == "3"\n'
)


def test_code_that_a_test_runs_in_a_process_counts_for_coverage(project: Sandbox) -> None:
    # Without `patch = subprocess` in .coveragerc, src/calc.py has 0% and the floor fails.
    (project.folder / "src" / "__init__.py").write_text('"""Source."""\n', encoding="utf-8")
    (project.folder / "src" / "calc.py").write_text(CALC, encoding="utf-8")
    (project.folder / "main.py").write_text(MAIN, encoding="utf-8")
    (project.folder / "tests" / "e2e" / "test_main.py").write_text(MAIN_TEST, encoding="utf-8")
    code, output = check(project.folder)
    assert code == 0, output


def test_code_with_no_test_fails(project: Sandbox) -> None:
    # A package file that holds only a docstring is not code.
    (project.folder / "src" / "__init__.py").write_text(GOOD, encoding="utf-8")
    code, output = check(project.folder)
    assert code == 0, output
    assert "skipped  pytest (no test_*.py in tests/)" in output
    (project.folder / "src" / "calc.py").write_text(CALC, encoding="utf-8")
    code, output = check(project.folder)
    assert code == 2
    assert "failed   pytest" in output
    assert "`src/` holds Python code, and `tests/` holds no `test_*.py` file." in output
    # The rule does not apply when the tests are skipped.
    (project.folder / "docs" / "plan.md").write_text("# Plan\n", encoding="utf-8")
    project.git("add", "docs/plan.md")
    code, output = check(project.folder)
    assert code == 0, output


def test_a_live_test_does_not_count_as_a_test(project: Sandbox) -> None:
    # The normal test runs skip tests/live/, so pytest would collect nothing there.
    live = project.folder / "tests" / "live"
    live.mkdir(exist_ok=True)
    (live / "test_x.py").write_text("def test_x() -> None:\n    assert True\n", encoding="utf-8")
    code, output = check(project.folder)
    assert code == 0, output
    assert "skipped  pytest (no test_*.py in tests/)" in output
    (project.folder / "src" / "calc.py").write_text(CALC, encoding="utf-8")
    code, output = check(project.folder)
    assert code == 2
    assert "`src/` holds Python code, and `tests/` holds no `test_*.py` file." in output


def test_javascript_with_no_test_fails(tmp_path: Path) -> None:
    # No npm runs here: each check is skipped, or it fails before it needs a tool.
    folder = tmp_path / "web"
    build(folder, "--with", "javascript")
    code, output = check(folder)
    assert code == 0, output
    assert "skipped  eslint (no JavaScript in src/ or tests/)" in output
    assert "skipped  node --test (no *.test.js in tests/)" in output
    assert "All checks passed." in output
    (folder / "src" / "main.js").write_text("export const one = 1;\n", encoding="utf-8")
    code, output = check(folder)
    assert code == 2
    assert "failed   node --test" in output
    assert "`src/` holds JavaScript code, and `tests/` holds no `*.test.js` file." in output


def test_eslint_allows_one_class_per_file() -> None:
    config = (bi.assets_dir() / "eslint.config.js").read_text(encoding="utf-8")
    assert '"max-classes-per-file": ["error", 1]' in config


def test_a_todo_comment_fails(project: Sandbox) -> None:
    todo = '"""A module."""\n\n# TODO: finish the module.\n'
    (project.folder / "src" / "todo.py").write_text(todo, encoding="utf-8")
    code, output = check(project.folder)
    assert code == 2
    assert "FIX002" in output or "line-contains-todo" in output


def test_eslint_refuses_a_todo_comment() -> None:
    config = (bi.assets_dir() / "eslint.config.js").read_text(encoding="utf-8")
    terms = '"no-warning-comments": ["error", { terms: ["todo", "fixme", "xxx", "hack"]'
    assert terms in config


def test_eslint_allows_console_and_fetch_in_their_modules_in_any_folder_of_src() -> None:
    # The design chooses the folder of the page, such as src/web/ next to a Python server, and no
    # session may edit eslint.config.js. The sixth real run blocked on the old `src/log.js`.
    config = (bi.assets_dir() / "eslint.config.js").read_text(encoding="utf-8")
    assert '{ files: ["src/**/api.js"], rules: { "no-restricted-globals": "off" } }' in config
    assert '{ files: ["src/**/log.js"], rules: { "no-console": "off" } }' in config


def stylelint_config() -> dict[str, object]:
    """Return the Stylelint config that new projects get."""
    text = (bi.assets_dir() / ".stylelintrc.json").read_text(encoding="utf-8")
    config: dict[str, object] = json.loads(text)
    return config


def test_stylelint_refuses_a_color_outside_the_theme() -> None:
    config = stylelint_config()
    rules = config["rules"]
    assert isinstance(rules, dict)
    assert rules["color-no-hex"] is True
    assert rules["color-named"] == "never"
    assert {"rgb", "hsl", "oklch"} <= set(rules["function-disallowed-list"])
    overrides = config["overrides"]
    assert isinstance(overrides, list)
    theme = next(o for o in overrides if o["files"] == ["**/theme.css"])
    assert set(theme["rules"]) == {"color-no-hex", "color-named", "function-disallowed-list"}
    assert all(value is None for value in theme["rules"].values())


@pytest.mark.parametrize(
    ("name", "valid"),
    [
        ("sidebar", True),
        ("sidebar__toggle", True),
        ("sidebar__toggle--open", True),
        ("main-view__search-box--wide", True),
        ("card--active", True),
        ("blueBox", False),
        ("sidebar_toggle", False),
        ("sidebar__toggle__icon", False),
        ("Sidebar", False),
    ],
)
def test_stylelint_checks_the_bem_form_of_a_class(name: str, valid: bool) -> None:
    rules = stylelint_config()["rules"]
    assert isinstance(rules, dict)
    pattern = rules["selector-class-pattern"][0]
    assert (re.fullmatch(pattern, name) is not None) is valid


def test_a_new_project_ignores_the_release_folder(tmp_path: Path) -> None:
    build(tmp_path / "my-app")
    assert "dist/" in (tmp_path / "my-app" / ".gitignore").read_text("utf-8").splitlines()


def write_module(folder: Path, name: str, imports: str = "") -> None:
    """Write a Python file of the project: a docstring, then the import lines."""
    path = folder / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f'"""A module."""\n\n{imports}', encoding="utf-8")


def write_scripts(folder: Path, files: dict[str, str]) -> None:
    """Write JavaScript files of the project: each name with its text."""
    for name, text in files.items():
        path = folder / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def write_design(folder: Path, section: str) -> None:
    """Write a docs/design.md that holds the section, between two other sections."""
    text = f"# Design\n\n### 2.3 Settings\n\n{section}\n## 3. Data model\n"
    (folder / "docs" / "design.md").write_text(text, encoding="utf-8")


def test_module_boundaries_follow_the_table_of_the_design(project: Sandbox) -> None:
    rows = "| `src/orders` | `src/payments`, `src/clock.py` |\n| `src/payments` | none |\n"
    write_design(project.folder, BOUNDARIES + rows + "| `src/clock.py` | none |\n")
    write_module(project.folder, "src/clock.py")
    write_module(project.folder, "src/payments/core.py", "import json\n\nfrom src import util\n")
    orders = "import src.clock\nfrom src.payments import core\nfrom src.payments.core import pay\n"
    write_module(project.folder, "src/orders/api.py", orders)
    # A module that the table does not list can import each module.
    write_module(project.folder, "src/util.py", "from src.orders import api\n")
    _, output = check(project.folder)
    assert "passed   module boundaries" in output
    write_module(project.folder, "src/payments/core.py", "import src.orders.api\n")
    write_module(project.folder, "src/clock.py", "from src import payments\n")
    code, output = check(project.folder)
    assert code == 2
    assert "failed   module boundaries" in output
    for problem in [
        "src/clock.py:3 imports src/payments. The row of src/clock does not permit it.",
        "src/payments/core.py:3 imports src/orders. The row of src/payments does not permit it.",
    ]:
        assert problem in output


JS_ROWS = "| `src/orders` | `src/payments` |\n| `src/payments` | none |\n| `src/api.js` | none |\n"
JS_PERMITTED = {
    "src/orders/list.js": 'import { pay } from "../payments/pay.js";\nimport fs from "node:fs";\n',
    # A comment is not an import, and a package is not a module of the table.
    "src/payments/pay.js": '// import "../orders/list.js";\nimport "left-pad";\n',
    "src/api.js": "export const get = 1;\n",
    # A module that the table does not list can import each module.
    "src/main.js": 'import "./orders/list.js";\nimport "./api.js";\n',
}
JS_REFUSED = {
    "src/payments/pay.js": 'const list = require("../orders/list.js");\n',
    "src/api.js": (
        'export { pay } from "/src/payments/pay.js";\nconst later = import("./orders/list.js");\n'
    ),
}


def test_module_boundaries_cover_javascript(tmp_path: Path) -> None:
    # No npm runs here: the check of the module boundaries needs no tool.
    folder = tmp_path / "web"
    build(folder, "--with", "javascript")
    write_design(folder, BOUNDARIES + JS_ROWS)
    write_scripts(folder, JS_PERMITTED)
    _, output = check(folder)
    assert "passed   module boundaries" in output
    write_scripts(folder, JS_REFUSED)
    code, output = check(folder)
    assert code == 2
    assert "failed   module boundaries" in output
    for problem in [
        "src/api.js:1 imports src/payments. The row of src/api does not permit it.",
        "src/api.js:2 imports src/orders. The row of src/api does not permit it.",
        "src/payments/pay.js:1 imports src/orders. The row of src/payments does not permit it.",
    ]:
        assert problem in output


def test_an_import_belongs_to_the_most_specific_listed_module() -> None:
    owner = load_check().owner
    modules = ["src.payments", "src.payments.core"]
    assert owner("src.payments.core.fees", modules) == "src.payments.core"
    assert owner("src.payments.api", modules) == "src.payments"
    assert owner("src.payments_old", modules) == ""


def test_module_boundaries_are_skipped_with_no_table_or_no_row(project: Sandbox) -> None:
    write_module(project.folder, "src/payments/core.py", "import src.orders.api\n")
    write_design(project.folder, "TBD\n")
    _, output = check(project.folder)
    assert "skipped  module boundaries (docs/design.md has no table of module boundaries)" in output
    write_design(project.folder, BOUNDARIES)
    _, output = check(project.folder)
    assert "skipped  module boundaries (the table of module boundaries has no row)" in output


def test_a_commit_of_docs_alone_skips_the_tests(project: Sandbox) -> None:
    # A blocked milestone and an approval commit docs/plan.md alone: no test result can change.
    write_tested_module(project.folder, 4)
    (project.folder / "docs" / "plan.md").write_text("# Plan\n", encoding="utf-8")
    project.git("add", "docs/plan.md")
    code, output = check(project.folder)
    assert code == 0, output
    assert "skipped  pytest (only files under docs/ are staged)" in output
    assert "All checks passed." in output
    project.git("add", "-A")
    code, output = check(project.folder)
    assert code == 2
    assert "test_add" in output


def test_docs_alone_still_run_the_other_checks(project: Sandbox) -> None:
    (project.folder / "src" / "bad.py").write_text(BAD, encoding="utf-8")
    (project.folder / "docs" / "plan.md").write_text("# Plan\n", encoding="utf-8")
    project.git("add", "docs/plan.md")
    code, output = check(project.folder)
    assert code == 2
    assert "bad.py" in output


def test_pre_commit_hook_refuses_a_failing_commit(project: Sandbox) -> None:
    # The hook finds Python through the active conda environment, as in a VS Code terminal.
    env = {**project.env, "CONDA_DEFAULT_ENV": "demo", "CONDA_PREFIX": sys.prefix}
    (project.folder / "src" / "bad.py").write_text(BAD, encoding="utf-8")
    project.git("add", "-A")
    refused = run([git_path(), "commit", "-m", "bad"], project.folder, env)
    assert refused.returncode != 0
    assert "ruff check" in refused.stderr
    (project.folder / "src" / "bad.py").write_text(GOOD, encoding="utf-8")
    project.git("add", "-A")
    accepted = run([git_path(), "commit", "-m", "good"], project.folder, env)
    assert accepted.returncode == 0, accepted.stderr


HARD_TEXT = (  # semicolons, passive voice and long sentences: far over 2.5 for 100 words
    "The data is processed by the service; the results are stored by the database layer "
    "after they have been validated by the component that was configured by the operator. "
) * 8


def test_docs_that_are_hard_to_read_fail(project: Sandbox) -> None:
    (project.folder / "docs" / "notes.md").write_text(HARD_TEXT, encoding="utf-8")
    code, output = check(project.folder)
    assert code == 2
    assert "failed   plain docs" in output
    assert "docs/notes.md:" in output
    assert "(over)" in output


def test_a_sentence_in_two_docs_fails(project: Sandbox) -> None:
    sentence = "The runner keeps the work of a blocked milestone in its own branch for later.\n"
    (project.folder / "docs" / "a.md").write_text(sentence, encoding="utf-8")
    (project.folder / "docs" / "b.md").write_text(sentence, encoding="utf-8")
    code, output = check(project.folder)
    assert code == 2
    assert "is in docs/a.md and docs/b.md. Keep it in one." in output


def test_a_long_purpose_in_readme_and_claude_md_passes(sandbox: Sandbox) -> None:
    # The builder writes the purpose into README.md and CLAUDE.md. A purpose of 12 words or more
    # failed the check of repeated sentences at the first commit of the docs (fourth real run).
    purpose = "Turns a title into a URL slug, and signs readers up for the newsletter"
    result = sandbox.init("--with", "python", "--no-github", "--no-conda", "--purpose", purpose)
    assert result.returncode == 0, result.stderr
    (sandbox.folder / "docs" / "notes.md").write_text("A short note.\n", encoding="utf-8")
    sandbox.git("add", "docs/notes.md")
    code, output = check(sandbox.folder)
    assert code == 0, output
    assert "passed   plain docs" in output


def test_a_skipped_file_is_left_out_of_the_repeated_check(tmp_path: Path) -> None:
    sentence = "The runner keeps the work of a blocked milestone in its own branch for later.\n"
    for name in ("a.md", "b.md"):
        (tmp_path / name).write_text(sentence, encoding="utf-8")
    script = str(bi.assets_dir() / "scripts" / "ste_lint.py")
    files = [str(tmp_path / "a.md"), str(tmp_path / "b.md")]
    assert run([sys.executable, script, "--repeated", "12", *files]).returncode == 1
    skip = ["--repeated-skip", (tmp_path / "b.md").as_posix()]
    assert run([sys.executable, script, "--repeated", "12", *skip, *files]).returncode == 0


def test_a_long_list_or_table_is_not_a_long_paragraph(tmp_path: Path) -> None:
    # The style asks for lists and tables before prose (USER-20), so they do not count as one
    # long paragraph, as they do in ste-lint.py.
    items = "".join(f"- Item {n} names one short fact for the user.\n" for n in range(12))
    table = "| A | B |\n| --- | --- |\n" + "| one | two |\n" * 12
    doc = tmp_path / "list.md"
    doc.write_text(items + "\n" + table, encoding="utf-8")
    script = bi.assets_dir() / "scripts" / "ste_lint.py"
    done = run([sys.executable, str(script), "--fail-over", "2.5", str(doc)])
    assert done.returncode == 0, done.stdout
    assert "0.0 for 100 (ok)" in done.stdout
