# Plan — ledger

Only unfinished milestones. Delete a milestone's row and block in the commit that finishes it; git
history is the record. Template: `docs/workflow.md`.

**Next milestone number: M2**

## Milestones at a glance

| Milestone | Description | Model | Effort | Human test | Status |
| --- | --- | --- | --- | --- | --- |
| **M1** Ledger tool | Adds, totals and lists expenses in one data file | sonnet | medium | no | open |

## Milestones

### M1 — Ledger tool

- **Refs:** LEDG-001, LEDG-002, LEDG-003, LEDG-004, LEDG-005, LEDG-006, LEDG-007, DEC-001, DEC-002, DEC-003.
- **Owner:** `src/money.py`, `src/store.py`, `src/cli.py`, `main.py`.
- **Tests first:**
  - unit: `test_ledg_002_ex_002_three_decimals_are_refused`, `test_ledg_002_ex_003_zero_is_refused`,
    `test_ledg_002_ex_004_upper_limit`, `test_ledg_006_missing_file_is_an_empty_ledger`,
    `test_ledg_007_invalid_file_raises_value_error`.
  - e2e: `test_ledg_001_ex_001_add_prints_the_id_and_stores_the_entry`,
    `test_ledg_001_ex_004_largest_amount_is_stored`, `test_ledg_003_ex_005_uppercase_category_is_refused`,
    `test_ledg_004_ex_006_total_and_total_of_a_category`, `test_ledg_004_ex_007_empty_total`,
    `test_ledg_005_ex_008_list_in_order_of_entry`, `test_ledg_006_ex_009_add_makes_the_folder`,
    `test_ledg_007_ex_010_invalid_data_file_exits_3`, `test_ledg_002_ex_002_cli_refuses_three_decimals`.
- **Build:** `src/money.py`, `src/store.py`, `src/cli.py` and `main.py`.
- **Gate:** `python scripts/check.py` passes, and `python scripts/spec_coverage.py M1` shows every
  requirement and example of the Refs as tested.
