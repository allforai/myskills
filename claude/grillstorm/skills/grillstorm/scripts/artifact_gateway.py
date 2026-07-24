#!/usr/bin/env python3
"""Deterministic admission gate for untrusted Grillstorm worker artifacts."""
from dataclasses import dataclass
import fnmatch
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess


class ArtifactViolation(RuntimeError):
    pass


OPERATIONS = {"create", "modify", "delete", "rename"}
CONTROL_PLANE_DEFAULTS = (
    "docs/grillstorm/**",
    "orchestration.json", "all-tasks.json", "models.json",
    "tasks.json", "model-policy*.json", "model-sources*.json",
    "execution-checkpoint.json", "workflow-state*.json",
    "workflow-events*.jsonl", "workflow-report*.json",
    "requirements-state-registry.json", "probe-plan.json",
    "probe-results.jsonl", "probe-state.json", "gap-manifest.json",
    ".grillstorm/**", "prompts/**", "**/prompts/**",
    "scripts/run_layers.py", "**/scripts/run_layers.py",
    "scripts/model_policy.py", "**/scripts/model_policy.py",
    "scripts/artifact_gateway.py", "**/scripts/artifact_gateway.py",
)


@dataclass(frozen=True)
class Change:
    operation: str
    path: str
    source: str = ""


def canonical_json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode()


def normalize_path(raw):
    if not isinstance(raw, str) or not raw or "\0" in raw or "\\" in raw:
        raise ArtifactViolation(f"invalid repository path: {raw!r}")
    path = PurePosixPath(raw)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        raise ArtifactViolation(f"unsafe repository path: {raw!r}")
    normalized = path.as_posix()
    if normalized != raw.rstrip("/"):
        raise ArtifactViolation(f"non-canonical repository path: {raw!r}")
    return normalized


def validate_contract(contract):
    if not isinstance(contract, dict) or contract.get("schema_version") != 1:
        raise ArtifactViolation("task artifact contract schema_version must be 1")
    if "expected_interfaces" in contract or "allowed_paths" in contract:
        raise ArtifactViolation("legacy path/interface contract fields are forbidden")
    required = ("task_id", "path_rules", "required_outputs", "forbidden_paths",
                "acceptance_cmd_sha256", "interface_assertions", "max_files_changed")
    missing = [key for key in required if key not in contract]
    if missing:
        raise ArtifactViolation(f"task artifact contract missing: {missing}")
    if not isinstance(contract["task_id"], str) or not contract["task_id"]:
        raise ArtifactViolation("task_id must be non-empty")
    rules = contract["path_rules"]
    if not isinstance(rules, list) or not rules:
        raise ArtifactViolation("path_rules must be non-empty")
    for rule in rules:
        if not isinstance(rule, dict) or set(rule) != {"pattern", "kind", "operations"}:
            raise ArtifactViolation("path rule has unknown/missing fields")
        normalize_path(rule["pattern"].replace("*", "x").replace("?", "x"))
        if rule["kind"] not in {"literal", "glob"}:
            raise ArtifactViolation("path rule kind must be literal|glob")
        if rule["kind"] == "literal" and any(c in rule["pattern"] for c in "*?["):
            raise ArtifactViolation("literal path rule contains glob syntax")
        ops = rule["operations"]
        if not isinstance(ops, list) or not ops or not set(ops) <= OPERATIONS:
            raise ArtifactViolation("path rule operations are invalid")
    for key in ("required_outputs", "forbidden_paths"):
        if not isinstance(contract[key], list):
            raise ArtifactViolation(f"{key} must be an array")
    if not isinstance(contract["acceptance_cmd_sha256"], str) or len(
            contract["acceptance_cmd_sha256"]) != 64:
        raise ArtifactViolation("acceptance_cmd_sha256 must be SHA-256")
    if not isinstance(contract["max_files_changed"], int) or contract["max_files_changed"] < 0:
        raise ArtifactViolation("max_files_changed must be non-negative")
    for assertion in contract["interface_assertions"]:
        expected = {"schema_version", "kind", "interface_id", "artifact_path",
                    "verifier_id", "verifier_sha256"}
        if not isinstance(assertion, dict) or set(assertion) != expected:
            raise ArtifactViolation("interface assertion shape is invalid")
        if assertion["schema_version"] != 1:
            raise ArtifactViolation("interface assertion schema is unsupported")
        normalize_path(assertion["artifact_path"])
        if len(assertion["verifier_sha256"]) != 64:
            raise ArtifactViolation("interface verifier hash is invalid")
    return hashlib.sha256(canonical_json(contract)).hexdigest()


def _matches(path, pattern, kind):
    if kind == "literal":
        return path == pattern
    return fnmatch.fnmatchcase(path, pattern)


def _operation_allowed(change, rules):
    return any(_matches(change.path, rule["pattern"], rule["kind"])
               and change.operation in rule["operations"] for rule in rules)


def _forbidden(path, patterns):
    return any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns)


def git_changes(repo, base_commit):
    """Return actual committed/working operations, preserving rename endpoints."""
    result = subprocess.run(
        ["git", "diff", "--name-status", "-z", "--find-renames", base_commit],
        cwd=str(repo), capture_output=True, check=False,
    )
    if result.returncode != 0:
        raise ArtifactViolation("cannot inspect worker diff")
    fields = result.stdout.split(b"\0")
    changes = []
    i = 0
    while i < len(fields) and fields[i]:
        code = fields[i].decode("ascii", "strict"); i += 1
        op = code[0]
        if op in {"R", "C"}:
            if i + 1 >= len(fields):
                raise ArtifactViolation("truncated rename record")
            source = normalize_path(fields[i].decode("utf-8", "strict")); i += 1
            dest = normalize_path(fields[i].decode("utf-8", "strict")); i += 1
            changes.append(Change("rename", dest, source))
        else:
            if i >= len(fields):
                raise ArtifactViolation("truncated change record")
            path = normalize_path(fields[i].decode("utf-8", "strict")); i += 1
            operation = {"A": "create", "M": "modify", "D": "delete"}.get(op)
            if operation is None:
                raise ArtifactViolation(f"unsupported Git operation: {code}")
            changes.append(Change(operation, path))
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard", "-z"], cwd=str(repo),
        capture_output=True, check=False,
    )
    if untracked.returncode != 0:
        raise ArtifactViolation("cannot inspect untracked worker files")
    known = {change.path for change in changes}
    for raw in untracked.stdout.split(b"\0"):
        if raw:
            path = normalize_path(raw.decode("utf-8", "strict"))
            if path not in known:
                changes.append(Change("create", path))
    # Git does not classify an unstaged delete + untracked create as a rename.
    # Pair unique byte-identical endpoints deterministically against the baseline.
    deletes = [change for change in changes if change.operation == "delete"]
    creates = [change for change in changes if change.operation == "create"]
    pairs = []
    used_creates = set()
    for deleted in deletes:
        old = subprocess.run(["git", "show", f"{base_commit}:{deleted.path}"],
                             cwd=str(repo), capture_output=True, check=False)
        if old.returncode != 0:
            continue
        candidates = []
        for created in creates:
            if created.path in used_creates:
                continue
            try:
                current = (Path(repo) / created.path).read_bytes()
            except OSError:
                continue
            if current == old.stdout:
                candidates.append(created)
        if len(candidates) == 1:
            created = candidates[0]
            used_creates.add(created.path)
            pairs.append((deleted, created))
    for deleted, created in pairs:
        changes.remove(deleted); changes.remove(created)
        changes.append(Change("rename", created.path, deleted.path))
    changes.sort(key=lambda change: (change.path, change.source, change.operation))
    return changes


def _check_path_object(root, change):
    path = root / change.path
    if change.operation == "delete":
        return
    tracked = subprocess.run(["git", "ls-files", "-s", "--", change.path],
                             cwd=str(root), capture_output=True, text=True, check=False)
    if any(line.startswith("160000 ") for line in tracked.stdout.splitlines()):
        raise ArtifactViolation(f"submodule/gitlink artifact is not admitted: {change.path}")
    current = root
    for part in PurePosixPath(change.path).parts:
        current = current / part
        try:
            info = current.lstat()
        except FileNotFoundError:
            raise ArtifactViolation(f"declared artifact is missing: {change.path}")
        if stat.S_ISLNK(info.st_mode):
            target = current.resolve()
            try:
                target.relative_to(root)
            except ValueError as exc:
                raise ArtifactViolation(f"symlink escapes task worktree: {change.path}") from exc
        if stat.S_ISREG(info.st_mode) and info.st_nlink > 1:
            raise ArtifactViolation(f"hardlinked artifact is not admitted: {change.path}")
    if path.is_dir() and (path / ".git").exists():
        raise ArtifactViolation(f"nested repository artifact is not admitted: {change.path}")


def admit_artifacts(repo, contract, changes, acceptance_cmd, control_hashes,
                    interface_verifiers=None):
    """Validate untrusted worker files; return immutable admission evidence."""
    contract_hash = validate_contract(contract)
    root = Path(repo).resolve()
    actual_acceptance = hashlib.sha256(acceptance_cmd.encode()).hexdigest()
    if actual_acceptance != contract["acceptance_cmd_sha256"]:
        raise ArtifactViolation("acceptance command hash changed")
    if len(changes) > contract["max_files_changed"]:
        raise ArtifactViolation("worker changed too many files")
    folded = {}
    forbidden = tuple(contract["forbidden_paths"]) + CONTROL_PLANE_DEFAULTS
    for change in changes:
        path = normalize_path(change.path)
        collision = folded.setdefault(path.casefold(), path)
        if collision != path:
            raise ArtifactViolation(f"case-fold path collision: {collision}, {path}")
        if _forbidden(path, forbidden):
            raise ArtifactViolation(f"worker modified frozen/forbidden path: {path}")
        if not _operation_allowed(change, contract["path_rules"]):
            raise ArtifactViolation(f"worker operation outside artifact contract: {change}")
        if change.operation == "rename":
            source = normalize_path(change.source)
            source_change = Change("rename", source)
            if _forbidden(source, forbidden) or not _operation_allowed(
                    source_change, contract["path_rules"]):
                raise ArtifactViolation(f"rename source outside artifact contract: {source}")
        _check_path_object(root, change)
    changed_paths = {change.path for change in changes if change.operation != "delete"}
    for required in contract["required_outputs"]:
        path = normalize_path(required)
        if path not in changed_paths or not (root / path).is_file():
            raise ArtifactViolation(f"required output missing: {path}")
    for rel, expected in control_hashes.items():
        path = root / normalize_path(rel)
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ArtifactViolation(f"frozen control-plane drift: {rel}")
    interface_verifiers = interface_verifiers or {}
    verified_interfaces = []
    for assertion in contract["interface_assertions"]:
        entry = interface_verifiers.get(assertion["verifier_id"])
        if not entry or entry[0] != assertion["verifier_sha256"]:
            raise ArtifactViolation(f"unknown interface verifier: {assertion['verifier_id']}")
        if entry[1](root, assertion) is not True:
            raise ArtifactViolation(f"interface assertion failed: {assertion['interface_id']}")
        verified_interfaces.append(assertion["interface_id"])
    evidence = {
        "contract_sha256": contract_hash,
        "acceptance_cmd_sha256": actual_acceptance,
        "changes": [change.__dict__ for change in changes],
        "interfaces": verified_interfaces,
        "artifact_sha256": {
            change.path: hashlib.sha256((root / change.path).read_bytes()).hexdigest()
            for change in changes
            if change.operation != "delete" and (root / change.path).is_file()
        },
    }
    evidence["admission_sha256"] = hashlib.sha256(canonical_json(evidence)).hexdigest()
    return evidence
