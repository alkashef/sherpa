"""Show the state of the project on one HTML page: what needs you, the plan, the trace, the code.

Standard library only. The script reads the files and git, and writes nothing (except the page
with --out). It holds no fact of its own: each fact comes from its owner.

- Needs you: a draft spec, each Proposed design decision and open design question, each blocked
  milestone with its question, the problems of `spec_coverage.py --consistency`, each requirement
  with no test, uncommitted docs, the `DECISION:` lines and the kept `FINDING:` lines of the
  runner logs in .claude/logs/, and the count of unapproved ideas.
- Plan and releases: the rows of docs/plan.md, the rows of docs/releases.md, and the last
  milestone commits of git.
- Trace: for each requirement of docs/spec.md, its state (from `spec_coverage.py`), the design
  rows that cite it, its milestone (the Refs of a block in the plan, or the block that a commit
  `M<n>: <title>` deleted), the tests with its ID in their name, and the modules whose docstring
  cites it.
- Code map: one box for each file of src/, its size by lines; the imports between the modules of
  the design's table "Module boundaries", each with whether the table permits it; and the class
  list, from the first line of each class docstring.

A side panel links to each section and each part of it. Needs you puts the needs of one kind in
one part, such as "Requirements in spec.md with no test (3)".

The page never shows a bare ID: it names the kind and the file, such as "requirement PAY-001 in
spec.md" or "milestone M4 in plan.md", or the heading of its part names them. The review findings
exist only in the runner logs of the machine that ran the milestones.

Run:
    python scripts/dashboard.py [--port N] [--no-browser]   # serves the page on 127.0.0.1
    python scripts/dashboard.py --out FILE   # saves the page to FILE, and serves nothing
The Refresh button of the page reads the files again. With no --port, the page is on port 8765,
or on a free port that the system picks when another program holds 8765.
"""

import argparse
import ast
import html
import math
import re
import shutil
import subprocess
import sys
import time
import webbrowser
from collections.abc import Iterable
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOST = "127.0.0.1"
DEFAULT_PORT = 8765
ANY_ID = re.compile(r"\b(?:[A-Z][A-Z0-9]*-\d{3,}|M\d+)\b")
ROW_ID = re.compile(r"^\|\s*([A-Z][A-Z0-9]*-\d{3,})\s*\|")
STATE_LINE = re.compile(r"^([A-Z][A-Z0-9]*-\d{3,})\s+(tested|manual|planned|missing)$")
PLAN_ROW = re.compile(r"^\|\s*\*\*M(\d+)\*\*\s*([^|]*)\|")
MILESTONE_COMMIT = re.compile(r"^M(\d+): (?!blocked$|partial work$|review repairs$|test repairs$)")
DEC_ROW = re.compile(r"^\|\s*(DEC-\d{3,})\s*\|\s*([^|]*?)\s*\|")
QUESTION_ROW = re.compile(r"^\|\s*([A-Z]+-\d+|\d+)\s*\|\s*([^|]+?)\s*\|")
BLOCKED_ENTRY = "- **Blocked:**"
BOUNDARIES_HEADING = "### 2.4 Module boundaries"
QUESTIONS_HEADING = re.compile(r"^## (?:\d+\.\s*)?Open design questions", re.IGNORECASE)
LOG_LINE = re.compile(r"^\W*(DECISION|FINDING):\s*(.*?)\W*$")
KINDS = {"EX": "acceptance example", "SCN": "scenario", "DEC": "design decision"}
FILES = {"EX": "spec.md", "SCN": "spec.md", "DEC": "design.md"}
SECTIONS = ("Needs you", "Plan and releases", "Trace", "Code map")
BOX_SCALE = 6  # pixels for the square root of one line of code

type Group = tuple[str, list[str]]  # a heading that names the kind and file, and its items
type Part = tuple[str, str]  # the subheading of a part of a section ('' for none), and its HTML


@dataclass(frozen=True)
class Requirement:
    """One requirement of the spec, with what traces it: state, design, milestone, tests, code."""

    spec_id: str
    state: str
    design: list[str]
    milestones: list[str]
    tests: list[str]
    modules: list[str]


@dataclass(frozen=True)
class SourceFile:
    """One file of src/: its path from the project, its lines, its imports and its classes."""

    path: str
    lines: int
    imports: list[str]
    classes: list[tuple[str, str]]


def named(identifier: str) -> str:
    """Return an ID with its kind and its file, such as "requirement PAY-001 in spec.md"."""
    if re.fullmatch(r"M\d+", identifier):
        return f"milestone {identifier} in plan.md"
    prefix = identifier.split("-")[0]
    return f"{KINDS.get(prefix, 'requirement')} {identifier} in {FILES.get(prefix, 'spec.md')}"


def with_names(text: str) -> str:
    """Return a text in which each ID is named with its kind and its file."""
    return ANY_ID.sub(lambda match: named(match[0]), text)


def read(relative: str) -> list[str]:
    """Return the lines of a project file, or no line when it does not exist."""
    path = ROOT / relative
    return path.read_text(encoding="utf-8-sig").splitlines() if path.is_file() else []


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    """Run a command in the project and return its result."""
    program = shutil.which(command[0]) or command[0]
    done = subprocess.run(
        [program, *command[1:]],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return done


def script_output(name: str, *args: str) -> subprocess.CompletedProcess[str] | None:
    """Return the result of a script of scripts/, run with this Python, or None without it."""
    if not (ROOT / "scripts" / name).is_file():
        return None
    return run([sys.executable, str(ROOT / "scripts" / name), *args])


def section(lines: list[str], heading: re.Pattern[str]) -> list[str]:
    """Return the lines under a heading, up to the next heading of level 1 or 2."""
    found: list[str] = []
    inside = False
    for line in lines:
        if line.startswith("#") and not line.startswith("###"):
            inside = heading.match(line) is not None
        elif inside:
            found.append(line)
    return found


# --- needs you -----------------------------------------------------------------------------------


def single_needs() -> list[str]:
    """Return the needs that come one at a time: a draft spec, uncommitted docs, waiting ideas."""
    needs: list[str] = []
    if any(line.strip() == "Status: Draft" for line in read("docs/spec.md")):
        needs.append("The spec (spec.md) is a draft: approve it, or go on with /write-spec.")
    if run(["git", "status", "--porcelain", "--", "docs"]).stdout.strip():
        needs.append("docs/ has uncommitted changes: commit them before a run.")
    ideas = [
        line
        for line in section(read("docs/unapproved-ideas.md"), re.compile("## Ideas"))
        if line.startswith("- ")
    ]
    if ideas:
        needs.append(f"{len(ideas)} unapproved ideas wait in unapproved-ideas.md.")
    return needs


def design_needs() -> list[Group]:
    """Return the Proposed decisions and the open questions of the design."""
    lines = read("docs/design.md")
    proposed = [match[1] for match in map(DEC_ROW.match, lines) if match and match[2] == "Proposed"]
    questions = [
        with_names(match[2])
        for match in map(QUESTION_ROW.match, section(lines, QUESTIONS_HEADING))
        if match and not set(match[2]) <= {"-", " "}
    ]
    return [
        ("Proposed design decisions in design.md: confirm or replace each", proposed),
        ("Open design questions in design.md", questions),
    ]


def plan_needs() -> list[Group]:
    """Return each blocked milestone of the plan with the first line of its Blocked entry."""
    blocked: list[str] = []
    current = ""
    for line in read("docs/plan.md"):
        heading = re.match(r"^### (M\d+)\b", line)
        current = heading[1] if heading else current
        if line.startswith(BLOCKED_ENTRY):
            blocked.append(f"{current}: {with_names(line[len(BLOCKED_ENTRY) :].strip())}")
    return [("Blocked milestones in plan.md", blocked)]


def spec_needs(states: dict[str, str]) -> list[Group]:
    """Return the consistency problems of the spec and its requirements with no test."""
    consistency = script_output("spec_coverage.py", "--consistency")
    problems = consistency.stdout if consistency is not None and consistency.returncode else ""
    return [
        ("Consistency problems of the spec", [with_names(line) for line in problems.splitlines()]),
        (
            "Requirements in spec.md with no test",
            [spec_id for spec_id, state in states.items() if state == "missing"],
        ),
    ]


def log_needs() -> list[Group]:
    """Return the DECISION lines and the kept FINDING lines of the runner logs of this machine."""
    logs = ROOT / ".claude" / "logs"
    found: dict[str, list[str]] = {"DECISION": [], "FINDING": []}
    for path in sorted(logs.glob("M*.log")) if logs.is_dir() else []:
        keeps_findings = path.stem.endswith("review-last")
        for match in map(LOG_LINE.match, path.read_text(encoding="utf-8").splitlines()):
            if match and (match[1] == "DECISION" or keeps_findings):
                found[match[1]].append(f"{path.name}: {with_names(match[2])}")
    return [
        ("Decisions in the runner logs", found["DECISION"]),
        ("Findings of the last reviews in the runner logs", found["FINDING"]),
    ]


def needs_parts(states: dict[str, str]) -> list[Part]:
    """Return what needs the user: the single needs first, then one part for each kind of need.

    The heading of a part names the kind and the file of its items, so an item can be a bare ID.
    """
    single = single_needs()
    groups = design_needs() + plan_needs() + spec_needs(states) + log_needs()
    parts = [("", items(single, ""))] if single else []
    parts += [(f"{heading} ({len(lines)})", items(lines, "")) for heading, lines in groups if lines]
    return parts or [("", items([], "Nothing needs you now."))]


# --- the plan and the trace ----------------------------------------------------------------------


def requirement_states() -> dict[str, str]:
    """Return each requirement and example ID with its state, from `spec_coverage.py`."""
    listing = script_output("spec_coverage.py")
    lines = listing.stdout.splitlines() if listing is not None else []
    matches = (STATE_LINE.match(line) for line in lines)
    return {match[1]: match[2] for match in matches if match}


def plan_rows() -> list[list[str]]:
    """Return the cells of each row of the table "Milestones at a glance", the milestone named."""
    rows: list[list[str]] = []
    for line in read("docs/plan.md"):
        match = PLAN_ROW.match(line)
        if match:
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            rows.append(
                [f"{named('M' + match[1])}: {match[2].strip()}", *map(with_names, cells[1:])]
            )
    return rows


def release_rows() -> list[list[str]]:
    """Return the cells of each row of docs/releases.md, without the header and its line."""
    rows = [
        line.strip().strip("|").split("|")
        for line in read("docs/releases.md")
        if line.startswith("|")
    ]
    return [[cell.strip() for cell in row] for row in rows[2:]]


def milestone_commits() -> list[tuple[str, str, str]]:
    """Return the hash, the milestone and the subject of each commit that finished a milestone.

    The newest commit comes first.
    """
    commits: list[tuple[str, str, str]] = []
    for line in run(["git", "log", "--format=%H%x09%s"]).stdout.splitlines():
        sha, _, subject = line.partition("\t")
        match = MILESTONE_COMMIT.match(subject)
        if match:
            commits.append((sha, f"M{match[1]}", subject))
    return commits


def refs_of_commit(sha: str) -> list[str]:
    """Return the IDs of the Refs entry that a commit deleted from docs/plan.md."""
    diff = run(["git", "show", "--format=", sha, "--", "docs/plan.md"]).stdout.splitlines()
    refs = [line for line in diff if line.startswith("-- **Refs:**")]
    return ANY_ID.findall(" ".join(refs))


def milestones_by_requirement() -> dict[str, list[str]]:
    """Return the milestones of each requirement: open blocks of the plan, then finished ones."""
    found: dict[str, list[str]] = {}
    current = ""
    for line in read("docs/plan.md"):
        heading = re.match(r"^### (M\d+)\b", line)
        current = heading[1] if heading else current
        for spec_id in ANY_ID.findall(line) if line.startswith("- **Refs:**") else []:
            found.setdefault(spec_id, []).append(current)
    for sha, number, _ in milestone_commits():
        for spec_id in refs_of_commit(sha):
            found.setdefault(spec_id, []).append(number)
    return found


def design_by_requirement() -> dict[str, list[str]]:
    """Return the design decisions and test-design rows that cite each requirement."""
    found: dict[str, list[str]] = {}
    for line in read("docs/design.md"):
        decision = DEC_ROW.match(line)
        label = named(decision[1]) if decision else "a table row of design.md"
        if not line.startswith("|"):
            continue
        for spec_id in {i for i in ANY_ID.findall(line) if not i.startswith(("DEC-", "M"))}:
            labels = found.setdefault(spec_id, [])
            if label not in labels:
                labels.append(label)
    return found


def test_names() -> list[str]:
    """Return the name of each Python test under tests/."""
    names: list[str] = []
    for path in sorted((ROOT / "tests").rglob("test_*.py")):
        names += re.findall(
            r"^\s*(?:async\s+)?def\s+(test_\w+)", path.read_text(encoding="utf-8"), re.MULTILINE
        )
    return names


def tests_of(spec_id: str, names: Iterable[str]) -> list[str]:
    """Return the tests whose name carries an ID, such as test_pay_001_... for PAY-001."""
    key = spec_id.lower().replace("-", "_")
    return [name for name in names if re.search(rf"(?:^|_){key}(?:_|$)", name)]


def trace(states: dict[str, str], files: list[SourceFile]) -> list[Requirement]:
    """Return the trace of each requirement of the spec (examples left out)."""
    design, milestones, names = design_by_requirement(), milestones_by_requirement(), test_names()
    modules = module_citations(files)
    return [
        Requirement(
            spec_id,
            state,
            design.get(spec_id, []),
            sorted(set(milestones.get(spec_id, []))),
            tests_of(spec_id, names),
            modules.get(spec_id, []),
        )
        for spec_id, state in states.items()
        if not spec_id.startswith("EX-")
    ]


# --- the code map --------------------------------------------------------------------------------


def source_file(path: Path) -> SourceFile:
    """Read one Python file of src/: its lines, the modules it imports, its classes."""
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports += [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            imports.append(node.module)
    classes = [
        (node.name, (ast.get_docstring(node) or "").split("\n")[0])
        for node in tree.body
        if isinstance(node, ast.ClassDef)
    ]
    relative = path.relative_to(ROOT).as_posix()
    return SourceFile(relative, len(text.splitlines()), imports, classes)


def source_files() -> list[SourceFile]:
    """Return every Python file of src/ that parses."""
    files: list[SourceFile] = []
    for path in sorted((ROOT / "src").rglob("*.py")):
        try:
            files.append(source_file(path))
        except SyntaxError:
            continue  # ruff reports the error; the map shows the files that parse
    return files


def module_citations(files: list[SourceFile]) -> dict[str, list[str]]:
    """Return the files whose module docstring cites each ID."""
    found: dict[str, list[str]] = {}
    for file in files:
        docstring = (
            ast.get_docstring(ast.parse((ROOT / file.path).read_text(encoding="utf-8"))) or ""
        )
        for spec_id in set(ANY_ID.findall(docstring)):
            found.setdefault(spec_id, []).append(file.path)
    return found


def boundary_table() -> dict[str, set[str]]:
    """Return each module of the table "Module boundaries" of the design, and what it may import."""
    table: dict[str, set[str]] = {}
    inside = False
    for line in read("docs/design.md"):
        if line.startswith("#"):
            inside = line.strip() == BOUNDARIES_HEADING
        elif inside and line.startswith("|") and "`" in line:
            cells = [cell.strip().strip("`") for cell in line.strip("| \n").split("|")]
            table[dotted(cells[0])] = {dotted(name) for name in cells[1].split(",")} - {"", "none"}
    return table


def dotted(path: str) -> str:
    """Return a module path (`src/payments`, `src/clock.py`) as a dotted name (`src.payments`)."""
    name = Path(path.strip().strip("`").strip("/"))
    return ".".join(name.with_suffix("").parts) if name.parts else ""


def owner(name: str, modules: Iterable[str]) -> str:
    """Return the most specific module of the table that holds a dotted name, or ''."""
    holders = [module for module in modules if f"{name}.".startswith(f"{module}.")]
    return max(holders, key=len, default="")


def import_edges(
    files: list[SourceFile], table: dict[str, set[str]]
) -> list[tuple[str, str, bool]]:
    """Return each import between two modules of the table, and whether the table permits it."""
    edges: set[tuple[str, str, bool]] = set()
    for file in files:
        home = owner(dotted(file.path), table)
        for target in (owner(name, table) for name in file.imports) if home else ():
            if target and target != home:
                edges.add((home, target, target in table[home]))
    return sorted(edges)


# --- the page ------------------------------------------------------------------------------------


def escape(text: str) -> str:
    """Return the text safe for HTML."""
    return html.escape(text, quote=True)


def items(lines: list[str], empty: str) -> str:
    """Render lines as an HTML list, or a sentence when there is none."""
    if not lines:
        return f"<p class='quiet'>{escape(empty)}</p>"
    return "<ul>" + "".join(f"<li>{escape(line)}</li>" for line in lines) + "</ul>"


def table(header: list[str], rows: list[list[str]], empty: str) -> str:
    """Render rows as an HTML table, or a sentence when there is none."""
    if not rows:
        return f"<p class='quiet'>{escape(empty)}</p>"
    head = "".join(f"<th>{escape(cell)}</th>" for cell in header)
    body = "".join("<tr>" + "".join(f"<td>{escape(c)}</td>" for c in row) + "</tr>" for row in rows)
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def plan_parts() -> list[Part]:
    """Render the plan table, the releases and the last milestone commits."""
    commits = [[with_names(subject)] for _, _, subject in milestone_commits()[:10]]
    plan_header = ["Milestone", "Description", "Model", "Effort", "Human test", "Status"]
    releases = [[with_names(c) for c in r] for r in release_rows()]
    return [
        ("Milestones at a glance", table(plan_header, plan_rows(), "No milestone is planned.")),
        (
            "Releases",
            table(["Version", "Date", "Last milestone", "Milestones"], releases, "No release yet."),
        ),
        ("Last milestones done", table(["Commit"], commits, "No milestone is done yet.")),
    ]


def trace_parts(requirements: list[Requirement]) -> list[Part]:
    """Render the trace of each requirement as one table."""
    rows = [
        [
            named(item.spec_id),
            item.state,
            "; ".join(item.design) or "-",
            ", ".join(named(m) for m in item.milestones) or "-",
            ", ".join(item.tests) or "-",
            ", ".join(item.modules) or "-",
        ]
        for item in requirements
    ]
    header = ["Requirement", "State", "Design", "Milestone", "Tests", "Code"]
    return [("", table(header, rows, "The spec has no requirement yet."))]


def code_parts(files: list[SourceFile]) -> list[Part]:
    """Render the floor plan of src/, the import graph against the table, and the class list."""
    boxes = "".join(
        f"<div class='box' style='width:{max(int(math.sqrt(f.lines) * BOX_SCALE), 40)}px;"
        f"height:{max(int(math.sqrt(f.lines) * BOX_SCALE), 40)}px' title='{escape(f.path)}'>"
        f"{escape(f.path.removeprefix('src/'))}<br>{f.lines}</div>"
        for f in files
    )
    edges = [
        [a, b, "yes" if ok else "no: the table does not permit it"]
        for a, b, ok in import_edges(files, boundary_table())
    ]
    classes = [[name, file.path, doc or "-"] for file in files for name, doc in file.classes]
    floor = (
        f"<div class='plan'>{boxes}</div>"
        if boxes
        else "<p class='quiet'>src/ holds no Python yet.</p>"
    )
    return [
        ("Floor plan of src/ (box size by lines)", floor),
        (
            "Imports between the modules of the design",
            table(
                ["From", "To", "Permitted"], edges, "No import between the modules of the table."
            ),
        ),
        ("Classes", table(["Class", "File", "Responsibility"], classes, "No class yet.")),
    ]


def anchor(*texts: str) -> str:
    """Return an HTML id made of the texts, such as 'needs-you--blocked-milestones-in-plan-md-1'."""
    return "--".join(re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") for text in texts)


def sections_html(sections: list[tuple[str, list[Part]]]) -> tuple[str, str]:
    """Render the side panel of links, and the sections with their parts."""
    links: list[str] = []
    bodies: list[str] = []
    for title, parts in sections:
        sub_links = ""
        body = f"<section id='{anchor(title)}'><h2>{escape(title)}</h2>"
        for heading, part in parts:
            if heading:
                key = anchor(title, heading)
                sub_links += f"<li><a href='#{key}'>{escape(heading)}</a></li>"
                body += f"<h3 id='{key}'>{escape(heading)}</h3>"
            body += part
        sub_list = f"<ul>{sub_links}</ul>" if sub_links else ""
        links.append(f"<li><a href='#{anchor(title)}'>{escape(title)}</a>{sub_list}</li>")
        bodies.append(body + "</section>")
    nav = f"<nav aria-label='Contents'><ul>{''.join(links)}</ul></nav>"
    return nav, "".join(bodies)


STYLE = """
:root { color-scheme: light dark; --fg: #1f2328; --bg: #ffffff; --muted: #59636e;
  --line: #d1d9e0; --box: #ddf4ff; }
@media (prefers-color-scheme: dark) { :root { --fg: #e6edf3; --bg: #0d1117; --muted: #9198a1;
  --line: #3d444d; --box: #0c2d6b; } }
html { scroll-behavior: smooth; }
body { margin: 0; font: 15px/1.5 system-ui, sans-serif; color: var(--fg); background: var(--bg); }
.layout { display: grid; grid-template-columns: 240px minmax(0, 1fr); gap: 32px;
  max-width: 1380px; margin: 0 auto; padding: 16px; }
nav { position: sticky; top: 16px; align-self: start; max-height: calc(100vh - 32px);
  overflow-y: auto; font-size: 14px; border-right: 1px solid var(--line); padding-right: 16px; }
nav ul { list-style: none; margin: 0; padding: 0; }
nav > ul > li { margin-bottom: 12px; font-weight: 600; }
nav li li { font-weight: 400; margin: 4px 0 0 12px; }
nav a { color: var(--fg); text-decoration: none; }
nav li li a { color: var(--muted); }
nav a:hover { text-decoration: underline; }
main { min-width: 0; overflow-x: auto; }
h2, h3 { scroll-margin-top: 16px; }
@media (max-width: 760px) { .layout { grid-template-columns: minmax(0, 1fr); }
  nav { position: static; max-height: none; border-right: 0; padding-right: 0;
    border-bottom: 1px solid var(--line); padding-bottom: 8px; } }
header { display: flex; justify-content: space-between; align-items: center; gap: 16px; }
table { border-collapse: collapse; width: 100%; margin: 8px 0 16px; }
th, td { border: 1px solid var(--line); padding: 4px 8px; text-align: left; vertical-align: top; }
.quiet { color: var(--muted); }
.plan { display: flex; flex-wrap: wrap; gap: 4px; }
.box { background: var(--box); border: 1px solid var(--line); font-size: 12px; overflow: hidden;
  padding: 4px; box-sizing: border-box; }
button { font: inherit; padding: 4px 12px; }
"""


def page() -> str:
    """Read every owner of a fact, and return the whole page."""
    states = requirement_states()
    files = source_files()
    parts = [
        needs_parts(states),
        plan_parts(),
        trace_parts(trace(states, files)),
        code_parts(files),
    ]
    nav, sections = sections_html(list(zip(SECTIONS, parts, strict=True)))
    note = "Review findings and decisions come from the runner logs of this machine only."
    return (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        f"<title>Dashboard - {escape(ROOT.name)}</title><style>{STYLE}</style></head><body>"
        f"<div class='layout'>{nav}<main>"
        f"<header><h1>{escape(ROOT.name)}</h1><form method='get' action='/'>"
        "<button type='submit' title='Read the files again'>Refresh</button></form></header>"
        f"<p class='quiet'>Read at {time.strftime('%Y-%m-%d %H:%M:%S')}. {note}</p>"
        f"{sections}</main></div></body></html>"
    )


class PageHandler(BaseHTTPRequestHandler):
    """Answers each GET with the page, read again from the files; it serves nothing else."""

    def do_GET(self) -> None:
        """Send the page."""
        body = page().encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        """Print nothing for each request."""


class PageServer(ThreadingHTTPServer):
    """Serves the page, and refuses a port that another program holds.

    On Windows, SO_REUSEADDR lets a second socket bind a port that a program already listens on,
    and the browser can then reach that program. So the server does not set it there.
    """

    allow_reuse_address = sys.platform != "win32"


def open_server(port: int | None) -> PageServer:
    """Bind the server to the port given; with none, to DEFAULT_PORT, or else to a free port.

    Raises OSError when the port given is not free. Windows can report a port that another
    program holds as WinError 10013 (access forbidden), not as "in use".
    """
    if port is not None:
        return PageServer((HOST, port), PageHandler)
    try:
        return PageServer((HOST, DEFAULT_PORT), PageHandler)
    except OSError:
        return PageServer((HOST, 0), PageHandler)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Read the command line."""
    parser = argparse.ArgumentParser(description="Show the state of the project on one page.")
    parser.add_argument("--out", type=Path, default=None, help="save the page to this file")
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help=f"the port on {HOST} (default: {DEFAULT_PORT}, or a free port if it is taken)",
    )
    parser.add_argument("--no-browser", action="store_true", help="do not open the browser")
    return parser.parse_args(argv)


def serve(server: PageServer, open_browser: bool) -> None:
    """Print the URL, open the browser if asked, and serve the page until Ctrl+C."""
    url = f"http://{HOST}:{server.server_address[1]}/"
    sys.stdout.write(f"The dashboard is at {url} (Ctrl+C stops it).\n")
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        sys.stdout.write("Stopped.\n")


def main(argv: list[str] | None = None) -> int:
    """Save the page, or serve it on 127.0.0.1 and open the browser until Ctrl+C."""
    args = parse_args(argv)
    if args.out is not None:
        args.out.write_text(page(), encoding="utf-8")
        return 0
    try:
        server = open_server(args.port)
    except OSError as error:
        sys.stderr.write(
            f"Port {args.port} on {HOST} is not free: another program holds it, or Windows "
            f"reserves it ({error.strerror}). Give another port, or leave out --port.\n"
        )
        return 1
    serve(server, open_browser=not args.no_browser)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
