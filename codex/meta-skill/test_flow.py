"""Driver contract tests: no paid CLI calls and no installed-skill mutations."""
import importlib.util
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
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


def test_accepted_with_gaps_is_not_reported_as_a_ready_artifact(tmp_path):
    report = tmp_path / 'report.json'
    write(report, {'status': 'accepted_with_gaps', 'gaps': []})
    assert not flow.artifact_ready(tmp_path, 'report.json')
    assert 'accepted_with_gaps' in flow.artifact_status_error(report, tmp_path)
    write(report, {'status': 'passed', 'gaps': []})
    assert flow.artifact_ready(tmp_path, 'report.json')


@pytest.mark.parametrize('status', ['existence_only', 'not_good_enough', 'quality_failed'])
def test_unverified_or_failed_quality_is_not_a_ready_artifact(tmp_path, status):
    report = tmp_path / 'report.json'
    write(report, {'status': status})
    assert not flow.artifact_ready(tmp_path, 'report.json')
    assert status in flow.artifact_status_error(report, tmp_path)
    write(report, {'status': 'passed'})
    assert flow.artifact_ready(tmp_path, 'report.json')


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


# --- declared QA repair loops (unattended-run-readiness-spec.required_repair_loops) ---

OMIT = object()


def repair_project(tmp_path, *, qa_report=None, transition_log=None, max_attempts=2):
    """Four-node loop: implement -> verify(QA) -> repair -> accept(closure)."""
    nodes = [
        {'node_id': 'implement', 'hard_blocked_by': [], 'exit_artifacts': ['impl.json']},
        {'node_id': 'verify', 'hard_blocked_by': ['implement'], 'exit_artifacts': ['verify.json']},
        {'node_id': 'repair', 'hard_blocked_by': ['verify'], 'exit_artifacts': ['repair.json']},
        {'node_id': 'accept', 'hard_blocked_by': ['repair'], 'exit_artifacts': ['accept.json']},
    ]
    workflow = {'nodes': nodes, 'transition_log': transition_log or []}
    write(tmp_path / '.allforai/bootstrap/workflow.json', workflow)
    loop = {
        'scope': 'orders-export',
        'qa_node_ids': ['verify'],
        'repair_node_id': 'repair',
        'closure_node_ids': ['accept'],
    }
    if max_attempts is not OMIT:
        loop['max_attempts'] = max_attempts
    write(tmp_path / '.allforai/bootstrap/unattended-run-readiness-spec.json', {
        'version': 1,
        'required_repair_loops': [loop],
    })
    write(tmp_path / 'impl.json', {'status': 'passed'})
    if qa_report is not None:
        write(tmp_path / 'verify.json', qa_report)
    stamp_attempt_evidence(tmp_path, workflow)
    return workflow


def iso_from_now(offset_seconds):
    """An ISO timestamp `offset_seconds` in the future (negative = in the past)."""
    return (datetime.now(timezone.utc) + timedelta(seconds=offset_seconds)).astimezone().isoformat(timespec='seconds')


def stamp_attempt_evidence(root, workflow, node_id='verify', bound=True):
    """Mark the node's recorded failed attempts with what that attempt produced.

    The driver writes this itself around every declared QA node — see
    `test_the_driver_records_what_a_qa_attempt_produced` — so fixtures that start
    mid-run record it the same way. `bound=False` is an attempt that ran while the
    node's inputs were bound to no observed snapshot.
    """
    node = next(n for n in workflow['nodes'] if n['node_id'] == node_id)
    produced = {a: flow.file_digest(root / a) for a in node.get('exit_artifacts', [])
                if (root / a).exists()}
    # A fixture with no freshness state stands in for one, matching the stub
    # `gate_by_ready_artifacts` installs; a real one uses its own recorded snapshot.
    binding = (flow.binding_identity(root, node_id) or STUB_BINDING) if bound else None
    for entry in workflow['transition_log']:
        if (entry.get('node') == node_id and entry.get('status') == 'failed'
                and 'qa_evidence' not in entry):
            entry['qa_evidence'] = {'binding': binding, 'produced': dict(produced)}
    write(root / '.allforai/bootstrap/workflow.json', workflow)
    return workflow


def qa_failed(node_id, started_at=None):
    return {'node': node_id, 'status': 'failed',
            'started_at': started_at or iso_from_now(-3600)}


def repair_delivered(node_id='repair'):
    return {'node': node_id, 'status': 'completed'}


# A declared node whose inputs have not moved. `evidence: unpublished` is the drift a
# failed QA node always has: it never gets to publish the evidence it failed to produce.
# The exact shape a bound-but-failed QA node has: its evidence is unpublished, so
# `status` is stale, while `readiness_status` says its binding still matches the inputs.
BOUND_FRESHNESS = {'admission': 'declared', 'status': 'stale', 'readiness_status': 'valid',
                   'diff': {'evidence': 'unpublished'}}
# Identity of the snapshot those fixtures stand in for having been observed against.
STUB_BINDING = 'stub-binding-identity'


def gate_by_ready_artifacts(tmp_path, monkeypatch):
    """Real artifact-status semantics without spawning check_artifacts.py.

    These fixtures are about routing, budgets and closure, not provenance, so
    `node_freshness` is stubbed to the shape a failed QA node has while its inputs are
    still the ones it was observed against. The admission rule itself is exercised
    against the real helpers in `freshness_project` and `legacy_project` below.
    """
    monkeypatch.setattr(flow, 'node_freshness', lambda project_root, node_id: dict(BOUND_FRESHNESS))
    monkeypatch.setattr(flow, 'binding_identity', lambda project_root, node_id: STUB_BINDING)
    def gate(project_root, node_id):
        workflow = flow.load_json(tmp_path / '.allforai/bootstrap/workflow.json')
        node = next(n for n in workflow['nodes'] if n['node_id'] == node_id)
        return all(flow.artifact_ready(project_root, flow.artifact_path(a))
                   for a in node['exit_artifacts'])
    monkeypatch.setattr(flow, 'independent_artifact_gate', gate)


def test_failed_qa_with_a_current_report_reaches_its_declared_repair(tmp_path, monkeypatch):
    workflow = repair_project(tmp_path, qa_report={'status': 'failed', 'gaps': ['missing column']},
                              transition_log=[qa_failed('verify')])
    gate_by_ready_artifacts(tmp_path, monkeypatch)
    node = flow.first_pending_node(tmp_path, workflow)
    assert node['node_id'] == 'repair'


def test_failed_qa_without_a_report_is_retried_not_routed(tmp_path, monkeypatch):
    workflow = repair_project(tmp_path, qa_report=None)
    gate_by_ready_artifacts(tmp_path, monkeypatch)
    node = flow.first_pending_node(tmp_path, workflow)
    assert node['node_id'] == 'verify'


def test_unreadable_qa_report_is_not_a_usable_repair_trigger(tmp_path, monkeypatch):
    workflow = repair_project(tmp_path, qa_report={'status': 'failed'})
    (tmp_path / 'verify.json').write_text('{broken')
    gate_by_ready_artifacts(tmp_path, monkeypatch)
    node = flow.first_pending_node(tmp_path, workflow)
    assert node['node_id'] == 'verify'


def test_repair_delivery_requeues_qa_before_closure(tmp_path, monkeypatch):
    workflow = repair_project(tmp_path, qa_report={'status': 'failed'},
                              transition_log=[qa_failed('verify'), repair_delivered()])
    write(tmp_path / 'repair.json', {'status': 'passed'})
    gate_by_ready_artifacts(tmp_path, monkeypatch)
    node = flow.first_pending_node(tmp_path, workflow)
    assert node['node_id'] == 'verify', 'a delivered repair is answered by the QA rerun, not another repair'
    workflow['transition_log'].append(qa_failed('verify'))
    stamp_attempt_evidence(tmp_path, workflow)
    node = flow.first_pending_node(tmp_path, workflow)
    assert node['node_id'] == 'repair', 'the rerun failed again: attempt 2 of 2 is still declared'
    workflow['transition_log'].extend([repair_delivered(), qa_failed('verify')])
    stamp_attempt_evidence(tmp_path, workflow)
    node = flow.first_pending_node(tmp_path, workflow)
    assert node['node_id'] == 'verify', 'budget spent: the QA node itself must run again'


def test_a_leftover_report_with_no_recorded_run_is_not_routed(tmp_path, monkeypatch):
    # File existence and parseability are not proof of a current verdict: a report left
    # behind by an earlier plan belongs to no run of this node.
    workflow = repair_project(tmp_path, qa_report={'status': 'failed', 'gaps': ['missing column']})
    gate_by_ready_artifacts(tmp_path, monkeypatch)
    assert flow.open_repair_loops(tmp_path, workflow, {}) == {}
    assert flow.first_pending_node(tmp_path, workflow)['node_id'] == 'verify'


def test_a_report_written_before_the_current_run_is_not_a_current_verdict(tmp_path, monkeypatch):
    workflow = repair_project(tmp_path, qa_report={'status': 'failed', 'gaps': ['missing column']},
                              transition_log=[qa_failed('verify', started_at=iso_from_now(3600))])
    gate_by_ready_artifacts(tmp_path, monkeypatch)
    assert flow.open_repair_loops(tmp_path, workflow, {}) == {}, \
        'the report predates the run that is being judged'
    assert flow.first_pending_node(tmp_path, workflow)['node_id'] == 'verify'


def test_a_current_qa_verdict_still_reaches_its_repair(tmp_path, monkeypatch):
    # The legitimate recovery path: this run produced the failing verdict.
    workflow = repair_project(tmp_path, qa_report={'status': 'failed', 'gaps': ['missing column']},
                              transition_log=[qa_failed('verify', started_at=iso_from_now(-3600))])
    gate_by_ready_artifacts(tmp_path, monkeypatch)
    assert flow.first_pending_node(tmp_path, workflow)['node_id'] == 'repair'


@pytest.mark.parametrize("status", ['failed_env', 'blocked', 'not_ready', 'not_generated',
                                    'existence_only', 'blocked_by_upstream'])
def test_a_non_qa_report_status_never_opens_a_repair_loop(tmp_path, monkeypatch, status):
    # Same admission rule as engine-core.js NON_QA_FAILURE_TYPES: an environment,
    # authority or never-ran failure carries no QA verdict to repair against.
    workflow = repair_project(tmp_path, qa_report={'status': status},
                              transition_log=[qa_failed('verify', started_at=iso_from_now(-3600))])
    gate_by_ready_artifacts(tmp_path, monkeypatch)
    assert flow.open_repair_loops(tmp_path, workflow, {}) == {}, status
    assert flow.first_pending_node(tmp_path, workflow)['node_id'] == 'verify'


def test_an_empty_report_carries_no_qa_verdict(tmp_path, monkeypatch):
    workflow = repair_project(tmp_path, qa_report={},
                              transition_log=[qa_failed('verify')])
    gate_by_ready_artifacts(tmp_path, monkeypatch)
    assert flow.open_repair_loops(tmp_path, workflow, {}) == {}
    assert flow.first_pending_node(tmp_path, workflow)['node_id'] == 'verify'


@pytest.mark.parametrize("report", [
    {'gaps': [], 'test_gaps': []},
    {'status': 'passed', 'gaps': []},
    {'summary': 'ran the suite'},
    [],
    [{'gap': 'missing column'}],
])
def test_a_report_without_a_positive_verdict_never_opens_repair(tmp_path, monkeypatch, report):
    # Parseable is not a verdict: empty documents, empty gap arrays and reports that
    # state no failing outcome have nothing for a repair node to act on. Such a report
    # may well let the node complete normally; what it must never do is open a repair.
    workflow = repair_project(tmp_path, qa_report=report,
                              transition_log=[qa_failed('verify')])
    gate_by_ready_artifacts(tmp_path, monkeypatch)
    node = next(n for n in workflow['nodes'] if n['node_id'] == 'verify')
    assert flow.qa_report_usable(tmp_path, node, workflow) is False, report
    assert flow.open_repair_loops(tmp_path, workflow, {}) == {}, report


@pytest.mark.parametrize("transition_log", [
    [],                                                          # never ran
    [{'node': 'verify', 'status': 'completed', 'started_at': 'FILL'}],   # last attempt passed
    [{'node': 'verify', 'status': 'failed'}],                    # failed, but unbindable
    [{'node': 'verify', 'status': 'failed', 'started_at': 'FILL'},
     {'node': 'verify', 'status': 'completed', 'started_at': 'FILL'}],   # failure superseded
])
def test_repair_needs_an_actual_failed_qa_attempt(tmp_path, monkeypatch, transition_log):
    # No recorded failure of this QA node on this attempt: there is no verdict this
    # run produced, whatever is on disk.
    for entry in transition_log:
        if entry.get('started_at') == 'FILL':
            entry['started_at'] = iso_from_now(-3600)
    workflow = repair_project(tmp_path, qa_report={'status': 'failed', 'gaps': ['missing column']},
                              transition_log=transition_log)
    gate_by_ready_artifacts(tmp_path, monkeypatch)
    assert flow.open_repair_loops(tmp_path, workflow, {}) == {}, transition_log
    assert flow.first_pending_node(tmp_path, workflow)['node_id'] == 'verify'


# --- admission bound to current inputs, judged by the real freshness helpers ---

ORCHESTRATOR = ROOT / '../../claude/meta-skill/scripts/orchestrator'


def freshness_cli(root, request):
    script = root / '.allforai/bootstrap/scripts/evidence_freshness.py'
    proc = subprocess.run([sys.executable, str(script), str(root)],
                          input=json.dumps(request), text=True, capture_output=True, cwd=root)
    assert proc.stdout, proc.stderr
    return json.loads(proc.stdout)


def freshness_project(tmp_path):
    """A QA node that declares its inputs and has a published freshness record.

    Runs the real orchestrator helpers the generated runtime ships, so admission is
    judged by the same freshness state the independent artifact gate reads.
    """
    scripts = tmp_path / '.allforai/bootstrap/scripts'
    scripts.mkdir(parents=True, exist_ok=True)
    for name in ('check_artifacts.py', 'evidence_freshness.py'):
        (scripts / name).write_bytes((ORCHESTRATOR / name).read_bytes())
    (tmp_path / 'src').mkdir(parents=True, exist_ok=True)
    (tmp_path / 'src/orders.py').write_text('def export():\n    return []\n')
    nodes = [
        {'node_id': 'verify', 'hard_blocked_by': [], 'source_inputs': [],
         'input_dependencies': ['src/orders.py'], 'exit_artifacts': ['verify.json']},
        {'node_id': 'repair', 'hard_blocked_by': ['verify'], 'source_inputs': [],
         'exit_artifacts': ['repair.json']},
    ]
    workflow = {'nodes': nodes, 'transition_log': []}
    write(tmp_path / '.allforai/bootstrap/workflow.json', workflow)
    write(tmp_path / '.allforai/bootstrap/unattended-run-readiness-spec.json', {
        'version': 1,
        'required_repair_loops': [{'scope': 'orders-export', 'qa_node_ids': ['verify'],
                                   'repair_node_id': 'repair', 'closure_node_ids': [],
                                   'max_attempts': 2}],
    })
    specs = tmp_path / '.allforai/bootstrap/node-specs'
    specs.mkdir(parents=True, exist_ok=True)
    (specs / 'verify.md').write_text('QA the orders export.\n')
    observed = freshness_cli(tmp_path, {'operation': 'observe', 'node_id': 'verify', 'kind': 'contract'})
    published = freshness_cli(tmp_path, {'operation': 'publish', 'observation': observed['observation'],
                                         'verification_command': [sys.executable, '-c', 'pass']})
    assert published.get('status') == 'valid', published
    return workflow


def record_failed_qa(tmp_path, workflow, report=None, bound=True):
    write(tmp_path / 'verify.json', report or {'status': 'failed', 'gaps': ['missing column']})
    workflow['transition_log'].append(qa_failed('verify'))
    stamp_attempt_evidence(tmp_path, workflow, bound=bound)


def test_a_current_failed_qa_with_current_inputs_reaches_its_repair(tmp_path):
    # The legitimate recovery path, end to end through the real artifact gate.
    workflow = freshness_project(tmp_path)
    record_failed_qa(tmp_path, workflow)
    assert flow.open_repair_loops(tmp_path, workflow, {}).keys() == {'verify'}
    assert flow.first_pending_node(tmp_path, workflow)['node_id'] == 'repair'


def test_a_touched_report_whose_inputs_moved_is_not_current(tmp_path):
    # mtime is not provenance: touching the report after an input changed must not
    # make a stale verdict look like this run's.
    workflow = freshness_project(tmp_path)
    record_failed_qa(tmp_path, workflow)
    (tmp_path / 'src/orders.py').write_text('def export():\n    return [1]\n')
    os.utime(tmp_path / 'verify.json', None)
    assert flow.open_repair_loops(tmp_path, workflow, {}) == {}
    assert flow.first_pending_node(tmp_path, workflow)['node_id'] == 'verify'


def test_a_report_bound_to_no_freshness_record_is_not_current(tmp_path):
    # A report whose node declares inputs but has published nothing has no provenance
    # binding it to any input at all.
    workflow = freshness_project(tmp_path)
    (tmp_path / '.allforai/bootstrap/evidence-freshness.json').unlink()
    record_failed_qa(tmp_path, workflow)
    assert flow.open_repair_loops(tmp_path, workflow, {}) == {}
    assert flow.first_pending_node(tmp_path, workflow)['node_id'] == 'verify'


def test_an_unreadable_freshness_gate_admits_nothing(tmp_path):
    workflow = freshness_project(tmp_path)
    record_failed_qa(tmp_path, workflow)
    (tmp_path / '.allforai/bootstrap/scripts/check_artifacts.py').unlink()
    assert flow.node_freshness(tmp_path, 'verify') is False
    assert flow.open_repair_loops(tmp_path, workflow, {}) == {}


# --- legacy projects: completion unchanged, automatic repair needs proof ---

def legacy_project(tmp_path, report=None):
    """A project with no freshness declarations and no freshness state at all.

    The real helpers are copied in, so `node_freshness` returns exactly what the
    independent artifact gate reports for such a project: nothing.
    """
    scripts = tmp_path / '.allforai/bootstrap/scripts'
    scripts.mkdir(parents=True, exist_ok=True)
    for name in ('check_artifacts.py', 'evidence_freshness.py'):
        (scripts / name).write_bytes((ORCHESTRATOR / name).read_bytes())
    (tmp_path / 'src').mkdir(parents=True, exist_ok=True)
    (tmp_path / 'src/orders.py').write_text('def export():\n    return []\n')
    nodes = [
        {'node_id': 'verify', 'hard_blocked_by': [], 'exit_artifacts': ['verify.json']},
        {'node_id': 'repair', 'hard_blocked_by': ['verify'], 'exit_artifacts': ['repair.json']},
    ]
    workflow = {'nodes': nodes, 'transition_log': []}
    write(tmp_path / '.allforai/bootstrap/workflow.json', workflow)
    write(tmp_path / '.allforai/bootstrap/unattended-run-readiness-spec.json', {
        'version': 1,
        'required_repair_loops': [{'scope': 'orders-export', 'qa_node_ids': ['verify'],
                                   'repair_node_id': 'repair', 'closure_node_ids': [],
                                   'max_attempts': 2}],
    })
    specs = tmp_path / '.allforai/bootstrap/node-specs'
    specs.mkdir(parents=True, exist_ok=True)
    (specs / 'verify.md').write_text('QA the orders export.\n')
    write(tmp_path / 'verify.json', report or {'status': 'failed', 'gaps': ['missing column']})
    workflow['transition_log'].append(qa_failed('verify'))
    # The attempt ran while nothing bound this node's inputs, which is what a legacy
    # project is; the driver would record exactly this.
    stamp_attempt_evidence(tmp_path, workflow, bound=False)
    return workflow


def observe_node_inputs(tmp_path, workflow, node_id='verify'):
    """The supported recovery: declare the node's inputs and observe them once."""
    node = next(n for n in workflow['nodes'] if n['node_id'] == node_id)
    node['source_inputs'] = []
    node['input_dependencies'] = ['src/orders.py']
    write(tmp_path / '.allforai/bootstrap/workflow.json', workflow)
    observed = freshness_cli(tmp_path, {'operation': 'observe', 'node_id': node_id, 'kind': 'contract'})
    published = freshness_cli(tmp_path, {'operation': 'publish', 'observation': observed['observation'],
                                         'verification_command': [sys.executable, '-c', 'pass']})
    assert published.get('status') == 'valid', published


def test_a_legacy_project_reports_no_freshness_at_all(tmp_path):
    workflow = legacy_project(tmp_path)
    assert flow.node_freshness(tmp_path, 'verify') is None


def test_a_touched_legacy_report_does_not_dispatch_automatic_repair(tmp_path):
    # Legacy completion semantics are untouched, but automatic repair is work this run
    # starts on the strength of a report. Absence of provenance is not permission for
    # it: a leftover verdict that was merely touched proves nothing about this attempt's
    # inputs, so the QA node is re-run and repeated failure is diagnosed instead.
    workflow = legacy_project(tmp_path)
    os.utime(tmp_path / 'verify.json', None)
    assert flow.qa_verdict(flow.load_json(tmp_path / 'verify.json')), 'the report does state a verdict'
    assert flow.last_failed_dispatch(workflow, 'verify'), 'and this run did record a failed attempt'
    assert flow.open_repair_loops(tmp_path, workflow, {}) == {}, 'yet nothing binds it to current inputs'
    assert flow.first_pending_node(tmp_path, workflow)['node_id'] == 'verify'


def rerun_qa(tmp_path, workflow, report, node_id='verify'):
    """A new attempt of the QA node: it starts, writes its report, and fails.

    The same order the driver uses — `started_at` is taken before the node runs, and
    the evidence records what the attempt changed while it ran.
    """
    node = next(n for n in workflow['nodes'] if n['node_id'] == node_id)
    started_at = iso_from_now(-5)
    before = flow.report_state(tmp_path, node)
    binding_before = flow.binding_identity(tmp_path, node_id)
    if binding_before is not None and not flow.qa_inputs_current(flow.node_freshness(tmp_path, node_id)):
        binding_before = None
    write(tmp_path / f'{node_id}.json', report)
    binding_after = flow.binding_identity(tmp_path, node_id)
    entry = {'node': node_id, 'status': 'failed', 'started_at': started_at,
             'qa_evidence': flow.attempt_evidence(
                 before, flow.report_state(tmp_path, node),
                 binding_before if binding_before == binding_after else None)}
    workflow['transition_log'].append(entry)
    write(tmp_path / '.allforai/bootstrap/workflow.json', workflow)
    return entry


def test_observing_a_legacy_node_does_not_launder_its_old_report(tmp_path):
    # A contract observation binds inputs. It says nothing about what an attempt that
    # already ran actually read, so it must never turn a historical report into a
    # current verdict — no matter that the inputs happen to be unchanged.
    workflow = legacy_project(tmp_path)
    assert flow.open_repair_loops(tmp_path, workflow, {}) == {}
    observe_node_inputs(tmp_path, workflow)
    assert flow.qa_inputs_current(flow.node_freshness(tmp_path, 'verify')) is True, \
        'the node is now bound: only the historical attempt is the problem'
    assert flow.open_repair_loops(tmp_path, workflow, {}) == {}, \
        'the old report was produced by an attempt that ran bound to nothing'
    assert flow.first_pending_node(tmp_path, workflow)['node_id'] == 'verify'


def test_a_rerun_after_observing_restores_the_legacy_repair_route(tmp_path):
    # The documented way back in, and the whole of it: declare the node's inputs,
    # observe them once, then let the QA node actually run again. The repair answers
    # that new attempt's verdict, not the one that came before the binding.
    workflow = legacy_project(tmp_path)
    observe_node_inputs(tmp_path, workflow)
    entry = rerun_qa(tmp_path, workflow, {'status': 'failed', 'gaps': ['orders export column']})
    assert entry['qa_evidence'] == {'binding': flow.binding_identity(tmp_path, 'verify'), 'ran': True,
                                    'produced': {'verify.json': flow.file_digest(tmp_path / 'verify.json')}}
    assert entry['qa_evidence']['binding'], 'the attempt ran against an observed snapshot'
    assert flow.open_repair_loops(tmp_path, workflow, {}).keys() == {'verify'}
    assert flow.first_pending_node(tmp_path, workflow)['node_id'] == 'repair'


def test_an_observed_legacy_node_still_loses_the_route_when_its_inputs_move(tmp_path):
    workflow = legacy_project(tmp_path)
    observe_node_inputs(tmp_path, workflow)
    rerun_qa(tmp_path, workflow, {'status': 'failed', 'gaps': ['orders export column']})
    assert flow.open_repair_loops(tmp_path, workflow, {}).keys() == {'verify'}
    (tmp_path / 'src/orders.py').write_text('def export():\n    return [1]\n')
    os.utime(tmp_path / 'verify.json', None)
    assert flow.open_repair_loops(tmp_path, workflow, {}) == {}
    assert flow.first_pending_node(tmp_path, workflow)['node_id'] == 'verify'


def test_a_bound_node_does_not_pass_on_mtime_alone(tmp_path):
    # Declared inputs that never moved, an old report merely touched, and a later
    # failed dispatch. Every timestamp lines up; the attempt still produced nothing,
    # so there is no verdict of its own to repair against.
    workflow = freshness_project(tmp_path)
    record_failed_qa(tmp_path, workflow)
    assert flow.open_repair_loops(tmp_path, workflow, {}).keys() == {'verify'}, 'the first attempt did produce it'

    node = next(n for n in workflow['nodes'] if n['node_id'] == 'verify')
    os.utime(tmp_path / 'verify.json', None)
    before = flow.report_state(tmp_path, node)      # the attempt starts after the touch
    workflow['transition_log'].append({
        'node': 'verify', 'status': 'failed', 'started_at': iso_from_now(-1),
        'qa_evidence': flow.attempt_evidence(before, flow.report_state(tmp_path, node),
                                             flow.binding_identity(tmp_path, 'verify')),
    })
    write(tmp_path / '.allforai/bootstrap/workflow.json', workflow)
    assert (tmp_path / 'verify.json').stat().st_mtime > 0
    assert flow.qa_inputs_current(flow.node_freshness(tmp_path, 'verify')) is True
    assert flow.open_repair_loops(tmp_path, workflow, {}) == {}, 'a touch is not a verdict'
    assert flow.first_pending_node(tmp_path, workflow)['node_id'] == 'verify'


def publish_evidence(tmp_path, node_id='verify'):
    """Publish the node as a passing delivery, the way a node that succeeded would."""
    observed = freshness_cli(tmp_path, {'operation': 'observe', 'node_id': node_id, 'kind': 'evidence'})
    published = freshness_cli(tmp_path, {'operation': 'publish', 'observation': observed['observation'],
                                         'verification_command': [sys.executable, '-c', 'pass']})
    assert published.get('status') == 'valid', published


def test_a_node_that_once_passed_is_not_denied_forever_by_its_stale_evidence(tmp_path):
    """Old passing evidence must not be a permanent veto.

    The node delivered once and published passing evidence. Its inputs then changed, so
    that evidence is stale — and a failing QA node can never publish new passing evidence
    to replace it. Observing its contract against the new inputs is the recovery: the
    node's binding is current again, and what still holds the route is the separate
    external-change gate, which has its own owner and its own resolution.
    """
    workflow = freshness_project(tmp_path)
    write(tmp_path / 'verify.json', {'status': 'passed'})
    publish_evidence(tmp_path)
    assert flow.qa_inputs_current(flow.node_freshness(tmp_path, 'verify')) is True

    (tmp_path / 'src/orders.py').write_text('def export():\n    return [1]\n')
    stale = flow.node_freshness(tmp_path, 'verify')
    assert stale['readiness_status'] == 'stale', 'the published evidence judged inputs that moved'
    assert flow.qa_inputs_current(stale) is False

    # The recovery: reobserve the contract against the inputs as they are now.
    observed = freshness_cli(tmp_path, {'operation': 'observe', 'node_id': 'verify', 'kind': 'contract'})
    published = freshness_cli(tmp_path, {'operation': 'publish', 'observation': observed['observation'],
                                         'verification_command': [sys.executable, '-c', 'pass']})
    assert published.get('status') == 'valid', published

    recovered = flow.node_freshness(tmp_path, 'verify')
    assert recovered['readiness_status'] == 'valid', \
        'the fresh contract binds the current inputs; the stale evidence does not veto it'
    # What remains is the external-change gate, not the old evidence snapshot.
    assert recovered.get('external') == 'unverified'
    assert flow.qa_inputs_current({k: v for k, v in recovered.items() if k != 'external'}) is True, \
        'with that gate satisfied the route is open again, bound to the new inputs'


def test_a_declared_node_whose_contract_is_current_admits_despite_unpublished_evidence(tmp_path):
    """`status` tracks evidence and a failed QA node has none; `readiness_status` is the test."""
    workflow = freshness_project(tmp_path)
    freshness = flow.node_freshness(tmp_path, 'verify')
    assert freshness['status'] == 'stale' and freshness['readiness_status'] == 'valid'
    assert flow.qa_inputs_current(freshness) is True
    record_failed_qa(tmp_path, workflow)
    assert flow.open_repair_loops(tmp_path, workflow, {}).keys() == {'verify'}


def test_a_byte_identical_rerun_is_recorded_as_ambiguous_not_produced(tmp_path):
    """Unchanged bytes are not a verdict this attempt produced, and not a denial either.

    A node that re-ran and reached the same verdict is indistinguishable from a file
    nobody wrote, so the attempt records the ambiguity, the route stays shut, and the
    run diagnoses it rather than the driver guessing.
    """
    workflow = freshness_project(tmp_path)
    verdict = {'status': 'failed', 'gaps': ['missing column']}
    record_failed_qa(tmp_path, workflow, verdict)
    assert flow.open_repair_loops(tmp_path, workflow, {}).keys() == {'verify'}

    entry = rerun_qa(tmp_path, workflow, verdict)
    assert entry['qa_evidence']['produced'] == {}, 'nothing new was said'
    assert entry['qa_evidence']['ambiguous'] == ['verify.json']
    assert flow.open_repair_loops(tmp_path, workflow, {}) == {}
    assert flow.first_pending_node(tmp_path, workflow)['node_id'] == 'verify'


def test_a_repeated_verdict_carrying_its_attempt_identity_opens_the_repair(tmp_path):
    """The supported way to repeat a verdict: say which attempt reached it.

    The QA node's report names the attempt that produced it, so the same finding twice
    is still two distinct verdicts and neither has to be inferred from a write time.
    """
    workflow = freshness_project(tmp_path)
    record_failed_qa(tmp_path, workflow, {'status': 'failed', 'gaps': ['missing column'],
                                          'attempt': 'run-1'})
    assert flow.open_repair_loops(tmp_path, workflow, {}).keys() == {'verify'}

    entry = rerun_qa(tmp_path, workflow, {'status': 'failed', 'gaps': ['missing column'],
                                          'attempt': 'run-2'})
    assert entry['qa_evidence']['produced'] == {'verify.json': flow.file_digest(tmp_path / 'verify.json')}
    assert 'ambiguous' not in entry['qa_evidence']
    assert flow.open_repair_loops(tmp_path, workflow, {}).keys() == {'verify'}


def test_an_input_changed_and_reobserved_during_the_attempt_is_refused(tmp_path):
    """Two currentness answers are not one snapshot.

    The inputs are bound when the attempt starts and bound again when it ends, but not
    to the same observation: the source moved underneath and was republished. Both
    booleans would say yes; the snapshot identity says they are different inputs.
    """
    workflow = freshness_project(tmp_path)
    node = next(n for n in workflow['nodes'] if n['node_id'] == 'verify')
    binding_before = flow.binding_identity(tmp_path, 'verify')
    before = flow.report_state(tmp_path, node)

    # ... the attempt runs, and the source it is judging changes and is republished ...
    (tmp_path / 'src/orders.py').write_text('def export():\n    return [1]\n')
    observed = freshness_cli(tmp_path, {'operation': 'observe', 'node_id': 'verify', 'kind': 'contract'})
    published = freshness_cli(tmp_path, {'operation': 'publish', 'observation': observed['observation'],
                                         'verification_command': [sys.executable, '-c', 'pass']})
    assert published.get('status') == 'valid', published
    write(tmp_path / 'verify.json', {'status': 'failed', 'gaps': ['missing column']})

    binding_after = flow.binding_identity(tmp_path, 'verify')
    assert binding_before != binding_after, 'the observed snapshot moved during the attempt'
    assert flow.qa_inputs_current(flow.node_freshness(tmp_path, 'verify')) is True, \
        'and freshness alone still says the inputs are current'
    workflow['transition_log'].append({
        'node': 'verify', 'status': 'failed', 'started_at': iso_from_now(-5),
        'qa_evidence': flow.attempt_evidence(before, flow.report_state(tmp_path, node),
                                             binding_before if binding_before == binding_after else None),
    })
    write(tmp_path / '.allforai/bootstrap/workflow.json', workflow)
    assert flow.open_repair_loops(tmp_path, workflow, {}) == {}
    assert flow.first_pending_node(tmp_path, workflow)['node_id'] == 'verify'


def test_reobserving_after_the_attempt_does_not_revalidate_its_report(tmp_path):
    """The other half of the snapshot rule, on the admission side.

    The attempt genuinely ran and genuinely produced its report against snapshot A.
    Then the source changes and is republished, so the node is bound and current
    again — to snapshot B. The stored report judged A, and re-observing does not make
    it a verdict about B.
    """
    workflow = freshness_project(tmp_path)
    record_failed_qa(tmp_path, workflow)
    assert flow.open_repair_loops(tmp_path, workflow, {}).keys() == {'verify'}
    bound_to = flow.binding_identity(tmp_path, 'verify')

    (tmp_path / 'src/orders.py').write_text('def export():\n    return [1]\n')
    observed = freshness_cli(tmp_path, {'operation': 'observe', 'node_id': 'verify', 'kind': 'contract'})
    published = freshness_cli(tmp_path, {'operation': 'publish', 'observation': observed['observation'],
                                         'verification_command': [sys.executable, '-c', 'pass']})
    assert published.get('status') == 'valid', published

    assert flow.qa_inputs_current(flow.node_freshness(tmp_path, 'verify')) is True, \
        'the node is bound and current again'
    assert flow.binding_identity(tmp_path, 'verify') != bound_to, 'but to a different snapshot'
    assert flow.open_repair_loops(tmp_path, workflow, {}) == {}
    assert flow.first_pending_node(tmp_path, workflow)['node_id'] == 'verify'


def test_an_executor_that_only_touches_the_report_does_not_dispatch_repair(tmp_path, monkeypatch):
    """`flow.main()` with an executor that runs `utime` and nothing else.

    The report is a real, positive, failing verdict left from before; the attempt is
    real and its inputs are bound. Only the write time moved, and a write time is not
    a verdict — the driver records the ambiguity and no repair is dispatched.
    """
    import shutil
    workflow = freshness_project(tmp_path)
    scripts = tmp_path / '.allforai/bootstrap/scripts'
    shutil.copy2(ORCHESTRATOR / 'product_intent.py', scripts)
    write(tmp_path / '.allforai/bootstrap/run-policy.json', {
        'on_repeated_failure': 'halt', 'on_needs_iteration': 'halt_with_report',
        'on_safety_warning': 'continue'})
    node = next(n for n in workflow['nodes'] if n['node_id'] == 'verify')
    write(tmp_path / 'verify.json', {'status': 'failed', 'gaps': ['missing column']})
    left_over = flow.file_digest(tmp_path / 'verify.json')

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, 'argv', ['flow.py'])
    monkeypatch.setattr(flow, 'run_preflight', lambda *a: 0)
    monkeypatch.setattr(flow, 'run_expanders', lambda *a: True)
    monkeypatch.setattr(flow, 'first_pending_node', lambda *a: node)
    monkeypatch.setattr(flow, 'run_diagnosis', lambda *a: subprocess.CompletedProcess([], 0, '', ''))

    def worker(project_root, prompt):
        os.utime(project_root / 'verify.json', None)     # the whole of the "run"
        return subprocess.CompletedProcess([], 0, '', '')

    monkeypatch.setattr(flow, 'run_codex', worker)
    flow.main()

    current = flow.load_json(tmp_path / '.allforai/bootstrap/workflow.json')
    log = [e for e in current['transition_log'] if e.get('node') == 'verify']
    assert flow.file_digest(tmp_path / 'verify.json') == left_over, 'the bytes never changed'
    assert log[-1]['qa_evidence']['produced'] == {}, 'a touch produced nothing'
    assert log[-1]['qa_evidence']['ambiguous'] == ['verify.json']
    assert 'must carry the attempt that produced it' in log[-1]['error'], \
        'and the run is told why, rather than the route silently closing'
    assert flow.open_repair_loops(tmp_path, current, {}) == {}
    assert flow.first_pending_node(tmp_path, current)['node_id'] == 'verify'


def routing_project(tmp_path):
    """The canonical declared loop: QA -> repair -> closure, every node fully declared.

    No node is downgraded to obtain a green run. Every node declares `source_inputs`,
    the repair node is `hard_blocked_by` its QA node and the closure node is
    `hard_blocked_by` the repair node, which is the shape
    `validate_unattended_readiness._validate_repair_loop_spec` requires, and each node
    publishes its own contract at planning time as the freshness protocol asks.
    """
    workflow = freshness_project(tmp_path)
    # Closure is hard_blocked_by the repair node (readiness) and by every QA node
    # (validate_bootstrap: it would otherwise close on the repair alone, without the QA
    # rerun that proves it).
    workflow['nodes'].append({'node_id': 'accept', 'hard_blocked_by': ['repair', 'verify'],
                              'source_inputs': [], 'input_dependencies': ['src/orders.py'],
                              'exit_artifacts': ['accept.json']})
    spec = json.loads((tmp_path / '.allforai/bootstrap/unattended-run-readiness-spec.json').read_text())
    spec['required_repair_loops'][0]['closure_node_ids'] = ['accept']
    write(tmp_path / '.allforai/bootstrap/unattended-run-readiness-spec.json', spec)
    write(tmp_path / '.allforai/bootstrap/workflow.json', workflow)
    specs = tmp_path / '.allforai/bootstrap/node-specs'
    for node_id in ('repair', 'accept'):
        (specs / f'{node_id}.md').write_text(f'{node_id} node.\n')
    for node_id in ('repair', 'accept'):
        observed = freshness_cli(tmp_path, {'operation': 'observe', 'node_id': node_id,
                                            'kind': 'contract'})
        published = freshness_cli(tmp_path, {'operation': 'publish',
                                             'observation': observed['observation'],
                                             'verification_command': [sys.executable, '-c', 'pass']})
        assert published.get('status') == 'valid', (node_id, published)
    return workflow


def try_publish_evidence(tmp_path, node_id):
    """Publish the node's delivery if freshness allows it yet; report what happened.

    A declared repair node cannot publish while the QA node it repairs is still
    failing — its own upstream evidence is stale — so a real run gets `stale` here and
    carries on. That refusal is the system working, not something to route around.
    """
    observed = freshness_cli(tmp_path, {'operation': 'observe', 'node_id': node_id, 'kind': 'evidence'})
    return freshness_cli(tmp_path, {'operation': 'publish', 'observation': observed['observation'],
                                    'verification_command': [sys.executable, '-c', 'pass']}).get('status')


def drive_real_routing(tmp_path, monkeypatch, executor, failing_nodes=frozenset(),
                       max_iterations=None):
    """Run `flow.main()` with the real node selection, recording what it actually chose.

    `first_pending_node` is wrapped, not replaced: the driver picks nodes through
    `open_repair_loops` exactly as it does in a run, and the spy only records the choice.
    Preflight and expanders are stubbed because they are not what is under test.
    """
    import shutil
    scripts = tmp_path / '.allforai/bootstrap/scripts'
    shutil.copy2(ORCHESTRATOR / 'product_intent.py', scripts)
    write(tmp_path / '.allforai/bootstrap/run-policy.json', {
        'on_repeated_failure': 'halt', 'on_needs_iteration': 'halt_with_report',
        'on_safety_warning': 'continue'})
    selected = []
    real_first_pending_node = flow.first_pending_node

    def spy(project_root, workflow):
        node = real_first_pending_node(project_root, workflow)
        selected.append(node and node.get('node_id'))
        return node

    executed = []

    def worker(project_root, prompt):
        node_id = selected[-1]          # the node the real selector just chose
        executed.append(node_id)
        try:
            executor(project_root, node_id, executed.count(node_id))
        except RuntimeError as exc:
            return subprocess.CompletedProcess([], 1, '', str(exc))
        return subprocess.CompletedProcess([], 1 if node_id in failing_nodes else 0, '', '')

    monkeypatch.chdir(tmp_path)
    argv = ['flow.py'] if max_iterations is None else ['flow.py', 'goal', str(max_iterations)]
    monkeypatch.setattr(sys, 'argv', argv)
    monkeypatch.setattr(flow, 'run_preflight', lambda *a: 0)
    monkeypatch.setattr(flow, 'run_expanders', lambda *a: True)
    monkeypatch.setattr(flow, 'run_post_checks', lambda *a: True)
    monkeypatch.setattr(flow, 'run_diagnosis', lambda *a: subprocess.CompletedProcess([], 0, '', ''))
    monkeypatch.setattr(flow, 'first_pending_node', spy)
    monkeypatch.setattr(flow, 'run_codex', worker)
    flow.main()
    return selected, executed


def _load_orchestrator_module(name):
    import importlib.util
    loader = importlib.util.spec_from_file_location(name, ORCHESTRATOR / f'{name}.py')
    module = importlib.util.module_from_spec(loader)
    sys.path.insert(0, str(ORCHESTRATOR))
    try:
        loader.loader.exec_module(module)
    finally:
        sys.path.remove(str(ORCHESTRATOR))
    return module


def test_the_routing_fixture_satisfies_the_planner_repair_loop_rules(tmp_path):
    """The graph under test is the shape both planner validators require."""
    workflow = routing_project(tmp_path)
    module = _load_orchestrator_module('validate_unattended_readiness')
    spec = json.loads((tmp_path / '.allforai/bootstrap/unattended-run-readiness-spec.json').read_text())
    blockers, warnings = [], []
    # The readiness validator gained a warnings sink for the budget check; accept either
    # shape so this pins the loop wiring, not the version of a file it does not own.
    import inspect
    arity = len(inspect.signature(module._validate_repair_loop_spec).parameters)
    args = (spec, workflow['nodes'], blockers, warnings)[:arity]
    module._validate_repair_loop_spec(*args)
    assert blockers == [], blockers
    assert warnings == [], warnings

    # And the bootstrap validator, whose closure rule is stricter: the closure node must be
    # hard_blocked_by every QA node, not the repair node alone.
    bootstrap = _load_orchestrator_module('validate_bootstrap')
    if hasattr(bootstrap, 'validate_repair_loop_declaration'):
        errors = bootstrap.validate_repair_loop_declaration(str(tmp_path / '.allforai/bootstrap'))
        assert errors == [], errors
        broken = json.loads((tmp_path / '.allforai/bootstrap/workflow.json').read_text())
        next(n for n in broken['nodes'] if n['node_id'] == 'accept')['hard_blocked_by'] = ['repair']
        write(tmp_path / '.allforai/bootstrap/workflow.json', broken)
        assert any('not hard_blocked_by QA node' in e for e in
                   bootstrap.validate_repair_loop_declaration(str(tmp_path / '.allforai/bootstrap'))), \
            'the fixture would have failed that rule without the QA closure edge'
        write(tmp_path / '.allforai/bootstrap/workflow.json', workflow)

    assert all('source_inputs' in n for n in workflow['nodes']), 'no node is downgraded'


def test_a_declared_repair_node_cannot_complete_while_its_qa_node_fails(tmp_path):
    """The constraint the loop has to live with, pinned so it cannot be forgotten.

    A declared repair node is `hard_blocked_by` the QA node it repairs, and freshness
    treats that as an evidence dependency, so while the QA node is failing the repair
    node's own evidence is stale and its gate refuses it. The loop therefore cannot
    advance on the repair node *completing*; it advances on the repair *delivering*.
    """
    routing_project(tmp_path)
    write(tmp_path / 'verify.json', {'status': 'failed', 'gaps': ['missing column']})
    write(tmp_path / 'repair.json', {'status': 'passed'})

    freshness = flow.node_freshness(tmp_path, 'repair')
    assert freshness['diff']['upstream'] == ['verify']
    assert freshness['reason'] == 'Upstream evidence is stale or missing'
    assert flow.independent_artifact_gate(tmp_path, 'repair') is False
    assert try_publish_evidence(tmp_path, 'repair') == 'stale'

    bound = flow.binding_identity(tmp_path, 'repair')
    produced = {'repair.json': flow.file_digest(tmp_path / 'repair.json')}
    delivered = {'node': 'repair', 'status': 'failed', 'started_at': iso_from_now(-1),
                 'qa_evidence': {'binding': bound, 'ran': True, 'produced': produced}}
    assert flow.repair_delivered(delivered) is True, 'it delivered what the QA node must re-verify'

    def evidence(**overrides):
        payload = {'binding': bound, 'ran': True, 'produced': dict(produced)}
        payload.update(overrides)
        return {'node': 'repair', 'status': 'failed', 'qa_evidence': payload}

    assert flow.repair_delivered(evidence(produced={})) is False, 'wrote nothing'
    assert flow.repair_delivered(evidence(ran=False)) is False, 'the executor never ran'
    assert flow.repair_delivered(evidence(binding=None)) is False, 'ran against no observed snapshot'
    assert flow.repair_delivered({'node': 'repair', 'status': 'failed'}) is False, 'no evidence at all'


def test_real_routing_never_executes_repair_for_a_touched_leftover(tmp_path, monkeypatch):
    """End to end through the real selector: a touch must not reach the repair node."""
    workflow = routing_project(tmp_path)
    write(tmp_path / 'verify.json', {'status': 'failed', 'gaps': ['missing column']})

    def executor(project_root, node_id, attempt):
        if node_id == 'verify':
            os.utime(project_root / 'verify.json', None)

    selected, executed = drive_real_routing(tmp_path, monkeypatch, executor)
    assert executed, 'the driver did dispatch work'
    assert 'repair' not in executed, f'a touch reached the repair node: {executed}'
    assert 'repair' not in selected, f'a touch selected the repair node: {selected}'
    assert 'accept' not in executed, 'and closure never ran on an unrepaired QA failure'


def test_real_routing_drives_the_declared_loop_to_closure(tmp_path, monkeypatch):
    """The canonical loop end to end: every node declared, nothing stubbed.

    Real `first_pending_node`, real `check_artifacts` gate with real freshness
    admission, and real `evidence_freshness` publication. Each node does what a node
    does: writes its artifacts and publishes its delivery when freshness allows.
    """
    routing_project(tmp_path)
    published = []

    def executor(project_root, node_id, attempt):
        if node_id == 'verify' and attempt == 1:
            write(project_root / 'verify.json', {'status': 'failed', 'gaps': ['missing column']})
            return                                   # a failing node publishes nothing
        if node_id == 'verify':
            write(project_root / 'verify.json', {'status': 'passed'})
        elif node_id == 'repair':
            write(project_root / 'repair.json', {'status': 'passed', 'attempt': attempt})
        elif node_id == 'accept':
            write(project_root / 'accept.json', {'status': 'passed'})
        published.append((node_id, attempt, try_publish_evidence(project_root, node_id)))

    selected, executed = drive_real_routing(tmp_path, monkeypatch, executor)

    assert executed[:4] == ['verify', 'repair', 'verify', 'repair'], executed
    assert executed.index('accept') == 4, executed
    assert 'accept' not in executed[:4], 'closure never precedes the passing QA rerun'
    # The repair node's first delivery is refused by freshness, exactly as reproduced;
    # the loop advances on the delivery, and the node completes on its own merits later.
    assert ('repair', 1, 'stale') in published, published
    assert ('repair', 2, 'valid') in published, published
    assert ('verify', 2, 'valid') in published, published
    assert ('accept', 1, 'valid') in published, published

    current = flow.load_json(tmp_path / '.allforai/bootstrap/workflow.json')
    by_node = {}
    for entry in current['transition_log']:
        by_node.setdefault(entry['node'], []).append(entry['status'])
    assert by_node['verify'] == ['failed', 'completed'], by_node
    assert by_node['repair'] == ['failed', 'completed'], by_node
    assert by_node['accept'] == ['completed'], by_node
    assert flow.first_pending_node(tmp_path, current) is None, 'the workflow is finished'


def test_real_routing_converges_when_the_repair_changes_the_source(tmp_path, monkeypatch):
    """The realistic loop: the repair edits the source the QA node judges.

    The QA node's first verdict is against the old source; the repair changes it; the
    rerun must verify the *new* source and publish evidence bound to it, and only then
    may closure run. The repair node's second dispatch is a finalization: it publishes
    the delivery it already made rather than repeating an edit that would invalidate the
    verification that just passed.
    """
    routing_project(tmp_path)
    finalizing = []

    def executor(project_root, node_id, attempt):
        if node_id == 'verify' and attempt == 1:
            write(project_root / 'verify.json', {'status': 'failed', 'gaps': ['missing column']})
            return
        if node_id == 'verify':
            write(project_root / 'verify.json', {'status': 'passed', 'source': 'with-column'})
        elif node_id == 'repair' and attempt == 1:
            # A real repair edits the source the QA node judges.
            (project_root / 'src/orders.py').write_text('def export():\n    return ["column"]\n')
            write(project_root / 'repair.json', {'status': 'passed'})
        elif node_id == 'repair':
            finalizing.append(flow.file_digest(project_root / 'src/orders.py'))
        elif node_id == 'accept':
            write(project_root / 'accept.json', {'status': 'passed'})
        try_publish_evidence(project_root, node_id)

    prompts = []
    real_build_prompt = flow.build_prompt
    monkeypatch.setattr(flow, 'build_prompt',
                        lambda node_id, goal, finalize=False: (prompts.append((node_id, finalize))
                                                               or real_build_prompt(node_id, goal, finalize)))
    selected, executed = drive_real_routing(tmp_path, monkeypatch, executor)

    assert executed[:4] == ['verify', 'repair', 'verify', 'repair'], executed
    assert executed.index('accept') == 4, executed
    assert ('repair', False) in prompts and ('repair', True) in prompts, prompts
    assert prompts[3] == ('repair', True), 'the second repair dispatch is a finalization'
    assert flow.FINALIZE_EVIDENCE_NOTE.strip().splitlines()[0] in real_build_prompt('repair', 'g', True)
    # The finalization did not touch the source the passing QA run verified.
    assert finalizing == [flow.file_digest(tmp_path / 'src/orders.py')], finalizing
    assert json.loads((tmp_path / 'verify.json').read_text())['source'] == 'with-column'

    current = flow.load_json(tmp_path / '.allforai/bootstrap/workflow.json')
    assert flow.first_pending_node(tmp_path, current) is None, 'the workflow is finished'
    assert flow.node_freshness(tmp_path, 'verify')['status'] == 'valid', \
        'closure ran with QA evidence current for the final source'


def test_a_repair_that_mutates_after_the_qa_pass_does_not_reach_closure(tmp_path, monkeypatch):
    """Post-QA mutation must not close.

    The finalization dispatch edits the source anyway. That invalidates the evidence the
    QA node just published, and closure — which depends on the repair, which depends on
    the QA node — must not complete on a verification that no longer describes the source.
    """
    routing_project(tmp_path)

    def executor(project_root, node_id, attempt):
        if node_id == 'verify' and attempt == 1:
            write(project_root / 'verify.json', {'status': 'failed', 'gaps': ['missing column']})
            return
        if node_id == 'verify':
            write(project_root / 'verify.json', {'status': 'passed'})
        elif node_id == 'repair' and attempt == 1:
            write(project_root / 'repair.json', {'status': 'passed'})
        elif node_id == 'repair':
            # Ignores the finalization instruction and edits the source again, differently
            # each time, so every QA pass is invalidated by the edit that follows it.
            (project_root / 'src/orders.py').write_text(
                f'def export():\n    return ["late-{attempt}"]\n')
        elif node_id == 'accept':
            write(project_root / 'accept.json', {'status': 'passed'})
        try_publish_evidence(project_root, node_id)

    selected, executed = drive_real_routing(tmp_path, monkeypatch, executor, max_iterations=8)
    assert 'accept' not in executed, f'closure ran on invalidated QA evidence: {executed}'
    assert executed.count('repair') >= 2, executed
    current = flow.load_json(tmp_path / '.allforai/bootstrap/workflow.json')
    assert flow.node_freshness(tmp_path, 'verify')['status'] != 'valid', \
        'the last edit left the QA evidence describing a source that no longer exists'
    assert [e['status'] for e in current['transition_log'] if e['node'] == 'accept'] == []


@pytest.mark.parametrize("mode", ['writes-nothing', 'touches-only', 'executor-error', 'blocked-report'])
def test_a_repair_attempt_that_delivers_nothing_never_releases_the_qa_rerun(tmp_path, monkeypatch, mode):
    """Four ways to not deliver, none of which may advance the loop or spend a budget."""
    routing_project(tmp_path)
    if mode in ('touches-only', 'blocked-report'):
        write(tmp_path / 'repair.json', {'status': 'passed'})

    def executor(project_root, node_id, attempt):
        if node_id == 'verify':
            write(project_root / 'verify.json', {'status': 'failed', 'gaps': ['missing column']})
        elif node_id == 'repair':
            if mode == 'touches-only':
                os.utime(project_root / 'repair.json', None)
            elif mode == 'blocked-report':
                write(project_root / 'repair.json', {'status': 'failed_env'})
            elif mode == 'executor-error':
                write(project_root / 'repair.json', {'status': 'passed', 'attempt': attempt})
                raise RuntimeError('executor failed')

    selected, executed = drive_real_routing(tmp_path, monkeypatch, executor,
                                            failing_nodes={'repair'} if mode == 'executor-error' else set())
    current = flow.load_json(tmp_path / '.allforai/bootstrap/workflow.json')
    assert 'accept' not in executed, f'closure ran without a repair: {executed}'
    assert executed.count('verify') == 1, f'the QA node was released by a non-delivery: {executed}'
    delivered, _ = flow.repair_progress(current, 'repair', 'verify')
    assert delivered == 0, f'{mode} spent a budgeted attempt: {current["transition_log"]}'


def test_a_spent_repair_budget_is_counted_once_across_a_restart(tmp_path, monkeypatch):
    """The budget is durable: re-reading the same log yields the same count, and once spent
    the QA node is no longer routed, so closure is never reached."""
    routing_project(tmp_path)

    def executor(project_root, node_id, attempt):
        if node_id == 'verify':
            write(project_root / 'verify.json', {'status': 'failed', 'gaps': ['missing column'],
                                                 'attempt': attempt})
        elif node_id == 'repair':
            write(project_root / 'repair.json', {'status': 'passed', 'attempt': attempt})
        try_publish_evidence(project_root, node_id)

    selected, executed = drive_real_routing(tmp_path, monkeypatch, executor)
    current = flow.load_json(tmp_path / '.allforai/bootstrap/workflow.json')
    delivered, answered = flow.repair_progress(current, 'repair', 'verify')
    assert delivered == 2, f'max_attempts is 2: {executed}'
    assert executed.count('repair') == 2, executed
    assert 'accept' not in executed, 'an unrepaired QA failure never reaches closure'
    # A restart re-derives the same spent budget from the same durable log.
    reloaded = flow.load_json(tmp_path / '.allforai/bootstrap/workflow.json')
    assert flow.repair_progress(reloaded, 'repair', 'verify') == (delivered, answered)
    assert flow.open_repair_loops(tmp_path, reloaded, {}) == {}, 'the budget stays spent'


def test_a_worker_cannot_supply_its_own_attempt_evidence(tmp_path, monkeypatch):
    """The driver observed the attempt; the worker inside it did not.

    A node that appends its own transition — with its own `qa_evidence`, or a second
    entry behind the driver's — must not be able to hand itself a repair.
    """
    import shutil
    workflow = freshness_project(tmp_path)
    scripts = tmp_path / '.allforai/bootstrap/scripts'
    shutil.copy2(ORCHESTRATOR / 'product_intent.py', scripts)
    write(tmp_path / '.allforai/bootstrap/run-policy.json', {
        'on_repeated_failure': 'halt', 'on_needs_iteration': 'halt_with_report',
        'on_safety_warning': 'continue'})
    node = next(n for n in workflow['nodes'] if n['node_id'] == 'verify')
    write(tmp_path / 'verify.json', {'status': 'failed', 'gaps': ['left over']})
    forged = {'binding': flow.binding_identity(tmp_path, 'verify'),
              'produced': {'verify.json': flow.file_digest(tmp_path / 'verify.json')}}

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, 'argv', ['flow.py'])
    monkeypatch.setattr(flow, 'run_preflight', lambda *a: 0)
    monkeypatch.setattr(flow, 'run_expanders', lambda *a: True)
    monkeypatch.setattr(flow, 'first_pending_node', lambda *a: node)
    monkeypatch.setattr(flow, 'run_diagnosis', lambda *a: subprocess.CompletedProcess([], 0, '', ''))

    def worker(project_root, prompt):
        # The worker writes nothing, and claims the leftover as its own verdict.
        path = project_root / '.allforai/bootstrap/workflow.json'
        current = flow.load_json(path)
        current.setdefault('transition_log', []).extend([
            {'node': 'verify', 'status': 'failed', 'started_at': iso_from_now(-1),
             'qa_evidence': dict(forged)},
            {'node': 'verify', 'status': 'failed', 'started_at': iso_from_now(-1),
             'qa_evidence': dict(forged)},
        ])
        flow.save_json(path, current)
        return subprocess.CompletedProcess([], 0, '', '')

    monkeypatch.setattr(flow, 'run_codex', worker)
    flow.main()

    log = [e for e in flow.load_json(tmp_path / '.allforai/bootstrap/workflow.json')['transition_log']
           if e.get('node') == 'verify']
    assert all(e['qa_evidence']['produced'] == {} for e in log), \
        'the driver overwrote every forged claim with what it observed'
    assert flow.open_repair_loops(tmp_path, flow.load_json(
        tmp_path / '.allforai/bootstrap/workflow.json'), {}) == {}


def test_the_driver_records_what_a_qa_attempt_produced(tmp_path, monkeypatch):
    """The public driver seam: `main()` writes the evidence admission later reads.

    One attempt writes a failing report; the next two write nothing. The first is
    recorded as having produced it with its inputs bound, the others as having
    produced nothing — which is exactly what stops a leftover from opening a repair.
    """
    import shutil
    workflow = freshness_project(tmp_path)
    scripts = tmp_path / '.allforai/bootstrap/scripts'
    shutil.copy2(ORCHESTRATOR / 'product_intent.py', scripts)
    write(tmp_path / '.allforai/bootstrap/run-policy.json', {
        'on_repeated_failure': 'halt', 'on_needs_iteration': 'halt_with_report',
        'on_safety_warning': 'continue'})
    node = next(n for n in workflow['nodes'] if n['node_id'] == 'verify')

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, 'argv', ['flow.py'])
    monkeypatch.setattr(flow, 'run_preflight', lambda *a: 0)
    monkeypatch.setattr(flow, 'run_expanders', lambda *a: True)
    monkeypatch.setattr(flow, 'first_pending_node', lambda *a: node)
    monkeypatch.setattr(flow, 'run_diagnosis', lambda *a: subprocess.CompletedProcess([], 0, 'diagnosed', ''))
    attempts = []

    def worker(project_root, prompt):
        attempts.append(prompt)
        if len(attempts) == 1:
            write(project_root / 'verify.json', {'status': 'failed', 'gaps': ['orders export column']})
        return subprocess.CompletedProcess([], 0, '', '')

    monkeypatch.setattr(flow, 'run_codex', worker)
    flow.main()

    log = [e for e in flow.load_json(tmp_path / '.allforai/bootstrap/workflow.json')['transition_log']
           if e.get('node') == 'verify' and e.get('status') == 'failed']
    assert len(log) >= 2, log
    assert log[0]['qa_evidence']['binding'] == flow.binding_identity(tmp_path, 'verify')
    assert set(log[0]['qa_evidence']['produced']) == {'verify.json'}
    assert log[0]['qa_evidence']['produced']['verify.json'] == flow.file_digest(tmp_path / 'verify.json')
    assert log[1]['qa_evidence']['produced'] == {}, 'an attempt that wrote nothing produced nothing'


def test_a_report_edited_after_the_attempt_that_produced_it_is_refused(tmp_path):
    workflow = freshness_project(tmp_path)
    record_failed_qa(tmp_path, workflow)
    assert flow.open_repair_loops(tmp_path, workflow, {}).keys() == {'verify'}
    write(tmp_path / 'verify.json', {'status': 'failed', 'gaps': ['a different story']})
    assert flow.open_repair_loops(tmp_path, workflow, {}) == {}


@pytest.mark.parametrize("freshness", [
    None,
    False,
    {'admission': 'legacy', 'status': 'undeclared',
     'reason': 'Retained legacy node without source declarations; no provenance claimed'},
    {'admission': 'missing', 'status': 'undeclared'},
    {'admission': 'invalid', 'status': 'invalid'},
    {'admission': 'declared', 'status': 'uncertain', 'readiness_status': 'uncertain'},
    {'admission': 'declared', 'status': 'stale', 'readiness_status': 'stale',
     'diff': {'files': {'src/orders.py': 'changed'}}},
    {'admission': 'declared', 'status': 'stale', 'readiness_status': 'valid',
     'diff': {'evidence': 'unpublished'}, 'external': 'conflict'},
])
def test_automatic_repair_needs_positive_input_proof(freshness):
    # Every state that claims no provenance refuses the route, including the legacy
    # `undeclared` one: "no provenance claimed" is not "inputs are current".
    assert flow.qa_inputs_current(freshness) is False, freshness


def test_a_shared_repair_node_budgets_each_qa_node_separately(tmp_path, monkeypatch):
    # `repair` serves verifyA and verifyB. The declared budget is per QA node
    # (codex/meta-skill/knowledge/orchestrator-template.md), so attempts spent on
    # verifyA must leave verifyB its own.
    nodes = [
        {'node_id': 'verifyA', 'hard_blocked_by': [], 'exit_artifacts': ['verifyA.json']},
        {'node_id': 'verifyB', 'hard_blocked_by': [], 'exit_artifacts': ['verifyB.json']},
        {'node_id': 'repair', 'hard_blocked_by': ['verifyA', 'verifyB'], 'exit_artifacts': ['repair.json']},
    ]
    workflow = {'nodes': nodes, 'transition_log': [
        qa_failed('verifyA'), repair_delivered(), qa_failed('verifyA'), qa_failed('verifyB'),
    ]}
    write(tmp_path / '.allforai/bootstrap/workflow.json', workflow)
    write(tmp_path / '.allforai/bootstrap/unattended-run-readiness-spec.json', {
        'version': 1,
        'required_repair_loops': [{
            'scope': 'orders-export',
            'qa_node_ids': ['verifyA', 'verifyB'],
            'repair_node_id': 'repair',
            'closure_node_ids': [],
            'max_attempts': 1,
        }],
    })
    write(tmp_path / 'verifyA.json', {'status': 'failed'})
    write(tmp_path / 'verifyB.json', {'status': 'failed'})
    stamp_attempt_evidence(tmp_path, workflow, 'verifyA')
    stamp_attempt_evidence(tmp_path, workflow, 'verifyB')
    gate_by_ready_artifacts(tmp_path, monkeypatch)

    spent, _ = flow.repair_progress(workflow, 'repair', 'verifyA')
    assert spent == 1, 'verifyA spent its declared attempt'
    spent, _ = flow.repair_progress(workflow, 'repair', 'verifyB')
    assert spent == 0, "a sibling QA node's attempt is not verifyB's"
    assert flow.open_repair_loops(tmp_path, workflow, {}).keys() == {'verifyB'}
    assert 'verifyB' in flow.blocked_pending_nodes(tmp_path, workflow), \
        'verifyB waits for the repair its own budget still allows'
    assert flow.first_pending_node(tmp_path, workflow)['node_id'] == 'verifyA', \
        'verifyA spent its budget: it reruns instead of routing again'


def test_a_spent_budget_survives_a_restart(tmp_path, monkeypatch):
    # The budget is read from the durable transition_log, so a new driver process
    # resumes it instead of handing out the same attempts again.
    workflow = repair_project(tmp_path, qa_report={'status': 'failed'}, transition_log=[
        qa_failed('verify'), repair_delivered(), qa_failed('verify'), repair_delivered(),
        qa_failed('verify'),
    ])
    write(tmp_path / 'repair.json', {'status': 'passed'})
    gate_by_ready_artifacts(tmp_path, monkeypatch)
    assert flow.repair_progress(workflow, 'repair', 'verify') == (2, False)
    assert flow.first_pending_node(tmp_path, workflow)['node_id'] == 'verify'


def test_an_explicitly_invalid_budget_routes_nothing(tmp_path, monkeypatch):
    for max_attempts in (0, -1, '2', None, True, 2.5):
        assert flow.repair_budget({'max_attempts': max_attempts}) is None, max_attempts
    workflow = repair_project(tmp_path, qa_report={'status': 'failed'}, max_attempts=0)
    gate_by_ready_artifacts(tmp_path, monkeypatch)
    assert flow.open_repair_loops(tmp_path, workflow, {}) == {}
    assert flow.first_pending_node(tmp_path, workflow)['node_id'] == 'verify'


def test_an_omitted_budget_uses_the_documented_default(tmp_path, monkeypatch):
    assert flow.repair_budget({}) == flow.DEFAULT_REPAIR_ATTEMPTS == 3
    workflow = repair_project(tmp_path, qa_report={'status': 'failed'}, max_attempts=OMIT,
                              transition_log=[qa_failed('verify')])
    gate_by_ready_artifacts(tmp_path, monkeypatch)
    assert flow.first_pending_node(tmp_path, workflow)['node_id'] == 'repair'


def test_closure_never_starts_while_its_qa_node_is_failed(tmp_path, monkeypatch):
    workflow = repair_project(tmp_path, qa_report={'status': 'failed'},
                              transition_log=[qa_failed('verify')] + [repair_delivered()] * 2)
    write(tmp_path / 'repair.json', {'status': 'passed'})
    gate_by_ready_artifacts(tmp_path, monkeypatch)
    for _ in range(3):
        node = flow.first_pending_node(tmp_path, workflow)
        assert node['node_id'] != 'accept', 'closure requires a passing QA rerun'
    write(tmp_path / 'verify.json', {'status': 'passed'})
    assert flow.first_pending_node(tmp_path, workflow)['node_id'] == 'accept'


def test_an_undeclared_successor_never_runs_on_a_failed_dependency(tmp_path, monkeypatch):
    workflow = repair_project(tmp_path, qa_report={'status': 'failed'},
                              transition_log=[qa_failed('verify')])
    workflow['nodes'].append({'node_id': 'ship', 'hard_blocked_by': ['verify'],
                              'exit_artifacts': ['ship.json']})
    write(tmp_path / '.allforai/bootstrap/workflow.json', workflow)
    gate_by_ready_artifacts(tmp_path, monkeypatch)
    seen = set()
    for _ in range(3):
        seen.add(flow.first_pending_node(tmp_path, workflow)['node_id'])
    assert 'ship' not in seen


def test_blocked_pending_nodes_are_not_reported_as_a_finished_workflow(tmp_path, monkeypatch, capsys):
    workflow = {'nodes': [{'node_id': 'orphan', 'hard_blocked_by': ['ghost'],
                           'exit_artifacts': ['orphan.json']}], 'transition_log': []}
    write(tmp_path / '.allforai/bootstrap/workflow.json', workflow)
    gate_by_ready_artifacts(tmp_path, monkeypatch)
    assert flow.first_pending_node(tmp_path, workflow) is None
    assert 'orphan' in flow.blocked_pending_nodes(tmp_path, workflow)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, 'argv', ['flow.py'])
    monkeypatch.setattr(flow, 'run_preflight', lambda *a: 0)
    monkeypatch.setattr(flow, 'run_expanders', lambda *a: True)
    monkeypatch.setattr(flow, 'run_post_checks', lambda *a: True)
    assert flow.main() == 6
    assert json.loads(capsys.readouterr().err)['done'] is False


def test_missing_repair_spec_keeps_current_selection(tmp_path, monkeypatch):
    workflow = repair_project(tmp_path, qa_report={'status': 'failed'})
    (tmp_path / '.allforai/bootstrap/unattended-run-readiness-spec.json').write_text('{broken')
    gate_by_ready_artifacts(tmp_path, monkeypatch)
    assert flow.first_pending_node(tmp_path, workflow)['node_id'] == 'verify'
