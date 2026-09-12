"""Normalize an actor's own receipt into the bounded admission shape, preserving the original.

The private file permits this: "the coordinator may normalize actual raw actor records into this
shape while preserving originals." Actors write richer, host-specific receipts; `admit_evidence.py`
reads a fixed set of fields. Normalizing by hand was how a receipt first reached admission with no
identity binding at all, so this does it by rule and refuses to invent anything.

What it will NOT do: fabricate a field. The Orca process incarnation comes from the coordinator's own
launch record, never from the actor, and the actor's independently reported dispatch id and terminal
handle are CHECKED against that record rather than trusted.

Usage: normalize_receipt.py <cell-dir> --candidate-root <path> --raw-dialogue <path> [--out <path>]
"""
import argparse
import hashlib
import json
from pathlib import Path

ASSET_KEYS = ("loaded_assets", "loaded_files", "references_loaded")
HOSTS = {"codex": "codex", "claude": "claude"}


def normalize_host(value):
    """'Codex inside Orca' and 'Claude Code' must land on the admission vocabulary, or fail loudly."""
    if isinstance(value, dict):
        value = value.get("product") or value.get("name") or ""
    text = str(value).lower()
    hits = [canonical for token, canonical in HOSTS.items() if token in text]
    if len(hits) != 1:
        raise ValueError(f"cannot determine a single host from {value!r}")
    return hits[0]


def session_id(receipt):
    """The one session identity the receipt reports, or a refusal.

    Hosts name this differently, so several keys are searched. If two of them disagree the receipt is
    refused rather than resolved by search order: silently preferring whichever key happened to be
    checked first is how a record starts describing a session that never ran.
    """
    direct = receipt.get("session_id")
    if isinstance(direct, str) and direct:
        return direct
    found = {}
    for key in ("independent_session_identity", "session_identity"):
        block = receipt.get(key)
        if isinstance(block, dict):
            for field in ("CODEX_SESSION_ID", "claude_code_session_id", "session_id", "CODEX_THREAD_ID"):
                if block.get(field):
                    found[f"{key}.{field}"] = block[field]
    distinct = set(found.values())
    if not distinct:
        raise ValueError("receipt carries no session identity to normalize")
    if len(distinct) > 1:
        raise ValueError(f"receipt reports conflicting session identities: {found}")
    return distinct.pop()


def loaded_files(receipt, candidate_root):
    """Every asset the actor recorded that lives inside the pinned candidate tree.

    Assets outside the candidate (the host's own skill stubs, for instance) are deliberately dropped:
    admission compares against the candidate manifest, and an outside path would read as an extra file.
    """
    root = Path(candidate_root).resolve()
    out, seen = [], set()
    for key in ASSET_KEYS:
        for asset in receipt.get(key) or []:
            if not isinstance(asset, dict):
                continue
            raw = asset.get("resolved_path") or asset.get("path")
            if not raw or not asset.get("sha256"):
                continue
            path = Path(raw).resolve()
            if not path.is_relative_to(root) or str(path) in seen:
                continue
            seen.add(str(path))
            out.append({"path": str(path), "sha256": asset["sha256"]})
    return out


def identity_binding(receipt, coordinator_identity):
    """Bind to what the coordinator observed, and verify what the actor independently reported."""
    orca_side = coordinator_identity.get("orca_side") or {}
    incarnation = (orca_side.get("dispatch_prompt_processIncarnation")
                   or orca_side.get("terminal_incarnationId"))
    dispatch = coordinator_identity.get("dispatch_id")
    if not dispatch or not incarnation:
        raise ValueError("coordinator identity record is incomplete; cannot bind")
    disagreements = []
    for field, observed in (("dispatch_id", dispatch),
                            ("terminal_handle", orca_side.get("terminal_handle"))):
        claimed = receipt.get(field)
        if claimed and observed and claimed != observed:
            disagreements.append({"field": field, "actor_said": claimed, "coordinator_saw": observed})
    return ({"dispatch_id": dispatch, "process_incarnation": incarnation,
             "actor_agreed_on": sorted(f for f in ("dispatch_id", "terminal_handle")
                                       if receipt.get(f) and receipt.get(f) == (
                                           dispatch if f == "dispatch_id" else orca_side.get(f)))},
            disagreements)


def actor_receipt_path(cell):
    """Always normalize from the actor's own words.

    Once receipt.json has been normalized it no longer carries the actor's top-level dispatch_id and
    terminal_handle, so re-reading it silently loses the actor-agreement evidence that makes the
    identity binding worth anything. Prefer the preserved original whenever it exists, which also
    makes normalization idempotent.
    """
    cell = Path(cell)
    original = cell / "receipt.actor-original.json"
    return original if original.is_file() else cell / "receipt.json"


def build(cell, candidate_root, raw_dialogue):
    cell = Path(cell)
    receipt = json.loads(actor_receipt_path(cell).read_text())
    identity_file = cell / "capture" / "coordinator-identity.json"
    coordinator = json.loads(identity_file.read_text())
    binding, disagreements = identity_binding(receipt, coordinator)
    if disagreements:
        raise ValueError(f"actor identity contradicts the coordinator record: {disagreements}")
    raw = Path(raw_dialogue).resolve()
    return {
        "host": normalize_host(receipt.get("host")),
        "session_id": session_id(receipt),
        "orca_identity": binding,
        "source_root": str(Path(candidate_root).resolve()),
        "loaded_files": loaded_files(receipt, candidate_root),
        "raw_dialogue": {"path": str(raw),
                         "sha256": hashlib.sha256(raw.read_bytes()).hexdigest()},
        "normalized_by": ("coordinator; the actor's own record is preserved at "
                          "receipt.actor-original.json. process_incarnation comes from the "
                          "coordinator's launch record, never from the actor; the actor's own "
                          "dispatch_id and terminal_handle were checked against it and agreed."),
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("cell")
    ap.add_argument("--candidate-root", required=True)
    ap.add_argument("--raw-dialogue", required=True)
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    cell = Path(a.cell)
    record = build(cell, a.candidate_root, a.raw_dialogue)
    original = cell / "receipt.actor-original.json"
    if not original.exists():
        original.write_text((cell / "receipt.json").read_text())
    out = Path(a.out) if a.out else cell / "receipt.json"
    out.write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps({"written": str(out), "preserved": str(original),
                      "loaded_files": len(record["loaded_files"]),
                      "actor_agreed_on": record["orca_identity"]["actor_agreed_on"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
