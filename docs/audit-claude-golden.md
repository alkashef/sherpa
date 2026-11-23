# Audit of the rules in `CLAUDE_GOLDEN.md`

Rank 17 (USER-06) of `docs/unapproved-ideas.md`, approved on November 22, 2026. The audit runs
after the build adds its new rules, so it sees all of them. **The user approved the table on
November 23, 2026, and it is applied** (see "What the approval changed"). A rule that a real run
later proves necessary comes back.

## How to read it

- One row for each rule: each bullet, and each paragraph that states a rule. 180 rows.
- **Where** tells where the rule loads today: `CLAUDE.md` (every session) or the name of the rules
  file (only when Claude touches a matching file).
- **Proposal** is one of four:

  | Proposal | Meaning |
  | --- | --- |
  | Keep | The rule needs judgment, no tool checks it, and it stops a known fault. |
  | Tool | A tool can enforce it, or does already. Keep a short pointer, or delete the prose. |
  | Move | Move it out of `CLAUDE.md` into a rules file or a skill, where it loads only when needed. |
  | Delete | Another file owns it, or it is too rigid for the objectives. |

- The built `CLAUDE.md` has 198 of its 199 lines. The rows marked Move free about 45 lines.

## Summary

| Proposal | Rows |
| --- | --- |
| Keep | 117 |
| Tool | 28 |
| Move | 20 |
| Delete | 15 |

The three examples that the user named:

- Row 168, "Do not write your own decorators, metaclasses, context managers, or descriptors":
  **Delete** the ban on context managers and decorators. A `with` block for a resource of the
  project (a temporary folder, a server for a test) is plain Python, and the ban makes the code
  catch and clean up by hand. Keep the ban on metaclasses and descriptors: they are hard to read.
- Row 36, "One class per file": **Tool**. `check.py` and ESLint enforce it. Keep it, because a file
  with two classes is the second responsibility that the size rule looks for, but shorten the prose
  to the pointer.
- Row 33, "a design pattern that no `Decided` decision names": **Keep**. It is the rule that stops
  speculative structure, and the review checklist uses it. It is not too rigid: a milestone can
  add the decision with the Status `Proposed`.

## The table

| No. | Section | Where | Rule | Proposal | Reason |
| --- | --- | --- | --- | --- | --- |
| 1 | Project | CLAUDE.md | Purpose | Keep | Filled per project. |
| 2 | Project | CLAUDE.md | Stack | Keep | Filled per project. |
| 3 | Project | CLAUDE.md | Test command | Keep | The hooks and the sessions use it. |
| 4 | Project | CLAUDE.md | Run command | Keep | Filled per project. |
| 5 | Project | CLAUDE.md | Project rules, with protected paths | Keep | The only place for a rule of one project. |
| 6 | Identity | CLAUDE.md | The objective: code for humans and machines; follow every rule | Keep | Sets the intent of every other rule. |
| 7 | Identity | CLAUDE.md | The four docs always exist; a skill writes to them, not elsewhere | Keep | Stops a plugin skill from writing a second spec. |
| 8 | Identity | CLAUDE.md | Requirements live only in `docs/spec.md`; ask when not covered | Keep | The core of the method. |
| 9 | Identity | CLAUDE.md | Write the spec in EARS, one requirement per statement | Delete | `/write-spec` and `docs/workflow.md` own it; only the spec skill writes requirements. |
| 10 | Identity | CLAUDE.md | Stable IDs; never renumber; mark withdrawn | Keep | `spec_coverage.py` checks the rows, not the history. Saves 1 line if shortened. |
| 11 | Identity | CLAUDE.md | Cite IDs; do not copy their content | Keep | One fact in one place. |
| 12 | Workflow | CLAUDE.md | Follow `docs/workflow.md` exactly | Keep | Loads the workflow. |
| 13 | Workflow | CLAUDE.md | Do not refactor outside the milestone | Keep | Stops scope creep. |
| 14 | Communication | CLAUDE.md | Concise and direct; no recap | Keep | The user's preference. |
| 15 | Communication | CLAUDE.md | Top-down; one thing at a time | Keep | The user's preference. |
| 16 | Communication | CLAUDE.md | A decision request gives a recommendation and pros and cons | Keep | The user's preference. |
| 17 | Communication | CLAUDE.md | Name the kind and the file of an ID the first time | Keep | Added by D1. |
| 18 | Communication | CLAUDE.md | Critical-thinking partner; no debate in a milestone | Keep | The user's preference. |
| 19 | Communication | CLAUDE.md | The report: files changed | Keep | The user reads it. |
| 20 | Communication | CLAUDE.md | The report: tests added or updated | Keep | The user reads it. |
| 21 | Communication | CLAUDE.md | The report: tests run, N of M | Keep | Evidence before a claim. |
| 22 | Communication | CLAUDE.md | The report: assumptions and open questions | Keep | The user reads it. |
| 23 | Communication | CLAUDE.md | The report: one `DECISION:` line for each decision | Keep | The runner counts them. |
| 24 | Communication | CLAUDE.md | The report: TLDR, last, in bold | Keep | The user reads it. |
| 25 | Code smells | code-quality | Ruff, mypy and ESLint enforce the limits | Tool | A pointer only. |
| 26 | Code smells | code-quality | Never weaken a config, never add `noqa` or `type: ignore` | Keep | An `ask` rule guards the configs, but not `noqa` in code. Tool candidate: ruff `RUF100` and a `noqa` ban in `check.py`. |
| 27 | Code smells | code-quality | Two hooks run `check.py`; fix what the edit hook reports | Keep | Tells the session why a block comes. |
| 28 | Code smells | code-quality | Never bypass the hooks | Tool | `settings.json` denies `--no-verify` and `core.hooksPath`. Shorten to the pointer. |
| 29 | Code smells | code-quality | Editing the check configs asks first | Tool | `settings.json` asks; the prose repeats it. Delete. |
| 30 | Code smells | code-quality | One thing for each function, class, module | Keep | Judgment; the review checks it. |
| 31 | Code smells | code-quality | About 20 lines, 4 parameters, complexity 8 | Tool | Ruff and ESLint enforce the numbers. Keep the 300-line check. |
| 32 | Code smells | code-quality | Composition; group values; inject collaborators | Keep | Judgment. |
| 33 | Code smells | code-quality | No duplicated logic, dead code, needless abstraction, unnamed pattern, wrappers, global state | Keep | Matches the 8 smells of the review. |
| 34 | Code smells | code-quality | Code that a beginner to intermediate programmer can read | Keep | The first standard of the review. |
| 35 | Code smells | code-quality | Readable before clever; plain constructs | Delete | Repeats row 34. |
| 36 | Code smells | code-quality | One class per file, imports at the top, module boundaries | Tool | `check.py`, ruff `PLC0415` and ESLint enforce all three. |
| 37 | Architecture | CLAUDE.md | Follow the layers of the design; name the owner first | Move | To code-quality: it applies when code changes. |
| 38 | Architecture | CLAUDE.md | One module per concern; entry points only connect | Move | To code-quality. |
| 39 | Architecture | CLAUDE.md | Business logic is pure | Move | To code-quality. |
| 40 | Architecture | CLAUDE.md | One module for each external system | Move | To code-quality. |
| 41 | Architecture | CLAUDE.md | Pass external systems in; no DI framework | Move | To code-quality. |
| 42 | Architecture | CLAUDE.md | A change of layer, boundary, data model or API needs a decision | Keep | The design and the workflow depend on it; stays in `CLAUDE.md`. |
| 43 | Directory | CLAUDE.md | The table of folders | Keep | Where things live, in every session. |
| 44 | Directory | CLAUDE.md | All code under `src/`; a folder only when the design lists it | Keep | The design owns the layout. |
| 45 | Directory | CLAUDE.md | Never edit a generated file | Keep | Short and general. |
| 46 | Directory | CLAUDE.md | `cleanup.py` deletes by name, never source or data | Delete | The docstring of `cleanup.py` owns it, and no session needs it. |
| 47 | Naming | code-quality | Names by purpose; the glossary Term, never an Avoid word | Keep | Added by USER-13. |
| 48 | Naming | code-quality | Every module, class and function has a docstring | Tool | Ruff `D` enforces it. Keep the content rules below. |
| 49 | Naming | code-quality | Module docstring: what, what not, the IDs | Keep | The trace of the dashboard reads the IDs. |
| 50 | Naming | code-quality | Class docstring: one responsibility, its state | Keep | The class list of the dashboard reads it. |
| 51 | Naming | code-quality | Public function docstring: summary, args, returns, raises | Tool | Ruff `D` with the Google convention checks the parts. |
| 52 | Naming | code-quality | Comment only what is not obvious | Keep | The review smell "Comments". |
| 53 | Naming | code-quality | No TODO comments | Tool | Ruff `FIX002` (flake8-fixme) can enforce it. Add the rule, delete the prose. |
| 54 | Configuration | CLAUDE.md | Settings in `config/.env`; only `config.py` reads them | Move | To code-quality: it applies when code reads a setting. |
| 55 | Configuration | CLAUDE.md | Only the entry point imports config; no defaults in code | Move | To code-quality. |
| 56 | Configuration | CLAUDE.md | No inline URL, port, path, model, threshold | Move | To code-quality. |
| 57 | Configuration | CLAUDE.md | Fixed vocabularies are enums | Move | To code-quality. |
| 58 | Configuration | CLAUDE.md | The five steps to add a setting | Move | To code-quality. |
| 59 | Dependencies | CLAUDE.md | Prefer the standard library; ask before a dependency | Keep | A blocker of the workflow; every session must know it. |
| 60 | Dependencies | CLAUDE.md | The dependency file is the only list; same change as the import | Move | To the language rules files. |
| 61 | Dependencies | CLAUDE.md | Direct dependencies only, pinned; no `pip freeze` | Move | To the language rules files. Note: `release.py` now saves `pip freeze` in the archive, which is a record, not the list. |
| 62 | Testing | CLAUDE.md | Each requirement and example has a test named after its ID | Keep | `spec_coverage.py` checks it; every session must know it. |
| 63 | Testing | CLAUDE.md | Each workflow has an e2e test; each UI workflow a Playwright test | Move | To code-quality, with the globs of `tests/**`. |
| 64 | Testing | CLAUDE.md | A real local part, a fake only for an external service | Delete | `docs/workflow.md`, the runner prompts and `/write-tests` own it. |
| 65 | Testing | CLAUDE.md | Layout of `tests/`; requirement coverage first; 80% floor | Tool | `check.py` and `.coveragerc` enforce the floor. Keep the layout in one line. |
| 66 | Testing | CLAUDE.md | Public behavior; deterministic; temporary folders; invented data | Move | To code-quality, with the globs of `tests/**`. |
| 67 | Testing | CLAUDE.md | Never weaken a test; change one only for a changed requirement | Keep | The runner checks the hashes, but a chat session needs the rule. |
| 68 | Error handling | code-quality | Catch only at a boundary, to add context | Keep | Judgment; ruff blocks only the blind catch. |
| 69 | Error handling | code-quality | Do not catch the unexpected; the top level shows the trace | Keep | Judgment. |
| 70 | Error handling | code-quality | Invalid input is not an error; no secrets in messages | Keep | Judgment. |
| 71 | Error handling | code-quality | An app for other users records a decision for short messages | Keep | Rare, but it changes the rule above. |
| 72 | Logging | code-quality | The logging library; no `print` | Tool | Ruff `T20` and ESLint `no-console` enforce it. |
| 73 | Logging | code-quality | Configure once, from settings, plain lines | Keep | Judgment. |
| 74 | Logging | code-quality | What to log at each level | Keep | Judgment. |
| 75 | Logging | code-quality | No secrets; user content only at DEBUG; log once | Keep | Security. |
| 76 | LLMs | llm | One provider | Keep | Stops a provider switch that nobody asked for. |
| 77 | LLMs | llm | Prompts in files; model ID and limits from config | Keep | Judgment. |
| 78 | LLMs | llm | LLM output is untrusted; validate against a schema | Keep | Security. |
| 79 | LLMs | llm | The LLM only produces data | Keep | Security. |
| 80 | LLMs | llm | An API model: send only the fields that the prompt needs | Keep | Privacy. |
| 81 | LLMs | llm | A local model: localhost, offline, models in `models/` | Keep | Privacy. |
| 82 | LLMs | llm | Tests prove a bad answer of the fake model | Keep | Added by rank 16. |
| 83 | Git | CLAUDE.md | Work on `main`; never commit secrets, data, logs | Keep | Every session commits. |
| 84 | Git | CLAUDE.md | What `settings.json` blocks and asks | Tool | `settings.json` enforces it. Delete the list, keep "never work around a block". |
| 85 | Git | CLAUDE.md | Delete only your own scratch folder; touch nothing outside the repo | Keep | Safety. |
| 86 | Git | CLAUDE.md | A blocker stops the milestone; an Approval permits exactly what it says | Delete | `docs/workflow.md`, step 5 and 6, owns it. |
| 87 | Security | CLAUDE.md | Secrets only in `config/.env` | Keep | Security. |
| 88 | Security | CLAUDE.md | User data stays on the machine; flows need a decision | Keep | Privacy. |
| 89 | Security | CLAUDE.md | Never run against real data; counts, not content | Keep | Privacy. |
| 90 | Living docs | CLAUDE.md | Update each doc that a change makes wrong; link, do not copy | Keep | One fact in one place. |
| 91 | Living docs | CLAUDE.md | The table of which change updates which doc | Keep | Every session changes docs. |
| 92 | Living docs | CLAUDE.md | Docs for a person use STE | Tool | `check.py` lints them (USER-20). Keep the one line. |
| 93 | Living docs | CLAUDE.md | What `README.md` always has | Move | To a rules file with the glob `README.md`. |
| 94 | Living docs | CLAUDE.md | Never edit `CLAUDE.md` without approval | Tool | An `ask` rule guards it. Keep: a chat session can still propose the change. |
| 95 | Long-running | code-quality | Never block the UI or the request path | Keep | Judgment. |
| 96 | Long-running | code-quality | Python: async at the boundaries; `asyncio.to_thread` | Move | To the python rules file. |
| 97 | Long-running | code-quality | JavaScript: async and a Web Worker | Move | To the javascript rules file. |
| 98 | Long-running | code-quality | A long request returns 202 and a job ID | Move | To the http-apis rules file. |
| 99 | Long-running | code-quality | Tests prove a stop and a run that continues | Keep | Added by rank 16. |
| 100 | Validation | code-quality | One validation component at the boundary | Keep | Judgment. |
| 101 | Validation | code-quality | It reports every problem at once; a typed object | Keep | Judgment. |
| 102 | Validation | code-quality | The server is the authority; the browser only gives fast feedback | Move | To the html-css rules file. |
| 103 | Validation | code-quality | Python: Pydantic for API bodies, a validator class otherwise | Move | To the python rules file. |
| 104 | Python | python | Ruff and mypy enforce naming, types, docstrings and more | Tool | A pointer only. |
| 105 | Python | python | Test file and test function names | Tool | `spec_coverage.py` checks the IDs in the names. Keep the example. |
| 106 | Python | python | Annotate everything; no `Any` without a reason | Tool | mypy strict and ruff `ANN401` enforce it. |
| 107 | Python | python | Dataclasses, f-strings, `with`; no own decorators, metaclasses, context managers, descriptors; `_` for internals; `__init__.py`; `from src...` imports | Keep | Change the ban: see row 168. |
| 108 | Python | python | Only `logger` at module level, besides enums | Keep | Judgment. |
| 109 | Python | python | `main.py` is the entry point; `config.py` uses python-dotenv | Keep | The layout of every Python project. |
| 110 | Python | python | The conda environment; pip, never conda install | Keep | The environment of the runner checks it, but a session installs. |
| 111 | Python | python | The checks and the tools of `requirements.txt` | Tool | `check.py` runs them. Shorten to the command. |
| 112 | JavaScript | javascript | No framework unless the design chooses one | Keep | Judgment. |
| 113 | JavaScript | javascript | ES modules with JSDoc, `@ts-check`, no `any`, `node --test` | Tool | tsc and ESLint enforce most. Keep "no build step". |
| 114 | JavaScript | javascript | ESLint and tsc enforce the limits and the bans | Tool | A pointer only. |
| 115 | JavaScript | javascript | Naming and JSDoc | Tool | ESLint `jsdoc` rules can enforce the JSDoc part. |
| 116 | JavaScript | javascript | `main.js` connects; logic apart from views; pass collaborators | Keep | Judgment. |
| 117 | JavaScript | javascript | One frozen `config.js`; frozen vocabularies | Keep | Judgment. |
| 118 | JavaScript | javascript | `try/catch` only in `api.js`; one top-level handler; `log.js` | Keep | Judgment. |
| 119 | JavaScript | javascript | No markup strings or styles in JavaScript; no app data in storage | Keep | Judgment. |
| 120 | JavaScript | javascript | The checks | Tool | `check.py` runs them. |
| 121 | JavaScript | javascript | Report UI changes by behavior; prove them with the checks | Delete | The report format of `CLAUDE.md` covers it. |
| 122 | HTML and CSS | html-css | Stylelint and Prettier enforce the style | Tool | A pointer only. |
| 123 | HTML and CSS | html-css | Semantic elements; a title and one main heading | Keep | Judgment. |
| 124 | HTML and CSS | html-css | No `style=""` and no `<style>` | Tool | An HTML linter (html-validate) can enforce it. |
| 125 | HTML and CSS | html-css | No inline handlers or `<script>` blocks | Tool | html-validate can enforce it. |
| 126 | HTML and CSS | html-css | Markup that JavaScript needs lives in `<template>` | Keep | Judgment. |
| 127 | HTML and CSS | html-css | Nothing from the network | Keep | Privacy; a CSP header in the server can enforce it later. |
| 128 | HTML and CSS | html-css | Colors only from `theme.css` | Tool | Stylelint `color-no-hex` outside `theme.css` can enforce it. |
| 129 | HTML and CSS | html-css | Shared sheets; one sheet per view; a header comment | Keep | Judgment. |
| 130 | HTML and CSS | html-css | BEM class names by purpose | Tool | Stylelint `selector-class-pattern` can enforce BEM. |
| 131 | HTML and CSS | html-css | No duplicate rules, unused classes, hacks | Keep | Judgment. |
| 132 | HTML and CSS | html-css | Link text, `alt` text, contrast, not color alone | Keep | Accessibility. |
| 133 | HTML and CSS | html-css | Mockups are a reference, not code | Delete | No session copies a mockup into code; it says nothing that a test checks. |
| 134 | HTML and CSS | html-css | Tests prove each scenario in Playwright, keyboard only | Keep | Added by rank 16. |
| 135 | UI design | ui-design | Quick: feedback and loading states | Keep | Judgment. |
| 136 | UI design | ui-design | Responsive | Keep | Judgment. |
| 137 | UI design | ui-design | Minimal and uncluttered | Keep | Judgment. |
| 138 | UI design | ui-design | Standard layout; native controls | Keep | Judgment. |
| 139 | UI design | ui-design | Hover text and `aria-label` on each control | Tool | A Playwright accessibility check (axe) can enforce the labels. |
| 140 | UI design | ui-design | System fonts; assets only through `download_assets.py` | Keep | Privacy and licenses. |
| 141 | UI design | ui-design | Tests prove each scenario in Playwright, keyboard only | Delete | Repeats row 134; both files load for a browser front end. |
| 142 | HTTP APIs | http-apis | FastAPI; async handlers; JSON; no templates | Keep | The stack choice of the module. |
| 143 | HTTP APIs | http-apis | A handler calls one service function | Keep | Judgment. |
| 144 | HTTP APIs | http-apis | Plural kebab-case paths under `/api/`; `/health` | Keep | Judgment. |
| 145 | HTTP APIs | http-apis | Pydantic bodies; 422, 404, 409 | Keep | Judgment. |
| 146 | HTTP APIs | http-apis | One shared authentication dependency | Keep | Security. |
| 147 | HTTP APIs | http-apis | CORS origins from config, none by default | Keep | Security. |
| 148 | HTTP APIs | http-apis | E2E tests through the test client | Keep | Judgment. |
| 149 | HTTP APIs | http-apis | Tests prove status, body and a failed outside service | Keep | Added by rank 16. |
| 150 | Data | data | Data in `data/`, code in `src/` | Keep | Layout. |
| 151 | Data | data | Raw input is read-only; output can be made again | Keep | Safety. |
| 152 | Data | data | One module for each data store | Delete | Repeats row 40 (one module for each external system). |
| 153 | Data | data | Paths from config; tests use temporary folders | Delete | Rows 56 and 66 say it. |
| 154 | Data | data | Document the data model in the design | Delete | The design template (`erDiagram`, USER-14) and Living docs own it. |
| 155 | Data | data | UUID IDs and UTC ISO timestamps | Keep | A choice that the design does not repeat. |
| 156 | Data | data | Back up before a change rewrites stored data | Keep | Safety. |
| 157 | Data | data | Tests prove the stored form, an interrupted write, old data | Keep | Added by rank 16. |
| 158 | CLI | cli | argparse in `main.py`; flags in the README | Keep | Judgment. |
| 159 | CLI | cli | Only the intended output; a progress counter on one line | Keep | Judgment. |
| 160 | CLI | cli | Exit codes | Keep | Tests prove them (row 161). |
| 161 | CLI | cli | Tests prove exit codes and output; a second run gives the same result | Keep | Added by rank 16. |
| 162 | Static site | static-site | `content/` is the source | Keep | Layout. |
| 163 | Static site | static-site | `site/` is generated and committed | Keep | Layout. |
| 164 | Static site | static-site | One template; navigation from content; relative links; slugs | Keep | Judgment. |
| 165 | Static site | static-site | Fail on missing metadata; skip drafts | Keep | Judgment. |
| 166 | Static site | static-site | `marked` at build time only | Keep | The stack choice of the module. |
| 167 | Static site | static-site | Works without JavaScript; static files only | Keep | Judgment. |
| 168 | Python | python | (part of row 107) No own decorators, metaclasses, context managers, descriptors | Delete | Delete "decorators" and "context managers"; keep metaclasses and descriptors. A `with` block for a resource is plain Python. |
| 169 | Static site | static-site | The README explains add, build, preview, publish | Delete | Row 93 (what README always has) and Living docs cover it. |
| 170 | MCP | mcp | The official SDK; tools over MCP only | Keep | The stack choice of the module. |
| 171 | MCP | mcp | Streamable HTTP on 127.0.0.1; no SSE | Keep | Security. |
| 172 | MCP | mcp | Typed schemas; no LLM inside a server | Keep | Judgment. |
| 173 | MCP | mcp | A host checks the tool and handles failures | Keep | Judgment. |
| 174 | MCP | mcp | The calls are async | Delete | Long-running work (row 95) covers it. |
| 175 | MCP | mcp | E2E tests cover startup, discovery, invocation, side effects | Keep | The "Tests prove" of the module. Rename it to that form. |
| 176 | Docker | docker | Docker for services and deployment; the app runs from conda | Keep | Judgment. |
| 177 | Docker | docker | `settings.json` blocks volume deletion | Tool | `settings.json` enforces it; keep only "volumes are protected data". |
| 178 | Docker | docker | Ports on 127.0.0.1; pinned base image; telemetry off | Keep | Security. A hadolint check can enforce the pin later. |
| 179 | Docker | docker | No secrets or data in an image; `.dockerignore` | Keep | Security. |
| 180 | Living docs | CLAUDE.md | (row 91, the table) "A library added or removed" goes to `requirements.txt` | Delete | Row 60 says it; the table keeps four rows. |

## What the approval changed

One commit on November 23, 2026 did this:

1. Moved rows 37 to 41 (Architecture), 54 to 58 (Configuration), and 63 and 66 (a new section,
   "Test code") to `code-quality`. Row 42 went to Workflow, so it stays in `CLAUDE.md`. Rows 60
   and 61 went to the Python and JavaScript sections, and rows 96 to 98, 102 and 103 to the
   Python, JavaScript, HTTP APIs and HTML and CSS sections. Row 93 went to a new rules file,
   `readme`, with the glob `README.md`.
2. Deleted the rows marked Delete, and shortened the rows marked Tool to a pointer.
3. Added the tool rules of rows 53 (ruff `FIX`) and 128 to 130 (Stylelint: `color-no-hex`,
   `color-named` and the color functions, off in `theme.css`; `selector-class-pattern` for BEM),
   each with a test. Row 53 also got ESLint `no-warning-comments`, because the rule covers
   JavaScript too. A real run of Stylelint and ESLint on good and bad files checked the rules once.
4. The built `CLAUDE.md` has 138 lines, down from 199.

Where the commit differs from the table, because a check of the tool showed that the Reason was
wrong:

- Row 48: ruff `D` checks only the public modules, classes and functions. The rule stays, with
  that pointer.
- Row 51: ruff `D` with the Google convention does not require the parts of a docstring (the
  arguments, the return value, the errors). The rule stays as it was.
- Rows 115, 124, 125 and 139 name a tool that the project does not have yet (ESLint `jsdoc`,
  html-validate, axe). Their rules stay as they were until the tool comes in.
