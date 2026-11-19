# Design — <project name>

How to build what `spec.md` says. If this file and the spec disagree, the spec wins.

Review state: <draft, awaiting a named decision, or approved scope with its approval reference>. The design is approved when no decision is `Proposed` and no design question is open.
Spec baseline: <document path and revision when available>.

## 1. Decisions

Keep one current decision per topic. Never reuse or renumber a decision ID. Keep the row of a replaced decision with the Status `Superseded`, and name its replacement in Why.
Status: `Decided` means the user chose or confirmed it. `Proposed` means the AI derived it and the user has not confirmed it.

| ID | Status | Decision | Why and requirement references |
| --- | --- | --- | --- |
| <DEC ID> | <Decided, Proposed or Superseded> | <chosen approach> | <reason, spec IDs, project constraint references> |

### <DEC ID>: <topic>

- Context: <driver or risk>.
- Alternatives: <feasible alternatives and reasons for rejection>.
- Consequences: <benefits, costs, limitations, and remaining risk>.
- Evidence: <source or actual result, otherwise explicit assumption>.
- Validation: <check and pass criterion, with planned or executed status>.
- Revisit when: <specific change that would invalidate the choice>.

## 2. Architecture

### 2.1 Components

| Component or layer | Responsibility and owned state | Allowed dependencies | References |
| --- | --- | --- | --- |

### 2.2 Directory structure

Create a folder only when it is listed here. Keep the layout consistent with the components.

| Path | Purpose and owner |
| --- | --- |

### 2.3 Settings

| Setting | Default | Meaning and references |
| --- | --- | --- |

### 2.4 Technology choices

Record selected technologies and proposals here. Keep the installed dependency inventory and exact pins in the dependency files.

| Technology | Role | Decision | State and compatibility constraint | Official source and date checked |
| --- | --- | --- | --- | --- |

### 2.5 Critical flows and operations

<Describe applicable workflow paths, failures, deployment, recovery, and external data flows. Cite requirements and decisions.>

## 3. Data model

<Define entities, types, ownership, relationships, integrity, persistence, and migration boundaries where applicable. Cite the relevant IDs.>

## 4. Interfaces

<Define applicable public contracts, inputs, outputs, validation, authorization, errors, and recovery. Name every interface a test needs: entry points, request and response fields, stored records, and public functions. Cite the relevant IDs.>

## 5. Test design

<State the test level of each requirement (`unit`, `e2e` or `ui`), the test tools, the test harness, and the fake for each external system. The project rules own the test policy: cite them and do not weaken them.>

## 6. Open design questions

| ID | Question, risk or design check, and references | Who decides | Blocks what |
| --- | --- | --- | --- |

<Remove unused optional sections. Resolve material blockers before declaring the design ready for planning.>
