---
name: write-tests
description: Write the failing tests of one milestone in docs/plan.md from the spec's requirements and acceptance examples and the design's interfaces, before the code exists and without reading it. Use as the first session of a milestone, or when the user asks to write the tests for a milestone. Do not use to write or fix application code, or to make a failing test pass.
---

# Write Tests

Write the tests that prove one milestone, from what the app must do, not from how it is built.
Another session builds the code afterwards and may not change these tests. Write tests only.

## Read only what the tests come from

- Read `CLAUDE.md`, the rules files for tests, `docs/workflow.md`, and the milestone's block in
  `docs/plan.md`.
- Read the rows of `docs/spec.md` that the block cites in **Refs**, the scenarios they belong to,
  and the acceptance examples (`EX-NNN`) that cite them.
- Read in `docs/design.md`: the test design, the interfaces of the modules in **Owner** (entry
  points, request and response fields, stored records, public functions), the data model they use,
  and the decisions in **Refs**.
- Read the test harness that the design names: the shared fixtures, helpers and fakes under
  `tests/`. Read existing tests only to reuse their fixtures.
- Do not read the code in `src/`, also not through the shell. The tests must come from the spec and
  the design, so that they catch code that drifts from them. If a test needs an interface the
  design does not name, that is a gap in the design. Choose the most conservative name, use it, and
  report it as a `DECISION:` line (`docs/workflow.md`, Rules).

## Write the tests

1. Write one test for each name under **Tests first**, at the level the block gives it:
   - `unit:` in `tests/unit/`: a logic module, through its public functions.
   - `e2e:` in `tests/e2e/`: a user workflow, through the outermost non-browser entry point (HTTP
     API, CLI or service).
   - `ui:` in `tests/e2e/ui/`: the page, through Playwright, against a server that a fixture
     starts on 127.0.0.1.
   - `live:` in `tests/live/`: a live external service, with the test account that the design
     names. Write the test, but do not run it: no milestone session calls a live service. The
     test reads the budget ceiling from the environment variable `LIVE_BUDGET_CEILING` and stops
     before it passes it.

   A test uses the real local part that the design names (a database file in a temporary folder,
   a server that the test starts on 127.0.0.1). It uses a fake only for an external service.
2. Each test checks one behavior and asserts the result its requirement or example names: what the
   system answers, what is stored, or what the user sees. Do not assert private functions, log
   lines, or the order of calls.
3. Cover each acceptance example that cites the requirement: first the most likely cases, in
   full, then the edge cases (an unwanted-behavior requirement, `If ..., then ...`, is one). A
   test that comes from an example carries the example ID in its name
   (`test_pay_001_ex_003_refund_over_limit`). So the source of each expected result is on record.
   Take each expected result from the spec. Never work it out the way the code would.
   Then test the limits and the defaults that the requirements name:
   - For each limit (a length, a range, a count), test the limit and one value on each side.
   - For each default, test a call that leaves out the value.
   - For each invalid input, test one value of each kind (out of range, wrong type).
4. Use invented data. No test outside `tests/live/` calls a live external service (an LLM, a
   network API), and no test reads the user's data. A test keeps its files in a temporary folder. Fix the clock and any random value, so
   the test gives the same result on every run.
5. Do not change an existing test, unless its requirement changed in `spec.md`. Then name the test
   and the spec change in the report.

## Run them

1. Run the new tests, except those in `tests/live/`. Each must fail because the behavior is
   missing: a missing module named in
   **Owner**, a missing entry point, a wrong value. A syntax error, a broken fixture, or a wrong
   import path of the test itself is not a valid failure: fix the test until it fails for the
   right reason.
2. Run the whole suite. Every older test must still pass.

## Finish

Do not commit: the pre-commit hook refuses failing tests. Leave the files for the build session.
Report, one line each: the test, the requirement ID and the example ID it checks, and how it fails
now. Then each requirement ID in **Refs** without a test, and why (`Manual: <requirement ID>`).
Then each `live:` test that you wrote and did not run. Then the `DECISION:` lines.
