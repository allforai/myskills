#!/usr/bin/env python3
"""Expand game_2d_production handoff into workflow nodes and node-specs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from validate_bootstrap import (
    GAME_2D_PRODUCTION_REQUIRED_ARTIFACTS,
    GAME_2D_PRODUCTION_REQUIRED_NODES,
    _game_2d_handoff_required,
)


NODE_DEFS = [
    {
        "node_id": "game-2d-runtime-profile",
        "skill": "game-2d-production/00-env/runtime-profile",
        "goal": "检测 2D 游戏运行时、命令、视口和自动化能力",
        "exit_artifacts": [".allforai/game-2d/env/2d-runtime-profile.json"],
    },
    {
        "node_id": "game-2d-view-mode-runtime-contract",
        "skill": "game-2d-production/20-spec/view-mode-runtime-contract",
        "goal": "生成 2D 视角、坐标、相机、层级和缩放运行契约",
        "exit_artifacts": [".allforai/game-2d/spec/view-mode-runtime-contract.json"],
    },
    {
        "node_id": "game-2d-core-loop-playable-contract",
        "skill": "game-2d-production/20-spec/core-loop-playable-contract",
        "goal": "生成 2D 核心循环可玩性执行契约",
        "exit_artifacts": [".allforai/game-2d/spec/core-loop-playable-contract.json"],
    },
    {
        "node_id": "game-2d-asset-runtime-binding-contract",
        "skill": "game-2d-production/20-spec/asset-runtime-binding-contract",
        "goal": "生成 2D 美术、UI、动画、特效和音频运行时绑定契约",
        "exit_artifacts": [".allforai/game-2d/spec/asset-runtime-binding-contract.json"],
    },
    {
        "node_id": "game-2d-input-feedback-contract",
        "skill": "game-2d-production/20-spec/input-feedback-contract",
        "goal": "生成 2D 输入与反馈闭环契约",
        "exit_artifacts": [".allforai/game-2d/spec/input-feedback-contract.json"],
    },
    {
        "node_id": "game-2d-session-flow-contract",
        "skill": "game-2d-production/20-spec/session-flow-contract",
        "goal": "生成 2D 启动、游玩、胜负、重试和继续的 session flow 契约",
        "exit_artifacts": [".allforai/game-2d/spec/session-flow-contract.json"],
    },
    {
        "node_id": "game-2d-playable-slice-assembly",
        "skill": "game-2d-production/30-generate/playable-slice-assembly",
        "goal": "把 2D 设计、美术、UI、音频和前端契约总装为可运行切片",
        "exit_artifacts": [
            ".allforai/game-2d/assembly/playable-slice-manifest.json",
            ".allforai/game-2d/assembly/playable-slice-assembly-report.json",
        ],
    },
    {
        "node_id": "game-2d-core-loop-playability-qa",
        "skill": "game-2d-production/40-qa/core-loop-playability-qa",
        "goal": "使用运行时输入、状态断言和截图验证 2D 核心循环可玩",
        "exit_artifacts": [".allforai/game-2d/qa/core-loop-playability-qa-report.json"],
    },
    {
        "node_id": "game-2d-asset-binding-visual-qa",
        "skill": "game-2d-production/40-qa/asset-binding-visual-qa",
        "goal": "使用运行时截图和 Codex CLI 验证 2D 资产真实绑定且可读",
        "exit_artifacts": [".allforai/game-2d/qa/asset-binding-visual-qa-report.json"],
    },
    {
        "node_id": "game-2d-session-completion-qa",
        "skill": "game-2d-production/40-qa/session-completion-qa",
        "goal": "自动验证 2D 游戏 session 可以启动、进入玩法、完成、重试或继续",
        "exit_artifacts": [".allforai/game-2d/qa/session-completion-qa-report.json"],
    },
    {
        "node_id": "game-2d-code-repair-loop",
        "skill": "game-2d-production/40-qa/code-repair-loop",
        "goal": "修复 2D QA 发现的代码缺口并重跑受影响验收",
        "exit_artifacts": [
            ".allforai/game-2d/repair/code-repair-loop-report.json",
            ".allforai/game-2d/repair/code-repair-loop-report.md",
            ".allforai/game-2d/qa/revalidation-report.json",
        ],
    },
    {
        "node_id": "game-2d-production-closure-qa",
        "skill": "game-2d-production/40-qa/2d-production-closure-qa",
        "goal": "执行 2D 游戏最终出厂闭环验收",
        "exit_artifacts": sorted(GAME_2D_PRODUCTION_REQUIRED_ARTIFACTS),
    },
]


def _load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _artifact_paths(items) -> list[str]:
    paths = []
    for item in items or []:
        if isinstance(item, dict):
            paths.append(item.get("path", ""))
        else:
            paths.append(str(item))
    return paths


def _find_frontend_assembly_node(nodes: list[dict]) -> str | None:
    for node in nodes:
        node_id = node.get("node_id")
        if not node_id:
            continue
        blob = " ".join(_artifact_paths(node.get("exit_artifacts"))).lower()
        if "playable-client-assembly-report.json" in blob:
            return node_id
        if "game-frontend" in node_id and "assembly" in node_id:
            return node_id
    return None


def _node_for(defn: dict, blockers: list[str]) -> dict:
    return {
        "node_id": defn["node_id"],
        "goal": defn["goal"],
        "capability": "game-2d-production",
        "human_gate": False,
        "discipline_owner": "gameplay-frontend-engineer",
        "hard_blocked_by": blockers,
        "alignment_refs": [],
        "exit_artifacts": defn["exit_artifacts"],
    }


def _yaml_list(values: list[str]) -> str:
    if not values:
        return " []"
    return "\n" + "\n".join(f"  - {json.dumps(value, ensure_ascii=False)}" for value in values)


def _spec_for(defn: dict, node: dict) -> str:
    node_id = defn["node_id"]
    skill = defn["skill"]
    exit_artifacts = node["exit_artifacts"]
    blockers = node.get("hard_blocked_by") or []
    alignment_refs = node.get("alignment_refs") or []
    return f"""---
node: {node_id}
goal: {json.dumps(node["goal"], ensure_ascii=False)}
capability: game-2d-production
human_gate: false
discipline_owner: gameplay-frontend-engineer
hard_blocked_by:{_yaml_list(blockers)}
alignment_refs:{_yaml_list(alignment_refs)}
exit_artifacts:{_yaml_list(exit_artifacts)}
---

# {node_id}

## Mission

执行 2D 游戏生产闭环节点。读取并严格遵循：

`${{CLAUDE_PLUGIN_ROOT}}/skills/{skill}/SKILL.md`

## Inputs

- `.allforai/game-design/game-design-doc.json`
- `.allforai/game-design/design/program-development-node-handoff.json`
- `.allforai/game-runtime/art/engine-ready-art-manifest.json`
- `.allforai/game-frontend/assembly/playable-client-assembly-report.json`
- `.allforai/game-frontend/qa/runtime-gameplay-visual-acceptance-report.json`
- 上游 `game-2d-production` 节点已经生成的 `.allforai/game-2d/` 契约和报告

## Required Behavior

- 使用目标项目真实运行时；如果无法运行，输出阻塞状态，不使用替代验收。
- 需要视觉判断时，使用运行时截图和 Codex CLI 视觉验收文档。
- 不允许只凭 JSON、日志、源码阅读或静态截图通过可玩性验收。
- 输出必须写到 frontmatter 中声明的 `exit_artifacts`。

## Outputs

{chr(10).join(f"- `{path}`" for path in exit_artifacts)}
"""


def expand_game_2d_production(project_root: Path, *, dry_run: bool = False) -> dict:
    project_root = project_root.resolve()
    bootstrap_dir = project_root / ".allforai/bootstrap"
    workflow_path = bootstrap_dir / "workflow.json"
    specs_dir = bootstrap_dir / "node-specs"

    if not workflow_path.exists():
        return {"status": "blocked", "reason": "missing_workflow", "changed": False}
    if not _game_2d_handoff_required(str(project_root)):
        return {"status": "skipped", "reason": "game_2d_production_not_required", "changed": False}

    workflow = _load_json(workflow_path)
    nodes = workflow.setdefault("nodes", [])
    if not isinstance(nodes, list):
        return {"status": "blocked", "reason": "workflow_nodes_not_list", "changed": False}

    by_node_id = {node.get("node_id"): node for node in nodes if node.get("node_id")}
    frontend_assembly = _find_frontend_assembly_node(nodes)
    changed = False
    previous: str | None = None
    generated: list[str] = []
    updated: list[str] = []

    for defn in NODE_DEFS:
        node_id = defn["node_id"]
        blockers = [previous] if previous else []
        if node_id == "game-2d-playable-slice-assembly" and frontend_assembly:
            blockers = sorted(set(blockers + [frontend_assembly]))
        if node_id == "game-2d-code-repair-loop":
            blockers = [
                "game-2d-core-loop-playability-qa",
                "game-2d-asset-binding-visual-qa",
                "game-2d-session-completion-qa",
            ]
        if node_id == "game-2d-production-closure-qa":
            blockers = ["game-2d-code-repair-loop"]
        blockers = [item for item in blockers if item]

        node = _node_for(defn, blockers)
        existing = by_node_id.get(node_id)
        if existing is None:
            nodes.append(node)
            by_node_id[node_id] = node
            generated.append(node_id)
            changed = True
        else:
            for key in (
                "goal",
                "capability",
                "human_gate",
                "discipline_owner",
                "hard_blocked_by",
                "alignment_refs",
                "exit_artifacts",
            ):
                if existing.get(key) != node[key]:
                    existing[key] = node[key]
                    changed = True
                    if node_id not in updated:
                        updated.append(node_id)

        spec_text = _spec_for(defn, by_node_id[node_id])
        spec_path = specs_dir / f"{node_id}.md"
        if not spec_path.exists() or spec_path.read_text(encoding="utf-8") != spec_text:
            if not dry_run:
                spec_path.parent.mkdir(parents=True, exist_ok=True)
                spec_path.write_text(spec_text, encoding="utf-8")
            changed = True
            if node_id not in generated and node_id not in updated:
                updated.append(node_id)
        previous = node_id

    if changed and not dry_run:
        _write_json(workflow_path, workflow)

    return {
        "status": "expanded",
        "changed": changed,
        "generated_nodes": generated,
        "updated_nodes": updated,
        "required_nodes": GAME_2D_PRODUCTION_REQUIRED_NODES,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_root", nargs="?", default=".")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    result = expand_game_2d_production(Path(args.project_root), dry_run=args.dry_run)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] in {"expanded", "skipped"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
