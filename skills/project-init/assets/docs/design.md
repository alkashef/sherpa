# Design — {{PROJECT_NAME}}

How to build what `spec.md` says. If this file and the spec disagree, the spec wins.

## 1. Decisions

One current decision per topic. Status: `Decided` means the user chose or confirmed it. `Proposed`
means the AI derived it and the user has not confirmed it. `Superseded` means a newer decision
replaced it: keep its row, and name the replacement in Why. Never reuse or renumber an ID.

| ID | Status | Decision | Why |
| --- | --- | --- | --- |
| DEC-001 | Proposed | {{STACK}} | TBD |

## 2. Architecture

### 2.1 Components

One Mermaid diagram of the components and their interfaces, then one line for each component:
what it does and what it owns.

TBD

### 2.2 Directory structure

Create a folder only when it is listed here, and update this table in the same change.

{{DIRECTORY_STRUCTURE}}

### 2.3 Settings

| Setting | Default | Meaning |
| --- | --- | --- |

### 2.4 Module boundaries

A module is a folder or a file under `src/`. `May import` lists the other modules of this table
that it can import, or `none`. `scripts/check.py` fails when the code breaks a row.

| Module | May import |
| --- | --- |

## 3. Data model

TBD

## 4. Interfaces

Name every interface a test needs: entry points, inputs and outputs, stored records, and public
functions. The tests are written from the spec and this file, without the code.

TBD

## 5. Test design

The test level of each requirement (`unit`, `e2e`, `ui` or `live`), the test tool, and the real
local part or the fake that the test uses. `CLAUDE.md` (Testing) owns the test rules.
`scripts/spec_coverage.py --consistency` fails when a requirement has no row here.

| Requirement | Level | Test tool | Real local part or fake |
| --- | --- | --- | --- |

## 6. Open design questions

The design is approved when no decision is `Proposed` and this table is empty.

| ID | Question | Who decides | Blocks what |
| --- | --- | --- | --- |
