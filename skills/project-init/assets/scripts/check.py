"""Run the project's checks and tests, for Python and for the web.

Python: ruff, mypy, one class per file, pytest. Web: ESLint, tsc, Prettier, Stylelint,
`node --test`. Both: module boundaries.

Two hooks run it, and so can you:
    python scripts/check.py            # everything. The git pre-commit hook runs this.
    python scripts/check.py --edited   # one edited file, with a Claude Code hook's JSON on stdin

The full run prints one line for each check of the project's stack, with its result: `passed`,
`failed` or `skipped`. A skipped line gives the reason, such as `skipped  mypy (no Python in
src/)`. Then the output of each failed check goes to standard error. The last line is
`All checks passed.` when no check failed. A project with no `ruff.toml` and no `package.json`
has no check, and the run prints `No check applied.`

Each check runs once there is something for it to check. Python (with `ruff.toml`): ruff always,
mypy and one class per file once `src/` holds Python, pytest with the 80% branch-coverage
floor once `tests/` holds a `test_*.py`. Web (with `package.json`): ESLint and tsc (with
`eslint.config.js`) once `src/` or `tests/` holds JavaScript, Prettier once they hold
JavaScript, CSS or HTML, Stylelint once `src/` holds CSS, `node --test` once `tests/` holds a
`*.test.js`. Module boundaries, with one line for the two stacks, once the design has rows for
it.

Code with no test fails. The pytest check fails when `src/` holds Python code and `tests/` holds
no `test_*.py`. A Python file is code when it holds a statement other than a docstring, so a new
project with an empty package file can still commit. The `node --test` check fails when `src/`
holds a JavaScript file and `tests/` holds no `*.test.js`. A file under `tests/live/` does not
count as a test, because the normal test runs skip that folder. When every staged file is under
`docs/`, the tests are skipped (the other checks still run): a commit of the plan or the spec
alone cannot change a test result.

One class per file: a Python file under `src/` defines at most one class at the top level.

UTF-8 text: each staged text file must be valid UTF-8 and must not hold the replacement character
U+FFFD, the mark of a text that was read in a wrong encoding. A shell can write a file in another
encoding (Windows PowerShell 5.1 writes in the ANSI code page). A file with a NUL byte in its first
8000 bytes is binary, as git counts it, and is skipped. The check is skipped when nothing is
staged, and in a project with no check of a stack.

Module boundaries: `docs/design.md` can hold a table under `### 2.4 Module boundaries`, with the
columns `Module` and `May import`. A module is a folder or a file under `src/`, written as a path
(`src/payments`). A Python or JavaScript file of a listed module must not import another listed
module that its row does not permit. An import of something that the table does not list is
always permitted. In Python, the check reads absolute imports from the project root, such as
`import src.payments`. In JavaScript, it reads each `import`, `export ... from` and `require`
that names a file: a path from the file (`./api.js`, `../orders/store.js`) or from the project
root (`/src/api.js`, `src/api.js`). An import of a package names no file.

The full run exits 2 if anything fails, so that git refuses the commit. With --edited, ruff,
ESLint, Stylelint and Prettier fix what they can in that one file (tests do not run). The check
of one class per file also runs, for an edited Python file under `src/`. The rest goes back to
Claude as a JSON `block` decision on stdout (exit 0). Claude Code may run hooks in PowerShell,
which turns every failing exit code into 1, so an exit code alone would not reach Claude. A tool
that is not installed fails the full run, but is skipped after an edit.
"""

import argparse
import ast
import json
import os
import re
import shutil
import subprocess
import sys
from collections.abc import Iterable
from importlib.util import find_spec
from pathlib import Path
from typing import NamedTuple

ROOT = Path(__file__).resolve().parent.parent
FAILED = 2
JS_SUFFIXES = {".js", ".mjs", ".cjs", ".ts"}
WEB_SUFFIXES = JS_SUFFIXES | {".css", ".html"}
DOCS_PREFIX = "docs/"
LIVE = "live"  # tests/live/ holds the live checks, and scripts/live_checks.py runs them
PASS, FAIL, SKIP = "passed", "failed", "skipped"
NO_PYTHON = "no Python in src/"
NO_WEB = "no JavaScript, CSS or HTML in src/ or tests/"
ONE_CLASS = "one class per file"
UTF8 = "UTF-8 text"
REPLACEMENT_CHARACTER = chr(0xFFFD)  # what a decoder puts in place of a byte it cannot read
BINARY_PROBE = 8000  # git counts a file as binary when a NUL byte is in its first 8000 bytes
BOUNDARIES = "module boundaries"
BOUNDARIES_HEADING = "### 2.4 Module boundaries"
# A file that JavaScript names in an import: after `from`, `import`, `import(` or `require(`.
SCRIPT_IMPORT = re.compile(
    r"""(?:\bfrom\s*|\bimport\s*\(?\s*|\brequire\s*\(\s*)(["'])([^"'\n]+)\1"""
)
COMMENT_STARTS = ("//", "/*", "*")
ROOT_PREFIXES = ("/src/", "src/")  # an import path from the project root


class Result(NamedTuple):
    """The result of one check. `detail` is the reason of a skip, or the report of a failure."""

    name: str
    state: str
    detail: str = ""


def run(command: list[str]) -> tuple[int, str]:
    """Run a command in the project root. Return its exit code and its output, without colors."""
    result = subprocess.run(
        command,
        cwd=ROOT,
        env={**os.environ, "NO_COLOR": "1", "FORCE_COLOR": "0"},
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return result.returncode, (result.stdout + result.stderr).strip()


def python_tool(*args: str) -> list[str]:
    """Return the command that runs a Python tool from this environment."""
    return [sys.executable, "-m", *args]


def has_files(folders: list[str], suffixes: set[str]) -> bool:
    """Return True if any of the folders holds a file with one of the suffixes."""
    return any(p.suffix in suffixes for folder in folders for p in (ROOT / folder).rglob("*"))


def has_tests(pattern: str) -> bool:
    """Return True if `tests/` holds a file whose name matches the pattern.

    A file under `tests/live/` does not count: the normal test runs skip that folder.
    """
    tests = ROOT / "tests"
    return any(path.relative_to(tests).parts[0] != LIVE for path in tests.rglob(pattern))


def staged_files() -> list[str]:
    """Return the paths staged for the next commit; a moved file lists both of its paths."""
    git = shutil.which("git") or "git"
    code, output = run([git, "diff", "--cached", "--name-only", "--no-renames"])
    return output.splitlines() if code == 0 else []


def staged_bytes(path: str) -> bytes | None:
    """Return the staged content of a file, or None when the index has none (a deleted file)."""
    git = shutil.which("git") or "git"
    done = subprocess.run([git, "show", f":{path}"], cwd=ROOT, capture_output=True, check=False)
    return done.stdout if done.returncode == 0 else None


def encoding_problems(paths: list[str]) -> list[str]:
    """Return one message for each staged text file that is not clean UTF-8."""
    problems: list[str] = []
    for path in paths:
        data = staged_bytes(path)
        if data is None or b"\0" in data[:BINARY_PROBE]:
            continue
        if REPLACEMENT_CHARACTER in data.decode("utf-8", errors="replace"):
            problems.append(
                f"{path} is not valid UTF-8, or it holds the character U+FFFD. Write the file "
                "again with the Edit or Write tool, not through the shell."
            )
    return problems


def encoding_result() -> Result:
    """Return the result of the check that each staged text file is UTF-8."""
    staged = staged_files()
    if not staged:
        return Result(UTF8, SKIP, "no staged file")
    return problems_result(UTF8, encoding_problems(staged))


def only_docs_staged() -> bool:
    """Return True if files are staged and every one of them is under `docs/`."""
    staged = staged_files()
    return bool(staged) and all(path.startswith(DOCS_PREFIX) for path in staged)


def why_not_runnable(command: list[str]) -> str:
    """Return why a check cannot run (its tool is not installed), or '' if it can."""
    if command[1:2] == ["-m"]:
        modules = [command[2], *(["pytest_cov"] if "--cov=src" in command else [])]
        missing = [m.replace("_", "-") for m in modules if find_spec(m) is None]
        if missing:
            return f"`{'`, `'.join(missing)}` not installed in this environment. See the README."
        return ""
    if shutil.which(command[0]) is None:
        return f"`{Path(command[0]).name}` is not installed."
    if not (ROOT / "node_modules").is_dir():
        return "The JavaScript tools are not installed. Run `npm install`."
    return ""


def label(command: list[str]) -> str:
    """Return a short name for a command, such as `ruff check .` or `npm run lint`."""
    words = command[2:] if command[1:2] == ["-m"] else [Path(command[0]).stem, *command[1:]]
    return " ".join(words)


def failure(name: str, title: str, problem: str) -> Result:
    """Return a failed result. Its report starts with the title, then gives the problem."""
    return Result(name, FAIL, f"`{title}` failed:\n{problem}")


def command_result(name: str, command: list[str]) -> Result:
    """Run the command of a check and return its result. A tool that is not installed fails."""
    problem = why_not_runnable(command)
    if not problem:
        code, output = run(command)
        problem = output if code else ""
    return failure(name, label(command), problem) if problem else Result(name, PASS)


def problems_result(name: str, problems: list[str]) -> Result:
    """Return the result of a check that this script does itself, from the problems it found."""
    return failure(name, name, "\n".join(problems)) if problems else Result(name, PASS)


def tests_result(name: str, command: list[str], pattern: str, code: str) -> Result:
    """Return the result of a test check. Code with no test fails.

    Args:
        name: The name of the check.
        command: The command that runs the tests.
        pattern: The file name pattern of a test, such as `test_*.py`.
        code: The language of the code that `src/` holds, or '' when it holds none.
    """
    if only_docs_staged():
        return Result(name, SKIP, f"only files under {DOCS_PREFIX} are staged")
    if has_tests(pattern):
        return command_result(name, command)
    if code:
        problem = f"`src/` holds {code} code, and `tests/` holds no `{pattern}` file. Write a test."
        return failure(name, name, problem)
    return Result(name, SKIP, f"no {pattern} in tests/")


def relative(path: Path) -> str:
    """Return the path of a project file from the project root, with forward slashes."""
    return path.relative_to(ROOT).as_posix()


def source_files() -> list[Path]:
    """Return the Python files under `src/`, in a fixed order."""
    return sorted((ROOT / "src").rglob("*.py"))


def script_files() -> list[Path]:
    """Return the JavaScript files under `src/`, in a fixed order."""
    return sorted(p for p in (ROOT / "src").rglob("*") if p.suffix in JS_SUFFIXES)


def parse(path: Path) -> ast.Module | None:
    """Return the syntax tree of a Python file, or None if it does not parse (ruff reports it)."""
    try:
        return ast.parse(path.read_bytes())
    except (SyntaxError, ValueError):
        return None


def is_code(path: Path) -> bool:
    """Return True if a Python file holds a statement other than a docstring."""
    tree = parse(path)
    if tree is None:
        return False
    has_docstring = ast.get_docstring(tree, clean=False) is not None
    return len(tree.body) > (1 if has_docstring else 0)


def class_problems(paths: list[Path]) -> list[str]:
    """Return one message for each Python file that defines more than one top-level class."""
    problems: list[str] = []
    for path in paths:
        tree = parse(path)
        names = [node.name for node in tree.body if isinstance(node, ast.ClassDef)] if tree else []
        if len(names) > 1:
            found = f"{relative(path)} defines {len(names)} classes: {', '.join(names)}."
            problems.append(f"{found} Keep one class in a file.")
    return problems


def one_class_result() -> Result:
    """Return the result of the check of one class per file, for `src/`."""
    files = source_files()
    if not files:
        return Result(ONE_CLASS, SKIP, NO_PYTHON)
    return problems_result(ONE_CLASS, class_problems(files))


def table_rows(text: str, heading: str) -> list[list[str]]:
    """Return the cells of each table row under a heading, up to the next heading."""
    rows: list[list[str]] = []
    inside = False
    for line in (raw.strip() for raw in text.splitlines()):
        if line.startswith("#"):
            inside = line == heading
        elif inside and line.startswith("|"):
            rows.append([cell.strip().strip("`") for cell in line.strip("|").split("|")])
    return rows


def dotted(path: str) -> str:
    """Return a module path of the design (`src/payments`) as a dotted name (`src.payments`).

    The suffix of a file (`src/clock.py`, `src/api.js`) is not part of the name.
    """
    name = Path(path.strip().strip("`").strip("/"))
    if name.suffix in JS_SUFFIXES | {".py"}:
        name = name.with_suffix("")
    return ".".join(name.parts)


def permitted(cell: str) -> set[str]:
    """Return the dotted names of the modules that a `May import` cell lists."""
    names = {dotted(name) for name in cell.split(",")}
    return names - {"", "none"}


def boundaries() -> dict[str, set[str]] | None:
    """Return each module of the design's table with the modules it may import.

    Returns:
        The rows of the table, with dotted names. None when the design has no such table.
    """
    design = ROOT / "docs" / "design.md"
    text = design.read_text(encoding="utf-8") if design.is_file() else ""
    rows = table_rows(text, BOUNDARIES_HEADING)
    if not rows or "Module" not in rows[0] or "May import" not in rows[0]:
        return None
    module, allowed = rows[0].index("Module"), rows[0].index("May import")
    table: dict[str, set[str]] = {}
    for row in rows[1:]:
        name = dotted(row[module]) if len(row) > max(module, allowed) else ""
        if name.strip("-:"):  # not an empty cell, and not the line under the header
            table[name] = permitted(row[allowed])
    return table


def owner(name: str, modules: Iterable[str]) -> str:
    """Return the most specific listed module that holds a dotted name, or '' if none does."""
    holders = [module for module in modules if f"{name}.".startswith(f"{module}.")]
    return max(holders, key=len, default="")


def imported_names(tree: ast.Module) -> list[tuple[int, str]]:
    """Return the line and the dotted name of each absolute import in a syntax tree."""
    names: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names += [(node.lineno, alias.name) for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names += [(node.lineno, f"{node.module}.{alias.name}") for alias in node.names]
    return names


def script_target(path: Path, specifier: str) -> str:
    """Return the dotted name of the project file that a JavaScript import names, or ''.

    A specifier that starts with `.` is a path from the file. One that starts with `/src/` or
    `src/` is a path from the project root. Each other specifier names a package.
    """
    if specifier.startswith("."):
        target = (path.parent / specifier).resolve()
    elif specifier.startswith(ROOT_PREFIXES):
        target = (ROOT / specifier.lstrip("/")).resolve()
    else:
        return ""
    return dotted(relative(target)) if target.is_relative_to(ROOT) else ""


def script_imports(path: Path) -> list[tuple[int, str]]:
    """Return the line and the dotted name of each project file that a JavaScript file imports.

    The file is read as text, one line at a time. A line that starts a comment is skipped.
    """
    names: list[tuple[int, str]] = []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for number, line in enumerate(lines, start=1):
        if line.lstrip().startswith(COMMENT_STARTS):
            continue
        targets = (script_target(path, found.group(2)) for found in SCRIPT_IMPORT.finditer(line))
        names += [(number, target) for target in targets if target]
    return names


def imports_of(path: Path) -> list[tuple[int, str]]:
    """Return the line and the dotted name of each import of a Python or JavaScript file."""
    if path.suffix != ".py":
        return script_imports(path)
    tree = parse(path)
    return imported_names(tree) if tree else []


def file_boundary_problems(path: Path, table: dict[str, set[str]]) -> list[str]:
    """Return one message for each import of one file that its module's row does not permit."""
    home = owner(dotted(relative(path)), table)
    problems: list[str] = []
    for line, name in imports_of(path) if home else []:
        target = owner(name, table)
        if target and target != home and target not in table[home]:
            imports = f"{relative(path)}:{line} imports {target.replace('.', '/')}."
            problems.append(f"{imports} The row of {home.replace('.', '/')} does not permit it.")
    return problems


def boundaries_result() -> Result:
    """Return the result of the check of module boundaries, or a skip if the design has no row."""
    table = boundaries()
    if table is None:
        return Result(BOUNDARIES, SKIP, "docs/design.md has no table of module boundaries")
    if not table:
        return Result(BOUNDARIES, SKIP, "the table of module boundaries has no row")
    files = source_files() + script_files()
    problems = [p for path in files for p in file_boundary_problems(path, table)]
    return problems_result(BOUNDARIES, problems)


def python_results() -> list[Result]:
    """Return the result of each Python check, or no result for a project with no `ruff.toml`."""
    if not (ROOT / "ruff.toml").is_file():
        return []
    files = source_files()
    coverage = ["--cov=src", "--cov-branch", "--cov-fail-under=80"]
    code = "Python" if any(is_code(path) for path in files) else ""
    return [
        command_result("ruff check", python_tool("ruff", "check", ".")),
        command_result("ruff format", python_tool("ruff", "format", "--check", ".")),
        command_result("mypy", python_tool("mypy")) if files else Result("mypy", SKIP, NO_PYTHON),
        one_class_result(),
        boundaries_result(),
        tests_result("pytest", python_tool("pytest", "-q", *coverage), "test_*.py", code),
    ]


def npm_command(script: str) -> list[str]:
    """Return the command that runs a script of package.json."""
    return [shutil.which("npm") or "npm", "run", script]


def npm_result(name: str, script: str, skip: str) -> Result:
    """Run a script of package.json and return its result, or a skip if `skip` gives a reason."""
    return Result(name, SKIP, skip) if skip else command_result(name, npm_command(script))


def lint_skip() -> str:
    """Return why ESLint and tsc have nothing to check, or '' if they have."""
    if not (ROOT / "eslint.config.js").is_file():
        return "no eslint.config.js"
    return "" if has_files(["src", "tests"], JS_SUFFIXES) else "no JavaScript in src/ or tests/"


def web_results() -> list[Result]:
    """Return the result of each web check, or no result for a project with no `package.json`."""
    if not (ROOT / "package.json").is_file():
        return []
    lint = lint_skip()
    web = has_files(["src", "tests"], WEB_SUFFIXES)
    css = has_files(["src"], {".css"})
    code = "JavaScript" if has_files(["src"], JS_SUFFIXES) else ""
    # A project with Python already has the line of the module boundaries.
    boundary = [] if (ROOT / "ruff.toml").is_file() else [boundaries_result()]
    return [
        npm_result("eslint", "lint", lint),
        npm_result("tsc", "typecheck", lint),
        npm_result("prettier", "format:check", "" if web else NO_WEB),
        npm_result("stylelint", "lint:css", "" if css else "no CSS in src/"),
        *boundary,
        tests_result("node --test", npm_command("test"), "*.test.js", code),
    ]


def inventory_line(result: Result) -> str:
    """Return the line of one check: its result, its name, and the reason of a skip."""
    reason = f" ({result.detail})" if result.state == SKIP else ""
    return f"{result.state:<9}{result.name}{reason}"


def check_all() -> int:
    """Run every check, print the line of each one, then each failure. Return 0 or FAILED."""
    results = python_results() + web_results()
    if results:
        results.insert(0, encoding_result())
    for result in results:
        print(inventory_line(result))
    failures = [result.detail for result in results if result.state == FAIL]
    if failures:
        sys.stdout.flush()
        print("\n\n".join(failures), file=sys.stderr)
        return FAILED
    print("All checks passed." if results else "No check applied.")
    return 0


def edited_file(hook_input: str) -> Path | None:
    """Return the file a Claude Code hook says was edited, if it is a file in this project."""
    tool_input = json.loads(hook_input or "{}").get("tool_input", {})
    raw = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
    path = (ROOT / raw).resolve()
    return path if raw and path.is_relative_to(ROOT) and path.is_file() else None


def node_tool(name: str) -> str | None:
    """Return the path of a tool `npm install` put in node_modules, or None."""
    return shutil.which(name, path=str(ROOT / "node_modules" / ".bin"))


def web_fix_commands(path: Path, relative_path: str) -> list[list[str]]:
    """Return the linter's fixes (ESLint or Stylelint), then Prettier's formatting, for one file."""
    linter = (
        "stylelint" if path.suffix == ".css" else "eslint" if path.suffix in JS_SUFFIXES else ""
    )
    commands: list[list[str]] = []
    for tool, option in [(linter, "--fix"), ("prettier", "--write")]:
        executable = node_tool(tool) if tool else None
        if executable:
            commands.append([executable, option, relative_path])
    return commands


def fix_commands(path: Path) -> list[list[str]]:
    """Return the commands that fix one file and report what they cannot fix.

    Python is formatted before the fixes (so line breaks do not count as errors) and after them
    (so a removed import leaves no blank line behind).
    """
    relative_path = str(path.relative_to(ROOT))
    if path.suffix == ".py" and (ROOT / "ruff.toml").is_file():
        formatting = python_tool("ruff", "format", relative_path)
        fixes = python_tool("ruff", "check", "--fix", "--output-format=concise", relative_path)
        return [formatting, fixes, formatting]
    if path.suffix in WEB_SUFFIXES:
        return web_fix_commands(path, relative_path)
    return []


def tool_problems(path: Path) -> list[str]:
    """Fix one file with its tools. Return what they cannot fix, or nothing if one is missing."""
    commands = fix_commands(path)
    if any(why_not_runnable(command) for command in commands):
        return []
    results = [run(command) for command in commands]
    return list(dict.fromkeys(output for code, output in results if code))


def edited_class_problems(path: Path) -> list[str]:
    """Return the problem of one class per file, for a Python file under `src/`."""
    checked = (ROOT / "ruff.toml").is_file() and path.suffix == ".py"
    return class_problems([path]) if checked and path.is_relative_to(ROOT / "src") else []


def check_edited(hook_input: str) -> int:
    """Fix and check the file named in the hook input. Print what is left as a block decision."""
    path = edited_file(hook_input)
    problems = tool_problems(path) + edited_class_problems(path) if path else []
    if problems:
        reason = f"Checks failed for {path}. Fix these:\n" + "\n".join(problems)
        print(json.dumps({"decision": "block", "reason": reason}))
    return 0


def parse_args() -> argparse.Namespace:
    """Read the command-line options."""
    parser = argparse.ArgumentParser(description="Run the project's checks.")
    parser.add_argument(
        "--edited", action="store_true", help="check one file named by a hook's JSON on stdin"
    )
    return parser.parse_args()


def main() -> int:
    """Run the full checks, or the checks for one edited file."""
    if parse_args().edited:
        return check_edited(sys.stdin.buffer.read().decode("utf-8"))
    return check_all()


if __name__ == "__main__":
    raise SystemExit(main())
