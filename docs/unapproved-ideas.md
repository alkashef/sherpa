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
| 24 | The project skill `/find-bugs`: the scope since the last release tag, the lines that no test runs, `pip-audit` and `npm audit`, the surviving mutants, one `BUG:` line for each fault, and a fix milestone for each bug by the rules of `/write-plan`. `/sherpa`, the workflow, the page and the README name it | USER-18, approved on November 21, 2026 |
| 25 | `/write-tests` writes a property test (Hypothesis, `max_examples=50`) for a rule over all inputs; `hypothesis` joins the `python` module. `assets/.github/workflows/mutation.yml`: a manual Linux workflow that runs `mutmut` or Stryker on the files changed since the last release, and keeps the surviving mutants for `/find-bugs` | C3, approved on November 22, 2026 |
| 26 | A line "Tests prove" in the sections `cli`, `data`, `http-apis`, `html-css`, `ui-design`, `long-running` and `llm` of `CLAUDE_GOLDEN.md`; `/write-design` covers it in the test design, and `AGENTS.md` carries every rules file | Rank 16 (REPORT-15), approved on November 22, 2026 |
| 27 | The design guide takes the folder layout from the framework, gives a frontend and a backend their own folders, and groups files by feature | Rank 18 (USER-05), approved on November 22, 2026 |
| 28 | The README, "Change what new projects get", names the four places that a new language needs | Rank 19 (USER-07), November 22, 2026 |
| 29 | `build_instance.py --list-modules` prints the numbered module table (No., Module, Section, Details) that `/project-init` and `/write-design` show; `--add` adds a module to a project that exists and keeps every file. `/write-design` matches the modules and their globs to the approved design | USER-19, approved on November 21, 2026 |
| 30 | Living docs: the docs that a person reads use STE, flavored mode. `assets/scripts/ste_lint.py`, a typed port of the MIT `ste-lint.py` with its license notice: `check.py` fails a doc of 100 words or more over 2.5 marks for each 100 words, and a sentence of 12 words or more in two docs. The suite lints the docs of a full build; `workflow.md` lost its semicolons (2.60 to 2.06) | USER-20, approved on November 21, 2026 |
| 31 | Communication and reporting: the first time that a reply names an ID, it names its kind and its file. The runner names "milestone M<n> in docs/plan.md" in its messages, and "requirement X in docs/spec.md" in the question of a review block | D1, approved on November 22, 2026 |
| 32 | The table of the runner: planned rows in very dark grey (256-color 238) with `-` and `planned`, a Total row under Duration, and a last row with a progress bar, the percent and `n/m` | USER-21, approved on November 21, 2026 |
| 33 | `assets/scripts/dashboard.py`, standard library only: one HTML page on 127.0.0.1 (or `--out`) with Needs you, Plan and releases, Trace (also to a milestone that a commit finished) and Code map (file boxes by lines, imports against the module boundaries, the class list). The Refresh button reads the files again, it writes nothing, and it never shows a bare ID | USER-22, USER-23 and USER-24, approved on November 21, 2026 |
| 34 | `assets/.github/workflows/check.yml` in each project: at each push a clean Linux machine installs from `requirements.txt` (and `npm ci`, with the Playwright browsers for `ui` tests) and runs `python scripts/check.py`. `release.py` adds `versions/pip-freeze.txt` (and `versions/npm-ls.txt`) to the release archive | Rank 14 (REPORT-10), approved in part on November 22, 2026 |
| 35 | Fixes that the second trial and the third real run found on November 23, 2026: a list item is its own paragraph in `ste_lint.py`, and the plan template drops a semicolon; the runner makes its folders with the usual permissions (`tempfile.mkdtemp` shut out the Codex sandbox); the build prompt asks for one commit; the check and test tools of a project are approved dependencies; a repair or rebuild session that finds a test wrong reports a `BLOCKED:` line, the runner keeps its work and blocks, and after the approval a test session gets the decision | Found while running the second trial and the third real run (open work) |
| 36 | The third real run, November 23, 2026 (README, "Checked in real Claude Code sessions"): three milestones with real sessions, the test folder, findings about tests sent to test sessions, a block by the last review in each milestone, the approvals and the merges, `/sherpa` and the dashboard. No build session blocked, so that path is still checked by the suite only | Item of the open work, approved on November 22, 2026 |
| 37 | `docs/v4/`: the report, the presentation and the demo of version 4. `docs/v3/` stays as the record of version 3, and sherpa's `CLAUDE.md` names `v4/` as current | Approved by the user on November 22, 2026 |
| 38 | The second trial of the test writers (`trials/test-writers/`, results in `results-2/`): Claude, Codex and Antigravity, 3 runs on each of 2 kits through the runner. All three qualify, the medians of seeded bugs caught tie at 17.5, and Claude is the fastest (217 s), so by the rule Claude stays the default writer | USER-17, rule of the second trial approved on November 22, 2026 |
| 39 | The audit of `CLAUDE_GOLDEN.md` (`docs/audit-claude-golden.md`): the built `CLAUDE.md` drops from 199 to 138 lines. Architecture, Configuration and the test-code rules move to `code-quality`, the dependency list to the language files, the README rule to a new `readme` rules file; 15 rules go; ruff `FIX`, ESLint `no-warning-comments`, and Stylelint (no color outside `theme.css`, BEM class names) take over four rules. Five rows marked Tool keep their prose, because no tool checks them yet | Rank 17 (USER-06), table approved on November 23, 2026 |

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

1. **RUN-08 (option C), approved on November 23, 2026: an approval covers the code that the user
   saw.**
   - After the approval of a block by the last review, a repair session gets the decision and the
     findings of the Blocked entry. No new first review runs.
   - When the session changes nothing, the runner runs its checks and merges.
   - When it commits a change, the last review runs, and its blocking findings block as usual.
   - The approval of a test that looks wrong (a `BLOCKED:` line) covers only that test: later
     reviews block as usual.
2. **RUN-09 (option B), approved on November 23, 2026:** a finding of the last review blocks when
   it is `high`, or `medium` with a requirement ID as its rule. A `low` finding never blocks.
3. **A fourth real run (option B), approved on November 23, 2026,** after items 1 and 2: one
   project, two milestones, with real sessions. One milestone sends the user's name and email
   address to an outside mailing-list service that only a `Proposed` decision names, so its build
   session must block. The run checks a build session that blocks with partial work, the approval
   path of RUN-08, and the audited rules.

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

On November 22, 2026 the user decided each idea of Part 2, and Part 1 holds the result. The
sections below keep the context of the ideas. A new idea goes here, with its own entry. The user
decided RUN-08 and RUN-09 on November 23, 2026 (Part 1).

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
RUN-NN and no rank. RUN-06 and RUN-07 came from the trial of three test writers. RUN-01 to RUN-07
are decided and built.

Ideas from the third real run and the second trial (November 23, 2026). On the same day the user
approved RUN-08 with option C (an approval covers the code that the user saw), not its proposal
below, and RUN-09 with its proposal: Part 1.

- **RUN-08: an approval covers only the findings that it answers.** After the user approves a
  milestone that the last review blocked, no finding of a later review blocks it again. In the
  third real run, the next review of M1 found two new medium faults against SLUG-005 and SLUG-007,
  and the milestone merged with them. Proposal: a finding blocks again unless its file and rule
  match a finding of the approved Blocked entry.
- **RUN-09: a low finding that names a requirement need not block.** In the third real run, a
  low "missing test" finding with SLUG-005 in its rule blocked M1. Proposal: block for a high
  finding, or for a medium or high one that names a requirement.

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
(Part 1). Part 2 holds two open ideas: RUN-08 and RUN-09.
