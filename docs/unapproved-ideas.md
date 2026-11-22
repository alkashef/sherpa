# Unapproved ideas

This file has two parts.

- **Part 1** holds what is left of the changes that the user approved. An item of Part 1 is work:
  build it without a new approval, and delete it in the commit that finishes it.
- **Part 2** holds ideas for sherpa's workflow that nobody approved. An idea is not a
  requirement: never design, plan, test or build from Part 2. An idea becomes work only when the
  user approves it.

Dates of this file:

- Approved for recording: October 17, 2026
- Consolidated: October 17, 2026
- Renamed from `todo.md`: November 19, 2026
- Reviewed with the user, one idea at a time: November 20, 2026
- Combined with `implementation-order.md`, which is deleted: November 21, 2026
- Added the user's list (USER-12 to USER-24, section G of Part 2): November 21, 2026
- Walked through section G with the user, and decided each item: November 21, 2026

All paths are below `skills/project-init/` unless they start with `tests/` or `docs/`.

## Part 1: approved changes

On November 20, 2026 the user decided ranks 1 to 12 of the first list of ideas and added two
ideas (USER-10: date-based versions and light releases; USER-11: a branch for each milestone).
The approved changes are built. Their first text is in the git history of this file.

### Built

| Stage | What | Ideas |
| --- | --- | --- |
| 1 | Tool rules in `assets/scripts/check.py`, `ruff.toml` and `eslint.config.js`: one line for each check, code with no test fails, one class per file, imports at the top, module boundaries | Ranks 5, 7, 9 |
| 2 | `assets/scripts/spec_coverage.py`: the mode `--consistency`, and acceptance examples in the list and in the milestone check | Ranks 8, 1 |
| 3 | `assets/scripts/release.py` and `assets/docs/releases.md` | USER-10 |
| 4 | `assets/scripts/live_checks.py`, and normal test runs that skip `tests/live/` | Rank 2 |
| 5 | The rules master, the skills and the templates of the spec, the design and the plan | Ranks 1, 2, 6, 7, 9, 11, 12 |
| 6 | The skill `/code-review-sherpa` with its checklist | Rank 3 |
| 7 | `assets/scripts/milestones-runner.py`: a branch for each milestone, the review and repair sessions, the merge, the human test, the live stage, the start checks, the reason for a retry | USER-11, ranks 3, 6, 10, 2, 8 |
| 8 | `assets/docs/workflow.md`, the page with the philosophy, the README, the builder, the tests | All |
| 9 | `assets/scripts/check.py`: the module boundaries of JavaScript files. `assets/scripts/milestones-runner.py`: a refused `M<n>: blocked` commit or push says how to finish the step | Open work of the first build |
| 10 | `assets/ruff.toml`: `known-first-party = ["src"]`, so that the order of the imports of a test does not depend on whether the code file exists. A bug that the second real run found | RUN-05, approved on November 21, 2026 |
| 11 | The project skill `/sdd` is now `/sherpa`: its folder, its name, and each reference in the skills, the docs, the page, the runner, the builder and the tests. `docs/v1/` to `docs/v3/` keep `/sdd` | Asked by the user on November 22, 2026 |
| 12 | `assets/.coveragerc` with `patch = subprocess`, copied into each Python project: the coverage floor counts the processes that a test starts | RUN-06, approved on November 21, 2026 |
| 13 | `/write-tests`, step 3: the limits (the limit and one value on each side), the defaults and one invalid value of each kind | RUN-07, approved on November 21, 2026 |
| 14 | The glossary table in `assets/docs/spec.md`, the `erDiagram` of the data model in `assets/docs/design.md`, the rules of `/write-spec`, `/write-design` and Naming. The templates of the two skills are copies of the two docs, and a test keeps them equal | USER-13 and USER-14, approved on November 21, 2026 |
| 15 | The test session runs in a temporary folder with no `src/` and no `.git`. `config/test-writer.json` (from `/project-init`, `--test-writer`) names the writer: Claude, Antigravity, Codex or Copilot, with `AGENTS.md` for the last three. A start check of the writer; the runner copies `tests/` back, runs ruff, mypy and the tests itself, never trusts the exit code, and gives one round of repair. The build steps of the trial | USER-17, approved on November 21, 2026 |
| 16 | The runner runs the new tests with `--junitxml` and accepts only a wrong value, an error of `src/`, or a missing module that the Owner names | Rank 15 (REPORT-05), approved in part on November 22, 2026 |
| 17 | A review finding names the file of its fix. A finding about `tests/` goes to a test session in the folder of the writer, then a rebuild (`M<n>: test repairs`). A public function that a repair adds goes into Interfaces | RUN-01, approved on November 22, 2026 |
| 18 | A finding of the last review that is `high`, or whose rule is a requirement ID, blocks the milestone. The runner writes the Blocked entry on the base branch, and after the approval rebases the branch and merges | RUN-02, approved on November 22, 2026 |
| 19 | Each session gets the folders of the conda environment first on its PATH, and a start check refuses a `python` from another environment | RUN-03, approved on November 22, 2026 |
| 20 | `check.py` refuses a staged text file that is not UTF-8 or holds U+FFFD. `settings.json` denies `Set-Content`, `Out-File` and `Add-Content`. The prompts say to write files with Edit and Write | RUN-04, approved on November 22, 2026 |
| 21 | Each review runs in a temporary git worktree that the runner deletes; a change there only adds a warning to the log | IMPL-01, approved on November 22, 2026 |
| 22 | `settings.json` allows `git switch -c milestone/*`, `git switch main`, `git merge --ff-only milestone/*` and `git branch -d milestone/*`; the workflow and `/sherpa` name them | IMPL-02, approved on November 22, 2026 |
| 23 | `milestones-runner.py --tests-only M<n>` (with `--review-findings`) and `--review-only M<n>` are the test session and the review of a milestone in chat; `/sherpa` uses them | C2, approved on November 22, 2026 |

One real run followed on November 21, 2026 (README, "Checked in real Claude Code sessions"). It
proved the condition of the user's decision on rank 3: a `claude -p` session runs the built-in
`/code-review` and `/code-review-sherpa`. After that run the user approved one more change:
`assets/ruff.toml` permits `subprocess` (S603) in `tests/**`. `docs/v3/` shows the workflow with
these changes.

### Open work, in this order

The user decided on November 21, 2026: build the approved changes together, in one pass,
after the walk-through of section G ends. Several of them change the same files (the runner,
`/write-tests`, `assets/docs/workflow.md` and `workflow.html`), so one pass changes each file and
the diagram one time.

1. **USER-18, approved on November 21, 2026:** the project skill `/find-bugs`.
   - The user starts it, before a release. It changes no code. Its scope is the code changed
     since the last release tag, or all of the code before the first release.
   - First the tools: the lines that no test runs (the coverage report), and a dependency audit
     (`pip-audit`, `npm audit`).
   - Then the AI compares the code with the spec and the design, with most attention on those
     lines. Each finding is a `BUG:` line with a requirement ID and `file:line`.
   - Each bug becomes a fix milestone in `docs/plan.md`, by the rules of `/write-plan`. The user
     approves the rows, and the runner builds them. The isolated test session writes the failing
     test first. A bug whose test passes is a false alarm.
   - A finding that no requirement covers goes to the user as a question about the spec, not into
     the plan.
   - Mutation testing is not part of it. Rank 1 keeps it deferred.
   - Update `assets/docs/workflow.md`, `assets/docs/workflow.html` and the README.
   - Chat mode (`/sherpa`) uses this folder too, through `--tests-only` (open work below, C2).
   - Update `assets/docs/workflow.md`, `assets/docs/workflow.html` and the README.
2. **C3, approved on November 22, 2026:** property tests, and mutation tests on demand.
    - `/write-tests` writes a property test (Hypothesis) when a requirement states a rule for all
      inputs, with at most 50 examples for each test. `hypothesis` joins the `python` module.
    - A manual GitHub Actions workflow (Linux) runs `mutmut` (Python) or Stryker (JavaScript) on
      the files changed since the last release. `mutmut` 3 needs `fork`, so it does not run on
      Windows. `/find-bugs` reads the list of surviving mutants, and writes a fix milestone for
      each real gap in the tests.
3. **USER-19, approved on November 21, 2026:** the modules follow the design.
   - When the design is approved, `/write-design` compares the design (languages, components,
     folders) with the modules of the project and the globs of their rules files. It proposes
     the missing modules and the globs for the real folders, and the user approves.
   - `build_instance.py` gets a mode that adds one module to an existing project, and keeps every
     existing file. A project must reach the builder: the skill is installed for each user, not
     in the project.
   - **Added by the user:** `/project-init` and `/write-design` show the modules as a numbered
     table, so that the user selects them by number: `No. | Module | Section | Details`. Details
     says in one or two sentences what the rules of the module cover. It replaces the globs.
   - One owner for the table: `build_instance.py` holds each module with its details and prints
     the table (`--list-modules`). The two skills show that output and do not copy the table.
4. **Rank 16 (REPORT-15), approved on November 22, 2026:** each module names what its tests
   prove. Each module section of `assets/CLAUDE_GOLDEN.md` gets one line "Tests prove":
   - `cli`: each exit code, stdout and stderr. A second run with the same input gives the same
     result.
   - `data`: the stored form of each record. A write that stops in the middle leaves the old data
     readable. Data of a released version still loads.
   - `http-apis`: the status code and the body of each case. A slow or failed outside service (a
     fake) gives the documented error.
   - `html-css` and `ui-design`: each user scenario in Playwright. The main flows work with the
     keyboard only.
   - `long-running`: a stop in the middle, and a run that continues after it.
   - `llm`: a bad answer from the fake model gives the documented error.
   - `/write-design` uses the line in the test design. The `AGENTS.md` of the test folder carries
     the rules files of the project.
5. **Rank 18 (USER-05), approved on November 22, 2026:** where the folder layout comes from. One
    paragraph in `assets/.claude/skills/write-design/references/design-guide.md`: take the folder
    layout from the documented structure of the chosen framework, when it has one. When the
    project has a frontend and a backend, give each its own folder. Inside a folder, group the
    files by feature when there is more than one feature.
6. **USER-20, approved on November 21, 2026:** the style of the documents.
   - `assets/CLAUDE_GOLDEN.md`, Living docs, one rule: each doc that a person reads uses STE,
     flavored mode. Top-down, short sections, tables and lists before prose, one fact in one
     place.
   - Copy `ste-lint.py` of the `asd-ste100` skill (MIT, keep its license notice) to
     `assets/scripts/`. `check.py` runs it on `README.md`, `CLAUDE.md` and `docs/*.md`, with the
     limit 2.5 problems per 100 words. It skips a file under 100 words.
   - `check.py` fails when a sentence of 12 words or more is in two docs.
   - sherpa's suite runs the same lint on the templates. First fix
     `assets/docs/workflow.md` (2.77 on November 21, 2026).
   - EARS keeps "shall": flavored mode allows it.
7. **D1, approved on November 22, 2026:** no bare ID in text for a person.
    - One line in `assets/CLAUDE_GOLDEN.md`, Communication and reporting: the first time that a
      reply or a report names an ID, it names the kind and the file, for example "requirement
      SLUG-003 in docs/spec.md".
    - The runner does the same in its own messages, for example in the question of a blocked
      milestone.
    - The lines that a script reads keep their form: `DECISION:`, `FINDING:`, the cells of the
      plan table, and the commit subject `M<n>: <title>`. Their free text can name the kind.
    - The built `CLAUDE.md` used 193 of its 200 lines on November 22, 2026. This line and the
      STE line need room, so the audit (rank 17) frees some.
8. **USER-21, approved on November 21, 2026:** the table of the milestone runner.
   - After the running milestone, a row for each planned milestone of the range, in very dark
     grey (256-color code 238): `-` in Duration, Decisions and Findings, `planned` in Result.
     With colors off, the row is plain text.
   - The total time moves to its own row, under the Duration column, with `Total` to its left.
   - A last row holds a progress bar over the width of the table, then the percent and `n/m`.
     The bar counts finished milestones only.
   - The planned rows count for the width of the Title column.
   - Update the runner docstring, `assets/docs/workflow.md`, the panel of `workflow.html`, and
     the tests of the table.
9. **USER-22, USER-23 and USER-24, approved on November 21, 2026:** a dashboard for the
   developer.
   - `assets/scripts/dashboard.py`, standard library only. It serves an HTML page on 127.0.0.1
     and opens the browser. The Refresh button makes the script read the files again. No AI, no
     tokens, no file written. `--out <file>` saves the HTML page.
   - Each fact comes from its owner: the spec, the design, the plan, `docs/releases.md`, git, the
     tests, the code and the runner logs. The page holds no fact of its own.
   - The sections, top-down: Needs you, Plan and releases, Trace, Code map.
   - Trace: a requirement, the design rows that cite it, its milestone (the plan Refs, or a commit
     `M<n>:`), the tests with its ID in the name, and the modules whose docstring cites it.
   - Code map: a floor plan of `src/` (one box for each file, size by lines), the import graph
     compared with the module table, and the class list from the first line of each class
     docstring (from USER-15).
   - **Added by the user:** the page never shows a bare ID. It names the kind and the file, for
     example "design decision DEC-007 in design.md", "requirement SLUG-001 in spec.md" and
     "milestone M4 in plan.md". The programmer may not know what an ID is or where it is.
   - Two phases: first Needs you, the plan and the trace (they reuse `spec_coverage.py`), then
     the code map.
   - Limit: the review findings exist only in the runner logs of one machine.
   - Update `assets/docs/workflow.md`, `workflow.html`, the README and the table "Directory
     structure" of `CLAUDE_GOLDEN.md`.
10. **Rank 14 (REPORT-10), approved in part on November 22, 2026:** a clean install at each
    push.
   - A GitHub Actions job in each new project (`assets/.github/workflows/check.yml`): at each
     push, a clean machine installs the project from `requirements.txt` (and `npm ci` for
     JavaScript), then runs `python scripts/check.py`. The `ui` tests need their browsers there.
   - `release.py` saves the output of `pip freeze` (and `npm ls --all` for JavaScript) in the
     release archive, so that a release can be installed again with the same versions.
11. **Rank 19 (USER-07), November 22, 2026:** the README section for contributors names the four
    places that a new language needs: a module section in `CLAUDE_GOLDEN.md` and an entry in the
    builder, its commands in `check.py`, its test-name pattern in `spec_coverage.py`, and its
    config files in `assets/`.
12. **Rank 17 (USER-06), approved on November 22, 2026:** one audit of `CLAUDE_GOLDEN.md` for rules
    that are too rigid.
   - Do it after the build adds its new rules, so that the audit sees all of them.
   - One row for each rule (about 155): keep it with its reason, move it into a tool, move it
     into a rules file or a skill, or delete it.
   - The user approves the table before any rule changes.
   - A rule that a real run later proves necessary comes back.
   - Examples to question: "Do not write your own ... context managers", "One class per file",
     and "a design pattern that no `Decided` decision names".
13. **The second trial of the test writers (USER-17, approved on November 21 and 22, 2026):** the
    build of USER-17 is done (Built, stage 15). Run the trial of the three writers again, with
    RUN-06 and RUN-07 in place, by the rule of the second trial: each writer runs 3 times on each
    of 2 projects (the slug tool, and a new project that stores data), scored by
    `trials/test-writers/evaluate.py`. A writer qualifies only if all gates pass in all 6 runs.
    Of the qualified writers, the highest median of seeded bugs caught wins, and on a tie the
    faster one. If no writer qualifies, Claude stays the default, and each failed gate becomes a
    new idea. Then the user decides the default writer.
14. **After the build, in a real session:** run the changes above, and also what is not
   run in a real session yet: `/sherpa`, and a milestone that a build session blocks with
   partial work in its branch. The second real run ran a human test, a block in the test
   session, and the approval.
15. **`docs/v4/`, approved by the user on November 22, 2026:** after the real run, make
    `docs/v4/` with the report, the presentation and the demo of the new workflow. `docs/v3/`
    stays as the record of the earlier version. sherpa's `CLAUDE.md` then names `v4/` as current.

### Decided with no work

The user also decided these points on November 20, 2026. They need no change.

- Rank 1: property and mutation checks are deferred, because they add much run time. Replaced
  on November 22, 2026 by C3 (open work).
- Rank 3: the review does not use the Anthropic `code-review` plugin (it needs a pull request)
  or CodeRabbit (it sends the code to an external service).
- Rank 4 (evidence before completion): closed as delivered. A pushed commit is the evidence,
  because the pre-commit hook refuses a commit that fails a check. The separate evidence record
  is rejected. "Accepted for release" is the human's decision (stage 3).
- Rank 5: the record of commands, environment and fixtures is rejected.
- Rank 7: the list of quality criteria is closed. The review checklist owns them (stage 6).
- Rank 8: the evidence record after a milestone is rejected. Git history and
  `docs/releases.md` hold it.
- Rank 9: no new skill for the system overview. `/write-design` owns it.
- Rank 10: the separate defect procedure is rejected. The failing test of a fix milestone is
  the diagnosis.
- Rank 12: closed as delivered, with the transition rule of stage 5.
- USER-10: the release record is not in the plan table, because that table holds only
  unfinished milestones and each session reads it.

The user decided these points of section G on November 21, 2026. They need no change.

- USER-12 (modules and an architectural view): closed as delivered. The design has the
  component diagram, the directory structure and the module boundaries, and `check.py` enforces
  the boundaries.
- USER-15 (a list of the classes): a list kept by hand in the design is rejected. It must name
  classes before the code exists, it copies the docstrings and goes stale, and no tool can check
  it. A list generated from the docstrings is part of the dashboard (USER-22 to USER-24, open work).
- USER-16 (Attribute-Driven Design 3.0): closed as answered. `/write-design` runs a short form
  of the ADD 3.0 cycle. The drivers are the measurable rows of the spec, and each DEC row names
  its driver and the alternative it rejected. The separate table of quality scenarios, the design
  backlog and a record of each round are left out, because they add little to a small project.
- USER-17: the second GitHub repository (`<REPO-NAME>_TEST`) is rejected. A temporary folder
  isolates the test writer equally well, with no second remote, history or sync.
- Rank 13 (REPORT-01, a baseline record before changes), November 22, 2026: rejected. sherpa
  starts only in an empty folder, and the commit hook keeps the base branch free of known
  failures. The first commit, the milestone commits and the release tags are the baseline. The
  idea must come back if sherpa adopts an existing project.
- Rank 14 (REPORT-10), November 22, 2026: the handover document (operation, ownership,
  recovery) is rejected. The README already has setup, run and test, and for one developer a
  handover document is work that nobody reads.
- Rank 15 (REPORT-05), November 22, 2026: a separate record of why each test fails is rejected,
  because the runner log keeps the reasons. Evidence for setup and refactoring work is closed as
  delivered: the milestone guide refuses setup work that no test can show, and a refactor keeps
  all tests passing.
- Rank 19 (USER-07), November 22, 2026: closed as delivered for the method. The workflow, the
  docs, the runner and the skills name no language. A third language comes only when a project
  needs one (the README names its cost, open work).
- Rank 20 (USER-04), November 22, 2026: rejected. A config folder breaks the tools and the VS
  Code extensions, which look for their config at the root. Merging the configs into
  `pyproject.toml` and `package.json` is also rejected: it does not improve the code, and it
  changes the builder, `check.py`, the permission rules and their tests.
- Rank 21 (USER-01), November 22, 2026: closed. The framework has its own name, sherpa, and the
  skill keeps `project-init`, because the name says what it does.

---

## Part 2: ideas that nobody approved

Since November 22, 2026, Part 2 holds no open idea: the user decided each one, and Part 1 holds
the result. The sections below keep the context of the ideas. A new idea goes here, with its own
entry.

### A. Open decisions of the approved changes

These points came up while Claude built the approved changes. An idea here has the ID IMPL-NN
and no rank. IMPL-01 and IMPL-02 are decided (Part 1).

### B. Source and review context of the first list

Source: Fully_AI_Assisted_SDD_October_2026.html, dated October 16, 2026. Each Report reference
below gives the section number, the title and the HTML anchor. The proposals come from the report
and from a comparison with the repository. They are not implemented changes.

Repository reviewed: alkashef/project-init (now sherpa), at the baseline commit
373622e557e2597e0551d9a400dbb1ff6b5cf493. Method: document and source inspection. No application
checks or tests were run. Path-specific findings describe that baseline, not the present files.

Repository path key:

- W: `skills/project-init/assets/docs/workflow.md`
- G: `skills/project-init/assets/CLAUDE_GOLDEN.md`
- P: `skills/project-init/assets/.claude/skills/write-plan/SKILL.md`
- M: `skills/project-init/assets/.claude/skills/write-plan/references/milestone-guide.md`
- C: `skills/project-init/assets/scripts/check.py`
- R: `skills/project-init/assets/scripts/milestones-runner.py`
- S: `skills/project-init/assets/.claude/skills/write-spec/`
- D: `skills/project-init/assets/.claude/skills/write-design/`

### C. The ranking of the first list

The rank numbers come from the first list of 21 proposals, ordered by their expected effect on
the quality of the programs that the workflow produces. The order is engineering judgment, not a
measured effect. Ranks 1 to 12 left the file, so the list starts at rank 13. A rank shows
priority only. The stable IDs (USER-NN and REPORT-NN) identify an idea.

---

### D. The proposals of the first list, ranks 13 to 21

The user decided ranks 13 to 21 on November 22, 2026 (Part 1).

Source labels distinguish the user's proposals from report-derived extensions.
Report-derived proposals adapt the report to the reviewed repository.
They do not imply that the report mandates a particular skill or file layout.

### E. From the real runs and the trial of November 21, 2026

The runs are in the README, "Checked in real Claude Code sessions". An idea from them has the ID
RUN-NN and no rank. RUN-06 and RUN-07 came from the trial of three test writers. Each RUN idea is
decided: RUN-05 is built, and the others are open work in Part 1.

### G. The user's list of November 21, 2026

The user gave this list on November 21, 2026, and asked for a walk-through, one item at a time.
The walk-through ended the same day: each item is decided, and Part 1 holds the work.
The IDs follow the order of the walk-through: first what is implemented, then the expected effect
on the quality of the code. A walk-through item can hold more than one idea.

| Item | What | Ideas | State |
| --- | --- | --- | --- |
| 1 | The views of the spec and the design | USER-12 to USER-15 | Decided (Part 1) |
| 2 | Attribute-Driven Design 3.0 | USER-16 | Decided (Part 1) |
| 3 | Tests that a different AI writes, in a separate repository | USER-17 | Decided (Part 1) |
| 4 | A run that finds and repairs bugs | USER-18 | Decided (Part 1) |
| 5 | The modules of `CLAUDE.md` | USER-19 | Decided (Part 1) |
| 6 | The style of the documents | USER-20 | Decided (Part 1) |
| 7 | The table of the milestone runner | USER-21 | Decided (Part 1) |
| 8 | A dashboard for the developer | USER-22 to USER-24 | Decided (Part 1) |

---

### F. Source map

- Original user idea 1 -> USER-01, rank 21.
- Original user idea 4 -> USER-04, rank 20.
- Original user idea 5 -> USER-05, rank 18.
- Original user idea 6 -> USER-06, rank 17.
- Original user idea 7 -> USER-07, rank 19.
- REPORT-01 -> rank 13. REPORT-10 -> rank 14. REPORT-05 -> rank 15. REPORT-15 -> rank 16.
- The real runs of November 21, 2026 -> RUN-01 to RUN-04, no rank, approved on November 22,
  2026 (Part 1). RUN-05 is built (stage 10).
- The trial of three test writers, November 21, 2026 -> RUN-06 and RUN-07, no rank. Both are
  approved (Part 1).
- The build of the approved changes -> IMPL-01 and IMPL-02, no rank, approved on November 22,
  2026 (Part 1).
- The user's list of November 21, 2026 -> USER-12 to USER-24, no rank (section G). All of them
  are decided (Part 1).

The user decided ranks 1 to 12 on November 20, 2026, and ranks 13 to 21 on November 22, 2026
(Part 1). Part 2 holds no open idea.
