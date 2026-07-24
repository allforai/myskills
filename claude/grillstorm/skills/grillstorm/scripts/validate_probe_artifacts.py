#!/usr/bin/env python3
"""Validate Grillstorm post-delivery probe plans, evidence, and saturation."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath


LOGIC_CHANNELS = {"code", "document"}
RUNTIME_CHANNELS = {
    "browser", "api", "cli", "library", "data", "device", "external",
}
RESULT_STATUSES = {"pass", "gap"}
EVIDENCE_KINDS = {
    "code", "document", "screenshot", "dom", "network", "stdout", "stderr",
    "data", "log", "trace",
}
RUNTIME_EVIDENCE_KINDS = EVIDENCE_KINDS - {"code", "document"}


class ProbeValidationError(ValueError):
    pass


def _hash(value):
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def validate_registry(registry):
    if registry.get("schema_version") != 1 or not registry.get("delivery_run_id"):
        raise ProbeValidationError("invalid requirement-state registry header")
    requirements = registry.get("requirements")
    if not isinstance(requirements, list) or not requirements:
        raise ProbeValidationError("registry requires at least one requirement")
    cells = {}
    for requirement in requirements:
        rid = requirement.get("id")
        source = requirement.get("source")
        states = requirement.get("states")
        if not isinstance(rid, str) or not rid or not isinstance(source, str) or not source:
            raise ProbeValidationError("registry requirement lacks id/source")
        if not isinstance(states, list) or not states:
            raise ProbeValidationError(f"{rid}: no applicable states")
        for state in states:
            sid = state.get("id")
            risk = state.get("risk")
            key = (rid, sid)
            if not isinstance(sid, str) or not sid or risk not in {"high", "medium", "low"}:
                raise ProbeValidationError(f"{rid}: invalid state")
            if key in cells:
                raise ProbeValidationError(f"duplicate registry cell: {rid}/{sid}")
            cells[key] = risk
    return cells


def validate_plan(registry, plan):
    cells = validate_registry(registry)
    if plan.get("schema_version") != 1 or not isinstance(plan.get("round"), int):
        raise ProbeValidationError("invalid probe plan header")
    if plan.get("registry_fingerprint") != _hash(registry):
        raise ProbeValidationError("probe plan registry fingerprint mismatch")
    probes = plan.get("probes")
    if not isinstance(probes, list) or not probes:
        raise ProbeValidationError("probe plan is empty")
    probe_ids = set()
    covered = set()
    for probe in probes:
        pid = probe.get("id")
        axis = probe.get("axis")
        channel = probe.get("observation_channel")
        targets = probe.get("targets")
        if not isinstance(pid, str) or not pid or pid in probe_ids:
            raise ProbeValidationError("probe IDs must be unique and non-empty")
        probe_ids.add(pid)
        if axis == "logic-alignment":
            if channel not in LOGIC_CHANNELS:
                raise ProbeValidationError(f"{pid}: logic probe must inspect code/document")
        elif axis == "feature-state-completeness":
            if channel not in RUNTIME_CHANNELS:
                raise ProbeValidationError(f"{pid}: feature probe requires a runtime channel")
        else:
            raise ProbeValidationError(f"{pid}: invalid probe axis")
        if not isinstance(targets, list) or not targets:
            raise ProbeValidationError(f"{pid}: no registry targets")
        if not all(isinstance(probe.get(key), str) and probe[key].strip()
                   for key in ("action", "expected_evidence", "falsifier")):
            raise ProbeValidationError(f"{pid}: incomplete probe contract")
        for target in targets:
            key = (target.get("requirement"), target.get("state"))
            if key not in cells:
                raise ProbeValidationError(f"{pid}: unknown target {key}")
            covered.add(key)
    unsampled = set()
    for item in plan.get("unsampled", []):
        key = (item.get("requirement"), item.get("state"))
        if key not in cells or not item.get("reason"):
            raise ProbeValidationError(f"invalid unsampled cell: {key}")
        if cells[key] == "high":
            raise ProbeValidationError(f"high-risk cell cannot be unsampled: {key}")
        unsampled.add(key)
    missing = set(cells) - covered - unsampled
    if missing:
        raise ProbeValidationError(f"plan omits registry cells: {sorted(missing)}")
    return {probe["id"]: probe for probe in probes}


def load_results(path):
    results = []
    for number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            results.append(json.loads(line))
        except ValueError as exc:
            raise ProbeValidationError(f"invalid result JSONL line {number}") from exc
    return results


def validate_results(probes, results, evidence_root=None):
    root = Path(evidence_root).resolve() if evidence_root is not None else None
    by_id = {}
    for result in results:
        pid = result.get("probe_id")
        if result.get("schema_version") != 1 or pid not in probes or pid in by_id:
            raise ProbeValidationError(f"invalid or duplicate probe result: {pid}")
        if result.get("status") not in RESULT_STATUSES:
            raise ProbeValidationError(f"{pid}: invalid result status")
        evidence = result.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            raise ProbeValidationError(f"{pid}: evidence is required")
        for item in evidence:
            raw_path = item.get("path")
            if (item.get("kind") not in EVIDENCE_KINDS or
                    not isinstance(raw_path, str) or not raw_path or
                    not isinstance(item.get("sha256"), str) or
                    len(item["sha256"]) != 64):
                raise ProbeValidationError(f"{pid}: invalid evidence record")
            relative = PurePosixPath(raw_path)
            if relative.is_absolute() or any(part in ("", ".", "..") for part in relative.parts):
                raise ProbeValidationError(f"{pid}: unsafe evidence path")
            if root is not None:
                candidate = (root / relative.as_posix()).resolve()
                try:
                    candidate.relative_to(root)
                except ValueError as exc:
                    raise ProbeValidationError(f"{pid}: evidence escapes root") from exc
                if not candidate.is_file():
                    raise ProbeValidationError(f"{pid}: evidence file is missing: {raw_path}")
                actual = hashlib.sha256(candidate.read_bytes()).hexdigest()
                if actual != item["sha256"]:
                    raise ProbeValidationError(f"{pid}: evidence hash mismatch: {raw_path}")
        probe = probes[pid]
        if probe["axis"] == "feature-state-completeness":
            if result.get("runtime_attempted") is not True:
                raise ProbeValidationError(f"{pid}: feature result lacks a runtime attempt")
            if not isinstance(result.get("exit_code"), int):
                raise ProbeValidationError(f"{pid}: feature result lacks runtime exit code")
            if not any(item["kind"] in RUNTIME_EVIDENCE_KINDS for item in evidence):
                raise ProbeValidationError(f"{pid}: feature result lacks runtime evidence")
            if result["status"] == "pass" and result.get("runtime_started") is not True:
                raise ProbeValidationError(f"{pid}: feature pass lacks real runtime execution")
            if (result["status"] == "gap" and result.get("runtime_started") is not True and
                    result.get("failure_kind") != "runtime_start_failure"):
                raise ProbeValidationError(
                    f"{pid}: failed runtime start must be an explicit blocking gap"
                )
        if result["status"] == "gap" and not result.get("gap_ids"):
            raise ProbeValidationError(f"{pid}: gap result lacks gap IDs")
        by_id[pid] = result
    missing = set(probes) - set(by_id)
    if missing:
        raise ProbeValidationError(f"missing probe results: {sorted(missing)}")
    return by_id


def validate_gap_manifest(results, manifest, require_child_links=False):
    if manifest.get("schema_version") != 1 or not manifest.get("audit_cycle_id"):
        raise ProbeValidationError("invalid gap manifest header")
    gaps = manifest.get("gaps")
    if not isinstance(gaps, list):
        raise ProbeValidationError("gap manifest gaps must be an array")
    ids = set()
    for gap in gaps:
        gid = gap.get("id")
        if (not isinstance(gid, str) or not gid or gid in ids or
                not gap.get("family_fingerprint") or not gap.get("probe_ids") or
                not gap.get("affected_requirements") or
                not gap.get("affected_states") or
                not gap.get("recommended_scope") or
                not gap.get("acceptance_probes") or
                "child_delivery_run_id" not in gap or "child_state_path" not in gap):
            raise ProbeValidationError("invalid gap manifest entry")
        if require_child_links and (
                not isinstance(gap["child_delivery_run_id"], str) or
                not gap["child_delivery_run_id"] or
                not isinstance(gap["child_state_path"], str) or
                not gap["child_state_path"]
        ):
            raise ProbeValidationError(f"{gid}: remediation child link is missing")
        ids.add(gid)
    result_gap_ids = {
        gap_id
        for result in results.values()
        for gap_id in result.get("gap_ids", [])
    }
    if result_gap_ids != ids:
        raise ProbeValidationError("gap manifest does not match probe results")


def validate_saturation(state):
    if state.get("schema_version") != 1 or state.get("status") != "saturated":
        raise ProbeValidationError("audit state is not saturated")
    rounds = state.get("rounds")
    if not isinstance(rounds, list) or len(rounds) < 2:
        raise ProbeValidationError("saturation requires at least two rounds")
    for item in rounds[-2:]:
        if (item.get("new_gap_families") != 0 or
                item.get("new_blocking_members") != 0 or
                item.get("unexplored_cells") != 0):
            raise ProbeValidationError("last two rounds do not prove saturation")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("registry")
    parser.add_argument("plan")
    parser.add_argument("results")
    parser.add_argument("--evidence-root",
                        help="run directory used to resolve and hash every evidence path")
    parser.add_argument("--gap-manifest")
    parser.add_argument("--audit-state")
    parser.add_argument("--require-child-links", action="store_true",
                        help="require every gap to point to its remediation delivery run")
    args = parser.parse_args(argv)
    try:
        registry = json.loads(Path(args.registry).read_text(encoding="utf-8"))
        plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
        probes = validate_plan(registry, plan)
        evidence_root = args.evidence_root or str(Path(args.registry).resolve().parent)
        results = validate_results(probes, load_results(args.results), evidence_root)
        if args.gap_manifest:
            validate_gap_manifest(
                results,
                json.loads(Path(args.gap_manifest).read_text(encoding="utf-8")),
                require_child_links=args.require_child_links,
            )
        if args.audit_state:
            validate_saturation(
                json.loads(Path(args.audit_state).read_text(encoding="utf-8"))
            )
    except (OSError, ValueError, KeyError, ProbeValidationError) as exc:
        parser.error(str(exc))
    print("probe artifacts: valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
