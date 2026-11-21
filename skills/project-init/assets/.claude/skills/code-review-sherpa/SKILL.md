---
name: code-review-sherpa
description: Review the diff of one milestone against the spec, the design and the project's review checklist, without changing a file. Reports each finding as a FINDING line with its severity, its location, the rule or code smell, and the simplest remedy. Use as the review session of a milestone, or when the user asks for a review of a change, a branch or a diff. Do not use to repair a finding, to write code, or to change a test.
---

# Code Review Sherpa

Review one change. The spec and the design say what the code must do. The checklist says how the
code must read. Report the findings only: another session repairs them.

## Read

- `CLAUDE.md`, the rules files for code, and the Rules of `docs/workflow.md`.
- The diff. The caller names it. Without a name, it is the diff of the milestone branch against
  the base branch: `git diff <base branch>...HEAD`. Read each changed file in full, not only the
  changed lines.
- The requirements, the acceptance examples and the design sections that the change implements.
  The test names carry the requirement IDs. Read the interfaces, the decisions and the table
  "Module boundaries" of `docs/design.md`.
- [The review checklist](references/checklist.md).

## Review

1. If this Claude Code has the built-in `/code-review`, run it first on the same diff. It looks
   for correctness bugs. Put its findings in your list. If it is not available, write
   `BUILT-IN REVIEW: not available` and continue.
2. Go through the checklist, one part at a time.
3. Try to refute each finding before you keep it. Read the code around it. Look for the test that
   covers it. Read the design decision that explains it. Keep a finding only when you are sure:
   you can name the line, the rule, and what goes wrong for a reader or a user.
4. Drop a matter of taste. Drop what a tool already checks: ruff, mypy, ESLint and
   `scripts/check.py` pass on every commit.
5. Give each finding a severity:
   - `high`: wrong behavior, a broken requirement, a broken design decision or module boundary.
   - `medium`: a smell of the checklist, or code that a reader will misunderstand.
   - `low`: a small loss of readability.
6. Give each finding the simplest remedy that removes its cause. A remedy does not change behavior
   that the spec states. It does not change a test. It does not add a design pattern.

## Do not

- Do not change, create or delete a file, and do not commit.
- Do not report code outside the diff, unless the diff breaks it.
- Do not propose a new feature or a new requirement.
- Do not report a smell that the checklist does not list.

## Report

Write one line for each finding, the most severe first:

`FINDING: <high|medium|low> | <file>:<line> | <rule or smell> | <remedy>`

When there is no finding, write `NO FINDINGS`. Then write one line that says how many findings you
dropped because you were not sure.
