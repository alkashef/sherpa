"""Cut a release at a finished milestone: an archive, a tag and a row in docs/releases.md.

The human starts it. It uses no AI session. `M<n>` is the last milestone of the release.

It stops when git is not clean, or when HEAD reaches no commit whose message starts with `M<n>: `
(a commit `M<n>: blocked` does not count). The newest such commit is the cut commit. Then:

1. It builds dist/<project>-<version>.zip with `git archive` from the cut commit. So the release
   holds the exact files that passed the checks. <project> is the name of the root folder.
2. It adds the annotated tag v<version> to the cut commit.
3. It adds a row to docs/releases.md: version, date, last milestone, milestones with titles.
4. It commits docs/releases.md with the message `Release <version>`.
5. It pushes the branch and the tag to origin.

The version is the date of the release, YYYY.MM.DD. When the tag v<version> exists, the version
gets `.2`, then `.3`. The milestones of the release are the milestone commits (`M<k>: <title>`)
after the last release tag, up to the cut commit. Each milestone counts one time, with the title of
its first commit. `blocked`, `review repairs` and `partial work` are not titles.

A step that fails stops the release. The script does not undo the steps before it.

Run:
    python scripts/release.py M<n> [--dry-run] [--date YYYY-MM-DD] [--root FOLDER]

`--dry-run` prints what it would do and changes nothing. `--date` gives the date of the release
(default: today).
"""

import argparse
import logging
import re
import shutil
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from pathlib import Path

logger = logging.getLogger("release")

ROOT = Path(__file__).resolve().parent.parent
RELEASES_PATH = Path("docs") / "releases.md"
RELEASES = RELEASES_PATH.as_posix()
DIST_DIR = "dist"
REMOTE = "origin"
SHORT_ID_LENGTH = 7

MILESTONE_ARGUMENT = re.compile(r"M(\d+)", re.IGNORECASE)
MILESTONE_COMMIT = re.compile(r"M(\d+): (.+)")
BLOCKED = "blocked"
# What follows `M<k>: ` in a commit that does not carry the title of the milestone.
NOT_TITLES = (BLOCKED, "review repairs", "partial work")
# A release tag for `git describe --match`: v, then YYYY.MM.DD, then `.2` or more, if any.
RELEASE_TAG_GLOB = "v[0-9][0-9][0-9][0-9].[0-9][0-9].[0-9][0-9]*"

EXIT_OK = 0
EXIT_STOPPED = 1


class ReleaseStoppedError(Exception):
    """The release must stop. main() logs the message and returns the exit code 1."""


@dataclass(frozen=True)
class Release:
    """Holds what one release is: its version, its cut commit and its milestones."""

    project: str
    version: str
    day: date
    milestone: int
    cut: str
    branch: str
    milestones: tuple[str, ...]

    @property
    def tag(self) -> str:
        """Return the name of the release tag: v<version>."""
        return f"v{self.version}"

    @property
    def short_cut(self) -> str:
        """Return the short ID of the cut commit."""
        return self.cut[:SHORT_ID_LENGTH]


def git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Run git in the project root and return its result. The caller checks the return code."""
    program = shutil.which("git") or "git"
    return subprocess.run(
        [program, *args],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def git_output(root: Path, *args: str) -> str:
    """Run git in the project root and return its output, without the space around it.

    Args:
        root: The project root.
        *args: The arguments of git.

    Returns:
        The standard output of git.

    Raises:
        ReleaseStoppedError: If git fails. The message names the command and gives git's answer.
    """
    done = git(root, *args)
    if done.returncode != 0:
        answer = (done.stderr or done.stdout).strip()
        raise ReleaseStoppedError(f"`git {' '.join(args)}` failed: {answer}")
    return done.stdout.strip()


def require_clean(root: Path) -> None:
    """Stop the release when git has a changed, staged or untracked file."""
    if git_output(root, "status", "--porcelain"):
        raise ReleaseStoppedError(
            "Git is not clean. Commit or remove the changes, then run the release again."
        )


def current_branch(root: Path) -> str:
    """Return the name of the branch that HEAD is on, and stop the release when it is on none."""
    done = git(root, "symbolic-ref", "--short", "-q", "HEAD")
    if done.returncode != 0:
        raise ReleaseStoppedError("HEAD is not on a branch. Check out the branch to release.")
    return done.stdout.strip()


def cut_commit(root: Path, milestone: int) -> str:
    """Return the ID of the cut commit: the newest commit of the milestone that HEAD can reach.

    Args:
        root: The project root.
        milestone: The number of the last milestone of the release.

    Returns:
        The full ID of the commit.

    Raises:
        ReleaseStoppedError: If no commit message starts with `M<n>: `, other than a blocked one.
    """
    start = f"M{milestone}: "
    for line in git_output(root, "log", "--format=%H %s", "HEAD").splitlines():
        commit, _, subject = line.partition(" ")
        if subject.startswith(start) and subject.strip() != start + BLOCKED:
            return commit
    raise ReleaseStoppedError(
        f"HEAD reaches no commit whose message starts with `{start}`. Finish M{milestone} first."
    )


def last_release_tag(root: Path) -> str | None:
    """Return the nearest release tag that HEAD can reach, or None when it reaches none."""
    done = git(root, "describe", "--tags", "--abbrev=0", "--match", RELEASE_TAG_GLOB, "HEAD")
    return done.stdout.strip() if done.returncode == 0 else None


def milestone_titles(subjects: list[str]) -> list[str]:
    """Return `M<k>: <title>` one time for each milestone of the commit messages, in their order.

    A milestone gets the title of its first commit. A blocked commit, review repairs and partial
    work carry no title.
    """
    titles: dict[int, str] = {}
    for subject in subjects:
        match = MILESTONE_COMMIT.fullmatch(subject.strip())
        if match is not None and match[2] not in NOT_TITLES:
            titles.setdefault(int(match[1]), match[0])
    return list(titles.values())


def new_milestones(root: Path, cut: str, milestone: int) -> list[str]:
    """Return the milestones of the release: those after the last release tag, up to the cut commit.

    Args:
        root: The project root.
        cut: The ID of the cut commit.
        milestone: The number of the last milestone of the release.

    Returns:
        One `M<k>: <title>` for each milestone, oldest first.

    Raises:
        ReleaseStoppedError: If the last release already holds each milestone up to the cut commit.
    """
    tag = last_release_tag(root)
    commits = cut if tag is None else f"{tag}..{cut}"
    subjects = git_output(root, "log", "--reverse", "--format=%s", commits).splitlines()
    titles = milestone_titles(subjects)
    if not titles:
        since = "the first commit" if tag is None else f"the tag {tag}"
        raise ReleaseStoppedError(
            f"Nothing to release. No milestone is new from {since} to the cut commit of "
            f"M{milestone}."
        )
    return titles


def next_version(day: date, tags: set[str]) -> str:
    """Return YYYY.MM.DD for the day, with `.2`, then `.3`, while the tag of the version exists."""
    base = day.strftime("%Y.%m.%d")
    version, count = base, 1
    while f"v{version}" in tags:
        count += 1
        version = f"{base}.{count}"
    return version


def table_end(lines: list[str]) -> int:
    """Return the index after the last table line, and stop the release when no line is one."""
    rows = [index for index, line in enumerate(lines) if line.lstrip().startswith("|")]
    if not rows:
        raise ReleaseStoppedError(f"{RELEASES} has no table. Put the table of the template back.")
    return rows[-1] + 1


def require_table(root: Path) -> None:
    """Stop the release when docs/releases.md is missing or holds no table."""
    path = root / RELEASES_PATH
    if not path.is_file():
        raise ReleaseStoppedError(f"{RELEASES} is missing in {root}.")
    table_end(path.read_text(encoding="utf-8").splitlines())


def plan_release(root: Path, milestone: int, day: date) -> Release:
    """Check that the release can start, and return what it holds. It only reads.

    Args:
        root: The project root.
        milestone: The number of the last milestone of the release.
        day: The date of the release.

    Returns:
        The release, with its version, its cut commit and its milestones.
    """
    require_clean(root)
    cut = cut_commit(root, milestone)
    branch = current_branch(root)
    require_table(root)
    milestones = new_milestones(root, cut, milestone)
    tags = set(git_output(root, "tag", "--list").splitlines())
    version = next_version(day, tags)
    return Release(root.name, version, day, milestone, cut, branch, tuple(milestones))


def archive_path(release: Release) -> Path:
    """Return the path of the archive, from the project root: dist/<project>-<version>.zip."""
    return Path(DIST_DIR) / f"{release.project}-{release.version}.zip"


def build_archive(root: Path, release: Release) -> None:
    """Build the archive from the files of the cut commit, with `git archive`."""
    path = archive_path(release)
    (root / path.parent).mkdir(exist_ok=True)
    git_output(root, "archive", "--format=zip", f"--output={path.as_posix()}", release.cut)


def add_tag(root: Path, release: Release) -> None:
    """Add the annotated tag v<version> to the cut commit."""
    message = f"--message=Release {release.version}"
    git_output(root, "tag", "--annotate", message, release.tag, release.cut)


def table_row(release: Release) -> str:
    """Return the row of the release: version, date, last milestone, milestones with titles."""
    milestones = "<br>".join(release.milestones).replace("|", "\\|")
    cells = [release.version, release.day.isoformat(), f"M{release.milestone}", milestones]
    return f"| {' | '.join(cells)} |"


def add_row(root: Path, release: Release) -> None:
    """Add the row of the release after the last row of the table in docs/releases.md."""
    path = root / RELEASES_PATH
    lines = path.read_text(encoding="utf-8").splitlines()
    lines.insert(table_end(lines), table_row(release))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def commit_row(root: Path, release: Release) -> None:
    """Commit docs/releases.md alone, with the message `Release <version>`."""
    git_output(root, "add", "--", RELEASES)
    git_output(root, "commit", f"--message=Release {release.version}")


def push(root: Path, release: Release) -> None:
    """Push the branch and the tag to origin.

    Args:
        root: The project root.
        release: The release, with its branch and its tag.

    Raises:
        ReleaseStoppedError: If the push fails. The tag and the commit stay on this machine.
    """
    done = git(root, "push", REMOTE, release.branch, release.tag)
    if done.returncode != 0:
        answer = (done.stderr or done.stdout).strip()
        raise ReleaseStoppedError(
            f"The push failed: {answer}\n"
            f"The tag {release.tag} and the commit `Release {release.version}` stay on this "
            f"machine. Run `git push {REMOTE} {release.branch} {release.tag}` to finish the "
            "release."
        )


def release_steps(release: Release) -> list[tuple[str, Callable[[Path, Release], None]]]:
    """Return the steps of the release in their order: what each step does, and its function."""
    archive = archive_path(release).as_posix()
    message = f"`Release {release.version}`"
    return [
        (f"build {archive} from commit {release.short_cut}", build_archive),
        (f"add the tag {release.tag} to commit {release.short_cut}", add_tag),
        (f"add a row to {RELEASES}", add_row),
        (f"commit {RELEASES} with the message {message}", commit_row),
        (f"push the branch {release.branch} and the tag {release.tag} to {REMOTE}", push),
    ]


def log_release(release: Release) -> None:
    """Log the version, the last milestone, the cut commit and each milestone of the release."""
    logger.info(
        "Release %s. Last milestone: M%d. Cut commit: %s.",
        release.version,
        release.milestone,
        release.short_cut,
    )
    for milestone in release.milestones:
        logger.info("  %s", milestone)


def run_release(root: Path, release: Release, dry_run: bool) -> None:
    """Do each step of the release and log it, or only log what each step would do.

    Args:
        root: The project root.
        release: The release to cut.
        dry_run: True to change nothing.
    """
    log_release(release)
    for text, step in release_steps(release):
        if dry_run:
            logger.info("Would %s.", text)
        else:
            step(root, release)
            logger.info("Done: %s.", text)
    if dry_run:
        logger.info("Dry run: nothing changed.")
    else:
        logger.info("Archive: %s", root / archive_path(release))


def report_stop(stop: ReleaseStoppedError) -> int:
    """Log why the release stopped, and return the exit code of a stopped release."""
    logger.error("%s", stop)
    return EXIT_STOPPED


def milestone_number(text: str) -> int:
    """Return the number of a milestone argument such as M3. argparse refuses any other text."""
    match = MILESTONE_ARGUMENT.fullmatch(text)
    if match is None:
        raise argparse.ArgumentTypeError(f"'{text}' is not a milestone. Give M<n>, such as M3.")
    return int(match[1])


def release_date(text: str) -> date:
    """Return the date of a YYYY-MM-DD argument. argparse refuses any other text."""
    try:
        return date.fromisoformat(text)
    except ValueError as err:
        raise argparse.ArgumentTypeError(f"'{text}' is not a date. Give YYYY-MM-DD.") from err


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    """Read the command line: the last milestone (M<n>), and the options."""
    parser = argparse.ArgumentParser(
        description="Cut a release at a finished milestone: an archive, a tag and a row."
    )
    parser.add_argument(
        "milestone", type=milestone_number, help="the last milestone of the release, such as M3"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="print what it would do, and change nothing"
    )
    parser.add_argument(
        "--date", type=release_date, help="the date of the release, YYYY-MM-DD (default: today)"
    )
    parser.add_argument(
        "--root", type=Path, default=ROOT, help="the project folder (default: above scripts/)"
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Cut the release, or only print its steps with --dry-run. Return the exit code.

    Args:
        argv: The command-line arguments. None means sys.argv.

    Returns:
        0 when the release is done, 1 when it stopped. argparse exits with 2 for a bad argument.
    """
    arguments = parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)
    root = arguments.root.resolve()
    day = arguments.date or date.today()
    try:
        release = plan_release(root, arguments.milestone, day)
        run_release(root, release, arguments.dry_run)
    except ReleaseStoppedError as stop:
        return report_stop(stop)
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
