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

ORCHESTRATOR_SCRIPTS = Path(__file__).resolve().parents[2] / 'claude/meta-skill/scripts/orchestrator'


def install_repair_ledger(tmp_path):
    """Ship the canonical helper into the project and record its provably new run.

    The generated runtime carries `repair_authorization.py` under
    `.allforai/bootstrap/scripts/`, and the driver reaches the ledger only through it.
    `initialize` reads the workflow itself and refuses a document that already shows
    execution, so a fixture that starts mid-run records its origin here, before it adds
    the transition log the run would have produced.
    """
    scripts = tmp_path / '.allforai/bootstrap/scripts'
    scripts.mkdir(parents=True, exist_ok=True)
    (scripts / 'repair_authorization.py').write_bytes(
        (ORCHESTRATOR_SCRIPTS / 'repair_authorization.py').read_bytes())
    verdict = flow.authorization_request(tmp_path, {'operation': 'initialize',
                                                    'run_id': 'fixture-run'})
    assert verdict and verdict['status'] == 'ok', verdict
    return verdict


def ledger_entries(tmp_path):
    return json.loads((tmp_path / flow.REPAIR_LEDGER).read_text())['authorizations']


def repair_project(tmp_path, *, qa_report=None, transition_log=None, max_attempts=2):
    """Four-node loop: implement -> verify(QA) -> repair -> accept(closure)."""
    nodes = [
        {'node_id': 'implement', 'hard_blocked_by': [], 'exit_artifacts': ['impl.json']},
        {'node_id': 'verify', 'hard_blocked_by': ['implement'], 'exit_artifacts': ['verify.json']},
        {'node_id': 'repair', 'hard_blocked_by': ['verify'], 'exit_artifacts': ['repair.json']},
        {'node_id': 'accept', 'hard_blocked_by': ['repair'], 'exit_artifacts': ['accept.json']},
    ]
    write(tmp_path / '.allforai/bootstrap/workflow.json', {'nodes': nodes, 'transition_log': []})
    install_repair_ledger(tmp_path)
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


def repair_dispatched(root, workflow, qa_node_id='verify', repair_node_id='repair',
                      settle='delivered'):
    """Charge and claim one repair attempt exactly as a real dispatch does.

    The budget ledger is the canonical `.allforai/bootstrap/repair-authorizations.json`,
    written through `repair_authorization.py` write-ahead of the executor, so a fixture
    that starts mid-run has to carry the same durable grant a real dispatch left. Passing
    `settle=None` leaves the grant unresolved — the state a killed driver leaves behind.
    """
    budget = flow.repair_budget(next(
        loop for loop in flow.declared_repair_loops(root)
        if str(loop['repair_node_id']) == repair_node_id
        and qa_node_id in flow.loop_nodes(loop, 'qa_node_ids', 'qa_nodes')))
    authorization_id = f'{repair_node_id}-{qa_node_id}-{len(ledger_entries(root)) + 1}'
    granted = flow.authorization_request(root, {
        'operation': 'authorize', 'run_id': 'fixture-run',
        'authorization_id': authorization_id, 'repair_node_id': repair_node_id,
        'obligations': [qa_node_id], 'budgets': {qa_node_id: budget}})
    assert granted and granted['status'] == 'authorized', granted
    claimed = flow.authorization_request(root, {'operation': 'start', 'run_id': 'fixture-run',
                                                'authorization_id': authorization_id})
    assert claimed and claimed['execution_allowed'] is True, claimed
    if settle is not None:
        flow.authorization_request(root, {'operation': 'settle', 'outcome': settle,
                                          'authorization_id': authorization_id})
    return workflow


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
    repair_dispatched(tmp_path, workflow)          # the attempt that delivered was charged
    write(tmp_path / 'repair.json', {'status': 'passed'})
    gate_by_ready_artifacts(tmp_path, monkeypatch)
    node = flow.first_pending_node(tmp_path, workflow)
    assert node['node_id'] == 'verify', 'a delivered repair is answered by the QA rerun, not another repair'
    workflow['transition_log'].append(qa_failed('verify'))
    stamp_attempt_evidence(tmp_path, workflow)
    node = flow.first_pending_node(tmp_path, workflow)
    assert node['node_id'] == 'repair', 'the rerun failed again: attempt 2 of 2 is still declared'
    repair_dispatched(tmp_path, workflow)
    workflow['transition_log'].extend([repair_delivered(), qa_failed('verify')])
    stamp_attempt_evidence(tmp_path, workflow)
    # Budget spent and the rerun failed again. There is no attempt left that could fix
    # it, so the obligation is blocked and reported rather than re-run into the same
    # failure — and its closure is never released (ADR 0005; the Claude engine reaches
    # the same verdict through `blockedFailures`).
    assert flow.first_pending_node(tmp_path, workflow) is None
    blocked = flow.blocked_pending_nodes(tmp_path, workflow)
    assert 'verify' in blocked, 'an exhausted obligation is blocked, never accepted'
    assert 'accept' in blocked, 'and its closure node stays shut'


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
    install_repair_ledger(tmp_path)
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
    install_repair_ledger(tmp_path)
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
                       max_iterations=None, on_safety_warning='continue',
                       on_needs_iteration='halt_with_report'):
    """Run `flow.main()` with the real node selection, recording what it actually chose.

    `first_pending_node` is wrapped, not replaced: the driver picks nodes through
    `open_repair_loops` exactly as it does in a run, and the spy only records the choice.
    Preflight and expanders are stubbed because they are not what is under test.
    """
    import shutil
    scripts = tmp_path / '.allforai/bootstrap/scripts'
    shutil.copy2(ORCHESTRATOR / 'product_intent.py', scripts)
    write(tmp_path / '.allforai/bootstrap/run-policy.json', {
        'on_repeated_failure': 'halt', 'on_needs_iteration': on_needs_iteration,
        'on_safety_warning': on_safety_warning})
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
    """Four ways to not deliver. None releases the QA rerun; each still spends an attempt.

    Delivery decides whether the QA node re-runs. It does not decide the budget: an
    attempt is charged for the dispatch, so a repair that errors or writes nothing costs
    exactly what one that delivered costs. That is what bounds the loop — the declared
    `max_attempts` (2 here) is spent, and the obligation is then blocked rather than
    re-run: nothing is left that could fix it, and it is never accepted either.
    """
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
    # Nothing the repair did released the QA node: every declared attempt was dispatched,
    # and the QA node never ran a second time because no attempt was left to judge.
    assert executed.count('repair') == 2, \
        f'the declared attempts were not all dispatched: {executed}'
    assert executed.count('verify') == 1, \
        f'the QA node was released by a non-delivery: {executed}'
    spent, answered = flow.repair_progress(tmp_path, current, 'repair', 'verify')
    assert spent == 2, f'{mode} did not spend its budgeted attempts: {ledger_entries(tmp_path)}'
    assert answered is False, f'{mode} delivered nothing for the QA node to re-verify'
    assert flow.open_repair_loops(tmp_path, current, {}) == {}, 'and the budget is spent'
    assert 'verify' in flow.blocked_pending_nodes(tmp_path, current), \
        'the exhausted obligation is reported, not silently dropped'


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
    delivered, answered = flow.repair_progress(tmp_path, current, 'repair', 'verify')
    assert delivered == 2, f'max_attempts is 2: {executed}'
    assert executed.count('repair') == 2, executed
    assert 'accept' not in executed, 'an unrepaired QA failure never reaches closure'
    # A restart re-derives the same spent budget from the same durable log.
    reloaded = flow.load_json(tmp_path / '.allforai/bootstrap/workflow.json')
    assert flow.repair_progress(tmp_path, reloaded, 'repair', 'verify') == (delivered, answered)
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
    write(tmp_path / '.allforai/bootstrap/workflow.json', {'nodes': nodes, 'transition_log': []})
    install_repair_ledger(tmp_path)
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
    repair_dispatched(tmp_path, workflow, 'verifyA')   # only verifyA's attempt was charged
    gate_by_ready_artifacts(tmp_path, monkeypatch)

    spent, _ = flow.repair_progress(tmp_path, workflow, 'repair', 'verifyA')
    assert spent == 1, 'verifyA spent its declared attempt'
    spent, _ = flow.repair_progress(tmp_path, workflow, 'repair', 'verifyB')
    assert spent == 0, "a sibling QA node's attempt is not verifyB's"
    assert flow.open_repair_loops(tmp_path, workflow, {}).keys() == {'verifyB'}
    assert 'verifyB' in flow.blocked_pending_nodes(tmp_path, workflow), \
        'verifyB waits for the repair its own budget still allows'
    assert 'verifyA' in flow.blocked_pending_nodes(tmp_path, workflow), \
        'verifyA spent its budget: it is blocked, and a spent obligation is never accepted'
    assert flow.first_pending_node(tmp_path, workflow)['node_id'] == 'repair', \
        "the shared repair still runs for verifyB, whose own budget is untouched"


def test_a_spent_budget_survives_a_restart(tmp_path, monkeypatch):
    # The budget is read from the durable transition_log, so a new driver process
    # resumes it instead of handing out the same attempts again.
    workflow = repair_project(tmp_path, qa_report={'status': 'failed'}, transition_log=[
        qa_failed('verify'), repair_delivered(), qa_failed('verify'), repair_delivered(),
        qa_failed('verify'),
    ])
    repair_dispatched(tmp_path, workflow)
    repair_dispatched(tmp_path, workflow)
    write(tmp_path / 'repair.json', {'status': 'passed'})
    gate_by_ready_artifacts(tmp_path, monkeypatch)
    assert flow.repair_progress(tmp_path, workflow, 'repair', 'verify') == (2, False)
    assert flow.first_pending_node(tmp_path, workflow) is None
    assert 'verify' in flow.blocked_pending_nodes(tmp_path, workflow), \
        'a restart resumes the spent budget and blocks, it does not hand out a third attempt'


def test_a_repair_dispatch_is_charged_before_its_executor_runs(tmp_path, monkeypatch):
    """Write-ahead accounting: the ledger entry is on disk while the executor is running.

    This is the whole reason the attempt is charged at the dispatch rather than at the
    delivery. An interruption between the two — a kill, a timeout, a host that dies — must
    leave the attempt spent, because the work it authorized may already have edited the
    tree. Over-counting the one interrupted attempt is safe; re-granting it is not.
    """
    routing_project(tmp_path)
    charged_while_running = []

    def executor(project_root, node_id, attempt):
        if node_id == 'verify':
            write(project_root / 'verify.json', {'status': 'failed', 'gaps': ['missing column'],
                                                 'attempt': attempt})
        elif node_id == 'repair':
            # What a restart would read if this process died right here: the canonical
            # ledger, not this driver's memory of what it meant to charge.
            charged_while_running.append(
                (flow.repair_attempts_spent(project_root, 'repair', 'verify'),
                 [e['state'] for e in ledger_entries(project_root)]))
            write(project_root / 'repair.json', {'status': 'passed', 'attempt': attempt})
        try_publish_evidence(project_root, node_id)

    drive_real_routing(tmp_path, monkeypatch, executor)
    assert [spent for spent, _ in charged_while_running] == [1, 2], \
        f'each dispatch must already be charged while its own executor runs: {charged_while_running}'
    # And the launch claim is durable too, so a restart cannot run the same attempt again.
    assert [states[-1] for _, states in charged_while_running] == ['started', 'started'], \
        f'the execution claim must be on disk before the executor: {charged_while_running}'
    assert [e['state'] for e in ledger_entries(tmp_path)] == ['settled', 'settled'], \
        'an attempt this driver watched finish is settled, and settling refunds nothing'


def test_an_interrupted_repair_dispatch_does_not_get_its_attempt_back(tmp_path, monkeypatch):
    """The charge survives the process that made it; a restart resumes the same budget."""
    routing_project(tmp_path)

    def executor(project_root, node_id, attempt):
        if node_id == 'verify':
            write(project_root / 'verify.json', {'status': 'failed', 'gaps': ['missing column'],
                                                 'attempt': attempt})
        elif node_id == 'repair':
            raise RuntimeError('killed between the authorization and the work')

    drive_real_routing(tmp_path, monkeypatch, executor, failing_nodes={'repair'})
    reloaded = flow.load_json(tmp_path / '.allforai/bootstrap/workflow.json')
    spent, _ = flow.repair_progress(tmp_path, reloaded, 'repair', 'verify')
    assert spent == 2, f'an interrupted dispatch still spent its attempt: {ledger_entries(tmp_path)}'
    assert flow.open_repair_loops(tmp_path, reloaded, {}) == {}, \
        'a restart resumes the spent budget instead of handing the attempts out again'


@pytest.mark.parametrize("damage", [
    'not a ledger document',
    json.dumps({'ledger_version': 99, 'run_id': 'r', 'origin': {}, 'authorizations': []}),
    json.dumps({'ledger_version': 1, 'run_id': '', 'origin': {'kind': 'new_run'}, 'authorizations': []}),
    json.dumps({'ledger_version': 1, 'run_id': 'r', 'origin': {'kind': 'new_run'},
                'authorizations': 'none'}),
    json.dumps({'ledger_version': 1, 'run_id': 'r', 'origin': {'kind': 'new_run'},
                'authorizations': [{'authorization_id': 'a'}]}),
])
def test_an_unreadable_repair_ledger_dispatches_nothing(tmp_path, monkeypatch, damage):
    """The spent budget cannot be read, so no node runs — never a fresh budget.

    Restarting the count would hand out attempts whose work may already be in the tree.
    The refusal is the canonical helper's, read through the driver rather than
    re-decided by it.
    """
    workflow = repair_project(tmp_path, qa_report={'status': 'failed'},
                              transition_log=[qa_failed('verify')])
    (tmp_path / flow.REPAIR_LEDGER).write_text(damage)
    gate_by_ready_artifacts(tmp_path, monkeypatch)
    assert flow.ledger_consumption(tmp_path) is None
    assert flow.repair_ledger_unreadable(tmp_path, workflow) is True
    assert flow.first_pending_node(tmp_path, workflow) is None
    assert set(flow.blocked_pending_nodes(tmp_path, workflow)) == \
        {'implement', 'verify', 'repair', 'accept'}, 'no node of any kind is dispatched'


def test_a_missing_ledger_on_a_run_with_history_blocks_instead_of_starting_at_zero(tmp_path, monkeypatch):
    """Absence of records is not proof of unused budget (ADR 0005/0007).

    The workflow already shows execution, so `initialize` refuses and the driver has no
    trustworthy accounting. It blocks; it never silently resets the run to zero.
    """
    workflow = repair_project(tmp_path, qa_report={'status': 'failed'},
                              transition_log=[qa_failed('verify')])
    (tmp_path / flow.REPAIR_LEDGER).unlink()
    gate_by_ready_artifacts(tmp_path, monkeypatch)
    assert flow.ledger_consumption(tmp_path) is None
    assert flow.repair_attempts_spent(tmp_path, 'repair', 'verify') is None
    assert flow.repair_ledger_unreadable(tmp_path, workflow) is True
    assert flow.first_pending_node(tmp_path, workflow) is None


def test_a_provably_new_run_starts_at_zero_and_is_recorded_as_such(tmp_path, monkeypatch):
    """The one case that may start at zero: a workflow the helper itself proves untouched."""
    nodes = [{'node_id': 'verify', 'hard_blocked_by': [], 'exit_artifacts': ['verify.json']},
             {'node_id': 'repair', 'hard_blocked_by': ['verify'], 'exit_artifacts': ['repair.json']}]
    write(tmp_path / '.allforai/bootstrap/workflow.json', {'nodes': nodes, 'transition_log': []})
    write(tmp_path / '.allforai/bootstrap/unattended-run-readiness-spec.json', {
        'version': 1, 'required_repair_loops': [{'scope': 's', 'qa_node_ids': ['verify'],
        'repair_node_id': 'repair', 'closure_node_ids': [], 'max_attempts': 2}]})
    scripts = tmp_path / '.allforai/bootstrap/scripts'
    scripts.mkdir(parents=True, exist_ok=True)
    (scripts / 'repair_authorization.py').write_bytes(
        (ORCHESTRATOR_SCRIPTS / 'repair_authorization.py').read_bytes())
    assert not (tmp_path / flow.REPAIR_LEDGER).exists()
    consumption = flow.ledger_consumption(tmp_path)
    assert consumption and consumption['origin'] == 'new_run'
    assert flow.repair_attempts_spent(tmp_path, 'repair', 'verify') == 0
    ledger = json.loads((tmp_path / flow.REPAIR_LEDGER).read_text())
    assert ledger['origin']['proof']['kind'] == 'verified_untouched_workflow'


def test_an_explicitly_invalid_budget_blocks_a_failed_qa_node(tmp_path, monkeypatch):
    """An unusable `max_attempts` is a planning error, not a slower loop.

    The QA node has failed and its declared loop can never bound a repair, so re-running
    it would reproduce the same failure with nothing able to fix it. It is blocked and the
    run says why — the same terminal answer `runEngine` gives on the Claude host.
    """
    workflow = repair_project(tmp_path, qa_report={'status': 'failed'}, max_attempts=0,
                              transition_log=[qa_failed('verify')])
    gate_by_ready_artifacts(tmp_path, monkeypatch)
    assert flow.unbounded_repair_loops(tmp_path) == ['repair']
    assert flow.open_repair_loops(tmp_path, workflow, {}) == {}, 'no repair is routed'
    assert flow.first_pending_node(tmp_path, workflow) is None, \
        'and the failed QA node is not quietly re-run instead'
    assert 'verify' in flow.blocked_pending_nodes(tmp_path, workflow)


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


# --- common execution-contract scenarios (claude/meta-skill/tests/fixtures) -----------
# The fixture states the business decision both hosts must reach. Each test drives the
# real Codex selection or the real driver and compares what it did to that decision; the
# fixture is never asserted against itself.

SCENARIOS = {s['id']: s for s in json.loads(
    (Path(__file__).resolve().parents[2] /
     'claude/meta-skill/tests/fixtures/execution-contract-scenarios.json').read_text())['scenarios']}


def install_run_safety(tmp_path):
    """Ship the canonical quarantine helper the driver calls on a halt."""
    scripts = tmp_path / '.allforai/bootstrap/scripts'
    scripts.mkdir(parents=True, exist_ok=True)
    (scripts / 'run_safety.py').write_bytes((ORCHESTRATOR_SCRIPTS / 'run_safety.py').read_bytes())


def test_a_safety_warning_raised_by_the_executor_stops_before_the_completion(tmp_path, monkeypatch):
    """The halt is checked after the executor and before the node is recorded completed.

    Answering it on the next iteration would be too late: the node would already be
    completed and would already have released its successors. Codex cannot cancel an
    executor that has finished, so its outputs are quarantined rather than accepted.
    """
    scenario = SCENARIOS['late_wave_safety_halt']
    routing_project(tmp_path)
    install_run_safety(tmp_path)

    def executor(project_root, node_id, attempt):
        write(project_root / f'{node_id}.json', {'status': 'passed'})
        write(project_root / '.allforai/bootstrap/run-warnings.json',
              {'warnings': ['workspace escape attempted']})

    selected, executed = drive_real_routing(tmp_path, monkeypatch, executor,
                                            on_safety_warning='halt')
    current = flow.load_json(tmp_path / '.allforai/bootstrap/workflow.json')
    latest = [e for e in current['transition_log'] if e['node'] == executed[0]][-1]
    assert latest['status'] == 'failed', 'a quarantined attempt is never recorded completed'
    assert executed == executed[:1], f'no dispatch followed the halt: {executed}'
    assert scenario['expect']['quarantine_required'] is True
    marker = json.loads((tmp_path / flow.SAFETY_QUARANTINE).read_text())
    assert executed[0] in marker['node_ids'], 'the attempt\'s own outputs are fenced'
    assert (tmp_path / f'{executed[0]}.json').exists(), 'quarantine preserves outputs, never deletes them'


def test_a_safety_halt_stops_every_branch_not_only_the_one_that_raised_it(tmp_path, monkeypatch):
    """`new_dispatch_allowed: false` is run-wide: an untouched independent branch stops too."""
    scenario = SCENARIOS['late_wave_safety_halt']
    workflow = repair_project(tmp_path, qa_report={'status': 'failed'},
                              transition_log=[qa_failed('verify')])
    workflow['nodes'].append({'node_id': 'independent', 'hard_blocked_by': [],
                              'exit_artifacts': ['independent.json']})
    write(tmp_path / '.allforai/bootstrap/workflow.json', workflow)
    gate_by_ready_artifacts(tmp_path, monkeypatch)
    assert flow.first_pending_node(tmp_path, workflow) is not None, 'dispatchable before the halt'
    write(tmp_path / flow.SAFETY_QUARANTINE, {'schema_version': 1, 'status': 'quarantined',
                                              'events': [], 'node_ids': ['verify']})
    assert scenario['expect']['new_dispatch_allowed'] is False
    assert flow.first_pending_node(tmp_path, workflow) is None
    assert 'independent' in flow.blocked_pending_nodes(tmp_path, workflow), \
        'a branch that never failed is stopped by the run-wide halt too'


def test_a_safety_halt_is_not_answered_by_a_repair_route(tmp_path, monkeypatch):
    """`hard_qa_with_safety_warning`: a halt is not an ordinary QA failure."""
    scenario = SCENARIOS['hard_qa_with_safety_warning']
    workflow = repair_project(tmp_path, qa_report={'status': 'failed'},
                              transition_log=[qa_failed('verify')])
    gate_by_ready_artifacts(tmp_path, monkeypatch)
    assert flow.open_repair_loops(tmp_path, workflow, {}).keys() == {'verify'}
    write(tmp_path / flow.SAFETY_QUARANTINE, {'schema_version': 1, 'status': 'quarantined',
                                              'events': [], 'node_ids': ['verify']})
    assert scenario['expect']['repair_route_allowed'] is False
    assert flow.open_repair_loops(tmp_path, workflow, {}) == {}
    assert scenario['expect']['new_dispatch_allowed'] is False
    assert flow.first_pending_node(tmp_path, workflow) is None


def test_an_ordinary_qa_failure_blocks_its_chain_but_not_an_independent_branch(tmp_path, monkeypatch):
    """`ordinary_qa_failure_with_independent_branch`: block the chain, keep the rest moving."""
    scenario = SCENARIOS['ordinary_qa_failure_with_independent_branch']
    workflow = repair_project(tmp_path, qa_report={'status': 'failed'},
                              transition_log=[qa_failed('verify')])
    workflow['nodes'].append({'node_id': 'independent', 'hard_blocked_by': [],
                              'exit_artifacts': ['independent.json']})
    write(tmp_path / '.allforai/bootstrap/workflow.json', workflow)
    gate_by_ready_artifacts(tmp_path, monkeypatch)
    blocked = flow.blocked_pending_nodes(tmp_path, workflow)
    assert scenario['expect']['failed_qa_successors_allowed'] is False
    assert 'accept' in blocked, 'the closure node downstream of the failed QA stays shut'
    assert scenario['expect']['independent_branch_allowed'] is True
    assert 'independent' not in blocked, 'an unrelated branch keeps running'
    assert scenario['expect']['final_acceptance'] is False
    assert blocked, 'and the run cannot finish while the obligation is open'


def test_a_shared_repair_charges_only_the_obligations_that_still_have_budget(tmp_path, monkeypatch):
    """`shared_repair_asymmetric_budget`, driven through the canonical ledger.

    qa-a is exhausted and qa-b is not. The dispatch charges qa-b alone: an exhausted
    sibling is never charged again, and it is never discharged by the attempt that
    answers another obligation either.
    """
    scenario = SCENARIOS['shared_repair_asymmetric_budget']
    given, expect = scenario['given'], scenario['expect']
    nodes = [{'node_id': 'qa-a', 'hard_blocked_by': [], 'exit_artifacts': ['qa-a.json']},
             {'node_id': 'qa-b', 'hard_blocked_by': [], 'exit_artifacts': ['qa-b.json']},
             {'node_id': 'repair', 'hard_blocked_by': ['qa-a', 'qa-b'], 'exit_artifacts': ['repair.json']}]
    write(tmp_path / '.allforai/bootstrap/workflow.json', {'nodes': nodes, 'transition_log': []})
    install_repair_ledger(tmp_path)
    workflow = {'nodes': nodes, 'transition_log': [qa_failed('qa-a'), qa_failed('qa-b')]}
    write(tmp_path / '.allforai/bootstrap/workflow.json', workflow)
    write(tmp_path / '.allforai/bootstrap/unattended-run-readiness-spec.json', {
        'version': 1, 'required_repair_loops': [{
            'scope': 'shared', 'qa_node_ids': ['qa-a', 'qa-b'], 'repair_node_id': 'repair',
            'closure_node_ids': [], 'max_attempts': given['budgets']['qa-a']}]})
    for qa_node_id in ('qa-a', 'qa-b'):
        write(tmp_path / f'{qa_node_id}.json', {'status': 'failed'})
        stamp_attempt_evidence(tmp_path, workflow, qa_node_id)
    for _ in range(given['spent']['qa-a']):
        repair_dispatched(tmp_path, workflow, 'qa-a')
    for _ in range(given['spent']['qa-b']):
        repair_dispatched(tmp_path, workflow, 'qa-b')
    gate_by_ready_artifacts(tmp_path, monkeypatch)

    routed = flow.qa_nodes_routed_to(tmp_path, workflow, 'repair')
    assert sorted(routed) == expect['eligible_obligations'], routed
    assert sorted(flow.eligible_obligations(tmp_path, workflow, 'repair', routed)) == \
        expect['eligible_obligations'], 'only the funded obligation may be charged'
    grant = flow.authorize_repair_dispatch(tmp_path, workflow, 'repair', routed)
    assert grant and grant['obligations'] == expect['eligible_obligations']
    for blocked_obligation in expect['blocked_obligations']:
        assert flow.repair_attempts_spent(tmp_path, 'repair', blocked_obligation) == \
            given['spent'][blocked_obligation], 'the exhausted sibling was not charged again'
        assert blocked_obligation in flow.blocked_pending_nodes(tmp_path, workflow)
    assert expect['final_acceptance'] is False
    assert flow.blocked_pending_nodes(tmp_path, workflow), 'the run cannot finish around it'


def test_a_replayed_authorization_charges_nothing_and_never_re_executes(tmp_path):
    """`duplicate_authorization` and `conflicting_authorization_replay` at the driver's call."""
    duplicate, conflicting = SCENARIOS['duplicate_authorization'], SCENARIOS['conflicting_authorization_replay']
    workflow = repair_project(tmp_path, qa_report={'status': 'failed'},
                              transition_log=[qa_failed('verify')])
    request = {'operation': 'authorize', 'run_id': 'fixture-run', 'authorization_id': 'once',
               'repair_node_id': 'repair', 'obligations': ['verify'], 'budgets': {'verify': 2}}
    assert flow.authorization_request(tmp_path, request)['status'] == 'authorized'
    spent = flow.repair_attempts_spent(tmp_path, 'repair', 'verify')
    replay = flow.authorization_request(tmp_path, request)
    assert replay['status'] == 'replayed'
    assert replay['execution_allowed'] is False, duplicate['expect']['replay_execution_allowed']
    assert flow.repair_attempts_spent(tmp_path, 'repair', 'verify') == spent, \
        duplicate['expect']['additional_charges']
    changed = {**request, 'budgets': {'verify': 5}}
    assert flow.authorization_request(tmp_path, changed)['status'] == 'payload_conflict', \
        conflicting['expect']['blocked']
    assert flow.repair_attempts_spent(tmp_path, 'repair', 'verify') == spent, \
        conflicting['expect']['additional_charges']
    first = flow.authorization_request(tmp_path, {'operation': 'start', 'run_id': 'fixture-run',
                                                  'authorization_id': 'once'})
    assert first['execution_allowed'] is True, 'the first claim runs'
    again = flow.authorization_request(tmp_path, {'operation': 'start', 'run_id': 'fixture-run',
                                                  'authorization_id': 'once'})
    assert again['execution_allowed'] is False, 'a replayed claim never re-executes'


def test_an_unresolved_authorization_blocks_the_next_dispatch_instead_of_replaying_it(tmp_path, monkeypatch):
    """`unknown_execution_after_crash`: no automatic refund, no automatic re-execution."""
    scenario = SCENARIOS['unknown_execution_after_crash']
    workflow = repair_project(tmp_path, qa_report={'status': 'failed'},
                              transition_log=[qa_failed('verify')])
    repair_dispatched(tmp_path, workflow, settle=None)   # killed between the claim and the outcome
    gate_by_ready_artifacts(tmp_path, monkeypatch)
    spent = flow.repair_attempts_spent(tmp_path, 'repair', 'verify')
    assert spent == 1, scenario['expect']['automatic_refund']
    assert flow.authorize_repair_dispatch(tmp_path, workflow, 'repair', ['verify']) is None, \
        scenario['expect']['automatic_reexecution']
    assert flow.repair_attempts_spent(tmp_path, 'repair', 'verify') == spent, \
        'a refused dispatch charges nothing'
    assert scenario['expect']['reconciliation_required'] is True
    unresolved = flow.ledger_consumption(tmp_path)['unresolved']
    assert [entry['state'] for entry in unresolved] == ['started']


def test_a_declared_per_qa_budget_is_not_curtailed_by_the_generic_caps(tmp_path):
    """An explicit `max_attempts` outranks the generic supervisor and stagnation caps.

    Both stay finite: they rise only to what the plan itself declared.
    """
    repair_project(tmp_path, qa_report={'status': 'failed'}, max_attempts=6)
    assert flow.MAX_CONSECUTIVE_FAILURES_PER_NODE == 3 and flow.MAX_STAGNANT_ITERATIONS == 5
    for node_id in ('verify', 'repair'):
        assert flow.failure_threshold(tmp_path, node_id) == 7, \
            'a declared 6-attempt loop is not ended at the generic 3'
    assert flow.failure_threshold(tmp_path, 'implement') == 3, \
        'a node no loop declared keeps the generic backstop'
    assert flow.stagnation_limit(tmp_path) == 13, \
        'two transitions per authorized attempt, plus the failure that opened the loop'


def test_a_smaller_declared_budget_never_raises_the_generic_backstop(tmp_path):
    repair_project(tmp_path, qa_report={'status': 'failed'}, max_attempts=1)
    assert flow.failure_threshold(tmp_path, 'verify') == flow.MAX_CONSECUTIVE_FAILURES_PER_NODE
    assert flow.stagnation_limit(tmp_path) == flow.MAX_STAGNANT_ITERATIONS


# --- role overlap, uncertain execution, and the fences around them ---------------------
# A node may hold different roles in different loops (ADR 0006). These drive the real
# selection and the real driver through that shape; the ledger and the quarantine helper
# are the canonical ones.


def overlap_project(tmp_path, *, spent_on_shared=1, budget_b=1):
    """Two loops sharing one node: `shared` repairs loop A and is loop B's QA obligation.

    `validate_bootstrap` refuses a repair node that is its own loop's QA or closure node,
    and nothing refuses this shape — ADR 0006 keeps cross-loop roles supported rather than
    banning a valid graph to hide a failure-accounting defect.
    """
    nodes = [
        {'node_id': 'qa1', 'hard_blocked_by': [], 'exit_artifacts': ['qa1.json']},
        {'node_id': 'shared', 'hard_blocked_by': ['qa1'], 'exit_artifacts': ['shared.json']},
        {'node_id': 'fixer', 'hard_blocked_by': ['shared'], 'exit_artifacts': ['fixer.json']},
        {'node_id': 'closeA', 'hard_blocked_by': ['qa1', 'shared'], 'exit_artifacts': ['closeA.json']},
        {'node_id': 'closeB', 'hard_blocked_by': ['shared', 'fixer'], 'exit_artifacts': ['closeB.json']},
    ]
    write(tmp_path / '.allforai/bootstrap/workflow.json', {'nodes': nodes, 'transition_log': []})
    install_repair_ledger(tmp_path)
    write(tmp_path / '.allforai/bootstrap/unattended-run-readiness-spec.json', {
        'version': 1, 'required_repair_loops': [
            {'scope': 'A', 'qa_node_ids': ['qa1'], 'repair_node_id': 'shared',
             'closure_node_ids': ['closeA'], 'max_attempts': 2},
            {'scope': 'B', 'qa_node_ids': ['shared'], 'repair_node_id': 'fixer',
             'closure_node_ids': ['closeB'], 'max_attempts': budget_b}]})
    workflow = {'nodes': nodes, 'transition_log': [qa_failed('qa1'), qa_failed('shared')]}
    write(tmp_path / 'qa1.json', {'status': 'failed'})
    write(tmp_path / 'shared.json', {'status': 'failed'})
    write(tmp_path / '.allforai/bootstrap/workflow.json', workflow)
    stamp_attempt_evidence(tmp_path, workflow, 'qa1')
    stamp_attempt_evidence(tmp_path, workflow, 'shared')
    for _ in range(spent_on_shared):
        repair_dispatched(tmp_path, workflow, qa_node_id='shared', repair_node_id='fixer',
                          settle='failed')
    return workflow


def test_a_node_blocked_as_an_obligation_is_not_dispatched_in_its_repair_role(tmp_path, monkeypatch):
    """`shared` owes loop B an obligation it has no budget left for, and repairs loop A.

    Selecting it for the repair role would put it in front of the executor with its own
    QA report as an exit artifact: the dispatch loop A pays for would write loop B's
    verdict. Success in one role never cancels another role's blocker (ADR 0006).
    """
    workflow = overlap_project(tmp_path)
    gate_by_ready_artifacts(tmp_path, monkeypatch)
    assert flow.repair_attempts_spent(tmp_path, 'fixer', 'shared') == 1, 'loop B is spent'
    assert flow.exhausted_obligations(tmp_path, workflow) == ['shared']
    assert 'shared' in flow.blocked_pending_nodes(tmp_path, workflow)
    selected = flow.first_pending_node(tmp_path, workflow)
    assert selected is None or selected['node_id'] != 'shared', \
        'an exhausted obligation is not dispatchable, whatever else the node also is'


def test_a_repair_role_dispatch_never_discharges_the_nodes_own_exhausted_obligation(tmp_path, monkeypatch, capsys):
    """End to end: the run may not finish around loop B's unsatisfied obligation.

    Nor may loop B's repair node run again once its budget is spent: a dispatch nothing
    authorized is an unpaid attempt, not a free one.
    """
    overlap_project(tmp_path)
    gate_by_ready_artifacts(tmp_path, monkeypatch)

    def executor(project_root, node_id, attempt):
        write(project_root / f'{node_id}.json', {'status': 'passed'})

    selected, executed = drive_real_routing(tmp_path, monkeypatch, executor, max_iterations=12)
    out = capsys.readouterr().out
    assert '"done": true' not in out, 'an exhausted obligation is refused, never accepted'
    assert 'shared' not in executed and 'fixer' not in executed, executed
    entries = [(e['repair_node_id'], e['obligations']) for e in ledger_entries(tmp_path)]
    assert entries == [('fixer', ['shared'])], f'no further attempt was charged: {entries}'


def test_an_exhausted_obligation_stays_blocked_when_its_report_is_made_to_look_ready(tmp_path, monkeypatch):
    """A ready exit artifact is not a QA attempt; only the recorded attempt satisfies it.

    Its latest recorded attempt failed and no budget is left, so the obligation stands
    however passed its report now reads — otherwise anything able to write that file could
    discharge it. The loop's repair node is blocked with it: nothing is left to pay for a
    dispatch, so it never runs as an ordinary pending node either.
    """
    workflow = overlap_project(tmp_path)
    write(tmp_path / 'shared.json', {'status': 'passed'})     # not written by a QA attempt
    gate_by_ready_artifacts(tmp_path, monkeypatch)
    blocked = flow.blocked_pending_nodes(tmp_path, workflow)
    assert 'shared' in blocked, blocked
    assert 'fixer' in blocked, f'a dead loop\'s repair node is never dispatched unpaid: {blocked}'
    selected = flow.first_pending_node(tmp_path, workflow)
    assert selected is None or selected['node_id'] not in {'shared', 'fixer'}, selected


def test_a_halt_whose_quarantine_cannot_be_published_still_fences_the_next_start(tmp_path, monkeypatch, capsys):
    """`run_safety.py` absent: the canonical marker is not written, and the run is fenced.

    Without a fence the only durable record of the halt is the warnings file a worker
    writes and a Run Policy a user can edit, and the quarantined outputs read as a
    completed node on the next start. `safety_quarantine.lock` is what `run_safety.py`
    itself leaves for a quarantine it could not publish, and it is what
    `validate_unattended_readiness.py` refuses, so the driver leaves it too.
    """
    routing_project(tmp_path)                       # deliberately no install_run_safety

    def executor(project_root, node_id, attempt):
        write(project_root / f'{node_id}.json', {'status': 'passed'})
        write(project_root / '.allforai/bootstrap/run-warnings.json',
              {'warnings': ['workspace escape attempted']})

    selected, executed = drive_real_routing(tmp_path, monkeypatch, executor,
                                            on_safety_warning='halt')
    payload = json.loads(capsys.readouterr().err.strip().splitlines()[-1])
    assert payload['quarantine_persisted'] is False, 'persistence is reported, never assumed'
    assert payload['halt_fenced'] is True
    assert not (tmp_path / flow.SAFETY_QUARANTINE).exists(), 'no marker is invented'
    assert (tmp_path / flow.SAFETY_LOCK).exists()
    assert flow.safety_halted(tmp_path), 'the halt survives this process'
    workflow = flow.load_json(tmp_path / '.allforai/bootstrap/workflow.json')
    gate_by_ready_artifacts(tmp_path, monkeypatch)
    assert flow.first_pending_node(tmp_path, workflow) is None, \
        'and the quarantined outputs are not read as a completed node on the next start'
    write(tmp_path / '.allforai/bootstrap/run-warnings.json', {'warnings': []})
    assert flow.safety_halted(tmp_path), \
        'clearing the warnings a worker wrote does not release a quarantine'


def test_an_unresolved_authorization_refuses_the_whole_run_before_the_first_dispatch(tmp_path, monkeypatch, capsys):
    """Uncertain execution is not an ordinary QA failure and is not blocked branch by branch.

    A grant with no recorded outcome may already have edited the tree, so no branch may
    proceed on the assumption that it did not — including one that never failed. The
    refusal is global, it happens before anything is dispatched, and it is reported as
    reconciliation rather than as a QA verdict (ADR 0006, ADR 0007).
    """
    workflow = repair_project(tmp_path, qa_report={'status': 'failed'},
                              transition_log=[qa_failed('verify')])
    workflow['nodes'].append({'node_id': 'independent', 'hard_blocked_by': [],
                              'exit_artifacts': ['independent.json']})
    write(tmp_path / '.allforai/bootstrap/workflow.json', workflow)
    repair_dispatched(tmp_path, workflow, settle=None)   # killed between claim and outcome
    gate_by_ready_artifacts(tmp_path, monkeypatch)

    def executor(project_root, node_id, attempt):
        write(project_root / f'{node_id}.json', {'status': 'passed'})

    selected, executed = drive_real_routing(tmp_path, monkeypatch, executor, max_iterations=6)
    payload = json.loads(capsys.readouterr().err.strip().splitlines()[-1])
    assert executed == [], f'nothing runs while an execution is unaccounted for: {executed}'
    assert 'independent' in payload['blocked_nodes'], 'the refusal is run-wide'
    assert payload['unresolved_repair_authorizations'], payload
    assert 'reconciled' in payload['uncertain_execution']
    assert 'exhausted_obligations' not in payload, \
        'an unresolved authorization is not reported as a spent budget'
    assert flow.repair_attempts_spent(tmp_path, 'repair', 'verify') == 1, 'and nothing is refunded'


def test_an_unconfirmed_settlement_stops_the_run_before_the_node_is_completed(tmp_path, monkeypatch, capsys):
    """The ledger is the record of what a dispatch did; an unrecorded outcome is not one.

    Completing the node here would accept work whose authorization stays open, and the
    next dispatch for that obligation is refused anyway. So the attempt is recorded as
    failed with the reason, and the run stops for reconciliation.
    """
    workflow = repair_project(tmp_path, qa_report={'status': 'failed'},
                              transition_log=[qa_failed('verify')])
    gate_by_ready_artifacts(tmp_path, monkeypatch)
    helper = tmp_path / '.allforai/bootstrap/scripts' / flow.LEDGER_HELPER

    def executor(project_root, node_id, attempt):
        write(project_root / f'{node_id}.json', {'status': 'passed'})
        helper.unlink()                    # the settlement can no longer reach the ledger

    selected, executed = drive_real_routing(tmp_path, monkeypatch, executor, max_iterations=3)
    payload = json.loads(capsys.readouterr().err.strip().splitlines()[-1])
    assert executed == ['repair'], executed
    assert payload['unresolved_repair_authorizations'], payload
    current = flow.load_json(tmp_path / '.allforai/bootstrap/workflow.json')
    latest = [e for e in current['transition_log'] if e['node'] == 'repair'][-1]
    assert latest['status'] == 'failed', 'an attempt that never settled is not a completion'
    assert 'not recorded in the canonical ledger' in latest['error']
    entry = ledger_entries(tmp_path)[-1]
    assert entry['state'] == 'started' and entry['outcome'] is None, entry


def test_a_receipt_for_another_authorization_is_not_permission_to_execute(tmp_path, monkeypatch):
    """A verdict is trusted for its accounting, not for its addressing.

    A receipt naming a different authorization says nothing about this dispatch, and
    reading it as if it did would attribute one attempt's charge or claim to another.
    """
    workflow = repair_project(tmp_path, qa_report={'status': 'failed'},
                              transition_log=[qa_failed('verify')])
    gate_by_ready_artifacts(tmp_path, monkeypatch)
    scripts = tmp_path / '.allforai/bootstrap/scripts'
    (scripts / flow.LEDGER_HELPER).write_text(
        'import json,sys\n'
        'request = json.load(sys.stdin)\n'
        'operation = request.get("operation")\n'
        'verdict = {"consumption": {"status": "ok", "run_id": "fixture-run", "obligations": [],\n'
        '                           "unresolved": []},\n'
        '           "authorize": {"status": "authorized", "authorization_id": "somebody-else",\n'
        '                         "run_id": "fixture-run"},\n'
        '           "start": {"status": "started", "authorization_id": "somebody-else",\n'
        '                     "execution_allowed": True}}[operation]\n'
        'print(json.dumps(verdict))\n')
    assert flow.authorize_repair_dispatch(tmp_path, workflow, 'repair', ['verify']) is None
    assert flow.settle_repair_dispatch(tmp_path, {'authorization_id': 'mine'}, 'delivered') is False


# --- the concept-acceptance coverage gate (ADR 0008) ---
#
# The gate names the behaviour mappings that have no evidence; it renders no score and no
# verdict. A non-empty list fires on_needs_iteration, an empty one proceeds, and under
# auto_fix_once the list is a bounded QA repair request that reaches the declared repair
# node only through the canonical ledger (ADR 0005, ADR 0006).

MISSING_MAPPING = [{'mapping_id': 'bm-3', 'behaviour': 'frustration lowers difficulty',
                    'expected_evidence': 'runtime probe of the next exercise'}]


def test_acceptance_gate_reads_the_missing_mapping_list_and_nothing_else(tmp_path):
    report = tmp_path / flow.ACCEPTANCE_REPORT
    assert flow.acceptance_gate(tmp_path) == ([], None), 'no report: the gate has not run'
    write(report, {'gate': 'concept-acceptance', 'missing_mappings': []})
    assert flow.acceptance_gate(tmp_path) == ([], None), 'every mapping has evidence: proceed'
    assert not flow.acceptance_requires_iteration(tmp_path)
    write(report, {'gate': 'concept-acceptance', 'missing_mappings': MISSING_MAPPING})
    assert flow.acceptance_gate(tmp_path) == (MISSING_MAPPING, None), 'a named mapping fires'
    assert flow.acceptance_requires_iteration(tmp_path)
    assert 'missing_mappings contains unresolved' in flow.artifact_status_error(report, tmp_path), \
        'a non-empty list is the gate\'s QA verdict; the report is not a ready artifact'


@pytest.mark.parametrize('report, named', [
    ({'verdict': 'needs_iteration', 'overall_score': 78, 'pass_threshold': 80, 'gaps': ['x']}, 'verdict'),
    ({'verdict': 'pass', 'missing_mappings': []}, 'verdict'),
    ({'gate': 'concept-acceptance', 'gaps': ['x']}, 'missing_mappings'),
    ({'gate': 'concept-acceptance', 'missing_mappings': 'bm-3'}, 'missing_mappings'),
])
def test_a_scored_or_listless_acceptance_report_is_refused_by_name(tmp_path, report, named):
    write(tmp_path / flow.ACCEPTANCE_REPORT, report)
    missing, refused = flow.acceptance_gate(tmp_path)
    assert missing == [] and refused and named in refused, refused
    assert flow.acceptance_requires_iteration(tmp_path), 'a refusal is never read as proceed'


def concept_gate_project(tmp_path, max_attempts=2, declare_loop=True):
    """implement -> concept gate (QA) -> gate-repair, the gate declared as the loop's obligation."""
    nodes = [
        {'node_id': 'implement', 'hard_blocked_by': [], 'exit_artifacts': ['implement.json']},
        {'node_id': 'concept-gate', 'hard_blocked_by': ['implement'],
         'exit_artifacts': [flow.ACCEPTANCE_REPORT]},
        {'node_id': 'gate-repair', 'hard_blocked_by': ['concept-gate'], 'exit_artifacts': ['gate-repair.json']},
    ]
    write(tmp_path / '.allforai/bootstrap/workflow.json', {'nodes': nodes, 'transition_log': []})
    install_repair_ledger(tmp_path)
    loops = [{'scope': 'concept', 'qa_node_ids': ['concept-gate'], 'repair_node_id': 'gate-repair',
              'closure_node_ids': [], 'max_attempts': max_attempts}] if declare_loop else []
    write(tmp_path / '.allforai/bootstrap/unattended-run-readiness-spec.json',
          {'version': 1, 'required_repair_loops': loops})
    return nodes


def gate_executor(covered_from_attempt):
    """The gate names a missing mapping until its `covered_from_attempt`-th run."""
    def executor(project_root, node_id, attempt):
        if node_id == 'concept-gate':
            write(project_root / flow.ACCEPTANCE_REPORT, {
                'gate': 'concept-acceptance', 'attempt': attempt,
                'missing_mappings': [] if attempt >= covered_from_attempt else MISSING_MAPPING})
        else:
            write(project_root / f'{node_id}.json', {'status': 'passed'})
    return executor


def test_a_missing_mapping_is_repaired_once_through_the_ledger_and_the_rerun_proceeds(tmp_path, monkeypatch, capsys):
    concept_gate_project(tmp_path)
    gate_by_ready_artifacts(tmp_path, monkeypatch)
    selected, executed = drive_real_routing(tmp_path, monkeypatch, gate_executor(covered_from_attempt=2),
                                            max_iterations=8, on_needs_iteration='auto_fix_once')
    assert executed == ['implement', 'concept-gate', 'gate-repair', 'concept-gate'], executed
    entries = [(e['repair_node_id'], e['obligations'], e['state'], e['outcome']) for e in ledger_entries(tmp_path)]
    assert entries == [('gate-repair', ['concept-gate'], 'settled', 'delivered')], \
        f'the one repair was charged, claimed and settled through the ledger: {entries}'
    assert '"done": true' in capsys.readouterr().out, 'an empty list after the rerun proceeds'


def test_a_mapping_still_missing_after_the_one_recorded_repair_halts_with_its_report(tmp_path, monkeypatch, capsys):
    concept_gate_project(tmp_path, max_attempts=3)
    gate_by_ready_artifacts(tmp_path, monkeypatch)
    selected, executed = drive_real_routing(tmp_path, monkeypatch, gate_executor(covered_from_attempt=99),
                                            max_iterations=8, on_needs_iteration='auto_fix_once')
    assert executed == ['implement', 'concept-gate', 'gate-repair', 'concept-gate'], \
        f'the loop had budget left; the recorded policy is what stopped a second repair: {executed}'
    assert len(ledger_entries(tmp_path)) == 1, 'nothing further charged'
    err = json.loads(capsys.readouterr().err)
    assert err['run_policy_outcome'] == 'iteration halted with report'
    summary = (tmp_path / '.allforai/concept-acceptance/acceptance-report.md').read_text()
    assert 'bm-3' in summary and 'score' not in summary.lower()


def test_a_missing_mapping_with_no_declared_repair_loop_is_an_unauthorized_repair(tmp_path, monkeypatch, capsys):
    concept_gate_project(tmp_path, declare_loop=False)
    gate_by_ready_artifacts(tmp_path, monkeypatch)
    selected, executed = drive_real_routing(tmp_path, monkeypatch, gate_executor(covered_from_attempt=99),
                                            max_iterations=8, on_needs_iteration='auto_fix_once')
    assert executed == ['implement', 'concept-gate'], f'no repair ran and the gate was not rerun: {executed}'
    assert ledger_entries(tmp_path) == []
    lines = capsys.readouterr().err.strip().splitlines()
    assert any('no declared repair loop names the concept-acceptance gate' in line for line in lines), lines


def test_a_missing_mapping_whose_budget_is_spent_halts_without_a_dispatch(tmp_path, monkeypatch, capsys):
    nodes = concept_gate_project(tmp_path, max_attempts=1)
    gate_by_ready_artifacts(tmp_path, monkeypatch)
    workflow = {'nodes': nodes, 'transition_log': [
        {'node': 'implement', 'status': 'completed', 'artifacts_created': ['implement.json']},
        qa_failed('concept-gate')]}
    write(tmp_path / 'implement.json', {'status': 'passed'})
    write(tmp_path / flow.ACCEPTANCE_REPORT, {'gate': 'concept-acceptance', 'missing_mappings': MISSING_MAPPING})
    stamp_attempt_evidence(tmp_path, workflow, 'concept-gate')
    repair_dispatched(tmp_path, workflow, 'concept-gate', 'gate-repair', settle='failed')
    workflow['transition_log'].append({'node': 'gate-repair', 'status': 'failed'})
    workflow['transition_log'].append(qa_failed('concept-gate'))
    stamp_attempt_evidence(tmp_path, workflow, 'concept-gate')
    monkeypatch.setattr(flow, 'policy_action', lambda root, event=None: 'auto_fix_once' if event else 'ready')
    assert flow.handle_iteration(tmp_path, workflow) == 6
    err = json.loads(capsys.readouterr().err.strip().splitlines()[-1])
    assert 'budget is spent' in err['error'] and err['spent'] == 1 and err['budget'] == 1
    assert len(ledger_entries(tmp_path)) == 1, 'an over-budget repair charges nothing'


def test_a_gate_whose_ledger_accounting_is_unknown_halts_rather_than_repairing(tmp_path, monkeypatch, capsys):
    nodes = concept_gate_project(tmp_path)
    (tmp_path / flow.REPAIR_LEDGER).write_text('{broken')
    write(tmp_path / flow.ACCEPTANCE_REPORT, {'gate': 'concept-acceptance', 'missing_mappings': MISSING_MAPPING})
    monkeypatch.setattr(flow, 'policy_action', lambda root, event=None: 'auto_fix_once' if event else 'ready')
    assert flow.handle_iteration(tmp_path, {'nodes': nodes, 'transition_log': []}) == 6
    err = json.loads(capsys.readouterr().err.strip().splitlines()[-1])
    assert err['spent'] is None and 'accounting is unknown' in err['error']


def test_a_scored_acceptance_report_never_opens_a_repair(tmp_path, monkeypatch, capsys):
    nodes = concept_gate_project(tmp_path)
    write(tmp_path / flow.ACCEPTANCE_REPORT, {'verdict': 'needs_iteration', 'overall_score': 78, 'gaps': ['x']})
    monkeypatch.setattr(flow, 'policy_action', lambda root, event=None: 'auto_fix_once' if event else 'ready')
    assert flow.handle_iteration(tmp_path, {'nodes': nodes, 'transition_log': []}) == 6
    assert 'renders no score' in json.loads(capsys.readouterr().err.strip().splitlines()[-1])['error']
    assert ledger_entries(tmp_path) == []
    monkeypatch.setattr(flow, 'policy_action', lambda root, event=None: 'halt_with_report' if event else 'ready')
    assert flow.handle_iteration(tmp_path, {'nodes': nodes, 'transition_log': []}) == 5
    assert 'refused' in (tmp_path / '.allforai/concept-acceptance/acceptance-report.md').read_text()
