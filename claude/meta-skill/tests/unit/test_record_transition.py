"""record_transition.py: a node's transition is written by code, never by a model editing
workflow.json by hand (expert review 2026-11-26, item 4)."""
import json
from pathlib import Path
import subprocess
import sys

SCRIPT = Path(__file__).resolve().parents[2] / 'scripts/orchestrator/record_transition.py'
WORKFLOW = '.allforai/bootstrap/workflow.json'


def project(tmp_path, log=None):
    path = tmp_path / WORKFLOW
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({'nodes': [{'node_id': 'a'}], 'transition_log': log or []}, indent=2))
    return tmp_path


def record(root, request):
    done = subprocess.run([sys.executable, str(SCRIPT), str(root)], input=json.dumps(request),
                          capture_output=True, text=True)
    return done.returncode, json.loads(done.stdout)


def log_of(root):
    return json.loads((root / WORKFLOW).read_text())['transition_log']


COMPLETED = {'node_id': 'a', 'status': 'completed', 'artifacts_created': ['out.json'],
             'verification': {'method': 'test', 'command': 'pytest'}}


def test_completed_transition_is_appended_with_receipt(tmp_path):
    root = project(tmp_path)
    code, receipt = record(root, COMPLETED)
    log = log_of(root)
    assert code == 0
    assert receipt == {'status': 'recorded', 'node_id': 'a', 'transition_index': len(log) - 1,
                       'replayed': False}
    entry = log[-1]
    assert entry['node_id'] == 'a' and entry['status'] == 'completed'
    assert entry['artifacts_created'] == ['out.json']
    assert entry['verification'] == {'method': 'test', 'command': 'pytest'}
    assert entry['completed_at']


def test_same_request_twice_is_a_replay_not_a_second_entry(tmp_path):
    root = project(tmp_path)
    record(root, COMPLETED)
    code, receipt = record(root, COMPLETED)
    assert code == 0 and receipt['replayed'] is True
    assert len(log_of(root)) == 1 and receipt['transition_index'] == 0


def test_a_different_request_after_one_is_a_new_entry(tmp_path):
    root = project(tmp_path)
    record(root, COMPLETED)
    code, receipt = record(root, {**COMPLETED, 'artifacts_created': ['other.json']})
    assert code == 0 and receipt['replayed'] is False and len(log_of(root)) == 2


def test_failed_transition_requires_error(tmp_path):
    root = project(tmp_path)
    code, receipt = record(root, {'node_id': 'a', 'status': 'failed', 'artifacts_created': []})
    assert code == 1 and receipt['status'] == 'refused' and log_of(root) == []


def test_unknown_status_is_refused(tmp_path):
    root = project(tmp_path)
    code, receipt = record(root, {**COMPLETED, 'status': 'done'})
    assert code == 1 and receipt['status'] == 'refused'


def test_missing_workflow_is_refused_not_created(tmp_path):
    code, receipt = record(tmp_path, COMPLETED)
    assert code == 1 and receipt['status'] == 'refused'
    assert not (tmp_path / WORKFLOW).exists()


def test_unreadable_input_is_refused(tmp_path):
    root = project(tmp_path)
    done = subprocess.run([sys.executable, str(SCRIPT), str(root)], input='not json',
                          capture_output=True, text=True)
    assert done.returncode == 1 and json.loads(done.stdout)['status'] == 'refused'


def test_other_entries_are_untouched(tmp_path):
    earlier = [{'node': 'b', 'status': 'completed', 'artifacts_created': []},
               {'node_id': 'c', 'status': 'failed', 'error': 'x', 'artifacts_created': []}]
    root = project(tmp_path, earlier)
    record(root, COMPLETED)
    assert log_of(root)[:2] == earlier


def test_assumed_decisions_are_appended(tmp_path):
    root = project(tmp_path)
    decision = {'id': 'd1', 'choice': 'x'}
    record(root, {**COMPLETED, 'assumed_decisions': [decision]})
    path = root / '.allforai/bootstrap/assumed-decisions.json'
    assert json.loads(path.read_text()) == [decision]


def test_clear_corrections_deletes_the_node_file(tmp_path):
    root = project(tmp_path)
    corrections = root / '.allforai/bootstrap/diagnosis-corrections/a.json'
    corrections.parent.mkdir(parents=True)
    corrections.write_text('{}')
    code, _ = record(root, {**COMPLETED, 'clear_corrections': True})
    assert code == 0 and not corrections.exists()
    code, _ = record(root, {**COMPLETED, 'artifacts_created': [], 'clear_corrections': True})
    assert code == 0
