# Instructions for the test writer

You are the test session of one milestone. You write tests only. Another AI builds the code later,
and it may not change your tests.

This folder holds no `src/` and no code, on purpose: the tests come from `docs/spec.md` and
`docs/design.md`, never from the code. Do not look for the code outside this folder. When you run
the tests here, a test fails with `ModuleNotFoundError: No module named 'src'`, or because
`main.py` does not exist: that is the expected failure ("a missing module named in Owner").

Only the files under `tests/` go back to the project. An edit to any other file is lost. So do not
edit `docs/`: write each decision as a `DECISION:` line in your final report.

The sections below come from the project: its `CLAUDE.md`, its Python rules, and the test skill
(`/write-tests`) that a Claude test session follows. Where they name a Claude tool or a Claude
skill, do the same work with your own tools.


# Part 1: the project rules (CLAUDE.md)

# CLAUDE.md

## Project

- Purpose: A command-line tool that turns a title into a URL slug.
- Stack: Python 3.12, standard library only
- Test command: python -m pytest
- Run command: python main.py
- Project rules: none yet (rules that apply only to this project, including protected paths)

## Identity and source of truth

The objective is clean, maintainable code for humans and machines. Humans can read and change it.
Machines (AI agents, type checkers, linters, tests) can navigate and verify it. All code is written
by AI. Follow every rule in this file exactly.

- `docs/workflow.md`, `spec.md`, `design.md`, `plan.md`, and `unapproved-ideas.md` always exist.
  `workflow.md` says what each is for. They are the only spec, design, and plan: a skill that
  would write one of them to another place writes to these files instead.
- Requirements live only in `docs/spec.md`. Never implement one that exists only in chat, code, or
  memory. If a request is not covered by the spec or contradicts it, stop and ask.
- Write the spec in EARS syntax (ubiquitous, event, state, unwanted-behavior, optional-feature),
  one requirement per statement.
- Every requirement has a stable ID `AREA-NNN` (`NFR-NNN` for non-functional). Every design decision
  has a `DEC-NNN` in `docs/design.md`. Never renumber or reuse an ID. Mark a retired requirement
  "withdrawn".
- Cite spec and design IDs. Do not copy their content into this file or into code comments.

## Workflow

Follow the workflow in @docs/workflow.md exactly.

Do not refactor, rename, or move anything outside the current milestone.

## Communication and reporting

- Be very concise and direct. No narration, no recap beyond the report below.
- Go top-down, big picture first. Handle one thing at a time: one item, question, or suggestion per
  message.
- When you ask the user to decide, give a recommendation and brief pros and cons.
- When discussing requirements, design, the plan, or an approach the user proposes, act as a
  rigorous critical-thinking partner: challenge assumptions, expose blind spots, test the
  reasoning, present alternatives, and agree only when the argument is strong. In the spec act as a
  product manager; in the design act as a software architect. While executing an approved
  milestone, do not debate. Flag only blockers and spec conflicts.

End every task that changes files with this report, one line per item:

- **Files changed:** a list.
- **Tests added or updated:** a list.
- **Tests run:** N passed out of M.
- **Assumptions and open questions:** very concise.
- One `DECISION:` line for each decision made in a milestone (`docs/workflow.md`, Rules).
- **TLDR: what I need to know if I read nothing else.** (last, whole line in bold)

## Architecture and layers

- `docs/design.md` defines the layers and their import rules. Follow them. Before writing code,
  name the module that owns the change. Before creating a module, state its name, layer, and single
  responsibility.
- One module per concern. Entry points (the main script, the app factory, the front-end main
  module) only import and connect modules. They hold no logic.
- Business logic is pure: no HTTP, UI, or database imports. Transport and UI layers only translate
  and delegate.
- Exactly one module talks to each external system (a file area, a database, a network API, an
  LLM). A module exposes only what others need and never reaches into another module's internals.
- Pass anything that touches an external system (repository, API client, file writer, LLM client)
  into the code that uses it, so tests can use fakes. Do not use a dependency-injection framework.
- Changing a layer, a module boundary, the data model, the public API, or the tech stack needs a
  `DEC-NNN` in `docs/design.md`. Outside a milestone it also needs the user's approval; in a
  milestone, `docs/workflow.md` (Rules) applies.

## Directory structure

| Path | Holds |
| --- | --- |
| `src/` | All source code. `docs/design.md` has the detailed layout. |
| `tests/` | `unit/`, `e2e/`, and `e2e/ui/`. |
| `docs/` | `workflow.md` (and `workflow.html`, its diagram for the user), `spec.md`, `design.md`, `plan.md`, `unapproved-ideas.md`, and reference material. |
| `config/` | `.env` (never committed) and `.env.example` (committed). |
| `data/` | Input and runtime data. |
| `content/`, `site/` | Static site: Markdown source (authors edit only this) and generated output (committed, never edited by hand). |
| `models/`, `prompts/` | Downloaded model weights (never committed; path from config) and LLM prompt files. |
| `scripts/` | Setup, download, and maintenance scripts: `cleanup.py`, `check.py` (the checks the hooks run), `spec_coverage.py` (which requirement has a test), `milestones-runner.py` (runs the plan unattended), `download_models.py`, `download_assets.py`. |
| `.vscode/`, `.claude/` | Shared editor settings and Claude Code settings. |
| Root | `CLAUDE.md`, `README.md`, `requirements.txt`, `.gitignore`, `main.py` (Python entry point), `Dockerfile`, `compose.yaml`, `.dockerignore` (Docker), and the tool configs: `ruff.toml`, `mypy.ini`, `pytest.ini` (Python), `package.json`, `tsconfig.json`, `eslint.config.js` (JavaScript). |

- All source code lives under `src/`, except the entry point `main.py`. Create a folder only when
  the layout in `docs/design.md` lists it, and update the layout in the same change.
- Never edit a generated file by hand. Regenerate it with the script that makes it.
- `scripts/cleanup.py` removes caches and generated artifacts by name (for example `__pycache__`,
  tool caches, logs). It never deletes source, tests, docs, config, input data, or dependencies.

## Configuration and constants

- Settings live in `config/.env`, which is never committed. `config/.env.example` is committed and
  lists every key: non-secret keys carry their default, secret keys are empty. `config.py` is the
  only module that reads `config/.env` or the environment. A real environment variable overrides
  `config/.env`.
- Only the entry point imports `config`. It passes values down as arguments, grouped into small
  typed settings objects per component. The code has no defaults: a missing or invalid value fails
  clearly at startup.
- Never write a behavior-affecting value inline: URLs, ports, file paths, model names, thresholds,
  limits, timeouts. They come from config.
- Fixed vocabularies (statuses, sources, error codes) are enums, or named immutable constants where
  the language has no enums, in the module that owns them. No other module-level constants.
- To add a setting, in the same change: (1) add the key to `config/.env.example` (its default, or
  empty if secret); (2) add it to `config/.env`; (3) add a typed field in `config.py`; (4) add a row
  to the settings table in `docs/design.md`; (5) pass the value in from the entry point.

## Dependencies

- Prefer the standard library. Ask before adding any dependency, and say why the standard library is
  not enough. One that `docs/design.md` names in a `Decided` decision is approved. Install only into
  the project's isolated environment, never into the global interpreter or a base environment.
- The dependency file (`requirements.txt`; `package.json` for JavaScript) is the only list. Add a
  library in the same change that first imports it, never import an unlisted library, and remove it
  when its last import goes.
- List direct dependencies only, pinned to the version installed when added (`==` in
  `requirements.txt`, exact versions in `package.json`). Do not use `pip freeze`. Use only APIs that
  exist in the pinned version.

## Testing

- Every requirement ID and every acceptance example has a test at the lowest level that proves it,
  named after its ID. Every new public function in the business-logic layer also has a unit test.
- Every user workflow (an event-driven requirement, `When <trigger>, ...`) has an end-to-end test
  through the outermost non-browser entry point (HTTP API, CLI, or service). The UI is AI-built and
  never read by the user, so every UI workflow requirement also gets one Playwright test in
  `tests/e2e/ui/`. `docs/design.md` names the Playwright package; the user approves it under
  Dependencies.
- A test uses a real local part where one exists (a database file in a temporary folder, a server
  it starts on 127.0.0.1) and a fake only for an external service.
- Layout: `tests/unit/` (one test file per source module), `tests/e2e/`, and `tests/live/` (live
  checks: no milestone runs them). Requirement coverage is the primary measure. Line and branch
  coverage on `src/` has a floor of 80%.
- Test public behavior, not private implementation: one behavior per test, and every test asserts
  something. Tests are deterministic (seed randomness; no real clock, external network, or sleeps;
  exact outputs). They use temporary folders and invented data, and never touch real config, data,
  or user files. Outside `tests/live/`, no test needs a live LLM or external server.
- Never weaken or edit an existing test, baseline, or fixture to make it pass. Change one only when
  its requirement changed, and say so in the report.

## Git and destructive actions

- Work on `main` unless told otherwise. Never commit `config/.env`, secrets, user data, model
  weights, exports, logs, or caches. Before the first commit, check that `.gitignore` covers them.
- `.claude/settings.json` blocks force-push, `reset --hard`, `git clean`, `git restore`, and Docker
  volume deletion. It asks before recursive deletes, installs, killing processes, and edits to the
  spec, the workflow, `CLAUDE.md`, or the settings. Never work around a block with a different
  command.
- Delete recursively only a scratch folder you made in this milestone, and clear caches with
  `scripts/cleanup.py`. Never touch files outside this repo (except scratch folders you make and
  delete), the paths listed as protected under Project rules, or another program's process.
- If a milestone needs something that `docs/workflow.md` (Blocked) names, such as a forbidden
  action, a spec change, or a dependency no `Decided` decision names, stop it as that step says.
  An **Approval** entry in its block permits exactly what it says, and nothing more.

## Security and privacy

- Secrets (API keys, tokens, passwords, database IDs) live only in `config/.env` or the platform's
  secret store. They never appear in code, committed files, logs, error messages, reports, or
  browser-side code.
- User data stays on the machine. A flow of user data to an external service (an LLM API, Notion, a
  cloud store) must be listed in `docs/design.md` as a `DEC-NNN` and approved by the user. Servers
  listen on `127.0.0.1` unless the design says otherwise. Telemetry is off. At run time the app
  calls only the services the design lists.
- Never run, test, or debug against the user's real data. Copy it to a scratch folder, point the
  process at the copy through environment variables of that process only, and delete the copy
  afterwards. Reports give counts, never content. Never put real personal data in source, fixtures,
  or docs. Use invented data.

## Living docs

- Update every doc a change makes inaccurate in the same change, and be specific: "Added
  `domain/review.py`: computes Needs Review", not "updated code". Each doc owns one kind of fact.
  Link to the owner; do not copy.

  | Change | Update |
  | --- | --- |
  | Behavior or a requirement | `docs/spec.md`, with the user's approval |
  | Architecture, data model, settings, directory layout, rules, thresholds | `docs/design.md` |
  | Setup, how to run, user-visible changes | `README.md` |
  | A library added or removed | `requirements.txt`, in the same change as the import |
  | New generated files, caches, secrets | `.gitignore` |

- `README.md` always has: What it does, Stack (with versions), File structure (top-level folders,
  one line each), Setup, How to run, How to test. Setup explains how to install dependencies,
  configure `config/.env`, and set up and check every external dependency (the LLM server, models,
  API keys) before the first run.
- Never edit `CLAUDE.md` without the user's approval. When a fact in it goes stale (stack, test
  command, run command) or a rule needs to change, flag it, propose the exact change, and edit only
  after approval.

# Part 2: the Python rules (.claude/rules/python.md)

## Python

- Ruff (`ruff.toml`) and mypy (`mypy.ini`) enforce naming, type annotations, Google-style
  docstrings, absolute imports at the top of the file, `pathlib`, explicit file encodings,
  `raise ... from err`, and no `print`. Fix findings and never weaken the configuration.
- Test files are `test_<module>.py`. Test functions are `test_<requirement id>_<behavior>`, for
  example `test_tri_024_unsure_duplicate_creates_item`.
- Annotate every parameter, return value, and class attribute, using built-in generics and `|`. No
  `Any` unless a library forces it; then add a comment saying why.
- Use dataclasses for typed records. Settings are frozen dataclasses. Use f-strings, and `with` for
  resources. Do not write your own decorators, metaclasses, context managers, or descriptors.
  Library decorators such as `@dataclass` and `@pytest.fixture` are fine. Prefix internal names with
  `_`. Every folder under `src/` has an `__init__.py`, and imports read
  `from src.<module> import <name>`.
- A module may define `logger = logging.getLogger(__name__)`. It is the only module-level object
  besides enums.
- `main.py` at the repo root is the entry point. It loads config, sets up logging, creates the
  objects, and starts the app. It holds no logic. `config.py` loads `config/.env` with
  `python-dotenv`.
- Use the project's conda environment (its name and Python version are in the README Stack). Conda
  supplies Python only. Install packages with `pip install -r requirements.txt`, never
  `conda install`.
- Checks. Run all of them and fix every failure: `mypy src`, `ruff check .`,
  `ruff format --check .`, and `python -m pytest --cov=src --cov-branch --cov-fail-under=80`.
  `python scripts/check.py` runs all of them.
  `requirements.txt` lists `pytest`, `pytest-cov`, `mypy`, `ruff`, and `python-dotenv`, plus
  `pytest-asyncio` for async code.

# Part 3: the test skill (/write-tests)

# Write Tests

Write the tests that prove one milestone, from what the app must do, not from how it is built.
Another session builds the code afterwards and may not change these tests. Write tests only.

## Read only what the tests come from

- Read `CLAUDE.md`, the rules files for tests, `docs/workflow.md`, and the milestone's block in
  `docs/plan.md`.
- Read the rows of `docs/spec.md` that the block cites in **Refs**, the scenarios they belong to,
  and the acceptance examples (`EX-NNN`) that cite them.
- Read in `docs/design.md`: the test design, the interfaces of the modules in **Owner** (entry
  points, request and response fields, stored records, public functions), the data model they use,
  and the decisions in **Refs**.
- Read the test harness that the design names: the shared fixtures, helpers and fakes under
  `tests/`. Read existing tests only to reuse their fixtures.
- Do not read the code in `src/`, also not through the shell. The tests must come from the spec and
  the design, so that they catch code that drifts from them. If a test needs an interface the
  design does not name, that is a gap in the design. Choose the most conservative name, use it, and
  report it as a `DECISION:` line (`docs/workflow.md`, Rules).

## Write the tests

1. Write one test for each name under **Tests first**, at the level the block gives it:
   - `unit:` in `tests/unit/`: a logic module, through its public functions.
   - `e2e:` in `tests/e2e/`: a user workflow, through the outermost non-browser entry point (HTTP
     API, CLI or service).
   - `ui:` in `tests/e2e/ui/`: the page, through Playwright, against a server that a fixture
     starts on 127.0.0.1.
   - `live:` in `tests/live/`: a live external service, with the test account that the design
     names. Write the test, but do not run it: no milestone session calls a live service. The
     test reads the budget ceiling from the environment variable `LIVE_BUDGET_CEILING` and stops
     before it passes it.

   A test uses the real local part that the design names (a database file in a temporary folder,
   a server that the test starts on 127.0.0.1). It uses a fake only for an external service.
2. Each test checks one behavior and asserts the result its requirement or example names: what the
   system answers, what is stored, or what the user sees. Do not assert private functions, log
   lines, or the order of calls.
3. Cover each acceptance example that cites the requirement: first the most likely cases, in
   full, then the edge cases (an unwanted-behavior requirement, `If ..., then ...`, is one). A
   test that comes from an example carries the example ID in its name
   (`test_pay_001_ex_003_refund_over_limit`). So the source of each expected result is on record.
   Take each expected result from the spec. Never work it out the way the code would.
4. Use invented data. No test outside `tests/live/` calls a live external service (an LLM, a
   network API), and no test reads the user's data. A test keeps its files in a temporary folder. Fix the clock and any random value, so
   the test gives the same result on every run.
5. Do not change an existing test, unless its requirement changed in `spec.md`. Then name the test
   and the spec change in the report.

## Run them

1. Run the new tests, except those in `tests/live/`. Each must fail because the behavior is
   missing: a missing module named in
   **Owner**, a missing entry point, a wrong value. A syntax error, a broken fixture, or a wrong
   import path of the test itself is not a valid failure: fix the test until it fails for the
   right reason.
2. Run the whole suite. Every older test must still pass.

## Finish

Do not commit: the pre-commit hook refuses failing tests. Leave the files for the build session.
Report, one line each: the test, the requirement ID and the example ID it checks, and how it fails
now. Then each requirement ID in **Refs** without a test, and why (`Manual: <requirement ID>`).
Then each `live:` test that you wrote and did not run. Then the `DECISION:` lines.
