### Test Report (M1 — Slug tool)

- [test_slug.py](tests/unit/test_slug.py)::`test_slug_001_slug_holds_only_safe_characters` | SLUG-001 | none | Collection error: `ModuleNotFoundError: No module named 'src'`
- [test_slug.py](tests/unit/test_slug.py)::`test_slug_001_ex_001_hello_world` | SLUG-001, SLUG-003 | EX-001 | Collection error: `ModuleNotFoundError: No module named 'src'`
- [test_slug.py](tests/unit/test_slug.py)::`test_slug_002_ex_002_accents_become_plain_letters` | SLUG-002 | EX-002 | Collection error: `ModuleNotFoundError: No module named 'src'`
- [test_slug.py](tests/unit/test_slug.py)::`test_slug_002_ex_009_kelvin_sign_becomes_k` | SLUG-002 | EX-009 | Collection error: `ModuleNotFoundError: No module named 'src'`
- [test_slug.py](tests/unit/test_slug.py)::`test_slug_002_ex_010_letters_without_ascii_form_are_dropped` | SLUG-002 | EX-010 | Collection error: `ModuleNotFoundError: No module named 'src'`
- [test_slug.py](tests/unit/test_slug.py)::`test_slug_003_ex_003_runs_of_symbols_become_one_hyphen` | SLUG-003 | EX-003 | Collection error: `ModuleNotFoundError: No module named 'src'`
- [test_slug.py](tests/unit/test_slug.py)::`test_slug_003_underscores_become_single_hyphen` | SLUG-003 | none | Collection error: `ModuleNotFoundError: No module named 'src'`
- [test_slug.py](tests/unit/test_slug.py)::`test_slug_004_ex_004_cut_keeps_whole_words` | SLUG-004 | EX-004 | Collection error: `ModuleNotFoundError: No module named 'src'`
- [test_slug.py](tests/unit/test_slug.py)::`test_slug_004_ex_005_long_first_word_is_cut` | SLUG-004 | EX-005 | Collection error: `ModuleNotFoundError: No module named 'src'`
- [test_slug.py](tests/unit/test_slug.py)::`test_slug_004_cut_drops_partial_word` | SLUG-004 | none | Collection error: `ModuleNotFoundError: No module named 'src'`
- [test_slug.py](tests/unit/test_slug.py)::`test_slug_004_slug_at_exact_max_length_is_kept` | SLUG-004 | none | Collection error: `ModuleNotFoundError: No module named 'src'`
- [test_slug.py](tests/unit/test_slug.py)::`test_slug_004_default_max_length_is_60` | SLUG-004, SLUG-005 | none | Collection error: `ModuleNotFoundError: No module named 'src'`
- [test_slug.py](tests/unit/test_slug.py)::`test_slug_006_empty_slug_raises_value_error` | SLUG-006 | none | Collection error: `ModuleNotFoundError: No module named 'src'`
- [test_slug.py](tests/unit/test_slug.py)::`test_slug_006_non_ascii_only_title_raises_value_error` | SLUG-006, SLUG-002 | none | Collection error: `ModuleNotFoundError: No module named 'src'`
- [test_cli.py](tests/unit/test_cli.py)::`test_slug_005_cli_main_prints_slug_and_returns_0` | SLUG-005 | none | Collection error: `ModuleNotFoundError: No module named 'src'`
- [test_cli.py](tests/unit/test_cli.py)::`test_slug_005_cli_main_respects_max_option` | SLUG-005 | none | Collection error: `ModuleNotFoundError: No module named 'src'`
- [test_cli.py](tests/unit/test_cli.py)::`test_slug_005_cli_main_reads_sys_argv_when_argv_is_none` | SLUG-005 | none | Collection error: `ModuleNotFoundError: No module named 'src'`
- [test_cli.py](tests/unit/test_cli.py)::`test_slug_006_cli_main_empty_slug_returns_2` | SLUG-006 | none | Collection error: `ModuleNotFoundError: No module named 'src'`
- [test_cli.py](tests/unit/test_cli.py)::`test_slug_007_cli_main_max_zero_returns_2` | SLUG-007 | none | Collection error: `ModuleNotFoundError: No module named 'src'`
- [test_cli.py](tests/unit/test_cli.py)::`test_slug_007_cli_main_max_above_200_returns_2` | SLUG-007 | none | Collection error: `ModuleNotFoundError: No module named 'src'`
- [test_cli.py](tests/unit/test_cli.py)::`test_slug_007_cli_main_max_non_integer_returns_2` | SLUG-007 | none | Collection error: `ModuleNotFoundError: No module named 'src'`
- [test_main.py](tests/e2e/test_main.py)::`test_slug_005_ex_006_prints_slug_and_exits_0` | SLUG-005 | EX-006 | Fails: `main.py` missing (`[Errno 2] No such file or directory`, returncode 2 instead of 0)
- [test_main.py](tests/e2e/test_main.py)::`test_slug_005_max_option_limits_output_length` | SLUG-005, SLUG-004 | none | Fails: `main.py` missing (`[Errno 2] No such file or directory`, returncode 2 instead of 0)
- [test_main.py](tests/e2e/test_main.py)::`test_slug_006_ex_007_title_without_letters_exits_2` | SLUG-006 | EX-007 | Fails: `main.py` missing (stderr is Python's `can't open file ... main.py` instead of SLUG-006 error)
- [test_main.py](tests/e2e/test_main.py)::`test_slug_007_ex_008_max_out_of_range_exits_2` | SLUG-007 | EX-008 | Fails: `main.py` missing (stderr is Python's `can't open file ... main.py` instead of SLUG-007 error)
- [test_main.py](tests/e2e/test_main.py)::`test_slug_007_max_above_200_exits_2` | SLUG-007 | none | Fails: `main.py` missing (stderr is Python's `can't open file ... main.py` instead of SLUG-007 error)
- [test_main.py](tests/e2e/test_main.py)::`test_slug_007_max_negative_exits_2` | SLUG-007 | none | Fails: `main.py` missing (stderr is Python's `can't open file ... main.py` instead of SLUG-007 error)
- [test_main.py](tests/e2e/test_main.py)::`test_slug_007_max_non_integer_exits_2` | SLUG-007 | none | Fails: `main.py` missing (stderr is Python's `can't open file ... main.py` instead of SLUG-007 error)
- [test_main.py](tests/e2e/test_main.py)::`test_slug_007_max_boundary_1_is_accepted` | SLUG-007, SLUG-005 | none | Fails: `main.py` missing (`[Errno 2] No such file or directory`, returncode 2 instead of 0)
- [test_main.py](tests/e2e/test_main.py)::`test_slug_007_max_boundary_200_is_accepted` | SLUG-007, SLUG-005 | none | Fails: `main.py` missing (`[Errno 2] No such file or directory`, returncode 2 instead of 0)

Requirements in Refs without a test: none (all of SLUG-001 through SLUG-007 and EX-001 through EX-010 are tested).

Live tests written and not run: none.

- **Files changed:** [tests/unit/test_slug.py](tests/unit/test_slug.py), [tests/unit/test_cli.py](tests/unit/test_cli.py), [tests/e2e/test_main.py](tests/e2e/test_main.py).
- **Tests added or updated:** 14 unit tests in `tests/unit/test_slug.py`, 7 unit tests in `tests/unit/test_cli.py`, 9 e2e tests in `tests/e2e/test_main.py` (including all 12 names from `docs/plan.md`).
- **Tests run:** 0 passed out of 30 (`python -m pytest` hit 2 collection errors for missing `src`; `python -m pytest tests/e2e/test_main.py` ran 9 e2e tests, all 9 failed due to missing `main.py`). `ruff check` and `ruff format --check` passed on `tests/`.
- **Assumptions and open questions:** none.
- DECISION: Added `tests/unit/test_cli.py` calling `src.cli.main(argv)` directly in addition to subprocess e2e tests | `docs/design.md` Section 4 specifies `src.cli.main` as a testable interface, `CLAUDE.md` specifies one unit test file per source module, and in-process tests are needed so `pytest --cov=src --cov-branch --cov-fail-under=80` measures coverage on `src/cli.py` | none
- DECISION: Named the e2e test module `tests/e2e/test_main.py` | Matches the `main.py` entry point under test and avoids a pytest import basename collision with `tests/unit/test_cli.py` when `tests/` subpackages lack `__init__.py` | none
- **TLDR: Added 30 ruff-clean unit and e2e tests covering SLUG-001..SLUG-007 and EX-001..EX-010 for M1; all fail solely because `src/` and `main.py` are not yet implemented.**

