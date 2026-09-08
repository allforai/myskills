"""The diagnostic CLI does not invent provenance for never-observed legacy work."""
import json

import pytest

from .test_evidence_freshness import setup, invoke, write, WORKFLOW


@pytest.mark.parametrize('host', ['claude', 'codex'])
def test_unobserved_legacy_diagnostic_is_undeclared_not_verified(tmp_path, host):
    setup(tmp_path, host)
    workflow = json.loads((tmp_path / WORKFLOW).read_text())
    workflow['nodes'].append({'node_id': 'historical', 'exit_artifacts': ['old-report.json']})
    workflow['transition_log'].append({'node_id': 'historical', 'status': 'completed'})
    write(tmp_path, WORKFLOW, workflow)
    write(tmp_path, 'old-report.json', {'status': 'passed'})
    result, checked = invoke(tmp_path, 'check')
    assert result.returncode == 0, checked
    assert checked['nodes']['historical']['status'] == 'undeclared'
    assert checked['nodes']['historical']['readiness_status'] == 'undeclared'
    assert checked['nodes']['deliver-export']['status'] == 'stale'
