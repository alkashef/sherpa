# Trial of three test writers

The trial of November 21, 2026. Three AIs wrote the tests of one milestone from the same spec and
the same design, in a folder without the code. One script scored their tests. The work that
follows from it is in `docs/unapproved-ideas.md`, Part 1: USER-17 (with the rule of the second
trial), RUN-06 and RUN-07. This folder is not part of the skill, and the test suite does not
collect it.

## Contents

| Path | What |
| --- | --- |
| `project/docs/` | The spec, design and plan of the trial project: a slug tool with 7 requirements, 10 acceptance examples and one milestone |
| `prompts/agents.txt` | The prompt for Codex and Antigravity |
| `prompts/claude.txt` | The prompt for Claude |
| `records/AGENTS.md` | What Codex and Antigravity read: the `CLAUDE.md`, the Python rules and `/write-tests` of the trial project, under a short head |
| `reference/` | A correct implementation. The tests must pass on it |
| `evaluate.py` | The scoring script: ruff, mypy, `spec_coverage.py M1`, the failure before the code, the run on correct code, and 17 seeded bugs |
| `results/<writer>/` | The tests and the final report of each writer |

## Results

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

## Commands

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

## Run it again

1. Build the project, then copy the docs into it:
   `python skills/project-init/scripts/build_instance.py <work>/slugger --with python cli --name slugger`,
   then copy `project/docs/*.md` to `<work>/slugger/docs/`.
2. Copy `reference/` to `<work>/reference/`.
3. For each writer, make `<work>/tf-<writer>/` with the docs, the configs, an empty `tests/` and
   the instruction files of that writer, and run its command there. After the build of USER-17,
   the runner makes this folder.
4. Score each writer with the environment of the project: `python evaluate.py <work> tf-<writer>`.
