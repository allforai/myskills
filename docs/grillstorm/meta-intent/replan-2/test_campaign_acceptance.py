"""Campaign ledger consistency only; these tests do not prove host behavior."""
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent


@pytest.mark.parametrize("task", ["T15", "T16", "T17", "T18"])
def test_open_candidate_repairs_withdraw_launch_acceptance(task):
    checkpoint = json.loads((ROOT / "execution.json").read_text())["correction_verification_checkpoint"]
    recorded = json.loads((ROOT / task / "results.json").read_text())
    if not checkpoint["fresh_candidate_required"]:
        return
    assert recorded["candidate_accepted"] is False
    assert recorded["candidate_refresh_required"] is True
    withdrawal = recorded["candidate_acceptance_withdrawal"]
    assert withdrawal["previously_accepted_for_launch"] is True
    assert withdrawal["reason"]
    assert (ROOT / withdrawal["evidence"]).is_file()
    # Withdrawal preserves the old run identity; it must not erase inconvenient
    # attempts or relabel their candidate as the future repaired tree.
    assert recorded["launch_candidate"] == withdrawal["candidate"]
    assert recorded["launch_candidate_tree_sha256"] == withdrawal["tree_sha256"]
    assert recorded["launch_packet_root"]
    launch = (ROOT / task / "launch-request.md").read_text()
    assert "Launch suspended — candidate acceptance withdrawn" in launch
    assert "Do not launch the packets listed below" in launch
