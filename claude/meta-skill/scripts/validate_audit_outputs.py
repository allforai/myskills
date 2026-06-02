"""Shape validators for the three /bootstrap planning-audit artifacts.
These guard the machine-readable contracts; the audits themselves are LLM judgment."""


def _require_keys(obj, keys):
    return [f"missing top-level key: {k}" for k in keys if k not in obj]


def validate_granularity_audit(obj):
    errs = _require_keys(obj, ["split", "merged", "kept"])
    for s in obj.get("split", []):
        if "from" not in s or "into" not in s:
            errs.append("split entry needs 'from' and 'into'")
        if "rationale" not in s:
            errs.append("split entry needs 'rationale'")
    for m in obj.get("merged", []):
        if "from" not in m or "into" not in m:
            errs.append("merged entry needs 'from' and 'into'")
        if "rationale" not in m:
            errs.append("merged entry needs 'rationale'")
    return (len(errs) == 0, errs)


def validate_decision_coverage(obj):
    errs = _require_keys(obj, ["captured", "missing"])
    for m in obj.get("missing", []):
        if "id" not in m:
            errs.append("missing-entry needs 'id'")
        if "rationale" not in m:
            errs.append("missing-entry needs 'rationale'")
        if "consumer_node" not in m:  # fix C4: wire decision to its consumer
            errs.append("missing-entry needs 'consumer_node'")
    return (len(errs) == 0, errs)


def validate_decision_artifact(obj):
    errs = _require_keys(obj, ["id", "decision", "rationale"])
    return (len(errs) == 0, errs)


if __name__ == "__main__":
    import json, sys
    kind, path = sys.argv[1], sys.argv[2]
    obj = json.load(open(path))
    fn = {
        "granularity": validate_granularity_audit,
        "decision-coverage": validate_decision_coverage,
        "decision": validate_decision_artifact,
    }[kind]
    ok, errs = fn(obj)
    print("OK" if ok else "INVALID: " + "; ".join(errs))
    sys.exit(0 if ok else 1)
