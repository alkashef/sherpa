# sherpa

**A Spec-Driven Development (SDD) framework that helps a developer build software with an AI coding
assistant.** For now it supports Claude Code only (see [Approach](#approach)). It is delivered as a
Claude Code skill, `project-init`, that sets up a new project. You create an
empty folder and open it in VS Code, then run the skill. It gives the new project its starting
files: `CLAUDE.md` and path-scoped rules, docs, README, tool configs and starting folders. Then it
commits, creates a GitHub repository, and pushes.

This repository is the skill's source. Everything the skill needs is inside `skills/project-init/`.

## Contents

- [Objectives](#objectives)
- [Approach](#approach)
- [What it does](#what-it-does)
- [What a new project gets, and why](#what-a-new-project-gets-and-why)
  - [Every project](#every-project)
  - [With the `python` module](#with-the-python-module)
  - [With the `javascript` module](#with-the-javascript-module)
  - [With other modules](#with-other-modules)
- [Stack](#stack)
- [File structure](#file-structure)
- [How to use](#how-to-use)
  - [Set up the machine (once)](#set-up-the-machine-once)
  - [Start a new project](#start-a-new-project)
- [How to contribute](#how-to-contribute)
  - [Set up the environment](#set-up-the-environment)
  - [Run the scripts alone](#run-the-scripts-alone)
  - [Change what new projects get](#change-what-new-projects-get)
  - [The line budget](#the-line-budget)
- [How to test](#how-to-test)
  - [The test suite](#the-test-suite)
  - [Lint and type checks](#lint-and-type-checks)
  - [Checked in real Claude Code sessions](#checked-in-real-claude-code-sessions)

## Objectives

The software a developer builds with sherpa must be:

- **Written with zero lines of code by the developer.** Natural language is the programming
  language.
- **Production-level.** No prototype or demo software.
- **High-quality.** Correct, readable, tested, maintainable.

## Approach

Spec-Driven Development (SDD): the developer approves a spec, then a design, then a plan, and the
plan is built one milestone at a time. AI generation is probabilistic, so deterministic checks
(tests, linters, type checkers, hooks) bound it.

**Which assistant.** The ideal is a framework that works with any AI coding assistant (Claude,
Gemini, etc.). The current choice is to limit it to Claude Code, because the skill, the rules files,
the permissions, the hooks and the milestone runner use its features.

**How a new project meets each objective.** The rest of this file gives the details.

| Objective | How a new project gets it |
| --- | --- |
| Zero lines of code | `/sherpa` names the next step and starts its skill. `/write-spec`, `/write-design` and `/write-plan` turn an interview into the documents Claude builds from; `milestones-runner.py` runs the plan unattended. |
| Production-level | Approved requirements with stable IDs, acceptance examples, thin milestones, scope controls and permissions that block destructive commands. Ideas that nobody approved stay in `docs/unapproved-ideas.md`, and nothing is built from them. A release is a cut point on a branch where every commit passed the checks, with the date as its version (`release.py`). |
| High-quality | Ruff, mypy, ESLint, Prettier, Stylelint and an 80% branch-coverage floor, run by an edit hook and a pre-commit hook on every change. The tests of a milestone are written from the spec and the design by a session that may not read the code, and the session that writes the code may not change them. `spec_coverage.py` checks that each requirement and each acceptance example of a milestone has a test. A third session reviews the change against a checklist, and a repair must pass every check again. `check.py` also enforces one class per file and the module boundaries of the design. |

## What it does

1. `scripts/init_project.py` checks the folder, git, the `gh` login and conda (and changes nothing
   if a check fails), runs `git init`, calls the builder, creates a conda environment with the
   project's name (Python 3.12) and, for a Python project, installs the Python tools into it and
   pins them, then commits, turns on the pre-commit hook, runs `gh repo create`, and pushes.
2. `scripts/build_instance.py` splits the master `assets/CLAUDE_GOLDEN.md` into a `CLAUDE.md` of about
   140 lines that always loads, plus `.claude/rules/*.md` files that load only when Claude touches
   matching files. It copies or fills in the other files from `assets/`. Rules a tool can enforce
   (ruff, mypy, ESLint, `tsc`, permissions) are in the configs, not in prose.
3. `SKILL.md` tells Claude how to run it: what to ask, the command, how to handle failures.

## What a new project gets, and why

The skill writes files, sets up git and GitHub, and creates a conda environment named after the
project (Python 3.12). For a project with the `python` module it also installs the Python tools
(pytest, pytest-cov, hypothesis, mypy, ruff, python-dotenv) into that environment and pins the versions pip
actually installed in `requirements.txt`, so the hooks work from the first commit. It installs
nothing else: the JavaScript tools are installed with `npm install` afterwards, from the pinned
`package.json`.

The idea behind the files: Claude follows written rules most of the time, but not always, and every
line of `CLAUDE.md` costs context in every session. So each rule a tool can check goes into that
tool's config, where it is enforced on every run, and `CLAUDE.md` keeps only what no tool can check.

### Every project

| File | What it is | Why |
| --- | --- | --- |
| `CLAUDE.md` | The rules Claude always loads: workflow, project facts, how to work. About 140 lines. | Claude Code reads it at the start of every session. Anthropic advises keeping it under 200 lines: a longer file uses more context and is followed less reliably. |
| `.claude/rules/*.md` | The other rules, one file per topic, each with `paths:` globs. `code-quality.md` (code smells, architecture, naming, configuration, test code, errors) loads for `src/`, `tests/`, `scripts/` and `main.py`, and `readme.md` for `README.md`. The other files depend on the modules. | A rule file loads only when Claude touches a matching file, so the Python rules cost nothing while Claude edits CSS. |
| `.claude/settings.json` | Claude Code permissions. Allowed without asking: git status, diff, log, add, commit, push, `check.py`, `spec_coverage.py` and `cleanup.py`, and the steps of a milestone in chat: `git switch -c milestone/*`, `git switch main`, `git merge --ff-only milestone/*`, `git branch -d milestone/*`, and `milestones-runner.py --tests-only` and `--review-only`. Asks first: editing `CLAUDE.md`, the spec, the workflow and this file; editing the check configs (`ruff.toml`, `mypy.ini`, `pytest.ini`, `.coveragerc`, `package.json`, `tsconfig.json`, `eslint.config.js`, `.prettierrc.json`, `.stylelintrc.json`) and the hook files (`.githooks/`, `scripts/check.py`, `scripts/spec_coverage.py`, `scripts/run-check.sh`), so a check cannot be loosened to make it pass; installing packages; deleting folders; killing processes. Denied: force push, `git reset --hard`, `git clean`, `git restore`, deleting Docker volumes, skipping the git hooks (`--no-verify`, `commit -n`, `core.hooksPath`), and the PowerShell cmdlets `Set-Content`, `Out-File` and `Add-Content`, which write in the ANSI code page on Windows PowerShell 5.1. Each rule is written twice, as `Bash(...)` and `PowerShell(...)`. Also the edit hook: after every `Edit` or `Write`, it runs `scripts/check.py --edited` on that file. | Routine steps run without prompts, and commands that destroy work cannot run at all, even in bypass mode. A rule here is enforced; a rule in `CLAUDE.md` is only advice. An `ask` rule refuses when nobody can answer, so an unattended milestone cannot edit the spec or the workflow. On Windows, Claude Code may run commands with its PowerShell tool, which `Bash(...)` rules do not cover. The edit hook makes Claude fix lint errors as it writes, not at the end. |
| `scripts/check.py`, `scripts/run-check.sh` | The checks: `ruff check`, `ruff format --check` and `mypy` (with `ruff.toml`); `npm run lint`, `typecheck`, `format:check` (Prettier) and `lint:css` (Stylelint) with `package.json`, each once there are files for it to check; four checks that the script does itself: each staged text file is UTF-8, the docs a person reads (`README.md`, `CLAUDE.md`, `docs/*.md`) are plain English by `scripts/ste_lint.py` (at most 2.5 marks for each 100 words, and no sentence of 12 words or more in two docs; `CLAUDE.md` is left out of that last check, because its Project section repeats the purpose and the stack of `README.md` on purpose), one class per file in `src/`, and the module boundaries of `docs/design.md` (the imports of the Python and the JavaScript files in `src/`); and the tests: pytest with the 80% branch-coverage floor, and `npm test`. It prints one line for each check (`passed`, `failed`, or `skipped` with the reason), and `No check applied.` when the project has none. Code in `src/` with no test fails, and a test under `tests/live/` does not count as a test. When every staged file is under `docs/`, the tests are skipped and the other checks still run: a commit of the plan alone (a blocked milestone, an approval) cannot change a test result. With `--edited` it checks one file: ruff, ESLint, Stylelint and Prettier fix what they can, and the rest goes back to Claude, also a second class in the file. `run-check.sh` finds the project's conda Python (the active environment, or `envs/<name>` under conda's folder) and runs `check.py` with it. | One command runs every check the extensions show in the editor, and both hooks use it. The line for each check shows which checks ran, so a check that did not run never counts as a pass. `python` alone is not reliable in hooks: on Windows it can be the Microsoft Store stub, and Claude Code's shell may not have the environment active. |
| `.githooks/pre-commit` | Runs `scripts/run-check.sh`. A failing check or test refuses the commit. `init_project.py` turns it on with `git config core.hooksPath .githooks` after the first commit; after a fresh clone, the new README says to run that once. | Lint errors, type errors and failing tests cannot reach the history, from Claude or from you. The workflow already tells Claude to run the tests before a commit; the hook makes sure, for every commit. If a tool is missing (before `npm install`, for example), it refuses the commit and names the tool. |
| `.gitattributes` | LF line endings for every text file, on every machine. | The hook scripts fail under `sh` with CRLF endings, which git on Windows (`core.autocrlf=true`) would otherwise give them. |
| `docs/workflow.md`, `spec.md`, `design.md`, `plan.md` | The working loop (copied) and its three documents (filled in with the name and purpose). The loop: spec, design, plan, then one milestone at a time, each in its own branch, in a test session, a build session and a review session, and merged by the runner. `spec.md` is the full requirements template: scenarios, EARS requirements, acceptance examples, open questions and the approval record. The acceptance examples list the cases of each scenario, the most likely ones first, and each example gets a test. `design.md` gives each decision a Status: `Decided` (you chose or confirmed it), `Proposed` (Claude derived it) or `Superseded`; the design is approved when no decision is `Proposed` and no design question is open. It holds one diagram of the components, a table of module boundaries that `check.py` enforces, and a table that gives each requirement a test level. `plan.md` lists the milestones in a table, "Milestones at a glance", with the model, effort, human test and status of each, and holds one block per milestone, and at its end the live checks with your approval and budget ceiling ("Live checks"). When a milestone needs your decision (a spec change, a dependency the design does not name, a forbidden action, real user data, a test that looks wrong), Claude sets its Status to `blocked`, adds a **Blocked** entry with the question to its block, and commits nothing: the runner keeps the work in the milestone branch and commits the plan alone on the base branch. You add an **Approval** entry, set the Status to `approved`, and commit; the next run reads your approval and goes on from the work that the branch kept. Everything else a milestone decides itself: it takes the most conservative option, records a design change as a `Proposed` decision marked "auto-decided in M<n>, review", and reports it as a `DECISION:` line for you to review after the run. | `/write-spec` writes the spec, `/write-design` the design, then a plan, one milestone at a time. Claude works from these files instead of from memory of past sessions. Only the spec is locked in a milestone, so an unattended run stops for a requirement, not for a detail. |
| `docs/workflow.html` | The loop of `workflow.md` as a diagram (copied): one page, no dependencies, opened in a browser. `/sherpa` at the top, then Spec, Design, Plan, then the test, build and review sessions of a milestone and the runner's merge. A click on a step opens a panel: who does it, what it produces, what enforces it. Each section of a panel folds. The page also holds the philosophy of the workflow: one sentence under the title, and seven principles under the diagram. | You see the whole loop, and where the approvals and the checks are, before you read the rules. `workflow.md` owns the rules; the page only shows them. |
| `docs/unapproved-ideas.md` | A list of ideas for later that nobody approved, one line each (copied). You add to it, or ask Claude to note an idea. `/sherpa` routes an idea you take up to the skill that fits it, and that skill deletes its line. | An idea needs a place that is not the spec. Nothing is designed, planned, tested or built from this file: an idea becomes work only through the loop, with the approval its step needs. |
| `.claude/skills/sherpa/`, `write-spec/`, `write-design/`, `write-plan/`, `write-tests/`, `code-review-sherpa/`, `find-bugs/` | Seven project skills, copied as they are. `/sherpa` is the way in: it reads the state of the docs and what you ask, names the step of the loop that comes next, starts the skill of that step, and stops; it also notes an idea for later, and reports where the project stands. `/write-spec` interviews you one question at a time and writes `docs/spec.md` (a glossary of the domain terms, EARS requirements with stable IDs, scenarios, acceptance examples), each requirement written so that a test can be built from it before the design exists. `/write-design` turns the approved spec into `docs/design.md` (decisions with `DEC-NNN` IDs, architecture, the data model as one Mermaid `erDiagram`, interfaces, and the test level of each requirement: `unit`, `e2e`, `ui` or `live`). `/write-plan` turns the approved spec and design into `docs/plan.md`: a table of milestones with model, effort and status at the top, and a block per milestone with its tests and how to build it; a fix of behavior the spec already states is one milestone. `/write-tests` writes the failing tests of one milestone from the spec and the design, without reading `src/`. `/code-review-sherpa` reviews the diff of one milestone against the spec, the design and a checklist (four standards and a short list of 8 code smells), without changing a file, and reports each finding as a `FINDING:` line. `/find-bugs`, before a release, compares the code changed since the last release with the spec and the design, with most attention on the lines that no test runs, and writes each bug as a fix milestone for you to approve. Each skill ends by telling you the next one to run. Start them in a new Claude Code session: skill files created after a session starts load only in a new one. The first four are interactive; `milestones-runner.py` uses `/write-tests` and `/code-review-sherpa`. | The spec, design and plan are written by a method, not improvised: Claude asks instead of guessing, and nothing is built from a requirement or a design that was never approved. |
| `README.md` | Filled in with the name, purpose, stack, folder table, setup, run and test commands. | Every project starts with a README that says how to set it up and run it. |
| `.gitignore` | Ignores secrets (`config/.env`), data, models, logs, caches, `node_modules`, releases (`dist/`), local settings. | Secrets and large or generated files never reach GitHub. |
| `config/.env.example` | The list of settings, with secrets left empty. | Copied to `config/.env`, which is never committed, so settings live in one place and secrets stay out of the code. |
| `config/test-writer.json` | The AI that writes the tests (`claude`, `antigravity`, `codex` or `copilot`), with its recommended model and effort. Written by the builder from `--test-writer`. | A model of another family can catch faults that the model of the build session does not see. In the second trial (`trials/test-writers/`), Claude, Codex and Antigravity passed every gate in all their runs and caught the same median of seeded bugs; Claude stays the default because it was the fastest. The runner reads the file; `--test-writer` overrides it for one run. |
| `.vscode/settings.json` | Format on save, UTF-8, LF line endings, ruff for Python, Prettier and ESLint fixes for JavaScript, mypy with `mypy.ini`, pytest in `tests/`. The default terminal is cmd, and each new terminal runs `conda activate <project name>`. | The editor applies the same checks as the command line while you type, and every terminal starts in the project's environment, so nothing is installed into `base` by mistake. |
| `.vscode/extensions.json` | Recommends extensions for the modules you chose: Python, Ruff and Mypy with `python`; ESLint and Prettier with `javascript`; Prettier and Stylelint with `html-css` or `ui-design`. Error Lens and SonarLint for every project. Built by `build_instance.py`, not copied. | VS Code offers to install them when the project opens; nothing installs them without your click. A project gets only the extensions its files use. |
| `.github/workflows/check.yml`, `.github/workflows/mutation.yml` | `check.yml` (every project): at each push, a clean Linux machine installs the project from `requirements.txt` (and `npm ci` for JavaScript, with the Playwright browsers when the project has `ui` tests) and runs `python scripts/check.py`. `mutation.yml` (Python and JavaScript projects): a manual workflow that runs `mutmut` or Stryker on the files changed since the last release, and keeps the surviving mutants as an artifact for `/find-bugs`. | A dependency that is installed on your machine but missing from the dependency file fails at the next push, not at the next clone. Mutation tests find the tests that no change of the code breaks, but they take long, so they run only on demand. |
| `scripts/dashboard.py` | `python scripts/dashboard.py` serves one HTML page on 127.0.0.1 and opens the browser (`--out <file>` saves it instead). Sections: Needs you (a draft spec, `Proposed` decisions, open design questions, blocked milestones with their question, problems of `spec_coverage.py --consistency`, untested requirements, uncommitted docs, the `DECISION:` and kept `FINDING:` lines of the runner logs, unapproved ideas), Plan and releases, Trace (each requirement to the design rows that cite it, its milestone from the plan or from the commit that finished it, its tests and the modules whose docstring cites it), and Code map (a box for each file of `src/`, the imports against the table of module boundaries, the class list). Standard library only; the Refresh button reads the files again. It never shows a bare ID. | You see the state without reading four files and git. Each fact still has one owner: the page holds none of its own, and writes nothing. |
| `scripts/milestones-runner.py` | Runs the open milestones of `plan.md` in order. Each one runs in its own branch, `milestone/M<n>`, in unattended `claude -p` sessions with the model and effort of its row (`haiku`, `sonnet` or `opus`, meaning the latest of that family, or a full model ID such as `claude-sonnet-5-5` to pin a version): a test session, a build session that may not edit `tests/` and commits without a push, and a review session. The test session runs in a temporary folder with the docs, the rules, the tool configs and `tests/`, but no `src/` and no `.git`; the AI of `config/test-writer.json` writes the tests (Claude by default; Antigravity, Codex or GitHub Copilot with `--test-writer` or at `/project-init`). The runner copies `tests/` back and checks them itself: ruff and mypy, the reason of each new failure from `--junitxml` (a wrong value, or a missing module that the Owner names), and the older tests; a problem goes back to the writer once, with its error type and message. The review runs in a temporary git worktree, so it cannot change the branch. A finding about `tests/` goes to a test session (and, if a test changed, a build session commits `M<n>: test repairs`), any other finding to a repair session; then a last review runs. A finding of that last review that is `high`, or `medium` with a requirement ID as its rule, blocks the milestone (a `low` finding never blocks, and the review rates wrong behavior against a requirement `high`): the runner writes the Blocked entry into the plan on the base branch. After your approval the next run rebases the branch and gives your decision and the findings to a repair session: when it changes nothing, the runner merges the code you saw; when it commits a change, the last review checks that change, and its findings block as usual. A repair or rebuild session that finds a test wrong reports a `BLOCKED:` line: the runner keeps its work as `M<n>: partial work` and blocks the milestone in the same way, and after your approval a test session gets your decision before the build goes on. The other findings are counted. `--tests-only M<n>` and `--review-only M<n>` run the test session and the review alone, for a milestone in chat. Then the runner itself merges with `git merge --ff-only`, pushes the base branch and deletes the milestone branch. Checks first: the project's conda environment is active and `python` on the PATH of a session is its Python (each session gets the folders of the environment first on its PATH), `.claude/settings.json` exists, the commit hook is on, git is clean, the branch pushes to a remote, each milestone row has its six cells, `spec_coverage.py --consistency` passes, and a test writer other than Claude answers one short prompt. After the build session and after a repair: the row left the plan, git is clean, no file in `tests/` changed after the test session, `spec_coverage.py M<n>` passes, and `docs/spec.md` is as it was. A milestone with a **Human test** entry stops the run after its merge: the runner prints the entry and goes on only when you answer `yes`. When a session blocks its milestone, the runner keeps the work in the milestone branch (a commit `M<n>: partial work`), commits the plan alone on the base branch (`M<n>: blocked`), pushes, and prints the question (when git refuses that commit or that push, the runner says how to finish the step by hand); after you approve and commit, run it again and the milestone goes on from that work. A session that did not finish, or ran over `--timeout-minutes` (default 90), is tried again (`--retries`, default 1) from the changes it left, and gets the reason for the failure; after the last try the runner stops, and `--resume` starts the next run on that dirty tree. When the milestones are done, it runs `live_checks.py` and prints the result. A live table shows each milestone with its duration, its counts of `DECISION:` and `FINDING:` lines and its result, the planned milestones of the range in dark grey, a Total row and a progress bar; logs and timings in `.claude/logs/`. `--start N`, `--end N`. | A planned list of milestones runs without you, in fresh sessions, so no session carries another's context. The tests are not written by the session that must pass them, and the code is not reviewed by the session that wrote it. The base branch gets only commits that passed every check, because a script merges, not a session. The hooks still check every commit, and the runner stops instead of guessing. |
| `scripts/spec_coverage.py` | Lists each requirement ID and each acceptance example of `docs/spec.md` as tested (a test under `tests/` has the ID in its name), manual (a `Manual:` entry of the plan names it), planned or missing. With `M<n>` it checks the requirement IDs in the Refs of that milestone and the acceptance examples that cite them: each must be in the spec, and be tested or manual. With `--consistency` it checks that the spec, the design and the plan agree: each ID in a Refs entry, in a Tests first entry and in the test design table is a row of its document, and each requirement has a test level. It only reads files. | Requirement coverage is the primary measure of the tests, and line coverage cannot show it. The milestone runner uses it as a gate, and runs the consistency check before the first milestone. |
| `scripts/live_checks.py` | Runs the tests in `tests/live/`: the ones that call a live external service (a paid API, an LLM) with a test account. It runs them only when `docs/plan.md` holds your approval and a budget ceiling under "Live checks", and gives the ceiling to the tests in `LIVE_BUDGET_CEILING`. It prints one line: passed, failed or not run. The runner starts it after the milestones of a run. | A fake proves that the code agrees with the fake. A live check proves it against the real service, with no AI session, and only within the budget that you approved. |
| `scripts/release.py`, `docs/releases.md` | `python scripts/release.py M<n>` makes a release that holds every milestone up to M<n>. The version is the date (`YYYY.MM.DD`, then `.2` for a second release on the same day). It builds `dist/<project>-<version>.zip` from the commit of M<n> with `git archive`, adds the installed versions (`versions/pip-freeze.txt`, and `versions/npm-ls.txt` with a `package.json`) so the release can be installed again with the same versions, tags that commit `v<version>`, adds a row to `docs/releases.md`, commits and pushes. `--dry-run` shows the steps and changes nothing. | A release is a cut point on a branch where every commit passed the checks, so a version always names code that was tested. You start it, and no AI session runs. A version belongs to a release, not to a milestone. |
| `scripts/cleanup.py` | Deletes caches and generated files (`__pycache__`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache`, coverage, logs). Never source, data or environments. `--dry-run` lists only. | One safe command Claude may run without asking. |
| `src/`, `tests/unit/`, `tests/e2e/` | Empty starting folders (each holds a `.gitkeep`). | Every project has the same layout, which the rules and configs assume. |

### With the `python` module

| File | What it is | Why |
| --- | --- | --- |
| `ruff.toml` | Linter and formatter config: line length 100, docstrings, type annotations, import order (`src` is first-party, whether or not its files exist yet), imports only at the top of a file, naming, security checks, no `print` outside `scripts/`, no TODO comments, pathlib, and limits on complexity (8), arguments (4) and statements per function (15). | Ruff checks style, common bugs and code smells in well under a second, so Claude can run it after every change. The limits keep functions small. |
| `mypy.ini` | Type checker config: `strict = True` on `src/`. | Strict typing finds wrong types and missing `None` checks before the code runs, and typed code is easier for Claude to change safely. |
| `pytest.ini` | Test config: tests live in `tests/`, async tests run without decorators, and a normal run skips `tests/live/`. The test command requires 80% branch coverage. | Tests prove a change works. The coverage floor stops untested code from growing. |
| `.coveragerc` | Coverage config: `patch = subprocess` also measures the Python processes that a test starts. | An end-to-end test that runs `main.py` as a process counts for the coverage floor. Without it, a correct project with such tests failed the floor in the trial of the test writers. |
| `requirements.txt` | pytest, pytest-cov, hypothesis, mypy, ruff and python-dotenv, each pinned with `==`. With `--no-conda`, or if the install fails, only a comment naming them. | The skill installs the latest versions into the new environment and pins what pip installed, so it never guesses a version, and a clone gets the same tools. |

### With the `javascript` module

| File | What it is | Why |
| --- | --- | --- |
| `package.json` | Dev-only tools, pinned: ESLint, TypeScript, Node types, Prettier, Stylelint. Scripts: `typecheck`, `lint`, `lint:css`, `format:check`, `test` (it skips `tests/live/`). Also with `html-css` and `ui-design`. | The app itself has no dependencies and no build step. These tools only check the code. |
| `.prettierrc.json`, `.stylelintrc.json` | Prettier formats JavaScript, CSS and HTML at line length 100 (as ruff does). Stylelint checks CSS with its standard rules, BEM class names, and no color value outside `theme.css`. Also with `html-css` and `ui-design`. | The formatting and CSS the editor extensions show are checked by the hooks too, so they cannot drift. |
| `tsconfig.json` | Type-checks plain JavaScript (`checkJs`, `strict`) without compiling. | Type errors are found in `.js` files without switching to TypeScript. |
| `eslint.config.js` | ESLint rules: the same size limits as ruff, one class per file, `const` over `let`, `===`, no TODO comments, no `console` outside `log.js`, no `fetch` outside `api.js`, no `innerHTML`. | It enforces the JavaScript rules from `CLAUDE.md`, including the ones that keep unsafe HTML out. |

### With other modules

Most modules add only a rules file under `.claude/rules/`. Some also add folders: `data` adds
`data/`, `llm` adds `models/` and `prompts/`, `static-site` adds `content/` and `site/`, and the
`html-css` and `ui-design` modules add `tests/e2e/ui/`. `docker` adds `.dockerignore`, which keeps
secrets, data, models, caches, tests and docs out of the image.

## Stack

Python 3.12 (this repository's conda environment, `sherpa`). The scripts use only the standard library. They were
checked with ruff 0.17.0 and mypy 2.4.0 using the configs in `assets/`.

## File structure

```text
CLAUDE.md                       instructions for working on this repository
docs/
  completion-plan.md            the plan to finish sherpa, with a record line for each step
  unapproved-ideas.md           Part 1: what is left of the approved changes. Part 2: proposed
                                changes, not approved
  v1/ to v4/                    SDD report, presentation and demo; v4 is the current workflow
skills/project-init/            the skill. Install by copying this folder.
  SKILL.md                      what Claude reads: steps, questions, failure handling
  scripts/
    init_project.py             folder, git, GitHub: the entry point
    build_instance.py           builds the files; holds the section-to-file map and path globs
  assets/                       everything a new project receives, laid out as in a project
    CLAUDE_GOLDEN.md            the master, in tagged sections. Never copied.
    CLAUDE_GOLDEN.md.646        the master before the cut to the line budget. Reference only.
    docs/                       workflow.md, workflow.html, unapproved-ideas.md, releases.md (copied); spec, design, plan (filled in)
    .claude/skills/             sherpa, write-spec, write-design, write-plan, write-tests, code-review-sherpa (copied)
    scripts/cleanup.py          cache cleaner (copied)
    scripts/check.py            the checks both hooks run (copied)
    scripts/spec_coverage.py    which requirement has a test, and do the docs agree (copied)
    scripts/ste_lint.py         plain English in the docs: an MIT port of ste-lint (copied)
    scripts/dashboard.py        the state of the project on one page (copied)
    scripts/live_checks.py      runs the tests that call a live service (copied)
    scripts/release.py          cuts a release: version, archive, tag, record (copied)
    scripts/milestones-runner.py  runs the plan unattended (filled in)
    scripts/run-check.sh        finds the project's Python, runs check.py (filled in)
    .githooks/pre-commit        the git hook (copied)
    README.md, requirements.txt, config/.env.example    (filled in or copied)
    ruff.toml, mypy.ini, pytest.ini, .coveragerc        Python checks
    package.json, tsconfig.json, eslint.config.js       JavaScript checks
    .gitignore, .gitattributes, .dockerignore, .claude/settings.json, .vscode/
tests/                          the test suite (not installed with the skill)
  fake_gh.py, fake_conda.py     stand in for the GitHub CLI and conda; never touch the real ones
  helpers.py, conftest.py       the sandbox: project folder, bare remote, isolated git config
  test_assets.py                the assets match what the builder expects
  test_build_instance.py        what the builder writes and leaves alone
  test_init_project.py          init end to end, and every refusal
  test_checks.py                check.py and both hooks, with the real ruff, mypy and pytest
  test_spec_coverage.py         which requirement has a test, on a small spec, design, plan and tests
  test_live_checks.py           the live checks: approval, budget ceiling, result
  test_release.py               a release, on a git project with a bare remote
  test_runner.py                the milestone runner, with a fake claude
  fake_claude.py                stands in for `claude -p`: the sessions of a milestone
trials/test-writers/            two trials of the test writers, kits and results (not collected)
pytest.ini                      points pytest at tests/ and the skill's scripts
```

`assets/CLAUDE_GOLDEN.md.646` is the master as it was before it was cut from 646 lines to 525, so
that the always-loaded `CLAUDE.md` would fit under 200 lines. The name records its line count. It
is kept so you can see the full wording of rules that were shortened or dropped, and bring one back.
Nothing reads it: `build_instance.py` reads only `CLAUDE_GOLDEN.md`, and new projects never get it.
Do not edit it.

## How to use

First set up the machine, once. Then start each new project.

### Set up the machine (once)

#### 1. Install the skill

1. Copy `skills/project-init` to `%USERPROFILE%\.claude\skills\project-init`.
2. Delete the old `%USERPROFILE%\.claude\skills\project-docs-init`. This skill replaces it.
3. After every change to the skill, copy it again.

#### 2. Set up GitHub

1. Install the GitHub CLI:

   ```bat
   winget install GitHub.cli
   ```

2. Open a new terminal. The old one does not see the new PATH.
3. Log in:

   ```bat
   gh auth login
   ```

4. Check that git has `user.name` and `user.email` set.

If winget fails with `0x8a15000f` (data required by the source is missing):

1. In an administrator terminal, run:

   ```bat
   winget source reset --force
   ```

2. Install again (step 1).

#### 3. Set up conda

1. Install Miniconda.
2. Set it up for cmd, once, so that `conda activate` works in the VS Code terminal:

   ```bat
   conda init cmd.exe
   ```

You do not create a conda environment for a new project. The skill creates it, named after that
project.

### Start a new project

Do "Set up the machine" above once. Then, for each new project:

#### 1. Create the project folder

1. Create an empty folder for the project, for example `C:\alkashef\GitHub\my-app`.
2. Open it in VS Code (File > Open Folder). The folder may hold only `.git`, `.claude` and
   `.vscode`. A repository with commits is refused, because the skill is for new projects.
3. Open Claude Code in that folder (the VS Code extension, or `claude` in the VS Code terminal).

#### 2. Run the skill

1. Type `/project-init`, or just say "start a new project".
2. Answer its questions. It proposes a default for each:
   - *Project name*: the GitHub repository name and the conda environment name. Default: the
     folder name.
   - *Purpose*: one line. It goes into `CLAUDE.md`, the spec, the README and the repository
     description.
   - *Modules*: what the project has. It proposes some from your purpose. Default: `python`.
   - *Visibility*: private unless you say public.

   | Module | Add when the project has |
   | --- | --- |
   | `python`, `javascript` | Python code, JavaScript or TypeScript |
   | `html-css`, `ui-design` | a browser front end, a user interface |
   | `http-apis`, `cli`, `mcp` | an HTTP API, a command-line interface, an MCP server or host |
   | `data`, `llm` | data files or a store, LLM calls or local models |
   | `logging`, `long-running`, `validation` | logging, async jobs, user-input validation |
   | `static-site`, `docker` | a Markdown-to-HTML site, Docker |

3. Wait for it to finish. It checks everything first and changes nothing if a check fails. Then it
   runs `git init`, builds the files, creates the conda environment and installs the Python tools
   (about a minute), makes the first commit (the whole scaffold), turns on the pre-commit hook,
   creates the GitHub repository, and pushes `main`. It ends by printing the repository URL and the
   environment.

#### 3. Start a new Claude Code session

1. Open a new conversation in the same folder. `CLAUDE.md`, the rules, the permissions, the edit
   hook and the project skills (`/sherpa` and the rest) were created after the first session
   began, so only a new one loads them.
2. If Claude Code asks whether you trust the folder, say yes. Until you do, it ignores the
   project's `allow` rules (the `ask` and `deny` rules still apply).

#### 4. Finish the setup

The skill's report lists these.

1. JavaScript, HTML or CSS: open a new VS Code terminal and run `npm install`. Until then, the
   pre-commit hook refuses every commit that has web files to check, and says so. (The Python
   tools are already installed.)
2. Check that the tools are found. In a new VS Code terminal (cmd, with the project's environment
   active), run:

   ```bat
   python scripts/check.py
   ```

   It should print `All checks passed.` If it names a tool, that tool is not installed yet.

3. Install the recommended VS Code extensions. VS Code may not offer them, because
   `.vscode/extensions.json` appeared after the folder was opened: in the Extensions view, search
   `@recommended` and choose *Install Workspace Recommended Extensions*.
4. Check the **Project** section of `CLAUDE.md` and the layout table in `docs/design.md`.

#### 5. Write the spec, the design and the plan

`/sherpa` is the way in at every step: it reads the state of the docs, names the step that comes
next, starts the skill of that step, and stops. You can also type the skill of a step yourself.

1. In the new session, type `/sherpa` (or `/write-spec`). Claude interviews you about the project
   and writes `docs/spec.md`.
2. Approve the spec, then type `/sherpa` (or `/write-design`). Claude writes `docs/design.md`.
3. Approve the design, then type `/sherpa` (or `/write-plan`). Claude shows the milestones table
   (model, effort, status); after you approve it, Claude writes `docs/plan.md`.
4. From there the loop is in `docs/workflow.md`: spec, design, plan, one milestone at a time.
   `docs/workflow.html` shows it as a diagram: open it in a browser, and click a step.
   For a change, a fix, or "what is next", type `/sherpa` and say what you want.
5. An idea for later: say "note this idea", or add a line to `docs/unapproved-ideas.md`.
   Nothing is built from that file until you take the idea up with `/sherpa`.

#### 6. Run the planned milestones (optional)

1. In the project terminal, run:

   ```bat
   python scripts/milestones-runner.py
   ```

2. It stops at the first milestone that fails or needs a decision, and prints why. To continue
   a milestone that did not finish, run it again with `--resume`.
3. After the run, read the `DECISION:` lines in `.claude/logs/` and the `Proposed` decisions in
   `docs/design.md`: confirm or revert each. Then do the "Human checks" at the end of the plan.

Before a run, `docs/workflow.md` ("Running milestones unattended") lists what to check so that
it does not stop for something known in advance.

#### If it stops with an error

Nothing was deleted. The usual causes:

- `gh` is missing or not logged in: run `winget install GitHub.cli`, then `gh auth login`.
- The folder holds other files.
- The repository name is taken: rerun with `--name`, or tell the skill another name.
- git has no `user.name` or `user.email`.
- conda is not installed: install Miniconda, or rerun with `--no-conda`.
- conda or pip fails partway (no network, for example): the project is still committed and pushed,
  and the error says the commands to run by hand.

## How to contribute

You need this only to change the skill or run its tests. `sherpa` here is this repository's
own environment, not a new project's.

### Set up the environment

1. Create the environment, once:

   ```bat
   conda create -n sherpa python=3.12
   ```

2. Activate it and install the tools, once:

   ```bat
   conda activate sherpa
   pip install ruff==0.17.0 mypy pytest pytest-cov
   ```

3. After that, each time you work here, only activate it:

   ```bat
   conda activate sherpa
   ```

### Run the scripts alone

From `skills/project-init/`:

```bash
python scripts/init_project.py --with python http-apis --purpose "Does X"   # in the new folder
python scripts/build_instance.py <folder> --with python --dry-run           # list only
python scripts/build_instance.py --list-modules                             # the module table
python scripts/build_instance.py <folder> --add data cli                    # add modules later
```

`--with` modules: `logging`, `llm`, `long-running`, `validation`, `python`, `javascript`,
`html-css`, `ui-design`, `http-apis`, `data`, `cli`, `static-site`, `mcp`, `docker`. Existing files
are never overwritten unless `build_instance.py` gets `--force`. `--list-modules` prints the
numbered table of the modules that `/project-init` and `/write-design` show. `--add` gives a
project that exists one more module: its rules file (a file named after the module when the
shared rules file exists), its config files and its folders, and no existing file changes.

### Change what new projects get

Edit `assets/`. For the rules, edit `assets/CLAUDE_GOLDEN.md`, keep its section tags, and keep the
always-loaded set (`always_loaded()` in `build_instance.py`) under 200 lines once built.

A new language needs four places: a module section in `CLAUDE_GOLDEN.md` and its entry in the
builder (`optional_flags()`, `rule_files()`, `template_files()`), its commands in
`assets/scripts/check.py`, its test-name pattern in `assets/scripts/spec_coverage.py`, and its
config files in `assets/`. Add one only when a project needs it.

### The line budget

The built `CLAUDE.md` must have fewer than 200 lines, counting every line, blank lines included. It
is about 140 now, after the audit of its rules (`docs/audit-claude-golden.md`). The test suite checks this on a build with every module.

- *Why every line:* Anthropic's advice to keep `CLAUDE.md` under 200 lines counts the file as it
  is. Skipping blank lines would let the file pass the test at well over 200 real lines.
- *Why only `CLAUDE.md`:* it loads in every session. A rules file loads only when Claude touches a
  matching file, so it has no limit. Keep rules files short anyway: several can load at once (a
  `.js` file loads both `javascript.md` and `ui-design.md`).
- *If the test fails:* shorten a section, or move one out of `always_loaded()` into a rules file
  in `rule_files()`. Do not raise the limit.

## How to test

### The test suite

From the repository root:

```bash
conda run -n sherpa python -m pytest
```

It runs in about 20 minutes and needs only git. With `pytest-xdist` in the environment,
`python -m pytest -n 12` runs it in about 3 minutes. Each test works in its own temporary folder, with
its own git config, a fake `gh` (`tests/fake_gh.py`) that answers the three calls the skill makes
and adds a local bare repository as `origin`, so every push is a real git push, and a fake conda
(`tests/fake_conda.py`) that lists and "creates" environments without touching conda. Your own git
config, GitHub account and conda environments are never touched.

- `test_assets.py`: every asset the builder lists exists; every section of `CLAUDE_GOLDEN.md` goes
  into `CLAUDE.md` or a rules file; every `Bash(...)` permission rule has a `PowerShell(...)` twin;
  the edit hook is set up; editing a check config, a hook file, the spec or the workflow asks
  first; the project skills are the six slash commands, and every file of a skill is linked
  from its `SKILL.md`; `/sherpa` routes to every other skill; a milestone has a test session, a
  build session and a review session; the review checklist holds the 8 smells and never
  proposes polymorphism for a conditional; the plan table has the Human test column; the
  workflow page holds the philosophy; the workflow page (`docs/workflow.html`) names every skill and script of the
  workflow, each of its cards has a panel, and its stamp is the SHA-256 of `docs/workflow.md` (a
  change to the workflow fails until the page is read, corrected and stamped with the hash that
  the test prints); the test levels are the same in the workflow and
  the skills; unapproved ideas are never built from; and no asset keeps the wording of another
  project.
- `test_build_instance.py`: which files each build writes, no `{{placeholders}}` left, rules files
  start with `paths:`, `--dry-run` writes nothing, a second run keeps existing files, `--force`
  overwrites, an unknown module is refused, the recommended extensions follow the modules (a
  Python-only project gets no ESLint, Prettier or Stylelint), and `CLAUDE.md` has fewer than 200
  lines (see "The line budget").
- `test_init_project.py`: a run commits once on `main` and pushes; the repository is created
  private (or `--public`) with the purpose; `--no-github`, `--remote-url`, an existing empty
  repository and an existing `origin` work without calling `gh`; a failed push says how to finish;
  the conda environment is created with the project's name, kept if it exists, skipped with
  `--no-conda`, and a failed create says how to finish; a Python project gets its tools installed
  and pinned in the first commit, other projects get none, and a failed install says how to
  finish; and each of ten refusals stops with its message and changes nothing in the folder.
- `test_checks.py`: init turns on the pre-commit hook and marks the hook scripts executable; the
  scripts have LF endings; `check.py` passes on a new project and fails on a lint error; after an
  edit it fixes the file and sends the rest back as a `block` decision, and ignores other files; a
  missing tool is named; the tests run once there are some, and a failing one fails the check; a
  commit of files under `docs/` alone skips the tests but not the other checks; each check has
  its line (`passed`, `failed` or `skipped`), and a project with no check says so; code with no
  test fails, and a live test does not count as a test; a second class in a file fails, in the
  full run and after an edit; an import inside a function fails; an import that the table of
  module boundaries does not permit fails, in Python and in JavaScript; a test that runs a
  process passes, and the code that it reaches counts for the coverage floor; a staged file that
  is not UTF-8, or holds U+FFFD, fails; and a real `git commit` is refused by the hook, then
  accepted once fixed.
- `test_spec_coverage.py`: each requirement is listed as tested, manual, planned or missing;
  examples, decisions and withdrawn rows are not requirements; a milestone passes when each
  requirement in its Refs has a test or a `Manual:` entry, and fails for one without, or for one
  that is not in the spec; a test name must carry the whole ID; a web test carries it in its
  title; an acceptance example is listed and checked as a requirement is; and `--consistency`
  finds an ID that is not a row of its document and a requirement without a test level, and
  ignores text such as "SHA-256" outside the fixed places.
- `test_live_checks.py`: no test in `tests/live/`, or no approval with a budget ceiling in the
  plan, means not run; a placeholder is not an approval; the tests get the ceiling in
  `LIVE_BUDGET_CEILING`; the result is passed or failed; a normal pytest or `npm test` run
  skips `tests/live/`; and the script changes no file.
- `test_dashboard.py`: the page shows what needs you, the trace of each requirement (also to a
  milestone that a commit finished), the code map with a forbidden import and the class list,
  never a bare ID, and the served page reads the files again on Refresh and writes nothing.
- `test_release.py`: a release builds the archive from the commit of its last milestone, tags
  it, adds the row, commits and pushes; the version is the date, with `.2` for a second one on
  the same day; the milestones are those after the last release; `--dry-run` changes nothing;
  and a dirty tree, a milestone that is not finished, and a failed push each stop with a
  message.
- `test_runner.py`: a new project's plan template, the workflow's row template and `.gitignore`
  match what the runner reads; a row has six cells, and a plan with a row of five is refused;
  it checks the environment, the model and effort, and the prompt names the milestone and its
  commit message; the test session is denied `src/`, the build and repair sessions are denied
  edits to `tests/`, and the review session is denied every edit; each test writer runs with its
  prompts off, `AGENTS.md` holds the rules of the project, and an unknown writer is refused; a
  new test may fail only for a wrong value, an error of `src/` or a missing Owner module; a
  finding blocks the merge when it is high, or medium and names a requirement; an approval
  covers the code that the user saw; the table of the run, with
  its planned rows in grey, its Total row and its progress bar. Whole
  runs, with a fake `claude` and the real hooks: every open milestone runs in its branch, in a
  test, a build and a review session, and the runner merges it with a fast-forward, pushes and
  deletes the branch; the build session does not push; the next milestone comes from the plan
  of the base branch; a review with findings is followed by a repair and a last review, the
  findings that stay are counted, and a review that changed a file changes nothing in the
  branch (it runs in a worktree); the test session runs in a folder without `src/` and `.git`,
  a test that fails for a wrong reason gets one round of repair and stops the milestone if it
  stays wrong, and a writer that writes nothing does not count; another writer gets `AGENTS.md`
  and its own command, also from `config/test-writer.json`; a finding about a test goes to a test
  session and a rebuild; a high finding of the last review blocks the merge, and once approved
  the branch is rebased and merged; `--tests-only` and `--review-only` run one step in chat; a
  milestone
  that blocks leaves `M<n>: partial work` in its branch and `M<n>: blocked` on the base
  branch, and once approved it goes on from that work; a refused commit of the blocked plan says how to finish; a human test continues on `yes` and
  stops on another answer or on no input; the consistency check that fails stops the run at
  the start; a session that did not finish is tried again with the reason, and after the last
  try the run stops and `--resume` continues with the build session; a build session that
  changed a test, and a milestone that changed the spec, do not count; a refused fast-forward
  and a failed push say what to do; the live checks run at the end; a dirty tree is refused.
- The built `.vscode/settings.json` makes cmd the default terminal with `conda activate <name>`.

### Lint and type checks

Use the configs that new projects get, in `assets/`. Run the checks for
`assets/scripts/cleanup.py` from inside `assets/`, where it sits as it will in a new project. From
anywhere else, the `scripts/**` exception for `print` does not match it. The same goes for
`assets/scripts/check.py`, `assets/scripts/milestones-runner.py`, `assets/scripts/live_checks.py`
and `assets/scripts/release.py`, whose `S603` exceptions (they run the check tools, git, claude,
pytest and node) are in `ruff.toml`. One
line in `init_project.py` carries `# noqa: S603` (it exists to run git and gh).

```bash
# from skills/project-init/
conda run -n sherpa ruff check --config assets/ruff.toml scripts
conda run -n sherpa ruff format --check --config assets/ruff.toml scripts assets/scripts
conda run -n sherpa mypy --config-file assets/mypy.ini scripts assets/scripts
# from skills/project-init/assets/
conda run -n sherpa ruff check --config ruff.toml scripts
# from the repository root (bash; MYPYPATH lets mypy find the scripts the tests import)
conda run -n sherpa ruff check --config skills/project-init/assets/ruff.toml tests
MYPYPATH="skills/project-init/scripts;tests" conda run -n sherpa mypy --config-file skills/project-init/assets/mypy.ini tests
```

### Checked in real Claude Code sessions

Run once by hand with headless `claude -p` sessions in a project built by the skill (not part of
the suite):

- `CLAUDE.md` loads at the start of a session. `.claude/rules/python.md` loads only after Claude
  reads a `.py` file, and not after it reads `README.md`.
- The deny rules block `git clean`, `git reset --hard` and `git push --force`, even in bypass mode.
  Before the `PowerShell(...)` twins were added they blocked nothing, because these sessions ran
  commands with the PowerShell tool.
- An `ask` rule (`pip install`) blocks the command when no one can answer the prompt.
- An `Edit` ask rule holds even in accept-edits mode: asked to raise `line-length` in `ruff.toml`,
  Claude's edit waited for a permission no one gave, and the file stayed as it was.
- A reworded command gets past a deny rule: `git -C . clean -n` ran. Deny rules match the command
  text, so they stop mistakes, not a determined workaround.
- The edit hook: Claude wrote `import os` / `x=1` to `src/sample.py`. The hook removed the import,
  formatted the rest, and Claude got "Missing docstring in public module" as hook feedback. The
  first version reported through exit code 2, and Claude saw nothing: Claude Code ran the hook in
  PowerShell, which turned the exit code into 1 (a non-blocking error, not shown to Claude). Hence
  the JSON `block` decision.
- The pre-commit hook, with no conda environment active: it found the project's environment
  under Miniconda's folder, refused a commit with a lint error, and accepted it once fixed.
- The web checks, in a `javascript` + `html-css` project after a real `npm install` of the pinned
  tools: on an empty project they pass; with `var`, `==`, an unformatted page and an empty CSS
  block, ESLint, Prettier and Stylelint each fail. After an edit, ESLint and Stylelint fixed what
  they could, Prettier formatted the file, and only `==` and the empty block went back to Claude.

Also run once by hand: the skill with the real conda, in a scratch folder. It created the
environment in about 30 seconds, and `conda activate <name>` in cmd then found its Python 3.12.

Also run once by hand: the installed skill against the real `gh` 2.102.0, in a scratch folder. It
created the private repository `project-init-smoke-test` with the purpose as its description,
pushed one commit to `main` (the same commit as the local one, 32 files and folders on GitHub),
and created the conda environment. A second run with the same name in another empty folder was
refused (`already exists`) and left that folder empty.

Also run once by hand, on November 21, 2026: the runner with real `claude -p` sessions (Claude
Code 2.1.318, `sonnet`, effort `medium`), on one milestone of a project built by the skill, with a
local bare repository as the remote. Six sessions ran in 4 minutes 16 seconds: test, build,
review, repair (two tries) and last review.

- The test session ran `/write-tests`. Each review session ran the built-in `/code-review` and
  then `/code-review-sherpa`, changed no file, and reported `FINDING:` lines. The first review had
  2 findings. The repair session repaired one and rejected the other, because its remedy changes a
  file in `tests/`. The last review had 5 findings, and the runner counted them.
- The runner made the branch `milestone/M1`, merged it with a fast-forward, pushed the base
  branch and deleted the milestone branch.
- The denied tools, each one in its own session: with `Edit`, `Write` and `NotebookEdit` denied, a
  session has none of these tools. `Edit(./tests/**)` also refuses the Write tool in `tests/`.
  `Read(./src/**)` also refuses Grep in `src/`, and Glob finds no file there. Claude Code warns
  about a `Grep(...)`, `Glob(...)` or `Write(...)` rule with a path and about `MultiEdit`, so the
  runner does not use them.

The same run showed five problems. The first one is solved, and the others are not
(`docs/unapproved-ideas.md`, RUN-01 to RUN-04):

- Ruff refused `subprocess` in `tests/` (S603). The design asked for a test that runs the program
  as a process, and the test session ran it in the test process instead. `ruff.toml` now permits
  S603 in `tests/**`.
- The review found that test. The repair session may not edit `tests/`, so the finding stayed.
- The build session wrote its files with PowerShell, not with the Write tool. The edit hook did
  not run for them, and PowerShell damaged a character in `docs/plan.md`: the session repaired it
  and amended its commit. A path rule does not cover the shell, so the runner's hashes of `tests/`
  are the guard there.
- The sessions found no `python` on PATH, because the runner started from the environment's
  `python.exe` without `conda activate`, and the runner's check passed. The test session did not
  run its tests, and the first repair try did not run the Gate.
- The last review reported 3 findings that the first review left out as not sure, one of them a
  fault against a requirement. The milestone merged with them.

A second real run on November 21, 2026 used a new project with two milestones: M1 with a human
test, and M2 that the test session must block (the spec did not say what `--max 0` does). The
runner ran with the environment's folders first on the PATH, as after `conda activate`.

- The sessions found `python`, and the test session ran its tests. This solved the second
  problem of the first run.
- M1: the review found a real fault (the Kelvin sign U+212A became `k` when the code lowercased it
  before it filtered it, against SLUG-002). The repair session fixed it, and the last review said
  `NO FINDINGS`. After the merge the runner printed the human test and went on when `yes` came in
  on standard input.
- M2: the test session blocked the milestone with a clear question. The pre-commit hook then
  refused the commit of the blocked plan on the base branch. The runner stopped with the message
  of `blocked_plan_refused`, and the steps in it worked as written: correct the cause, commit,
  push, approve in the plan, run again. The approved M2 ran in 3 minutes 29 seconds, from a
  milestone branch that was behind the base branch, and merged with a fast-forward.
- The cause of the refusal was a bug. Ruff sorted the imports of a test as first-party only
  when `src/slug.py` existed. The test session writes the test before it exists, and ruff's
  cache hid the error until a checkout changed the file. `ruff.toml` now names `src` as
  first-party (`known-first-party`).
- The built-in `/code-review` ran in 3 of the 4 review sessions. In the last review of M2 the
  session wrote `BUILT-IN REVIEW: not available` and went on with `/code-review-sherpa`, as the
  prompt says. The two kinds of review do not always run together.
- A repair session rejected a finding about a missing test again (RUN-01), and its repair made a
  new public function that has no unit test. The last review reported that, and the milestone
  merged with it.

A third real run on November 23, 2026 checked version 4 (`sonnet`, effort `medium`, Claude as
the test writer) on a project built by the skill, with a local bare repository as the remote and
three milestones: M1, the slug tool; M2, Cyrillic titles, with a library that only a `Proposed`
decision named; M3, short links from an outside service. A first attempt found three faults of
sherpa; the second attempt ran after their repair, and all three milestones merged.

- Each test session ran in a folder without `src/` and `.git`. Claude wrote a Hypothesis property
  test and tests of the limits and the defaults. The runner's checks sent a test session back
  once: ruff format failed on mixed line ends.
- The reviews found real faults: a `--max` of 5000 digits passed the digit check and then broke
  the limit of Python's `int()` (SLUG-007); letters of other Cyrillic alphabets were dropped
  (SLUG-008, which the user then narrowed to the Russian alphabet); an HTTP error of the service
  escaped as a traceback (SLUG-009). In the first attempt, a title that starts with `-` was read
  as an option (SLUG-005).
- In each milestone, a finding about a test went to a test session, and a build session made the
  new tests pass (`M<n>: test repairs`).
- The last review blocked each milestone once, with a high finding or a finding against a
  requirement. The runner wrote the Blocked entry into the plan of the base branch and pushed it.
  After the approval, the next run rebased the branch, resolved the conflict of `docs/plan.md`,
  gave the decision to the repair session, and merged. M1 to M3 took 11, 11 and 16 minutes of
  sessions, with the blocks.
- The user (here, Claude in that role) added a design decision on the base branch while M2 was
  open, and the build session of M2 had taken the same number, DEC-005. The rebase stopped with
  its message, and a rebase by hand finished it.
- `/sherpa` in a real session read the state: the plan done, five `Proposed` decisions in the
  design, and the next step `/write-design`. The dashboard showed the same decisions, a high
  finding that the approval of M1 had let through, and the map of the code.
- No build session blocked. The build session of M2 replaced the library with a table of its own,
  and that of M3 called the service: both recorded an auto-decision, as the rules allow. So a
  milestone that a build session blocks with partial work is still checked only by the suite.
- The first attempt found three faults, now repaired: the plan failed the plain-docs check at its
  first commit (a milestone block counted as one long paragraph); a build session committed the
  tests in a second commit; and a rebuild session that found a test wrong could not block, so the
  run stopped on a dirty tree.
- Two new ideas, approved and built on November 23, 2026: an approval let through the new
  findings of a later review, so now it covers only the code that the user saw (RUN-08); and a low
  finding that named a requirement blocked, so now a low finding never blocks (RUN-09).

A fourth real run on November 23, 2026 checked the audited rules (a `CLAUDE.md` of 138 lines),
RUN-08 and RUN-09, with the same model, effort and test writer, on a new project: M1, the slug
tool; M2, a newsletter sign-up that sends the name and the email address of a reader to an outside
mailing-list service, a flow that only a `Proposed` decision named. Both milestones merged, and the
project's checks pass.

- Before the first session, the run found a fault of sherpa: a purpose of 12 words or more failed
  the plain-docs check at the first commit of the docs, because the builder writes it into
  `README.md`, `CLAUDE.md` and the draft spec. It is repaired.
- RUN-08 worked in real sessions. The last review blocked M2 (`medium`, SLUG-009: a redirect
  counted as a success). After the approval, a repair session got the decision and the finding, and
  no new first review ran. The repair committed a change, so the last review checked it and
  blocked M2 again (no test of a redirect). The runner read the second Blocked entry and the second
  Approval: the finding was about `tests/`, so a test session wrote the tests, a build session
  committed them, and the last review let M2 merge. The two runs after the approvals took 102 and
  129 seconds.
- RUN-09 let two faults of a requirement through. The last review of M1 rated as `low` a
  `--max` of more than 4300 digits, which still ends in a traceback instead of the error of
  SLUG-007 (the third run rated the same fault `high`), and `python main.py Hello World`, which
  drops `Hello`. By the review skill, a broken requirement is `high`; the old rule would have
  blocked M1. New idea RUN-10, approved with option B and built on November 23, 2026: the
  review skill and the review prompt now say that wrong behavior against a requirement is `high`,
  never `low`.
- No build session blocked. The build session of M2 wrote in its report that DEC-004 was still
  `Proposed` and that the user must approve the flow of user data, then it committed the milestone
  instead of blocking it, against the rule of the build prompt. The workflow normally stops this
  earlier (a plan needs an approved design, with no `Proposed` decision), but no check enforces it.
  New idea RUN-11. So a milestone that a build session blocks with partial work is still checked
  only by the suite.
