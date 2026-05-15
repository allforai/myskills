import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../scripts/orchestrator"))
from check_artifacts import check_node_artifacts


def _make_node(artifacts):
    return {"node_id": "test-node", "goal": "test", "exit_artifacts": artifacts}


def test_string_artifact_exists(tmp_path):
    f = tmp_path / "out.json"
    f.write_text('{"status": "passed"}')
    result = check_node_artifacts(_make_node([str(f)]))
    assert result["all_exist"] is True
    assert result["node_id"] == "test-node"
    assert len(result["artifacts"]) == 1


def test_node_id_required():
    try:
        check_node_artifacts({"goal": "test", "exit_artifacts": []})
    except ValueError as exc:
        assert "node_id" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_string_artifact_missing(tmp_path):
    result = check_node_artifacts(_make_node([str(tmp_path / "missing.json")]))
    assert result["all_exist"] is False


def test_dict_artifact_exists_no_commands(tmp_path):
    f = tmp_path / "out.json"
    f.write_text('{"status": "passed"}')
    result = check_node_artifacts(_make_node([{"path": str(f), "validation_commands": []}]))
    assert result["all_exist"] is True


def test_dict_artifact_validation_command_passes(tmp_path):
    f = tmp_path / "out.json"
    f.write_text('{"status": "final"}')
    result = check_node_artifacts(_make_node([{
        "path": str(f),
        "validation_commands": [f'python3 -c "import json; json.load(open(\\"{f}\\"))"']
    }]))
    assert result["all_exist"] is True
    assert "validation_error" not in result["artifacts"][0]


def test_dict_artifact_validation_command_fails(tmp_path):
    """File exists but validation command exits non-zero → all_exist must be False."""
    f = tmp_path / "bad.json"
    f.write_text("not json")
    result = check_node_artifacts(_make_node([{
        "path": str(f),
        "validation_commands": [f'python3 -c "import json,sys; json.load(open(sys.argv[1]))" {f}']
    }]))
    assert result["all_exist"] is False
    assert "validation_error" in result["artifacts"][0]


def test_false_command_fails(tmp_path):
    """Using `false` as command (always exits 1) → all_exist must be False."""
    f = tmp_path / "file.txt"
    f.write_text("content")
    result = check_node_artifacts(_make_node([{
        "path": str(f),
        "validation_commands": ["false"]
    }]))
    assert result["all_exist"] is False
    assert "validation_error" in result["artifacts"][0]


def test_blocked_status_artifact_is_not_complete(tmp_path):
    f = tmp_path / "qa.json"
    f.write_text('{"qa_status":"blocked"}')

    result = check_node_artifacts(_make_node([str(f)]))

    assert result["all_exist"] is False
    assert result["artifacts"][0]["status_error"]["field"] == "qa_status"


def test_conditional_pass_status_artifact_is_not_complete(tmp_path):
    f = tmp_path / "qa.json"
    f.write_text('{"overall_status":"conditional_pass"}')

    result = check_node_artifacts(_make_node([str(f)]))

    assert result["all_exist"] is False
    assert result["artifacts"][0]["status_error"]["field"] == "overall_status"


def test_blocked_by_status_artifact_is_not_complete(tmp_path):
    f = tmp_path / "qa.json"
    f.write_text('{"status":"blocked_by_missing_runtime_probe"}')

    result = check_node_artifacts(_make_node([str(f)]))

    assert result["all_exist"] is False
    assert result["artifacts"][0]["status_error"]["field"] == "status"


def test_empty_json_artifact_is_not_complete(tmp_path):
    f = tmp_path / "qa.json"
    f.write_text("{}")

    result = check_node_artifacts(_make_node([str(f)]))

    assert result["all_exist"] is False
    assert result["artifacts"][0]["status_error"]["field"] == "$"


def test_completed_status_artifact_is_complete(tmp_path):
    f = tmp_path / "qa.json"
    f.write_text('{"qa_status":"passed"}')

    result = check_node_artifacts(_make_node([str(f)]))

    assert result["all_exist"] is True


def test_asset_gap_with_placeholder_terms_is_not_complete(tmp_path):
    f = tmp_path / "qa.json"
    f.write_text('{"asset_gaps":[{"severity":"minor","notes":"VFX frames missing; tween fallback active"}]}')

    result = check_node_artifacts(_make_node([str(f)]))

    assert result["all_exist"] is False
    assert result["artifacts"][0]["status_error"]["field"] == "asset_gaps"


def test_remaining_gap_without_forbidden_terms_is_not_complete(tmp_path):
    f = tmp_path / "qa.json"
    f.write_text('{"remaining_gaps":[{"id":"audio-meta","notes":"音频 .meta 缺失，需要继续处理"}]}')

    result = check_node_artifacts(_make_node([str(f)]))

    assert result["all_exist"] is False
    assert result["artifacts"][0]["status_error"]["field"] == "remaining_gaps"


def test_visual_blocker_with_prototype_renderer_is_not_complete(tmp_path):
    f = tmp_path / "qa.json"
    f.write_text(
        '{"major_findings":[{"severity":"blocker","notes":"PrototypeBoard renders pure-color Graphics tiles"}]}'
    )

    result = check_node_artifacts(_make_node([str(f)]))

    assert result["all_exist"] is False
    assert result["artifacts"][0]["status_error"]["field"] == "major_findings"


def test_runtime_qa_artifact_is_stale_after_source_change(tmp_path):
    report = tmp_path / ".allforai/game-2d/qa/asset-binding-visual-qa-report.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text('{"status": "passed"}')
    time.sleep(0.01)
    source = tmp_path / "game-client/assets/scripts/GameScene.ts"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("export const changed = true;")

    result = check_node_artifacts(_make_node([".allforai/game-2d/qa/asset-binding-visual-qa-report.json"]), tmp_path)

    assert result["all_exist"] is False
    assert result["artifacts"][0]["status_error"]["field"] == "$mtime"


def test_explicit_production_policy_does_not_make_asset_gap_complete(tmp_path):
    f = tmp_path / "qa.json"
    f.write_text(
        '{"production_acceptance_policy":{"allow_placeholder_or_fallback_assets":true},'
        '"asset_gaps":[{"severity":"minor","notes":"placeholder art explicitly accepted for prototype"}]}'
    )

    result = check_node_artifacts(_make_node([str(f)]))

    assert result["all_exist"] is False
    assert result["artifacts"][0]["status_error"]["field"] == "asset_gaps"
