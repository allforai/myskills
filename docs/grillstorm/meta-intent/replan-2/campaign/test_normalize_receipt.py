"""Normalization must never invent a field, and must never accept a contradiction."""
import importlib.util
import hashlib
import json
from pathlib import Path

import pytest

HERE = Path(__file__).parent


def load():
    spec = importlib.util.spec_from_file_location("nr", HERE / "normalize_receipt.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def cell_with(tmp_path, receipt_extra=None, identity_extra=None):
    candidate = tmp_path / "candidate"
    asset = candidate / "codex" / "meta-skill" / "SKILL.md"
    asset.parent.mkdir(parents=True)
    asset.write_text("candidate entry\n")
    digest = hashlib.sha256(asset.read_bytes()).hexdigest()
    cell = tmp_path / "cell"
    (cell / "capture").mkdir(parents=True)
    raw = cell / "capture" / "raw-dialogue.json"
    raw.write_text(json.dumps({"dialogue": []}))
    receipt = {"host": "Codex inside Orca",
               "independent_session_identity": {"CODEX_SESSION_ID": "sess-1"},
               "dispatch_id": "ctx_a", "terminal_handle": "term_a",
               "loaded_assets": [{"path": str(asset), "sha256": digest}]}
    receipt.update(receipt_extra or {})
    (cell / "receipt.json").write_text(json.dumps(receipt))
    identity = {"dispatch_id": "ctx_a",
                "orca_side": {"dispatch_prompt_processIncarnation": "inc_a",
                              "terminal_incarnationId": "inc_a", "terminal_handle": "term_a"}}
    identity.update(identity_extra or {})
    (cell / "capture" / "coordinator-identity.json").write_text(json.dumps(identity))
    return cell, candidate, raw


def test_normalizes_host_session_and_binds_coordinator_identity(tmp_path):
    m = load()
    cell, candidate, raw = cell_with(tmp_path)
    record = m.build(cell, candidate, raw)
    assert record["host"] == "codex"
    assert record["session_id"] == "sess-1"
    assert record["orca_identity"]["process_incarnation"] == "inc_a", (
        "the incarnation must come from the coordinator, which the actor cannot author")
    assert record["orca_identity"]["actor_agreed_on"] == ["dispatch_id", "terminal_handle"]
    assert record["raw_dialogue"]["sha256"] == hashlib.sha256(raw.read_bytes()).hexdigest()


def test_a_claude_receipt_normalizes_to_the_claude_host(tmp_path):
    m = load()
    cell, candidate, raw = cell_with(tmp_path, receipt_extra={
        "host": {"product": "Claude Code"},
        "independent_session_identity": None,
        "session_identity": {"claude_code_session_id": "session_x"}})
    receipt = json.loads((cell / "receipt.json").read_text())
    receipt.pop("independent_session_identity")
    (cell / "receipt.json").write_text(json.dumps(receipt))
    record = m.build(cell, candidate, raw)
    assert record["host"] == "claude"
    assert record["session_id"] == "session_x"


def test_an_actor_contradicting_the_coordinator_is_refused(tmp_path):
    """The whole point of the binding: a disagreement must stop normalization, not be smoothed over."""
    m = load()
    cell, candidate, raw = cell_with(tmp_path, receipt_extra={"dispatch_id": "ctx_somebody_else"})
    with pytest.raises(ValueError, match="contradicts the coordinator"):
        m.build(cell, candidate, raw)


def test_a_contradicting_terminal_handle_is_also_refused(tmp_path):
    m = load()
    cell, candidate, raw = cell_with(tmp_path, receipt_extra={"terminal_handle": "term_wrong"})
    with pytest.raises(ValueError, match="contradicts the coordinator"):
        m.build(cell, candidate, raw)


def test_an_incomplete_coordinator_record_refuses_to_bind(tmp_path):
    m = load()
    cell, candidate, raw = cell_with(tmp_path, identity_extra={"orca_side": {}})
    with pytest.raises(ValueError, match="incomplete"):
        m.build(cell, candidate, raw)


def test_a_receipt_with_no_session_identity_is_refused_not_defaulted(tmp_path):
    m = load()
    cell, candidate, raw = cell_with(tmp_path)
    receipt = json.loads((cell / "receipt.json").read_text())
    receipt.pop("independent_session_identity")
    (cell / "receipt.json").write_text(json.dumps(receipt))
    with pytest.raises(ValueError, match="no session identity"):
        m.build(cell, candidate, raw)


def test_an_ambiguous_host_string_is_refused(tmp_path):
    m = load()
    cell, candidate, raw = cell_with(tmp_path, receipt_extra={"host": "Claude and Codex together"})
    with pytest.raises(ValueError, match="single host"):
        m.build(cell, candidate, raw)


def test_assets_outside_the_candidate_are_dropped(tmp_path):
    """Host skill stubs live outside the pinned tree; keeping them would read as extra files."""
    m = load()
    outside = tmp_path / "elsewhere" / "SKILL.md"
    outside.parent.mkdir(parents=True)
    outside.write_text("host stub\n")
    cell, candidate, raw = cell_with(tmp_path, receipt_extra={"host_protocol_assets": [
        {"path": str(outside), "sha256": hashlib.sha256(outside.read_bytes()).hexdigest()}]})
    record = m.build(cell, candidate, raw)
    assert all(str(candidate) in f["path"] for f in record["loaded_files"])
    assert len(record["loaded_files"]) == 1


def test_the_original_receipt_is_preserved_before_overwriting(tmp_path):
    m = load()
    cell, candidate, raw = cell_with(tmp_path)
    before = (cell / "receipt.json").read_text()
    m.main([str(cell), "--candidate-root", str(candidate), "--raw-dialogue", str(raw)])
    assert (cell / "receipt.actor-original.json").read_text() == before
    assert json.loads((cell / "receipt.json").read_text())["host"] == "codex"


def test_rerunning_normalization_does_not_overwrite_the_preserved_original(tmp_path):
    m = load()
    cell, candidate, raw = cell_with(tmp_path)
    before = (cell / "receipt.json").read_text()
    m.main([str(cell), "--candidate-root", str(candidate), "--raw-dialogue", str(raw)])
    m.main([str(cell), "--candidate-root", str(candidate), "--raw-dialogue", str(raw)])
    assert (cell / "receipt.actor-original.json").read_text() == before, (
        "a second run must not archive the already-normalized receipt over the actor's own")


def test_conflicting_session_identities_are_refused_not_resolved_by_search_order(tmp_path):
    m = load()
    cell, candidate, raw = cell_with(tmp_path, receipt_extra={
        "session_identity": {"claude_code_session_id": "a-different-session"}})
    with pytest.raises(ValueError, match="conflicting session identities"):
        m.build(cell, candidate, raw)


def test_agreeing_duplicate_session_identities_are_accepted(tmp_path):
    m = load()
    cell, candidate, raw = cell_with(tmp_path, receipt_extra={
        "session_identity": {"session_id": "sess-1"}})
    assert m.build(cell, candidate, raw)["session_id"] == "sess-1"


def test_normalization_is_idempotent_and_keeps_the_actor_agreement_evidence(tmp_path):
    """Re-running once read its own output and silently lost actor_agreed_on."""
    m = load()
    cell, candidate, raw = cell_with(tmp_path)
    m.main([str(cell), "--candidate-root", str(candidate), "--raw-dialogue", str(raw)])
    first = json.loads((cell / "receipt.json").read_text())
    m.main([str(cell), "--candidate-root", str(candidate), "--raw-dialogue", str(raw)])
    second = json.loads((cell / "receipt.json").read_text())
    assert first == second, "normalization must be idempotent"
    assert second["orca_identity"]["actor_agreed_on"] == ["dispatch_id", "terminal_handle"], (
        "the actor's independent agreement is the evidence; it must survive a re-run")


def test_a_declared_non_read_is_never_harvested_as_a_read(tmp_path):
    """The one lie normalization must not introduce: claiming a read the actor said it skipped."""
    m = load()
    cell, candidate, raw = cell_with(tmp_path)
    skipped = candidate / "claude" / "meta-skill" / "knowledge" / "product-intent.md"
    skipped.parent.mkdir(parents=True, exist_ok=True)
    skipped.write_text("routed elsewhere; not read\n")
    digest = hashlib.sha256(skipped.read_bytes()).hexdigest()
    receipt = json.loads((cell / "receipt.json").read_text())
    receipt["references_deliberately_not_loaded"] = [{"path": str(skipped), "sha256": digest}]
    receipt["installed_plugin_not_used"] = {"path": str(skipped), "sha256": digest}
    (cell / "receipt.json").write_text(json.dumps(receipt))
    record = m.build(cell, candidate, raw)
    assert all("product-intent.md" not in f["path"] for f in record["loaded_files"]), (
        "a key naming a non-read must be refused even though it carries a path and a sha256")


def test_assets_are_discovered_whatever_the_host_named_the_key(tmp_path):
    m = load()
    cell, candidate, raw = cell_with(tmp_path)
    extra = candidate / "claude" / "meta-skill" / "knowledge" / "engine.md"
    extra.parent.mkdir(parents=True, exist_ok=True)
    extra.write_text("read in part\n")
    receipt = json.loads((cell / "receipt.json").read_text())
    receipt.pop("loaded_assets")
    receipt["references_loaded_in_full"] = [
        {"path": "codex/meta-skill/SKILL.md",
         "sha256": hashlib.sha256((candidate / "codex/meta-skill/SKILL.md").read_bytes()).hexdigest()}]
    receipt["references_loaded_in_part"] = [
        {"abs_path": str(extra), "sha256": hashlib.sha256(extra.read_bytes()).hexdigest()}]
    (cell / "receipt.json").write_text(json.dumps(receipt))
    record = m.build(cell, candidate, raw)
    names = [f["path"] for f in record["loaded_files"]]
    assert len(names) == 2, names
    assert any("SKILL.md" in n for n in names), "a relative path must resolve against the candidate"
    assert any("engine.md" in n for n in names), "abs_path must be honoured too"


def test_the_host_is_found_when_nested_under_session_identity(tmp_path):
    m = load()
    cell, candidate, raw = cell_with(tmp_path)
    receipt = json.loads((cell / "receipt.json").read_text())
    receipt.pop("host")
    receipt["session_identity"] = {"host": "Claude Code CLI", "claude_code_session_id": "session_y"}
    receipt.pop("independent_session_identity")
    (cell / "receipt.json").write_text(json.dumps(receipt))
    record = m.build(cell, candidate, raw)
    assert record["host"] == "claude"
    assert record["session_id"] == "session_y"


def test_a_recorded_path_that_does_not_exist_is_not_reported_as_loaded(tmp_path):
    m = load()
    cell, candidate, raw = cell_with(tmp_path)
    receipt = json.loads((cell / "receipt.json").read_text())
    receipt["loaded_assets"].append({"path": str(candidate / "ghost.md"), "sha256": "0" * 64})
    (cell / "receipt.json").write_text(json.dumps(receipt))
    record = m.build(cell, candidate, raw)
    assert all("ghost.md" not in f["path"] for f in record["loaded_files"])


def test_orca_ids_nested_under_session_identity_are_found_and_verified(tmp_path):
    """A shallow read dropped this host's agreement evidence entirely."""
    m = load()
    cell, candidate, raw = cell_with(tmp_path)
    receipt = json.loads((cell / "receipt.json").read_text())
    receipt.pop("dispatch_id"); receipt.pop("terminal_handle")
    receipt["session_identity"] = {"orca": {"dispatch_id": "ctx_a", "worker_terminal_handle": "term_a",
                                            "task_id": "task_a"}}
    (cell / "receipt.json").write_text(json.dumps(receipt))
    identity = json.loads((cell / "capture" / "coordinator-identity.json").read_text())
    identity["task_id"] = "task_a"
    (cell / "capture" / "coordinator-identity.json").write_text(json.dumps(identity))
    record = m.build(cell, candidate, raw)
    assert record["orca_identity"]["actor_agreed_on"] == ["dispatch_id", "task_id", "terminal_handle"]


def test_a_nested_id_that_disagrees_is_still_refused(tmp_path):
    m = load()
    cell, candidate, raw = cell_with(tmp_path)
    receipt = json.loads((cell / "receipt.json").read_text())
    receipt.pop("dispatch_id")
    receipt["session_identity"] = {"orca": {"dispatch_id": "ctx_not_mine"}}
    (cell / "receipt.json").write_text(json.dumps(receipt))
    with pytest.raises(ValueError, match="contradicts the coordinator"):
        m.build(cell, candidate, raw)


def test_refuses_to_rewrite_the_receipt_of_a_certified_cell(tmp_path):
    """I rewrote a certified receipt and could not restore the as-evaluated bytes."""
    m = load()
    cell, candidate, raw = cell_with(tmp_path)
    ledger = tmp_path / "results.json"
    ledger.write_text(json.dumps({"cells": [
        {"scenario": "T15/x", "host": "codex", "status": "passed",
         "attempts": [{"receipt": str(cell / "receipt.json")}]}]}))
    with pytest.raises(SystemExit, match="certified cell"):
        m.main([str(cell), "--candidate-root", str(candidate), "--raw-dialogue", str(raw),
                "--ledger", str(ledger)])
    m.main([str(cell), "--candidate-root", str(candidate), "--raw-dialogue", str(raw),
            "--ledger", str(ledger), "--allow-certified"])


def test_an_unverified_cell_is_not_blocked_by_the_guard(tmp_path):
    m = load()
    cell, candidate, raw = cell_with(tmp_path)
    ledger = tmp_path / "results.json"
    ledger.write_text(json.dumps({"cells": [
        {"scenario": "T15/x", "host": "codex", "status": "unverified",
         "attempts": [{"receipt": str(cell / "receipt.json")}]}]}))
    assert m.main([str(cell), "--candidate-root", str(candidate), "--raw-dialogue", str(raw),
                   "--ledger", str(ledger)]) == 0


def test_writing_to_an_explicit_out_path_never_touches_the_cell(tmp_path):
    m = load()
    cell, candidate, raw = cell_with(tmp_path)
    ledger = tmp_path / "results.json"
    ledger.write_text(json.dumps({"cells": [
        {"scenario": "T15/x", "host": "codex", "status": "passed",
         "attempts": [{"receipt": str(cell / "receipt.json")}]}]}))
    before = (cell / "receipt.json").read_text()
    assert m.main([str(cell), "--candidate-root", str(candidate), "--raw-dialogue", str(raw),
                   "--ledger", str(ledger), "--out", str(tmp_path / "elsewhere.json")]) == 0
    assert (cell / "receipt.json").read_text() == before
