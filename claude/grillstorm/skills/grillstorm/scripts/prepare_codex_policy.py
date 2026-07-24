#!/usr/bin/env python3
"""Prepare a conservative inherited Codex worker policy from the current host."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess

from host_command import resolve_invocation
from model_policy import (
    ModelPolicyError,
    ModelSource,
    PRECEDENCE,
    create_policy_artifact,
    recommend_policy,
)


def ensure_outside_repository(output, cwd=None):
    probe = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    if probe.returncode != 0:
        return
    root = Path(probe.stdout.strip()).resolve()
    target = Path(output).resolve()
    try:
        target.relative_to(root)
    except ValueError:
        return
    raise ValueError("policy output directory must be outside the Git repository")


def build_sources(invocation):
    records = []
    for name in PRECEDENCE:
        status = "unknown"
        evidence = "not proven overridable; inherit the active host model"
        if name == "argv" and invocation.argv_model:
            status = "locked"
            evidence = "active Codex argv owns the model"
        elif name == "wrapper" and invocation.wrapper_model_ownership:
            status = invocation.wrapper_model_ownership
            evidence = invocation.wrapper_model_evidence
        records.append(ModelSource(name, status, evidence))
    return records


def select_policy(think, verify, build, sources):
    values = (think, verify, build)
    if not any(values):
        return "inherited", {}, {
            "think": "<host-owned>",
            "verify": "<host-owned>",
            "bulk": "<host-owned>",
        }
    if not all(isinstance(value, str) and value.strip() for value in values):
        raise ValueError("tiered policy requires THINK, VERIFY, and BUILD model names")
    recommendation, reason = recommend_policy(sources)
    if recommendation != "tiered":
        raise ValueError(f"tiered policy is not allowed: {reason}")
    mappings = {"THINK": think, "VERIFY": verify, "BULK": build}
    return "tiered", mappings, {
        "think": think,
        "verify": verify,
        "bulk": build,
    }


def write_private(path, data):
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    fd = os.open(path, flags, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(data)
    finally:
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir")
    parser.add_argument("--confirmed-by", default="approved Grillstorm launch contract")
    parser.add_argument("--model-sources-input")
    parser.add_argument("--think-model")
    parser.add_argument("--verify-model")
    parser.add_argument("--build-model")
    args = parser.parse_args(argv)

    output = Path(args.output_dir).resolve()
    try:
        ensure_outside_repository(output)
    except ValueError as exc:
        parser.error(str(exc))
    output.mkdir(parents=True, exist_ok=True)
    invocation = resolve_invocation()
    if args.model_sources_input:
        raw_sources = json.loads(Path(args.model_sources_input).read_text(encoding="utf-8"))
        sources = [
            ModelSource(
                item["name"],
                item["status"],
                item["evidence"],
                tuple(item.get("paths", ())),
            )
            for item in raw_sources
        ]
    else:
        sources = build_sources(invocation)
    try:
        choice, mappings, models = select_policy(
            args.think_model,
            args.verify_model,
            args.build_model,
            sources,
        )
    except (ValueError, ModelPolicyError) as exc:
        parser.error(str(exc))
    key = os.urandom(32)
    version = subprocess.run(
        [invocation.executable, "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    codex_version = (version.stdout or version.stderr).strip()
    if version.returncode != 0 or not codex_version:
        parser.error("cannot determine Codex version")

    artifact = create_policy_artifact(
        invocation,
        sources,
        choice,
        args.confirmed_by,
        datetime.now(timezone.utc).isoformat(),
        key,
        model_mappings=mappings,
        codex_version=codex_version,
    )
    source_payload = [
        {
            "name": item.name,
            "status": item.status,
            "evidence": item.evidence,
            "paths": list(item.paths),
        }
        for item in sources
    ]

    key_path = output / "policy.key"
    key_fd = os.open(key_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(key_fd, "wb") as handle:
        handle.write(key)
    os.chmod(key_path, 0o600)
    write_private(
        output / "model-policy.json",
        json.dumps(artifact, indent=2) + "\n",
    )
    write_private(
        output / "model-sources.json",
        json.dumps(source_payload, indent=2) + "\n",
    )
    write_private(
        output / "models.json",
        json.dumps(models, indent=2) + "\n",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
