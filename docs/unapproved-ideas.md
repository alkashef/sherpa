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

1. **RUN-06, approved on November 21, 2026:** the coverage gate counts the processes that a
   test starts. Add `assets/.coveragerc` with `[run]` and `patch = subprocess` (Coverage.py 7.10
   or later), and copy it into each new project. In the trial, a correct implementation had 41%
   coverage with the tests of Codex and of Claude, and 90% with this setting.
2. **RUN-07, approved on November 21, 2026:** `/write-tests`, step 3, asks for the limits and
   the defaults. For each limit that a requirement names, test the limit and one value on each
   side. For each default, test a call that leaves out the value. For each invalid input, test one
   value of each kind (out of range, wrong type).
3. **USER-13 and USER-14, approved on November 21, 2026:** the glossary and the data model.
   - `assets/docs/spec.md`, section 2: a table `Term | Meaning | Avoid`. `/write-spec` fills it.
     Names in the code use the Term, never an Avoid word (`assets/CLAUDE_GOLDEN.md`, Naming).
   - `assets/docs/design.md`, section 3: one Mermaid `erDiagram` with the entities, their typed
     attributes and their relationships. `/write-design` draws it. Section 4 (Interfaces) links
     to it for the stored records, and does not copy them.
   - Make the spec and design templates of `/write-spec` and `/write-design` agree with
     `assets/docs/spec.md` and `assets/docs/design.md`. The copies drifted apart.
4. **USER-17, approved on November 21, 2026:** the tests come from a folder without the code.
   - For each test session, `assets/scripts/milestones-runner.py` makes a temporary folder
     outside the project. It holds `docs/spec.md`, `docs/design.md`, `docs/plan.md`, the test
     rules, the tool configs and `tests/`, but no `src/` and no `.git`.
   - The runner copies `tests/` back and runs the tests. It gives the test writer the error type
     and the message of each failure, with no lines of code, for one round of repair. The runner
     also runs the older tests.
   - **Amended by the user on November 21, 2026:** `/project-init` asks which AI writes the
     tests: Claude (the default), Antigravity, Codex or GitHub Copilot. It writes the answer, with
     the recommended model and effort, to `config/test-writer.json`. The runner reads that file,
     and `--test-writer` overrides it. After one sign-in to the chosen CLI, the run needs no
     person.
   - The folder gets the files of the chosen writer. Claude: `CLAUDE.md`, the rules files for
     tests, `.claude/settings.json` and `/write-tests`. Antigravity, Codex and Copilot: one
     `AGENTS.md` that the runner generates from the same sources. All three read `AGENTS.md`.
   - The commands and the recommendations, from the vendor docs of November 21, 2026. Check the
     names at build time, because they change:

     | Writer | Command | Model | Effort | One-time sign-in |
     | --- | --- | --- | --- | --- |
     | Claude | `claude -p --permission-mode bypassPermissions` | Model of the plan row | Effort of the plan row | As now |
     | Codex | `codex exec --sandbox workspace-write --skip-git-repo-check` | `gpt-6.2-astra` | `high` | `codex login`, or `CODEX_API_KEY` |
     | Antigravity | `agy -p --dangerously-skip-permissions` | `gemini-4-neon`, or `gemini-4-hydrogen` on the Free and Plus plans | `high` | One interactive `agy` session, or `GEMINI_API_KEY` with `modelProvider` |
     | Copilot | `copilot -p --allow-all-tools --no-ask-user` | `gpt-6.2-astra` | `high` | `COPILOT_GITHUB_TOKEN`, a fine-grained token |

   - Through Copilot or Antigravity, the recommended model is not a Claude model. Copilot uses
     `claude-sonnet-5.5` when no model is given, and Antigravity also offers Claude. The gain
     comes from a different model family.
   - A start check of the runner sends one short prompt with the chosen CLI and model. A missing
     sign-in or an unknown model then stops the run before the first milestone.
   - The runner trusts only its own run of the tests after the copy back, never the exit code of
     the writer. Antigravity exits with 0 when it refuses an action.
   - Limit: the folder stops a normal read of `src/`. It is not a security boundary, because a
     shell can still reach the project by its full path.
   - **Trial with Codex, November 21, 2026.** A small project built by the skill (a slug tool:
     7 requirements, 10 examples, one milestone). Codex CLI 0.171.0-alpha.13 (the copy in the
     VS Code extension), `gpt-6.2-astra`, effort `high`, in a folder with the docs, the configs,
     `tests/` and a generated `AGENTS.md` of 19 KB. Command: `codex exec -m gpt-6.2-astra -c
     model_reasoning_effort=high -c 'windows.sandbox="unelevated"' --sandbox workspace-write
     --skip-git-repo-check --ignore-user-config --ephemeral -C <folder> --json -o <file> -`.
     - The run took 139 seconds: 352,458 input tokens (322,816 cached) and 3,573 output tokens.
     - It wrote the 12 planned tests as 20 cases. `spec_coverage.py M1` found all 7 requirements
       and 10 examples tested. Ruff passed. All 20 failed before the code existed, and all 20
       passed on a correct implementation. They caught 10 of 11 seeded bugs. The one missed: the
       default of `make_slug(max_length=60)`, because no unit test omits the argument.
     - An extra case of its own (maximum length 13) caught the bug "cut at N characters". The
       planned example alone (EX-004) does not catch it.
     - It read only the folder, and its file search left out `src/` and `main.py`.
     - For the build: (1) `--ignore-user-config` drops the user's `windows.sandbox`, and then
       every shell command is refused. The runner passes `-c windows.sandbox="unelevated"` on
       Windows. (2) The first try did nothing and still exited with 0. (3) The tests import
       `src.slug` inside a helper (`import_module`), to avoid an error at collection. Mypy then
       fails (`no-any-return`), and the commit hook would refuse the tests. So after the copy
       back the runner runs ruff and mypy on `tests/` too, and `AGENTS.md` says that the imports
       go at the top and that a missing module named in Owner is a valid failure.
   - **Build steps from the trials (approved by the user on November 21, 2026):**
     - On Windows, pass `-c windows.sandbox="unelevated"` to Codex with `--ignore-user-config`.
     - Judge a test session only by the runner's own checks, never by the exit code of the CLI.
     - After the copy back, run ruff, mypy and pytest on `tests/`, and give the errors to the
       writer in its round of repair. A Claude session in a new folder is not trusted: it ignores
       the allow list of `.claude/settings.json`, and possibly its hooks.
     - `AGENTS.md` says that the imports go at the top, and that a missing module named in Owner
       is a valid failure.
     - After the build, run the trial of the three writers a second time, with RUN-06 and RUN-07
       in place. Then the user decides the default writer.
   - **Trial of three writers, November 21, 2026.** The same project and the same rules. Claude
     got the files of a Claude folder, and its prompt got the head of the `AGENTS.md` that the
     other two got. One run each, effort `high`, scored by one script with 17 seeded bugs:

     | | Codex `gpt-6.2-astra` | Claude `claude-opus-5-5` | Antigravity `gemini-4-neon-high` |
     | --- | --- | --- | --- |
     | Time | 139 s | 76 s | 226 s |
     | Tests (cases) | 12 (20) | 12 (12) | 30 (30) |
     | Seeded bugs caught | 16 of 17 | 11 of 17 | 15 of 17 |
     | Mypy, with the code present | 1 error | 12 errors | Passed |
     | Coverage gate (80%), with a correct implementation | 41%, fails | 41%, fails | 94%, passes |
     | Ruff, IDs, right failure before the code, pass on correct code, docs not edited | Yes | Yes | Yes |

     - Claude wrote only the planned examples: no limit, no default and no second invalid value.
       It also left out the `-> None` of each test.
     - Antigravity alone added unit tests that call `src.cli.main` in the test process. The
       coverage gate does not count a test that runs `main.py` as a process (RUN-06).
     - Claude ran with `--setting-sources project`. It warned that the folder is not trusted, so
       its project hooks possibly did not run.
     - One run of each writer is weak evidence, because the output of a model changes from run to
       run. The default stays Claude until a second trial, after RUN-06 and RUN-07.
5. **USER-18, approved on November 21, 2026:** the project skill `/find-bugs`.
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
   - Chat mode (`/sdd`) keeps its test subagent for now.
   - Update `assets/docs/workflow.md`, `assets/docs/workflow.html` and the README.
6. **USER-19, approved on November 21, 2026:** the modules follow the design.
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
7. **USER-20, approved on November 21, 2026:** the style of the documents.
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
10. **After the build, in a real session:** run the changes above, and also what is not
   run in a real session yet: `/sdd`, and a milestone that a build session blocks with
   partial work in its branch. The second real run ran a human test, a block in the test
   session, and the approval.

### Decided with no work

The user also decided these points on November 20, 2026. They need no change.

- Rank 1: property and mutation checks are deferred, because they add much run time.
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
  it. A list generated from the docstrings is part of the dashboard (open work 9).
- USER-16 (Attribute-Driven Design 3.0): closed as answered. `/write-design` runs a short form
  of the ADD 3.0 cycle. The drivers are the measurable rows of the spec, and each DEC row names
  its driver and the alternative it rejected. The separate table of quality scenarios, the design
  backlog and a record of each round are left out, because they add little to a small project.
- USER-17: the second GitHub repository (`<REPO-NAME>_TEST`) is rejected. A temporary folder
  isolates the test writer equally well, with no second remote, history or sync.

---

## Part 2: ideas that nobody approved

Ranks 13 to 21 of the first list are still here. In the review of November 20, 2026 Claude
proposed a resolution for each one, and the user did not decide them. The review stopped at
rank 13. The ideas with the IDs IMPL-NN, RUN-NN came later, and the user did not decide them.

### A. Open decisions of the approved changes

These points came up while Claude built the approved changes. An idea here has the ID IMPL-NN
and no rank.

#### - [ ] IMPL-01 | A review that changed a file

**Proposed resolution (Claude, November 21, 2026; the user did not decide it):** The runner puts
the changes of the review session in a git stash, says so, and tries the review again.

- **Current:** The runner (R) finds the change and counts the session as failed. It does not
  undo the change, and the retry cannot edit, so the run stops and the user cleans the branch
  by hand.
- **Why:** A review that goes wrong must not stop an unattended run for a cause that a script
  can remove.

#### - [ ] IMPL-02 | Permissions for a milestone in chat

**Proposed resolution (Claude, November 21, 2026; the user did not decide it):** Put the three
commands on the allow list of `assets/.claude/settings.json`, each one only for a branch
`milestone/*`.

- **Current:** `.claude/settings.json` asks before `git checkout -b`, `git merge --ff-only` and
  `git branch -d`. A milestone that `/sdd` builds in chat needs the three commands, so the user
  gets three prompts for each milestone.
- **Why:** The commands are part of the approved workflow, and none of them can lose work on
  the base branch.

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

### D. The 9 open proposals of the first list, in the order of their rank

Source labels distinguish the user's proposals from report-derived extensions.
Report-derived proposals adapt the report to the reviewed repository.
They do not imply that the report mandates a particular skill or file layout.

#### - [ ] Rank 13 | REPORT-01 | Record a factual baseline before changes

**Proposed resolution (Claude, November 20, 2026; the user did not decide it):** Reject as a separate record. The first commit, the checked base branch and the release tags are the baseline. The idea must come back if sherpa adopts existing projects.

**Expected impact:** Medium-high; context-dependent.
**Ranking reason:** Separates old failures from regressions and exposes environment or compatibility assumptions. Its impact rises for existing systems.
**Ranking basis:** Sections 5.2 (#stage-02) and 5.1 (#stage-01).

- **Current:** W starts with specification. S, D, and P inspect existing files, but the
  workflow has no explicit baseline record with executed checks and known failures.
- **Proposal:** Before planning, record the source revision, relevant system map,
  runtime and dependency versions, existing test results, and known defects.
  For a new project, establish its build and test environment. For an existing
  project, record behavior and compatibility obligations that must survive.
  Record pre-existing failures separately from regressions introduced by the change.
- **Report:** Section 5.2, "Inspect the system and establish a baseline" (#stage-02).
  Also Section 5.1, "Define the outcome and boundaries" (#stage-01).
- **Why:** Later claims need a factual starting point and a clear delivery boundary.

---

#### - [ ] Rank 14 | REPORT-10 | Repeatable installation, release, and checked handover

**Proposed resolution (Claude, November 20, 2026; the user did not decide it):** Approve in part: a CI job that installs the project on a clean machine and runs `check.py` at each push. Reject the handover gate.

**Expected impact:** Medium-high.
**Ranking reason:** Detects installation and environment failures and makes the accepted release operable and recoverable by someone else.
**Ranking basis:** Section 5.12 (#stage-12) and Appendix 2 (#production).

- **Current:** W updates inaccurate documents and G requires README setup instructions.
  G pins direct dependencies, but a clean-environment setup and release handover
  are not explicit workflow gates.
- **Proposal:** Test the documented setup from a clean environment. Retain sufficient
  dependency and environment information to repeat it, including resolved versions
  where direct pins alone do not control installation.
  Identify the release artifact and source revision. Include operation, diagnostics,
  known limits, ownership, safe reruns, and recovery instructions.
  Check that the instructions work for someone other than the implementer.
- **Report:** Section 5.12, "Document, release, and hand over" (#stage-12).
  Also Appendix 2 (#production), Delivery and Operation.
- **Why:** Committing code and documenting commands do not establish installability or
  operational readiness.

---

#### - [ ] Rank 15 | REPORT-05 | Prove that failing tests detect the intended defect

**Proposed resolution (Claude, November 20, 2026; the user did not decide it):** Close as delivered: `/write-tests` accepts a failing test only when the behavior is missing. Reject the kept record of the reason.

**Expected impact:** Medium-high.
**Ranking reason:** Rejects meaningless red results caused by broken setup. Strengthens the test basis already ranked first.
**Ranking basis:** Section 5.6 (#stage-06).

- **Current:** W's Execute loop says that new tests must fail. M applies a failing-test
  condition to every milestone and rejects setup work that no test can show.
- **Proposal:** For behavior changes and defect repairs, record why the new regression
  or acceptance check fails before the repair and passes afterward.
  An import error, broken fixture, or missing tool does not establish that a test
  detects the intended behavioral defect.
  Give setup, documentation, and refactoring work suitable evidence instead of
  forcing an artificial failing behavioral test. Preserve tests-first work where
  it adds useful evidence.
- **Report:** Section 5.6, "Establish tests and expected results" (#stage-06).
  Also Section 5.5 (#stage-05) and Section 5.10 (#stage-10).
- **Why:** The reason for a failure matters more than the presence of a red result.
- **Status (November 19, 2026):** Partly delivered. `/write-tests` accepts a failing test only
  when the behavior is missing, not for a syntax error, a broken fixture or a wrong import, and
  its report says how each test fails. Not delivered: a kept record of that reason, and other
  evidence for setup, documentation and refactoring work.

---

#### - [ ] Rank 16 | REPORT-15 | Match evidence to the kind of system

**Proposed resolution (Claude, November 20, 2026; the user did not decide it):** Reject: the design already gives each requirement a test level, and the modules select the checks.

**Expected impact:** Medium; system-dependent.
**Ranking reason:** Adds the checks that matter to the actual workload and avoids irrelevant ceremony. Amplifies earlier controls rather than replacing them.
**Ranking basis:** Section 5.14 (#system-types) and Appendix 2 (#production).

- **Current:** The generator selects optional stack modules, but W applies the same
  execution loop and milestone template to every project.
- **Proposal:** Keep one shared workflow with applicable evidence profiles.
  - A script needs file-effect, exit-status, rerun, and interruption checks.
  - A data workflow needs reconciliation, schema, backfill, and recovery evidence.
  - A service needs contract, timeout, concurrency, and compatibility evidence.
  - A user interface needs interaction, visual, and accessibility evidence.

  Use only the records and checks needed for the actual scope. Several records can
  share a document if their ownership and links remain clear.
  Do not turn the report's 13 stages into 13 mandatory documents or repeated approvals
  for decisions the user already made.
- **Report:** Section 5.14, "Adapt the same workflow to different systems"
  (#system-types). Also Section 4.2 (#artifacts) and Appendix 2 (#production).
- **Why:** Proportionate evidence makes the workflow reusable without adding needless work.

---

#### - [ ] Rank 17 | USER-06 | Remove unjustified rigidity from instructions

**Proposed resolution (Claude, November 20, 2026; the user did not decide it):** Approve: audit `CLAUDE_GOLDEN.md` one time. Each rule goes into a tool, stays with a reason, or is deleted.

**Expected impact:** Medium; conditional.
**Ranking reason:** Can remove constraints that force poor designs. Benefit depends on retaining approved contracts, acceptance criteria, and evidence gates.
**Ranking basis:** Sections 5.2 (#stage-02), 5.4 (#stage-04), and Appendix 3 (#quality).

> Reduce overly specific instructions.
> Give AI room to choose how to meet the requirements.
> Review constraints that could cause bugs or other issues.
> Source: User, original idea 6.

---

#### - [ ] Rank 18 | USER-05 | Choose source structure during design

**Proposed resolution (Claude, November 20, 2026; the user did not decide it):** Approve: one line in `/write-design` says that the design names the folder layout.

**Expected impact:** Low-medium.
**Ranking reason:** Clear responsibility boundaries can help maintainability. Folder names alone do not establish cohesion, correctness, or sound architecture.
**Ranking basis:** Section 5.4 (#stage-04) and Appendix 3 (#quality); report-informed assessment of a user proposal.

> Research common source folder structures before choosing the layout.
> Include frontend, backend, and named feature or component subfolders where appropriate.
> Source: User, original idea 5.

---

#### - [ ] Rank 19 | USER-07 | Keep the core workflow language-independent

**Proposed resolution (Claude, November 20, 2026; the user did not decide it):** Close as delivered: the workflow is the same in each project, and the language rules are in modules.

**Expected impact:** Low direct impact.
**Ranking reason:** Improves reuse and language choice across projects. It does not directly improve a given program when its current language already fits.
**Ranking basis:** Section 2.1 (#scope), 5.4 (#stage-04), and 5.14 (#system-types); report-informed assessment of a user proposal.

> Support different programming languages without tying the core workflow to one language.
> Source: User, original idea 7.

---

#### - [ ] Rank 20 | USER-04 | Collect linters and checkers in one folder

**Proposed resolution (Claude, November 20, 2026; the user did not decide it):** Reject: each tool looks for its config at the project root, and the scripts are already in `scripts/`.

**Expected impact:** Low direct impact.
**Ranking reason:** Simplifies maintenance of the workflow tools. Moving files does not improve the checks or the generated program by itself.
**Ranking basis:** Sections 5.8 (#stage-08) and Appendix 3 (#quality); indirect assessment, not a report recommendation for this folder layout.

> Collect the linting and checking scripts and their configurations in a single dedicated folder.
> Source: User, original idea 4.

---

#### - [ ] Rank 21 | USER-01 | Rename the project to SDD Workflow

**Proposed resolution (Claude, November 20, 2026; the user did not decide it):** Close: the framework has the name sherpa now, and `project-init` says what the skill does.

**Expected impact:** No direct impact.
**Ranking reason:** Improves naming and communication. A rename does not change generated behavior, reliability, or maintainability.
**Ranking basis:** Appendix 3 (#quality); indirect assessment, not a report recommendation to rename the project.

> Rename project-init to "SDD Workflow".
> SDD stands for Spec Driven Development.
> Source: User, original idea 1.

---

### E. From the real runs and the trial of November 21, 2026

The runs are in the README, "Checked in real Claude Code sessions". An idea from them has the ID
RUN-NN and no rank. RUN-06 and RUN-07 came from the trial of three test writers, and they are
approved (Part 1).

#### - [ ] RUN-01 | A review finding about a test is never repaired

**Proposed resolution (Claude, November 21, 2026; the user did not decide it):** The runner sends
each finding about a file in `tests/` to a second test session, which cannot read `src/`. The
build session then makes the changed tests pass.

- **Current:** The repair session may not edit `tests/` (R). It rejects each finding about a
  test, and the finding stays. The runner counts it, and the milestone merges with it.
- **Seen:** In the real run, the test session did not obey the design: it ran the program in the
  test process, not as a process. The two reviews reported this, and no session repaired it. The
  cause of that test is solved (ruff now permits `subprocess` in `tests/**`), but the gap in the
  repair is not.
- **Proposal:** After the review, the runner divides the findings by their file. A finding about
  a file in `tests/` goes to a second test session with the rules of the first one. If that
  session changed a test, a build session runs again, and then the last review.
- **Seen again:** In the second real run, the repair session rejected a finding that a test is
  missing (the cut of a slug at a hyphen). It also made a new public function, `cut_slug`, and
  added no unit test, because it may not edit `tests/`. The last review reported the missing
  unit test, and the milestone merged with it. So a repair session that adds code also adds a
  gap that nobody repairs.
- **Alternative:** Only report such a finding to the user. This adds no session, and the finding
  stays until the user plans a fix milestone.
- **Why:** The session that writes the code must never change its tests. Thus only a test
  session can repair a test.
- **Cost:** One or two more sessions for a milestone with such a finding.

---

#### - [ ] RUN-02 | The findings that stay do not stop the merge

**Proposed resolution (Claude, November 21, 2026; the user did not decide it):** A `high`
finding of the last review blocks the milestone, with the finding as its question. A `medium` or
`low` finding stays in the report, as now.

- **Current:** A finding that the last review still reports is counted, and the milestone merges
  with it at each severity (W, R). The user approved this on November 20, 2026.
- **Seen:** In the real run, the first review reported 2 findings and the last review 5. One of
  the new findings was a fault against a requirement, with the severity `medium`. The milestone
  merged with it.
- **Why:** The base branch must hold only checked work. One run is weak evidence, and a review
  does not give the same findings each time, so a stop for each finding costs many stops.

---

#### - [ ] RUN-03 | `python` on the PATH of a session

**Proposed resolution (Claude, November 21, 2026; the user did not decide it):** The runner puts
the folder of its own Python, and its `Scripts` folder, first on the PATH of each session.

- **Current:** The runner (R) checks that its own Python is the project's environment. It does
  not check the PATH that the sessions get.
- **Seen:** In the real run, the runner started from the environment's `python.exe` without
  `conda activate`, and its check passed. The sessions found no `python`: the test session did
  not run its tests, and the first try of the repair session did not run the Gate.
- **Why:** A session that cannot run the checks must not depend on how the user started the
  runner.

---

#### - [ ] RUN-04 | Files written through the shell

**Proposed resolution (Claude, November 21, 2026; the user did not decide it):** The prompts of
the runner tell a session to write files only with the Edit and Write tools. This is advice, not
a guard.

- **Current:** A session can write a file with a shell command. The edit hook does not run for
  that file, and a path rule such as `Edit(./tests/**)` does not cover the shell. The runner's
  hashes of `tests/` are the guard for the tests.
- **Seen:** In the real run, the build session wrote its files with PowerShell. One character in
  `docs/plan.md` was damaged, and the session repaired it and amended its commit.
- **Why:** The lint at each edit saves a failed commit, and the edit tools keep the encoding of
  a file.

---

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
- The real runs of November 21, 2026 -> RUN-01 to RUN-04, no rank. RUN-05 is built (stage 10).
- The trial of three test writers, November 21, 2026 -> RUN-06 and RUN-07, no rank. Both are
  approved (Part 1).
- The build of the approved changes -> IMPL-01 and IMPL-02, no rank.
- The user's list of November 21, 2026 -> USER-12 to USER-24, no rank (section G). All of them
  are decided (Part 1).

The other user ideas and report proposals were decided on November 20, 2026 (Part 1). No
proposal in Part 2 is implemented or approved.
