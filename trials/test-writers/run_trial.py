"""Run the second trial of the test writers, through the runner of a real sherpa project.

Usage: python run_trial.py <work folder> [--writers claude codex antigravity] [--runs 3]
           [--kits slug ledger] [--results results-2] [--rescore]

For each kit, each writer and each run, it builds a project with sherpa's builder (named `sherpa`,
so that the runner accepts this conda environment), puts in the docs of the kit, commits, and
runs `python scripts/milestones-runner.py --tests-only M1` with that writer. Then it scores the
tests with evaluate.py. The writers run in parallel, one thread each; the runs of one writer run
one after another. It keeps the tests, the runner's output, the logs and the score of each run
under the results folder, and writes summary.md by the rule of the second trial (docs/
unapproved-ideas.md of sherpa): a writer qualifies only when all gates pass in all its runs; of
those, the highest median of seeded bugs caught wins, and on a tie the faster one. --rescore
scores the kept runs again, for a kit whose correct implementation changed.
"""

import argparse
import json
import os
import shutil
import statistics
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
SHERPA = HERE.parent.parent
BUILDER = SHERPA / "skills" / "project-init" / "scripts" / "build_instance.py"
PY = sys.executable
MODELS = {  # the same model and effort as in the first trial
    "claude": ("claude-opus-5-5", "high"),
    "codex": ("gpt-6.2-astra", "high"),
    "antigravity": ("gemini-4-neon-high", "high"),
    "copilot": ("gpt-6.2-astra", "high"),
}
IDENTITY = ["-c", "user.name=Trial", "-c", "user.email=trial@example.com"]


def run(command: list[str], cwd: Path, timeout: float | None = None) -> subprocess.CompletedProcess[str]:
    """Run a command and capture its output."""
    return subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        env={**os.environ, "NO_COLOR": "1"},
    )


def make_project(folder: Path, kit: str, writer: str) -> None:
    """Build a project with the docs of the kit and the writer, commit it, and turn the hook on."""
    shutil.rmtree(folder.parent, ignore_errors=True)
    folder.parent.mkdir(parents=True)
    built = run([PY, str(BUILDER), str(folder), "--with", "python", "cli", "data", "--name", "sherpa"], SHERPA)
    assert built.returncode == 0, built.stderr
    for name in ("spec.md", "design.md", "plan.md"):
        shutil.copyfile(HERE / "kits" / kit / "docs" / name, folder / "docs" / name)
    model, effort = MODELS[writer]
    config = {"writer": writer, "model": model, "effort": effort}
    (folder / "config" / "test-writer.json").write_text(json.dumps(config) + "\n", encoding="utf-8")
    for command in (
        ["git", "init", "-q", "-b", "main"],
        ["git", "add", "-A"],
        ["git", *IDENTITY, "commit", "-q", "--no-verify", "-m", f"Trial kit {kit}"],
        ["git", "config", "core.hooksPath", ".githooks"],
    ):
        done = run(command, folder)
        assert done.returncode == 0, done.stderr


def one_run(work: Path, results: Path, kit: str, writer: str, number: int) -> dict[str, object]:
    """Run the test session of one writer on one kit, score it, and keep what it left."""
    folder = work / f"{kit}-{writer}-{number}" / "project"
    make_project(folder, kit, writer)
    start = time.monotonic()
    runner = [PY, "scripts/milestones-runner.py", "--tests-only", "M1", "--timeout-minutes", "30"]
    done = run(runner, folder, timeout=3 * 3600)
    seconds = round(time.monotonic() - start)
    keep = results / kit / writer / f"run{number}"
    shutil.rmtree(keep, ignore_errors=True)
    keep.mkdir(parents=True)
    (keep / "runner.txt").write_text(done.stdout + done.stderr, encoding="utf-8")
    shutil.copytree(folder / "tests", keep / "tests", ignore=shutil.ignore_patterns("__pycache__"))
    if (folder / ".claude" / "logs").is_dir():
        shutil.copytree(folder / ".claude" / "logs", keep / "logs")
    score = run([PY, str(HERE / "evaluate.py"), str(HERE / "kits" / kit), str(folder), "--json", str(keep / "score.json")], HERE)
    (keep / "score.txt").write_text(score.stdout + score.stderr, encoding="utf-8")
    summary = json.loads((keep / "score.json").read_text(encoding="utf-8")) if (keep / "score.json").is_file() else {"all_gates": False, "caught": 0, "total": 0, "gates": {}}
    summary.update({"kit": kit, "writer": writer, "run": number, "seconds": seconds, "runner_exit": done.returncode})
    (keep / "score.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"{kit} {writer} run {number}: exit {done.returncode}, {seconds} s, gates {summary['all_gates']}, caught {summary['caught']}/{summary['total']}", flush=True)
    return summary


def rescore(work: Path, results: Path, kit: str, writer: str, number: int) -> dict[str, object]:
    """Score a kept run again with the current kit: same project, same tests, same time."""
    folder = work / f"{kit}-{writer}-{number}" / "project"
    keep = results / kit / writer / f"run{number}"
    old = json.loads((keep / "score.json").read_text(encoding="utf-8"))
    score = run([PY, str(HERE / "evaluate.py"), str(HERE / "kits" / kit), str(folder), "--json", str(keep / "score.json")], HERE)
    (keep / "score.txt").write_text(score.stdout + score.stderr, encoding="utf-8")
    summary = json.loads((keep / "score.json").read_text(encoding="utf-8"))
    summary.update({key: old[key] for key in ("kit", "writer", "run", "seconds", "runner_exit")})
    (keep / "score.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"{kit} {writer} run {number}: rescored, gates {summary['all_gates']}, caught {summary['caught']}/{summary['total']}", flush=True)
    return summary


def writer_runs(work: Path, results: Path, writer: str, kits: list[str], runs: int) -> list[dict[str, object]]:
    """Run every kit and run of one writer, one after another."""
    return [one_run(work, results, kit, writer, n) for kit in kits for n in range(1, runs + 1)]


def summary_table(scores: list[dict[str, object]], writers: list[str]) -> str:
    """Return summary.md: each run, then each writer by the rule of the second trial."""
    lines = ["# The second trial of the test writers", "", "| Kit | Writer | Run | Seconds | All gates | Failed gates | Bugs caught |", "| --- | --- | --- | --- | --- | --- | --- |"]
    for s in scores:
        failed = ", ".join(name for name, ok in dict(s["gates"]).items() if not ok) or "-"  # type: ignore[call-overload]
        lines.append(f"| {s['kit']} | {s['writer']} | {s['run']} | {s['seconds']} | {s['all_gates']} | {failed} | {s['caught']} of {s['total']} |")
    lines += ["", "| Writer | Qualifies | Median bugs caught | Median seconds |", "| --- | --- | --- | --- |"]
    for writer in writers:
        own = [s for s in scores if s["writer"] == writer]
        qualifies = bool(own) and all(s["all_gates"] for s in own)
        caught = statistics.median(int(str(s["caught"])) for s in own) if own else 0
        seconds = statistics.median(int(str(s["seconds"])) for s in own) if own else 0
        lines.append(f"| {writer} | {'yes' if qualifies else 'no'} | {caught} | {seconds} |")
    return "\n".join(lines) + "\n"


def main() -> None:
    """Run the trial and write the summary."""
    parser = argparse.ArgumentParser(description="Run the second trial of the test writers.")
    parser.add_argument("work", type=Path)
    parser.add_argument("--writers", nargs="+", default=["claude", "codex", "antigravity"])
    parser.add_argument("--kits", nargs="+", default=["slug", "ledger"])
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--results", type=Path, default=HERE / "results-2")
    parser.add_argument("--rescore", action="store_true", help="score the kept runs again")
    args = parser.parse_args()
    args.results.mkdir(parents=True, exist_ok=True)
    if args.rescore:
        scores = [rescore(args.work, args.results, k, w, n) for k in args.kits for w in args.writers for n in range(1, args.runs + 1)]
    else:
        with ThreadPoolExecutor(max_workers=len(args.writers)) as pool:
            futures = [pool.submit(writer_runs, args.work, args.results, w, args.kits, args.runs) for w in args.writers]
            scores = [score for future in futures for score in future.result()]
    (args.results / "summary.md").write_text(summary_table(scores, args.writers), encoding="utf-8")
    print((args.results / "summary.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
