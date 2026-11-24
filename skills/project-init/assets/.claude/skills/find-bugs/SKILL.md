---
name: find-bugs
description: Look for bugs before a release, without changing the code or a test. Compares the code changed since the last release tag with docs/spec.md and docs/design.md, with most attention on the lines that no test runs, and reads the dependency audit and the surviving mutants of a mutation run. Writes each bug as a fix milestone in docs/plan.md by the rules of /write-plan, for the user to approve. Use when the user asks to find bugs, to check the code before a release, or to look for faults. Do not use to repair a bug, to write code, or to change a test.
---

# Find Bugs

Find the faults of the code against the spec and the design, before a release. Change no code and
no test. Each bug becomes a fix milestone, and the runner builds it: its test session writes the
test first. The test of a fault of the code fails until the build repairs it, so if it passes at
once, the fault was a false alarm. The test of a gap in the tests (a surviving mutant) passes at
once, because the code is right, and it kills the mutant.

## 1. Set the scope

- Find the last release tag: `git describe --tags --abbrev=0 --match "v*"`.
- The scope is the code changed since that tag: `git diff --name-only <tag>..HEAD -- src main.py`.
  Before the first release, the scope is all of `src/` and `main.py`.
- Tell the user the scope in one line before you start.

## 2. Run the tools first

1. **The lines that no test runs.** Run
   `python -m pytest -q --cov=src --cov-branch --cov-report=term-missing`. Keep the missing lines
   of the files in scope.
2. **The dependency audit.** Run `pip-audit -r requirements.txt` for Python and
   `npm audit --omit=dev` for JavaScript. If a tool is not installed, say so in the report. Do not
   install it without the user's approval.
3. **The surviving mutants.** When the user ran the workflow "Mutation tests" of GitHub Actions
   (`.github/workflows/mutation.yml`) and gives you its artifact, read the list of surviving
   mutants. A surviving mutant in the scope is a change of the code that no test notices.

## 3. Compare the code with the spec and the design

- Read the requirements of `docs/spec.md` and the decisions and interfaces of `docs/design.md`
  that the files in scope implement. Their docstrings cite the IDs.
- Read the code in scope. Give the most attention to the lines that no test runs and to the code
  of the surviving mutants.
- Report only a fault that you are sure of: a behavior that a requirement or a decision states
  and the code does not do. Write one line for each:
  `BUG: <requirement ID> | <file>:<line> | <what is wrong> | <the test that shows it>`.
- A surviving mutant whose code a requirement covers is a gap in the tests: a `BUG:` line whose
  test kills the mutant.
- A known vulnerability of a dependency, or a fault that no requirement covers, is not a bug of
  the spec. Ask the user one question about it: must the spec change (`/write-spec`)? Do not plan
  it.

## 4. Turn each bug into a fix milestone

- For each `BUG:` line, add one fix milestone to `docs/plan.md`, by the rules of `/write-plan`: a
  row in the table "Milestones at a glance" and a block. Its **Refs** hold the requirement ID, and
  its **Tests first** hold the test of the `BUG:` line: it fails while a fault of the code is
  there, and for a gap in the tests it passes at once and kills the mutant.
- Show the table first. The user approves the rows. Commit nothing.

## 5. Finish

Report, one line each: the scope, the coverage of the files in scope, the result of each tool,
each `BUG:` line with its milestone, and each question about the spec. Then tell the user the next
step in one line: "Next: approve the rows, commit the plan, then run
`python scripts/milestones-runner.py`."
