"""Contract behavior of the shared repair-authorization ledger.

These exercise the module and its CLI only. They are not host acceptance: neither
Claude's Workflow engine nor the Codex executor is driven here, and nothing in this
file is evidence that either host consumes this ledger. The cases marked with a
scenario id come from `tests/fixtures/execution-contract-scenarios.json`, the accepted
cross-host behavioral scenarios; the host-level scenarios in that file (safety halt,
closure, admission) belong to the engines and validators, not to this helper.
"""
import json
from pathlib import Path
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import pytest

from ..module_isolation import load

SCRIPT = Path(__file__).resolve().parents[2] / 'scripts/orchestrator/repair_authorization.py'
SCENARIOS = Path(__file__).resolve().parents[1] / 'fixtures/execution-contract-scenarios.json'
LEDGER = '.allforai/bootstrap/repair-authorizations.json'
WORKFLOW = '.allforai/bootstrap/workflow.json'
SPEC = '.allforai/bootstrap/unattended-run-readiness-spec.json'
# The plan most of these tests run against: one shared repair node answering two QA
# obligations, plus two single-obligation loops. None of them declares `max_attempts`,
# which is the ordinary case — the documented default of three attempts per QA node
# applies, exactly as `validate_unattended_readiness.py` and both hosts read it.
DEFAULT_PLAN = (('fix', ['qa-a', 'qa-b'], None),
                ('fix-a', ['qa-a'], None),
                ('fix-b', ['qa-b'], None))

# Loaded out of this plugin's orchestrator directory rather than by bare name, so a
# combined collection cannot bind some other tree's same-named module here.
ra = load('repair_authorization')


def scenario(identifier):
    """The accepted expectations for one shared contract scenario."""
    cases = json.loads(SCENARIOS.read_text())['scenarios']
    return next(case for case in cases if case['id'] == identifier)


@pytest.fixture
def root(tmp_path):
    (tmp_path / '.allforai/bootstrap').mkdir(parents=True)
    return tmp_path


def write_workflow(root, **fields):
    document = {'nodes': [{'node_id': 'build'}], 'required_repair_loops': []}
    document.update(fields)
    (root / WORKFLOW).write_text(json.dumps(document, indent=2))
    return document


def plan(root, *loops):
    """The confirmed plan: one `required_repair_loops` entry per declared loop.

    A loop is (repair_node_id, [qa node ids], max_attempts). Pass None for max_attempts to
    declare none and take the documented default. This is the authority for every budget
    below: a bound the request names is not a bound.
    """
    declared = []
    for repair_node_id, qa_node_ids, max_attempts in loops:
        loop = {'scope': f'{repair_node_id}-loop', 'repair_node_id': repair_node_id,
                'qa_node_ids': list(qa_node_ids), 'closure_node_ids': ['accept']}
        if max_attempts is not None:
            loop['max_attempts'] = max_attempts
        declared.append(loop)
    (root / SPEC).write_text(json.dumps({'version': 1, 'required_repair_loops': declared},
                                        indent=2))
    return root


def started(root, run_id='run-1', loops=DEFAULT_PLAN):
    """A verified-new run: a declared plan, an untouched workflow, a recorded origin."""
    write_workflow(root)
    plan(root, *loops)
    ra.initialize(root, run_id)
    return root


def grant(root, identifier, obligations, budgets, repair_node_id='fix', run_id='run-1'):
    return ra.authorize(root, {'run_id': run_id, 'authorization_id': identifier,
                               'repair_node_id': repair_node_id,
                               'obligations': obligations, 'budgets': budgets})


def attempt(root, identifier, obligations, budgets, outcome='failed', **kwargs):
    """A whole attempt: charge it, claim its one execution, record how it ended."""
    verdict = grant(root, identifier, obligations, budgets, **kwargs)
    ra.start(root, kwargs.get('run_id', 'run-1'), identifier)
    ra.settle(root, identifier, outcome)
    return verdict


def refusal(call, *args, **kwargs):
    with pytest.raises(ra.Refusal) as caught:
        call(*args, **kwargs)
    return caught.value.verdict


def cli(root, request):
    result = subprocess.run([sys.executable, str(SCRIPT), str(root)],
                            input=json.dumps(request), text=True, capture_output=True)
    return result, json.loads(result.stdout)


def spend_by_obligation(root):
    return {o['qa_node_id']: o['spent'] for o in ra.consumption(root)['obligations']}


def grant_succeeds(root, identifier, obligations, budgets, **kwargs):
    """Whether the helper actually issues this grant — observed, not assumed."""
    try:
        return grant(root, identifier, obligations, budgets, **kwargs)['status'] == 'authorized'
    except ra.Refusal:
        return False


def start_permits_execution(root, identifier, run_id='run-1'):
    """Whether the helper actually lets this authorization execute."""
    try:
        return ra.start(root, run_id, identifier)['execution_allowed']
    except ra.Refusal:
        return False


def ran(root, node='fix', **fields):
    """Evidence that the repair node ran: a real record of the real workflow."""
    record = {'node': node, 'status': 'completed', 'at': '2099-01-01T00:00:00Z'}
    record.update(fields)
    write_workflow(root, transition_log=[record])
    return {'source_path': WORKFLOW, 'source_digest': ra.file_digest(root / WORKFLOW),
            'observation_ref': 'transition_log[0]', 'basis': 'the repair node ran'}


def never_ran(root, log=None):
    """Evidence that it did not: a log asserted complete, holding nothing of this attempt."""
    write_workflow(root, transition_log=log if log is not None else [])
    return {'source_path': WORKFLOW, 'source_digest': ra.file_digest(root / WORKFLOW),
            'absence_of': 'transition_log', 'complete': True,
            'basis': 'the complete transition log records no run of this repair node'}


# --- a charge is the grant, and it is per obligation -------------------------------

def test_authorize_charges_every_obligation_of_one_dispatch(root):
    started(root)
    verdict = grant(root, 'a1', ['qa-a', 'qa-b'], {'qa-a': 3, 'qa-b': 3})
    assert verdict['status'] == 'authorized'
    assert verdict['charged'] == {'qa-a': 1, 'qa-b': 1}
    assert verdict['remaining'] == {'qa-a': 2, 'qa-b': 2}
    assert verdict['state'] == 'authorized'


def test_a_sibling_obligation_is_never_charged_for_another_repair(root):
    started(root)
    attempt(root, 'a1', ['qa-a'], {'qa-a': 3})
    attempt(root, 'a2', ['qa-a'], {'qa-a': 3})
    assert spend_by_obligation(root) == {'qa-a': 2}
    # qa-b shares the repair node but has never been authorized, so it has spent nothing.
    assert grant(root, 'a3', ['qa-b'], {'qa-b': 3})['charged'] == {'qa-b': 1}


def test_the_same_repair_node_spends_one_attempt_of_each_obligation_it_answers(root):
    started(root, loops=(('fix', ['qa-a', 'qa-b'], 2),))
    attempt(root, 'a1', ['qa-a', 'qa-b'], {'qa-a': 2, 'qa-b': 2})
    attempt(root, 'a2', ['qa-a', 'qa-b'], {'qa-a': 2, 'qa-b': 2})
    assert refusal(grant, root, 'a3', ['qa-a', 'qa-b'],
                   {'qa-a': 2, 'qa-b': 2})['status'] == 'budget_exhausted'


def test_settlement_does_not_refund_the_attempt(root):
    started(root, loops=(('fix', ['qa-a', 'qa-b'], 2),))
    verdict = attempt(root, 'a1', ['qa-a'], {'qa-a': 2}, outcome='failed')
    assert verdict['charged'] == {'qa-a': 1}
    assert ra.settle(root, 'a1', 'failed')['refunded'] is False
    # A failed attempt is still an attempt: the second grant is the last one.
    assert grant(root, 'a2', ['qa-a'], {'qa-a': 2})['remaining'] == {'qa-a': 0}


# --- scenario: shared_repair_asymmetric_budget -------------------------------------

def test_shared_repair_asymmetric_budget(root):
    expect = scenario('shared_repair_asymmetric_budget')['expect']
    started(root, loops=(('fix', ['qa-a', 'qa-b'], 2),))
    attempt(root, 'a1', ['qa-a', 'qa-b'], {'qa-a': 2, 'qa-b': 2})
    attempt(root, 'a2', ['qa-a'], {'qa-a': 2})            # qa-a spent 2, qa-b spent 1
    report = {o['qa_node_id']: o for o in ra.consumption(root)['obligations']}
    assert report['qa-a']['spent'] == 2 and report['qa-b']['spent'] == 1
    blocked = sorted(k for k, o in report.items() if o['exhausted'])
    eligible = sorted(k for k, o in report.items() if not o['exhausted'])
    assert blocked == expect['blocked_obligations']
    assert eligible == expect['eligible_obligations']
    # The shared dispatch is refused outright; the driver re-requests the eligible one.
    assert refusal(grant, root, 'a3', ['qa-a', 'qa-b'],
                   {'qa-a': 2, 'qa-b': 2})['status'] == 'budget_exhausted'
    assert grant(root, 'a4', ['qa-b'], {'qa-b': 2})['charged'] == {'qa-b': 2}
    # An exhausted obligation is refused, never accepted: it still has to be satisfied.
    exhausted_accepted = grant_succeeds(root, 'a5', ['qa-a'], {'qa-a': 2})
    assert exhausted_accepted is expect['final_acceptance']


# --- budget upper bounds, all-or-none ----------------------------------------------

def test_exhausted_budget_refuses_and_charges_nothing(root):
    started(root, loops=(('fix', ['qa-a', 'qa-b'], 1),))
    attempt(root, 'a1', ['qa-a'], {'qa-a': 1})
    verdict = refusal(grant, root, 'a2', ['qa-a'], {'qa-a': 1})
    assert verdict['status'] == 'budget_exhausted'
    assert verdict['exhausted'] == {'qa-a': {'spent': 1, 'budget': 1}}
    assert spend_by_obligation(root) == {'qa-a': 1}


def test_one_exhausted_obligation_stops_the_whole_multi_obligation_charge(root):
    started(root, loops=(('fix', ['qa-a'], 1), ('fix', ['qa-b'], None)))
    attempt(root, 'a1', ['qa-a'], {'qa-a': 1})
    verdict = refusal(grant, root, 'a2', ['qa-a', 'qa-b'], {'qa-a': 1, 'qa-b': 3})
    assert verdict['status'] == 'budget_exhausted'
    assert set(verdict['exhausted']) == {'qa-a'}
    # qa-b keeps its untouched budget rather than paying for its exhausted sibling.
    assert spend_by_obligation(root) == {'qa-a': 1}


def test_a_bound_that_moves_is_refused(root):
    """The bound moves in the plan, not in the request; the spend is already charged."""
    started(root, loops=(('fix', ['qa-a'], 1),))
    attempt(root, 'a1', ['qa-a'], {'qa-a': 1})
    plan(root, ('fix', ['qa-a'], 9))
    verdict = refusal(grant, root, 'a2', ['qa-a'], {'qa-a': 9})
    assert verdict['status'] == 'blocked' and verdict['untrusted'] == 'budget_conflict'
    assert verdict['budgets'] == {'qa-a': {'recorded': 1, 'requested': 9}}
    # Neither re-priced nor reset: the attempt already charged is still charged.
    assert spend_by_obligation(root) == {'qa-a': 1}


# --- authorize grants; only start permits execution --------------------------------

def test_authorize_alone_permits_no_execution(root):
    started(root)
    assert grant(root, 'a1', ['qa-a'], {'qa-a': 3})['execution_allowed'] is False


def test_only_the_first_start_permits_execution(root):
    started(root)
    grant(root, 'a1', ['qa-a'], {'qa-a': 3})
    first = ra.start(root, 'run-1', 'a1')
    assert first['status'] == 'started' and first['execution_allowed'] is True
    second = ra.start(root, 'run-1', 'a1')
    assert second['status'] == 'started' and second['execution_allowed'] is False
    assert second['replayed'] is True
    assert spend_by_obligation(root) == {'qa-a': 1}


def test_a_settled_attempt_is_not_restartable(root):
    started(root)
    attempt(root, 'a1', ['qa-a'], {'qa-a': 3})
    verdict = refusal(ra.start, root, 'run-1', 'a1')
    assert verdict['status'] == 'blocked' and verdict['untrusted'] == 'already_settled'


def test_starting_an_unknown_grant_is_refused(root):
    started(root)
    verdict = refusal(ra.start, root, 'run-1', 'never-granted')
    assert verdict['status'] == 'blocked'
    assert verdict['untrusted'] == 'unknown_authorization'


def test_start_is_refused_for_another_run(root):
    started(root)
    grant(root, 'a1', ['qa-a'], {'qa-a': 3})
    assert refusal(ra.start, root, 'run-2', 'a1')['untrusted'] == 'run_identity_mismatch'


# --- scenario: duplicate_authorization / conflicting_authorization_replay -----------

def test_duplicate_authorization(root):
    expect = scenario('duplicate_authorization')['expect']
    started(root, loops=(('fix', ['qa-a', 'qa-b'], 1),))
    grant(root, 'a1', ['qa-a', 'qa-b'], {'qa-a': 1, 'qa-b': 1})
    replay = grant(root, 'a1', ['qa-b', 'qa-a'], {'qa-a': 1, 'qa-b': 1})
    assert replay['status'] == 'replayed'
    assert replay['execution_allowed'] is expect['replay_execution_allowed']
    assert replay['charged'] == {'qa-a': 1, 'qa-b': 1}
    assert set(spend_by_obligation(root).values()) == {1 + expect['additional_charges']}


def test_conflicting_authorization_replay(root):
    expect = scenario('conflicting_authorization_replay')['expect']
    started(root)
    grant(root, 'a1', ['qa-a'], {'qa-a': 3})
    verdict = refusal(grant, root, 'a1', ['qa-a', 'qa-b'], {'qa-a': 3, 'qa-b': 3})
    assert (verdict['status'] in ra.REFUSED) is expect['blocked']
    assert verdict['status'] == 'payload_conflict'
    assert spend_by_obligation(root) == {'qa-a': 1 + expect['additional_charges']}


def test_a_replayed_grant_never_re_permits_execution(root):
    started(root)
    grant(root, 'a1', ['qa-a'], {'qa-a': 3})
    ra.start(root, 'run-1', 'a1')
    assert grant(root, 'a1', ['qa-a'], {'qa-a': 3})['execution_allowed'] is False


def test_settle_is_idempotent_but_refuses_a_second_different_outcome(root):
    started(root)
    grant(root, 'a1', ['qa-a'], {'qa-a': 3})
    ra.start(root, 'run-1', 'a1')
    assert ra.settle(root, 'a1', 'delivered')['status'] == 'settled'
    assert ra.settle(root, 'a1', 'delivered')['replayed'] is True
    assert refusal(ra.settle, root, 'a1', 'failed')['status'] == 'payload_conflict'


def test_malformed_requests_are_rejected_before_anything_is_charged(root):
    started(root)
    assert refusal(grant, root, '', ['qa-a'], {'qa-a': 1})['status'] == 'invalid'
    assert refusal(grant, root, 'a1', [], {})['status'] == 'invalid'
    assert refusal(grant, root, 'a1', ['qa-a', 'qa-a'], {'qa-a': 1})['status'] == 'invalid'
    assert refusal(grant, root, 'a1', ['qa-a'], {'qa-a': 0})['status'] == 'invalid'
    assert refusal(grant, root, 'a1', ['qa-a'], {})['status'] == 'invalid'
    assert ra.consumption(root)['obligations'] == []


# --- scenario: partial_shared_charge_crash / unknown_execution_after_crash ----------

def test_partial_shared_charge_crash(root):
    expect = scenario('partial_shared_charge_crash')['expect']
    started(root, loops=(('fix', ['qa-a'], 1), ('fix', ['qa-b'], 2)))
    # The refused multi-obligation grant is the observable half of "no partial charge":
    # either both obligations are charged or neither is, never one.
    attempt(root, 'a1', ['qa-a'], {'qa-a': 1})
    before = spend_by_obligation(root)
    refusal(grant, root, 'a2', ['qa-a', 'qa-b'], {'qa-a': 1, 'qa-b': 2})
    charged_partially = spend_by_obligation(root) != before
    assert charged_partially is expect['partial_charge_allowed']
    # And no execution is permitted without a durable grant to claim.
    assert start_permits_execution(root, 'a2') is expect['execution_without_durable_grant']


def test_unknown_execution_after_crash(root):
    expect = scenario('unknown_execution_after_crash')['expect']
    started(root)
    grant(root, 'a1', ['qa-a'], {'qa-a': 3})
    ra.start(root, 'run-1', 'a1')                  # crash here: outcome never recorded
    spent = spend_by_obligation(root)
    # Nothing may re-run on its own ...
    reexecuted = grant_succeeds(root, 'a2', ['qa-a'], {'qa-a': 3})
    assert reexecuted is expect['automatic_reexecution']
    # ... nor may the attempt quietly come back as budget ...
    refunded = spend_by_obligation(root) != spent
    assert refunded is expect['automatic_refund']
    # ... and the only way forward is reconciliation, which itself demands evidence.
    assert (refusal(grant, root, 'a2', ['qa-a'],
                    {'qa-a': 3})['untrusted'] == 'unresolved_authorization'
            ) is expect['reconciliation_required']
    assert refusal(ra.reconcile, root, 'a1', 'executed', None)['status'] == 'blocked'


def test_a_charged_but_never_claimed_grant_also_blocks(root):
    started(root)
    grant(root, 'a1', ['qa-a'], {'qa-a': 3})       # crash between charge and claim
    verdict = refusal(grant, root, 'a2', ['qa-a'], {'qa-a': 3})
    assert verdict['untrusted'] == 'unresolved_authorization'
    assert ra.consumption(root)['unresolved'][0]['state'] == 'authorized'


def test_an_unresolved_grant_blocks_only_its_own_obligations(root):
    started(root)
    grant(root, 'a1', ['qa-a'], {'qa-a': 3}, repair_node_id='fix-a')
    ra.start(root, 'run-1', 'a1')
    # An independent repair loop grants normally while that one is unresolved.
    other = grant(root, 'b1', ['qa-b'], {'qa-b': 3}, repair_node_id='fix-b')
    assert other['status'] == 'authorized'
    assert ra.start(root, 'run-1', 'b1')['execution_allowed'] is True
    assert len(ra.consumption(root)['unresolved']) == 2


def test_reconciliation_requires_evidence_that_can_be_checked(root):
    started(root)
    grant(root, 'a1', ['qa-a'], {'qa-a': 3})
    ra.start(root, 'run-1', 'a1')
    unverifiable = (None, {}, {'basis': 'I think it did not run'},
                    {'source_path': WORKFLOW, 'source_digest': 'sha256:0', 'basis': 'x'},
                    {'source_path': 'nope.json', 'source_digest': 'sha256:0', 'basis': 'x'})
    for evidence in unverifiable:
        assert refusal(ra.reconcile, root, 'a1', 'not_executed',
                       evidence)['untrusted'] == 'unverifiable_evidence'
    assert ra.consumption(root)['unresolved'][0]['authorization_id'] == 'a1'


def test_a_verified_digest_alone_attributes_nothing(root):
    """The audit's core point: a real file with a real digest is not evidence of this."""
    started(root)
    grant(root, 'a1', ['qa-a'], {'qa-a': 3})
    ra.start(root, 'run-1', 'a1')
    bare = {'source_path': WORKFLOW, 'source_digest': ra.file_digest(root / WORKFLOW),
            'basis': 'trust me, it ran'}
    verdict = refusal(ra.reconcile, root, 'a1', 'executed', bare)
    assert verdict['status'] == 'blocked'
    assert verdict['untrusted'] == 'unattributable_evidence'
    # ... and the same bare evidence proves no absence either.
    assert refusal(ra.reconcile, root, 'a1', 'not_executed',
                   bare)['untrusted'] == 'unverifiable_evidence'
    assert ra.consumption(root)['unresolved'][0]['state'] == 'started'


def test_evidence_about_another_node_is_refused(root):
    started(root)
    grant(root, 'a1', ['qa-a'], {'qa-a': 3}, repair_node_id='fix')
    ra.start(root, 'run-1', 'a1')
    verdict = refusal(ra.reconcile, root, 'a1', 'executed', ran(root, node='some-other-node'))
    assert verdict['untrusted'] == 'unattributable_evidence'
    assert verdict['observed']['node'] == 'some-other-node'


def test_evidence_naming_another_authorization_is_refused(root):
    started(root)
    grant(root, 'a1', ['qa-a'], {'qa-a': 3}, repair_node_id='fix')
    ra.start(root, 'run-1', 'a1')
    evidence = ran(root, node='elsewhere', authorization_id='a-different-grant')
    assert refusal(ra.reconcile, root, 'a1', 'executed',
                   evidence)['untrusted'] == 'unattributable_evidence'


def test_an_observation_ref_that_resolves_to_nothing_is_refused(root):
    started(root)
    grant(root, 'a1', ['qa-a'], {'qa-a': 3})
    ra.start(root, 'run-1', 'a1')
    for reference in ('transition_log[9]', 'not_a_field[0]', 'transition_log', ''):
        evidence = dict(ran(root), observation_ref=reference)
        assert refusal(ra.reconcile, root, 'a1', 'executed',
                       evidence)['untrusted'] == 'unattributable_evidence'


def test_evidence_predating_the_execution_claim_is_refused(root):
    started(root)
    grant(root, 'a1', ['qa-a'], {'qa-a': 3})
    ra.start(root, 'run-1', 'a1')
    stale = ran(root, at='2000-01-01T00:00:00Z')
    verdict = refusal(ra.reconcile, root, 'a1', 'executed', stale)
    assert verdict['untrusted'] == 'unattributable_evidence'
    assert verdict['observed_at'] == '2000-01-01T00:00:00Z'


def test_absence_must_be_proved_against_a_log_asserted_complete(root):
    started(root)
    grant(root, 'a1', ['qa-a'], {'qa-a': 3})
    ra.start(root, 'run-1', 'a1')
    incomplete = dict(never_ran(root))
    incomplete.pop('complete')
    assert refusal(ra.reconcile, root, 'a1', 'not_executed',
                   incomplete)['untrusted'] == 'unverifiable_evidence'
    missing_field = dict(never_ran(root), absence_of='no_such_log')
    assert refusal(ra.reconcile, root, 'a1', 'not_executed',
                   missing_field)['untrusted'] == 'unverifiable_evidence'


def test_a_log_that_records_the_run_cannot_prove_it_did_not_run(root):
    started(root)
    grant(root, 'a1', ['qa-a'], {'qa-a': 3}, repair_node_id='fix')
    ra.start(root, 'run-1', 'a1')
    contradicted = never_ran(root, log=[{'node': 'fix', 'status': 'completed',
                                         'at': '2099-01-01T00:00:00Z'}])
    verdict = refusal(ra.reconcile, root, 'a1', 'not_executed', contradicted)
    assert verdict['untrusted'] == 'unattributable_evidence'
    assert verdict['contradicting'] == [0]


def test_absence_ignores_records_predating_the_claim(root):
    started(root)
    grant(root, 'a1', ['qa-a'], {'qa-a': 3}, repair_node_id='fix')
    ra.start(root, 'run-1', 'a1')
    # An earlier run of the same node is not this attempt, so it does not contradict.
    evidence = never_ran(root, log=[{'node': 'fix', 'status': 'completed',
                                     'at': '2000-01-01T00:00:00Z'}])
    assert ra.reconcile(root, 'a1', 'not_executed', evidence)['status'] == 'ok'


@pytest.mark.parametrize('determination,build', [('executed', ran),
                                                 ('not_executed', never_ran)])
def test_reconciliation_from_attributable_evidence_never_refunds(root, determination, build):
    started(root)
    grant(root, 'a1', ['qa-a'], {'qa-a': 3}, repair_node_id='fix')
    ra.start(root, 'run-1', 'a1')
    verdict = ra.reconcile(root, 'a1', determination, build(root))
    assert verdict['status'] == 'ok' and verdict['refunded'] is False
    # The next grant continues from attempt 2; a crash does not hand attempt 1 back.
    assert grant(root, 'a2', ['qa-a'], {'qa-a': 3})['charged'] == {'qa-a': 2}
    recorded = json.loads((root / LEDGER).read_text())['authorizations'][0]
    reconciliation = recorded['provenance']['reconciliation']
    assert reconciliation['determination'] == determination
    assert reconciliation['attribution']['kind'] == (
        'execution_record' if determination == 'executed' else 'complete_log_absence')


# --- settle may only assert what the ledger already proves -------------------------

def test_an_unknown_settlement_cannot_resolve_an_uncertain_execution(root):
    """The bypass this audit was for: settle(unknown) was reconcile without evidence.

    A claimed attempt whose outcome nobody saw must not become resolved by saying so.
    If it could, the next authorization would rerun work that may already have run.
    """
    started(root)
    grant(root, 'a1', ['qa-a'], {'qa-a': 3})
    ra.start(root, 'run-1', 'a1')                       # crash: nobody saw the outcome
    assert refusal(ra.settle, root, 'a1', 'unknown')['status'] == 'invalid'
    # The blocker is still standing, so no reauthorization slips through behind it.
    assert ra.consumption(root)['unresolved'][0]['state'] == 'started'
    assert refusal(grant, root, 'a2', ['qa-a'],
                   {'qa-a': 3})['untrusted'] == 'unresolved_authorization'


def test_aborting_a_claimed_attempt_is_a_determination_not_a_settlement(root):
    started(root)
    grant(root, 'a1', ['qa-a'], {'qa-a': 3})
    ra.start(root, 'run-1', 'a1')
    verdict = refusal(ra.settle, root, 'a1', 'aborted')
    assert verdict['status'] == 'blocked'
    assert verdict['untrusted'] == 'undetermined_execution'
    assert verdict['settleable'] == ['delivered', 'failed']
    assert refusal(grant, root, 'a2', ['qa-a'],
                   {'qa-a': 3})['untrusted'] == 'unresolved_authorization'


@pytest.mark.parametrize('outcome', ['delivered', 'failed'])
def test_an_unclaimed_grant_cannot_report_an_execution_outcome(root, outcome):
    """A forged outcome: reporting how an execution went that was never claimed."""
    started(root)
    grant(root, 'a1', ['qa-a'], {'qa-a': 3})            # charged, never started
    verdict = refusal(ra.settle, root, 'a1', outcome)
    assert verdict['status'] == 'blocked'
    assert verdict['untrusted'] == 'unclaimed_execution'
    assert verdict['settleable'] == ['aborted']


def test_an_unclaimed_grant_may_be_abandoned(root):
    started(root)
    grant(root, 'a1', ['qa-a'], {'qa-a': 3})
    # The ledger itself proves nothing ran, so abandoning it needs no outside evidence.
    assert ra.settle(root, 'a1', 'aborted')['refunded'] is False
    assert ra.consumption(root)['unresolved'] == []
    # It is still spent: abandoning a grant is not getting the attempt back.
    assert grant(root, 'a2', ['qa-a'], {'qa-a': 3})['charged'] == {'qa-a': 2}


def test_settling_a_claimed_attempt_records_what_its_execution_did(root):
    started(root)
    grant(root, 'a1', ['qa-a'], {'qa-a': 3})
    ra.start(root, 'run-1', 'a1')
    assert ra.settle(root, 'a1', 'delivered')['outcome'] == 'delivered'
    assert ra.consumption(root)['unresolved'] == []


def test_no_settlement_path_reaches_unknown(root):
    """`unknown` is reconcile's to record, so settle can never produce it."""
    started(root, loops=(('fix', ['qa-authorized', 'qa-started'], None),))
    for state_setup in ('authorized', 'started'):
        identifier = f'a-{state_setup}'
        grant(root, identifier, [f'qa-{state_setup}'], {f'qa-{state_setup}': 3})
        if state_setup == 'started':
            ra.start(root, 'run-1', identifier)
        assert refusal(ra.settle, root, identifier, 'unknown')['status'] == 'invalid'
    outcomes = {e.get('outcome') for e in
                json.loads((root / LEDGER).read_text())['authorizations']}
    assert 'unknown' not in outcomes


def test_an_unrelated_file_correctly_hashed_reconciles_nothing(root):
    """A true digest of the wrong document is still not evidence about this attempt."""
    started(root)
    grant(root, 'a1', ['qa-a'], {'qa-a': 3}, repair_node_id='fix')
    ra.start(root, 'run-1', 'a1')
    unrelated = root / '.allforai/bootstrap/some-other-report.json'
    unrelated.write_text(json.dumps({'transition_log': [
        {'node': 'an-unrelated-node', 'status': 'completed', 'at': '2099-01-01T00:00:00Z'}]}))
    evidence = {'source_path': '.allforai/bootstrap/some-other-report.json',
                'source_digest': ra.file_digest(unrelated),
                'observation_ref': 'transition_log[0]',
                'basis': 'a genuine report, about entirely different work'}
    verdict = refusal(ra.reconcile, root, 'a1', 'executed', evidence)
    assert verdict['status'] == 'blocked'
    assert verdict['untrusted'] == 'unattributable_evidence'
    # Its absence half fails too: an unrelated document holds no trace of this attempt
    # whether or not it ran, so emptiness there proves nothing.
    absence = {'source_path': '.allforai/bootstrap/some-other-report.json',
               'source_digest': ra.file_digest(unrelated), 'absence_of': 'transition_log',
               'complete': True, 'basis': 'nothing about this node in here'}
    refused = refusal(ra.reconcile, root, 'a1', 'not_executed', absence)
    assert refused['untrusted'] == 'unattributable_evidence'
    assert refused['expected_source'] == WORKFLOW
    assert ra.consumption(root)['unresolved'][0]['authorization_id'] == 'a1'
    assert spend_by_obligation(root) == {'qa-a': 1}


def test_absence_must_be_proved_against_the_runs_own_execution_record(root):
    started(root)
    grant(root, 'a1', ['qa-a'], {'qa-a': 3}, repair_node_id='fix')
    ra.start(root, 'run-1', 'a1')
    elsewhere = root / '.allforai/bootstrap/other-log.json'
    elsewhere.write_text(json.dumps({'transition_log': []}))
    evidence = {'source_path': '.allforai/bootstrap/other-log.json',
                'source_digest': ra.file_digest(elsewhere), 'absence_of': 'transition_log',
                'complete': True, 'basis': 'an empty log somewhere else'}
    assert refusal(ra.reconcile, root, 'a1', 'not_executed',
                   evidence)['untrusted'] == 'unattributable_evidence'
    # The run's own record, asserted complete, does prove it.
    assert ra.reconcile(root, 'a1', 'not_executed', never_ran(root))['status'] == 'ok'


def test_reauthorization_after_a_refused_settlement_is_still_blocked(root):
    """Every refused shortcut leaves the blocker exactly where it was."""
    started(root)
    grant(root, 'a1', ['qa-a'], {'qa-a': 3})
    ra.start(root, 'run-1', 'a1')
    for call in (lambda: ra.settle(root, 'a1', 'unknown'),
                 lambda: ra.settle(root, 'a1', 'aborted'),
                 lambda: ra.reconcile(root, 'a1', 'executed', None),
                 lambda: ra.reconcile(root, 'a1', 'executed',
                                      {'source_path': WORKFLOW,
                                       'source_digest': ra.file_digest(root / WORKFLOW),
                                       'basis': 'no reference at all'})):
        with pytest.raises(ra.Refusal):
            call()
        assert refusal(grant, root, 'a2', ['qa-a'],
                       {'qa-a': 3})['untrusted'] == 'unresolved_authorization'
        assert spend_by_obligation(root) == {'qa-a': 1}


# --- scenario: missing_historical_ledger -------------------------------------------

def test_missing_historical_ledger(root):
    expect = scenario('missing_historical_ledger')['expect']
    write_workflow(root, repair_routes=[{'repair_node_id': 'fix', 'qa_node_id': 'qa-a',
                                         'attempt': 1}])
    verdict = refusal(grant, root, 'a1', ['qa-a'], {'qa-a': 3})
    # A run whose ledger is absent is neither readable as zero nor allowed to proceed.
    assert (verdict['status'] == 'authorized') is expect['assume_zero_consumption']
    assert (verdict['status'] in ra.REFUSED) is expect['blocked']
    assert verdict['untrusted'] == 'missing_ledger'
    # And the run cannot be declared new either: the workflow shows it already executed.
    origin = refusal(ra.initialize, root, 'run-1')
    assert origin['untrusted'] == 'prior_execution'
    assert origin['observed']['repair_routes'] == 1


def test_a_missing_ledger_is_not_zero_consumption(root):
    write_workflow(root)
    assert refusal(grant, root, 'a1', ['qa-a'],
                   {'qa-a': 3})['untrusted'] == 'missing_ledger'
    assert refusal(ra.consumption, root)['untrusted'] == 'missing_ledger'
    assert not (root / LEDGER).exists()


@pytest.mark.parametrize('damage', [
    '{"ledger_version": 1, "run_id": "run-1"',                                  # truncated
    '[]',                                                                       # wrong shape
    '{"ledger_version": 99, "run_id": "r", "origin": {}, "authorizations": []}',
])
def test_an_unreadable_ledger_blocks(root, damage):
    started(root)
    (root / LEDGER).write_text(damage)
    assert refusal(grant, root, 'a1', ['qa-a'],
                   {'qa-a': 3})['untrusted'] == 'unreadable_ledger'


@pytest.mark.parametrize('mutate', [
    lambda e: e.pop('state'),
    lambda e: e.update(state='running'),
    lambda e: e.pop('charged'),
    lambda e: e.update(charged={'other': 1}),
    lambda e: e.update(charged={'qa-a': 0}),
    lambda e: e.pop('obligations'),
    lambda e: e.update(authorization_id=''),
])
def test_an_entry_whose_spend_cannot_be_read_exactly_blocks(root, mutate):
    started(root)
    grant(root, 'a1', ['qa-a'], {'qa-a': 3})
    ledger = json.loads((root / LEDGER).read_text())
    mutate(ledger['authorizations'][0])
    (root / LEDGER).write_text(json.dumps(ledger))
    assert refusal(ra.consumption, root)['untrusted'] == 'unreadable_ledger'


def test_a_duplicated_entry_makes_the_spend_ambiguous_and_blocks(root):
    started(root)
    grant(root, 'a1', ['qa-a'], {'qa-a': 3})
    ledger = json.loads((root / LEDGER).read_text())
    ledger['authorizations'].append(dict(ledger['authorizations'][0]))
    (root / LEDGER).write_text(json.dumps(ledger))
    assert refusal(ra.consumption, root)['untrusted'] == 'unreadable_ledger'


# --- a new run is verified on disk, never asserted ---------------------------------

def test_a_new_run_is_proved_from_the_workflow_not_from_the_caller(root):
    write_workflow(root)
    verdict = ra.initialize(root, 'run-1')
    assert verdict['proof']['kind'] == 'verified_untouched_workflow'
    assert verdict['proof']['source_digest'] == ra.file_digest(root / WORKFLOW)
    assert verdict['proof']['observed'] == {'transition_log': 0, 'repair_routes': 0,
                                            'completed': 0}
    assert verdict['binding']['loops'] == 0


@pytest.mark.parametrize('fields,observed', [
    ({'transition_log': [{'node': 'build', 'status': 'completed'}]}, 'transition_log'),
    ({'repair_routes': [{'repair_node_id': 'fix', 'qa_node_id': 'qa-a', 'attempt': 1}]},
     'repair_routes'),
    ({'nodes': [{'node_id': 'build', 'status': 'completed'}]}, 'completed'),
])
def test_a_workflow_that_already_executed_may_not_be_declared_new(root, fields, observed):
    write_workflow(root, **fields)
    verdict = refusal(ra.initialize, root, 'run-1')
    assert verdict['status'] == 'blocked' and verdict['untrusted'] == 'prior_execution'
    assert verdict['observed'][observed] == 1
    assert not (root / LEDGER).exists()


@pytest.mark.parametrize('setup,untrusted', [
    (lambda root: None, 'missing_workflow'),
    (lambda root: (root / WORKFLOW).write_text('{not json'), 'unreadable_workflow'),
])
def test_a_run_with_no_readable_workflow_cannot_be_declared_new(root, setup, untrusted):
    setup(root)
    assert refusal(ra.initialize, root, 'run-1')['untrusted'] == untrusted


def test_reinitializing_the_same_run_is_a_replay_and_keeps_its_history(root):
    started(root)
    grant(root, 'a1', ['qa-a'], {'qa-a': 3})
    verdict = ra.initialize(root, 'run-1')
    assert verdict['replayed'] is True and verdict['authorizations'] == 1
    assert spend_by_obligation(root) == {'qa-a': 1}


def test_a_different_run_may_not_replace_the_existing_accounting(root):
    started(root)
    attempt(root, 'a1', ['qa-a'], {'qa-a': 3})
    verdict = refusal(ra.initialize, root, 'run-2')
    assert verdict['status'] == 'blocked' and verdict['untrusted'] == 'existing_run'
    assert verdict['existing_run_id'] == 'run-1'
    assert ra.consumption(root)['run_id'] == 'run-1'
    assert spend_by_obligation(root) == {'qa-a': 1}


def test_a_grant_for_another_run_is_refused(root):
    started(root)
    assert refusal(grant, root, 'a1', ['qa-a'], {'qa-a': 3},
                   run_id='run-2')['untrusted'] == 'run_identity_mismatch'


def test_the_binding_covers_declared_loops_not_moving_execution_state(root):
    loops = [{'repair_node_id': 'fix', 'qa_node_ids': ['qa-a'], 'max_attempts': 3}]
    write_workflow(root, required_repair_loops=loops)
    plan(root, ('fix', ['qa-a'], 3))
    binding = ra.initialize(root, 'run-1')['binding']
    assert binding['loops'] == 1
    # Expansion that adds a loop changes the binding without invalidating the ledger:
    # a newly declared obligation simply has no history to lose.
    write_workflow(root, required_repair_loops=loops + [
        {'repair_node_id': 'fix2', 'qa_node_ids': ['qa-b'], 'max_attempts': 3}])
    plan(root, ('fix', ['qa-a'], 3), ('fix2', ['qa-b'], 3))
    assert ra.loop_binding(json.loads((root / WORKFLOW).read_text()))['loops'] == 2
    assert grant(root, 'a1', ['qa-b'], {'qa-b': 3},
                 repair_node_id='fix2')['charged'] == {'qa-b': 1}
    assert ra.consumption(root)['binding'] == binding


# --- historical recovery only from verified, attributable evidence -----------------

ROUTES = [{'repair_node_id': 'fix', 'qa_node_id': 'qa-a', 'attempt': 1,
           'dispatched_at': '2026-09-01T00:00:00Z'},
          {'repair_node_id': 'fix', 'qa_node_id': 'qa-b', 'attempt': 1,
           'dispatched_at': '2026-09-01T00:01:00Z'}]
# What a legacy source records about execution, separately from the charge. A
# repair_routes entry alone says only that an attempt was paid for.
TRANSITIONS = [{'node': 'fix', 'status': 'completed', 'at': '2026-09-01T00:00:30Z'},
               {'node': 'fix', 'status': 'failed', 'at': '2026-09-01T00:01:30Z'}]


def history(root, routes=None, transitions=None, state='settled', loops=None):
    """Legacy evidence: the charges, plus the records that show how they ended."""
    routes = ROUTES if routes is None else routes
    transitions = TRANSITIONS if transitions is None else transitions
    write_workflow(root, repair_routes=routes, transition_log=transitions)
    plan(root, *(loops if loops is not None else DEFAULT_PLAN))
    records = []
    for index, route in enumerate(routes):
        record = {'authorization_id': f'legacy-{index}',
                  'repair_node_id': route['repair_node_id'],
                  'obligations': [route['qa_node_id']],
                  'charged': {route['qa_node_id']: route['attempt']},
                  'budgets': {route['qa_node_id']: 3}, 'state': state,
                  'source_ref': f'repair_routes[{index}]'}
        if state == 'settled':
            record['settlement_ref'] = f'transition_log[{index}]'
        elif state == 'started':
            record['start_ref'] = f'transition_log[{index}]'
        records.append(record)
    return {'source_path': WORKFLOW, 'source_digest': ra.file_digest(root / WORKFLOW),
            'complete': True, 'authorizations': records}


def test_complete_verified_history_is_adopted_with_its_provenance(root):
    evidence = history(root)
    verdict = ra.adopt_history(root, 'run-1', evidence)
    assert verdict['status'] == 'ok' and verdict['adopted'] == 2
    entry = json.loads((root / LEDGER).read_text())['authorizations'][0]
    assert entry['provenance']['adopted_from'] == 'repair_routes[0]'
    assert entry['provenance']['source'].endswith(evidence['source_digest'])
    assert entry['provenance']['route'] == ROUTES[0]
    assert ra.consumption(root)['origin'] == 'adopted_history'
    # Spend continues from the adopted history rather than restarting at one.
    assert grant(root, 'a2', ['qa-a'], {'qa-a': 3})['charged'] == {'qa-a': 2}


def test_adopted_history_can_exhaust_a_budget_immediately(root):
    evidence = history(root, [{'repair_node_id': 'fix', 'qa_node_id': 'qa-a', 'attempt': 1},
                              {'repair_node_id': 'fix', 'qa_node_id': 'qa-a', 'attempt': 2}],
                       loops=(('fix', ['qa-a', 'qa-b'], 2),))
    for record in evidence['authorizations']:
        record['budgets'] = {'qa-a': 2}
    evidence['authorizations'][1]['charged'] = {'qa-a': 2}
    ra.adopt_history(root, 'run-1', evidence)
    assert refusal(grant, root, 'a3', ['qa-a'], {'qa-a': 2})['status'] == 'budget_exhausted'


def test_an_adopted_unresolved_authorization_still_needs_reconciliation(root):
    evidence = history(root, [ROUTES[0]], state='started')
    assert ra.adopt_history(root, 'run-1', evidence)['unresolved'] == ['legacy-0']
    assert refusal(grant, root, 'a2', ['qa-a'],
                   {'qa-a': 3})['untrusted'] == 'unresolved_authorization'


def test_a_bare_charge_may_only_be_adopted_as_charged(root):
    """A repair_routes entry proves a charge. It cannot be read as an execution."""
    evidence = history(root, [ROUTES[0]], state='settled')
    evidence['authorizations'][0].pop('settlement_ref')
    verdict = refusal(ra.adopt_history, root, 'run-1', evidence)
    assert verdict['status'] == 'blocked' and verdict['untrusted'] == 'ambiguous_history'
    assert 'charged' in verdict['reason'] and 'authorized' in verdict['reason']
    # Adopted honestly as a charge, it is accepted — and it blocks until reconciled.
    charge_only = history(root, [ROUTES[0]], state='authorized')
    assert ra.adopt_history(root, 'run-1', charge_only)['unresolved'] == ['legacy-0']
    assert refusal(grant, root, 'a2', ['qa-a'],
                   {'qa-a': 3})['untrusted'] == 'unresolved_authorization'


def test_an_adopted_outcome_is_derived_from_the_evidence_not_declared(root):
    evidence = history(root, ROUTES, transitions=[
        {'node': 'fix', 'status': 'completed', 'at': '2026-09-01T00:00:30Z'},
        {'node': 'fix', 'status': 'failed', 'at': '2026-09-01T00:01:30Z'}])
    ra.adopt_history(root, 'run-1', evidence)
    outcomes = {e['authorization_id']: e['outcome']
                for e in json.loads((root / LEDGER).read_text())['authorizations']}
    assert outcomes == {'legacy-0': 'delivered', 'legacy-1': 'failed'}


def test_a_forged_outcome_that_contradicts_the_evidence_is_refused(root):
    """The record does not get to overrule the source it cites."""
    evidence = history(root, [ROUTES[0]], transitions=[
        {'node': 'fix', 'status': 'failed', 'at': '2026-09-01T00:00:30Z'}])
    evidence['authorizations'][0]['outcome'] = 'delivered'
    verdict = refusal(ra.adopt_history, root, 'run-1', evidence)
    assert verdict['status'] == 'blocked' and verdict['untrusted'] == 'ambiguous_history'
    assert 'delivered' in verdict['reason'] and 'failed' in verdict['reason']
    assert not (root / LEDGER).exists()


def test_a_settlement_ref_must_point_at_a_record_that_ends_the_attempt(root):
    evidence = history(root, [ROUTES[0]], transitions=[
        {'node': 'fix', 'status': 'running', 'at': '2026-09-01T00:00:30Z'}])
    verdict = refusal(ra.adopt_history, root, 'run-1', evidence)
    assert verdict['untrusted'] == 'ambiguous_history'
    assert 'terminal' in verdict['reason']


def test_execution_evidence_about_another_node_cannot_settle_a_legacy_charge(root):
    evidence = history(root, [ROUTES[0]], transitions=[
        {'node': 'a-completely-different-node', 'status': 'completed',
         'at': '2026-09-01T00:00:30Z'}])
    verdict = refusal(ra.adopt_history, root, 'run-1', evidence)
    assert verdict['status'] == 'blocked'
    assert verdict['untrusted'] == 'unattributable_evidence'


def test_a_settlement_ref_that_resolves_to_nothing_is_refused(root):
    evidence = history(root, [ROUTES[0]])
    evidence['authorizations'][0]['settlement_ref'] = 'transition_log[7]'
    assert refusal(ra.adopt_history, root, 'run-1',
                   evidence)['untrusted'] == 'ambiguous_history'


@pytest.mark.parametrize('mutate,untrusted', [
    (lambda h: h.update(complete=False), 'incomplete_history'),
    (lambda h: h.pop('complete'), 'incomplete_history'),
    (lambda h: h['authorizations'].pop(), 'incomplete_history'),
    (lambda h: h.update(source_digest='sha256:0'), 'unverifiable_evidence'),
    (lambda h: h.pop('source_digest'), 'unverifiable_evidence'),
    (lambda h: h.update(source_path='../escape.json'), 'unverifiable_evidence'),
    (lambda h: h['authorizations'][0].pop('source_ref'), 'ambiguous_history'),
    (lambda h: h['authorizations'][0].update(source_ref='repair_routes[9]'), 'ambiguous_history'),
    (lambda h: h['authorizations'][1].update(source_ref='repair_routes[0]'), 'ambiguous_history'),
    (lambda h: h['authorizations'][0].pop('authorization_id'), 'ambiguous_history'),
    (lambda h: h['authorizations'][0].update(repair_node_id='other'), 'ambiguous_history'),
    (lambda h: h['authorizations'][0].update(obligations=['qa-z']), 'ambiguous_history'),
    (lambda h: h['authorizations'][0].pop('state'), 'ambiguous_history'),
    (lambda h: h['authorizations'][0].pop('charged'), 'ambiguous_history'),
    (lambda h: h['authorizations'][0].update(charged={'qa-a': 0}), 'ambiguous_history'),
    (lambda h: h['authorizations'][0].pop('settlement_ref'), 'ambiguous_history'),
    (lambda h: h['authorizations'][0].update(settlement_ref='transition_log[0]',
                                             outcome='aborted'), 'ambiguous_history'),
])
def test_incomplete_or_ambiguous_history_leaves_the_run_blocked(root, mutate, untrusted):
    evidence = history(root)
    mutate(evidence)
    verdict = refusal(ra.adopt_history, root, 'run-1', evidence)
    assert verdict['status'] == 'blocked' and verdict['untrusted'] == untrusted
    # Nothing was written, so the run stays blocked rather than starting at zero.
    assert not (root / LEDGER).exists()
    assert refusal(grant, root, 'a1', ['qa-a'], {'qa-a': 3})['untrusted'] == 'missing_ledger'


def test_a_source_with_no_legacy_ledger_offers_nothing_to_reconstruct(root):
    write_workflow(root)
    evidence = {'source_path': WORKFLOW, 'source_digest': ra.file_digest(root / WORKFLOW),
                'complete': True, 'authorizations': []}
    assert refusal(ra.adopt_history, root, 'run-1',
                   evidence)['untrusted'] == 'unverifiable_evidence'


def test_history_may_not_be_adopted_over_live_accounting(root):
    started(root)
    grant(root, 'a1', ['qa-a'], {'qa-a': 3})
    evidence = history(root)
    verdict = refusal(ra.adopt_history, root, 'run-1', evidence)
    assert verdict['status'] == 'blocked' and verdict['existing_run_id'] == 'run-1'
    assert ra.consumption(root)['origin'] == 'new_run'


# --- durability, concurrency, and isolation ----------------------------------------

def spawn(root, requests):
    """Run each request in its own process, all at once."""
    with ThreadPoolExecutor(max_workers=len(requests)) as pool:
        return [f.result() for f in [pool.submit(cli, root, r) for r in requests]]


def test_concurrent_distinct_dispatches_cannot_overspend_a_budget(root):
    started(root, loops=(('fix', ['qa-a', 'qa-b'], 1),))
    verdicts = [v for _, v in spawn(root, [
        {'operation': 'authorize', 'run_id': 'run-1', 'authorization_id': f'c{i}',
         'repair_node_id': 'fix', 'obligations': ['qa-a'], 'budgets': {'qa-a': 1}}
        for i in range(8)])]
    statuses = [v['status'] for v in verdicts]
    # Exactly one grant fits the bound. The rest are refused, not queued behind it.
    assert statuses.count('authorized') == 1
    assert set(statuses) <= {'authorized', 'budget_exhausted', 'blocked'}
    assert spend_by_obligation(root) == {'qa-a': 1}


def test_concurrent_replays_of_one_dispatch_charge_exactly_once(root):
    started(root)
    request = {'operation': 'authorize', 'run_id': 'run-1', 'authorization_id': 'same',
               'repair_node_id': 'fix', 'obligations': ['qa-a', 'qa-b'],
               'budgets': {'qa-a': 3, 'qa-b': 3}}
    verdicts = [v for _, v in spawn(root, [dict(request) for _ in range(8)])]
    assert [v['status'] for v in verdicts].count('authorized') == 1
    assert all(v['status'] in ('authorized', 'replayed') for v in verdicts)
    assert all(v['execution_allowed'] is False for v in verdicts)
    assert set(spend_by_obligation(root).values()) == {1}


def test_concurrent_starts_claim_the_execution_exactly_once(root):
    started(root)
    grant(root, 'a1', ['qa-a'], {'qa-a': 3})
    verdicts = [v for _, v in spawn(root, [
        {'operation': 'start', 'run_id': 'run-1', 'authorization_id': 'a1'}
        for _ in range(8)])]
    assert [v['execution_allowed'] for v in verdicts].count(True) == 1
    assert all(v['status'] == 'started' for v in verdicts)


def test_concurrent_writers_never_leave_a_partial_entry(root):
    started(root, loops=tuple((f'fix-{i}', [f'qa-{i}a', f'qa-{i}b'], 2) for i in range(8)))
    # Eight repair loops that legitimately run at once, each charging two obligations.
    verdicts = [v for _, v in spawn(root, [
        {'operation': 'authorize', 'run_id': 'run-1', 'authorization_id': f'p{i}',
         'repair_node_id': f'fix-{i}', 'obligations': [f'qa-{i}a', f'qa-{i}b'],
         'budgets': {f'qa-{i}a': 2, f'qa-{i}b': 2}} for i in range(8)])]
    assert all(v['status'] == 'authorized' for v in verdicts)
    # A torn or half-charged entry would make the ledger unreadable; it stays readable,
    # every dispatch survives the interleaving, and no obligation is charged twice.
    report = ra.consumption(root)
    assert len(report['obligations']) == 16
    assert {o['spent'] for o in report['obligations']} == {1}
    assert len(json.loads((root / LEDGER).read_text())['authorizations']) == 8


def test_an_abandoned_lock_reports_a_blocker_instead_of_removing_it(root):
    started(root)
    lock = root / '.allforai/bootstrap/repair-authorizations.lock'
    lock.mkdir()
    with pytest.raises(ra.Refusal) as caught:
        with ra.ledger_lock(root, attempts=2, interval=0.001):
            pass
    assert caught.value.verdict['status'] == 'blocked'
    # Never cleared on the owner's behalf: a crashed writer is reconciled, not guessed at.
    assert lock.is_dir()


def test_the_lock_is_released_after_every_grant_and_every_refusal(root):
    started(root, loops=(('fix', ['qa-a', 'qa-b'], 1),))
    attempt(root, 'a1', ['qa-a'], {'qa-a': 1})
    refusal(grant, root, 'a2', ['qa-a'], {'qa-a': 1})
    assert not (root / '.allforai/bootstrap/repair-authorizations.lock').exists()
    with ra.ledger_lock(root, attempts=2, interval=0.001):
        pass


def test_the_ledger_never_writes_the_workflow_document(root):
    started(root)
    before = (root / WORKFLOW).read_bytes()
    grant(root, 'a1', ['qa-a'], {'qa-a': 3})
    ra.start(root, 'run-1', 'a1')
    ra.settle(root, 'a1', 'delivered')
    ra.consumption(root)
    assert (root / WORKFLOW).read_bytes() == before


# --- the CLI decides identically and says so in its exit code ----------------------

def test_cli_runs_a_whole_attempt(root):
    write_workflow(root)
    plan(root, ('fix', ['qa-a'], 1))
    for request, status, code in [
            ({'operation': 'initialize', 'run_id': 'run-1'}, 'ok', 0),
            ({'operation': 'authorize', 'run_id': 'run-1', 'authorization_id': 'a1',
              'repair_node_id': 'fix', 'obligations': ['qa-a'], 'budgets': {'qa-a': 1}},
             'authorized', 0),
            ({'operation': 'start', 'run_id': 'run-1', 'authorization_id': 'a1'},
             'started', 0),
            ({'operation': 'settle', 'authorization_id': 'a1', 'outcome': 'failed'},
             'settled', 0),
            ({'operation': 'consumption'}, 'ok', 0)]:
        result, verdict = cli(root, request)
        assert (verdict['status'], result.returncode) == (status, code), request


@pytest.mark.parametrize('request_body,status', [
    ({'operation': 'authorize', 'run_id': 'run-1', 'authorization_id': 'x',
      'repair_node_id': 'fix', 'obligations': ['qa-a'], 'budgets': {'qa-a': 1}}, 'blocked'),
    ({'operation': 'start', 'run_id': 'run-1', 'authorization_id': 'x'}, 'blocked'),
    ({'operation': 'consumption'}, 'blocked'),
    ({'operation': 'nonsense'}, 'invalid'),
])
def test_cli_exits_non_zero_on_every_refusal(root, request_body, status):
    write_workflow(root)
    result, verdict = cli(root, request_body)
    assert result.returncode == 1 and verdict['status'] == status
    assert verdict['reason'] and (verdict.get('untrusted') or status == 'invalid')


def test_cli_and_python_api_reach_the_same_verdict(root):
    started(root, loops=(('fix', ['qa-a', 'qa-b'], 1),))
    attempt(root, 'a1', ['qa-a'], {'qa-a': 1})
    result, verdict = cli(root, {'operation': 'authorize', 'run_id': 'run-1',
                                 'authorization_id': 'a2', 'repair_node_id': 'fix',
                                 'obligations': ['qa-a'], 'budgets': {'qa-a': 1}})
    assert result.returncode == 1 and verdict['status'] == 'budget_exhausted'
    assert refusal(grant, root, 'a3', ['qa-a'], {'qa-a': 1})['status'] == 'budget_exhausted'


def test_new_authorization_ids_are_unique(root):
    assert len({ra.new_authorization_id() for _ in range(100)}) == 100


# --- evidence has to pick out one attempt --------------------------------------------
# Regressions for the independently reproduced recovery findings
# (docs/grillstorm/meta-intent/replan-2/systematic-ledger-independent-review.md). Each
# one failed open before: it accepted evidence that fits some other attempt, some other
# list, or no time at all, and cleared a blocker on it.

def test_a_record_naming_another_authorization_never_falls_back_to_its_node(root):
    """A record that says which grant it is about has already answered the question."""
    started(root)
    # One repair node, two obligations, two grants that are legitimately unresolved at
    # once — the shared-repair shape ADR 0005 requires.
    for identifier, obligation in (('a1', 'qa-a'), ('a2', 'qa-b')):
        grant(root, identifier, [obligation], {obligation: 3}, repair_node_id='fix')
        ra.start(root, 'run-1', identifier)
    evidence = ran(root, node='fix', authorization_id='a2')
    verdict = refusal(ra.reconcile, root, 'a1', 'executed', evidence)
    assert verdict['untrusted'] == 'unattributable_evidence'
    assert verdict['observed']['authorization_id'] == 'a2'
    # a1 is still unresolved, so its budget is still not re-grantable.
    assert ra.consumption(root)['unresolved'][0]['authorization_id'] == 'a1'


def test_a_node_only_record_cannot_pick_one_of_several_unresolved_attempts(root):
    started(root)
    for identifier, obligation in (('a1', 'qa-a'), ('a2', 'qa-b')):
        grant(root, identifier, [obligation], {obligation: 3}, repair_node_id='fix')
        ra.start(root, 'run-1', identifier)
    evidence = ran(root, node='fix')                       # names the node, not the grant
    verdict = refusal(ra.reconcile, root, 'a1', 'executed', evidence)
    assert verdict['untrusted'] == 'unattributable_evidence' and verdict['rivals'] == ['a2']
    # Resolve the rival and the same record identifies a1 alone.
    ra.settle(root, 'a2', 'failed')
    assert ra.reconcile(root, 'a1', 'executed', evidence)['status'] == 'ok'


def test_an_undated_record_cannot_show_that_this_attempt_ran(root):
    started(root)
    grant(root, 'a1', ['qa-a'], {'qa-a': 3}, repair_node_id='fix')
    ra.start(root, 'run-1', 'a1')
    undated = ran(root, node='fix')
    undated_record = {'node': 'fix', 'status': 'completed'}
    write_workflow(root, transition_log=[undated_record])
    undated['source_digest'] = ra.file_digest(root / WORKFLOW)
    verdict = refusal(ra.reconcile, root, 'a1', 'executed', undated)
    assert verdict['untrusted'] == 'unattributable_evidence'


def test_absence_is_measured_against_the_execution_log_not_another_list(root):
    """`repair_routes` keys its entries by repair_node_id, so it is 'absent' of every run."""
    started(root)
    grant(root, 'a1', ['qa-a'], {'qa-a': 3}, repair_node_id='fix')
    ra.start(root, 'run-1', 'a1')
    write_workflow(root, transition_log=[{'node': 'fix', 'status': 'completed',
                                          'at': '2099-01-01T00:00:00Z'}],
                   repair_routes=[{'repair_node_id': 'fix', 'qa_node_id': 'qa-a'}])
    evidence = {'source_path': WORKFLOW, 'source_digest': ra.file_digest(root / WORKFLOW),
                'complete': True, 'basis': 'nothing in the routes', 'absence_of': 'repair_routes'}
    verdict = refusal(ra.reconcile, root, 'a1', 'not_executed', evidence)
    assert verdict['untrusted'] == 'unverifiable_evidence'
    assert verdict['expected_absence_of'] == 'transition_log'
    # Against the log that does record execution, the same document refutes the claim.
    evidence['absence_of'] = 'transition_log'
    assert refusal(ra.reconcile, root, 'a1', 'not_executed',
                   evidence)['contradicting'] == [0]


# --- history is reconstructed from the run's own record -------------------------------

def test_history_may_only_be_reconstructed_from_the_runs_own_workflow(root):
    """A correctly digested file the caller wrote is not attributable evidence."""
    write_workflow(root, repair_routes=ROUTES, transition_log=TRANSITIONS,
                   nodes=[{'node_id': 'build', 'status': 'completed'}])
    forged = root / 'legacy-evidence.json'
    forged.write_text(json.dumps({'repair_routes': []}))
    evidence = {'source_path': 'legacy-evidence.json',
                'source_digest': ra.file_digest(forged), 'complete': True,
                'authorizations': []}
    verdict = refusal(ra.adopt_history, root, 'run-1', evidence)
    assert verdict['untrusted'] == 'unverifiable_evidence'
    assert verdict['expected_source'] == WORKFLOW
    # The run this would have reset stays exactly as untrusted as it was.
    assert not (root / LEDGER).exists()
    assert refusal(ra.initialize, root, 'run-1')['untrusted'] == 'prior_execution'


def test_an_empty_legacy_ledger_reconstructs_nothing(root):
    """Zero adopted authorizations is a zero-spend origin dressed up as a recovery."""
    write_workflow(root, repair_routes=[],
                   transition_log=[{'node': 'build', 'status': 'completed',
                                    'at': '2026-09-01T00:00:00Z'}])
    evidence = {'source_path': WORKFLOW, 'source_digest': ra.file_digest(root / WORKFLOW),
                'complete': True, 'authorizations': []}
    verdict = refusal(ra.adopt_history, root, 'run-1', evidence)
    assert verdict['untrusted'] == 'incomplete_history'
    assert 'initialize' in verdict['reason']
    assert not (root / LEDGER).exists()


def test_adoption_records_the_execution_it_accounts_for(root):
    proof = ra.adopt_history(root, 'run-1', history(root))
    recorded = json.loads((root / LEDGER).read_text())['origin']['proof']
    assert recorded['observed'] == {'transition_log': 2, 'repair_routes': 2, 'completed': 0}
    assert recorded['records'] == recorded['routes'] == 2
    assert proof['adopted'] == 2


def test_an_adopted_claim_is_dated_from_the_record_that_evidences_it(root):
    """The chronology a later reconciliation is checked against comes from the source."""
    evidence = history(root, [ROUTES[0]], state='started')
    evidence['authorizations'][0].pop('started_at', None)
    ra.adopt_history(root, 'run-1', evidence)
    entry = json.loads((root / LEDGER).read_text())['authorizations'][0]
    assert entry['started_at'] == TRANSITIONS[0]['at']          # from transition_log[0]
    assert entry['granted_at'] == ROUTES[0]['dispatched_at']     # from repair_routes[0]
    # And that derived claim is what a later reconciliation is measured against.
    write_workflow(root, repair_routes=[ROUTES[0]],
                   transition_log=[{'node': 'fix', 'status': 'completed',
                                    'at': '2019-01-01T00:00:00Z'}])
    stale = {'source_path': WORKFLOW, 'source_digest': ra.file_digest(root / WORKFLOW),
             'basis': 'the run log', 'observation_ref': 'transition_log[0]'}
    assert refusal(ra.reconcile, root, 'legacy-0', 'executed',
                   stale)['untrusted'] == 'unattributable_evidence'


def test_an_undated_legacy_execution_record_is_refused(root):
    evidence = history(root, [ROUTES[0]], state='started',
                       transitions=[{'node': 'fix', 'status': 'dispatched'}])
    verdict = refusal(ra.adopt_history, root, 'run-1', evidence)
    assert verdict['untrusted'] == 'unattributable_evidence'
    assert 'no time' in verdict['reason']


def test_one_node_only_record_cannot_evidence_two_legacy_attempts(root):
    routes = [dict(ROUTES[0]), dict(ROUTES[0], attempt=2,
                                    dispatched_at='2026-09-01T00:01:00Z')]
    evidence = history(root, routes, transitions=[
        {'node': 'fix', 'status': 'completed', 'at': '2026-09-01T00:01:30Z'}])
    for record in evidence['authorizations']:
        record['settlement_ref'] = 'transition_log[0]'
    verdict = refusal(ra.adopt_history, root, 'run-1', evidence)
    assert verdict['untrusted'] == 'unattributable_evidence'
    assert 'cited by both' in verdict['reason']


def test_legacy_execution_evidence_predating_its_own_charge_is_refused(root):
    evidence = history(root, [ROUTES[0]], transitions=[
        {'node': 'fix', 'status': 'completed', 'at': '2025-01-01T00:00:00Z'}])
    verdict = refusal(ra.adopt_history, root, 'run-1', evidence)
    assert verdict['untrusted'] == 'unattributable_evidence'
    assert ROUTES[0]['dispatched_at'] in verdict['reason']


# --- a spend with no bound is a spend nothing can exhaust -----------------------------

def test_an_adopted_bound_comes_from_the_plan_not_from_the_record(root):
    """A stated bound may not overrule the plan; an absent one is taken from it."""
    evidence = history(root, [ROUTES[0]], loops=(('fix', ['qa-a'], 2),))
    evidence['authorizations'][0]['budgets'] = {'qa-a': 9}
    verdict = refusal(ra.adopt_history, root, 'run-1', evidence)
    assert verdict['untrusted'] == 'budget_not_declared'
    assert verdict['budgets'] == {'qa-a': {'declared': 2, 'stated': 9}}
    assert not (root / LEDGER).exists()

    evidence['authorizations'][0].pop('budgets')
    assert ra.adopt_history(root, 'run-1', evidence)['adopted'] == 1
    assert ra.consumption(root)['obligations'][0]['budget'] == 2


def test_a_ledger_entry_with_no_bound_cannot_be_read(root):
    started(root)
    grant(root, 'a1', ['qa-a'], {'qa-a': 3})
    ledger = json.loads((root / LEDGER).read_text())
    ledger['authorizations'][0].pop('budgets')
    (root / LEDGER).write_text(json.dumps(ledger))
    assert refusal(ra.consumption, root)['untrusted'] == 'unreadable_ledger'


def test_a_held_lock_is_classified_as_untrusted_state(root):
    """Every other refusal names the state it distrusts; a fenced ledger is one too."""
    started(root)
    (root / '.allforai/bootstrap/repair-authorizations.lock').mkdir()
    with pytest.raises(ra.Refusal) as caught:
        with ra.ledger_lock(root, attempts=2, interval=0.001):
            pass
    assert caught.value.verdict['untrusted'] == 'ledger_locked'


# --- the plan sets the bound, not the request ----------------------------------------
# Regressions for residual R1 of systematic-ledger-recovery-corrections.md: the bound was
# whatever the first grant for a pair happened to name, so a caller could charge 99
# attempts against a loop the plan bounded at 3, or charge a pair the plan never declared
# at all. The authority is `required_repair_loops` in the readiness spec.

def test_a_request_may_not_inflate_the_declared_budget(root):
    started(root, loops=(('fix', ['qa-a'], 3),))
    verdict = refusal(grant, root, 'a1', ['qa-a'], {'qa-a': 99})
    assert verdict['untrusted'] == 'budget_not_declared'
    assert verdict['budgets'] == {'qa-a': {'declared': 3, 'stated': 99}}
    # Nothing was charged, and the declared bound still governs.
    assert ra.consumption(root)['obligations'] == []
    assert grant(root, 'a1', ['qa-a'], {'qa-a': 3})['remaining'] == {'qa-a': 2}


def test_an_undeclared_pair_has_no_budget_to_be_within(root):
    started(root, loops=(('fix', ['qa-a'], 3),))
    verdict = refusal(grant, root, 'a1', ['qa-b'], {'qa-b': 3})
    assert verdict['untrusted'] == 'undeclared_repair_pair'
    assert verdict['undeclared'] == ['qa-b']
    # Declared through a different repair node is still not declared through this one.
    plan(root, ('fix', ['qa-a'], 3), ('fix-b', ['qa-b'], 3))
    assert refusal(grant, root, 'a1', ['qa-b'],
                   {'qa-b': 3})['untrusted'] == 'undeclared_repair_pair'
    assert grant(root, 'a1', ['qa-b'], {'qa-b': 3},
                 repair_node_id='fix-b')['charged'] == {'qa-b': 1}


def test_a_valid_expansion_is_grantable_and_keeps_what_was_spent(root):
    """A loop declared later is charged normally; the run is not reset to do it."""
    started(root, loops=(('fix', ['qa-a'], 2),))
    attempt(root, 'a1', ['qa-a'], {'qa-a': 2})
    plan(root, ('fix', ['qa-a'], 2), ('fix2', ['qa-new'], 4))
    assert grant(root, 'b1', ['qa-new'], {'qa-new': 4},
                 repair_node_id='fix2')['remaining'] == {'qa-new': 3}
    spent = spend_by_obligation(root)
    assert spent == {'qa-a': 1, 'qa-new': 1}          # the earlier attempt still counts
    assert ra.consumption(root)['origin'] == 'new_run'
    # And the expansion does not refill the loop that was already charged.
    assert attempt(root, 'a2', ['qa-a'], {'qa-a': 2})['remaining'] == {'qa-a': 0}
    assert refusal(grant, root, 'a3', ['qa-a'], {'qa-a': 2})['status'] == 'budget_exhausted'


def test_a_redeclared_bound_for_a_charged_pair_stops_rather_than_repricing(root):
    started(root, loops=(('fix', ['qa-a'], 2),))
    attempt(root, 'a1', ['qa-a'], {'qa-a': 2})
    plan(root, ('fix', ['qa-a'], 5))                  # the plan changed under the spend
    verdict = refusal(grant, root, 'a2', ['qa-a'], {'qa-a': 5})
    assert verdict['status'] == 'blocked' and verdict['untrusted'] == 'budget_conflict'
    # No reset and no re-pricing: the charge stands and the ledger keeps its origin.
    assert spend_by_obligation(root) == {'qa-a': 1}
    assert ra.consumption(root)['obligations'][0]['budget'] == 2
    # Restoring the declared bound lets the run continue on its real remaining budget.
    plan(root, ('fix', ['qa-a'], 2))
    assert grant(root, 'a2', ['qa-a'], {'qa-a': 2})['remaining'] == {'qa-a': 0}


@pytest.mark.parametrize('spec,untrusted', [
    (None, 'undeclared_repair_plan'),
    ('{broken', 'undeclared_repair_plan'),
    ({'version': 1}, 'undeclared_repair_plan'),
    ({'version': 1, 'required_repair_loops': {}}, 'undeclared_repair_plan'),
    ({'version': 1, 'required_repair_loops': ['not a loop']}, 'invalid_repair_declaration'),
    ({'version': 1, 'required_repair_loops': [{'qa_node_ids': ['qa-a']}]},
     'invalid_repair_declaration'),
    ({'version': 1, 'required_repair_loops': [{'repair_node_id': 'fix'}]},
     'invalid_repair_declaration'),
    ({'version': 1, 'required_repair_loops': [
        {'repair_node_id': 'fix', 'qa_node_ids': ['qa-a'], 'max_attempts': 0}]},
     'invalid_repair_declaration'),
    ({'version': 1, 'required_repair_loops': [
        {'repair_node_id': 'fix', 'qa_node_ids': ['qa-a'], 'max_attempts': '3'}]},
     'invalid_repair_declaration'),
    ({'version': 1, 'required_repair_loops': [
        {'repair_node_id': 'fix', 'qa_node_ids': ['qa-a'], 'max_attempts': 3},
        {'repair_node_id': 'fix', 'qa_node_ids': ['qa-a'], 'max_attempts': 4}]},
     'ambiguous_repair_declaration'),
])
def test_an_unusable_declaration_blocks_with_something_to_fix(root, spec, untrusted):
    """No bound is invented: not from a default, not from the request."""
    started(root)
    if spec is None:
        (root / SPEC).unlink()
    else:
        (root / SPEC).write_text(spec if isinstance(spec, str) else json.dumps(spec))
    assert refusal(grant, root, 'a1', ['qa-a'], {'qa-a': 3})['untrusted'] == untrusted
    assert ra.consumption(root)['obligations'] == []


def test_an_omitted_max_attempts_takes_the_documented_default(root):
    """The one legitimate fallback, read the same way by both hosts and the validator."""
    started(root, loops=(('fix', ['qa-a'], None),))
    assert grant(root, 'a1', ['qa-a'],
                 {'qa-a': ra.DEFAULT_REPAIR_ATTEMPTS})['remaining'] == {'qa-a': 2}
    assert refusal(grant, root, 'a2', ['qa-a'],
                   {'qa-a': 4})['untrusted'] == 'budget_not_declared'


def test_every_reported_obligation_has_a_known_bound(root):
    """`exhausted` can only be false-for-unknown if a bound can be unknown; none can."""
    started(root, loops=(('fix', ['qa-a', 'qa-b'], 2),))
    attempt(root, 'a1', ['qa-a', 'qa-b'], {'qa-a': 2, 'qa-b': 2})
    for record in ra.consumption(root)['obligations']:
        assert isinstance(record['budget'], int) and record['budget'] > 0
        assert record['remaining'] == record['budget'] - record['spent']
        assert record['exhausted'] is (record['remaining'] <= 0)
