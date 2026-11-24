---
name: write-plan
description: Turn an approved spec and design into the milestone plan in docs/plan.md. A table at the top shows each milestone with its model, effort and status; a block per milestone gives its tests and how to build it. Use after the design is approved, to add milestones when the spec or design changes, or to plan a fix of behavior the spec already states (a fix is one milestone). Do not use for requirements, architecture, or coding.
---

# Write Plan

Turn the approved spec and design into milestones that are built one at a time, in order. Write the
plan only. Do not write code, install dependencies, or start a milestone.

## Establish the baseline

- Read project instructions, `docs/workflow.md`, `docs/spec.md`, `docs/design.md`, and the current
  `docs/plan.md`. Read existing code, manifests, and tests when they exist.
- `docs/workflow.md` owns the row template, the block template, and the allowed model, effort, and
  status values. Follow it. Do not copy it into the plan.
- Check that the spec and the design are approved. If the spec says `Status: Draft`, or the design
  has a `Proposed` decision or an open design question, stop. Name the missing step: `/write-spec`
  or `/write-design`.
- Read [the milestone guide](references/milestone-guide.md) before cutting milestones.
- Number new milestones from the counter at the top of `plan.md`. Never renumber or reuse a number.
- Never plan from `docs/unapproved-ideas.md`: an idea there is not a requirement. The one
  exception is a fix of behavior the spec already states, when the user asks for it; then delete
  its line there in the same change.

## Cut the milestones

1. List the requirements in `spec.md` and the decisions in `design.md` that the plan must deliver.
2. Cut thin slices. Each milestone delivers behavior that tests can prove, and fits one unattended
   session. Order them by dependency: foundations first. The runner works without a person, so a
   milestone's Gate must be one a session can meet alone: offline, with real local parts and with
   fakes for the external services, with no user data and no human step. What only a person can
   judge is a human test (see 5). What needs a live service is a live check (see 6).
3. Check coverage. Every requirement ID belongs to at least one milestone. List any that does not,
   and say why. Run `python scripts/spec_coverage.py`: it lists each requirement ID as tested,
   manual, planned or missing.
4. Write one block per milestone, in the workflow's template:
   - **Refs:** the requirement IDs (`AREA-NNN`, `NFR-NNN`) and the `DEC-NNN` it implements.
   - **Owner:** the module or file that owns the change.
   - **Tests first:** at least one test name per requirement ID, and one per acceptance example
     that cites it. A name carries its requirement ID, and the example ID when the test comes from
     an example (`test_pay_001_ex_003_refund_over_limit`). Group the names by the level the design
     gives the requirement: `unit:`, `e2e:`, `ui:`, `live:`. A separate test session writes them
     with `/write-tests` from the spec's requirements and examples and the design, without the
     code, so each name must say which case and which result it checks. Write
     `Manual: <requirement ID>` only for what only a person can judge. Then the milestone has a
     human test (see 5).
   - **Build:** the smallest change that passes the tests, in terms the design already fixed.
   - **Gate:** what must be true before the commit, by checks a session can run alone.
   - **Human test:** only for a milestone whose row says `yes` (see 5).
5. Keep the human tests few. A milestone gets a human test only when it completes a user scenario
   that no tool can prove: a person's judgement. Where a tool can prove the result, plan a test
   (a `ui` test with Playwright for what the page shows). Put the human test at the milestone
   that completes the scenario, and join the judgements of one scenario in one entry. Set the
   column Human test of its row to `yes`, and write in its **Human test** entry what the user
   tests, step by step, and the result to expect. The runner stops after that milestone and waits
   for the user's answer. Every other row says `no`.
6. A test that only a live external service can prove has the level `live` and is in
   `tests/live/`. No milestone runs it. List each one under a heading "## Live checks", after the
   last milestone block (template in `docs/workflow.md`). Leave the entries **Approval** and
   **Budget ceiling** for the user: the live checks run only after the user fills them. The
   ceiling is an amount and a currency, such as `5 USD`.
7. Do not add a requirement or a dependency that the spec and design do not have. If the plan needs
   one, stop and propose the spec or design change for approval. For a decision the design leaves
   open, the milestone's session decides and records it (`docs/workflow.md`, Rules): do not turn it
   into a question.
8. List the dependencies each milestone first imports. Check that a `Decided` decision in
   `design.md` names each. Tell the user to approve and install every one before the run: an
   unattended session cannot install a dependency (`.claude/settings.json` asks first), and one
   that no `Decided` decision names stops the milestone.

## Choose the model and effort

Propose a model and an effort for each milestone, using the guide. The user may change any of them.
Use the aliases `haiku`, `sonnet`, and `opus` by default. Each alias means the latest model of that
family at the time of the run. Use a full model ID, for example `claude-sonnet-5-5`, only when the
user asks to pin a version.

## Show the table, then write the file

1. Show the milestones table in chat first: milestone, description, model, effort, human test,
   status. Say how many milestones stop for a human test. Add a line for each uncovered
   requirement. Ask for the user's approval or changes.
2. After approval, write the rows under "Milestones at a glance" and the blocks under "Milestones".
   Set every Status to `open`. Advance the counter at the top.
3. Keep the table at the top of the file, directly under the counter, so the user sees every
   milestone and its status at a glance. The milestone runner reads this table: keep its columns and
   heading exactly.

## Update an existing plan

- A fix, however small, is a milestone (`docs/workflow.md`, Rules). Refs: the requirement ID whose
  behavior is broken, and the `DEC-NNN` it breaks, if any. Tests first: a test, named after that
  ID, that fails while the fault is there. Use the smallest model and effort that fit.
- Add new milestones after the last one. Do not renumber.
- Do not edit a milestone whose Status is `blocked` or `approved`, or any **Blocked** or **Approval**
  entry. If the change affects one, tell the user.
- For an `open` milestone that the new spec or design changes, show the proposed edit before making
  it.
- A finished milestone is not in the plan: its row and block are deleted in its commit.

## Finish

Check that every row has a block, every block has a row, every number is unique, and every ID in
Refs exists in the spec or the design. Run `python scripts/spec_coverage.py --consistency` and
correct what it lists. A decision in Refs that is still `Proposed` is not yours to correct: never
change a Status. Tell the user to confirm it with `/write-design`. Report the milestones and any requirement left uncovered.
Tell the user the next step: run `python scripts/milestones-runner.py`, or run `/sherpa` to work the
first milestone in chat. Stop there.
