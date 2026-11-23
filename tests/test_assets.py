"""The skill's assets agree with what build_instance.py expects to find in them."""

import hashlib
import json
import re
import sys
from pathlib import Path

import build_instance as bi
from helpers import build, run


def golden_ids() -> set[str]:
    """Return the IDs of every section in the golden master."""
    return {s.section_id for s in bi.read_sections(bi.assets_dir() / "CLAUDE_GOLDEN.md")}


def placed_ids() -> set[str]:
    """Return the IDs of every section the builder puts in CLAUDE.md or a rules file."""
    in_rules = {i for _, ids in bi.rule_files().values() for i in ids}
    return set(bi.always_loaded()) | in_rules


def test_every_listed_asset_exists() -> None:
    listed = [f for files in bi.template_files().values() for f in files]
    listed += bi.rendered_templates()
    missing = [f for f in listed if not (bi.assets_dir() / f).is_file()]
    assert missing == []


def test_every_named_section_is_in_the_golden_master() -> None:
    named = placed_ids() | set(bi.optional_flags().values())
    assert named - golden_ids() == set()


def test_every_golden_section_goes_somewhere() -> None:
    assert golden_ids() - placed_ids() == set()


def test_every_bash_rule_has_a_powershell_twin() -> None:
    # On Windows, Claude Code may run commands with its PowerShell tool, which Bash(...) rules
    # do not cover. A headless session ran `git reset --hard` until each rule got a twin.
    settings = json.loads((bi.assets_dir() / ".claude" / "settings.json").read_text("utf-8"))
    for kind, rules in settings["permissions"].items():
        bash = {r[len("Bash(") :] for r in rules if r.startswith("Bash(")}
        powershell = {r[len("PowerShell(") :] for r in rules if r.startswith("PowerShell(")}
        assert bash - powershell == set(), kind


def test_every_edit_is_checked_by_a_hook() -> None:
    settings = json.loads((bi.assets_dir() / ".claude" / "settings.json").read_text("utf-8"))
    [entry] = settings["hooks"]["PostToolUse"]
    assert set(entry["matcher"].split("|")) >= {"Edit", "Write"}
    assert entry["hooks"][0]["command"].endswith('/scripts/run-check.sh" --edited')


def test_check_configs_and_hooks_ask_before_an_edit() -> None:
    # The hooks enforce these files; loosening one is the easy way to make a check pass.
    settings = json.loads((bi.assets_dir() / ".claude" / "settings.json").read_text("utf-8"))
    protected = [
        "ruff.toml",
        "mypy.ini",
        "pytest.ini",
        ".coveragerc",
        "package.json",
        "tsconfig.json",
        "eslint.config.js",
        ".prettierrc.json",
        ".stylelintrc.json",
        ".githooks/**",
        "scripts/check.py",
        "scripts/spec_coverage.py",
        "scripts/run-check.sh",
    ]
    ask = settings["permissions"]["ask"]
    assert [f for f in protected if f"Edit(/{f})" not in ask] == []


def test_a_milestone_in_chat_needs_no_permission_prompt() -> None:
    # IMPL-02 and C2: the git steps of a milestone branch and the two chat steps of the runner.
    # `git switch`, not `git checkout`: `git checkout <file>` discards changes.
    settings = json.loads((bi.assets_dir() / ".claude" / "settings.json").read_text("utf-8"))
    allow = settings["permissions"]["allow"]
    for command in (
        "git switch -c milestone/*",
        "git switch main",
        "git merge --ff-only milestone/*",
        "git branch -d milestone/*",
        "python scripts/milestones-runner.py --tests-only *",
        "python scripts/milestones-runner.py --review-only *",
    ):
        assert f"Bash({command})" in allow, command
    assert [rule for rule in allow if "checkout" in rule] == []


def test_a_shell_may_not_write_a_file_in_another_encoding() -> None:
    # RUN-04: Windows PowerShell 5.1 writes these in the ANSI code page, not in UTF-8.
    settings = json.loads((bi.assets_dir() / ".claude" / "settings.json").read_text("utf-8"))
    deny = settings["permissions"]["deny"]
    for cmdlet in ("Set-Content", "Out-File", "Add-Content"):
        assert f"PowerShell({cmdlet} *)" in deny, cmdlet


def test_the_spec_and_the_workflow_ask_before_an_edit() -> None:
    # An ask rule refuses when nobody can answer, so an unattended milestone cannot change the
    # requirements or the rules it works under (docs/workflow.md, Approval).
    settings = json.loads((bi.assets_dir() / ".claude" / "settings.json").read_text("utf-8"))
    ask = settings["permissions"]["ask"]
    assert [f for f in ("docs/spec.md", "docs/workflow.md") if f"Edit(/{f})" not in ask] == []


def test_every_section_id_is_unique() -> None:
    sections = bi.read_sections(bi.assets_dir() / "CLAUDE_GOLDEN.md")
    assert len(sections) == len(golden_ids())


def project_skills() -> list[Path]:
    """Return the folder of each skill that new projects receive."""
    return sorted(p for p in (bi.assets_dir() / ".claude" / "skills").iterdir() if p.is_dir())


def test_project_skills_are_the_seven_slash_commands() -> None:
    names = [p.name for p in project_skills()]
    assert names == [
        "code-review-sherpa",
        "find-bugs",
        "sherpa",
        "write-design",
        "write-plan",
        "write-spec",
        "write-tests",
    ]


def test_every_project_skill_names_itself_after_its_folder() -> None:
    for folder in project_skills():
        text = (folder / "SKILL.md").read_text(encoding="utf-8")
        assert text.startswith(f"---\nname: {folder.name}\ndescription:"), folder.name


def test_every_project_skill_link_resolves() -> None:
    for folder in project_skills():
        text = (folder / "SKILL.md").read_text(encoding="utf-8")
        links = re.findall(r"\]\(([^)#:]+)\)", text)
        assert [link for link in links if not (folder / link).is_file()] == [], folder.name


def test_every_project_skill_file_is_linked_from_its_skill() -> None:
    # A guide or template that SKILL.md does not link is never read.
    for folder in project_skills():
        text = (folder / "SKILL.md").read_text(encoding="utf-8")
        files = [p.relative_to(folder).as_posix() for p in folder.rglob("*") if p.is_file()]
        assert [f for f in files if f != "SKILL.md" and f"]({f})" not in text] == [], folder.name


def test_the_workflow_and_the_skills_hand_off_to_each_other() -> None:
    docs = bi.assets_dir() / "docs"
    skills = bi.assets_dir() / ".claude" / "skills"
    workflow = (docs / "workflow.md").read_text(encoding="utf-8")
    assert "/write-spec" in workflow
    assert "/write-design" in workflow
    assert "/write-design" in (skills / "write-spec" / "SKILL.md").read_text(encoding="utf-8")
    assert "/write-spec" in (skills / "write-design" / "SKILL.md").read_text(encoding="utf-8")


def test_no_asset_mentions_the_inbox() -> None:
    # The inbox was replaced by /write-spec.
    sources = [bi.assets_dir() / "CLAUDE_GOLDEN.md", *(bi.assets_dir() / "docs").glob("*.md")]
    assert [p.name for p in sources if "inbox" in p.read_text(encoding="utf-8")] == []


def test_the_plan_skill_follows_the_design_skill() -> None:
    skills = bi.assets_dir() / ".claude" / "skills"
    workflow = (bi.assets_dir() / "docs" / "workflow.md").read_text(encoding="utf-8")
    assert "/write-plan" in workflow
    assert "/write-plan" in (skills / "write-design" / "SKILL.md").read_text(encoding="utf-8")
    plan_skill = (skills / "write-plan" / "SKILL.md").read_text(encoding="utf-8")
    assert "/write-spec" in plan_skill
    assert "/write-design" in plan_skill


def skill_text(name: str) -> str:
    """Return the SKILL.md of one project skill."""
    path = bi.assets_dir() / ".claude" / "skills" / name / "SKILL.md"
    return path.read_text(encoding="utf-8")


def workflow_text() -> str:
    """Return the workflow that new projects get."""
    return (bi.assets_dir() / "docs" / "workflow.md").read_text(encoding="utf-8")


def test_sherpa_is_the_way_in_and_routes_to_every_other_skill() -> None:
    assert "`/sherpa` is the way in" in workflow_text()
    skills = (
        "/write-spec",
        "/write-design",
        "/write-plan",
        "/write-tests",
        "/code-review-sherpa",
        "/find-bugs",
    )
    for skill in skills:
        assert skill in skill_text("sherpa"), skill
    assert "scripts/milestones-runner.py" in skill_text("sherpa")
    assert "scripts/release.py" in skill_text("sherpa")


def workflow_page() -> str:
    """Return the page that shows the workflow as a diagram (docs/workflow.html)."""
    return (bi.assets_dir() / "docs" / "workflow.html").read_text(encoding="utf-8")


def test_the_workflow_page_names_every_skill_and_script_of_the_workflow() -> None:
    # The page is a picture of docs/workflow.md. A skill or a script that the workflow gains
    # must reach the page in the same change.
    skills = [f"/{folder.name}" for folder in project_skills()]
    scripts = sorted(set(re.findall(r"scripts/[\w-]+\.py", workflow_text())))
    assert scripts != []
    assert [name for name in [*skills, *scripts] if name not in workflow_page()] == []


def test_the_workflow_page_carries_the_hash_of_the_workflow() -> None:
    # The stamp is the SHA-256 of docs/workflow.md when the page was last made to agree with it.
    # A change to the workflow fails here until someone reads the page, corrects it, and writes
    # the new hash. The text is hashed with LF line endings, so the hash is the same on Windows.
    current = hashlib.sha256(workflow_text().encode("utf-8")).hexdigest()
    stamp = re.search(r'<meta name="workflow-md-sha256" content="([0-9a-f]{64})">', workflow_page())
    assert stamp is not None, "assets/docs/workflow.html has no workflow-md-sha256 stamp."
    assert stamp.group(1) == current, (
        "assets/docs/workflow.md changed. Read assets/docs/workflow.html, correct what the change "
        f"made wrong, then set its workflow-md-sha256 stamp to {current}"
    )


def test_every_card_of_the_workflow_page_has_its_panel() -> None:
    # A card opens the panel whose key is its data-step; a card without one opens nothing.
    page = workflow_page()
    cards = re.findall(r'data-step="([a-z]+)"', page)
    panels = re.findall(r"^    ([a-z]+): \{$", page, flags=re.MULTILINE)
    assert cards != []
    assert sorted(cards) == sorted(panels)


def test_a_milestone_has_a_test_a_build_and_a_review_session() -> None:
    workflow = workflow_text()
    assert "**Test session** (`/write-tests`)" in workflow
    assert "**Build session:**" in workflow
    assert "**Review session** (`/code-review-sherpa`)" in workflow
    assert "Do not change, create or delete a file" in skill_text("code-review-sherpa")
    assert "Do not change a file in `tests/`" in workflow
    assert "Do not read the code in `src/`" in skill_text("write-tests")
    assert "/write-tests" in skill_text("write-plan")
    assert "/write-tests" in skill_text("write-spec")
    assert "/write-tests" in skill_text("write-design")


def test_the_templates_of_the_skills_are_the_templates_of_the_docs() -> None:
    # The copies drifted apart once: the design template had no table of module boundaries.
    fills = {
        "{{PROJECT_NAME}}": "<project name>",
        "{{PURPOSE}}": "<purpose>",
        "{{STACK}}": "<stack>",
        "{{DIRECTORY_STRUCTURE}}": "<directory structure>",
    }
    skills = bi.assets_dir() / ".claude" / "skills"
    pairs = {
        "spec.md": skills / "write-spec" / "assets" / "spec-template.md",
        "design.md": skills / "write-design" / "assets" / "design-template.md",
    }
    for doc, template in pairs.items():
        text = (bi.assets_dir() / "docs" / doc).read_text(encoding="utf-8")
        for placeholder, value in fills.items():
            text = text.replace(placeholder, value)
        assert template.read_text(encoding="utf-8") == text, doc


def test_the_spec_has_a_glossary_and_the_design_a_data_model() -> None:
    spec = (bi.assets_dir() / "docs" / "spec.md").read_text(encoding="utf-8")
    design = (bi.assets_dir() / "docs" / "design.md").read_text(encoding="utf-8")
    assert "| Term | Meaning | Avoid |" in spec
    assert "erDiagram" in design
    assert "glossary" in skill_text("write-spec")
    assert "erDiagram" in skill_text("write-design")


def test_the_test_session_tests_the_limits_and_the_defaults() -> None:
    # In the trial of three test writers, two of them wrote only the planned examples (RUN-07).
    text = skill_text("write-tests")
    for case in ("each limit", "one value on each side", "each default", "each invalid input"):
        assert case in text, case


def test_find_bugs_changes_no_code_and_plans_each_bug() -> None:
    text = skill_text("find-bugs")
    for part in (
        "Change no code and\nno test",
        "since that tag",
        "--cov-report=term-missing",
        "pip-audit",
        "npm audit",
        "surviving mutants",
        "`BUG: <requirement ID> | <file>:<line>",
        "by the rules of `/write-plan`",
        "Do not plan\n  it.",
    ):
        assert part in text, part


def test_a_rule_for_all_inputs_gets_a_property_test_and_mutants_run_on_demand() -> None:
    assert "@settings(max_examples=50)" in skill_text("write-tests")
    workflow = (bi.assets_dir() / ".github" / "workflows" / "mutation.yml").read_text("utf-8")
    assert "workflow_dispatch:" in workflow
    assert "runs-on: ubuntu-latest" in workflow
    assert "mutmut" in workflow
    assert "@stryker-mutator/core" in workflow
    assert "name: mutants" in workflow
    assert ".github/workflows/mutation.yml" in bi.template_files()["python"]


def test_each_module_names_what_its_tests_prove() -> None:
    sections = {s.section_id: s for s in bi.read_sections(bi.assets_dir() / "CLAUDE_GOLDEN.md")}
    for section_id in ("B8", "B6", "B5", "B4", "B3", "A18", "A14"):
        assert any(line.startswith("- Tests prove:") for line in sections[section_id].body), (
            section_id
        )
    assert '"Tests prove"' in skill_text("write-design")


def test_the_test_levels_are_the_same_everywhere() -> None:
    # The design gives each requirement a level, the plan groups the test names by it, and the
    # test session writes each test in that level's folder.
    levels = ("unit:", "e2e:", "ui:", "live:")
    sources = {
        "workflow": workflow_text(),
        "write-plan": skill_text("write-plan"),
        "write-tests": skill_text("write-tests"),
    }
    assert [(name, lv) for name, text in sources.items() for lv in levels if lv not in text] == []
    for level in ("`unit`", "`e2e`", "`ui`", "`live`"):
        assert level in skill_text("write-design"), level


def test_the_review_checks_the_short_list_of_smells_and_no_polymorphism() -> None:
    # The user chose 8 smells and banned one refactoring. The checklist is the only place
    # that holds them, and only the review session loads it.
    folder = bi.assets_dir() / ".claude" / "skills" / "code-review-sherpa"
    checklist = (folder / "references" / "checklist.md").read_text(encoding="utf-8")
    smells = (
        "Speculative Generality",
        "Duplicate Code",
        "Dead Code",
        "Middle Man and Lazy Class",
        "Comments",
        "Long Method",
        "Long Parameter List",
        "Large Class",
    )
    assert [smell for smell in smells if f"| {smell} |" not in checklist] == []
    assert checklist.count("\n| ") == len(smells) + 2  # the header, its rule, and 8 rows
    assert 'Never propose "Replace Conditional with Polymorphism"' in checklist
    assert "FINDING: <high|medium|low> | <file>:<line> | <rule or smell> | <remedy>" in skill_text(
        "code-review-sherpa"
    )
    assert "`FINDING: <high, medium or low> | <file>:<line> | <rule or smell> | <remedy>`" in (
        workflow_text()
    )


def test_the_plan_table_has_the_human_test_column() -> None:
    # The runner reads six cells of a row, and the user sees the stops when approving the table.
    header = "| Milestone | Description | Model | Effort | Human test | Status |"
    assert header in (bi.assets_dir() / "docs" / "plan.md").read_text(encoding="utf-8")
    cells = ("**M<n>** <title>", "<one line: what it delivers>", "<model>", "<effort>")
    row = "| " + " | ".join((*cells, "<yes or no>", "open")) + " |"
    assert row in workflow_text()
    assert "- **Human test:**" in workflow_text()
    assert "**Human test**" in skill_text("write-plan")


def test_the_workflow_page_holds_the_philosophy() -> None:
    page = workflow_page()
    lead = "The human decides what to build. The AI builds it. The checks decide when it is done."
    assert lead in page
    principles = ("Intent", "Method", "Proof", "Independence", "Autonomy", "Cost", "Scope")
    assert [name for name in principles if f"<dt>{name}</dt>" not in page] == []


def test_the_design_records_who_decided() -> None:
    # /sherpa and /write-plan read the design as approved when no decision is Proposed.
    design = (bi.assets_dir() / "docs" / "design.md").read_text(encoding="utf-8")
    assert "| ID | Status | Decision | Why |" in design
    assert "## 6. Open design questions" in design
    for text in (workflow_text(), skill_text("sherpa"), skill_text("write-plan")):
        assert "`Proposed`" in text
    for status in ("`Decided`", "`Proposed`", "`Superseded`"):
        assert status in skill_text("write-design"), status


def test_unapproved_ideas_are_never_built_from() -> None:
    ideas = (bi.assets_dir() / "docs" / "unapproved-ideas.md").read_text(encoding="utf-8")
    assert "never\ndesign, plan, test or build from this file" in ideas
    assert "Never design, plan, test or build from it." in workflow_text()
    for skill in ("sherpa", "write-spec", "write-design", "write-plan"):
        assert "docs/unapproved-ideas.md" in skill_text(skill), skill
    # The file is for the user and for /sherpa; the sessions of a milestone never read it.
    runner = (bi.assets_dir() / "scripts" / "milestones-runner.py").read_text(encoding="utf-8")
    assert "unapproved-ideas" not in runner
    assert "unapproved-ideas" not in skill_text("write-tests")


def test_no_asset_keeps_the_wording_of_another_project() -> None:
    # The workflow, the skills and the scripts are the same in every project. These words came
    # from one project that used them, and must not come back with a later merge.
    # Its two-digit IDs (FR-NN, AC-NN, D-NN) are not part of NFR-NNN or DEC-NNN.
    words = re.compile(
        r"specs\.md|docs/ui|Ollama|embedding|design-kb|(?<![A-Z])(?:FR|AC|D)-NN(?!N)"
    )
    assets = bi.assets_dir()
    sources = [*(assets / "docs").glob("*.md"), *(assets / ".claude" / "skills").rglob("*.md")]
    sources += [*(assets / "scripts").glob("*.py"), assets / "CLAUDE_GOLDEN.md"]
    found = {p.name: words.findall(p.read_text(encoding="utf-8")) for p in sources}
    assert {name: hits for name, hits in found.items() if hits} == {}


def test_the_skills_show_the_module_table_of_the_builder() -> None:
    # One owner for the table of the modules: build_instance.py --list-modules (USER-19).
    assert "--list-modules" in skill_text("write-design")
    assert "--add <module>" in skill_text("write-design")
    project_init = (bi.assets_dir().parent / "SKILL.md").read_text(encoding="utf-8")
    assert "--list-modules" in project_init
    assert "| `python` |" not in project_init


def test_the_docs_of_a_new_project_are_plain_english(tmp_path: Path) -> None:
    # USER-20: the same lint that check.py runs in a project, on the templates of every module.
    project = tmp_path / "full"
    result = build(project, "--with", *sorted(bi.optional_flags()), "--purpose", "Tests all")
    assert result.returncode == 0, result.stderr
    names = ["README.md", "CLAUDE.md", *sorted(f"docs/{p.name}" for p in project.glob("docs/*.md"))]
    script = bi.assets_dir() / "scripts" / "ste_lint.py"
    options = ["--fail-over", "2.5", "--min-words", "100", "--repeated", "12"]
    done = run([sys.executable, str(script), *options, *names], project)
    assert done.returncode == 0, done.stdout


def test_each_push_installs_the_project_on_a_clean_machine() -> None:
    # Rank 14: a dependency that is only on the developer's machine fails at the next push.
    workflow = (bi.assets_dir() / ".github" / "workflows" / "check.yml").read_text("utf-8")
    assert "on:\n  push:" in workflow
    assert "pip install -r requirements.txt" in workflow
    assert "npm ci" in workflow
    assert "playwright install" in workflow
    assert workflow.rstrip().endswith("run: python scripts/check.py")
    assert ".github/workflows/check.yml" in bi.template_files()["always"]
