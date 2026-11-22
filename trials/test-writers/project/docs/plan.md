# Plan — slugger

Only unfinished milestones. Delete a milestone's row and block in the commit that finishes it; git
history is the record. Template: `docs/workflow.md`.

**Next milestone number: M2**

## Milestones at a glance

| Milestone | Description | Model | Effort | Human test | Status |
| --- | --- | --- | --- | --- | --- |
| **M1** Slug tool | Turns a title into a slug from the command line | sonnet | medium | no | open |

## Milestones

### M1 — Slug tool

- **Refs:** SLUG-001, SLUG-002, SLUG-003, SLUG-004, SLUG-005, SLUG-006, SLUG-007, DEC-001, DEC-002, DEC-003.
- **Owner:** `src/slug.py`, `src/cli.py`, `main.py`.
- **Tests first:**
  - unit: `test_slug_001_slug_holds_only_safe_characters`, `test_slug_001_ex_001_hello_world`,
    `test_slug_002_ex_002_accents_become_plain_letters`, `test_slug_002_ex_009_kelvin_sign_becomes_k`,
    `test_slug_002_ex_010_letters_without_ascii_form_are_dropped`,
    `test_slug_003_ex_003_runs_of_symbols_become_one_hyphen`,
    `test_slug_004_ex_004_cut_keeps_whole_words`, `test_slug_004_ex_005_long_first_word_is_cut`,
    `test_slug_006_empty_slug_raises_value_error`.
  - e2e: `test_slug_005_ex_006_prints_slug_and_exits_0`, `test_slug_006_ex_007_title_without_letters_exits_2`,
    `test_slug_007_ex_008_max_out_of_range_exits_2`.
- **Build:** `src/slug.py` with `make_slug`, `src/cli.py` with `main`, and `main.py`.
- **Gate:** `python scripts/check.py` passes, and `python scripts/spec_coverage.py M1` shows every
  requirement and example of the Refs as tested.
