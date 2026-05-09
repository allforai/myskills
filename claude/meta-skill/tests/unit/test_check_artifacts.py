import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../scripts/orchestrator"))
from check_artifacts import check_node_artifacts


def _make_node(artifacts):
    return {"id": "test-node", "goal": "test", "exit_artifacts": artifacts}


def test_string_artifact_exists(tmp_path):
    f = tmp_path / "out.json"
    f.write_text("{}")
    result = check_node_artifacts(_make_node([str(f)]))
    assert result["all_exist"] is True
    assert len(result["artifacts"]) == 1


def test_string_artifact_missing(tmp_path):
    result = check_node_artifacts(_make_node([str(tmp_path / "missing.json")]))
    assert result["all_exist"] is False


def test_dict_artifact_exists_no_commands(tmp_path):
    f = tmp_path / "out.json"
    f.write_text("{}")
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
