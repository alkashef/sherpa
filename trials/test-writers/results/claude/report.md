I wrote 12 tests for M1 (9 unit, 3 e2e). They all fail now because `src/slug.py` and `main.py` don't exist yet, not because of a bug in the tests. There were no older tests to re-run. Ruff check and format pass on `tests/`.

**Files changed:** `tests/unit/test_slug.py`, `tests/e2e/test_cli.py`.

**Unit tests** (`tests/unit/test_slug.py`): the whole file fails to load with `ModuleNotFoundError: No module named 'src'`. This stops the full run before the e2e tests, so I ran `tests/e2e` on its own.

| Test | Checks | Fails now |
| --- | --- | --- |
| `test_slug_001_slug_holds_only_safe_characters` | SLUG-001 | No module `src` |
| `test_slug_001_ex_001_hello_world` | SLUG-001, SLUG-003, EX-001 | No module `src` |
| `test_slug_002_ex_002_accents_become_plain_letters` | SLUG-002, EX-002 | No module `src` |
| `test_slug_002_ex_009_kelvin_sign_becomes_k` | SLUG-002, EX-009 | No module `src` |
| `test_slug_002_ex_010_letters_without_ascii_form_are_dropped` | SLUG-002, EX-010 | No module `src` |
| `test_slug_003_ex_003_runs_of_symbols_become_one_hyphen` | SLUG-003, EX-003 | No module `src` |
| `test_slug_004_ex_004_cut_keeps_whole_words` | SLUG-004, EX-004 | No module `src` |
| `test_slug_004_ex_005_long_first_word_is_cut` | SLUG-004, EX-005 | No module `src` |
| `test_slug_006_empty_slug_raises_value_error` | SLUG-006 | No module `src` |

**E2E tests** (`tests/e2e/test_cli.py`): each fails because `main.py` can't be opened (Errno 2), so stdout, stderr and the exit code are wrong.

| Test | Checks |
| --- | --- |
| `test_slug_005_ex_006_prints_slug_and_exits_0` | SLUG-005, EX-006 |
| `test_slug_006_ex_007_title_without_letters_exits_2` | SLUG-006, EX-007 |
| `test_slug_007_ex_008_max_out_of_range_exits_2` | SLUG-007, EX-008 |

**Tests run:** 0 passed out of 12. The 9 unit tests error on import; the 3 e2e tests fail.

**Refs without a test:** none. DEC-001, DEC-002 and DEC-003 are design decisions, not requirements; the tests above cover how they behave.

**Live tests:** none.

**Assumptions and open questions:** the default `--max` of 60 (SLUG-005) has no test of its own because no example covers it.

DECISION: The e2e test file is named `tests/e2e/test_cli.py`, and the tests run `main.py` with the project root as the working folder | design §4 says to run from the project root, and the e2e file name is free | none
DECISION: `test_slug_006_empty_slug_raises_value_error` requires the exact message `the title has no letters or digits` | this is the message design §4 gives | none
DECISION: The test for EX-006 does not check standard error | SLUG-005 and EX-006 name only standard output and the exit code | none
DECISION: Each e2e subprocess has a 60-second timeout | so a hung program fails the test instead of stalling the run | none
DECISION: The Kelvin sign is written as `"\N{KELVIN SIGN}"` | ruff RUF001 rejects the literal character | none

**TLDR: All 12 M1 tests are written and fail only because `src/` and `main.py` don't exist yet; no requirement is left without a test, nothing is blocked, and I changed nothing outside `tests/`.**
