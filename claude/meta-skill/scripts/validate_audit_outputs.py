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
    """A0 coverage, including the provenance that proves its passes ran (ADR-0011).

    The rule lives in the bootstrap gate, which also checks the recorded digests against
    the current plan; this CLI applies the project-free half of it, from that one place.
    """
    import os, sys
    orchestrator = os.path.join(os.path.dirname(os.path.abspath(__file__)), "orchestrator")
    if orchestrator not in sys.path:
        sys.path.insert(0, orchestrator)
    from validate_bootstrap import decision_coverage_shape_errors
    errs = decision_coverage_shape_errors(obj)
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
