import os
import sys
import time
import pytest

from ..module_isolation import load

check_node_artifacts = load("check_artifacts").check_node_artifacts


@pytest.mark.parametrize('content', ['{broken', '', 'NaN invalid'])
def test_invalid_json_without_validator_rejected(tmp_path, content):
    path = tmp_path / 'report.json'
    path.write_text(content)
    assert not check_node_artifacts(_make_node([str(path)]))['all_exist']


def test_empty_artifact_list_and_directory_rejected(tmp_path):
    assert not check_node_artifacts(_make_node([]))['all_exist']
    assert not check_node_artifacts(_make_node([str(tmp_path)]))['all_exist']


@pytest.mark.parametrize('content,passed', [('{"status":"passed","evidence":[]}', True),
    ('{"status":"unknown","evidence":[]}', False), ('{"status":"passed"}', False), ('[]', False)])
def test_explicit_report_contract(tmp_path, content, passed):
    path = tmp_path / 'report.json'
    path.write_text(content)
    item = {'path':str(path), 'required_fields':['status','evidence'], 'accepted_statuses':['passed']}
    assert check_node_artifacts(_make_node([item]))['all_exist'] is passed


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


def test_existence_only_quality_status_is_not_complete(tmp_path):
    f = tmp_path / "qa.json"
    f.write_text('{"quality_status":"existence_only"}')

    result = check_node_artifacts(_make_node([str(f)]))

    assert result["all_exist"] is False
    assert result["artifacts"][0]["status_error"]["field"] == "quality_status"


@pytest.mark.parametrize("field", ["quality_gaps", "effect_gaps", "experience_gaps",
                                   "visual_quality_gaps", "perceptual_gaps"])
def test_a_bare_finding_id_in_a_quality_gate_still_blocks(tmp_path, field):
    # The template says a non-empty quality gate blocks completion; the gate must not
    # depend on the entry happening to contain placeholder/fallback wording.
    f = tmp_path / "report.json"
    f.write_text('{"status":"passed","' + field + '":[{"id":"experience-002"}]}')
    result = check_node_artifacts(_make_node([str(f)]))
    assert result["all_exist"] is False
    assert result["artifacts"][0]["status_error"]["field"] == field


def test_quality_gaps_are_not_complete(tmp_path):
    f = tmp_path / "qa.json"
    f.write_text('{"status":"passed","quality_gaps":[{"notes":"structure only; does not match concept"}]}')

    result = check_node_artifacts(_make_node([str(f)]))

    assert result["all_exist"] is False
    assert result["artifacts"][0]["status_error"]["field"] == "quality_gaps"


def test_must_fix_before_implementation_in_gates_is_not_complete(tmp_path):
    f = tmp_path / "experience-quality-critique-design.json"
    f.write_text('{"status":"passed","gates":{"must_fix_before_implementation":[{"id":"F1","finding":"主流程缺少空状态"}]}}')

    result = check_node_artifacts(_make_node([str(f)]))

    assert result["all_exist"] is False
    assert result["artifacts"][0]["status_error"]["field"] == "must_fix_before_implementation"


def test_must_fix_before_release_in_gates_is_not_complete(tmp_path):
    f = tmp_path / "creative-quality-critique.json"
    f.write_text('{"status":"passed","gates":{"must_fix_before_release":[{"id":"F2","finding":"反馈音效缺失"}]}}')

    result = check_node_artifacts(_make_node([str(f)]))

    assert result["all_exist"] is False
    assert result["artifacts"][0]["status_error"]["field"] == "must_fix_before_release"


@pytest.mark.parametrize("field", ["must_fix_before_implementation", "must_fix_before_release"])
def test_top_level_must_fix_is_not_complete(tmp_path, field):
    f = tmp_path / "experience-quality-critique-runtime.json"
    f.write_text('{"status":"passed","%s":[{"id":"F3","finding":"引导步骤无法回退"}]}' % field)

    result = check_node_artifacts(_make_node([str(f)]))

    assert result["all_exist"] is False
    assert result["artifacts"][0]["status_error"]["field"] == field


def test_empty_must_fix_gates_are_complete(tmp_path):
    f = tmp_path / "experience-quality-critique-design.json"
    f.write_text(
        '{"status":"passed","gates":{"must_fix_before_implementation":[],"must_fix_before_release":[],'
        '"recommended_iterations":[{"id":"R1","finding":"可以再收紧标题层级"}]}}'
    )

    result = check_node_artifacts(_make_node([str(f)]))

    assert result["all_exist"] is True
    assert result["artifacts"][0].get("status_error") is None


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


@pytest.mark.parametrize('scopes', [[], None, 'a/**', ['../a'], ['.allforai'], ['b/**']])
def test_parallel_write_contract_invalid_blocks_admission(scopes):
    checker = load("check_artifacts")
    node = {'source_inputs': ['package.json'], 'exit_artifacts': ['a/report.json'],
            'parallel_write_scopes': scopes}
    assert checker.input_declaration_errors(node)


def test_parallel_write_contract_covers_outputs_but_not_shared_reads():
    checker = load("check_artifacts")
    node = {'source_inputs': ['package.json'], 'exit_artifacts': ['a/report.json'],
            'parallel_write_scopes': ['a/**']}
    assert checker.input_declaration_errors(node) == []
    node['required_documents'] = ['docs/a.md']
    assert checker.parallel_write_declaration_errors(node)
    node['parallel_write_scopes'].append('docs/a.md')
    assert checker.parallel_write_declaration_errors(node) == []
