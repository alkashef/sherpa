# Implementation order

The user approved a set of workflow changes on November 20, 2026. They came from
`docs/unapproved-ideas.md` (ranks 1 to 12, USER-10 and USER-11). The eight stages below are
built. This file now holds the work that is left, in the order to do it. Delete an item in the
commit that finishes it.

All paths are below `skills/project-init/` unless they start with `tests/` or `docs/`.

## Built

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

## Left to do, in this order

Items 1 to 4 come from the real run of November 21, 2026 (README, "Checked in real Claude Code
sessions"). That run proved the condition of the user's decision on rank 3: a `claude -p`
session runs the built-in `/code-review` and `/code-review-sherpa`. The user did not decide
items 1 to 4. A fifth problem of that run is solved: `assets/ruff.toml` now permits `subprocess`
(S603) in `tests/**` (approved on November 21, 2026).

1. **A finding in `tests/`.** The repair session may not edit `tests/`, so it rejects each
   finding about a test, and the finding stays. Decide who repairs it.
2. **The findings that stay.** The last review can report more findings than the first one, and
   the milestone merges with them at each severity. In the real run one of them was a fault
   against a requirement. Decide if a `high` finding stops the merge.
3. **`python` on the PATH of a session.** The runner checks its own Python, not the PATH that
   the sessions get. Started from the environment's `python.exe` without `conda activate`, the
   sessions find no `python`. Decide if the runner puts the environment first on the PATH of each
   session.
4. **Files written through the shell.** The build session wrote its files with PowerShell. The
   edit hook did not run, and a character in `docs/plan.md` was damaged. Decide if the prompts
   tell a session to write files only with the Edit and Write tools.
5. **A review that changed a file.** The runner finds the change and counts the session as
   failed. It does not undo the change, and the retry cannot edit, so the run stops and the user
   cleans the branch by hand. Decide if the runner must undo the change itself.
6. **A refused `M<n>: blocked` commit.** If the pre-commit hook refuses that commit on the base
   branch, `docs/plan.md` stays uncommitted there and the runner shows only git's output. The
   partial work is safe in the milestone branch. Give the user the steps to finish.
7. **Module boundaries for JavaScript.** `check.py` checks the table "Module boundaries" for
   Python only.
8. **Permissions for a milestone in chat.** `.claude/settings.json` asks before
   `git checkout -b`, `git merge --ff-only` and `git branch -d`. A milestone that `/sdd` builds
   in chat needs them. Decide if they go on the allow list.
9. **The reports in `docs/v2/`.** The report, the presentation and the demo show the workflow
   before these changes. A `v3/` must show the branch, the review, the human test, the live
   checks and the releases.
10. **Not run in a real session:** `/sdd`, a milestone that blocks, and a human test.
11. **Deferred by the user:** property and mutation checks (rank 1).

## Decided with no work

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
