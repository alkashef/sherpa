# Status of the finish

The state of each step of `completion-plan.md`, and of each other item that is open. Claude
updates this file when a status changes. Status: `-` to do, `doing`, `done`. A step is done when
it is built, committed and pushed, nothing still runs, and no issue is open.

The order follows the dependencies, so that no work is done two times: first the runs that can
find faults, then the repairs (C1), then the steps that check or write the README and the docs,
and the release last.

Last update: November 25, 2026.

| # | Step | What it is, and why it is in this place | Status |
| --- | --- | --- | --- |
| 1 | D1 | CI workflow (Windows only, by the user's decision). It needs nothing, and every later run uses it. | done |
| 2 | B5 | Other modules: `llm`, `validation`, `logging` and `live_checks.py` in a real run; the others accepted as suite-only. | done |
| 3 | Hosted LLM provider | B5 used a local model only, because no API key is on the machine. Data that leaves the machine and a paid call are not checked. Needs the user's decision: accept as suite-only, or give an API key for a run. A run can find faults, so it comes before C1. | - |
| 4 | B3 | Real interview, the only test of "zero lines of code" from the first step. 2 hours of the user's time. It can find faults, so it comes before C1. | doing |
| 5 | B4 | GitHub run on the project of B5: `check.yml`, `mutation.yml`, `/find-bugs` and a release. It can find faults, so it comes before C1. | done |
| 6 | C1 | Repairs of the faults that steps 2 to 5 find. After all the runs, so each repair is made one time. It opens again when a run finds a fault. | done |
| 7 | D2 | Clean clone install: the README setup steps on a new user profile. After the repairs, because they can change those steps. | - |
| 8 | D3 | README file tree. After every step that adds files, so the tree is written one time. | - |
| 9 | E1 | `docs/v5/`: report, presentation and demo. After parts B to D, so it is written one time. | - |
| 10 | E2 | Last README pass. After E1, and after every row of the paths table is closed. | - |
| 11 | E3 | Release tag. Last. | - |
