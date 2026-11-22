"""scripts/release.py, as a new project gets it: an archive, a tag and a row for each release.

Each test makes a small git project with a bare remote in a temporary folder and runs the script
on it with --root. The date comes from --date, so the version does not depend on the day of the
run.
"""

import sys
import zipfile
from datetime import date

import build_instance as bi
import pytest
from helpers import Sandbox, git_path, run

SCRIPT = bi.assets_dir() / "scripts" / "release.py"
TEMPLATE = bi.assets_dir() / "docs" / "releases.md"
DAY = "2026-11-20"
VERSION = "2026.11.20"
TAG = f"v{VERSION}"
HEADER = "| Version | Date | Last milestone | Milestones |"


@pytest.fixture
def project(sandbox: Sandbox) -> Sandbox:
    """A git project with the releases template, one commit, and `main` pushed to `origin`."""
    docs = sandbox.folder / "docs"
    docs.mkdir()
    (docs / "releases.md").write_bytes(TEMPLATE.read_bytes())
    (sandbox.folder / ".gitignore").write_text("dist/\n", encoding="utf-8")
    sandbox.git("init", "-b", "main")
    sandbox.git("remote", "add", "origin", str(sandbox.remote))
    sandbox.git("add", ".")
    sandbox.git("commit", "-m", "Add the project files")
    sandbox.git("push", "-u", "origin", "main")
    return sandbox


def commit(project: Sandbox, message: str, file: str) -> str:
    """Commit one new file under src/ with the message, and return the ID of the commit."""
    path = project.folder / "src" / file
    path.parent.mkdir(exist_ok=True)
    path.write_text(f"{message}\n", encoding="utf-8")
    project.git("add", ".")
    project.git("commit", "-m", message)
    return project.git("rev-parse", "HEAD")


def release(project: Sandbox, *args: str, day: str | None = DAY) -> tuple[int, list[str]]:
    """Run the script on the project and return its exit code and its output lines.

    It runs from the folder above the project, which is not a git repository. So a fault in
    --root cannot reach another repository.
    """
    command = [sys.executable, str(SCRIPT), *args, "--root", str(project.folder)]
    if day is not None:
        command += ["--date", day]
    result = run(command, project.folder.parent, project.env)
    return result.returncode, (result.stdout + result.stderr).splitlines()


def rows(project: Sandbox) -> list[list[str]]:
    """Return the cells of each release row of docs/releases.md."""
    text = (project.folder / "docs" / "releases.md").read_text(encoding="utf-8")
    table = [line for line in text.splitlines() if line.startswith("|")]
    return [[cell.strip() for cell in line.strip("|").split("|")] for line in table[2:]]


def archive_files(project: Sandbox, version: str = VERSION) -> set[str]:
    """Return the files of the archive of a version, without its folder entries."""
    with zipfile.ZipFile(project.folder / "dist" / f"demo-{version}.zip") as archive:
        return {name for name in archive.namelist() if not name.endswith("/")}


def commit_of(project: Sandbox, name: str) -> str:
    """Return the ID of the commit that a tag or a branch points to."""
    return project.git("rev-parse", f"{name}^{{commit}}")


def remote_commit_of(project: Sandbox, name: str) -> str:
    """Return the ID of the commit that a tag or a branch of the remote points to, or ''."""
    command = [git_path(), "--git-dir", str(project.remote), "rev-parse", f"{name}^{{commit}}"]
    result = run(command, env=project.env)
    return result.stdout.strip() if result.returncode == 0 else ""


def state(project: Sandbox) -> tuple[dict[str, bytes], str, str, str]:
    """Return what a release changes: the files, HEAD, the tags, and `main` of the remote."""
    paths = (p for p in project.folder.rglob("*") if p.is_file() and ".git" not in p.parts)
    files = {p.relative_to(project.folder).as_posix(): p.read_bytes() for p in paths}
    head = project.git("rev-parse", "HEAD")
    return files, head, project.git("tag", "--list"), project.remote_head()


def test_a_release_builds_the_archive_tags_the_cut_commit_and_pushes(project: Sandbox) -> None:
    commit(project, "M1: Pay", "pay.txt")
    cut = commit(project, "M2: Refund", "refund.txt")
    code, lines = release(project, "M2")
    assert code == 0, lines
    assert archive_files(project) == {
        ".gitignore",
        "docs/releases.md",
        "src/pay.txt",
        "src/refund.txt",
        "versions/pip-freeze.txt",
    }
    assert project.git("cat-file", "-t", TAG) == "tag"
    assert commit_of(project, TAG) == cut
    assert rows(project) == [[VERSION, DAY, "M2", "M1: Pay<br>M2: Refund"]]
    assert project.git("log", "-1", "--format=%s") == f"Release {VERSION}"
    assert project.git("diff", "--name-only", "HEAD~1", "HEAD") == "docs/releases.md"
    assert project.git("rev-parse", "HEAD~1") == cut
    assert project.git("status", "--porcelain") == ""
    assert project.remote_head() == project.git("rev-parse", "HEAD")
    assert remote_commit_of(project, TAG) == cut


def test_the_archive_holds_the_installed_versions(project: Sandbox) -> None:
    commit(project, "M1: Pay", "pay.txt")
    code, lines = release(project, "M1")
    assert code == 0, lines
    with zipfile.ZipFile(project.folder / "dist" / f"demo-{VERSION}.zip") as archive:
        assert "pytest==" in archive.read("versions/pip-freeze.txt").decode("utf-8")


def test_it_prints_each_step_and_the_path_of_the_archive(project: Sandbox) -> None:
    cut = commit(project, "M1: Pay", "pay.txt")
    code, lines = release(project, "m1")
    assert code == 0
    assert lines == [
        f"Release {VERSION}. Last milestone: M1. Cut commit: {cut[:7]}.",
        "  M1: Pay",
        f"Done: build dist/demo-{VERSION}.zip from commit {cut[:7]}.",
        f"Done: add the tag {TAG} to commit {cut[:7]}.",
        "Done: add a row to docs/releases.md.",
        f"Done: commit docs/releases.md with the message `Release {VERSION}`.",
        f"Done: push the branch main and the tag {TAG} to origin.",
        f"Archive: {project.folder.resolve() / 'dist' / f'demo-{VERSION}.zip'}",
    ]


def test_the_release_holds_the_files_of_the_cut_commit_and_not_of_head(project: Sandbox) -> None:
    commit(project, "M1: Pay", "pay.txt")
    cut = commit(project, "M2: Refund", "refund.txt")
    commit(project, "M3: Report", "report.txt")
    code, lines = release(project, "M2")
    assert code == 0, lines
    assert "src/report.txt" not in archive_files(project)
    assert commit_of(project, TAG) == cut
    assert rows(project) == [[VERSION, DAY, "M2", "M1: Pay<br>M2: Refund"]]
    with zipfile.ZipFile(project.folder / "dist" / f"demo-{VERSION}.zip") as archive:
        assert archive.read("docs/releases.md") == TEMPLATE.read_bytes()


def test_a_second_release_on_the_same_day_gets_2_then_3(project: Sandbox) -> None:
    commit(project, "M1: Pay", "pay.txt")
    assert release(project, "M1")[0] == 0
    second = commit(project, "M2: Refund", "refund.txt")
    assert release(project, "M2")[0] == 0
    third = commit(project, "M3: Report", "report.txt")
    code, lines = release(project, "M3")
    assert code == 0, lines
    assert commit_of(project, f"{TAG}.2") == second
    assert commit_of(project, f"{TAG}.3") == third
    assert archive_files(project, f"{VERSION}.3") >= {"src/pay.txt", "src/report.txt"}
    assert [row[0] for row in rows(project)] == [VERSION, f"{VERSION}.2", f"{VERSION}.3"]


def test_a_release_holds_only_the_milestones_after_the_last_release_tag(project: Sandbox) -> None:
    commit(project, "M1: Pay", "pay.txt")
    commit(project, "M2: Refund", "refund.txt")
    assert release(project, "M1")[0] == 0
    commit(project, "M3: Report", "report.txt")
    code, lines = release(project, "M3", day="2026-12-01")
    assert code == 0, lines
    assert rows(project) == [
        [VERSION, DAY, "M1", "M1: Pay"],
        ["2026.12.01", "2026-12-01", "M3", "M2: Refund<br>M3: Report"],
    ]


def test_each_milestone_counts_one_time_with_the_title_of_its_first_commit(
    project: Sandbox,
) -> None:
    commit(project, "M1: Pay", "pay.txt")
    commit(project, "M2: blocked", "plan.txt")
    commit(project, "M2: partial work", "part.txt")
    commit(project, "M2: Refund", "refund.txt")
    commit(project, "M2: review repairs", "repairs.txt")
    commit(project, "M1: Pay again", "again.txt")
    commit(project, "Update the README", "readme.txt")
    cut = commit(project, "M3: Report", "report.txt")
    code, lines = release(project, "M3")
    assert code == 0, lines
    assert rows(project) == [[VERSION, DAY, "M3", "M1: Pay<br>M2: Refund<br>M3: Report"]]
    assert commit_of(project, TAG) == cut


def test_the_cut_commit_is_the_newest_commit_of_the_milestone(project: Sandbox) -> None:
    commit(project, "M1: Pay", "pay.txt")
    repairs = commit(project, "M1: review repairs", "repairs.txt")
    commit(project, "M2: Refund", "refund.txt")
    code, lines = release(project, "M1")
    assert code == 0, lines
    assert commit_of(project, TAG) == repairs
    assert rows(project) == [[VERSION, DAY, "M1", "M1: Pay"]]
    assert "src/repairs.txt" in archive_files(project)


def test_a_bar_in_a_title_does_not_break_the_table(project: Sandbox) -> None:
    commit(project, "M1: Pay | refund", "pay.txt")
    assert release(project, "M1")[0] == 0
    text = (project.folder / "docs" / "releases.md").read_text(encoding="utf-8")
    assert text.splitlines()[-1] == f"| {VERSION} | {DAY} | M1 | M1: Pay \\| refund |"


def test_dry_run_prints_the_steps_and_changes_nothing(project: Sandbox) -> None:
    cut = commit(project, "M1: Pay", "pay.txt")
    before = state(project)
    code, lines = release(project, "M1", "--dry-run")
    assert code == 0
    assert lines == [
        f"Release {VERSION}. Last milestone: M1. Cut commit: {cut[:7]}.",
        "  M1: Pay",
        f"Would build dist/demo-{VERSION}.zip from commit {cut[:7]}.",
        f"Would add the tag {TAG} to commit {cut[:7]}.",
        "Would add a row to docs/releases.md.",
        f"Would commit docs/releases.md with the message `Release {VERSION}`.",
        f"Would push the branch main and the tag {TAG} to origin.",
        "Dry run: nothing changed.",
    ]
    assert state(project) == before
    assert not (project.folder / "dist").exists()


def test_the_version_is_the_date_of_today_without_a_date(project: Sandbox) -> None:
    commit(project, "M1: Pay", "pay.txt")
    # The day can change during the run: accept the day before it and the day after it.
    days = {date.today()}
    code, lines = release(project, "M1", "--dry-run", day=None)
    days.add(date.today())
    assert code == 0
    assert lines[0].split(". ")[0] in {f"Release {day:%Y.%m.%d}" for day in days}


def test_a_dirty_tree_stops_the_release(project: Sandbox) -> None:
    commit(project, "M1: Pay", "pay.txt")
    (project.folder / "notes.txt").write_text("not committed\n", encoding="utf-8")
    before = state(project)
    code, lines = release(project, "M1")
    assert code == 1
    assert lines == ["Git is not clean. Commit or remove the changes, then run the release again."]
    assert state(project) == before
    assert not (project.folder / "dist").exists()


def test_a_milestone_without_a_commit_stops_the_release(project: Sandbox) -> None:
    commit(project, "M10: Ten", "ten.txt")
    commit(project, "M1: blocked", "plan.txt")
    commit(project, "Note M1: later", "note.txt")
    before = state(project)
    code, lines = release(project, "M1")
    assert code == 1
    assert lines == ["HEAD reaches no commit whose message starts with `M1: `. Finish M1 first."]
    assert state(project) == before


def test_a_milestone_that_a_release_already_holds_stops_the_release(project: Sandbox) -> None:
    commit(project, "M1: Pay", "pay.txt")
    commit(project, "M2: Refund", "refund.txt")
    assert release(project, "M2")[0] == 0
    before = state(project)
    code, lines = release(project, "M1")
    assert code == 1
    assert lines == [
        f"Nothing to release. No milestone is new from the tag {TAG} to the cut commit of M1."
    ]
    assert state(project) == before


def test_a_head_that_is_on_no_branch_stops_the_release(project: Sandbox) -> None:
    cut = commit(project, "M1: Pay", "pay.txt")
    project.git("checkout", "--detach", cut)
    code, lines = release(project, "M1")
    assert code == 1
    assert lines == ["HEAD is not on a branch. Check out the branch to release."]
    assert project.git("tag", "--list") == ""


def test_a_missing_releases_file_or_table_stops_the_release(project: Sandbox) -> None:
    commit(project, "M1: Pay", "pay.txt")
    (project.folder / "docs" / "releases.md").write_text("# Releases\n", encoding="utf-8")
    project.git("commit", "-am", "Remove the table")
    code, lines = release(project, "M1")
    assert code == 1
    assert lines == ["docs/releases.md has no table. Put the table of the template back."]
    project.git("rm", "docs/releases.md")
    project.git("commit", "-m", "Remove the releases file")
    code, lines = release(project, "M1")
    assert code == 1
    assert lines == [f"docs/releases.md is missing in {project.folder.resolve()}."]
    assert project.git("tag", "--list") == ""
    assert not (project.folder / "dist").exists()


def test_a_failed_push_is_reported_and_keeps_the_tag_and_the_commit(project: Sandbox) -> None:
    cut = commit(project, "M1: Pay", "pay.txt")
    project.git("remote", "set-url", "origin", str(project.folder.parent / "no-remote.git"))
    code, lines = release(project, "M1")
    assert code == 1
    failed = next(index for index, line in enumerate(lines) if line.startswith("The push failed: "))
    assert lines[failed - 1] == (
        f"Done: commit docs/releases.md with the message `Release {VERSION}`."
    )
    assert lines[-1] == (
        f"The tag {TAG} and the commit `Release {VERSION}` stay on this machine. "
        f"Run `git push origin main {TAG}` to finish the release."
    )
    assert commit_of(project, TAG) == cut
    assert project.git("log", "-1", "--format=%s") == f"Release {VERSION}"
    assert (project.folder / "dist" / f"demo-{VERSION}.zip").is_file()
    assert project.remote_head() != project.git("rev-parse", "HEAD")


@pytest.mark.parametrize(
    ("args", "message"),
    [
        (["3"], "'3' is not a milestone. Give M<n>, such as M3."),
        (["M1", "--date", "tomorrow"], "'tomorrow' is not a date. Give YYYY-MM-DD."),
        ([], "the following arguments are required: milestone"),
    ],
)
def test_a_bad_argument_is_a_usage_error(project: Sandbox, args: list[str], message: str) -> None:
    code, lines = release(project, *args, day=None)
    assert code == 2
    assert lines[-1].endswith(message)
    assert project.git("tag", "--list") == ""


def test_the_template_is_a_heading_two_lines_and_an_empty_table() -> None:
    lines = TEMPLATE.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "# Releases"
    assert lines[-2:] == [HEADER, "| --- | --- | --- | --- |"]
    assert len([line for line in lines[1:-2] if line.strip()]) == 2
