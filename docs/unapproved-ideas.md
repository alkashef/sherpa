# Unapproved ideas

Ideas for sherpa's workflow that nobody approved. An idea is not a requirement: never design, plan,
test or build from this file. An idea becomes work only when the user approves it.

- Approved for recording: October 17, 2026
- Consolidated: October 17, 2026
- Renamed from `todo.md`: November 19, 2026
- Reviewed with the user, one idea at a time: November 20, 2026

## What left this file

On November 20, 2026 the user decided ranks 1 to 12 and added two ideas (USER-10: date-based
versions and light releases; USER-11: a branch for each milestone). The approved changes and
their designs are in `docs/implementation-order.md`. Their first text is in the git history of
this file.

Ranks 13 to 21 are still here. Nobody approved them. In the review of November 20, 2026 Claude
proposed a resolution for each one, and the user did not decide them. The review stopped at
rank 13.

## Source and review context

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

## The ranking

The rank numbers come from the first list of 21 proposals, ordered by their expected effect on
the quality of the programs that the workflow produces. The order is engineering judgment, not a
measured effect. Ranks 1 to 12 left the file, so the list starts at rank 13. A rank shows
priority only. The stable IDs (USER-NN and REPORT-NN) identify an idea.

---

## The 9 open proposals, in the order of their rank

Source labels distinguish the user's proposals from report-derived extensions.
Report-derived proposals adapt the report to the reviewed repository.
They do not imply that the report mandates a particular skill or file layout.

### - [ ] Rank 13 | REPORT-01 | Record a factual baseline before changes

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

### - [ ] Rank 14 | REPORT-10 | Repeatable installation, release, and checked handover

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

### - [ ] Rank 15 | REPORT-05 | Prove that failing tests detect the intended defect

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

### - [ ] Rank 16 | REPORT-15 | Match evidence to the kind of system

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

### - [ ] Rank 17 | USER-06 | Remove unjustified rigidity from instructions

**Proposed resolution (Claude, November 20, 2026; the user did not decide it):** Approve: audit `CLAUDE_GOLDEN.md` one time. Each rule goes into a tool, stays with a reason, or is deleted.

**Expected impact:** Medium; conditional.
**Ranking reason:** Can remove constraints that force poor designs. Benefit depends on retaining approved contracts, acceptance criteria, and evidence gates.
**Ranking basis:** Sections 5.2 (#stage-02), 5.4 (#stage-04), and Appendix 3 (#quality).

> Reduce overly specific instructions.
> Give AI room to choose how to meet the requirements.
> Review constraints that could cause bugs or other issues.
> Source: User, original idea 6.

---

### - [ ] Rank 18 | USER-05 | Choose source structure during design

**Proposed resolution (Claude, November 20, 2026; the user did not decide it):** Approve: one line in `/write-design` says that the design names the folder layout.

**Expected impact:** Low-medium.
**Ranking reason:** Clear responsibility boundaries can help maintainability. Folder names alone do not establish cohesion, correctness, or sound architecture.
**Ranking basis:** Section 5.4 (#stage-04) and Appendix 3 (#quality); report-informed assessment of a user proposal.

> Research common source folder structures before choosing the layout.
> Include frontend, backend, and named feature or component subfolders where appropriate.
> Source: User, original idea 5.

---

### - [ ] Rank 19 | USER-07 | Keep the core workflow language-independent

**Proposed resolution (Claude, November 20, 2026; the user did not decide it):** Close as delivered: the workflow is the same in each project, and the language rules are in modules.

**Expected impact:** Low direct impact.
**Ranking reason:** Improves reuse and language choice across projects. It does not directly improve a given program when its current language already fits.
**Ranking basis:** Section 2.1 (#scope), 5.4 (#stage-04), and 5.14 (#system-types); report-informed assessment of a user proposal.

> Support different programming languages without tying the core workflow to one language.
> Source: User, original idea 7.

---

### - [ ] Rank 20 | USER-04 | Collect linters and checkers in one folder

**Proposed resolution (Claude, November 20, 2026; the user did not decide it):** Reject: each tool looks for its config at the project root, and the scripts are already in `scripts/`.

**Expected impact:** Low direct impact.
**Ranking reason:** Simplifies maintenance of the workflow tools. Moving files does not improve the checks or the generated program by itself.
**Ranking basis:** Sections 5.8 (#stage-08) and Appendix 3 (#quality); indirect assessment, not a report recommendation for this folder layout.

> Collect the linting and checking scripts and their configurations in a single dedicated folder.
> Source: User, original idea 4.

---

### - [ ] Rank 21 | USER-01 | Rename the project to SDD Workflow

**Proposed resolution (Claude, November 20, 2026; the user did not decide it):** Close: the framework has the name sherpa now, and `project-init` says what the skill does.

**Expected impact:** No direct impact.
**Ranking reason:** Improves naming and communication. A rename does not change generated behavior, reliability, or maintainability.
**Ranking basis:** Appendix 3 (#quality); indirect assessment, not a report recommendation to rename the project.

> Rename project-init to "SDD Workflow".
> SDD stands for Spec Driven Development.
> Source: User, original idea 1.

---

## Source map

- Original user idea 1 -> USER-01, rank 21.
- Original user idea 4 -> USER-04, rank 20.
- Original user idea 5 -> USER-05, rank 18.
- Original user idea 6 -> USER-06, rank 17.
- Original user idea 7 -> USER-07, rank 19.
- REPORT-01 -> rank 13. REPORT-10 -> rank 14. REPORT-05 -> rank 15. REPORT-15 -> rank 16.

The other user ideas and report proposals were decided on November 20, 2026
(`docs/implementation-order.md`). No proposal in this file is implemented or approved.
