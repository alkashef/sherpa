# Workflow

The same in every project. Project-specific rules are in `CLAUDE.md`.

## The files

| File | Role | Who edits |
| --- | --- | --- |
| `docs/spec.md` | What to build: requirements with IDs | The user owns it. The AI edits it with `/write-spec` and the user's approval |
| `docs/design.md` | How to build it: architecture, data, interfaces, settings, test design, decisions | AI, with `/write-design` |
| `docs/plan.md` | What is left: only unfinished milestones, with their questions and approvals | AI, with `/write-plan`; the user adds approvals |
| `docs/unapproved-ideas.md` | What may come later: ideas that nobody approved | The user, and the AI when the user asks it to note an idea |
| `docs/releases.md` | What was released: one row for each release | `scripts/release.py`, when the user starts it |

Each fact lives in one file. Finished work is recorded by git history, not by the docs.

A requirement has an ID (`AREA-NNN`, or `NFR-NNN` for a non-functional one), an acceptance example has an `EX-NNN`, and a design decision has a `DEC-NNN`. Never renumber or reuse an ID. `/write-spec` gives a requirement its ID when it adds it.

## The loop

`/sdd` is the way in: it reads the state of these files and what the user asks, names the step below that comes next, and starts that step's skill. It runs one step, then stops.

1. **Spec.** For a new project or a change, the user runs `/write-spec`. The AI interviews the user, one question at a time, and writes the requirements into `spec.md` as a draft (`Status: Draft`). For a spec that is already approved, it proposes each change first. The user approves the spec; then `Status` is `Approved`. Each requirement is one EARS statement that a test can check without the design. The acceptance examples (`EX-NNN`) list the cases of each user scenario: first the most likely cases, in full, then the edge cases. For each external system, the spec says what the program does when that system fails. The requirements and these examples are the tests designed from the spec.
2. **Design.** Once the spec is approved, the user runs `/write-design`. The AI updates `design.md` and asks only what it cannot decide. If the design needs a different requirement, it proposes the spec change; the user approves it. The design shows the components and their interfaces in one diagram, lists the module boundaries (the checks enforce them), gives each requirement a test level (`unit`, `e2e`, `ui` or `live`) and names every interface a test needs. The user approves the design: then no decision is `Proposed` and no design question is open.
3. **Plan.** Once the design is approved, the user runs `/write-plan`. The AI turns the spec and design into milestones in `plan.md`: for each, a row in the table "Milestones at a glance" (at the top, so the status of every milestone is visible at a glance) and a block under "Milestones" (templates below). A milestone gets a human test only when it completes a user scenario that no tool can prove; the plan keeps the human tests few, and the table shows them. It shows the table first; the user approves it. It numbers the milestones from the counter at the top of `plan.md`, then advances the counter.
4. **Execute.** Work one milestone at a time, in order, in its own branch and in separate sessions. In chat, a subagent is the test session and another subagent is the review session.
   1. Make the branch `milestone/M<n>` from the base branch (the branch where the work starts), and work there.
   2. **Test session** (`/write-tests`): write the tests from the spec's requirements and examples and from the design, without reading `src/`. Name each after the requirement ID it verifies, and after the example ID when it comes from an example.
   3. Run them; each new test must fail because the behavior is missing. Do not commit.
   4. **Build session:** read the design sections that the Refs name, then implement the smallest change that passes. Do not change a file in `tests/`; a test that looks wrong is a blocker (step 5).
   5. Run the checks: `python scripts/check.py` (the tests, and the type check and lint named in `CLAUDE.md`) and `python scripts/spec_coverage.py M<n>` (each requirement ID in its Refs, and each acceptance example of those requirements, has a test or a `Manual:` entry). If any fail, go back to step 4.4.
   6. Update docs the change made inaccurate (README, design).
   7. Delete the milestone's row and block from `plan.md`.
   8. Commit only the files this milestone changed, with the message `M<n>: <title>`. The pre-commit hook runs the checks again. Do not push.
   9. **Review session** (`/code-review-sherpa`): a fresh session that changes no file reviews the diff of the branch, first with the built-in `/code-review` if Claude Code has it, and reports each finding as a `FINDING:` line. If it has findings, a session repairs them (it changes no file in `tests/`, passes the checks again and commits as `M<n>: review repairs`), then a last review runs. A finding that the last review still reports stays in the report; it does not stop the milestone.
   10. Merge: move the base branch to the milestone branch with `git merge --ff-only`, push the base branch, and delete the milestone branch. Do not start the next milestone until the push succeeds.
   11. **Human test:** if the block has a **Human test** entry, tell the user what to test and wait for the answer. A fault that the user finds is a fix milestone.
5. **Blocked.** If a milestone needs something it may not do on its own, stop it. These are the only reasons: a new or changed requirement in `spec.md`, an action `CLAUDE.md` forbids, a new flow of user data to an external service, real user data, a secret in a committed file, a dependency that `design.md` does not name in a `Decided` decision, or a test that the build session finds wrong. In `plan.md`, set its Status to `blocked` and add a **Blocked** entry to its block (template below). Change nothing else and commit nothing: the other changes stay in the milestone branch. In an unattended run, the runner commits them there as `M<n>: partial work`, commits `plan.md` alone on the base branch with the message `M<n>: blocked`, and pushes the base branch. In chat, ask the user and wait.
6. **Approval.** The user answers in the milestone's block: an **Approval** entry with the decision, and Status `approved`. Then the user commits `plan.md` and the milestone runs again, from the work that its branch kept. The approval permits exactly what it says, even an action the rules otherwise forbid, and nothing more. A settings rule denies editing `spec.md` in an unattended run, so for a change to the spec the user makes the edit and the Approval says so. To refuse, the user rewrites or deletes the milestone instead.

## Rules

- Never edit `spec.md` without the user's approval, given in chat or in an **Approval** entry. Running `/write-spec` allows draft requirements only; the spec is final when the user approves it.
- If the spec and the design disagree, the spec wins. In a milestone, in chat or unattended, fix the design and record it as a decision (below). Outside a milestone, stop and ask.
- Stay in scope. When in doubt about the spec, ask. Only the spec is locked: a milestone never changes it. Everything else that step 5 does not name as a blocker may change in a milestone, in chat or unattended, without a question: a design decision (also a `Decided` one), a module, an interface, a setting. Decide it, record it and report it.
- A decision in a milestone: pick the most conservative option and carry on. When it changes the design, add a `DEC-NNN` (the next free number) to `design.md` with the Status `Proposed`, and write "auto-decided in M<n>, review" in its Why. When it replaces a `Decided` decision, set that one to `Superseded`. The final report has one line per decision: `DECISION: <what> | <why> | <DEC-NNN or none>`. The user reviews these lines after the run and reverts or approves each.
- A finding of a review: `FINDING: <high, medium or low> | <file>:<line> | <rule or smell> | <remedy>`. A review reports only a finding that it is sure of. The user reads the findings that a milestone kept after the run.
- An idea in `unapproved-ideas.md` is not a requirement and not a decision. Never design, plan, test or build from it. It becomes work only through step 1, 2 or 3, with the approval that step needs. The skill that takes an idea up deletes its entry. To note an idea, add one line; do not act on it.
- Never report tests as passed unless they ran. Show failing output.
- A milestone run calls no live external service (an LLM, a paid API, a production database) and uses no real user data. It does not start the app for a person. A test uses a real local part where one exists (a database file in a temporary folder, a server that the test starts on 127.0.0.1) and a fake only for an external service. Its Gate is the checks of step 4.
- A live check is a test in `tests/live/` that calls a live external service with a test account. No milestone runs it. `python scripts/live_checks.py` runs the live checks after the milestones, and only when `plan.md` holds the user's approval with a budget ceiling under "## Live checks" (template below). The tests stop before they pass the ceiling.
- Every fix, however small, is a milestone. A fix that changes no requirement and no design decision goes straight to `/write-plan`: one milestone whose Tests first holds a test that fails while the fault is there.
- A release is a cut point. The user runs `python scripts/release.py M<n>`: the release holds every milestone up to M<n>, its version is the date (`YYYY.MM.DD`), and the script builds it into `dist/`, tags the commit and adds a row to `docs/releases.md`. A version belongs to a release, not to a milestone. After the first release, a change that breaks the data or an interface of a released version needs a decision in `design.md` that records the transition.

## Running milestones unattended

`python scripts/milestones-runner.py [--start N] [--end N] [--retries N] [--resume]
[--timeout-minutes N]`, run by the user from a terminal with the project's conda environment
active, works through the table in order. Each milestone runs in its branch `milestone/M<n>`, in
`claude -p` sessions with the model and effort of its row, following steps 4 to 6: a test session,
a build session, a review session and, when the review has findings, a repair session and a last
review. The runner, not a session, merges the branch into the base branch, pushes and deletes the
branch. A build or repair session that changed a test file counts as not finished, and so does a
milestone whose sessions changed `docs/spec.md`, and a review session that changed a file.

The runner stops at a `blocked` row, at a milestone that becomes blocked (and prints its
question), at a human test that the user does not confirm, or at a milestone that did not finish
(its row is still in the table, git is not clean, or a check of the runner failed) after its
retries. A session that did not finish is tried again in a new session (`--retries`, default 1)
that continues from the changes the first one left and gets the reason for the failure; a session
that runs over `--timeout-minutes` (default 90) counts as not finished. After the last try the
runner stops; `--resume` starts the next run on that dirty tree and continues from it. After you
approve and commit, run it again: it continues with the approved milestone, from the work that its
branch kept.

When the milestones of the run are done, the runner runs `python scripts/live_checks.py` and
prints its result: passed, failed or not run. The runner shows a table of the run, redrawn each
second; its Decisions column counts the `DECISION:` lines of a milestone and its Findings column
counts the `FINDING:` lines of its last review, and you read the lines themselves in its logs.
Logs and timings go to `.claude/logs/`. It needs a clean git tree (except with `--resume`) and a
branch that pushes to a remote.

Each session starts with permission prompts off. Its guard rails are the rules in
`.claude/settings.json`: a `deny` rule always refuses, and an `ask` rule refuses when nobody can
answer. The runner does not start without that file, while the commit hook is off, or when
`python scripts/spec_coverage.py --consistency` finds an ID that the spec, the design and the plan
do not agree on.

Before a run, so that it does not stop for something known in advance:

1. Commit every doc change.
2. Approve and install the dependencies the plan needs. An `ask` rule denies `pip install` and
   `npm install` in an unattended run.
3. After a fresh clone, turn the commit hook on: `git config core.hooksPath .githooks`.
4. Make sure that `claude -p --permission-mode bypassPermissions "say ok"` works. An organisation
   policy can disable it.
5. Make sure that `git push` works without a prompt. A session cannot answer a sign-in window.
6. For live checks, write your approval and the budget ceiling under "## Live checks" in
   `plan.md`.

A milestone's Gate must be one that a session can meet alone: offline, with real local parts and
with fakes for the external services, in temporary folders, with no user data and no human step.
What only a person can judge is the **Human test** of its milestone: the runner prints it after
the merge and waits for your answer. What needs a live service is a live check.

## Milestone templates

The table "Milestones at a glance" has the columns Milestone, Description, Model, Effort, Human
test and Status. Model: `haiku`, `sonnet` or `opus` (the latest model of that family), or a full
model ID such as `claude-sonnet-5-5` to stay on one version. Effort: `low`, `medium`, `high`,
`xhigh` or `max`. Human test: `yes` or `no`. Status: `open`, then `blocked` and `approved` if it
needs the user (steps 5 and 6).

```markdown
| **M<n>** <title> | <one line: what it delivers> | <model> | <effort> | <yes or no> | open |
```

A block under "Milestones":

```markdown
### M<n> — <title>

- **Refs:** <requirement IDs (AREA-NNN, NFR-NNN)>, <design decisions (DEC-NNN)>.
- **Owner:** <module or file that owns the change>.
- **Tests first:** <test names, at least one per requirement ID and one per acceptance example, grouped as unit:, e2e:, ui:, live:>.
- **Build:** <the smallest change that passes them>.
- **Gate:** <what must be true before commit>.
- **Human test:** <only when the row says yes: what the user tests, step by step, and the result to expect>.
```

The entries a blocked milestone adds to the end of its block: **Blocked** by the AI (step 5), then
**Approval** by the user (step 6).

```markdown
- **Blocked:** <One sentence: what the milestone needs, and why it may not do it.>
  - <Each fact behind the stop, with its source: a spec row, a plan block, a rule, file and line.>
  - The other changes are kept in the milestone branch. To continue, approve one of these:
    1. <The narrowest permission that lets the milestone go on.>
    2. <Another way, if there is one.>
- **Approval:** <The user's decision, in the user's words.>
```

The section for the live checks, after the last milestone block. The user writes the first two
entries.

```markdown
## Live checks

- **Approval:** <The user's decision, in the user's words.>
- **Budget ceiling:** <The most that one run of the live checks may cost.>
- <requirement ID>: <test name in tests/live/>
```
