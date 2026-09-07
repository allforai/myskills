"""Check T15 evidence identity before human/agent semantic evaluation.

This bounded evaluator utility never returns a semantic pass. A coordinator must
independently corroborate receipt claims against raw host/dispatch/tool records.
"""
import argparse
import hashlib
import json
from pathlib import Path


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
    if not receipt.get("session_id"):
        reasons.append("missing-session-identity")
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
                      "reasons": sorted(set(reasons)), "semantic_verdict": "not-evaluated"}))
    return 1 if reasons else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as error:
        print(json.dumps({"status": "unverified", "reasons": ["invalid-evidence-record"],
                          "detail": str(error), "semantic_verdict": "not-evaluated"}))
        raise SystemExit(1)
