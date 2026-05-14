#!/usr/bin/env python3
"""Recommend workflow nodes to rerun after meta-skill updates.

The analyzer is intentionally conservative: it maps changed skill/knowledge
files to existing bootstrap node-specs by explicit references first, then by
domain heuristics. It writes auditable JSON and Markdown so setup/update can
show exactly why a rerun is recommended.
"""

import argparse
import json
import os
import re
import subprocess
from pathlib import Path


DEFAULT_OUTPUT_ROOT = ".allforai/setup"
WORKFLOW_PATH = ".allforai/bootstrap/workflow.json"
NODE_SPECS_DIR = ".allforai/bootstrap/node-specs"


SKILL_PATH_RE = re.compile(r"claude/meta-skill/skills/([^\s]+/SKILL\.md)")


def _read_text(path: Path) -> str:
    try:
        return path.read_text()
    except Exception:
        return ""


def _load_json(path: Path):
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def _current_version(repo_root: Path) -> str | None:
    text = _read_text(repo_root / "claude/meta-skill/SKILL.md")
    match = re.search(r'version:\s*"([^"]+)"', text)
    return match.group(1) if match else None


def _git_changed_files(repo_root: Path, from_ref: str | None) -> tuple[list[str], str]:
    if not from_ref:
        return [], "none"
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", f"{from_ref}..HEAD"],
            cwd=repo_root,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except Exception:
        return [], "git_diff_failed"
    files = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return files, f"git:{from_ref}..HEAD"


def _normalize_changed_files(repo_root: Path, from_ref: str | None, explicit_files: list[str]) -> tuple[list[str], str]:
    files, source = _git_changed_files(repo_root, from_ref)
    if explicit_files:
        files.extend(explicit_files)
        source = "explicit" if source == "none" else f"{source}+explicit"
    seen = set()
    normalized = []
    for item in files:
        value = item.strip()
        if not value or value in seen:
            continue
        seen.add(value)
        normalized.append(value)
    return normalized, source


def _load_workflow(project_root: Path) -> dict:
    workflow = _load_json(project_root / WORKFLOW_PATH)
    if not isinstance(workflow, dict):
        return {"nodes": []}
    nodes = workflow.get("nodes")
    if not isinstance(nodes, list):
        workflow["nodes"] = []
    return workflow


def _node_text(project_root: Path, node_id: str) -> str:
    return _read_text(project_root / NODE_SPECS_DIR / f"{node_id}.md")


def _node_id(node: dict) -> str:
    return node.get("node_id") or ""


def _node_blob(project_root: Path, node: dict) -> str:
    node_id = _node_id(node)
    blob = json.dumps(node, ensure_ascii=False).lower()
    if node_id:
        blob += "\n" + _node_text(project_root, node_id).lower()
    return blob


def _changed_skill_slugs(changed_files: list[str]) -> list[str]:
    slugs = []
    for path in changed_files:
        match = SKILL_PATH_RE.search(path)
        if match:
            slugs.append(match.group(1).removesuffix("/SKILL.md"))
    return slugs


def _domain_rules(path: str) -> list[dict]:
    rules = []
    if "claude/meta-skill/skills/bootstrap.md" in path or "commands/bootstrap.md" in path:
        rules.append({
            "scope": "bootstrap",
            "reason": "bootstrap workflow generation changed",
            "rerun": "rerun /bootstrap before continuing project execution",
            "severity": "high",
        })
    if "claude/meta-skill/commands/setup.md" in path or "analyze_skill_update_impact.py" in path:
        rules.append({
            "scope": "setup",
            "reason": "setup/update impact logic changed",
            "rerun": "rerun /setup impact to refresh rerun recommendations",
            "severity": "medium",
        })
    if "claude/meta-skill/skills/game-art/" in path:
        rules.append({
            "scope": "game-art",
            "reason": "game art generation or QA contract changed",
            "rerun": "rerun art-generation/art-qa nodes that produced or accepted images",
            "severity": "high",
        })
    if "claude/meta-skill/skills/visual-qa/" in path:
        rules.append({
            "scope": "visual-qa",
            "reason": "visual QA/review contract changed",
            "rerun": "rerun visual acceptance, screenshot review, and art-qa nodes",
            "severity": "high",
        })
    if "claude/meta-skill/skills/game-frontend/" in path:
        rules.append({
            "scope": "game-frontend",
            "reason": "game frontend runtime contract changed",
            "rerun": "rerun game frontend binding, smoke, and visual runtime QA nodes",
            "severity": "medium",
        })
    if (
        "claude/meta-skill/skills/game-2d-production/" in path
        or "expand_game_2d_production.py" in path
        or "validate_game_2d_production_pipeline.py" in path
    ):
        rules.append({
            "scope": "game-2d-production",
            "reason": "2D game production closure or workflow expansion contract changed",
            "rerun": "rerun /bootstrap or run expand_game_2d_production.py, then rerun 2D production closure nodes",
            "severity": "high",
        })
    if "claude/meta-skill/skills/game-design/" in path:
        rules.append({
            "scope": "game-design",
            "reason": "game product design contract changed",
            "rerun": "rerun affected game-design node and downstream handoff/art-input nodes",
            "severity": "medium",
        })
    if "claude/meta-skill/skills/app-design/" in path:
        rules.append({
            "scope": "app-design",
            "reason": "app product design contract changed",
            "rerun": "rerun affected app-design node and downstream program/UI handoff nodes",
            "severity": "medium",
        })
    return rules


def _node_matches_domain(blob: str, scope: str) -> bool:
    terms_by_scope = {
        "game-art": ("game-art", "art-qa", "image-generation", "asset-registry", "visual-acceptance"),
        "visual-qa": ("visual", "screenshot", "codex-visual", "visual-qa", "art-qa"),
        "game-frontend": ("game-frontend", "runtime", "smoke", "visual-runtime", "client"),
        "game-2d-production": ("game-2d-production", "game-2d", "2d-production", "playable-slice", "core-loop-playability"),
        "game-design": ("game-design", "game", "core-loop", "level", "economy", "handoff"),
        "app-design": ("app-design", "screen", "user-flow", "interaction", "handoff"),
        "bootstrap": ("bootstrap",),
        "setup": ("setup",),
    }
    return any(term in blob for term in terms_by_scope.get(scope, (scope,)))


def analyze(repo_root: str, project_root: str, from_ref: str | None = None, changed_file: list[str] | None = None) -> dict:
    repo = Path(repo_root).resolve()
    project = Path(project_root).resolve()
    changed_files, change_source = _normalize_changed_files(repo, from_ref, changed_file or [])
    workflow = _load_workflow(project)
    nodes = workflow.get("nodes", [])
    skill_slugs = _changed_skill_slugs(changed_files)

    recommendations_by_node: dict[str, dict] = {}
    global_recommendations = []

    for changed in changed_files:
        changed_l = changed.lower()
        rules = _domain_rules(changed)
        if rules:
            global_recommendations.extend(rules)

        for node in nodes:
            node_id = _node_id(node)
            if not node_id:
                continue
            blob = _node_blob(project, node)
            reasons = []

            for slug in skill_slugs:
                if slug.lower() in blob:
                    reasons.append(f"node-spec references changed skill {slug}")

            for rule in rules:
                if _node_matches_domain(blob, rule["scope"]):
                    reasons.append(rule["reason"])

            if changed_l.endswith("bootstrap.md") and node_id:
                reasons.append("workflow generator changed; node may need regeneration")

            if not reasons:
                continue

            existing = recommendations_by_node.setdefault(node_id, {
                "node_id": node_id,
                "capability": node.get("capability"),
                "severity": "medium",
                "reasons": [],
                "recommended_action": "rerun node and downstream consumers if its output changed",
                "exit_artifacts": node.get("exit_artifacts", []),
            })
            existing["reasons"].extend(reason for reason in reasons if reason not in existing["reasons"])
            if any(rule.get("severity") == "high" for rule in rules):
                existing["severity"] = "high"

    if not changed_files:
        global_recommendations.append({
            "scope": "unknown",
            "reason": "no changed files were supplied or discovered",
            "rerun": "provide --from-ref or --changed-file, otherwise inspect recent release notes manually",
            "severity": "medium",
        })

    return {
        "schema_version": "1.0",
        "meta_skill_version": _current_version(repo),
        "change_source": change_source,
        "changed_files": changed_files,
        "changed_skill_slugs": skill_slugs,
        "workflow_path": str(project / WORKFLOW_PATH),
        "node_count": len(nodes),
        "global_recommendations": global_recommendations,
        "node_recommendations": sorted(recommendations_by_node.values(), key=lambda item: (item["severity"] != "high", item["node_id"])),
        "state": "completed" if changed_files else "needs_change_input",
    }


def write_reports(result: dict, output_root: str) -> tuple[Path, Path]:
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    json_path = root / "skill-update-impact.json"
    md_path = root / "skill-update-impact.md"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")

    lines = [
        "# Skill Update Impact",
        "",
        f"- meta-skill version: `{result.get('meta_skill_version')}`",
        f"- state: `{result.get('state')}`",
        f"- change source: `{result.get('change_source')}`",
        f"- changed files: {len(result.get('changed_files', []))}",
        f"- matched nodes: {len(result.get('node_recommendations', []))}",
        "",
        "## Global Recommendations",
    ]
    for item in result.get("global_recommendations", []):
        lines.append(f"- `{item['scope']}` {item['severity']}: {item['rerun']} ({item['reason']})")
    if not result.get("global_recommendations"):
        lines.append("- none")

    lines.extend(["", "## Node Recommendations"])
    for item in result.get("node_recommendations", []):
        reasons = "; ".join(item.get("reasons", []))
        lines.append(f"- `{item['node_id']}` {item['severity']}: {item['recommended_action']} ({reasons})")
    if not result.get("node_recommendations"):
        lines.append("- none")

    md_path.write_text("\n".join(lines) + "\n")
    return json_path, md_path


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--from-ref")
    parser.add_argument("--changed-file", action="append", default=[])
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT)
    args = parser.parse_args(argv)

    result = analyze(args.repo_root, args.project_root, args.from_ref, args.changed_file)
    json_path, md_path = write_reports(result, args.output_root)
    print(f"wrote {json_path}")
    print(f"wrote {md_path}")
    return 0 if result["state"] == "completed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
