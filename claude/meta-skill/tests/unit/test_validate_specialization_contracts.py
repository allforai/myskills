import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../scripts/orchestrator"))
from validate_specialization_contracts import REQUIRED_SECTIONS, validate_specialization_contracts


def _write(root, rel, text):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def _required_section_refs():
    return "\n".join(f"`{section}`" for section in sorted(REQUIRED_SECTIONS))


def _required_headings():
    return "\n".join(f"## {section}\ncontent\n" for section in sorted(REQUIRED_SECTIONS))


def _minimal_repo(tmp_path):
    required_refs = _required_section_refs()
    _write(
        tmp_path,
        "claude/meta-skill/skills/bootstrap.md",
        f"""Read knowledge/domains/game-genre-specialization.md.
Write project-local skills under .allforai/bootstrap/specialized-skills/.
Each generated specialized skill must include:
{required_refs}
""",
    )
    _write(
        tmp_path,
        "claude/meta-skill/knowledge/capabilities/game-design.md",
        """Use game-genre-specialization.md for project-local specialization.
Project-local output root: .allforai/bootstrap/specialized-skills/.

## Sub-Skill Mapping
| Node | Child Skill |
| --- | --- |
| level-design | game-design/30-content/level-design |

**Path validation:**
Validate bundled child skill paths only.
""",
    )
    _write(
        tmp_path,
        "claude/meta-skill/knowledge/domains/game-genre-specialization.md",
        f"""Project-local output root: .allforai/bootstrap/specialized-skills/.
{required_refs}
""",
    )
    _write(
        tmp_path,
        "claude/meta-skill/skills/game-art/SKILL.md",
        "---\nname: game-art\ndescription: x\n---\n",
    )


def test_validate_specialization_contracts_accepts_minimal_governance(tmp_path):
    _minimal_repo(tmp_path)

    assert validate_specialization_contracts(str(tmp_path)) == []


def test_validate_specialization_contracts_rejects_project_root_in_mapping(tmp_path):
    _minimal_repo(tmp_path)
    _write(
        tmp_path,
        "claude/meta-skill/knowledge/capabilities/game-design.md",
        """Use game-genre-specialization.md.
Project-local output root: .allforai/bootstrap/specialized-skills/.

## Sub-Skill Mapping
| Node | Child Skill |
| --- | --- |
| lianliankan-level-design | `.allforai/bootstrap/specialized-skills/lianliankan-level/SKILL.md` |

**Path validation:**
Validate bundled child skill paths only.
""",
    )

    errors = validate_specialization_contracts(str(tmp_path))

    assert any("Sub-Skill Mapping must not reference project-local specialized skills" in e for e in errors)


def test_validate_specialization_contracts_rejects_genre_tight_global_skill_name(tmp_path):
    _minimal_repo(tmp_path)
    _write(
        tmp_path,
        "claude/meta-skill/skills/game-design/30-content/lianliankan-level-solver/SKILL.md",
        "---\nname: lianliankan-level-solver\ndescription: x\n---\n",
    )

    errors = validate_specialization_contracts(str(tmp_path))

    assert any("genre-tight skill name belongs in project-local specialized-skills" in e for e in errors)


def test_validate_specialization_contracts_does_not_match_genre_term_substring(tmp_path):
    _minimal_repo(tmp_path)
    _write(
        tmp_path,
        "claude/meta-skill/skills/game-liveops/20-spec/monetization-spec/SKILL.md",
        "---\nname: monetization-spec\ndescription: x\n---\n",
    )

    assert validate_specialization_contracts(str(tmp_path)) == []


def test_validate_specialization_contracts_rejects_incomplete_project_specialized_skill(tmp_path):
    _minimal_repo(tmp_path)
    _write(
        tmp_path,
        ".allforai/bootstrap/specialized-skills/lianliankan-level/SKILL.md",
        _required_headings().replace("## Completion Conditions\ncontent\n", ""),
    )

    errors = validate_specialization_contracts(str(tmp_path))

    assert any("missing required section ## Completion Conditions" in e for e in errors)


def test_validate_specialization_contracts_requires_blocked_state_for_executable_validation(tmp_path):
    _minimal_repo(tmp_path)
    _write(
        tmp_path,
        ".allforai/bootstrap/specialized-skills/lianliankan-level/SKILL.md",
        _required_headings() + "\nUse a runtime solver and screenshot validation loop.\n",
    )

    errors = validate_specialization_contracts(str(tmp_path))

    assert any("executable validation mentioned without blocked/failed state" in e for e in errors)


def test_validate_specialization_contracts_accepts_executable_validation_with_blocked_state(tmp_path):
    _minimal_repo(tmp_path)
    _write(
        tmp_path,
        ".allforai/bootstrap/specialized-skills/lianliankan-level/SKILL.md",
        _required_headings() + "\nUse a runtime solver and mark blocked_by_missing_runtime when unavailable.\n",
    )

    assert validate_specialization_contracts(str(tmp_path)) == []
