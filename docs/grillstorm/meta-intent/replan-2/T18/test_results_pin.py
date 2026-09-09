"""Guard the recorded T18 result ledger; no actor behavior is judged here."""
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
LEDGER = HERE / "results.json"
MATRIX = json.loads((HERE.parents[1] / "tasks" / "scenario-matrix.json").read_text())


def load_exporter():
    spec = importlib.util.spec_from_file_location("t18_prepare_packets", HERE / "prepare_packets.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def ledger():
    return json.loads(LEDGER.read_text())


def test_ledger_pins_the_tree_it_claims_to_have_exported(tmp_path):
    recorded = ledger()
    exported = load_exporter().candidate(tmp_path / "candidate", recorded["reference_commit"])
    assert exported["tree_sha256"] == recorded["reference_tree_sha256"], (
        "the ledger hash must be recomputable from its own pinned commit")


def test_the_reference_candidate_is_never_recorded_as_accepted(tmp_path):
    recorded = ledger()
    if recorded["launch_candidate"] is not None:
        assert recorded["launch_candidate"] != recorded["reference_commit"]
        assert recorded["launch_packet_root"] != recorded["reference_packet_root"]
        exported = load_exporter().candidate(tmp_path / "candidate", recorded["launch_candidate"])
        assert exported["tree_sha256"] == recorded["launch_candidate_tree_sha256"]
        manifest = json.loads((Path(recorded["launch_packet_root"]) / "candidate-manifest.json").read_text())
        assert manifest["source_commit"] == recorded["launch_candidate"]
        assert manifest["tree_sha256"] == exported["tree_sha256"]
        if not recorded["candidate_accepted"]:
            assert recorded["candidate_refresh_required"] is True
            withdrawal = recorded["candidate_acceptance_withdrawal"]
            assert withdrawal["previously_accepted_for_launch"] is True
            assert withdrawal["candidate"] == recorded["launch_candidate"]
            assert withdrawal["tree_sha256"] == exported["tree_sha256"]
            assert withdrawal["reason"]
            assert (HERE.parent / withdrawal["evidence"]).is_file()
    else:
        assert recorded["candidate_accepted"] is False
        assert recorded["launch_packet_root"] is None, (
            "the reference export is preparation output, never a launch root")
    assert recorded["launch_precondition"], "the ledger must say what must happen before a launch"
    for word in ("regenerat", "fingerprint"):
        assert word in recorded["launch_precondition"].lower(), (
            "the launch precondition must require a regenerated, re-fingerprinted candidate")
    assert "accepted" not in recorded["reference_status"].split("not accepted")[0], (
        "the reference commit must not be described as accepted")


def test_ledger_covers_exactly_the_matrix_cells():
    recorded = ledger()
    expected = {(s["id"], host) for s in MATRIX["scenarios"] if s["task"] == "T18" for host in s["hosts"]}
    assert {(c["scenario"], c["host"]) for c in recorded["cells"]} == expected
    assert len(recorded["cells"]) == recorded["required_cells"] == 16


def test_each_cell_declares_the_requirements_the_matrix_binds_to_it():
    bound = {s["id"]: s["requirements"] for s in MATRIX["scenarios"] if s["task"] == "T18"}
    for cell in ledger()["cells"]:
        assert cell["requirements"] == bound[cell["scenario"]]


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
        assert last["candidate_tree_sha256"] == recorded["launch_candidate_tree_sha256"]
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


def test_preparation_is_never_reported_as_host_proof():
    recorded = ledger()
    assert recorded["host_evidence"] == f"{recorded['passed_cells']}/{recorded['required_cells']}"
    assert recorded["preparation_status"] != recorded.get("proof_status")
    assert recorded["issue_accepted_complete"] is False


def test_historic_host_blockers_are_not_reported_as_current_fact():
    recorded = ledger()
    assert recorded["blockers"], "the blockers that stopped earlier launches must be named"
    for blocker in recorded["blockers"]:
        assert blocker["status"] == "historic-unrevalidated", (
            "a blocker carried over from an earlier task is not current evidence")
        assert blocker["revalidation"], "each blocker must say how it is rechecked before launch"


def test_launch_request_carries_no_oracle_content():
    launch = (HERE / "launch-request.md").read_text()
    private = (HERE / "evaluator-private.md").read_text()
    for marker in ("**Pass:**", "**Fail:**", "Scripted user answers"):
        assert marker in private, "the oracle must state its criteria"
        assert marker not in launch, f"the launch request leaks '{marker}'"
    for scripted in load_exporter().SCRIPTED_REPLY_MARKERS:
        assert scripted in private, "the reply script must live in the private oracle"
        assert scripted not in launch, "the launch request leaks a scripted user reply"


def test_launch_request_pins_the_same_reference_and_refuses_to_launch_it():
    launch = (HERE / "launch-request.md").read_text()
    recorded = ledger()
    assert recorded["reference_commit"] in launch
    assert recorded["reference_tree_sha256"] in launch
    assert "Do not launch" in launch, "the reference export must be marked unlaunchable"
    for cell in recorded["cells"]:
        assert cell["reference_packet"] in launch, f"{cell['scenario']}/{cell['host']} is missing a prompt path"


def test_ledger_cannot_call_the_issue_complete_without_full_host_evidence():
    recorded = ledger()
    complete = recorded["passed_cells"] == recorded["required_cells"]
    assert recorded["issue_accepted_complete"] is complete
    if not complete:
        assert recorded["launch_decision"], "a cell left unlaunched must record who decided and why"


def test_no_fixture_patch_stands_in_for_a_candidate_bug():
    recorded = ledger()
    assert recorded["preparation_blocked_steps"] == [], (
        "a preparation step blocked by a known bug must be listed, not worked around")
    assert "no fixture was patched" in recorded["preparation_blocked_note"].lower()
