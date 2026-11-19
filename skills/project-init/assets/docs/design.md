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

TBD

### 2.2 Directory structure

Create a folder only when it is listed here, and update this table in the same change.

{{DIRECTORY_STRUCTURE}}

### 2.3 Settings

| Setting | Default | Meaning |
| --- | --- | --- |

## 3. Data model

TBD

## 4. Interfaces

Name every interface a test needs: entry points, inputs and outputs, stored records, and public
functions. The tests are written from the spec and this file, without the code.

TBD

## 5. Test design

The test level of each requirement (`unit`, `e2e` or `ui`), the test tools, and the fake for each
external system. `CLAUDE.md` (Testing) owns the test rules.

TBD

## 6. Open design questions

The design is approved when no decision is `Proposed` and this table is empty.

| ID | Question | Who decides | Blocks what |
| --- | --- | --- | --- |
