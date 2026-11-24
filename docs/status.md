# Status of the finish

The state of each step of `completion-plan.md`, and of each other item that is open. Claude
updates this file when a status changes. Status: `-` to do, `doing`, `done`. A step is done when
it is built, committed and pushed, nothing still runs, and no issue is open.

Last update: November 24, 2026.

## The steps, in the order of priority

| # | Step | What and why in this place | Status |
| --- | --- | --- | --- |
| 1 | D1 | CI workflow (Windows only, by the user's decision). Cheap, and it finds faults in the hooks and the runner that every later run uses. | done |
| 2 | B3 | Real interview. The only test of "zero lines of code" from the first step, which is the main objective. 2 hours of the user's time. | doing |
| 3 | B5 | Other modules. `llm`, `validation` and `logging` send data to a provider and make paid calls, so they carry the most risk. The other modules are quick decisions. | done |
| 4 | B4 | GitHub run. Needs the project of B1 or B3. Its workflows already pass in the suite, so lower risk. Needs the user's approval. | - |
| 5 | D2 | Clean clone install. Checks the README setup steps. After D1, which can show faults from the operating system. | - |
| 6 | D3 | README tree. Low value, but only 30 minutes. Anywhere before E2. | - |
| 7 | E1 | `docs/v5/`. After parts B to D, so that it is written one time. | - |
| 8 | E2 | Last README pass. After B5, because every row of the paths table must be closed. | - |
| 9 | E3 | Release tag. Last. | - |

## Other open items

| # | Item | What and why | Status |
| --- | --- | --- | --- |
| 10 | C1 | Repair each fault that a run finds. Opened again by B5 (three faults). The user accepted the checks in real sessions on November 24, 2026. | done |
| 11 | Hosted LLM provider | B5 ran the `llm` module with a local model only, because no API key is on the machine. Data that leaves the machine and a paid call are not checked. Needs the user's decision: accept as suite-only, or give an API key for a run. | - |
