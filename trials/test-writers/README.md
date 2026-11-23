# Trials of the test writers

Two trials of the AIs that write the tests of a milestone from the spec and the design, in a folder
without the code. One script scores their tests. This folder is not part of the skill, and the
test suite does not collect it.

- **The first trial**, November 21, 2026: one run of each writer on the slug tool, with folders
  and commands made by hand. Its work is in `docs/unapproved-ideas.md`, Part 1: USER-17 (with the
  rule of the second trial), RUN-06 and RUN-07.
- **The second trial**, November 23, 2026: three runs of each writer on each of two projects,
  through the runner of a real sherpa project (`milestones-runner.py --tests-only M1`). Its rule
  decides the default writer.

## Contents

| Path | What |
| --- | --- |
| `kits/slug/` | The slug tool: a spec with 7 requirements and 10 acceptance examples, a design, a plan with one milestone, a correct implementation (`reference/`) and 17 seeded bugs (`mutants.json`) |
| `kits/ledger/` | A ledger of expenses that stores data in a JSON file: 7 requirements, 10 examples, a design with a data model, one milestone, a correct implementation and 18 seeded bugs |
| `evaluate.py` | The scoring script: the gates (ruff check and format, `spec_coverage.py M1`, a valid failure before the code, a pass on correct code, mypy with the code, 80% coverage, the spec and the plan unchanged) and the seeded bugs |
| `run_trial.py` | The second trial: builds a project for each run, runs the writer through the runner, scores the tests, and writes `results-2/summary.md` |
| `prompts/`, `records/` | The prompts and the `AGENTS.md` of the first trial |
| `results/<writer>/` | The tests and the final report of each writer in the first trial |
| `results-2/<kit>/<writer>/run<n>/` | The tests, the runner's output, the logs and the score of each run of the second trial |

## Results of the first trial

One run of each writer, effort `high`, on Windows 11.

| | Codex `gpt-6.2-astra` | Claude `claude-opus-5-5` | Antigravity `gemini-4-neon-high` |
| --- | --- | --- | --- |
| Time | 139 s | 76 s | 226 s |
| Tests (cases) | 12 (20) | 12 (12) | 30 (30) |
| Seeded bugs caught | 16 of 17 | 11 of 17 | 15 of 17 |
| Mypy, with the code present | 1 error | 12 errors | Passed |
| Coverage gate (80%), on correct code | 41%, fails | 41%, fails | 94%, passes |
| Ruff, IDs, right failure before the code, pass on correct code, docs not edited | Yes | Yes | Yes |

- Codex added limit cases inside the planned tests. It imported `src.slug` inside a helper, which
  causes its mypy error (`no-any-return`).
- Claude wrote only the 12 planned examples, and left out `-> None` on each test.
- Antigravity added 18 tests. Some of them call `src.cli.main` in the test process, so it alone
  passes the coverage gate. The gate does not count a test that runs `main.py` as a process
  (RUN-06). With `[run] patch = subprocess` in a `.coveragerc`, the tests of Claude reach 90%.
- The first try of Codex did nothing in 24 seconds and still exited with 0:
  `--ignore-user-config` dropped the `windows.sandbox` setting, and Codex refused each shell
  command.
- Claude ran with `--setting-sources project`. It warned that the folder is not trusted, so it
  ignored the allow list, and possibly the project hooks.
- One run of each writer is weak evidence. The second trial decides the default writer.

## Commands of the first trial

The versions: Codex CLI 0.171.0-alpha.13 (the copy in the VS Code extension), Claude Code
2.1.318, Antigravity CLI 1.4.7. Each command ran in the folder of its writer, with the folders of
the conda environment first on the PATH.

```bash
codex exec -m gpt-6.2-astra -c model_reasoning_effort=high -c 'windows.sandbox="unelevated"' \
  --sandbox workspace-write --skip-git-repo-check --ignore-user-config --ephemeral \
  -C <folder> --json -o <report file> - < prompts/agents.txt

claude -p --model claude-opus-5-5 --effort high --permission-mode bypassPermissions \
  --setting-sources project --no-session-persistence --output-format json "$(cat prompts/claude.txt)"

agy --model gemini-4-neon-high --dangerously-skip-permissions --output-format json \
  --print-timeout 20m -p "$(cat prompts/agents.txt)"
```

## Results of the second trial

November 23, 2026, on Windows 11. Each writer ran 3 times on each kit, at effort `high`: Claude
`claude-opus-5-5`, Codex `gpt-6.2-astra`, Antigravity `gemini-4-neon-high`. The runner made the
folder of each test session, ran the writer, copied `tests/` back, checked the tests and gave one
round of repair when they needed it. `results-2/summary.md` has each run.

| | Claude | Codex | Antigravity |
| --- | --- | --- | --- |
| All gates in all 6 runs | Yes | Yes | Yes |
| Seeded bugs caught, slug (each run, of 17) | 16, 17, 17 | 16, 17, 16 | 17, 17, 17 |
| Seeded bugs caught, ledger (each run, of 18) | 18, 18, 18 | 18, 18, 18 | 18, 18, 18 |
| Median of seeded bugs caught | 17.5 | 17.5 | 17.5 |
| Median time of a run | 217 s | 226 s | 512 s |
| Test functions, slug and ledger | 26 to 34, 45 to 48 | 16 to 17, 25 to 28 | 25 to 38, 31 to 35 |
| Rounds of repair | none | none | 3 (mypy, ledger) |

**By the rule of the second trial, Claude stays the default writer.** All three writers qualify,
the three medians tie at 17.5, and on a tie the faster writer wins: Claude, by 9 seconds. The
margin is small, so Codex is an equal choice; Antigravity is as good and about twice as slow.

- The three bugs that a writer missed were all defaults of the slug tool: the default maximum
  length of the function (Codex, two runs) and of the command line (Claude, one run).
- Antigravity got one round of repair in each ledger run: the runner's mypy check found 41 type
  errors in its tests, and the writer repaired them.
- The trial found two faults of sherpa before it could run: the folder of the test session shut
  out the Codex sandbox (`tempfile.mkdtemp` makes a folder that only its owner can open), and
  Codex blocked each milestone because pytest and Hypothesis are named in no design decision.
  Both are repaired, and the trial ran again from the start.
- The writers read the design of the ledger more strictly than its first correct implementation:
  a data file with an extra key, or an entry that breaks a limit of the data model, is not a
  valid ledger. The reference was corrected, and each run was scored again with it.

## Run it again

The second trial, from the root of sherpa, with Codex on the PATH (the copy in the VS Code
extension works) and one sign-in to each CLI:

```bash
python trials/test-writers/run_trial.py <work folder>
python trials/test-writers/run_trial.py <work folder> --rescore    # after a change of a kit
```

One run: build a project with `build_instance.py ... --name sherpa`, copy the docs of a kit into
it, commit, turn the hook on, run `python scripts/milestones-runner.py --tests-only M1
--test-writer <writer>`, then `python trials/test-writers/evaluate.py trials/test-writers/kits/<kit>
<project>`. `run_trial.py` does these steps.
