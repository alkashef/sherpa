---
name: sherpa
description: The way into spec-driven development (SDD) in this repo. Reads the state of docs/spec.md, docs/design.md, docs/plan.md and docs/unapproved-ideas.md and what the user asks, names the step of docs/workflow.md that comes next, and starts that one skill (/write-spec, /write-design, /write-plan, a milestone with /write-tests, or /find-bugs before a release). Use when the user asks for a new feature, a change, a fix of any size, the next step, to build or run milestones, to note or take up an idea, or where the project stands, even if they do not name a skill. Runs one step, then stops.
---

# Sherpa

Route the request to one step of the loop in `docs/workflow.md`, start that step's skill, and stop.
Hold no rule of your own: `docs/workflow.md` and `CLAUDE.md` own the rules. Never pass an approval
gate for the user.

## 1. Read the state

Read the files, not memory:

- **Spec:** the `Status` line at the top of `docs/spec.md` (`Draft` or `Approved`), and its table
  "Assumptions and open questions".
- **Design:** the Status of each decision in `docs/design.md` (`Decided`, `Proposed` or
  `Superseded`), and its table "Open design questions". The design is approved when no decision is
  `Proposed` and no question is open. Compare the date of the last commit of each file
  (`git log -1 --format=%cs -- docs/spec.md`, then the same for `docs/design.md`). A spec commit
  newer than the last design commit means the design may be stale.
- **Plan:** the rows of "Milestones at a glance" in `docs/plan.md`, and the Status of each (`open`,
  `blocked`, `approved`).
- **Ideas:** the lines under "Ideas" in `docs/unapproved-ideas.md`. They are not requirements.
- **Git:** `git status --short`, whether the branch is ahead of its remote, and whether a branch
  `milestone/M<n>` exists (`git branch --list "milestone/*"`): a milestone that did not finish.

If a state is unclear (for example, you cannot tell whether the design covers the newest spec), ask
the user that one question before you route.

## 2. Sort the request

| The user asks for | Step | Skill |
| --- | --- | --- |
| New or changed behavior, or a fix where the spec is silent or wrong | 1. Spec | `/write-spec` |
| A change of architecture, data, interfaces, settings or libraries, with no change of behavior | 2. Design | `/write-design` |
| Milestones for an approved spec and design | 3. Plan | `/write-plan` |
| A fix of any size, of behavior the spec already states | 3. Plan: one fix milestone | `/write-plan` |
| To build, run or go on with the milestones | 4. Execute | see 4 below |
| A release | none | see 4 below |
| To look for bugs before a release | none | `/find-bugs` |
| To note an idea for later | none | add one line to `docs/unapproved-ideas.md` |
| To take up an idea from `docs/unapproved-ideas.md` | the row above that fits the idea | that row's skill |
| Where the project stands, or what is next | none | the status report of 3 below |

When the request does not say which row it is, ask one question. Quote the user's words.

To note an idea, write it in the user's words as `- <YYYY-MM-DD>: <the idea>`, and do nothing else
with it. To take one up, sort it like any other request; the skill that takes it deletes its line.
Never build, plan or design from an idea that did not pass its step's approval.

## 3. Check the order, then route

The loop runs in order. Before you start a step, check that the steps before it are done:

1. A spec in `Draft` comes first: resume `/write-spec`, or ask the user to approve it.
2. A design that is stale for the approved spec, or that has a `Proposed` decision or an open
   design question, comes next: `/write-design`.
3. A plan that is missing for an approved design comes next: `/write-plan`.
4. A `blocked` milestone comes before every other milestone: show its **Blocked** entry, and ask the
   user to approve or change it (`docs/workflow.md`, Approval). Do not edit its entries.
5. Uncommitted changes to `docs/` come before a run: name them, and ask the user to commit them.

If the request skips a step (for example, "build X" when X is not in the spec), say which step comes
first and why, and route there.

Before you start the skill, tell the user in two lines: the state you found, and the step you start.
For a status request, give only those lines, the number of unapproved ideas, and the next command.

## 4. Execute

- **Default:** give the runner command for the open rows:
  `python scripts/milestones-runner.py` (with `--start` and `--end` when the user names milestones).
  The user runs it in a terminal; it handles retries, timeouts and logs.
- **When the user asks to build a milestone in this chat:** run it as `docs/workflow.md`, Execute,
  says, in this order:
  1. Make the branch: `git switch -c milestone/M<n>`.
  2. Run `python scripts/milestones-runner.py --tests-only M<n>`. It runs the test session in a
     folder without the code, with the test writer of `config/test-writer.json`, and checks the
     tests. If it reports a problem or a block, stop and show it to the user.
  3. Build in this session without changing any file in `tests/`, run the checks, and commit. Do
     not push.
  4. Run `python scripts/milestones-runner.py --review-only M<n>`: the review with
     `/code-review-sherpa`, in a worktree.
     Repair the findings about the code. For the findings about tests, run
     `python scripts/milestones-runner.py --tests-only M<n> --review-findings`; if it changed a
     test, make the tests pass and commit as `M<n>: test repairs`. Then run `--review-only M<n>`
     one more time. A finding of that last review that is `high`, or whose rule is a requirement
     ID, blocks the milestone: ask the user. Report each other finding as a `FINDING:` line.
  5. Merge: `git switch main` (the base branch), `git merge --ff-only milestone/M<n>`, `git push`
     and `git branch -d milestone/M<n>`.
  6. If the block has a **Human test** entry, tell the user what to test, and wait for the answer.

  Ask the user only for a blocker of step 5 of the workflow; decide everything else as the Rules of
  `docs/workflow.md` say, and report each decision as a `DECISION:` line. One milestone per
  request.
- **When the user asks for a release:** give the command `python scripts/release.py M<n>`, where
  M<n> is the last milestone of the release. The user runs it in a terminal. Before it, offer
  `/find-bugs`: it looks for bugs in the code changed since the last release, and each bug becomes
  a fix milestone.

## 5. Stop

Run one skill, then stop. When it ends, tell the user the next step in one line, for example
"Next: approve the design, then run `/sherpa` again." Never start the next step yourself.
