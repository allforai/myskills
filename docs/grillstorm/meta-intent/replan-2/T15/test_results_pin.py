"""Guard the recorded T15 result ledger; no actor behavior is judged here."""
import importlib.util
import json
from pathlib import Path

LEDGER = Path(__file__).with_name("results.json")


def load_exporter():
    path = Path(__file__).with_name("prepare_packets.py")
    spec = importlib.util.spec_from_file_location("t15_prepare_packets", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_ledger_pins_the_tree_it_claims_to_have_exported(tmp_path):
    ledger = json.loads(LEDGER.read_text())
    exported = load_exporter().candidate(tmp_path / "candidate", ledger["source_commit"])
    assert exported["tree_sha256"] == ledger["candidate_tree_sha256"], (
        "ledger hash must be recomputable from its own pinned commit")
    assert ledger["production_commit"] == ledger["source_commit"], (
        "a separate producer commit means the exported tree is not the accepted candidate")


def test_no_cell_claims_a_pass_without_admitted_receipt_evidence():
    ledger = json.loads(LEDGER.read_text())
    assert len(ledger["cells"]) == ledger["required_cells"]
    proven = 0
    for cell in ledger["cells"]:
        if cell["status"] == "unverified":
            assert cell["reason"], "an unverified cell must say why"
            continue
        assert cell["status"] == "passed"
        attempts = cell["attempts"]
        assert attempts, "a pass needs at least one recorded attempt"
        last = attempts[-1]
        assert last["candidate_tree_sha256"] == ledger["candidate_tree_sha256"]
        assert last["session_id"] and last["raw_dialogue"]
        assert last["admission"] == "admissible-for-evaluation"
        proven += 1
    assert ledger["passed_cells"] == proven
    assert ledger["executed_cells"] == sum(1 for c in ledger["cells"] if c["attempts"])


def test_claude_evidence_is_never_counted_as_codex_host_coverage():
    ledger = json.loads(LEDGER.read_text())
    for cell in ledger["cells"]:
        for attempt in cell["attempts"]:
            assert attempt["host"] == cell["host"], "each attempt must come from its own host"
