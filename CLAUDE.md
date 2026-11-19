# sherpa

## Purpose

sherpa helps a developer build software that meets the objectives below. It is delivered as the
`project-init` Claude Code skill. Run in an empty folder, the skill gives the new project its
starting files (`CLAUDE.md` and path-scoped rules, docs, README, tool configs, starting folders),
commits them, creates a GitHub repository, and pushes. Everything the skill needs is in
`skills/project-init/`.

This repository is the skill's source. Working on it is not the same as working on a project the
skill creates: `skills/project-init/assets/` holds the files new projects receive, including their
`CLAUDE.md` master (`CLAUDE_GOLDEN.md`). This file is for working on the skill itself and is never
copied into a new project.

## Objectives

The software a developer builds with sherpa must be:

- Written with zero lines of code by the developer: natural language is the programming language.
- Production-level: no prototype or demo software.
- High-quality: correct, readable, tested, maintainable.

## Approach

Build a Spec-Driven Development (SDD) framework for building software: approved spec, then design,
then plan, then one milestone at a time. Deterministic checks (tests, linters, type checkers, hooks)
bound the probabilistic AI generation, so a rule a tool can enforce goes into that tool's config,
not into prose.

The ideal is a framework that works with any AI coding assistant (Claude, Gemini, etc.). The
current choice is to limit it to Claude Code: the skill, the rules files, the permissions, the hooks
and the milestone runner all use Claude Code features. Do not add support for another assistant
unless asked, but keep the method itself (spec, design, plan, checks) free of Claude-specific
wording where it costs nothing.

## Where things are

- `skills/project-init/SKILL.md`: what Claude reads when the skill runs.
- `skills/project-init/scripts/`: `init_project.py` (folder, git, GitHub) and `build_instance.py`
  (builds the new project's files).
- `skills/project-init/assets/`: everything a new project receives.
- `tests/`: the test suite. It is not installed with the skill.
- `docs/`: the SDD report, presentation and demo, one folder per version (`v2/` is current, `v1/`
  is the workflow before the test session); `unapproved-ideas.md` holds proposed workflow changes.
  Never implement one without the user's approval.
- `README.md`: the full description, usage, contribution and test guide. Read it before changing
  what new projects get.

## Environment

Conda environment: `sherpa`. Use it for all testing, linting and type checks in this
repository. Do not use `base`, another project's environment, or the system Python.

Run commands in it with `conda run -n sherpa <command>`, for example
`conda run -n sherpa python -m pytest` (the suite) or
`conda run -n sherpa python skills/project-init/scripts/build_instance.py <folder> --dry-run`.
The lint and type-check commands are in README, "How to test".

## Rules for changing the skill

- Change what new projects get by editing `skills/project-init/assets/`. For the rules, edit
  `assets/CLAUDE_GOLDEN.md` and keep its section tags.
- The built `CLAUDE.md` of a new project must stay under 200 lines, blank lines included. If the
  test fails, shorten a section or move one into a rules file. Do not raise the limit.
- The workflow, the project skills and the scripts in `assets/` are the same in every project. When
  a change comes back from a project that used them, remove that project's names first (its file
  names, ID scheme, tools) and do not bring back a check it cut. A test refuses the known ones.
- Do not edit `assets/CLAUDE_GOLDEN.md.646`. It is a reference copy that nothing reads.
- Run the test suite before every commit.

## Git

Every commit is followed by a sync: pull (`git pull --rebase`), then `git push` to `origin`. Never
leave a commit only on this machine. If the pull or the push fails, stop and report it.

## Communication rules

- Be very concise and direct.
- Use a top-down structure: big picture first, then details.
- Handle one thing at a time: one item, one question, one suggestion, etc.
- Act as a rigorous critical thinking partner: challenge my assumptions, expose weaknesses and blind spots, test my reasoning, present alternative viewpoints, and agree only when the argument is strong.
