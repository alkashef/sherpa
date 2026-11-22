"""scripts/dashboard.py, as a new project gets it: the page and what it reads from each owner."""

import html
import http.client
import re
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest
from helpers import Sandbox, run

SPEC_ROWS = (
    "| PAY-001 | When the user pays, the system shall record it. | Must | Confirmed | x | y | |\n"
    "| PAY-002 | The system shall refuse a payment over the limit. | Must | Confirmed | x | y |\n"
    "| EX-001 | PAY-001 | A payment of 10 | It is recorded | Awaiting review |\n"
)
DECISIONS = "| DEC-002 | Proposed | Store payments in SQLite | PAY-001 needs a store |\n"
TEST_DESIGN = "| PAY-001, PAY-002 | unit | pytest | a database file in a temporary folder |\n"
BOUNDARIES = "| `src/pay.py` | none |\n| `src/clock.py` | none |\n"
PLAN_ROWS = (
    "| **M1** Pay | Records a payment | sonnet | low | no | blocked |\n"
    "| **M2** Limit | Refuses a payment over the limit | sonnet | low | no | open |\n"
)
PLAN_BLOCKS = """
### M1 — Pay

- **Refs:** PAY-001, DEC-002.
- **Owner:** `src/pay.py`.
- **Blocked:** Needs a decision: which database for DEC-002?

### M2 — Limit

- **Refs:** PAY-002.
"""
PAY_CODE = (
    '"""Records payments (PAY-001)."""\n\nfrom src.clock import now\n\n\n'
    'class Payments:\n    """Keeps the payments of one user.\n\n    More text.\n    """\n'
)
TEST_CODE = "def test_pay_001_records_a_payment() -> None:\n    assert True\n"
LOG = "Done.\nDECISION: keep the payments in a list | the simplest way | none\n"
BARE_ID = re.compile(r"\b(?:[A-Z][A-Z0-9]*-\d{3,}|M\d+)\b")
KIND_BEFORE = re.compile(
    r"(?:requirement|design decision|acceptance example|scenario|milestone|Milestones)\s+$"
)


def insert_after(path: Path, marker: str, text: str) -> None:
    """Insert text after the first line of a file that starts with the marker (a table header)."""
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    index = next(i for i, line in enumerate(lines) if line.startswith(marker))
    lines.insert(index + 2, text)  # after the header and the line under it
    path.write_text("".join(lines), encoding="utf-8")


@pytest.fixture
def project(sandbox: Sandbox) -> Sandbox:
    """A project with a spec, a design, a plan, a test, code, a log and a finished milestone."""
    result = sandbox.init("--with", "python", "--no-github", "--no-conda")
    assert result.returncode == 0, result.stderr
    write_docs(sandbox.folder / "docs")
    (sandbox.folder / "src" / "pay.py").write_text(PAY_CODE, encoding="utf-8")
    (sandbox.folder / "src" / "clock.py").write_text('"""Clock."""\n', encoding="utf-8")
    (sandbox.folder / "tests" / "unit" / "test_pay.py").write_text(TEST_CODE, encoding="utf-8")
    sandbox.git("add", "-A")
    sandbox.git("commit", "--no-verify", "-m", "Spec, design and plan")
    finish_m2(sandbox)
    logs = sandbox.folder / ".claude" / "logs"
    logs.mkdir(parents=True)
    (logs / "M1.log").write_text(LOG, encoding="utf-8")
    return sandbox


def write_docs(docs: Path) -> None:
    """Fill the spec, the design and the plan of a new project with the rows of these tests."""
    insert_after(docs / "spec.md", "| ID | EARS requirement |", SPEC_ROWS)
    insert_after(docs / "design.md", "| ID | Status |", DECISIONS)
    insert_after(docs / "design.md", "| Requirement | Level |", TEST_DESIGN)
    insert_after(docs / "design.md", "| Module | May import |", BOUNDARIES)
    plan = docs / "plan.md"
    text = plan.read_text(encoding="utf-8").replace("None planned.\n", PLAN_BLOCKS.lstrip("\n"))
    plan.write_text(text, encoding="utf-8")
    insert_after(plan, "| Milestone | Description |", PLAN_ROWS)


def finish_m2(sandbox: Sandbox) -> None:
    """Do what the build session of M2 does: delete its row and block, and commit `M2: Limit`."""
    plan = sandbox.folder / "docs" / "plan.md"
    text = plan.read_text(encoding="utf-8")
    text = text.replace(PLAN_ROWS.splitlines()[1] + "\n", "")
    text = text[: text.index("### M2 — Limit")].rstrip("\n") + "\n"
    plan.write_text(text, encoding="utf-8")
    sandbox.git("commit", "--no-verify", "-am", "M2: Limit")


def page_text(project: Sandbox) -> str:
    """Run the dashboard with --out, and return the visible text of the page, on one line."""
    out = project.folder.parent / "page.html"
    done = run([sys.executable, "scripts/dashboard.py", "--out", str(out)], project.folder)
    assert done.returncode == 0, done.stderr
    visible = re.sub(r"<style>.*?</style>|<[^>]+>", " ", out.read_text("utf-8"), flags=re.DOTALL)
    return " ".join(html.unescape(visible).split())


def test_the_page_shows_what_needs_you(project: Sandbox) -> None:
    text = page_text(project)
    assert "The spec (spec.md) is a draft" in text
    assert "design decision DEC-002 in design.md is Proposed" in text
    assert "milestone M1 in plan.md is blocked: Needs a decision: which database for design" in text
    assert "Decision of M1.log: keep the payments in a list" in text
    assert "requirement PAY-002 in spec.md has no test." in text


def test_the_trace_follows_each_requirement(project: Sandbox) -> None:
    text = page_text(project)
    # PAY-001: tested, cited by a decision, planned in M1, a test, and the module that cites it.
    assert "requirement PAY-001 in spec.md tested design decision DEC-002 in design.md" in text
    assert "milestone M1 in plan.md test_pay_001_records_a_payment src/pay.py" in text
    # PAY-002: its milestone left the plan; the commit `M2: Limit` deleted its block.
    assert "requirement PAY-002 in spec.md missing" in text
    assert "milestone M2 in plan.md" in text


def test_the_code_map_shows_files_imports_and_classes(project: Sandbox) -> None:
    text = page_text(project)
    assert "pay.py 10" in text
    assert "src.pay src.clock no: the table does not permit it" in text
    assert "Payments src/pay.py Keeps the payments of one user." in text


def test_the_page_never_shows_a_bare_id(project: Sandbox) -> None:
    text = page_text(project)
    named = (KIND_BEFORE.search(text[: match.start()]) for match in BARE_ID.finditer(text))
    log_names = (text[match.end() :].startswith(".log") for match in BARE_ID.finditer(text))
    bare = [
        m[0]
        for m, ok, log in zip(BARE_ID.finditer(text), named, log_names, strict=True)
        if not ok and not log
    ]
    assert bare == []


def free_port() -> int:
    """Return a TCP port on 127.0.0.1 that nothing listens on now."""
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port: int = probe.getsockname()[1]
        return port


def fetch(port: int) -> str:
    """Return the page that the dashboard serves, after the server is up (at most 20 seconds)."""
    deadline = time.monotonic() + 20
    while True:
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        try:
            connection.request("GET", "/")
            return connection.getresponse().read().decode("utf-8")
        except OSError:
            if time.monotonic() > deadline:
                raise
            time.sleep(0.2)
        finally:
            connection.close()


def test_the_served_page_reads_the_files_again_on_refresh(project: Sandbox) -> None:
    port = free_port()
    command = [sys.executable, "scripts/dashboard.py", "--port", str(port), "--no-browser"]
    server = subprocess.Popen(command, cwd=project.folder)
    try:
        first = fetch(port)
        assert "Refresh</button>" in first
        assert "is Proposed" in first
        design = project.folder / "docs" / "design.md"
        design.write_text(design.read_text("utf-8").replace("Proposed", "Decided"), "utf-8")
        assert "is Proposed" not in fetch(port)
    finally:
        server.terminate()
        server.wait(timeout=20)
    # The dashboard writes nothing in the project.
    assert project.git("status", "--porcelain") == "M docs/design.md"
