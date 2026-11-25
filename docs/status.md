# Status of the finish

The state of each step of `completion-plan.md`, and of each other item that is open. Claude
updates this file when a status changes. Status: `-` to do, `doing`, `done`. A step is done when
it is built, committed and pushed, nothing still runs, and no issue is open.

The order follows the dependencies, so that no work is done two times: first the runs that can
find faults, then the repairs (C1), then the steps that check or write the README and the docs,
and the release last.

The Model and effort column recommends the Claude model and the effort for the session that
does the step, by the rule of `/write-plan`: the smallest that fit. `opus` is for a step that
judges or repairs the framework, or writes much text that must agree with the code. `sonnet` is
for a step that follows written steps. The aliases mean the latest model of each family.

Last update: November 25, 2026.

| # | Step | What it is, and why it is in this place | Model and effort | Status |
| --- | --- | --- | --- | --- |
| 1 | D1 | CI workflow (Windows only, by the user's decision). It needs nothing, and every later run uses it. | `sonnet`, medium | done |
| 2 | B5 | Other modules: `llm`, `validation`, `logging` and `live_checks.py` in a real run; the others accepted as suite-only. | `opus`, high | done |
| 3 | Hosted LLM provider | B5 used a local model only. On November 25, 2026, a run used an OpenAI model with the user's key, kept outside the project, and a ceiling of 1 USD. Its live check passed, and the key is in no file, output or transcript. A run can find faults, so it comes before C1. | `opus`, high | done |
| 4 | RUN-19 | No rule or deny rule stopped an unattended session from reading `config/.env`, so a real key could land in a session transcript. Found while row 3 was planned. Option A, approved by the user on November 25, 2026: deny rules and a rule line, checked in real sessions with a fake key. Recorded in C1. | `opus`, medium | done |
| 5 | B3 | Real interview, the only test of "zero lines of code" from the first step. 2 hours of the user's time. It can find faults, so it comes before C1. | `opus`, high | doing |
| 6 | B4 | GitHub run on the project of B5: `check.yml`, `mutation.yml`, `/find-bugs` and a release. It can find faults, so it comes before C1. | `sonnet`, high | done |
| 7 | C1 | Repairs of the faults that steps 2 to 6 find, and of RUN-19. After all the runs, so each repair is made one time. It opens again when a run finds a fault. | `opus`, high | done |
| 8 | D2 | Clean clone install: the README setup steps on a new user profile. After the repairs, because they can change those steps. Done on November 25, 2026: it found four faults (a folder of one machine in `SKILL.md`, the terms of Anaconda, the git identity, the module syntax), now repaired, and the second run of `/project-init` passed `check.py`. | `sonnet`, medium | done |
| 9 | D3 | README file tree. After every step that adds files, so the tree is written one time. | `sonnet`, low | done |
| 10 | E1 | `docs/v5/`: report, presentation and demo. After parts B to D, so it is written one time. | `opus`, high | - |
| 11 | E2 | Last README pass. After E1, and after every row of the paths table is closed. | `opus`, medium | - |
| 12 | E3 | Release tag. Last. | `sonnet`, low | - |
