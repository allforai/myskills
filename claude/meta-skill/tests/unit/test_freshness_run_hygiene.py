"""Leftover outputs are not inputs, and an interrupted wave leaves no residue."""
import json

import pytest

from .test_evidence_freshness import WORKFLOW, invoke, setup
from .test_bootstrap_scope import write

STATE = '.allforai/bootstrap/evidence-freshness.json'
READS = '.allforai/bootstrap/observed-input-dependencies.json'
LATER = '.allforai/bootstrap/later-report.json'


def add_node(root, node_id, artifact, blocked_by=()):
    workflow = json.loads((root / WORKFLOW).read_text())
    workflow['nodes'].append({'node_id': node_id, 'goal': 'later work', 'capability': 'implement',
                              'exit_artifacts': [artifact], 'source_inputs': [],
                              'hard_blocked_by': list(blocked_by)})
    write(root, WORKFLOW, workflow)


def block_first_node_on(root, node_id):
    workflow = json.loads((root / WORKFLOW).read_text())
    workflow['nodes'][0]['hard_blocked_by'] = [node_id]
    write(root, WORKFLOW, workflow)


@pytest.mark.parametrize('host', ['claude', 'codex'])
def test_read_refuses_a_leftover_output_of_a_node_that_has_not_published(tmp_path, host):
    setup(tmp_path, host)
    add_node(tmp_path, 'later', LATER)
    write(tmp_path, LATER, {'status': 'passed'})          # left on disk by an earlier cycle
    _, observed = invoke(tmp_path, 'observe', node_id='deliver-export')
    result, refused = invoke(tmp_path, 'read', observation=observed['observation'], path=LATER)
    assert result.returncode == 1
    assert refused['status'] == 'unpublished_producer' and refused['producer'] == 'later'
    assert 'content' not in refused
    assert not (tmp_path / READS).exists() or 'deliver-export' not in json.loads((tmp_path / READS).read_text())


@pytest.mark.parametrize('host', ['claude', 'codex'])
def test_read_allows_the_unpublished_output_of_a_node_this_one_is_ordered_after(tmp_path, host):
    # A repair reads the failed report of the QA node it answers.
    setup(tmp_path, host)
    add_node(tmp_path, 'later', LATER)
    block_first_node_on(tmp_path, 'later')
    write(tmp_path, LATER, {'status': 'failed'})
    _, observed = invoke(tmp_path, 'observe', node_id='deliver-export')
    result, read = invoke(tmp_path, 'read', observation=observed['observation'], path=LATER)
    assert result.returncode == 0 and 'content' in read


@pytest.mark.parametrize('host', ['claude', 'codex'])
def test_recover_returns_an_unclosed_wave_to_what_it_had(tmp_path, host):
    setup(tmp_path, host)
    (tmp_path / 'policy.txt').write_text('region = JP')
    result, opened = invoke(tmp_path, 'begin-wave', node_ids=['deliver-export'])
    assert result.returncode == 0 and opened['open'] == ['deliver-export']
    _, observed = invoke(tmp_path, 'observe', node_id='deliver-export')
    _, read = invoke(tmp_path, 'read', observation=observed['observation'], path='policy.txt')
    result, _ = invoke(tmp_path, 'publish', observation=read['observation'])
    assert result.returncode == 0
    assert 'deliver-export' in json.loads((tmp_path / STATE).read_text())['nodes']
    # the driver dies here: no transition, no end-wave
    result, recovered = invoke(tmp_path, 'recover-waves')
    assert result.returncode == 0 and recovered['recovered'] == ['deliver-export']
    assert 'deliver-export' not in json.loads((tmp_path / STATE).read_text())['nodes']
    assert 'deliver-export' not in json.loads((tmp_path / READS).read_text())
    _, again = invoke(tmp_path, 'recover-waves')
    assert again['recovered'] == []


@pytest.mark.parametrize('host', ['claude', 'codex'])
@pytest.mark.parametrize('closed_by', ['end-wave', 'completed-transition'])
def test_recover_leaves_a_wave_that_was_seen_to_finish(tmp_path, host, closed_by):
    setup(tmp_path, host)
    invoke(tmp_path, 'begin-wave', node_ids=['deliver-export'])
    _, observed = invoke(tmp_path, 'observe', node_id='deliver-export')
    invoke(tmp_path, 'publish', observation=observed['observation'])
    if closed_by == 'end-wave':
        _, closed = invoke(tmp_path, 'end-wave', node_ids=['deliver-export'])
        assert closed['open'] == []
    else:
        workflow = json.loads((tmp_path / WORKFLOW).read_text())
        workflow['transition_log'].append({'node_id': 'deliver-export', 'status': 'completed'})
        write(tmp_path, WORKFLOW, workflow)
    before = (tmp_path / STATE).read_bytes()
    _, recovered = invoke(tmp_path, 'recover-waves')
    assert recovered['recovered'] == []
    assert (tmp_path / STATE).read_bytes() == before


def publish(root, node_id):
    _, observed = invoke(root, 'observe', node_id=node_id)
    result, published = invoke(root, 'publish', observation=observed['observation'])
    assert result.returncode == 0, published
    return observed


@pytest.mark.parametrize('host', ['claude', 'codex'])
def test_read_refuses_a_published_output_of_a_node_the_plan_does_not_order_before(tmp_path, host):
    # Readiness rejects such a recorded read afterwards, so it is never recorded.
    setup(tmp_path, host)
    add_node(tmp_path, 'later', LATER)
    write(tmp_path, LATER, {'status': 'passed'})
    publish(tmp_path, 'later')
    _, observed = invoke(tmp_path, 'observe', node_id='deliver-export')
    result, refused = invoke(tmp_path, 'read', observation=observed['observation'], path=LATER)
    assert result.returncode == 1
    assert refused['status'] == 'producer_outside_graph' and refused['producer'] == 'later'
    assert 'content' not in refused
    assert not (tmp_path / READS).exists() or 'deliver-export' not in json.loads((tmp_path / READS).read_text())


@pytest.mark.parametrize('host', ['claude', 'codex'])
@pytest.mark.parametrize('directory', ['diagnosis-corrections', 'inline-review'])
def test_a_diagnosis_correction_is_never_registered_as_an_input(tmp_path, host, directory):
    # The run's instruction to a node, rewritten or deleted by the run; bound, it would
    # stale the evidence. An inline review's findings are the same kind of file.
    setup(tmp_path, host)
    correction = f'.allforai/bootstrap/{directory}/deliver-export.json'
    write(tmp_path, correction, {'corrections': ['x']})
    _, observed = invoke(tmp_path, 'observe', node_id='deliver-export')
    result, refused = invoke(tmp_path, 'read', observation=observed['observation'], path=correction)
    assert result.returncode == 1 and refused['status'] == 'invalid'
    assert 'orchestration state' in refused['reason']
    assert not (tmp_path / READS).exists() or 'deliver-export' not in json.loads((tmp_path / READS).read_text())


@pytest.mark.parametrize('host', ['claude', 'codex'])
@pytest.mark.parametrize('declared', [True, False])
def test_a_write_inside_another_nodes_declared_scope_is_not_this_nodes_unmapped_input(tmp_path, host, declared):
    setup(tmp_path, host)
    add_node(tmp_path, 'later', LATER)
    if declared:
        workflow = json.loads((tmp_path / WORKFLOW).read_text())
        workflow['nodes'][-1]['parallel_write_scopes'] = ['docs/index.md']
        write(tmp_path, WORKFLOW, workflow)
    publish(tmp_path, 'deliver-export')
    (tmp_path / 'docs').mkdir(exist_ok=True)
    (tmp_path / 'docs/index.md').write_text('written by the unrelated node\n')
    _, checked = invoke(tmp_path, 'check')
    assert checked['nodes']['deliver-export']['status'] == ('valid' if declared else 'uncertain')


@pytest.mark.parametrize('host', ['claude', 'codex'])
def test_an_upstream_is_recorded_as_an_identity_and_an_embedded_record_still_compares(tmp_path, host):
    setup(tmp_path, host)
    add_node(tmp_path, 'later', LATER)
    block_first_node_on(tmp_path, 'later')
    write(tmp_path, LATER, {'status': 'passed'})
    publish(tmp_path, 'later')
    publish(tmp_path, 'deliver-export')
    state = json.loads((tmp_path / STATE).read_text())
    recorded = state['nodes']['deliver-export']['inputs']['upstream']
    assert isinstance(recorded['later'], str) and len(recorded['later']) == 64
    # a record written before upstreams became identities embeds the snapshot whole
    recorded['later'] = state['nodes']['later']['inputs']
    write(tmp_path, STATE, state)
    _, checked = invoke(tmp_path, 'check')
    assert checked['nodes']['deliver-export']['status'] == 'valid'
    write(tmp_path, LATER, {'status': 'passed', 'changed': True})
    _, checked = invoke(tmp_path, 'check')
    assert checked['nodes']['deliver-export']['status'] == 'stale'


@pytest.mark.parametrize('host', ['claude', 'codex'])
def test_recover_removes_observations_no_attempt_can_still_publish(tmp_path, host):
    setup(tmp_path, host)
    invoke(tmp_path, 'observe', node_id='deliver-export')
    observations = tmp_path / '.allforai/bootstrap/input-observations'
    assert list(observations.glob('*.json'))
    result, recovered = invoke(tmp_path, 'recover-waves')
    assert result.returncode == 0 and recovered['pruned_observations'] == 1
    assert not list(observations.glob('*.json'))
