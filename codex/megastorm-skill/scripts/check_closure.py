#!/usr/bin/env python3
"""§4.2 闭环 (closed-loop) deterministic lens. Operates on structured manifests the
design agents emit alongside their markdown (covers_req_ids / exposes / consumes),
NOT on prose. Checks: forward coverage (every spec requirement covered), no orphan
requirement ids (design->ghost req), interface consistency (every consume has a
matching expose). Unconsumed exposes are advisory WARNs. Prose-level 'does design
actually satisfy req' is the LLM critic's job, not this script's."""
import json
import sys


def check_closure(requirements, manifests, interface_registry=None):
    """interface_registry: optional frozen closed-vocabulary of interface names
    (minted in Phase 0, written into the overview). When provided, any exposes/consumes
    name outside it is a naming-drift error — this is what stops parallel design agents
    from spelling the same interface three different ways (Finding 2)."""
    errors, warnings = [], []
    req_set = set(requirements)
    reg = set(interface_registry) if interface_registry is not None else None
    covered, exposes, consumes = set(), set(), set()
    for m in manifests:
        for rid in m.get("covers_req_ids", []):
            covered.add(rid)
            if rid not in req_set:
                errors.append(f"design '{m.get('module')}' covers orphan requirement '{rid}' (not in any spec)")
        for e in m.get("exposes", []):
            exposes.add(e)
            if reg is not None and e not in reg:
                errors.append(f"design '{m.get('module')}' exposes '{e}' not in the frozen interface registry")
        for c in m.get("consumes", []):
            consumes.add((m.get("module"), c))
            if reg is not None and c not in reg:
                errors.append(f"design '{m.get('module')}' consumes '{c}' not in the frozen interface registry")

    for rid in sorted(req_set - covered):
        errors.append(f"requirement '{rid}' is uncovered by any design")
    for module, c in sorted(consumes):
        if c not in exposes:
            errors.append(f"design '{module}' consumes '{c}' which no design exposes (dangling interface)")
    consumed_names = {c for _, c in consumes}
    for e in sorted(exposes - consumed_names):
        warnings.append(f"interface '{e}' is exposed but never consumed (possible orphan)")

    return {"ok": len(errors) == 0, "errors": errors, "warnings": warnings}


def main(argv):
    if len(argv) < 3:
        print("usage: check_closure.py <requirements.json> <manifests.json> [interface_registry.json]", file=sys.stderr)
        return 2
    requirements = json.load(open(argv[1]))
    manifests = json.load(open(argv[2]))
    registry = json.load(open(argv[3])) if len(argv) > 3 else None
    if isinstance(requirements, dict):
        requirements = requirements.get("requirements", [])
    if isinstance(manifests, dict):
        manifests = manifests.get("manifests", [])
    if isinstance(registry, dict):
        registry = registry.get("interfaces", [])
    r = check_closure(requirements, manifests, interface_registry=registry)
    print(json.dumps(r, indent=2))
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
