import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../scripts/orchestrator"))
from validate_game_2d_production_pipeline import (
    CHILD_REFS,
    REQUIRED_BOOTSTRAP_TERMS,
    REQUIRED_CLOSURE_TERMS,
    REQUIRED_GAME_DESIGN_TERMS,
    REQUIRED_GAME_PRODUCTION_TERMS,
    REQUIRED_PARENT_TERMS,
    validate_game_2d_production_pipeline,
)


def _write(root, rel, text):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def _minimal_repo(tmp_path):
    parent = "\n".join(
        f"${{CLAUDE_PLUGIN_ROOT}}/skills/game-2d-production/{ref}/SKILL.md"
        for ref in CHILD_REFS
    )
    parent += "\n" + "\n".join(sorted(REQUIRED_PARENT_TERMS))
    _write(tmp_path, "claude/meta-skill/skills/game-2d-production/SKILL.md", parent)

    for ref in CHILD_REFS:
        text = "---\nname: x\ndescription: x\n---\n"
        if ref == "40-qa/2d-production-closure-qa":
            text += "\n".join(sorted(REQUIRED_CLOSURE_TERMS))
        _write(tmp_path, f"claude/meta-skill/skills/game-2d-production/{ref}/SKILL.md", text)

    _write(
        tmp_path,
        "claude/meta-skill/knowledge/capabilities/game-design.md",
        "\n".join(sorted(REQUIRED_GAME_DESIGN_TERMS)),
    )
    _write(
        tmp_path,
        "claude/meta-skill/skills/bootstrap.md",
        "\n".join(sorted(REQUIRED_BOOTSTRAP_TERMS)),
    )
    _write(
        tmp_path,
        "claude/meta-skill/skills/game-production/SKILL.md",
        "\n".join(sorted(REQUIRED_GAME_PRODUCTION_TERMS)),
    )


def test_validate_game_2d_production_pipeline_accepts_minimal_graph(tmp_path):
    _minimal_repo(tmp_path)

    assert validate_game_2d_production_pipeline(str(tmp_path)) == []


def test_validate_game_2d_production_pipeline_rejects_unlisted_child(tmp_path):
    _minimal_repo(tmp_path)
    _write(
        tmp_path,
        "claude/meta-skill/skills/game-2d-production/40-qa/unlisted/SKILL.md",
        "---\nname: y\ndescription: y\n---\n",
    )

    errors = validate_game_2d_production_pipeline(str(tmp_path))

    assert any("missing canonical child path" in error for error in errors)
