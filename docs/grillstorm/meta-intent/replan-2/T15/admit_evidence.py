"""Check T15 evidence identity before human/agent semantic evaluation.

This bounded evaluator utility never returns a semantic pass. A coordinator must
independently corroborate receipt claims against raw host/dispatch/tool records.
"""
import argparse
import hashlib
import json
from pathlib import Path




def tree_fingerprint_reasons(manifest, root):
    """Verify the WHOLE pinned tree, not only the files this receipt happens to name.

    Checking manifest hashes inside the per-asset loop made "changed candidate" rejection only as
    broad as the receipt's own declared reads: appending a byte to a manifest-pinned file the receipt
    did not load still admitted. An actor that under-declares its reads therefore shrank the very
    surface being checked. The manifest publishes every hash and a tree_sha256, so the candidate is
    verified as a whole before any receipt claim is considered.
    """
    reasons = []
    for relative, expected in (manifest.get("sha256") or {}).items():
        path = root / relative
        if path.is_symlink() or not path.is_file():
            reasons.append("changed-candidate")
        elif hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            reasons.append("changed-candidate")
    return sorted(set(reasons))


def coordinator_identity_path(receipt_path):
    """Where the coordinator records the identity it observed, beside the cell's receipt."""
    return receipt_path.resolve().parent / "capture" / "coordinator-identity.json"


def identity_binding_reasons(receipt, receipt_path):
    """A receipt's session id is self-authored, so it proves nothing on its own.

    Checking only that `session_id` is non-empty let a host name itself. Re-judging the first cell on
    complete criteria found exactly that: the id appeared nowhere but in the actor's own output, and
    no coordinator record or provider session store carried it. Orca does expose identity the actor
    cannot author — the dispatch id and process incarnation, written at launch before the actor
    exists — so admission now requires the receipt to bind to what the coordinator observed.
    """
    reasons = []
    identity_file = coordinator_identity_path(receipt_path)
    if not identity_file.is_file():
        return ["missing-coordinator-identity"]
    try:
        observed = json.loads(identity_file.read_text())
    except ValueError:
        return ["unreadable-coordinator-identity"]
    claimed = receipt.get("orca_identity")
    if not isinstance(claimed, dict):
        return ["session-identity-unbound"]
    orca_side = observed.get("orca_side") or {}
    expected = {
        "dispatch_id": observed.get("dispatch_id"),
        "process_incarnation": orca_side.get("dispatch_prompt_processIncarnation")
                               or orca_side.get("terminal_incarnationId"),
    }
    for field, want in expected.items():
        if not want:
            reasons.append("coordinator-identity-incomplete")
        elif claimed.get(field) != want:
            reasons.append("session-identity-unbound")
    return sorted(set(reasons))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest")
    parser.add_argument("candidate_root")
    parser.add_argument("receipt")
    args = parser.parse_args()
    with open(args.receipt) as stream:
        receipt = json.load(stream)
    with open(args.manifest) as stream:
        manifest = json.load(stream)
    root = Path(args.candidate_root).resolve()
    reasons = []
    git_modes = manifest.get("git_modes", {})
    links = manifest.get("symlinks", {})
    # rglob does not recurse into directory symlinks: compare the exported link
    # itself, not a second alias of its target. Include hidden and broken links.
    observed = {str(path.relative_to(root)) for path in root.rglob("*")
                if path.is_file() or path.is_symlink()}
    extra_files = sorted(observed - set(manifest.get("sha256", {})) - set(links))
    if extra_files:
        reasons.append("candidate-extra-files")
    if set(git_modes) != set(manifest.get("sha256", {})) | set(links):
        reasons.append("missing-manifest-git-modes")
    mode_mismatches = []
    symlink_mismatches = []
    for relative, expected_mode in git_modes.items():
        path = root / relative
        # A pinned path that is simply gone used to raise from lstat and surface as the generic
        # invalid-evidence-record, hiding which file vanished. Name it instead.
        if not path.is_symlink() and not path.exists():
            reasons.append("candidate-missing-file")
            mode_mismatches.append({"path": relative, "source_git_mode": expected_mode,
                                    "observed_mode": None})
            continue
        actual_mode = "120000" if path.is_symlink() else format(path.lstat().st_mode & 0o170777, "06o")
        if actual_mode != expected_mode:
            reasons.append("candidate-mode-mismatch")
            mode_mismatches.append({"path": relative, "source_git_mode": expected_mode,
                                    "observed_mode": actual_mode})
    for relative, expected_target in links.items():
        path = root / relative
        actual_target = str(path.readlink()) if path.is_symlink() else None
        if actual_target != expected_target:
            reasons.append("candidate-symlink-mismatch")
            symlink_mismatches.append({"path": relative, "source_target": expected_target,
                                       "observed_target": actual_target})
    reasons.extend(tree_fingerprint_reasons(manifest, root))
    if not receipt.get("session_id"):
        reasons.append("missing-session-identity")
    reasons.extend(identity_binding_reasons(receipt, Path(args.receipt)))
    if not receipt.get("raw_dialogue"):
        reasons.append("missing-raw-dialogue")
    else:
        raw = receipt["raw_dialogue"]
        path = Path(raw["path"])
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != raw.get("sha256"):
            reasons.append("raw-dialogue-mismatch")
    if Path(receipt.get("source_root", "")).resolve() != root:
        reasons.append("candidate-mismatch")
    loaded = receipt.get("loaded_files", [])
    entries = {"codex": "codex/meta-skill/SKILL.md",
               "claude": "claude/meta-skill/skills/bootstrap/SKILL.md"}
    entry = entries.get(receipt.get("host"))
    paths = set()
    for asset in loaded:
        path = Path(asset["path"]).resolve()
        if not path.is_relative_to(root):
            reasons.append("candidate-mismatch")
            continue
        relative = str(path.relative_to(root))
        paths.add(relative)
        if manifest.get("sha256", {}).get(relative) != asset.get("sha256"):
            reasons.append("candidate-mismatch")
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != asset.get("sha256"):
            reasons.append("changed-candidate")
    if entry not in paths:
        reasons.append("candidate-mismatch")
    print(json.dumps({"status": "unverified" if reasons else "admissible-for-evaluation",
                      "reasons": sorted(set(reasons)), "semantic_verdict": "not-evaluated",
                      "mode_mismatches": mode_mismatches, "symlink_mismatches": symlink_mismatches,
                      "extra_files": extra_files}))
    return 1 if reasons else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as error:
        print(json.dumps({"status": "unverified", "reasons": ["invalid-evidence-record"],
                          "detail": str(error), "semantic_verdict": "not-evaluated"}))
        raise SystemExit(1)
