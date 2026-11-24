# Workflow

The same in every project. Project-specific rules are in `CLAUDE.md`.

## The files

| File | Role | Who edits |
| --- | --- | --- |
| `docs/spec.md` | What to build: requirements with IDs | The user owns it. The AI edits it with `/write-spec` and the user's approval |
| `docs/design.md` | How to build it: architecture, data, interfaces, settings, test design, decisions | AI, with `/write-design` |
| `docs/plan.md` | What is left: only unfinished milestones, with their questions and approvals | AI, with `/write-plan`. The user adds approvals |
| `docs/unapproved-ideas.md` | What may come later: ideas that nobody approved | The user, and the AI when the user asks it to note an idea |
| `docs/releases.md` | What was released: one row for each release | `scripts/release.py`, when the user starts it |

Each fact lives in one file. Finished work is recorded by git history, not by the docs. `python scripts/dashboard.py` shows these facts on one page in the browser: what needs you, the plan and the releases, the trace of each requirement to its design, milestone, tests and code, and a map of the code. It reads the files and git, writes nothing, and reads them again on Refresh.

A requirement has an ID (`AREA-NNN`, or `NFR-NNN` for a non-functional one), an acceptance example has an `EX-NNN`, and a design decision has a `DEC-NNN`. Never renumber or reuse an ID. `/write-spec` gives a requirement its ID when it adds it.

## The loop

`/sherpa` is the way in: it reads the state of these files and what the user asks, names the step below that comes next, and starts that step's skill. It runs one step, then stops.

1. **Spec.** For a new project or a change, the user runs `/write-spec`. The AI interviews the user, one question at a time, and writes the requirements into `spec.md` as a draft (`Status: Draft`). For a spec that is already approved, it proposes each change first. The spec gives each domain term one row in its glossary (Term, Meaning, Avoid), and the design and the code use the Term. The user approves the spec. Then `Status` is `Approved`. Each requirement is one EARS statement that a test can check without the design. The acceptance examples (`EX-NNN`) list the cases of each user scenario: first the most likely cases, in full, then the edge cases. For each external system, the spec says what the program does when that system fails. The requirements and these examples are the tests designed from the spec.
2. **Design.** Once the spec is approved, the user runs `/write-design`. The AI updates `design.md` and asks only what it cannot decide. If the design needs a different requirement, it proposes the spec change. The user approves it. The design shows the components and their interfaces in one diagram, draws the data model as one Mermaid `erDiagram`, lists the module boundaries (the checks enforce them), gives each requirement a test level (`unit`, `e2e`, `ui` or `live`) and names every interface a test needs. The user approves the design: then no decision is `Proposed` and no design question is open.
3. **Plan.** Once the design is approved, the user runs `/write-plan`. The AI turns the spec and design into milestones in `plan.md`: for each, a row in the table "Milestones at a glance" (at the top, so the status of every milestone is visible at a glance) and a block under "Milestones" (templates below). A milestone gets a human test only when it completes a user scenario that no tool can prove. The plan keeps the human tests few, and the table shows them. It shows the table first. The user approves it. It numbers the milestones from the counter at the top of `plan.md`, then advances the counter.
4. **Execute.** Work one milestone at a time, in order, in its own branch and in separate sessions. In chat, `python scripts/milestones-runner.py --tests-only M<n>` is the test session and `python scripts/milestones-runner.py --review-only M<n>` is the review session, with the same guards as in an unattended run.
   1. Make the branch with `git switch -c milestone/M<n>` from the base branch (the branch where the work starts), and work there.
   2. **Test session** (`/write-tests`): write the tests from the spec's requirements and examples and from the design. Name each after the requirement ID it verifies, and after the example ID when it comes from an example. The session runs in a temporary folder without the code: it holds the docs, the rules, the tool configs and `tests/`, but no `src/` and no `.git`. The AI that `config/test-writer.json` names writes the tests: Claude (the default), Antigravity, Codex or GitHub Copilot.
   3. The runner copies `tests/` back and checks it: ruff and mypy pass on `tests/`, each new test fails for a valid reason (a wrong value, or a missing module that the Owner names), and each older test passes. The exit code of the writer does not count. A problem goes back to the writer, with its error type and message and no line of the code, for one round of repair. Do not commit.
   4. **Build session:** read the design sections that the Refs name, then implement the smallest change that passes. Do not change a file in `tests/`. A test that looks wrong is a blocker (step 5).
   5. Run the checks: `python scripts/check.py` (the tests, and the type check and lint named in `CLAUDE.md`) and `python scripts/spec_coverage.py M<n>` (each requirement ID in its Refs, and each acceptance example of those requirements, has a test or a `Manual:` entry). If any fail, go back to step 4.4.
   6. Update docs the change made inaccurate (README, design).
   7. Delete the milestone's row and block from `plan.md`.
   8. Commit only the files this milestone changed, with the message `M<n>: <title>`. The pre-commit hook runs the checks again. Do not push.
   9. **Review session** (`/code-review-sherpa`): a fresh session reviews the diff of the branch in a temporary git worktree, first with the built-in `/code-review` if Claude Code has it, and reports each finding as a `FINDING:` line. The worktree is deleted after the review, so a change that the review makes cannot reach the branch. A finding names the file where the fix goes. A finding about `tests/` goes to a test session in the folder of step 2. If it changes a test, a build session makes the tests pass and commits as `M<n>: test repairs`. Any other finding goes to a repair session (it changes no file in `tests/`, passes the checks again and commits as `M<n>: review repairs`). Then a last review runs. A finding of the last review blocks the milestone (step 5) when its severity is `high`, or `medium` with a requirement ID as its rule. A `low` finding never blocks. The review rates wrong behavior against a requirement `high`, also when it reports it as a missing test. The other findings stay in the report. After the approval of that block, the decision and the findings of the block go to the repair sessions, and no new review runs: when the repairs change nothing, the runner merges; when they commit a change, the last review checks it, and its findings block as usual. The approval covers the code that the user saw. A repair or build session after the review that finds a test wrong reports a `BLOCKED:` line: the runner keeps its work in the branch and blocks the milestone, and after the approval a test session gets the decision before the build goes on. That approval covers only the test.
   10. Merge: `git switch main` (the base branch), `git merge --ff-only milestone/M<n>`, `git push`, and `git branch -d milestone/M<n>`. Do not start the next milestone until the push succeeds.
   11. **Human test:** if the block has a **Human test** entry, tell the user what to test and wait for the answer. A fault that the user finds is a fix milestone.
5. **Blocked.** If a milestone needs something it may not do on its own, stop it. These are the only reasons: a new or changed requirement in `spec.md`, an action `CLAUDE.md` forbids, a new flow of user data to an external service, real user data, a secret in a committed file, a dependency that `design.md` does not name in a `Decided` decision (the check and test tools of the project are approved), a test that the build session finds wrong, or a finding of the last review that blocks the merge (step 4.9). In `plan.md`, set its Status to `blocked` and add a **Blocked** entry to its block (template below). Change nothing else and commit nothing: the other changes stay in the milestone branch. In an unattended run, the runner commits them there as `M<n>: partial work`, commits `plan.md` alone on the base branch with the message `M<n>: blocked`, and pushes the base branch. In chat, ask the user and wait.
6. **Approval.** The user answers in the milestone's block: an **Approval** entry with the decision, and Status `approved`. Then the user commits `plan.md` and the milestone runs again, from the work that its branch kept. When a session made the block (not the last review), a test session gets the decision first, because no other session may change a test. It changes a test only when the decision says so. The approval permits exactly what it says, even an action the rules otherwise forbid, and nothing more. A settings rule denies editing `spec.md` in an unattended run, so for a change to the spec the user makes the edit and the Approval says so. To refuse, the user rewrites or deletes the milestone instead.

## Rules

- Never edit `spec.md` without the user's approval, given in chat or in an **Approval** entry. Running `/write-spec` allows draft requirements only. The spec is final when the user approves it.
- If the spec and the design disagree, the spec wins. In a milestone, in chat or unattended, fix the design and record it as a decision (below). Outside a milestone, stop and ask.
- Stay in scope. When in doubt about the spec, ask. Only the spec is locked: a milestone never changes it. Everything else that step 5 does not name as a blocker may change in a milestone, in chat or unattended, without a question: a design decision (also a `Decided` one), a module, an interface, a setting. Decide it, record it and report it.
- A decision in a milestone: pick the most conservative option and carry on. When it changes the design, add a `DEC-NNN` (the next free number) to `design.md` with the Status `Proposed`, and write "auto-decided in M<n>, review" in its Why. When it replaces a `Decided` decision, set that one to `Superseded` and change nothing else in its row: only the user makes a decision `Decided`. The final report has one line per decision: `DECISION: <what> | <why> | <DEC-NNN or none>`. The user reviews these lines after the run and reverts or approves each.
- A finding of a review: `FINDING: <high, medium or low> | <file>:<line> | <rule or smell> | <remedy>`. The file is the file where the fix goes: a missing test names a test file. A fault against a requirement that no test catches is a missing test, with the requirement ID as its rule. A review reports only a finding that it is sure of. The user reads the findings that a milestone kept after the run.
- An idea in `unapproved-ideas.md` is not a requirement and not a decision. Never design, plan, test or build from it. It becomes work only through step 1, 2 or 3, with the approval that step needs. The skill that takes an idea up deletes its entry. To note an idea, add one line. Do not act on it.
- Never report tests as passed unless they ran. Show failing output.
- A milestone run calls no live external service (an LLM, a paid API, a production database) and uses no real user data. It does not start the app for a person. A test uses a real local part where one exists (a database file in a temporary folder, a server that the test starts on 127.0.0.1) and a fake only for an external service. Its Gate is the checks of step 4.
- A live check is a test in `tests/live/` that calls a live external service with a test account. No milestone runs it. `python scripts/live_checks.py` runs the live checks after the milestones, and only when `plan.md` holds the user's approval with a budget ceiling under "## Live checks" (template below). The ceiling is an amount and a currency, such as `5 USD`. The tests get the amount in `LIVE_BUDGET_CEILING` and the currency in `LIVE_BUDGET_CURRENCY`, and stop before they pass the ceiling.
- Every fix, however small, is a milestone. A fix that changes no requirement and no design decision goes straight to `/write-plan`: one milestone whose Tests first holds a test that fails while the fault is there.
- At each push, the GitHub Actions workflow "Checks" installs the project on a clean machine from its dependency files and runs `python scripts/check.py`.
- Before a release, the user can run `/find-bugs`. It changes no code: it compares the code changed since the last release with the spec and the design, with most attention on the lines that no test runs, and reads the dependency audit and the surviving mutants of the workflow "Mutation tests" of GitHub Actions. Each bug becomes a fix milestone that the user approves. A finding that no requirement covers is a question about the spec.
- A test of a rule for all inputs is also a property test (Hypothesis, at most 50 examples). Mutation tests run only on demand, on Linux, in GitHub Actions.
- A release is a cut point. The user runs `python scripts/release.py M<n>`: the release holds every milestone up to M<n>, its version is the date (`YYYY.MM.DD`), and the script builds it into `dist/` with the installed versions (`pip freeze`, `npm ls --all`), tags the commit and adds a row to `docs/releases.md`. A version belongs to a release, not to a milestone. After the first release, a change that breaks the data or an interface of a released version needs a decision in `design.md` that records the transition.

## Running milestones unattended

`python scripts/milestones-runner.py [--start N] [--end N] [--retries N] [--resume]
[--timeout-minutes N]`, run by the user from a terminal with the project's conda environment
active, works through the table in order. Each milestone runs in its branch `milestone/M<n>`, in
`claude -p` sessions with the model and effort of its row, following steps 4 to 6: a test session
(by the test writer, in a folder without the code), a build session, a review session in a
worktree and, when the review has findings, the sessions that repair them and a last review. The
runner, not a session, merges the branch into the base branch, pushes and deletes the branch. A
build or repair session that changed a test file counts as not finished, and so does a milestone
whose sessions changed `docs/spec.md`, or changed a `Decided` row of `docs/design.md` in another
way than to set its Status to `Superseded`. Each session gets the folders of the project's conda
environment first on its PATH, and writes files with the Edit and Write tools.

The runner stops at a `blocked` row, at a milestone that becomes blocked (and prints its
question), at a human test that the user does not confirm, or at a milestone that did not finish
(its row is still in the table, git is not clean, or a check of the runner failed) after its
retries. A session that did not finish is tried again in a new session (`--retries`, default 1)
that continues from the changes the first one left and gets the reason for the failure. A session
that runs over `--timeout-minutes` (default 90) counts as not finished. After the last try the
runner stops. `--resume` starts the next run on that dirty tree and continues from it. After you
approve and commit, run it again: it continues with the approved milestone, from the work that its
branch kept.

When the milestones of the run are done, the runner runs `python scripts/live_checks.py` and
prints its result: passed, failed or not run. The runner shows a table of the run, redrawn each
second: the finished milestones, the one that runs now, and the planned ones in dark grey. Its
Decisions column counts the `DECISION:` lines of a milestone and its Findings column counts the
`FINDING:` lines of its last review, and you read the lines themselves in its logs. A Total row
gives the total time, and the last row a progress bar of the milestones done.
Logs and timings go to `.claude/logs/`. It needs a clean git tree (except with `--resume`) and a
branch that pushes to a remote.

Each session starts with permission prompts off. Its guard rails are the rules in
`.claude/settings.json`: a `deny` rule always refuses, and an `ask` rule refuses when nobody can
answer. A session loads only the settings of the project (`--setting-sources project,local`), so
the plugins and the hooks of the user's own settings stay out of a run. It loads no MCP server of
the user's account, such as a mail or chat connector (`--strict-mcp-config`): only the servers of
the project's `.mcp.json`, when its folder holds one. The runner does not start without that file, while the commit hook is off, when
`python scripts/spec_coverage.py --consistency` finds an ID that the spec, the design and the plan
do not agree on or a milestone whose Refs name a `Proposed` decision, when `python` on the PATH of a session is not the project's environment, or when
a test writer other than Claude does not answer one short prompt.

Before a run, so that it does not stop for something known in advance:

1. Commit every doc change.
2. Approve and install the dependencies the plan needs. An `ask` rule denies `pip install` and
   `npm install` in an unattended run.
3. After a fresh clone, turn the commit hook on: `git config core.hooksPath .githooks`.
4. Make sure that `claude -p --permission-mode bypassPermissions "say ok"` works. An organisation
   policy can disable it.
5. Make sure that `git push` works without a prompt. A session cannot answer a sign-in window.
6. For live checks, write your approval and the budget ceiling (an amount and a currency, such as
   `5 USD`) under "## Live checks" in `plan.md`.
7. For a test writer other than Claude, sign in to its command line once: `codex login`, one
   interactive `agy` session, or `COPILOT_GITHUB_TOKEN`. `--test-writer` overrides
   `config/test-writer.json` for one run.

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
- **Budget ceiling:** <An amount and a currency, for example `5 USD`: the most that one run of the live checks may cost.>
- <requirement ID>: <test name in tests/live/>
```
