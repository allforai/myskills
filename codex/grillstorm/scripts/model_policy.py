#!/usr/bin/env python3
"""Frozen Phase 0 model-policy decisions for Codex Grillstorm."""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from host_command import HostCommandError, argv_hmac, file_sha256


class ModelPolicyError(RuntimeError):
    pass


PRECEDENCE = ("wrapper", "argv", "profile", "config", "user_project", "default")
STATUSES = {"locked", "unlocked", "unknown"}


@dataclass(frozen=True)
class ModelSource:
    name: str
    status: str
    evidence: str
    paths: tuple = ()


def normalize_sources(sources):
    by_name = {}
    for source in sources:
        if isinstance(source, dict):
            source = ModelSource(source["name"], source["status"], source.get("evidence", ""),
                                 tuple(source.get("paths", ())))
        if not isinstance(source, ModelSource) or source.name not in PRECEDENCE:
            raise ModelPolicyError("invalid model source")
        if source.status not in STATUSES or not source.evidence:
            raise ModelPolicyError(f"invalid model-source evidence: {source.name}")
        if source.name in by_name:
            raise ModelPolicyError(f"duplicate model source: {source.name}")
        by_name[source.name] = source
    return tuple(by_name[name] for name in PRECEDENCE if name in by_name)


def recommend_policy(sources):
    sources = normalize_sources(sources)
    if any(source.status == "locked" for source in sources):
        return "inherited", "locked model source"
    if any(source.status == "unknown" for source in sources):
        return "inherited", "unknown model ownership; tiered is forbidden"
    if (set(source.name for source in sources) != set(PRECEDENCE) or
            not all(source.status == "unlocked" for source in sources)):
        raise ModelPolicyError("model ownership is not fully evidenced")
    return "tiered", "all effective model sources are proven overridable"


def _source_records(sources):
    records = []
    for source in normalize_sources(sources):
        files = []
        for raw in source.paths:
            path = str(Path(raw).resolve())
            files.append({"path": path, "sha256": file_sha256(path)})
        records.append({"name": source.name, "status": source.status,
                        "evidence": source.evidence, "files": files})
    return records


def _real_mapping(value):
    return isinstance(value, str) and value.strip() and value.lower() not in {
        "think-model", "verify-model", "bulk-model", "placeholder", "todo", "default"}


def create_policy_artifact(invocation, sources, choice, confirmed_by, confirmed_at,
                           integrity_key, model_mappings=None, environ=None,
                           codex_version=""):
    recommendation, reason = recommend_policy(sources)
    normalized = normalize_sources(sources)
    by_name = {source.name: source for source in normalized}
    if invocation.argv_model and ("argv" not in by_name or by_name["argv"].status != "locked"):
        raise ModelPolicyError("explicit argv model must be classified locked")
    if invocation.wrapper_model_ownership:
        wrapper = by_name.get("wrapper")
        if (wrapper is None or wrapper.status != invocation.wrapper_model_ownership or
                wrapper.evidence != invocation.wrapper_model_evidence):
            raise ModelPolicyError("wrapper model evidence does not match contract")
    if choice not in {"inherited", "tiered"}:
        raise ModelPolicyError("invalid model policy")
    if choice == "tiered" and recommendation != "tiered":
        raise ModelPolicyError("tiered policy cannot override locked or unknown ownership")
    mappings = {} if model_mappings is None else dict(model_mappings)
    if choice == "tiered" and (set(mappings) != {"THINK", "VERIFY", "BULK"} or
                               not all(_real_mapping(v) for v in mappings.values())):
        raise ModelPolicyError("tiered policy requires three real model mappings")
    invocation.verify_executables()
    return {
        "schema_version": 1,
        "model_policy": choice,
        "recommendation": recommendation,
        "recommendation_reason": reason,
        "confirmed": True,
        "confirmed_by": confirmed_by,
        "confirmed_at": confirmed_at,
        "command_source": invocation.source,
        "redacted_command": invocation.metadata(environ)["discovered_argv"],
        "argv_hmac_sha256": argv_hmac(invocation.materialized_discovered_argv(environ), integrity_key),
        "executable_pins": [{"path": p, "sha256": digest}
                            for p, digest in invocation.executable_pins],
        "wrapper_contract_hash": invocation.wrapper_contract_hash,
        "codex_version": codex_version,
        "model_sources": _source_records(normalized),
        "model_mappings": mappings if choice == "tiered" else {},
        "detected_model_source": next((s.name for s in normalized if s.status == "locked"),
                                      "default"),
        "child_preview": invocation.build(
            mappings.get("BULK", "<host-owned>"), "<task-worktree>",
            "<attempt-result>", "<prompt>", choice, environ),
    }


def validate_policy_artifact(artifact, invocation, sources, integrity_key,
                             environ=None, codex_version=""):
    if not isinstance(artifact, dict) or artifact.get("schema_version") != 1:
        raise ModelPolicyError("unsupported policy artifact")
    if artifact.get("confirmed") is not True or not artifact.get("confirmed_by") or not artifact.get("confirmed_at"):
        raise ModelPolicyError("policy artifact lacks Phase 0 confirmation")
    invocation.verify_executables()
    expected_hmac = argv_hmac(invocation.materialized_discovered_argv(environ), integrity_key)
    if artifact.get("argv_hmac_sha256") != expected_hmac:
        raise ModelPolicyError("host argv drift")
    if artifact.get("wrapper_contract_hash") != invocation.wrapper_contract_hash:
        raise ModelPolicyError("wrapper contract drift")
    if codex_version and artifact.get("codex_version") != codex_version:
        raise ModelPolicyError("Codex version drift")
    current_records = _source_records(sources)
    if artifact.get("model_sources") != current_records:
        raise ModelPolicyError("model source/config drift")
    recommendation, _ = recommend_policy(sources)
    choice = artifact.get("model_policy")
    if choice == "tiered" and recommendation != "tiered":
        raise ModelPolicyError("tiered policy is no longer safe")
    mappings = artifact.get("model_mappings", {})
    if choice == "tiered" and (set(mappings) != {"THINK", "VERIFY", "BULK"} or
                               not all(_real_mapping(v) for v in mappings.values())):
        raise ModelPolicyError("invalid tiered mappings")
    if choice not in {"inherited", "tiered"}:
        raise ModelPolicyError("invalid frozen model policy")
    canonical = json.dumps(artifact, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return {"model_policy": choice,
            "fingerprint": hashlib.sha256(canonical.encode()).hexdigest(),
            "model_mappings": mappings}
