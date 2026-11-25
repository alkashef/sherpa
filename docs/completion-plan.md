# Plan to finish sherpa

This file is the plan from the state of sherpa today to its first release. The steps are in the
order of the work. Each step has a "Done when" test and a record line. When a step is done, mark
its box `[x]` and fill in its record, in the commit that finishes the step. The record names that
commit by its subject line, because a commit cannot hold its own hash. Do not delete a finished
step: this file is the record of the finish.

- Written: November 23, 2026, at commit `aa7331a` (337 tests pass, no open work in Part 1 of
  `docs/unapproved-ideas.md`).
- Approved by the user: November 23, 2026

Two rules apply to each step:

- A step marked **Needs approval** changes the workflow or adds something new. It starts only after
  the user approves it, as for Part 2 of `docs/unapproved-ideas.md`. A built workflow change also
  gets its row in the Built table of that file.
- A real run goes into the README, "Checked in real Claude Code sessions", as runs 1 to 4 did. Each
  fault of sherpa that a run finds goes to step C1.

## Definition of done

sherpa is finished when all five points are true:

1. No idea in Part 2 of `docs/unapproved-ideas.md` waits for a decision.
2. Each path of the workflow ran in a real Claude Code session at least one time, or the user
   accepted it as checked by the suite only (next section).
3. The last real run of each kind of project found no new fault of sherpa.
4. The suite passes on Windows, on a clean machine. Before November 24, 2026, this point also
   named Linux and macOS (scope limitation below).
5. The docs show the workflow as built, and the release of sherpa has a tag.

Out of scope, by earlier decisions: AI assistants other than Claude Code (`CLAUDE.md`, Approach);
an existing project as the start (rank 13); a third language before a project needs one (rank 19).

Scope limitation, decided by the user on November 24, 2026 (D1): sherpa supports Windows only.
The suite, the skill, the hooks and the runner are checked on Windows, and no check runs them on
Linux or macOS. One part runs on Linux all the same: the `check.yml` workflow of a new project
runs `check.py` on a clean Linux machine of GitHub (B4 checks it).

## Paths that no real session ran

Runs 1 to 4 and the two trials ran these paths in real sessions: the test folder, the test writers
(Claude, Codex, Antigravity), the review, the repairs, the test repairs, a block by the last review,
the approval, the merge, the human test, `/sherpa` and the dashboard. The paths below ran only in
the suite.

| Path | Why no real run | Step |
| --- | --- | --- |
| `/write-spec`, `/write-design` and `/write-plan` with a person who answers | Runs 1 to 4 started from written docs (a kit) | B3 |
| A build session that blocks with partial work | Ran in the fifth real run: B1 is done | B1 |
| A repair or rebuild session that reports `BLOCKED:` for a wrong test | Accepted as suite-only by the user on November 23, 2026 | B1 |
| The modules `javascript`, `html-css`, `ui-design` and `http-apis`, and `ui` tests in Playwright | Ran in the sixth real run: B2 is done | B2 |
| `build_instance.py --add` in a project that exists | Ran in the sixth real run (`--add http-apis`) | B2 |
| `check.yml` and `mutation.yml` on GitHub Actions | Ran in the GitHub run: B4 is done | B4 |
| `/find-bugs` and `release.py` | Ran in the GitHub run: B4 is done | B4 |
| The modules `data`, `llm`, `logging`, `long-running`, `validation`, `static-site`, `mcp` and `docker`, and `live_checks.py` with an approved budget | `llm`, `validation`, `logging` and `live_checks.py` ran in the eighth real run. The others were accepted as suite-only on November 24, 2026 | B5 |

## A. Decide and build the open ideas

Both ideas change the review or the runner, so they come first: the runs of part B then check the
final behavior.

- [x] **A1. RUN-10: the review rates a fault of a requirement too low.** Needs approval. The
  options are in `docs/unapproved-ideas.md`, Part 2, section E. Recommendation: option B.
  - Done when: the user decided. If built: the review skill (and the runner, for option A),
    `workflow.md`, `workflow.html` and the tests change in one commit, and the suite passes.
  - Estimate: 30 minutes for option B, 1 hour for option A.
  - Decided on: November 23, 2026 (option B). Built in commit: "The review rates wrong behavior
    against a requirement high, never low (RUN-10)". The review prompt of the runner says it too,
    because it also rates the findings of the built-in `/code-review`.
- [x] **A2. RUN-11: a start check refuses a milestone whose Refs name a `Proposed` decision.**
  Needs approval.
  - Done when: as for A1.
  - After A2, a `Proposed` decision no longer makes a build session block, so the kit of B1 needs
    another cause.
  - Estimate: 1 hour.
  - Decided on: November 23, 2026 (option A). Built in commit: "The runner refuses a milestone
    whose Refs name a Proposed decision (RUN-11)". The check is part of
    `spec_coverage.py --consistency`, which the runner runs at its start, so `/write-plan` and the
    dashboard also show the problem. Part 2 of `docs/unapproved-ideas.md` now has no open idea
    (definition of done, point 1).

## B. Run the paths in real sessions

Each run uses a project that the skill built and real `claude -p` sessions, with `sonnet` at
effort `medium` unless the step says otherwise.

- [x] **B1. Fifth real run: a build session that blocks (Python, `cli`).** The kit of the fourth
  run, with DEC-004 `Decided` (since A2, a `Proposed` decision stops the run at its start). M1
  runs alone. Then an older test goes onto the base branch: it passes after M1, but it expects
  `--subscribe` to be refused as an unknown option, which SLUG-008 makes wrong. The build session
  of M2 makes that test fail, and it may not change a test, so it must block. Method approved by
  the user on November 23, 2026.
  - Done when: a build session blocks, the runner commits `M<n>: partial work` and `M<n>: blocked`,
    after the approval a test session gets the decision, and the milestone goes on from that work
    and merges.
  - A repair or rebuild session that reports `BLOCKED:` (after the review): accepted as
    suite-only by the user on November 23, 2026. It uses the same block code as the build session.
  - Risk: the test session of M2 can see the wrong test and correct it itself. Then the run shows
    another path, and B1 stays open.
  - Estimate: 1 hour for the kit, 1 hour of runs.
  - Status: in progress since November 23, 2026. In M1 a build session blocked on its own,
    before the planted test: the test session wrote a wrong test (`--max 1` expects `hello`, but
    SLUG-004 cuts it to `h`). The runner kept `M1: partial work` and committed `M1: blocked`. The
    approval (Claude in the role of the user, as in runs 3 and 4) is committed. The run after
    the approval found a fault of sherpa (C1, RUN-12): no test session got the decision, so the
    build session stopped again. The user approved RUN-12 with option B, and it is built. With
    the repaired runner, a `retest` session got the decision and changed the test, the build
    session finished from the kept work, and M1 merged (211 s). So the done-when of B1 is met in
    M1. In M2 the planted older test worked: the test session left it, and the build session
    blocked with partial work (187 s). After the approval a `retest` session changed it, and the
    build went on. Then the last review blocked M2 for a fault of SLUG-009 (`medium`), and the
    run after that approval merged M2 (434 s). The project's checks pass. The run also found
    RUN-13 (C1).
  - Done on: November 23, 2026. README record in commit: "Record the fifth real run, and its new idea (RUN-13)"
- [x] **B2. Sixth real run: a web project (`python`, `javascript`, `html-css`, `ui-design`,
  `http-apis`).** A small app with a page, an API and a `ui` test in Playwright. The project starts
  without `http-apis`, and `build_instance.py --add http-apis` adds it before the milestone of
  the API.
  - Done when: each milestone merges, the sessions get the feedback of ESLint, Prettier,
    Stylelint and `tsc` through the edit hook, and the `ui` test passes in `check.py`.
  - Estimate: 2 hours for the kit, 2 to 3 hours of runs.
  - Status: in progress since November 23, 2026. The kit is a page that counts the words and
    characters of a note (M1: a server of the standard library and the page, with no API). M2
    adds an API that saves notes, after `build_instance.py --add http-apis`, and replaces the
    server with FastAPI. The skill built the project with its own conda environment, `notecount`.
    Its pip install failed on a slow network (no version of ruff found), and the skill reported it
    with the command to finish by hand, as its step 3 says. In the first run of M1, every check
    passed in the build session (pytest with the `ui` test in Playwright, `node --test`, tsc,
    Prettier, Stylelint) except ESLint, which allowed `console` only in `src/log.js`. The build
    session blocked with partial work (C1, repaired). The approval (Claude in the role of the
    user) made the same change by hand in the project, and M1 merged (318 s). Then the user's
    part added `http-apis` with `build_instance.py . --add http-apis`, and DEC-005 (FastAPI)
    replaced DEC-001. The last review blocked M2 two times for `medium` findings of a
    requirement, and after each approval the repairs did what the decision said. M2 merged
    (275 s), and the project's checks pass, with 10 `ui` tests.
  - Of the done-when: each milestone merged, and the `ui` tests pass in `check.py`. The edit hook
    sent ESLint errors back and Prettier rewrote files, but no CSS edit gave a Stylelint error.
    tsc runs in the full check, not in the edit hook, so that part of the done-when was wrong.
    The run found a fault (C1), so a later web run checks the repair. It also found RUN-14 and
    RUN-15 (Part 2). RUN-15, option A, approved on November 23, 2026, and built in commit
    "Unattended sessions load only the settings of the project (RUN-15)". RUN-14, option A,
    approved on the same day, and built in commit "ESLint requires the JSDoc and the module block of the rules (RUN-14)".
    RUN-16 (the MCP servers of the user's account, found while RUN-15 was checked), option A,
    approved on the same day, and built in commit "Unattended sessions load no MCP server of the user's account (RUN-16)".
  - Done on: November 23, 2026. README record in commit: "Record the sixth real run, and its new ideas (RUN-14, RUN-15)"
- [ ] **B3. A real interview, from an empty folder to merged milestones.** The user is the
  developer: the user answers `/write-spec`, `/write-design` and `/write-plan` in chat for a small
  tool of the user's choice, with no kit, and then the runner builds the plan. This is the only test
  of the objective "zero lines of code" from the first step.
  - Done when: the user approved the three docs, `spec_coverage.py --consistency` passes, and the
    runner merges each milestone. Each unclear question and each fault is recorded.
  - Estimate: 2 hours of the user's time, plus 1 hour of runs.
  - Status: started on November 24, 2026. The installed skill was a copy of November 19 (with
    `/sdd`, not `/sherpa`), so it was replaced with the current one first. The user runs the
    interview in a new VS Code window and notes each unclear question. The user allowed Claude to
    read the session transcripts of the B3 project folder, only to record the faults and the
    unclear questions.
  - Done on: ____ README record in commit: ____
- [x] **B4. A real GitHub run: the two workflows, `/find-bugs` and a release.** Needs approval:
  it creates a private repository on the user's GitHub account. Push the project of B1 or B3 to
  GitHub. Then see `check.yml` pass, start `mutation.yml` by hand, run `/find-bugs` with the
  surviving mutants, build its fix milestones, and cut a release with `release.py`.
  - Done when: `check.yml` passes on GitHub, `mutation.yml` keeps the surviving mutants,
    `/find-bugs` writes its `BUG:` lines (or reports none), and the tag and the row of
    `docs/releases.md` are on GitHub.
  - Estimate: 2 hours.
  - Status: started on November 24, 2026, with the user's approval, on the project of B5
    (`tagnote`): it is the newest project, and B3 is still with the user. The user chose the
    account `alkashef` for the private repository `alkashef/tagnote`. `check.yml` passed on a clean
    Linux machine, the first real run of `check.py` on Linux. `mutation.yml` passed with an empty
    list of mutants: a fault of sherpa (C1), repaired. With the repair, a run made 158 mutants in
    15 minutes, and 32 survived. `/find-bugs` wrote four `BUG:` lines (gaps in the tests), and
    their fix milestones M3 to M6 merged. A fix milestone of the user, M7, changed the prompt, and
    the live check still failed: the model `qwen2.5:1.5b-instruct` does not meet TAG-010, a fault
    of the project. `release.py M7` pushed the tag `v2026.11.25` and the row of
    `docs/releases.md` to GitHub. Each `check.yml` run passed.
  - Done on: November 25, 2026. README record in commit: "Record the GitHub run (B4), and correct /find-bugs about a test that passes"
- [x] **B5. The other modules: a real run, or accepted as suite-only.** Needs the user's decision
  for each module. Recommendation: one run with `llm`, `validation` and `logging`, and
  `live_checks.py` with a small approved budget, because a flow of data to a provider and a paid
  call carry the most risk. Accept the other modules as suite-only.
  - Done when: each row below has a run or a date of acceptance.
  - Estimate: 3 hours for the recommended run.
  - Status: the user asked on November 24, 2026 to start and finish B5. The eighth real run used
    `llm`, `validation` and `logging` in `tagnote`, a CLI that tags a note with the local model
    `qwen2.5:1.5b-instruct` (Ollama). Both milestones merged. The live check ran with an approval
    and a ceiling of 0 USD, written by Claude in the role of the user. The run found a fault of
    `live_checks.py` (repaired, C1), RUN-17 and RUN-18 (Part 2). The done-when is met, but the box
    stays open until the user decides RUN-17 and RUN-18: the user's definition of done allows no
    open issue. RUN-17 and RUN-18 are built (option A each), and each repair was checked in the
    project of the run with real sessions: the repaired `live_checks.py` with the real model, and
    a session that read only `src/model_client.py` and got the LLM rules.
  - A hosted provider was checked later, on November 25, 2026: the user gave an OpenAI key, and a
    live check with a real call passed (row 3 of `docs/status.md`).
  - Done on: November 24, 2026. README record in commit: "Record the eighth real run, and repair the entries of the live checks"

  | Module | Real run (README record) or accepted as suite-only on |
  | --- | --- |
  | `data` | Accepted as suite-only on November 24, 2026, by the recommendation, when the user asked to finish B5 |
  | `llm` | Eighth real run (README record in commit "Record the eighth real run, and repair the entries of the live checks"), with a local model. A hosted provider (OpenAI) ran on November 25, 2026, with the user's key (README record in commit "Record the run with a hosted model (row 3 of the status table)") |
  | `logging` | Eighth real run (README record in commit "Record the eighth real run, and repair the entries of the live checks") |
  | `long-running` | Accepted as suite-only on November 24, 2026, by the recommendation, when the user asked to finish B5 |
  | `validation` | Eighth real run (README record in commit "Record the eighth real run, and repair the entries of the live checks") |
  | `static-site` | Accepted as suite-only on November 24, 2026, by the recommendation, when the user asked to finish B5 |
  | `mcp` | Accepted as suite-only on November 24, 2026, by the recommendation, when the user asked to finish B5 |
  | `docker` | Accepted as suite-only on November 24, 2026, by the recommendation, when the user asked to finish B5 |
  | `live_checks.py` | Eighth real run (README record in commit "Record the eighth real run, and repair the entries of the live checks"). It found a fault (repaired) and RUN-17 |

## C. Repair what the runs find

- [x] **C1. Repair each fault of sherpa that part B finds.** One commit for each fault, with a
  test, as in runs 3 and 4. A repair that changes the workflow goes to Part 2 of
  `docs/unapproved-ideas.md` first. When a run found a fault, a later run of the same kind checks
  the repair. After two such runs of one kind, the user decides whether to run it again.
  - Done when: the last run of each kind found no new fault (definition of done, point 3).
  - Estimate: about 1 hour for each fault (runs 3 and 4 found four faults).
  - Status: the seventh real run, a second web run, ran on November 24, 2026, with the user's
    approval. The kit is a page that splits a bill (M1) and saves the splits through an API (M2).
    Both milestones merged. The ESLint repair of run 6, RUN-13, RUN-14, RUN-15 and RUN-16 held in
    real sessions. The run found one new fault (the comments about the coverage of a process,
    below), so the web kind has now had two runs after a fault: the user decides whether it runs
    again. README record in commit: "Record the seventh real run, and repair the coverage rule of a stopped process".
  - Decided by the user on November 24, 2026: no third web run. The repair of run 7 is checked by
    the suite (`test_code_that_only_a_stopped_process_runs_does_not_count`). If B3 builds a small
    web tool, it also checks that `/write-design` plans a test of the server code in the test
    process.
  - Decided by the user on November 24, 2026, option A: run 7 checks the repairs of run 5 for the
    Python CLI kind too. RUN-12 and RUN-13 are in the runner and the design rules, which are the
    same for each kind. In run 7, M1 blocked, and after the approval a `retest` session got the
    decision first. The repair session added DEC-008 as `Proposed` and changed no `Decided` row.
    Thus each fault of runs 1 to 7 is repaired, and a real run or, by the user's decision, the
    suite checks the repair. Point 3 holds by these two decisions, not by a run that found no
    fault.
  - A fault that B3, B4 or B5 finds opens this step again: add its row to the table, and set the
    box back to `[ ]` until its repair is checked.
  - Done on: November 24, 2026, for runs 1 to 7. Recorded in commit: "Close C1: run 7 checks the repairs of run 5"
  - Opened again on November 24, 2026 by the eighth real run (B5). Its fault is repaired, and
    RUN-17 and RUN-18 are built. Each repair was checked in the project of the run with real
    sessions, not in a later run of the same kind. The user decides whether that check is enough.
  - Decided by the user on November 24, 2026, option 1: the checks in real sessions in the
    project of the eighth run are enough, as for RUN-15 and RUN-16. No second run of the kind.
  - Done again on: November 24, 2026, for runs 1 to 8. Recorded in commit: "Close C1 again: the repairs of run 8 are checked in real sessions"
  - Opened by B4 on November 24, 2026, and closed again in the commit of the repair: a real run of
    the repaired `mutation.yml` on GitHub checked it. The correction of `/find-bugs` is checked by
    the run itself: the runner merged M3 to M6, whose tests passed at once.
  - Opened by RUN-19 on November 25, 2026 (found while the run with a hosted model was planned),
    and closed again in the commit of the repair: real sessions with the flags of the runner
    checked it.

  | Run | Fault | Commit |
  | --- | --- | --- |
  | 5 (B1) | After the approval of a wrong test that a build session found, no test session ran, and M1 could not go on. RUN-12, option B, approved on November 23, 2026 | "After the approval of a block by a session, a test session gets the decision first (RUN-12)" |
  | 5 (B1) | A repair session rewrote the `Decided` decision DEC-004 and kept it `Decided`. RUN-13, option A, approved on November 23, 2026 | "A session may not change a Decided decision of the design (RUN-13)" |
  | 6 (B2) | `eslint.config.js` let only `src/log.js` use `console` and only `src/api.js` call `fetch`. The design put the page in `src/web/`, and no session may edit the config, so the build session of M1 blocked | "ESLint allows log.js and api.js in any folder under src/" |
  | 7 (C1) | The comments of `.coveragerc` and `pytest.ini` said that the processes that a test starts count for the coverage floor. A server that a test stops writes no data, so the build session of M1 blocked on a floor of 0%. Option A, approved by the user on November 24, 2026: the comments and the Testing rules say it now | "Record the seventh real run, and repair the coverage rule of a stopped process" |
  | 8 (B5) | `live_checks.py` read the line `- <requirement ID>: <test name>` under the budget ceiling as a part of the ceiling, and the template of `docs/workflow.md` puts that line there. An entry now ends at the next item of the list | "Record the eighth real run, and repair the entries of the live checks" |
  | 8 (B5) | RUN-17: the budget ceiling had no form, and the test writer read it as a number. Option A, approved by the user on November 24, 2026: the ceiling is an amount and a currency, and the tests get the amount and the currency apart | "The budget ceiling of the live checks is an amount and a currency (RUN-17)" |
  | 8 (B5) | RUN-18: the rules of `llm` loaded only for `prompts/**` and `src/**/llm*`, and the design named the client `src/model_client.py`. Option A, approved by the user on November 24, 2026: they load for every file of `src/` | "The rules of llm load for every file of src/ (RUN-18)" |
  | B4 | `mutation.yml` passed and kept an empty list. mutmut 3 refuses a module whose name starts with `src.`, and the projects import `from src.<module>`; the config was written for mutmut 2; and `|| true` hid each error. It now runs `mutmut==2.5.1`, fails on a fatal error or when it makes no mutant, keeps the log on a failure, and keeps the change of each surviving mutant | "The mutation workflow runs mutmut 2.5.1, and a failed run fails (B4)" |
  | B4 | `/find-bugs` said that a bug whose test passes is a false alarm. The test of a gap in the tests (a surviving mutant) passes at once, because the code is right, and the runner accepts it. The skill now says both | "Record the GitHub run (B4), and correct /find-bugs about a test that passes" |
  | Hosted model | RUN-19: no rule and no deny rule stopped a session from reading `config/.env`. Option A, approved by the user on November 25, 2026: deny rules for the Read tool and the usual read commands, and a rule in Security and privacy. In real sessions with a fake key, the old deny rules let the Read tool and `Get-Content` put the key in the transcript; the new ones refused each of 5 reads, also with the new rule line removed | "A session may not read config/.env (RUN-19)" |
  | D2 | On a new user profile, `conda create` failed on the terms of Anaconda, `SKILL.md` named a folder of one machine, and the README missed the git identity and Git. Repaired, and a second run of `/project-init` checked it (D2) | "Repair what a clean install found (D2)" |
  | ____ | ____ | ____ |

## D. Make sherpa itself ready for a release

- [x] **D1. A CI workflow for the suite of sherpa.** Needs approval. A workflow in
  `.github/workflows/` of this repository runs pytest, ruff and mypy at each push, on Windows,
  Linux and macOS. Today the suite runs only on one Windows machine, so no test ran the skill, the
  hooks or the runner on Linux or macOS.
  - Approved by the user on November 24, 2026, for Windows only, with Linux and macOS recorded as
    a scope limitation (definition of done). The workflow is `.github/workflows/suite.yml`. It
    installs the pinned tools of the new `requirements-dev.txt`, runs the lint and type checks of
    README, "How to test", and runs the suite with `pytest -n auto` on `windows-latest`. The first
    run failed 48 tests of `test_runner.py`, for one cause: Python ran from the tool cache of
    GitHub, and the runner starts only in a conda environment named after its project (`sherpa`
    in these tests). The workflow now creates the conda environment `sherpa`, as the README does.
    The second run passed on November 24, 2026: each lint and type check, and 362 tests in 301 s
    on 4 workers. It found no fault of sherpa.
  - Done when: the workflow passes on Windows.
  - Estimate: 1 hour, plus the repairs of what a clean machine finds.
  - Done in commit: "Mark D1 done: the suite passes on a clean Windows machine of GitHub"
- [x] **D2. Install sherpa from a clean clone.** Do the steps of the README, "Set up the machine
  (once)", word for word on a second machine or a new user profile. Then run `/project-init`.
  - Done when: each step works as written, or the README is correct after the run.
  - Estimate: 1 hour.
  - How: a new user profile in a scratch folder. `HOME`, `USERPROFILE`, `APPDATA` and
    `LOCALAPPDATA` named empty folders, and the skill came from a fresh clone of GitHub. Limits:
    Git, the GitHub CLI and Miniconda were already on the machine (Miniconda was linked into the
    new profile, the same version). The browser sign-ins of `gh auth login` and Claude Code were
    replaced by tokens in the environment of the process, and `gh auth setup-git` did the git part
    of `gh auth login`. `conda init cmd.exe` and the VS Code steps were not done, because they
    change the registry and the editor of the user.
  - Found and repaired:
    1. `SKILL.md` named the Miniconda Python of the machine where the skill was written. It now
       names the two places where the installer puts it, and a test refuses a user's folder in
       any file of the skill.
    2. `conda create` failed: the `defaults` channel of a new Miniconda refuses a script until the
       user accepts the terms of Anaconda. The skill reported it correctly and accepted nothing.
       Decided by the user on November 25, 2026: the skill creates the environment from
       conda-forge only. The README of a new project and the setup of sherpa say the same.
    3. The README gave no command for the git identity and no step to install Git, and did not say
       to let `gh auth login` set up git. Its example folder and the old skill were of this
       machine only.
    4. `SKILL.md` did not say that the modules are separated by spaces, and the session first
       tried commas.
  - The first run of `/project-init` committed and pushed to a new private repository, and conda
    failed (fault 2). The second run, with the repairs and `--no-github`, made the environment
    from conda-forge and pinned the tools, and `python scripts/check.py` printed
    `All checks passed.`
  - Done on: November 25, 2026. Commit: "The skill names no user's folder (D2)" and "Repair what a clean install found (D2)"
- [ ] **D3. Correct the old text that this plan found.**
  - `docs/unapproved-ideas.md`: the last line still said that Part 2 holds RUN-08 and RUN-09,
    which are decided, and a blank line was missing before section G. Corrected in the record
    commit of B2.
  - README, "File structure": the tree does not show `find-bugs`, `.github/workflows/`,
    `.coveragerc`, `.prettierrc.json`, `.stylelintrc.json`, `docs/audit-claude-golden.md` or
    `tests/test_dashboard.py`. It also does not show the files of D1 at the root of sherpa:
    `.github/workflows/suite.yml` and `requirements-dev.txt`.
  - Done when: both are correct and the suite passes.
  - Estimate: 30 minutes.
  - Done in commit: ____

## E. Write the final docs and release

- [ ] **E1. `docs/v5/`: the report, the presentation and the demo of the final workflow.** It
  comes after parts A to D, so that it is written one time. `docs/v4/` stays as the record of
  version 4, and sherpa's `CLAUDE.md` names `v5/` as current.
  - Done when: the three files show the workflow of `assets/docs/workflow.md` as built.
  - Estimate: 3 hours.
  - Done in commit: ____
- [ ] **E2. A last pass of the README.** The objectives table, "What a new project gets", and
  the record of the real runs agree with the code. The section "Paths that no real session ran" of
  this file has no open row.
  - Done when: the user read the README and accepted it.
  - Estimate: 1 hour.
  - Done in commit: ____
- [ ] **E3. Release sherpa.** Needs approval of the version scheme. Recommendation: the date as
  the version, as `release.py` does for a project (USER-10). Tag the commit, write release notes
  that name what ran in real sessions and what is suite-only, and push the tag.
  - Done when: the tag is on GitHub and the README names the version.
  - Estimate: 30 minutes.
  - Version: ____ Tag pushed on: ____
