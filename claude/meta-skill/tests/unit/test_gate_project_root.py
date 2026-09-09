"""Bootstrap CLI admission reads the target project, not its caller's directory."""
import subprocess
import sys

import pytest

from .test_bootstrap_scope import project, write
from .test_freshness_downgrade import _append_node, _complete, OLD_REF


@pytest.mark.parametrize('host', ['claude', 'codex'])
def test_retained_scope_admission_is_independent_of_cli_working_directory(tmp_path, host):
    project(tmp_path, confirmed=True, host=host)
    _append_node(tmp_path, {'node_id': 'historical', 'goal': 'Retain warehouse history',
        'capability': 'implement', 'requirement_refs': [OLD_REF],
        'exit_artifacts': ['.allforai/bootstrap/old-report.json']})
    _complete(tmp_path, 'historical', host)
    write(tmp_path, '.allforai/bootstrap/old-report.json', {'status': 'passed'})
    bootstrap = tmp_path / '.allforai/bootstrap'
    command = [sys.executable, str(bootstrap / 'scripts/validate_bootstrap.py'), str(bootstrap)]
    inside = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True)
    outside = subprocess.run(command, cwd=tmp_path.parent, capture_output=True, text=True)
    assert inside.returncode == 0, inside.stdout
    assert outside.returncode == 0, outside.stdout
    assert not inside.stderr and not outside.stderr
