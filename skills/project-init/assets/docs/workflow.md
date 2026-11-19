# Workflow

The same in every project. Project-specific rules are in `CLAUDE.md`.

## The files

| File | Role | Who edits |
| --- | --- | --- |
| `docs/spec.md` | What to build: requirements with IDs | The user owns it. The AI edits it with `/write-spec` and the user's approval |
| `docs/design.md` | How to build it: architecture, data, interfaces, settings, test design, decisions | AI, with `/write-design` |
| `docs/plan.md` | What is left: only unfinished milestones, with their questions and approvals | AI, with `/write-plan`; the user adds approvals |
| `docs/unapproved-ideas.md` | What may come later: ideas that nobody approved | The user, and the AI when the user asks it to note an idea |

Each fact lives in one file. Finished work is recorded by git history, not by the docs.

A requirement has an ID (`AREA-NNN`, or `NFR-NNN` for a non-functional one), an acceptance example has an `EX-NNN`, and a design decision has a `DEC-NNN`. Never renumber or reuse an ID. `/write-spec` gives a requirement its ID when it adds it.

## The loop

`/sdd` is the way in: it reads the state of these files and what the user asks, names the step below that comes next, and starts that step's skill. It runs one step, then stops.

1. **Spec.** For a new project or a change, the user runs `/write-spec`. The AI interviews the user, one question at a time, and writes the requirements into `spec.md` as a draft (`Status: Draft`). For a spec that is already approved, it proposes each change first. The user approves the spec; then `Status` is `Approved`. Each requirement is one EARS statement that a test can check without the design. Where a requirement needs a concrete case, an acceptance example (`EX-NNN`) gives it. The requirements and these examples are the tests designed from the spec.
2. **Design.** Once the spec is approved, the user runs `/write-design`. The AI updates `design.md` and asks only what it cannot decide. If the design needs a different requirement, it proposes the spec change; the user approves it. The design gives each requirement a test level (`unit`, `e2e` or `ui`) and names every interface a test needs. The user approves the design: then no decision is `Proposed` and no design question is open.
3. **Plan.** Once the design is approved, the user runs `/write-plan`. The AI turns the spec and design into milestones in `plan.md`: for each, a row in the table "Milestones at a glance" (at the top, so the status of every milestone is visible at a glance) and a block under "Milestones" (templates below). It shows the table first; the user approves it. It numbers the milestones from the counter at the top of `plan.md`, then advances the counter.
4. **Execute.** Work one milestone at a time, in order, in two sessions. In chat, a subagent is the test session.
   1. **Test session** (`/write-tests`): write the tests from the spec's requirements and examples and from the design, without reading `src/`. Name each after the requirement ID it verifies.
   2. Run them; each new test must fail because the behavior is missing. Do not commit.
   3. **Build session:** implement the smallest change that passes. Do not change a file in `tests/`; a test that looks wrong is a blocker (step 5).
   4. Run the checks: `python scripts/check.py` (the tests, and the type check and lint named in `CLAUDE.md`) and `python scripts/spec_coverage.py M<n>` (each requirement ID in its Refs has a test or a `Manual:` entry). If any fail, go back to step 3.
   5. Update docs the change made inaccurate (README, design).
   6. Delete the milestone's row and block from `plan.md`.
   7. Commit only the files this milestone changed, with the message `M<n>: <title>`, then push. The pre-commit hook runs the checks again. Do not start the next milestone until the push succeeds.
5. **Blocked.** If a milestone needs something it may not do on its own, stop it. These are the only reasons: a new or changed requirement in `spec.md`, an action `CLAUDE.md` forbids, a new flow of user data to an external service, real user data, a secret in a committed file, a dependency that `design.md` does not name in a `Decided` decision, or a test that the build session finds wrong. In `plan.md`, set its Status to `blocked` and add a **Blocked** entry to its block (template below). Undo its other changes, so that `plan.md` is the only changed file, commit `plan.md` alone with the message `M<n>: blocked`, and push. Ask in chat too if the user is present.
6. **Approval.** The user answers in the milestone's block: an **Approval** entry with the decision, and Status `approved`. Then the user commits `plan.md` and the milestone runs again. The approval permits exactly what it says, even an action the rules otherwise forbid, and nothing more. A settings rule denies editing `spec.md` in an unattended run, so for a change to the spec the user makes the edit and the Approval says so. To refuse, the user rewrites or deletes the milestone instead.

## Rules

- Never edit `spec.md` without the user's approval, given in chat or in an **Approval** entry. Running `/write-spec` allows draft requirements only; the spec is final when the user approves it.
- If the spec and the design disagree, the spec wins. In a milestone, in chat or unattended, fix the design and record it as a decision (below). Outside a milestone, stop and ask.
- Stay in scope. When in doubt about the spec, ask. Only the spec is locked: a milestone never changes it. Everything else that step 5 does not name as a blocker may change in a milestone, in chat or unattended, without a question: a design decision (also a `Decided` one), a module, an interface, a setting. Decide it, record it and report it.
- A decision in a milestone: pick the most conservative option and carry on. When it changes the design, add a `DEC-NNN` (the next free number) to `design.md` with the Status `Proposed`, and write "auto-decided in M<n>, review" in its Why. When it replaces a `Decided` decision, set that one to `Superseded`. The final report has one line per decision: `DECISION: <what> | <why> | <DEC-NNN or none>`. The user reviews these lines after the run and reverts or approves each.
- An idea in `unapproved-ideas.md` is not a requirement and not a decision. Never design, plan, test or build from it. It becomes work only through step 1, 2 or 3, with the approval that step needs. The skill that takes an idea up deletes its entry. To note an idea, add one line; do not act on it.
- Never report tests as passed unless they ran. Show failing output.
- A milestone run calls no live external service (an LLM, a paid API, a production database) and uses no real user data. It does not start the app for a person; a test may start its own server on 127.0.0.1 with fakes at the external boundaries. Its Gate is the checks of step 4. A check that needs a live service or a person is a human check in `plan.md`.
- Every fix, however small, is a milestone. A fix that changes no requirement and no design decision goes straight to `/write-plan`: one milestone whose Tests first holds a test that fails while the fault is there.

## Running milestones unattended

`python scripts/milestones-runner.py [--start N] [--end N] [--retries N] [--resume]
[--timeout-minutes N]`, run by the user from a terminal with the project's conda environment
active, works through the table in order. Each milestone runs in two `claude -p` sessions, a test
session and then a build session, with the model and effort of its row, following steps 4 to 6. A
build session that changed a test file counts as not finished, and so does a milestone whose
sessions changed `docs/spec.md`. The runner stops at a `blocked` row, at a milestone that becomes
blocked (and prints its question), or at one that did not finish (its row is still in the table,
git is not clean, or a commit was not pushed) after its retries. A milestone that did not finish is
tried again in a new session (`--retries`, default 1) that continues from the changes the first one
left; a session that runs over `--timeout-minutes` (default 90) counts as not finished. After the
last try the runner stops; `--resume` starts the next run on that dirty tree and continues from it.
After you approve and commit, run it again: it continues with the approved milestone. The runner
shows a table of the run, redrawn each second; its Decisions column counts the `DECISION:` lines of
a milestone, and you read the lines themselves in its log. Logs and timings go to `.claude/logs/`.
It needs a clean git tree (except with `--resume`) and a branch that pushes to a remote.

Each session starts with permission prompts off. Its guard rails are the rules in
`.claude/settings.json`: a `deny` rule always refuses, and an `ask` rule refuses when nobody can
answer. The runner does not start without that file, or while the commit hook is off.

Before a run, so that it does not stop for something known in advance:

1. Commit every doc change.
2. Approve and install the dependencies the plan needs. An `ask` rule denies `pip install` and
   `npm install` in an unattended run.
3. After a fresh clone, turn the commit hook on: `git config core.hooksPath .githooks`.
4. Make sure that `claude -p --permission-mode bypassPermissions "say ok"` works. An organisation
   policy can disable it.
5. Make sure that `git push` works without a prompt. A session cannot answer a sign-in window.

A milestone's Gate must be one that a session can meet alone: offline, with fakes at the external
boundaries, in temporary folders, with no user data and no human step. Checks that need a live
service or a person are listed at the end of the plan under "## Human checks", one line each with
its requirement or decision ID. They are not part of any milestone: the user does them after the
run.

## Milestone templates

A row of the table "Milestones at a glance". Model: `haiku`, `sonnet` or `opus` (the latest model of
that family), or a full model ID such as `claude-sonnet-5-5` to stay on one version. Effort: `low`,
`medium`, `high`, `xhigh` or `max`. Status: `open`, then `blocked` and `approved` if it needs the
user (steps 5 and 6).

```markdown
| **M<n>** <title> | <one line: what it delivers> | <model> | <effort> | open |
```

A block under "Milestones":

```markdown
### M<n> — <title>

- **Refs:** <requirement IDs (AREA-NNN, NFR-NNN)>, <design decisions (DEC-NNN)>.
- **Owner:** <module or file that owns the change>.
- **Tests first:** <test names, one per requirement ID, grouped as unit:, e2e:, ui:>.
- **Build:** <the smallest change that passes them>.
- **Gate:** <what must be true before commit>.
```

The entries a blocked milestone adds to the end of its block: **Blocked** by the AI (step 5), then
**Approval** by the user (step 6).

```markdown
- **Blocked:** <One sentence: what the milestone needs, and why it may not do it.>
  - <Each fact behind the stop, with its source: a spec row, a plan block, a rule, file and line.>
  - Nothing else was changed. To continue, approve one of these:
    1. <The narrowest permission that lets the milestone go on.>
    2. <Another way, if there is one.>
- **Approval:** <The user's decision, in the user's words.>
```
