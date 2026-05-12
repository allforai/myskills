#!/usr/bin/env python3
"""Validate bundled SKILL.md files for basic contract hygiene.

This is intentionally structural, not semantic. It catches low-level mistakes
that are easy to introduce while editing skills: broken frontmatter, malformed
Invocation Contract JSON, missing canonical child paths, duplicate names, and
obvious artifact path problems.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

try:
    import yaml
    _HAS_YAML = True
except ImportError:
    _HAS_YAML = False


FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
JSON_BLOCK_RE = re.compile(r"```json\n(.*?)\n```", re.DOTALL)
CANONICAL_SKILL_PATH_RE = re.compile(
    r"\$\{CLAUDE_PLUGIN_ROOT\}/skills/([^\s`]+/SKILL\.md)"
)
PATH_KEYS = {
    "input_paths",
    "output_root",
    "skill_index",
    "composition_plan",
    "artifact_graph",
    "bootstrap_profile",
}


def _parse_frontmatter(text: str):
    match = FRONTMATTER_RE.search(text)
    if not match:
        return None, "missing YAML frontmatter"
    raw = match.group(1)
    if _HAS_YAML:
        try:
            data = yaml.safe_load(raw)
        except Exception as exc:
            return None, f"frontmatter YAML parse error: {exc}"
        if not isinstance(data, dict):
            return None, "frontmatter is not a mapping"
        return data, None

    data = {}
    for line in raw.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            data[key.strip()] = value.strip()
    return data, None


def _iter_paths(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from _iter_paths(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from _iter_paths(item)


def _is_artifact_path(value: str) -> bool:
    return (
        value.startswith(".allforai/")
        or value.startswith("${CLAUDE_PLUGIN_ROOT}/")
        or value.startswith("$CLAUDE_PLUGIN_ROOT/")
        or value.startswith("claude/meta-skill/")
    )


def _skill_value_exists(skill_root: Path, skill_value: str) -> bool:
    parts = skill_value.split("/")
    if not parts:
        return False
    prefix = parts[0]
    leaf = parts[-1]
    base = skill_root / prefix
    if not base.exists():
        return False
    return any(path.parent.name == leaf for path in base.rglob("SKILL.md"))


def validate_skill_tree(skill_root: str) -> list:
    root = Path(skill_root)
    errors = []
    skill_files = sorted(root.rglob("SKILL.md"))
    names = {}

    if not root.exists():
        return [f"{skill_root}: skill root does not exist"]
    if not skill_files:
        return [f"{skill_root}: no SKILL.md files found"]

    for path in skill_files:
        rel = path.relative_to(root)
        try:
            text = path.read_text()
        except Exception as exc:
            errors.append(f"{rel}: cannot read: {exc}")
            continue

        fm, fm_error = _parse_frontmatter(text)
        if fm_error:
            errors.append(f"{rel}: {fm_error}")
            continue

        name = fm.get("name")
        description = fm.get("description")
        if not name:
            errors.append(f"{rel}: frontmatter missing name")
        elif name in names:
            errors.append(f"{rel}: duplicate skill name '{name}' also in {names[name]}")
        else:
            names[name] = rel
        if not description:
            errors.append(f"{rel}: frontmatter missing description")

        for target in CANONICAL_SKILL_PATH_RE.findall(text):
            target_path = root / target
            if not target_path.exists():
                errors.append(f"{rel}: canonical skill path missing: skills/{target}")

        json_blocks = JSON_BLOCK_RE.findall(text)
        if "## Invocation Contract" in text and not json_blocks:
            errors.append(f"{rel}: Invocation Contract has no json fenced block")

        for idx, block in enumerate(json_blocks, start=1):
            try:
                payload = json.loads(block)
            except Exception as exc:
                errors.append(f"{rel}: json block {idx} cannot parse: {exc}")
                continue
            if not isinstance(payload, dict):
                continue

            is_invocation = bool({"skill", "mode", "input_paths", "output_root"} & set(payload))
            if {"skill", "mode"} & set(payload):
                skill_value = payload.get("skill")
                if not skill_value:
                    errors.append(f"{rel}: invocation json block {idx} missing skill")
                elif not _skill_value_exists(root, skill_value):
                    errors.append(
                        f"{rel}: invocation skill '{skill_value}' has no matching SKILL.md"
                    )
                if not payload.get("mode"):
                    errors.append(f"{rel}: invocation json block {idx} missing mode")
                if not payload.get("output_root"):
                    errors.append(f"{rel}: invocation json block {idx} missing output_root")

            if not is_invocation:
                continue

            for key in PATH_KEYS & set(payload):
                for artifact_path in _iter_paths(payload[key]):
                    if not artifact_path:
                        errors.append(f"{rel}: json block {idx} contains empty path under {key}")
                    elif key != "skill_index" and not _is_artifact_path(artifact_path):
                        errors.append(
                            f"{rel}: json block {idx} path '{artifact_path}' under {key} "
                            "is not an .allforai or plugin-root path"
                        )

    return errors


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "skill_root",
        nargs="?",
        default="claude/meta-skill/skills",
        help="Path to bundled skill root",
    )
    args = parser.parse_args(argv)
    errors = validate_skill_tree(args.skill_root)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
