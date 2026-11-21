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

1. **Not run in a real session:** `/sdd`, and a milestone that a build session blocks with
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

---

## Part 2: ideas that nobody approved

Ranks 13 to 21 of the first list are still here. In the review of November 20, 2026 Claude
proposed a resolution for each one, and the user did not decide them. The review stopped at
rank 13. The ideas with the IDs IMPL-NN and RUN-NN came later, and the user did not decide them.

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

### E. From the real run of November 21, 2026

The run is in the README, "Checked in real Claude Code sessions". An idea from it has the ID
RUN-NN and no rank.

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

### F. Source map

- Original user idea 1 -> USER-01, rank 21.
- Original user idea 4 -> USER-04, rank 20.
- Original user idea 5 -> USER-05, rank 18.
- Original user idea 6 -> USER-06, rank 17.
- Original user idea 7 -> USER-07, rank 19.
- REPORT-01 -> rank 13. REPORT-10 -> rank 14. REPORT-05 -> rank 15. REPORT-15 -> rank 16.
- The real runs of November 21, 2026 -> RUN-01 to RUN-04, no rank. RUN-05 is built (stage 10).
- The build of the approved changes -> IMPL-01 and IMPL-02, no rank.

The other user ideas and report proposals were decided on November 20, 2026 (Part 1). No
proposal in Part 2 is implemented or approved.
