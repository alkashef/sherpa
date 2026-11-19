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
   - `unit:` in `tests/unit/`: a logic module, through its public functions, with fakes.
   - `e2e:` in `tests/e2e/`: a user workflow, through the outermost non-browser entry point (HTTP
     API, CLI or service), with fakes at the external boundaries.
   - `ui:` in `tests/e2e/ui/`: the page, through the headless-browser tool that the design names,
     against a server that a fixture starts on 127.0.0.1 with the same fakes.
2. Each test checks one behavior and asserts the result its requirement or example names: what the
   system answers, what is stored, or what the user sees. Do not assert private functions, log
   lines, or the order of calls.
3. Cover the success case of the requirement, and the failure or boundary case when the spec states
   one (an unwanted-behavior requirement, `If ..., then ...`, is one).
4. Use invented data. No test calls a live external service (an LLM, a network API) or reads the
   user's data. A test keeps its files in a temporary folder. Fix the clock and any random value, so
   the test gives the same result on every run.
5. Do not change an existing test, unless its requirement changed in `spec.md`. Then name the test
   and the spec change in the report.

## Run them

1. Run the new tests. Each must fail because the behavior is missing: a missing module named in
   **Owner**, a missing entry point, a wrong value. A syntax error, a broken fixture, or a wrong
   import path of the test itself is not a valid failure: fix the test until it fails for the
   right reason.
2. Run the whole suite. Every older test must still pass.

## Finish

Do not commit: the pre-commit hook refuses failing tests. Leave the files for the build session.
Report, one line each: the test, the requirement ID it checks, and how it fails now. Then each
requirement ID in **Refs** without a test, and why (`Manual: <requirement ID>`). Then the
`DECISION:` lines.
