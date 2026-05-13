import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../scripts/orchestrator"))
from analyze_skill_update_impact import analyze, write_reports


def _write(root, rel, text):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def test_analyze_skill_update_impact_matches_explicit_skill_ref(tmp_path):
    repo = tmp_path / "repo"
    project = tmp_path / "project"
    _write(repo, "claude/meta-skill/SKILL.md", '---\nversion: "0.9.0"\n---\n')
    _write(
        project,
        ".allforai/bootstrap/workflow.json",
        json.dumps({
            "nodes": [
                {
                    "node_id": "art-qa",
                    "capability": "game-art",
                    "exit_artifacts": [".allforai/game-design/art/qa/report.json"],
                },
                {
                    "node_id": "compile-verify",
                    "capability": "compile-verify",
                    "exit_artifacts": [".allforai/verify/compile.json"],
                },
            ]
        }),
    )
    _write(
        project,
        ".allforai/bootstrap/node-specs/art-qa.md",
        "${CLAUDE_PLUGIN_ROOT}/skills/game-art/40-qa/visual-acceptance-review/SKILL.md\n",
    )
    _write(project, ".allforai/bootstrap/node-specs/compile-verify.md", "compile only\n")

    result = analyze(
        str(repo),
        str(project),
        changed_file=["claude/meta-skill/skills/game-art/40-qa/visual-acceptance-review/SKILL.md"],
    )

    assert result["state"] == "completed"
    assert result["meta_skill_version"] == "0.9.0"
    node_ids = [item["node_id"] for item in result["node_recommendations"]]
    assert "art-qa" in node_ids
    assert "compile-verify" not in node_ids
    art = next(item for item in result["node_recommendations"] if item["node_id"] == "art-qa")
    assert art["severity"] == "high"


def test_analyze_skill_update_impact_writes_reports(tmp_path):
    repo = tmp_path / "repo"
    project = tmp_path / "project"
    _write(repo, "claude/meta-skill/SKILL.md", 'version: "1.2.3"\n')
    _write(project, ".allforai/bootstrap/workflow.json", '{"nodes":[]}')

    result = analyze(
        str(repo),
        str(project),
        changed_file=["claude/meta-skill/skills/bootstrap.md"],
    )
    json_path, md_path = write_reports(result, str(project / ".allforai/setup"))

    assert json_path.exists()
    assert md_path.exists()
    data = json.loads(json_path.read_text())
    assert data["meta_skill_version"] == "1.2.3"
    assert "rerun /bootstrap" in md_path.read_text()


def test_analyze_skill_update_impact_needs_change_input_without_ref_or_files(tmp_path):
    repo = tmp_path / "repo"
    project = tmp_path / "project"
    _write(repo, "claude/meta-skill/SKILL.md", 'version: "1.0.0"\n')
    result = analyze(str(repo), str(project))

    assert result["state"] == "needs_change_input"
    assert result["changed_files"] == []
    assert result["global_recommendations"][0]["scope"] == "unknown"
