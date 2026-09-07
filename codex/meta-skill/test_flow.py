"""Driver contract tests: no paid CLI calls and no installed-skill mutations."""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("meta_flow_tests", ROOT / "knowledge/flow-template.py")
flow = importlib.util.module_from_spec(spec)
spec.loader.exec_module(flow)


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


@pytest.mark.parametrize("result", [None, subprocess.CompletedProcess([], 1, '{"all_exist":true}'),
    subprocess.CompletedProcess([], 0, ''), subprocess.CompletedProcess([], 0, 'broken'),
    subprocess.CompletedProcess([], 0, '[]'),
    subprocess.CompletedProcess([], 0, '{"node_id":"n1","all_exist":"false","artifacts":[{}]}'),
    subprocess.CompletedProcess([], 0, '{"node_id":"other","all_exist":true,"artifacts":[{}]}')])
def test_gate_fails_closed(tmp_path, monkeypatch, result):
    monkeypatch.setattr(flow, "run_script", lambda *args: result)
    assert not flow.independent_artifact_gate(tmp_path, "n1")


def test_resume_runs_real_validation_commands(tmp_path):
    scripts = tmp_path / '.allforai/bootstrap/scripts'
    scripts.mkdir(parents=True)
    source = ROOT / '../../claude/meta-skill/scripts/orchestrator/check_artifacts.py'
    (scripts / 'check_artifacts.py').write_bytes(source.read_bytes())
    write(tmp_path / 'report.json', {'status': 'passed'})
    node = {'node_id': 'n1', 'exit_artifacts': [{'path': 'report.json', 'validation_commands': ['exit 1']}]}
    workflow = {'nodes': [node]}
    path = tmp_path / '.allforai/bootstrap/workflow.json'
    write(path, workflow)
    assert flow.first_pending_node(tmp_path, workflow) == node
    node['exit_artifacts'][0]['validation_commands'] = ['exit 0']
    write(path, workflow)
    assert flow.first_pending_node(tmp_path, workflow) is None
    (tmp_path / 'report.json').write_text('{broken')
    assert flow.first_pending_node(tmp_path, workflow) == node


def test_worker_success_cannot_mask_failed_gate(tmp_path):
    path = tmp_path / 'workflow.json'
    write(path, {'transition_log': [{'node':'n1', 'status':'completed'}]})
    flow.append_transition_if_missing(path, 0, 'n1', 'failed', 'now', [], 'gate failed')
    result = flow.load_json(path)
    assert flow.count_consecutive_failures(result, 'n1') == 1
    assert result['transition_log'][0]['error'] == 'gate failed'


def test_missing_preflight_blocks(tmp_path):
    assert flow.run_preflight(tmp_path) == 6


def test_preflight_requires_report(tmp_path, monkeypatch):
    monkeypatch.setattr(flow, 'run_script', lambda *args: subprocess.CompletedProcess([], 0, '', ''))
    assert flow.run_preflight(tmp_path) == 6
    write(tmp_path / '.allforai/bootstrap/unattended-run-readiness.json', {'status':'ready'})
    assert flow.run_preflight(tmp_path) == 0


def test_final_validation_failure_blocks_done(tmp_path, monkeypatch, capsys):
    write(tmp_path / '.allforai/bootstrap/workflow.json', {'nodes':[{'node_id':'n1'}]})
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, 'argv', ['flow.py'])
    monkeypatch.setattr(flow, 'run_preflight', lambda *a: 0)
    monkeypatch.setattr(flow, 'run_expanders', lambda *a: True)
    monkeypatch.setattr(flow, 'first_pending_node', lambda *a: None)
    monkeypatch.setattr(flow, 'run_post_checks', lambda *a: False)
    assert flow.main() == 6
    assert json.loads(capsys.readouterr().err)['done'] is False


def test_post_check_and_expander_missing(tmp_path):
    assert flow.run_post_checks(tmp_path) is False
    assert flow.run_expanders(tmp_path, {'expanders':['missing.py']}) is False
    assert flow.run_expanders(tmp_path, {'expanders':[]}) is True


@pytest.mark.parametrize('returncode', [124, 130])
def test_timeout_or_interrupt_records_failure_and_stops(tmp_path, monkeypatch, returncode):
    import shutil
    scripts = tmp_path / '.allforai/bootstrap/scripts'
    scripts.mkdir(parents=True)
    shutil.copy2(ROOT / '../../claude/meta-skill/scripts/orchestrator/product_intent.py', scripts)
    write(tmp_path / '.allforai/bootstrap/run-policy.json', {
        'on_repeated_failure': 'halt', 'on_needs_iteration': 'halt_with_report', 'on_safety_warning': 'continue'})
    node = {'node_id':'n1', 'exit_artifacts':['report.json']}
    path = tmp_path / '.allforai/bootstrap/workflow.json'
    write(path, {'nodes':[node]})
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, 'argv', ['flow.py'])
    monkeypatch.setattr(flow, 'run_preflight', lambda *a: 0)
    monkeypatch.setattr(flow, 'run_expanders', lambda *a: True)
    monkeypatch.setattr(flow, 'first_pending_node', lambda *a: node)
    calls = []
    def worker(*args):
        calls.append(args)
        return subprocess.CompletedProcess([], returncode, '', 'stopped')
    monkeypatch.setattr(flow, 'run_codex', worker)
    assert flow.main() == returncode
    assert len(calls) == 1
    assert flow.load_json(path)['transition_log'][0]['status'] == 'failed'


def test_codex_defaults_are_bounded(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(flow, 'run_bounded', lambda *args: calls.append(args))
    flow.run_codex(tmp_path, 'test')
    command, root, timeout = calls[0]
    assert command[command.index('--sandbox') + 1] == 'workspace-write'
    assert '--dangerously-bypass-approvals-and-sandbox' not in command
    assert timeout == 1800


@pytest.mark.parametrize('value', [{'sandbox':'danger-full-access'}, {'node_timeout_seconds':0},
    {'helper_timeout_seconds':True}, {'unexpected':True}, []])
def test_invalid_policy_rejected(tmp_path, value):
    write(tmp_path / '.allforai/codex/execution-policy.json', value)
    with pytest.raises(ValueError):
        flow.execution_policy(tmp_path)


def test_subprocess_timeout(tmp_path):
    result = flow.run_bounded([sys.executable, '-c', 'import time; time.sleep(30)'], tmp_path, 1)
    assert result.returncode == 124
    assert 'Timed out' in result.stderr


def test_canonical_entry_is_resolvable():
    canonical = (ROOT / '../../claude/meta-skill').resolve()
    protocol = (ROOT / 'skills/bootstrap.md').read_text()
    import re
    entries = re.findall(r'<canonical-root>/(skills/[^`]*SKILL\.md)', protocol)
    assert entries
    assert all((canonical / path).is_file() for path in entries)


def test_standalone_installer_keeps_canonical_entry(tmp_path):
    import os
    import shutil
    adapter = tmp_path / 'source/codex/meta-skill'
    canonical = tmp_path / 'source/claude/meta-skill'
    (adapter / 'knowledge').mkdir(parents=True)
    (adapter / 'skills').mkdir()
    (canonical / 'skills/bootstrap').mkdir(parents=True)
    (canonical / 'knowledge').mkdir()
    for relative in ('install.sh', 'install_bundle.py', 'SKILL.md', 'AGENTS.md', 'knowledge/flow-template.py', 'skills/bootstrap.md'):
        shutil.copyfile(ROOT / relative, adapter / relative)
    (canonical / 'skills/bootstrap/SKILL.md').write_text('canonical test entry')
    target = tmp_path / 'installed/meta-skill'
    bundle = tmp_path / 'skill-bundles/meta-skill'
    result = subprocess.run(['bash', str(adapter / 'install.sh')], capture_output=True, text=True,
        env={**os.environ, 'MYSKILLS_CODEX_INSTALL_DIR':str(target),
             'MYSKILLS_CODEX_BUNDLE_DIR':str(bundle), 'SOURCE_COMMIT':'fixture'})
    assert result.returncode == 0, result.stderr
    assert (bundle / 'canonical/skills/bootstrap/SKILL.md').read_text() == 'canonical test entry'
    assert list(target.rglob('SKILL.md')) == [target / 'SKILL.md']
    assert str(bundle) in (target / 'SKILL.md').read_text()
    assert not any(p.is_symlink() for p in target.rglob('*'))
