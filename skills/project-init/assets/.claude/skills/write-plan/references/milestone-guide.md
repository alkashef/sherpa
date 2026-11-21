# Milestone guide

## Size

A milestone is one unit of delivered behavior. Test it with these questions:

- Can one session finish it, including its tests, in one commit?
- Does it have at least one test that fails before the change and passes after? A `Manual:`
  entry stands in only for what only a person can judge (see Human test).
- Can the user say what is different when it is done?

If any answer is no, split the milestone or merge it with a neighbor.
Do not make a milestone for "set up" work that no test can show. Put setup in the first milestone
that needs it.

## Order

1. A milestone comes after everything it needs.
2. Put the riskiest unknown early, so a problem is found while the plan is cheap to change.
3. Prefer a thin end-to-end slice first. Then widen it.
4. Keep a milestone that changes a shared interface separate from the milestones that use it.

## Coverage

Make a list of requirement IDs with the milestone that owns each. A non-functional requirement
(`NFR-NNN`) belongs to the milestone where its test first can run, or to its own milestone when it
needs separate work. A requirement with status Withdrawn needs no milestone.
What only a person can judge is not a milestone: it is the human test of the milestone that
completes the scenario (see Human test). Put the requirements of one acceptance example in one
milestone, so that the example's test can pass there.

## Model and effort

| Work | Model | Effort |
| --- | --- | --- |
| Mechanical or repetitive: rename, move, copy a pattern, fill a table | `haiku` | `low` |
| Ordinary feature that follows a clear design | `sonnet` | `medium` |
| Feature with several rules, exceptions, or integration points | `sonnet` | `high` |
| Hard to reverse, security-relevant, concurrency, data migration, or a new shared structure | `opus` | `high` |
| Unclear design edge, or work where a mistake costs a lot | `opus` | `xhigh` or `max` |

Start from `sonnet` with `medium`. Move up only for a reason you can state in one line. Allowed
values are in `docs/workflow.md`.

An alias (`sonnet`) follows the newest model of its family, so the same plan can run on a newer
model next month. A full model ID (`claude-sonnet-5-5`) stays on that version. Use an ID when a run
must be repeatable.

## Tests first

- At least one test name per requirement ID, and one per acceptance example that cites it. The
  name shows the requirement ID, and the example ID when the test comes from an example
  (`test_pay_001_ex_003_refund_over_limit`). Group the names by the level the design gives each
  requirement: `unit:`, `e2e:`, `ui:`, `live:`.
- Name the tests of the most likely cases first, then the tests of the edge cases.
- A separate session writes the tests from the spec and the design, without the code
  (`/write-tests`). So each name says which case and which result it checks.
- Write `Manual: <requirement ID>` only for what only a person can judge. A test that needs a live
  external service is a `live:` test in `tests/live/`, and no milestone runs it.
- A test checks behavior the spec states. It does not check how the code is built.
- Name the boundary and failure cases the spec lists. Do not invent new ones.

## Build

- Describe the smallest change that passes the tests.
- Name the files or modules the design assigns. Do not specify private functions.
- Leave out anything the design does not decide. The milestone's session decides it, records it
  as a `Proposed` decision, and reports it (`docs/workflow.md`, Rules).

## Gate

The runner starts a milestone in a session with nobody to answer. A Gate is met by what the
session can run itself: the tests and checks of `CLAUDE.md`, with real local parts, with fakes
for the external services, and with invented data. These are not a Gate: a call to a live
external service (an LLM, a paid API), a read of the user's real data, a person's review, or a
download from the network. A person's review is the human test of the milestone. A call to a
live service is a live check: list it under "## Live checks" at the end of the plan. The heading
is level 2, so the runner's reading of the milestone blocks is not affected.

## Human test

The runner stops after a milestone that has a human test, prints the entry, and waits for the
user. So each human test costs the user's time and stops the run. Keep them few:

- Give a milestone a human test only when it completes a user scenario that no tool can prove.
- Where a tool can prove the result, plan a test. A `ui` test with Playwright proves what the
  page shows.
- Put the human test at the milestone that completes the scenario, not at each step of it.
- Join the judgements of one scenario in one entry.
- Write the entry for a person who did not read the plan: what to start, what to do step by
  step, and the result to expect.

## Example of one row and block

```markdown
| **M3** Record a payment | A clerk records a payment and the balance falls | sonnet | medium | no | open |

### M3 — Record a payment

- **Refs:** PAY-001, PAY-002, DEC-004.
- **Owner:** `src/payments/record.py`.
- **Tests first:** unit: `test_pay_001_ex_001_balance_falls_by_payment`,
  `test_pay_001_ex_002_payment_of_full_balance`, `test_pay_002_ex_003_overpayment_rejected`.
- **Build:** add `record_payment` to the payments module; reject an amount above the balance.
- **Gate:** the tests and the checks in `CLAUDE.md` pass; the README lists the new command.
```
