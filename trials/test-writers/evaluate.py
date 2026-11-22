"""Score the tests that one writer wrote for milestone M1 of a trial kit.

Usage: python evaluate.py <kit folder> <project folder> [--json FILE]

The project folder is a project that sherpa built, with the docs of the kit, and the tests that
the runner copied back (`milestones-runner.py --tests-only M1`). The kit folder holds `docs/`,
`reference/` (a correct implementation) and `mutants.json` (the seeded bugs).

The gates, each passed or failed:
- ruff check and ruff format on tests/
- spec_coverage.py M1: each requirement and example of the block has a test
- before the code: the tests fail, and only for a valid reason
- on correct code: the tests pass
- mypy on tests/, with the code present
- coverage: 80% branch coverage of the correct code, also of the processes that a test starts
- the spec and the plan are unchanged

Then each seeded bug is applied to a copy of the correct code: a bug is caught when a test fails.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PY = sys.executable
CONFIGS = ("ruff.toml", "mypy.ini", "pytest.ini", ".coveragerc")
INVALID = re.compile(r"SyntaxError|NameError|fixture '[^']+' not found|IndentationError")


def run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    """Run a command and capture its output."""
    return subprocess.run(
        command, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace"
    )


def last_line(done: subprocess.CompletedProcess[str]) -> str:
    """Return the last line of the output of a command."""
    lines = (done.stdout + done.stderr).strip().splitlines()
    return lines[-1] if lines else ""


def copy_code(kit: Path, project: Path, target: Path) -> None:
    """Make a copy of the correct code, with the configs and the tests of the project."""
    shutil.copytree(kit / "reference", target, ignore=shutil.ignore_patterns("tests", "__pycache__"))
    for name in CONFIGS:
        if (project / name).is_file():
            shutil.copyfile(project / name, target / name)
    shutil.copytree(
        project / "tests", target / "tests", ignore=shutil.ignore_patterns("__pycache__")
    )


def gates(kit: Path, project: Path, code: Path) -> dict[str, bool]:
    """Return the result of each gate, and print its line."""
    pytest = [PY, "-m", "pytest", "-q", "-p", "no:cacheprovider"]
    results: dict[str, bool] = {}
    checks = {
        "ruff check": (project, [PY, "-m", "ruff", "check", "tests"]),
        "ruff format": (project, [PY, "-m", "ruff", "format", "--check", "tests"]),
        "spec_coverage M1": (project, [PY, "scripts/spec_coverage.py", "M1"]),
        "pass on correct code": (code, pytest),
        "mypy with the code": (code, [PY, "-m", "mypy", "tests"]),
        "coverage 80%": (code, [*pytest, "--cov=src", "--cov-branch", "--cov-fail-under=80"]),
    }
    for name, (cwd, command) in checks.items():
        done = run(command, cwd)
        results[name] = done.returncode == 0
        print(f"{'passed' if results[name] else 'FAILED'}  {name}: {last_line(done)}")
    before = run([*pytest, "--tb=line"], project)
    results["fail before the code"] = before.returncode != 0 and not INVALID.search(before.stdout)
    print(f"{'passed' if results['fail before the code'] else 'FAILED'}  fail before the code")
    same = all(
        (project / "docs" / name).read_bytes() == (kit / "docs" / name).read_bytes()
        for name in ("spec.md", "plan.md")
    )
    results["spec and plan unchanged"] = same
    print(f"{'passed' if same else 'FAILED'}  spec and plan unchanged")
    return results


def caught_bugs(kit: Path, code: Path, scratch: Path) -> tuple[int, int]:
    """Apply each seeded bug to a copy of the correct code; return how many a test caught."""
    mutants = json.loads((kit / "mutants.json").read_text(encoding="utf-8"))
    caught = 0
    for number, mutant in enumerate(mutants):
        copy = scratch / f"mutant-{number}"
        shutil.copytree(code, copy)
        path = copy / mutant["file"]
        text = path.read_text(encoding="utf-8")
        assert mutant["old"] in text, mutant["label"]
        path.write_text(text.replace(mutant["old"], mutant["new"], 1), encoding="utf-8")
        failed = run([PY, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-x"], copy).returncode
        caught += failed != 0
        print(f"   {'CAUGHT' if failed else 'MISSED'}  {mutant['label']}")
    return caught, len(mutants)


def main() -> None:
    """Print the gates and the seeded bugs; write the summary as JSON when --json is given."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("kit", type=Path)
    parser.add_argument("project", type=Path)
    parser.add_argument("--json", type=Path, default=None)
    args = parser.parse_args()
    files = sorted(p.relative_to(args.project).as_posix() for p in (args.project / "tests").rglob("test_*.py"))
    print("test files:", ", ".join(files))
    with tempfile.TemporaryDirectory() as folder:
        scratch = Path(folder)
        code = scratch / "code"
        copy_code(args.kit, args.project, code)
        results = gates(args.kit, args.project, code)
        caught, total = caught_bugs(args.kit, code, scratch)
    print(f"seeded bugs caught: {caught} of {total}")
    summary = {"gates": results, "all_gates": all(results.values()), "caught": caught, "total": total}
    if args.json is not None:
        args.json.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
