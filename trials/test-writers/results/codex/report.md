**Files changed:** [tests/unit/test_slug.py](./tests/unit/test_slug.py) and [tests/e2e/test_cli.py](./tests/e2e/test_cli.py).  
**Tests run:** 0 passed out of 20 in both the targeted run and the full suite. Ruff lint and format checks passed.  
**Assumptions and open questions:** None. Pytest warned that `asyncio_mode` is unknown. All 20 cases collected and ran.

**Tests added:** All 12 tests named in M1, covering all seven requirements and ten acceptance examples.

| Test | Requirement | Example | Observed failure |
|---|---|---|---|
| `test_slug_001_slug_holds_only_safe_characters` | SLUG-001 | Requirement only | `ModuleNotFoundError: No module named 'src'` |
| `test_slug_001_ex_001_hello_world` | SLUG-001, SLUG-003 | EX-001 | Missing `src` |
| `test_slug_002_ex_002_accents_become_plain_letters` | SLUG-002 | EX-002 | Missing `src` in both cases |
| `test_slug_002_ex_009_kelvin_sign_becomes_k` | SLUG-002 | EX-009 | Missing `src` |
| `test_slug_002_ex_010_letters_without_ascii_form_are_dropped` | SLUG-002 | EX-010 | Missing `src` in both cases |
| `test_slug_003_ex_003_runs_of_symbols_become_one_hyphen` | SLUG-003 | EX-003 | Missing `src` |
| `test_slug_004_ex_004_cut_keeps_whole_words` | SLUG-004 | EX-004 | Missing `src` in both cases |
| `test_slug_004_ex_005_long_first_word_is_cut` | SLUG-004 | EX-005 | Missing `src` |
| `test_slug_006_empty_slug_raises_value_error` | SLUG-006 | Requirement only | Missing `src` |
| `test_slug_005_ex_006_prints_slug_and_exits_0` | SLUG-005 | EX-006 | Missing `main.py` caused exit 2 in all four cases |
| `test_slug_006_ex_007_title_without_letters_exits_2` | SLUG-006 | EX-007 | Stderr reported missing `main.py` |
| `test_slug_007_ex_008_max_out_of_range_exits_2` | SLUG-007 | EX-008 | Stderr reported missing `main.py` in all three cases |

DECISION: Import `src.slug` when each unit case runs | Allows pytest to collect and run every case before the module exists | none

DECISION: Parameterize the planned tests with Unicode and length boundary cases | Checks distinctions in the approved requirements that the examples alone do not exercise | none

**TLDR: M1 tests are ready for the build session. All 20 cases failed for the expected missing implementation.**