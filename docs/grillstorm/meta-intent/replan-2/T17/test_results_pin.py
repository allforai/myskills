"""Guard the recorded T17 result ledger; no actor behavior is judged here."""
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
LEDGER = HERE / "results.json"
MATRIX = json.loads((HERE.parents[1] / "tasks" / "scenario-matrix.json").read_text())


def load_exporter():
    spec = importlib.util.spec_from_file_location("t17_prepare_packets", HERE / "prepare_packets.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def ledger():
    return json.loads(LEDGER.read_text())


def test_ledger_pins_the_tree_it_claims_to_have_exported(tmp_path):
    recorded = ledger()
    exported = load_exporter().candidate(tmp_path / "candidate", recorded["source_commit"])
    assert exported["tree_sha256"] == recorded["candidate_tree_sha256"], (
        "the ledger hash must be recomputable from its own pinned commit")
    assert recorded["production_commit"] == recorded["source_commit"], (
        "a separate producer commit means the exported tree is not the candidate")
    for host, entry in recorded["candidate_entries"].items():
        assert exported["sha256"][entry] == recorded["candidate_entry_sha256"][host]


def test_a_preliminary_candidate_is_declared_and_blocks_launch():
    recorded = ledger()
    if recorded["candidate_status"] != "final":
        assert recorded["candidate_refresh_required"] is True
        assert recorded["candidate_refresh_reason"]
        assert recorded["passed_cells"] == 0, (
            "no cell may be counted against a candidate that is not the accepted final one")
        assert any("re-exported" in blocker or "re-export" in blocker
                   for blocker in recorded["blockers"]), (
            "the uncleared candidate refresh must be named as a blocker")


def test_ledger_covers_exactly_the_matrix_cells():
    recorded = ledger()
    expected = {(s["id"], host) for s in MATRIX["scenarios"] if s["task"] == "T17"
                for host in s["hosts"]}
    assert {(c["scenario"], c["host"]) for c in recorded["cells"]} == expected
    assert len(recorded["cells"]) == recorded["required_cells"] == 16


def test_every_cell_carries_the_matrix_requirements_it_claims():
    declared = {s["id"]: s["requirements"] for s in MATRIX["scenarios"] if s["task"] == "T17"}
    for cell in ledger()["cells"]:
        assert cell["requirements"] == declared[cell["scenario"]]


def test_no_cell_claims_a_pass_without_admitted_receipt_evidence():
    recorded = ledger()
    proven = 0
    for cell in recorded["cells"]:
        if cell["status"] == "unverified":
            assert cell["reason"], "an unverified cell must say why"
            continue
        assert cell["status"] == "passed"
        attempts = cell["attempts"]
        assert attempts, "a pass needs at least one recorded attempt"
        last = attempts[-1]
        assert last["candidate_tree_sha256"] == recorded["candidate_tree_sha256"]
        assert last["session_id"] and last["raw_dialogue"]
        assert last["admission"] == "admissible-for-evaluation"
        proven += 1
    assert recorded["passed_cells"] == proven
    assert recorded["executed_cells"] == sum(1 for c in recorded["cells"] if c["attempts"])


def test_one_hosts_evidence_is_never_counted_as_the_others_coverage():
    for cell in ledger()["cells"]:
        for attempt in cell["attempts"]:
            assert attempt["host"] == cell["host"], "each attempt must come from its own host"


def test_two_phase_scenarios_declare_both_phases():
    module = load_exporter()
    for cell in ledger()["cells"]:
        scene = cell["scenario"].split("/", 1)[1]
        assert cell.get("phases") == (2 if scene in module.PHASE_TWO else 1), (
            f"{cell['scenario']} must declare its fresh-context phase count")
        assert (cell["phase2_packet"] is not None) == (scene in module.PHASE_TWO)


def test_preparation_is_never_reported_as_host_proof():
    recorded = ledger()
    assert recorded["host_evidence"] == f"{recorded['passed_cells']}/{recorded['required_cells']}"
    assert recorded["preparation_status"] != recorded.get("proof_status")


def test_launch_request_carries_no_oracle_content():
    launch = (HERE / "launch-request.md").read_text()
    private = (HERE / "evaluator-private.md").read_text()
    for marker in ("**Pass:**", "**Fail:**", "Scripted user answers", "Pass, phase 1"):
        assert marker in private, "the oracle must state its criteria"
        assert marker not in launch, f"the launch request leaks '{marker}'"
    for scripted in ("I widened the coordinator list", "Nothing in the code changed",
                     "It says passed and it is newer than the code",
                     "I genuinely do not know"):
        assert scripted in private
        assert scripted not in launch, "the launch request leaks a scripted user reply"


def test_launch_request_pins_the_same_candidate_as_the_ledger():
    launch = (HERE / "launch-request.md").read_text()
    recorded = ledger()
    assert recorded["source_commit"] in launch
    assert recorded["candidate_tree_sha256"] in launch
    for cell in recorded["cells"]:
        assert cell["packet"] in launch, f"{cell['scenario']}/{cell['host']} is missing a prompt path"


def test_ledger_cannot_call_the_issue_complete_without_full_host_evidence():
    recorded = ledger()
    complete = recorded["passed_cells"] == recorded["required_cells"]
    assert recorded["issue_accepted_complete"] is complete, (
        "issue acceptance must track actual host evidence, never preparation status")
    if not complete:
        assert recorded["launch_decision"], "a cell left unlaunched must record who decided and why"
        assert recorded["blockers"], "the uncleared blockers must be named"


def test_recorded_blockers_stay_observations_not_permanent_claims():
    for blocker in ledger()["blockers"]:
        assert "permanent" not in blocker.lower() or "not claimed to be permanent" in blocker, (
            "a host blocker is an observation to recheck, never a standing universal claim")
