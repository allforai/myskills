#!/usr/bin/env python3
"""Unified pre-verification for all review phases.

Two modes:
  STRUCTURAL (concept, map): Direct JSON validation — no browser needed.
    Script reads JSON → checks completeness/consistency → outputs report.
    Claude Code fixes issues based on report → re-runs script.

  VISUAL (wireframe, ui): Playwright required — needs browser rendering.
    Script prepares metadata → Claude Code uses Playwright to verify.

Usage:
  python3 verify_review.py <BASE> --phase concept|map|wireframe|ui
  python3 verify_review.py <BASE> --phase wireframe|ui --report  # visual only

Output:
  .allforai/<phase>-verify/verification-report.json
"""

import json
import os
import sys
import subprocess
import time
import urllib.request
import urllib.error

sys.path.insert(0, os.path.dirname(__file__))
from _common import (
    resolve_base_path, ensure_dir, write_json, now_iso,
    append_pipeline_decision, load_json,
    load_experience_map, load_product_concept,
    load_task_inventory, load_business_flows,
    kill_other_review_servers
)


# ── STRUCTURAL VERIFICATION (no Playwright) ───────────────────────────────────

def verify_concept(base):
    """Verify product concept JSON completeness. Returns findings list."""
    concept = load_product_concept(base)
    if not concept:
        return [{"node_id": "concept", "severity": "ERROR", "issue": "product-concept.json not found"}]

    findings = []

    # Mission
    mission = concept.get("mission", "")
    if not mission:
        findings.append({"node_id": "mission", "severity": "ERROR",
                        "issue": "mission 为空", "fix": "添加产品使命描述"})
    else:
        findings.append({"node_id": "mission", "severity": "PASS",
                        "issue": f"mission: {mission[:60]}..."})

    # Roles
    roles = concept.get("roles", [])
    if not roles:
        findings.append({"node_id": "roles", "severity": "ERROR",
                        "issue": "roles 为空", "fix": "至少定义 1 个角色"})
    for i, role in enumerate(roles):
        name = role.get("name", f"Role{i}")
        problems = []
        if not role.get("jobs"):
            problems.append("jobs 为空")
        if not role.get("pain_relievers"):
            problems.append("pain_relievers 为空")
        if not role.get("gain_creators"):
            problems.append("gain_creators 为空")
        if problems:
            findings.append({"node_id": f"role_{name}", "severity": "WARNING",
                            "issue": f"角色 {name}: {', '.join(problems)}"})
        else:
            findings.append({"node_id": f"role_{name}", "severity": "PASS",
                            "issue": f"角色 {name}: jobs={len(role['jobs'])}, "
                                    f"pain={len(role['pain_relievers'])}, "
                                    f"gain={len(role['gain_creators'])}"})

    # Business Model
    bm = concept.get("business_model", {})
    metrics = bm.get("metrics", [])
    if len(metrics) < 3:
        findings.append({"node_id": "business_model", "severity": "WARNING",
                        "issue": f"metrics 只有 {len(metrics)} 个（建议 ≥3）"})
    else:
        incomplete = [m for m in metrics if not all(m.get(k) for k in ("metric", "type", "target"))]
        if incomplete:
            findings.append({"node_id": "business_model", "severity": "WARNING",
                            "issue": f"{len(incomplete)} 个 metric 缺少 metric/type/target 字段"})
        else:
            findings.append({"node_id": "business_model", "severity": "PASS",
                            "issue": f"{len(metrics)} metrics, all complete"})

    # Mechanisms
    mechs = concept.get("mechanisms", [])
    if len(mechs) < 5:
        findings.append({"node_id": "mechanisms", "severity": "WARNING",
                        "issue": f"mechanisms 只有 {len(mechs)} 个（通常 ≥5）"})
    else:
        findings.append({"node_id": "mechanisms", "severity": "PASS",
                        "issue": f"{len(mechs)} mechanisms"})

    # Pipeline Preferences
    prefs = concept.get("pipeline_preferences", {})
    if not prefs.get("ui_style") or not prefs.get("scope_strategy"):
        findings.append({"node_id": "pipeline_preferences", "severity": "WARNING",
                        "issue": "pipeline_preferences 缺少 ui_style 或 scope_strategy"})
    else:
        findings.append({"node_id": "pipeline_preferences", "severity": "PASS",
                        "issue": f"ui_style={prefs['ui_style']}, scope={prefs['scope_strategy']}"})

    return findings


def verify_map(base):
    """Verify product map JSON completeness. Returns findings list."""
    task_dict = load_task_inventory(base)
    tasks = list(task_dict.values()) if isinstance(task_dict, dict) else (task_dict or [])
    flows = load_business_flows(base)

    if not tasks:
        return [{"node_id": "tasks", "severity": "ERROR", "issue": "task-inventory.json not found or empty"}]

    findings = []

    # Role coverage
    roles = {}
    for t in tasks:
        role = t.get("owner_role", t.get("role_id", "unknown"))
        cat = t.get("category", "core")
        roles.setdefault(role, {"core": 0, "basic": 0})
        roles[role][cat] = roles[role].get(cat, 0) + 1

    for role, counts in roles.items():
        if counts["core"] == 0:
            findings.append({"node_id": f"role_{role}", "severity": "ERROR",
                            "issue": f"角色 {role} 没有 core task（只有 {counts['basic']} basic）",
                            "fix": f"将角色 {role} 的关键任务标记为 core"})
        else:
            findings.append({"node_id": f"role_{role}", "severity": "PASS",
                            "issue": f"角色 {role}: core={counts['core']}, basic={counts['basic']}"})

    # Task count
    core_tasks = [t for t in tasks if t.get("category") == "core"]
    basic_tasks = [t for t in tasks if t.get("category") == "basic"]
    findings.append({"node_id": "task_summary", "severity": "PASS",
                    "issue": f"total={len(tasks)}, core={len(core_tasks)}, basic={len(basic_tasks)}"})

    # Frequency/risk labels
    no_freq = [t for t in tasks if not t.get("frequency")]
    no_risk = [t for t in tasks if not t.get("risk_level")]
    if no_freq:
        findings.append({"node_id": "frequency", "severity": "WARNING",
                        "issue": f"{len(no_freq)} tasks 缺少频次标签: {', '.join(t['id'] for t in no_freq[:5])}"})
    if no_risk:
        findings.append({"node_id": "risk", "severity": "WARNING",
                        "issue": f"{len(no_risk)} tasks 缺少风险标签: {', '.join(t['id'] for t in no_risk[:5])}"})

    # Business flow coverage
    flow_list = flows if isinstance(flows, list) else (flows.get("flows", []) if flows else [])
    if not flow_list:
        findings.append({"node_id": "flows", "severity": "WARNING",
                        "issue": "business-flows.json not found or empty"})
    else:
        flow_task_ids = set()
        for flow in flow_list:
            nodes = flow.get("nodes", flow.get("steps", []))
            if len(nodes) < 2:
                findings.append({"node_id": f"flow_{flow.get('name', '?')}", "severity": "WARNING",
                                "issue": f"业务流 {flow.get('name', '?')} 只有 {len(nodes)} 步（太短）"})
            for node in nodes:
                tid = node.get("task_id", node.get("ref", ""))
                if tid:
                    flow_task_ids.add(tid)

        uncovered = [t["id"] for t in core_tasks if t["id"] not in flow_task_ids]
        if uncovered:
            findings.append({"node_id": "flow_coverage", "severity": "WARNING",
                            "issue": f"{len(uncovered)} core tasks 不在任何业务流中: {', '.join(uncovered[:8])}",
                            "fix": "将这些任务加入相关业务流"})
        else:
            findings.append({"node_id": "flow_coverage", "severity": "PASS",
                            "issue": f"所有 {len(core_tasks)} 个 core tasks 都有业务流覆盖"})

        findings.append({"node_id": "flows_summary", "severity": "PASS",
                        "issue": f"{len(flow_list)} business flows"})

    return findings


# ── VISUAL VERIFICATION (needs Playwright) ────────────────────────────────────

def prepare_wireframe(base):
    """Prepare wireframe items for Playwright verification."""
    lines, index, loaded = load_experience_map(base)
    if not loaded:
        return []

    items = []
    seen = set()
    for ol in lines:
        for node in ol.get("nodes", []):
            for s in node.get("screens", []):
                sid = s.get("id", "")
                if sid and sid not in seen:
                    seen.add(sid)
                    items.append({
                        "node_id": sid,
                        "label": f"{sid}: {s.get('name', '')}",
                        "interaction_type": s.get("interaction_type", "?"),
                        "field_count": len(s.get("data_fields", [])),
                        "action_count": len(s.get("actions", [])),
                        "platform": s.get("platform", "mobile"),
                    })
    items.sort(key=lambda x: x["node_id"])
    return items


def prepare_ui(base):
    """Prepare UI items for Playwright verification."""
    items = prepare_wireframe(base)
    for item in items:
        item["check_focus"] = "visual_consistency"
    return items


VISUAL_PREPARERS = {
    "wireframe": prepare_wireframe,
    "ui": prepare_ui,
}

VISUAL_CHECK_CRITERIA = {
    "wireframe": [
        "交互类型 vs 布局 slots 是否匹配",
        "data_fields 中的字段名是否渲染",
        "actions 中的按钮是否存在",
        "中文产品无英文 UI 文本泄露",
        "Flow 面板 ← → 指向正确上下游",
        "State 面板有状态机定义",
    ],
    "ui": [
        "HTML 预览正常加载（不为空白）",
        "颜色/字体/间距各屏幕间统一",
        "相同类型屏幕使用相同组件模式",
        "desktop 和 mobile 布局合理",
        "所有 UI 文本为中文",
    ],
}

HUB_PATHS = {
    "wireframe": "/wireframe",
    "ui": "/ui",
}


def ensure_hub_running(base, port=18900):
    """Start Review Hub if not already running."""
    try:
        urllib.request.urlopen(f"http://localhost:{port}/", timeout=2)
        return True
    except (urllib.error.URLError, OSError):
        pass

    script_dir = os.path.dirname(__file__)
    hub_script = os.path.join(script_dir, "review_hub_server.py")
    if not os.path.exists(hub_script):
        return False

    kill_other_review_servers(port)
    subprocess.Popen(
        [sys.executable, hub_script, base, "--port", str(port), "--no-open", "true"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )

    for _ in range(10):
        time.sleep(1)
        try:
            urllib.request.urlopen(f"http://localhost:{port}/", timeout=2)
            return True
        except (urllib.error.URLError, OSError):
            continue
    return False


# ── REPORT GENERATION ─────────────────────────────────────────────────────────

def generate_report(base, phase, findings, input_file=None):
    """Generate verification report."""
    if input_file:
        with open(input_file) as f:
            findings = json.load(f)

    errors = [r for r in findings if r.get("severity") == "ERROR"]
    warnings = [r for r in findings if r.get("severity") == "WARNING"]
    passed = [r for r in findings if r.get("severity") == "PASS"]

    report = {
        "phase": phase,
        "generated_at": now_iso(),
        "total_items": len(findings),
        "passed": len(passed),
        "warnings": len(warnings),
        "errors": len(errors),
        "overall": "PASS" if not errors else "FAIL",
        "findings": findings,
    }

    out_dir = os.path.join(base, f"{phase}-verify")
    ensure_dir(out_dir)
    write_json(os.path.join(out_dir, "verification-report.json"), report)

    phase_labels = {
        "concept": "Phase 1.4 — concept-pre-verify",
        "map": "Phase 2.4 — map-pre-verify",
        "wireframe": "Phase 4.7 — wireframe-verify",
        "ui": "Phase 8.5 — ui-pre-verify",
    }

    append_pipeline_decision(
        base,
        phase_labels.get(phase, f"{phase}-verify"),
        f"items={len(findings)}, pass={len(passed)}, warn={len(warnings)}, error={len(errors)}",
        decision="auto_verified" if not errors else "errors_found",
    )

    # Output summary
    title = {"concept": "概念预审", "map": "地图预审", "wireframe": "线框预审", "ui": "UI预审"}
    print(f"\n{title.get(phase, phase)}: {len(passed)} PASS, {len(warnings)} WARNING, {len(errors)} ERROR")
    if errors:
        print("\nERRORS:")
        for e in errors:
            print(f"  {e.get('node_id', '?')}: {e.get('issue', '')}")
    if warnings:
        print("\nWARNINGS:")
        for w in warnings:
            print(f"  {w.get('node_id', '?')}: {w.get('issue', '')}")

    return report


# ── MAIN ──────────────────────────────────────────────────────────────────────

STRUCTURAL_PHASES = {"concept": verify_concept, "map": verify_map}
VISUAL_PHASES = {"wireframe", "ui"}


def main():
    base = resolve_base_path()
    args = sys.argv[1:]
    remaining = [a for a in args if not os.path.isdir(a)]

    # Parse --phase
    phase = None
    if "--phase" in remaining:
        idx = remaining.index("--phase")
        if idx + 1 < len(remaining):
            phase = remaining[idx + 1]

    all_phases = set(STRUCTURAL_PHASES.keys()) | VISUAL_PHASES
    if not phase or phase not in all_phases:
        print(f"Usage: {sys.argv[0]} <BASE> --phase {{'|'.join(sorted(all_phases))}}")
        sys.exit(1)

    # ── STRUCTURAL: self-contained verification ──
    if phase in STRUCTURAL_PHASES:
        verifier = STRUCTURAL_PHASES[phase]
        findings = verifier(base)
        report = generate_report(base, phase, findings)
        sys.exit(0 if report["overall"] == "PASS" else 1)

    # ── VISUAL: prepare for Playwright or generate report ──
    if "--report" in remaining:
        input_file = None
        if "--input" in remaining:
            idx = remaining.index("--input")
            if idx + 1 < len(remaining):
                input_file = remaining[idx + 1]
        else:
            input_file = os.path.join(base, f"{phase}-verify", "verification-input.json")
        report = generate_report(base, phase, [], input_file)
        sys.exit(0 if report["overall"] == "PASS" else 1)

    # Prepare mode
    preparer = VISUAL_PREPARERS[phase]
    items = preparer(base)
    if not items:
        print(f"WARNING: No items for {phase} verification", file=sys.stderr)
        sys.exit(0)

    port = 18900
    hub_ok = ensure_hub_running(base, port)
    hub_path = HUB_PATHS[phase]

    out_dir = os.path.join(base, f"{phase}-verify")
    ensure_dir(out_dir)

    output = {
        "phase": phase,
        "generated_at": now_iso(),
        "hub_url": f"http://localhost:{port}{hub_path}" if hub_ok else None,
        "item_count": len(items),
        "items": items,
        "check_criteria": VISUAL_CHECK_CRITERIA[phase],
    }

    out_file = os.path.join(out_dir, "to-verify.json")
    write_json(out_file, output)

    print(f"{phase} pre-verify: {len(items)} items")
    print(f"Hub: {'running at ' + output['hub_url'] if hub_ok else 'FAILED'}")
    print(f"\nClaude Code: Playwright → snapshot each → judge → write {phase}-verify/verification-input.json → --report")


if __name__ == "__main__":
    main()
