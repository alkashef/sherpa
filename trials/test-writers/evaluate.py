"""Evaluate the tests that one AI wrote: checks, failure before code, reference run, seeded bugs.

Usage: python evaluate.py <trial folder> <test folder name>
"""

import re
import shutil
import subprocess
import sys
from pathlib import Path

PY = sys.executable

MUTANTS = {
    "no NFKD": ("src/slug.py", 'unicodedata.normalize("NFKD", title)', "title"),
    "NFKC in place of NFKD": ("src/slug.py", '"NFKD"', '"NFKC"'),
    "cut at N characters": (
        "src/slug.py",
        "        if len(candidate) > max_length:\n            break\n        slug = candidate\n"
        "    return slug or words[0][:max_length]",
        "        slug = candidate\n    return slug[:max_length].rstrip('-')",
    ),
    "cut one word short (>=)": ("src/slug.py", "len(candidate) > max_length", "len(candidate) >= max_length"),
    "function default 50": ("src/slug.py", "max_length: int = 60", "max_length: int = 50"),
    "CLI default 50": ("src/cli.py", "max_length = 60", "max_length = 50"),
    "--max accepts 201": ("src/cli.py", "<= 200", "<= 201"),
    "--max accepts 0": ("src/cli.py", "not 1 <=", "not 0 <="),
    "--max accepts 1.5": (
        "src/cli.py",
        "if not value.isdigit() or not 1 <= int(value) <= 200:",
        "if not value.replace('.', '', 1).isdigit() or not 1 <= int(float(value)) <= 200:",
    ),
    "empty-slug exit code 1": (
        "src/cli.py",
        '        print(f"error: {error}", file=sys.stderr)\n        return 2',
        '        print(f"error: {error}", file=sys.stderr)\n        return 1',
    ),
    "empty-slug error on stdout": ("src/cli.py", 'print(f"error: {error}", file=sys.stderr)', 'print(f"error: {error}")'),
    "error wording": ("src/slug.py", '"the title has no letters or digits"', '"title has no letters or digits"'),
    "no newline after slug": ("src/cli.py", "print(make_slug(args[0], max_length))", "sys.stdout.write(make_slug(args[0], max_length))"),
    "keep non-ASCII letters": ("src/slug.py", '.encode("ascii", "ignore").decode("ascii")', ""),
    "first long word not cut": ("src/slug.py", "return slug or words[0][:max_length]", "return slug or words[0]"),
    "underscore kept": ("src/slug.py", 'r"[a-z0-9]+"', 'r"[a-z0-9_]+"'),
    "uppercase kept": ("src/slug.py", 're.findall(r"[a-z0-9]+", ascii_text.lower())', 're.findall(r"[A-Za-z0-9]+", ascii_text)'),
}


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")


def summary(out: str) -> str:
    lines = [line for line in out.splitlines() if re.search(r"\d+ (passed|failed|error)", line)]
    return lines[-1].strip("= ") if lines else out.strip().splitlines()[-1:][0] if out.strip() else "?"


def main() -> None:
    trial, name = Path(sys.argv[1]), sys.argv[2]
    tests = trial / name / "tests"
    project = trial / f"eval-{name}"
    shutil.rmtree(project, ignore_errors=True)
    shutil.copytree(trial / "slugger", project, ignore=shutil.ignore_patterns(".git", "tests"))
    shutil.copytree(tests, project / "tests")
    files = sorted(p.relative_to(project).as_posix() for p in (project / "tests").rglob("*.py"))
    print("test files:", ", ".join(files))
    print("ruff check:", run([PY, "-m", "ruff", "check", "tests"], project).stdout.strip().splitlines()[-1])
    print("ruff format:", run([PY, "-m", "ruff", "format", "--check", "tests"], project).stdout.strip().splitlines()[-1])
    mypy = run([PY, "-m", "mypy", "tests"], project).stdout.strip().splitlines()
    print("mypy:", mypy[-1], *(f"\n    {line}" for line in mypy[:-1][:4]))
    cov = run([PY, "scripts/spec_coverage.py", "M1"], project)
    print("spec_coverage M1:", " / ".join(cov.stdout.strip().splitlines()[-2:]), f"(exit {cov.returncode})")
    before = run([PY, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--tb=line", "-rN"], project)
    print("before code:", summary(before.stdout))
    reasons = sorted(set(re.findall(r"(ModuleNotFoundError[^\n]*|AssertionError|ImportError[^\n]*|SyntaxError|NameError|fixture '[^']+' not found)", before.stdout)))
    print("   failure kinds:", reasons[:5])
    collected = run([PY, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider"], project)
    print("cases collected:", summary(collected.stdout))
    reference = trial / f"ref-{name}"
    shutil.rmtree(reference, ignore_errors=True)
    shutil.copytree(trial / "reference", reference, ignore=shutil.ignore_patterns("tests"))
    shutil.copytree(tests, reference / "tests")
    ref = run([PY, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--tb=short"], reference)
    print("on correct code:", summary(ref.stdout))
    if ref.returncode:
        bad = [line for line in ref.stdout.splitlines() if line.startswith(("FAILED", "E "))]
        print("\n".join("    " + line for line in bad[:12]))
    caught = 0
    for label, (rel, old, new) in MUTANTS.items():
        mutant = trial / f"mut-{name}"
        shutil.rmtree(mutant, ignore_errors=True)
        shutil.copytree(reference, mutant)
        path = mutant / rel
        text = path.read_text(encoding="utf-8")
        assert old in text, label
        path.write_text(text.replace(old, new), encoding="utf-8")
        result = run([PY, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-x"], mutant)
        caught += result.returncode != 0
        print(f"   {'CAUGHT' if result.returncode else 'MISSED'}  {label}")
    print(f"seeded bugs caught: {caught} of {len(MUTANTS)}")


if __name__ == "__main__":
    main()
