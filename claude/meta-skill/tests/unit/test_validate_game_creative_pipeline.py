import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../scripts/orchestrator"))
from validate_game_creative_pipeline import validate_game_creative_pipeline


def _write(root, rel, text):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def _minimal_repo(tmp_path):
    _write(
        tmp_path,
        "claude/meta-skill/skills/game-creative/SKILL.md",
        """${CLAUDE_PLUGIN_ROOT}/skills/game-creative/40-qa/creative-quality-critique/SKILL.md
creative-quality-critique
contract_defect
evidence_based_critique
llm_judgment
insufficient_evidence
.allforai/game-creative/
""",
    )
    _write(
        tmp_path,
        "claude/meta-skill/skills/game-creative/40-qa/creative-quality-critique/SKILL.md",
        """.allforai/game-creative/creative-quality-critique.json
.allforai/game-creative/creative-quality-critique.html
hook_score
coherence_score
novelty_score
readability_score
emotional_curve_score
production_fit_score
market_fit_score
audiovisual_sync_score
frontend_experience_score
contract_defect
evidence_based_critique
llm_judgment
insufficient_evidence
must_fix_before_art_gen
must_fix_before_frontend
must_fix_before_release
recommended_iterations
review_language
zh-CN
repair_route
counterexample_or_comparison
""",
    )


def test_validate_game_creative_pipeline_accepts_minimal_graph(tmp_path):
    _minimal_repo(tmp_path)

    assert validate_game_creative_pipeline(str(tmp_path)) == []


def test_validate_game_creative_pipeline_rejects_unlisted_child(tmp_path):
    _minimal_repo(tmp_path)
    _write(
        tmp_path,
        "claude/meta-skill/skills/game-creative/40-qa/new-critique/SKILL.md",
        "---\nname: y\ndescription: y\n---\n",
    )

    errors = validate_game_creative_pipeline(str(tmp_path))

    assert any("missing canonical child path" in error for error in errors)
