---
name: write-design
description: Turn an approved software spec into a practical technical design through a lightweight adaptation of Attribute-Driven Design 3.0. Use for architecture, technology stack selection, design reviews, or changes to docs/design.md in a Spec, Design, Plan workflow. Recommend languages, frameworks, and major libraries. Preserve requirement IDs and stable DEC IDs. Support users without programming experience through one question at a time. Do not use for initial requirements discovery, visual styling alone, implementation planning, or coding.
---

# Write Design

Build a design that explains how the approved requirements will work. Apply ADD 3.0 with depth proportional to technical risk.
Treat this as an adaptation of ADD, not the official method or a guarantee of technical quality.

## Establish the baseline

- Read project instructions, applicable rules, `docs/workflow.md`, `docs/spec.md`, and the current `docs/design.md`.
- Read existing code, manifests, and tests when available. Distinguish an implemented fact from a proposed design.
- Use the project's paths and conventions. Default to `docs/design.md` when none exist.
- Identify whether the request creates, resumes, reviews, or amends a design. Preserve unrelated decisions and user edits.
- Read `docs/unapproved-ideas.md` when it exists. An idea there is not a decision. Take one up only when the user asks; when it becomes a decision, or the user drops it, delete its line there in the same change.
- Confirm approval from the available record or the user's instruction. If the spec is unapproved, analyze it provisionally and resolve approval before finalizing design.
- If requirements are absent, ask for the spec or use `/write-spec` first. Do not invent business behavior to make architecture possible.

Read [the design guide](references/design-guide.md) when choosing drivers, boundaries, or validation methods.
Read [the technology guide](references/technology-guide.md) before recommending a stack or new dependency.
Use [the design template](assets/design-template.md) only for a new document. Preserve an existing format.

## Keep each fact in its proper file

Keep requirements and EARS statements in `spec.md`. Cite their IDs in design instead of copying their text.
Keep architecture, technical rules, data structures, interfaces, settings, and decisions in `design.md`.
Keep milestones, task order, and implementation approvals in `plan.md` under the local workflow.
Keep installed direct dependencies and exact pins in the existing dependency files. Do not duplicate the installed inventory in design.

When a design requires a changed requirement, propose the exact spec change for approval. Do not silently edit the spec.
Treat the spec as authoritative when design and spec conflict. Analyze unaffected parts while the conflict awaits resolution.
Follow local rules for an active blocked milestone. Do not start a milestone or create a plan merely to finish design.

## Select the drivers

Find the requirements and constraints that most affect structure or technology. Cite existing IDs and the source of project constraints.
Consider critical workflows, data ownership, performance, availability, security, privacy, deployment, cost, and maintainability only where relevant.
Use measurable quality scenarios from the spec. If a missing target could change the design, ask one business question to resolve it.
Do not invent traffic volumes, uptime targets, budgets, retention periods, or regulatory obligations.
Label estimates and assumptions. Record who must resolve each material unknown and whether it blocks design or later implementation.

## Develop the design

For each major design issue, apply this cycle internally:

1. Select the driver or risk to address.
2. Compare the recommended approach with a meaningful feasible alternative.
3. Define responsibilities, data ownership, interfaces, and allowed dependencies.
4. Walk a critical workflow and its failure paths through the design.
5. Assess the result against the driver and identify the remaining uncertainty.

Repeat only where another decision or unresolved risk warrants more detail. Avoid alternatives for trivial choices.
Prefer the smallest structure that satisfies the drivers and project rules. Add distributed services, queues, or abstraction layers only with a concrete reason.
In an existing project, examine the cost of reuse, migration, and operating both designs before proposing a replacement.
Record enough detail for separate implementation sessions to make consistent choices. Do not specify every private function.

## Work with the user

Infer expertise from the conversation. Ask at most one question per message and give one procedural step at a time.
Explain consequences in business terms. Recommend the technical choice yourself rather than asking a non-programmer to choose a library by name.
Ask only for facts, priorities, permissions, or trade-offs that the available evidence cannot resolve.
For a consequential choice, state the recommendation, relevant alternatives, business effect, and the exact decision needed.
Do not ask for approval again when the user already approved that choice and scope.
Distinguish business approval from technical review. Identify the specific decision that needs an experienced software reviewer when the evidence exceeds your ability to assess it.
Do not require a technical reviewer for every routine choice or claim that an AI review proves correctness.

## Write the design

Preserve the project's headings. For project-init, retain Decisions, Architecture, Data model, Interfaces, Test design, and Open design questions.
Add compact subsections for drivers, technology choices, important flows, and unresolved risks only when needed.
Cover these concerns where they apply:

- Components, layers, responsibilities, import rules, and the directory structure.
- Languages, runtime, frameworks, database, major libraries, and verification tools.
- Data types, identities, ownership, relationships, integrity, persistence, and migration boundaries.
- Public contracts, authorization boundaries, validation, errors, and recovery behavior.
- Deployment, external data flows, secrets, settings, and operational failure handling.
- How each requirement is tested, as one row of the table in "Test design": its level (`unit` for logic, `e2e` through the outermost non-browser entry point, `ui` for what only the page shows, `live` for what only a live external service can prove), the test tool, and the real local part or the fake that the test uses.
- A test uses a real local part where one exists: a database file in a temporary folder, a server that the test starts on 127.0.0.1. Name a fake only for an external service.
- For each module of the project, the test design covers what the line "Tests prove" of its rules file names (`.claude/rules/`), for the requirements that the module serves.
- Every user scenario of a project with a browser front end gets a `ui` test. The browser tool is Playwright.
- The module boundaries, as rows of the table "Module boundaries": each module under `src/`, and the other modules that it can import. `scripts/check.py` fails when the code breaks a row.

The test writer reads only the spec and the design, never the code (`/write-tests`). So name every interface a test needs: entry points, request and response fields, stored records, and public functions.

Draw the data model under "Data model" as one Mermaid `erDiagram`: each entity with its typed attributes, and the relationships between the entities. Name each entity with a Term of the glossary in `docs/spec.md`. Under "Interfaces", link a stored record to its entity and do not copy its attributes.

For an AI feature, define the provider or local runtime, outgoing data, output validation, failure handling, and test boundaries. Respect project rules.
Draw one Mermaid diagram of the components and their interfaces under "Components". This diagram is required: show each component, each connection, and the contract or the data on each important connection. Add another diagram only when it clarifies boundaries, dependencies, or runtime behavior. Use the least detail that helps implementation.
A retry, a fallback or a recovery needs a requirement that asks for it. Then a `Decided` decision says how, and the test design names the test that covers it (`CLAUDE.md`, Error handling).
When `docs/releases.md` lists a release, and a change breaks the stored data or a public interface of a released version, record the transition in a decision: how the old data or the old callers move to the new version.
Keep directory entries and technical settings concrete. Reference requirement IDs for user-visible rules and limits.

## Record decisions and evidence

Give every significant design decision a stable `DEC-NNN`, or the existing project convention.
Never renumber or reuse IDs. Find the highest allocated ID in the current document and available Git history before assigning a new one.
If history is unavailable, resolve the allocation boundary before finalizing new IDs. Provisional labels must not enter the approved design.
Record context, requirement references, choice, rationale, alternatives, consequences, and a validation method. Use compact tables or nearby details.
Give every decision a Status. Set it to `Decided` only when the user chose or confirmed the decision. A decision that you derived from a requirement is `Proposed` until the user confirms it.
Keep one current decision per topic. When a decision is replaced, keep its row, set its Status to `Superseded`, and name the replacement in its Why. Give the replacement a new ID.
A `Proposed` decision whose Why says "auto-decided in M<n>, review" was made by a milestone session (`docs/workflow.md`, Rules). Show each one to the user: confirm it as `Decided`, or replace it.
Record a question that the design cannot settle in the table "Open design questions", with who decides it and what it blocks. Delete the row when the question is closed.
Separate observed results, documented capabilities, estimates, assumptions, and planned checks. Cite sources for consequential claims.
Never mark a test, benchmark, compatibility check, or prototype as successful unless it actually ran.

## Match the modules to the design

When the user approves the design, compare its languages, components and folders with the modules of the project: the files in `.claude/rules/` and the `paths:` globs at their top.

1. Find the builder of the `project-init` skill: `build_instance.py` in the `scripts/` folder of that skill (for example `~/.claude/skills/project-init/scripts/`). The skill is installed for the user, not in the project. If you cannot find it, ask the user for its folder.
2. Run `python <builder> --list-modules` and show its table as it is: `No. | Module | Section | Details`. Mark the modules that the project has.
3. Propose, by number, each module that the design needs and the project lacks, and the globs of each rules file that do not match the folders of the design. The user approves.
4. Run `python <builder> . --add <module> ...`. It adds the rules file, the config files and the folders of each module, and keeps every existing file. Then edit the `paths:` globs to the real folders.

## Finish at the design boundary

Check that the design addresses the architectural drivers, respects the spec, and gives significant decisions real alternatives and validation methods.
Check references, unique IDs, technology evidence, data flows, interface failures, and consistency with project rules.
Check that material unknowns have an owner and a blocking condition. Do not call an unresolved stack choice final.
Check that every requirement has a test level and that the interfaces its test needs are named. `python scripts/spec_coverage.py --consistency` lists a requirement without a test level and an ID that the spec does not have.
Check that the component diagram and the table of module boundaries agree with the directory structure.
Present the concrete design before requesting any approval required by project rules. Allow review in chat or a draft without replacing approved content prematurely.
Record only approval actually given: a decision becomes `Decided` when the user chooses or confirms it. The design is approved when no decision is `Proposed` and no design question is open. Technical review and user approval are separate facts.
Save authorized design edits and follow applicable document checks and Git rules. Report the result and any remaining blocker briefly.
Stop after design. Do not install dependencies, create application code, run experiments, or build milestones unless separately authorized.
After approval, tell the user the next step is `/write-plan`.
