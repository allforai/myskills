#!/usr/bin/env python3
"""Generate feature-gap analysis: task-gaps, screen-gaps, journey-gaps,
flow-gaps, gap-tasks, gap-report, and decisions.

Pre-built script for Phase 5 (feature-gap). Fixes:
- Defensive checks for is_primary/on_failure field absence
- Uses _common.get_screen_tasks() instead of hardcoded field names
- Uses _common.get_flow_nodes() (nodes, not steps)
- Pipeline-decisions dedup via _common.append_pipeline_decision()

Usage:
    python3 gen_feature_gap.py <BASE_PATH> [--mode auto]
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C

# ── Setup ─────────────────────────────────────────────────────────────────────
BASE, args = C.parse_args()
OUT = os.path.join(BASE, "feature-gap")
C.ensure_dir(OUT)
NOW = C.now_iso()

# ── Load data ─────────────────────────────────────────────────────────────────
tasks = C.load_task_inventory(BASE)
tidx = C.load_task_index(BASE)
role_map = C.load_role_profiles(BASE)

screens, _ = C.load_screen_map(BASE)
screens_by_id = C.build_screen_by_id(screens)

flows = C.load_business_flows(BASE)
flow_idx = C.load_flow_index(BASE)

# ── Step 1: Task completeness check ──────────────────────────────────────────
task_gaps = []
for tid, task in tasks.items():
    gaps = []
    details = {
        "crud_missing": [],
        "exceptions_count": len(task.get("exceptions", [])),
        "acceptance_criteria_count": len(task.get("acceptance_criteria", [])),
        "rules_count": len(task.get("rules", [])),
        "high_freq_buried": False
    }

    if not task.get("exceptions"):
        gaps.append("NO_EXCEPTIONS")

    if not task.get("rules"):
        gaps.append("NO_RULES")

    if not task.get("acceptance_criteria"):
        gaps.append("NO_ACCEPTANCE_CRITERIA")

    # CRUD completeness for management tasks
    tname = task.get("task_name", "")
    main_flow = task.get("main_flow", [])
    if "管理" in tname or "创建" in tname:
        crud_ops = {"创建": False, "查看": False, "编辑": False, "删除": False}
        for step in main_flow:
            for op in crud_ops:
                if op in step:
                    crud_ops[op] = True
            if any(w in step for w in ["新增", "添加", "新建"]):
                crud_ops["创建"] = True
            if any(w in step for w in ["浏览", "查询", "列表", "查看"]):
                crud_ops["查看"] = True
            if any(w in step for w in ["修改", "更新", "调整", "编辑"]):
                crud_ops["编辑"] = True
            if any(w in step for w in ["移除", "下架", "删除"]):
                crud_ops["删除"] = True
        missing = [k for k, v in crud_ops.items() if not v]
        if missing:
            gaps.append("CRUD_INCOMPLETE")
            details["crud_missing"] = missing

    # High frequency buried check
    if task.get("frequency") == "高":
        prereqs = task.get("prerequisites", [])
        if len(prereqs) > 3:
            gaps.append("HIGH_FREQ_BURIED")
            details["high_freq_buried"] = True

    task_gaps.append({
        "task_id": tid,
        "task_name": task["task_name"],
        "frequency": task.get("frequency", "低"),
        "category": task.get("category", ""),
        "gaps": gaps if gaps else ["COMPLETE"],
        "details": details
    })

C.write_json(os.path.join(OUT, "task-gaps.json"), task_gaps)

# ── Step 2: Screen & button completeness check ──────────────────────────────
screen_gaps = []
task_screen_map = {}  # task_id -> list of screen_ids
for s in screens:
    trefs = C.get_screen_tasks(s)
    for tid in trefs:
        task_screen_map.setdefault(tid, []).append(s["id"])

# Check tasks without screens
for tid in tasks:
    if tid not in task_screen_map:
        screen_gaps.append({
            "screen_id": "N/A",
            "screen_name": f"(任务 {tid} 无对应界面)",
            "gaps": ["NO_SCREEN"],
            "details": [{
                "flag": "NO_SCREEN",
                "description": f"任务 {tid} ({tasks[tid]['task_name']}) 在 screen-map 中无对应界面",
                "affected_tasks": [tid],
                "severity": "高" if tasks[tid].get("frequency") == "高" else "中"
            }]
        })

for s in screens:
    gaps = []
    details_list = []
    actions = s.get("actions", [])
    trefs = C.get_screen_tasks(s)

    # Check primary action exists (defensive: is_primary may not exist)
    has_primary = any(a.get("is_primary", False) for a in actions)
    if not has_primary and actions:
        gaps.append("NO_PRIMARY")
        details_list.append({
            "flag": "NO_PRIMARY",
            "description": f"界面 {s['id']} ({s.get('name', '')}) 无主操作按钮",
            "affected_tasks": trefs,
            "severity": "中"
        })

    # Check high-risk tasks have confirmation
    for tid in trefs:
        task = tasks.get(tid, {})
        if task.get("risk_level") == "高":
            has_confirm = any(a.get("requires_confirm", False) for a in actions)
            if not has_confirm:
                gaps.append("HIGH_RISK_NO_CONFIRM")
                details_list.append({
                    "flag": "HIGH_RISK_NO_CONFIRM",
                    "description": f"高风险任务 {tid} ({task.get('task_name', '')}) 对应操作缺少二次确认",
                    "affected_tasks": [tid],
                    "severity": "高"
                })

    # Check orphan screens
    if not trefs:
        gaps.append("ORPHAN_SCREEN")
        details_list.append({
            "flag": "ORPHAN_SCREEN",
            "description": f"界面 {s['id']} ({s.get('name', '')}) 无关联任务",
            "affected_tasks": [],
            "severity": "低"
        })

    # Check SILENT_FAILURE for CUD actions (defensive: on_failure may not exist)
    for a in actions:
        crud = a.get("crud", "")
        if crud in ("C", "U", "D") or any(
            kw in a.get("label", "") for kw in ["提交", "删除", "保存", "创建", "修改", "发布"]
        ):
            if not a.get("on_failure", ""):
                gaps.append("SILENT_FAILURE")
                details_list.append({
                    "flag": "SILENT_FAILURE",
                    "description": f"操作 '{a.get('label', '')}' 无失败反馈定义",
                    "affected_tasks": trefs,
                    "severity": "高"
                })

    if gaps:
        seen = set()
        unique_gaps = []
        for g in gaps:
            if g not in seen:
                seen.add(g)
                unique_gaps.append(g)
        screen_gaps.append({
            "screen_id": s["id"],
            "screen_name": s.get("name", ""),
            "gaps": unique_gaps,
            "details": details_list
        })

C.write_json(os.path.join(OUT, "screen-gaps.json"), screen_gaps)

# ── Step 3: User journey validation ──────────────────────────────────────────
journey_gaps = []
for tid, task in tasks.items():
    rid = task.get("owner_role", "")
    rname = role_map.get(rid, rid)
    score = 4
    breakpoints = []

    # Node 1: Entry exists?
    has_screen = tid in task_screen_map
    if not has_screen:
        score -= 1
        breakpoints.append({
            "node": "入口存在",
            "issue": f"任务 {tid} 无对应界面",
            "affected_screen": "N/A"
        })

    # Node 2: Primary action reachable? (defensive: is_primary may be absent)
    if has_screen:
        sids = task_screen_map[tid]
        primary_found = False
        for sid in sids:
            s = screens_by_id.get(sid, {})
            if any(a.get("is_primary", False) for a in s.get("actions", [])):
                primary_found = True
                break
        if not primary_found:
            score -= 1
            breakpoints.append({
                "node": "主操作可触达",
                "issue": "界面无 is_primary 标记的操作",
                "affected_screen": sids[0] if sids else "N/A"
            })

    # Node 3: Feedback exists? (defensive: on_failure/on_success may be absent)
    if has_screen:
        sids = task_screen_map[tid]
        has_feedback = False
        for sid in sids:
            s = screens_by_id.get(sid, {})
            for a in s.get("actions", []):
                if a.get("on_failure", "") or a.get("on_success", ""):
                    has_feedback = True
                    break
        if not has_feedback:
            score -= 1
            breakpoints.append({
                "node": "操作有反馈",
                "issue": "无 on_failure/on_success 反馈定义",
                "affected_screen": sids[0] if sids else "N/A"
            })

    # Node 4: Result visible?
    if not task.get("outputs") and not task.get("main_flow"):
        score -= 1
        breakpoints.append({
            "node": "结果可见",
            "issue": "任务无 outputs 定义",
            "affected_screen": "N/A"
        })

    if breakpoints:
        journey_gaps.append({
            "role": rname,
            "task_id": tid,
            "task_name": task["task_name"],
            "score": f"{score}/4",
            "breakpoints": breakpoints
        })

C.write_json(os.path.join(OUT, "journey-gaps.json"), journey_gaps)

# ── Step 5: Business flow link completeness (uses 'nodes' not 'steps') ───────
flow_gaps = []
flow_task_refs = C.collect_flow_task_refs(flows)

orphan_tasks = [tid for tid in tasks if tid not in flow_task_refs]
if orphan_tasks:
    flow_gaps.append({
        "flow_id": "GLOBAL",
        "flow_name": "全局孤立任务检查",
        "gap_type": "ORPHAN_TASK",
        "description": f"{len(orphan_tasks)} 个任务未被任何业务流引用",
        "affected_tasks": orphan_tasks,
        "severity": "低"
    })

for flow in flows:
    if flow.get("gap_count", 0) > 0:
        flow_gaps.append({
            "flow_id": flow["id"],
            "flow_name": flow.get("name", ""),
            "gap_type": "FLOW_GAP",
            "description": f"业务流 {flow['id']} 含 {flow['gap_count']} 个缺口",
            "affected_tasks": [
                n.get("task_ref", "") if isinstance(n, dict) else n
                for n in C.get_flow_nodes(flow)
            ],
            "severity": "高"
        })

C.write_json(os.path.join(OUT, "flow-gaps.json"), flow_gaps)

# ── Step 6: State machine completeness check ─────────────────────────────────
# Load state-graph.json (generated by Claude runtime during interactive mode)
state_graph_path = os.path.join(OUT, "state-graph.json")
state_graph = C.load_json(state_graph_path) if os.path.exists(state_graph_path) else None

state_gaps = []

if not state_graph:
    print("WARNING: state-graph.json not found — Step 6 (状态机完整性检查) skipped.")
    print("  In auto mode, state-graph.json must be generated by a prior interactive run.")
    print("  Run /feature-gap full interactively first to generate the state graph.")

if state_graph and "entities" in state_graph:
    from collections import deque

    for entity_name, entity in state_graph["entities"].items():
        states = entity.get("states", [])
        transitions = entity.get("transitions", [])
        initial = entity.get("initial_state", "")
        terminals = set(entity.get("terminal_states", []))
        source_tasks = entity.get("source_tasks", [])

        gaps_found = []
        details = {
            "dead_ends": [],
            "unreachable": [],
            "missing_reverse": [],
            "no_error_recovery": [],
            "orphan": False
        }

        # ORPHAN_ENTITY: only 1 state, insufficient modeling
        if len(states) <= 1:
            gaps_found.append("ORPHAN_ENTITY")
            details["orphan"] = True
        else:
            # Build adjacency list
            adj = {s: set() for s in states}
            reverse_adj = {s: set() for s in states}
            for t in transitions:
                f, to = t.get("from", ""), t.get("to", "")
                if f in adj and to in adj:
                    adj[f].add(to)
                    reverse_adj[to].add(f)

            # UNREACHABLE_STATE: BFS from initial_state
            if initial and initial in adj:
                visited = set()
                queue = deque([initial])
                visited.add(initial)
                while queue:
                    cur = queue.popleft()
                    for nxt in adj.get(cur, []):
                        if nxt not in visited:
                            visited.add(nxt)
                            queue.append(nxt)
                unreachable = [s for s in states if s not in visited]
                if unreachable:
                    gaps_found.append("UNREACHABLE_STATE")
                    details["unreachable"] = unreachable

            # DEAD_END_STATE: non-terminal states with no outgoing edges
            for s in states:
                if s not in terminals and not adj.get(s, set()):
                    gaps_found.append("DEAD_END_STATE")
                    details["dead_ends"].append(s)

            # NO_REVERSE_TRANSITION: A→B exists but no path B→A
            # (only check when A is not initial and B is not terminal)
            for t in transitions:
                f, to = t.get("from", ""), t.get("to", "")
                if f == initial or to in terminals:
                    continue
                # BFS from 'to' to see if 'f' is reachable
                if to in adj and f in adj:
                    rev_visited = set()
                    rev_queue = deque([to])
                    rev_visited.add(to)
                    found_reverse = False
                    while rev_queue:
                        cur = rev_queue.popleft()
                        for nxt in adj.get(cur, []):
                            if nxt == f:
                                found_reverse = True
                                break
                            if nxt not in rev_visited:
                                rev_visited.add(nxt)
                                rev_queue.append(nxt)
                        if found_reverse:
                            break
                    if not found_reverse:
                        pair = {"from": f, "to": to}
                        if pair not in details["missing_reverse"]:
                            details["missing_reverse"].append(pair)
            if details["missing_reverse"] and "NO_REVERSE_TRANSITION" not in gaps_found:
                gaps_found.append("NO_REVERSE_TRANSITION")

            # NO_ERROR_RECOVERY: error states (from exceptions) with no outgoing edges
            # to non-error states — heuristic: states containing error keywords
            error_keywords = ["失败", "错误", "异常", "拒绝", "超时", "取消", "驳回", "中止"]
            error_states = [s for s in states if any(kw in s for kw in error_keywords)]
            for es in error_states:
                normal_targets = [nxt for nxt in adj.get(es, set())
                                  if not any(kw in nxt for kw in error_keywords)]
                if not normal_targets:
                    gaps_found.append("NO_ERROR_RECOVERY")
                    details["no_error_recovery"].append(es)

        # Deduplicate gap flags
        seen_flags = set()
        unique_gaps = []
        for g in gaps_found:
            if g not in seen_flags:
                seen_flags.add(g)
                unique_gaps.append(g)

        # Determine severity: highest among all gaps
        severity_map = {
            "UNREACHABLE_STATE": "高", "DEAD_END_STATE": "高",
            "NO_ERROR_RECOVERY": "高", "NO_REVERSE_TRANSITION": "中",
            "ORPHAN_ENTITY": "低"
        }
        severity_order = {"高": 0, "中": 1, "低": 2}
        severity = "低"
        for g in unique_gaps:
            gs = severity_map.get(g, "低")
            if severity_order.get(gs, 2) < severity_order.get(severity, 2):
                severity = gs

        if unique_gaps:
            state_gaps.append({
                "entity": entity_name,
                "gaps": unique_gaps,
                "state_count": len(states),
                "transition_count": len(transitions),
                "affected_tasks": source_tasks,
                "details": details,
                "severity": severity
            })

C.write_json(os.path.join(OUT, "state-gaps.json"), state_gaps)

# ── Step 4: Generate gap task list (prioritized) ─────────────────────────────
gap_counter = [0]
def next_gap():
    gap_counter[0] += 1
    return f"GAP-{gap_counter[0]:03d}"

gap_tasks_list = []

def priority_rank(freq, flag):
    freq_rank = {"高": 0, "中": 1, "低": 2}.get(freq, 2)
    flag_rank = {
        "SILENT_FAILURE": 0, "UNHANDLED_EXCEPTION": 0,
        "DEAD_END_STATE": 0, "NO_ERROR_RECOVERY": 0,
        "HIGH_RISK_NO_CONFIRM": 1,
        "NO_SCREEN": 1,
        "CRUD_INCOMPLETE": 2, "NO_EXCEPTIONS": 2, "NO_ACCEPTANCE_CRITERIA": 2,
        "UNREACHABLE_STATE": 2,
        "NO_PRIMARY": 3, "NO_REVERSE_TRANSITION": 3,
        "ORPHAN_SCREEN": 4, "ORPHAN_ENTITY": 4,
        "NO_RULES": 3,
        "HIGH_FREQ_BURIED": 2,
    }.get(flag, 5)
    return freq_rank * 10 + flag_rank

# From task gaps
for tg in task_gaps:
    if "COMPLETE" in tg["gaps"]:
        continue
    for gap in tg["gaps"]:
        tid = tg["task_id"]
        task = tasks[tid]
        freq = tg["frequency"]
        cat = task.get("category", "")
        prio = "高" if freq == "高" or gap in ("SILENT_FAILURE", "HIGH_RISK_NO_CONFIRM") else ("中" if freq == "中" or cat == "core" else "低")
        gap_tasks_list.append({
            "id": next_gap(),
            "title": f"{task['task_name']} — {gap}",
            "type": gap,
            "category": cat,
            "priority": prio,
            "affected_roles": [role_map.get(task["owner_role"], task["owner_role"])],
            "affected_tasks": [tid],
            "affected_screens": task_screen_map.get(tid, []),
            "description": f"任务 {tid} ({task['task_name']}) 检测到 {gap}",
            "frequency_impact": f"{freq}频任务",
            "_sort": priority_rank(freq, gap)
        })

# From screen gaps
for sg in screen_gaps:
    for detail in sg.get("details", []):
        flag = detail["flag"]
        freq = "高"
        for tid in detail.get("affected_tasks", []):
            if tid in tasks:
                freq = tasks[tid].get("frequency", "中")
                break
        prio = "高" if flag in ("SILENT_FAILURE", "HIGH_RISK_NO_CONFIRM", "NO_SCREEN") else "中"
        gap_tasks_list.append({
            "id": next_gap(),
            "title": f"{sg['screen_name']} — {flag}",
            "type": flag,
            "priority": prio,
            "affected_roles": [],
            "affected_tasks": detail.get("affected_tasks", []),
            "affected_screens": [sg["screen_id"]],
            "description": detail["description"],
            "frequency_impact": f"{freq}频相关",
            "_sort": priority_rank(freq, flag)
        })

# From state gaps
for sg in state_gaps:
    for gap in sg["gaps"]:
        # Determine frequency from affected tasks
        freq = "低"
        for tid in sg.get("affected_tasks", []):
            if tid in tasks:
                tf = tasks[tid].get("frequency", "低")
                if tf == "高":
                    freq = "高"
                    break
                elif tf == "中":
                    freq = "中"
        prio = sg["severity"]
        gap_tasks_list.append({
            "id": next_gap(),
            "title": f"实体「{sg['entity']}」— {gap}",
            "type": gap,
            "priority": prio,
            "affected_roles": [],
            "affected_tasks": sg.get("affected_tasks", []),
            "affected_screens": [],
            "description": f"实体「{sg['entity']}」状态机检测到 {gap}（{sg['state_count']} 个状态, {sg['transition_count']} 个转换）",
            "frequency_impact": f"{freq}频相关",
            "_sort": priority_rank(freq, gap)
        })

gap_tasks_list.sort(key=lambda x: x["_sort"])
for g in gap_tasks_list:
    del g["_sort"]

C.write_json(os.path.join(OUT, "gap-tasks.json"), gap_tasks_list)

# ── Per-priority split files ─────────────────────────────────────────────────
priority_labels = {"高": "high", "中": "medium", "低": "low"}
priority_buckets = {}
for g in gap_tasks_list:
    p = g.get("priority", "低")
    priority_buckets.setdefault(p, []).append(g)

splits = {}
for p_cn, p_en in priority_labels.items():
    items = priority_buckets.get(p_cn, [])
    splits[p_en] = {
        "label": f"{p_cn}优先级",
        "description": f"{p_cn}优先级缺口任务（{len(items)} 条）",
        "items": items,
    }

prio_split_files = C.write_split_files(BASE, "feature-gap", "gap-tasks", "priority", splits)
for p in prio_split_files:
    print(f"  Split: {p}")

# ── Statistics ────────────────────────────────────────────────────────────────
task_gap_count = sum(1 for tg in task_gaps if "COMPLETE" not in tg["gaps"])
screen_gap_count = len(screen_gaps)
journey_gap_count = len(journey_gaps)
flow_gap_count = len(flow_gaps)
state_gap_count = len(state_gaps)

flag_stats = {}
for tg in task_gaps:
    for g in tg["gaps"]:
        if g != "COMPLETE":
            flag_stats[g] = flag_stats.get(g, 0) + 1
for sg in screen_gaps:
    for g in sg["gaps"]:
        flag_stats[g] = flag_stats.get(g, 0) + 1
for sg in state_gaps:
    for g in sg["gaps"]:
        flag_stats[g] = flag_stats.get(g, 0) + 1

role_scores = {}
for jg in journey_gaps:
    role = jg["role"]
    score_val = int(jg["score"].split("/")[0])
    role_scores.setdefault(role, []).append(score_val)

# ── Markdown report ──────────────────────────────────────────────────────────
lines = []
lines.append("# 功能缺口报告\n")
lines.append("## 摘要\n")
lines.append(f"- 任务缺口: {task_gap_count} 个")
lines.append(f"- 界面缺口: {screen_gap_count} 个")
lines.append(f"- 旅程缺口: {journey_gap_count} 个")
lines.append(f"- 业务流缺口: {flow_gap_count} 个")
lines.append(f"- 状态机缺口: {state_gap_count} 个\n")

lines.append("## Flag 统计\n")
lines.append("| Flag | 数量 |")
lines.append("|------|------|")
for flag, count in sorted(flag_stats.items(), key=lambda x: -x[1]):
    lines.append(f"| {flag} | {count} |")

lines.append("\n## 用户旅程评分\n")
for role, scores in sorted(role_scores.items()):
    avg = sum(scores) / len(scores) if scores else 0
    lines.append(f"- {role}: 平均 {avg:.1f}/4（{len(scores)} 条旅程）")

if state_gaps:
    lines.append("\n## 状态机完整性检查\n")
    lines.append("| 实体 | 状态数 | 转换数 | 缺口 | 严重级 |")
    lines.append("|------|--------|--------|------|--------|")
    for sg in state_gaps:
        lines.append(f"| {sg['entity']} | {sg['state_count']} | {sg['transition_count']} | {', '.join(sg['gaps'])} | {sg['severity']} |")

lines.append("\n## 缺口任务清单（按优先级排序）\n")
lines.append("| 优先级 | ID | 任务 | 缺口类型 | 描述 |")
lines.append("|--------|----|------|---------|------|")
for g in gap_tasks_list[:50]:
    lines.append(f"| {g['priority']} | {g['id']} | {g['title']} | {g['type']} | {g['description'][:60]} |")

with open(os.path.join(OUT, "gap-report.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

# ── Decisions ─────────────────────────────────────────────────────────────────
decisions = [
    {"step": "Step 1", "item_id": "task_check", "item_name": f"{task_gap_count} 任务缺口",
     "decision": "auto_confirmed", "reason": "全自动模式", "decided_at": NOW},
    {"step": "Step 2", "item_id": "screen_check", "item_name": f"{screen_gap_count} 界面缺口",
     "decision": "auto_confirmed", "reason": "全自动模式", "decided_at": NOW},
    {"step": "Step 3", "item_id": "journey_check", "item_name": f"{journey_gap_count} 旅程缺口",
     "decision": "auto_confirmed", "reason": "全自动模式", "decided_at": NOW},
    {"step": "Step 4", "item_id": "gap_tasks", "item_name": f"{len(gap_tasks_list)} 缺口任务",
     "decision": "auto_confirmed", "reason": "全自动模式", "decided_at": NOW},
    {"step": "Step 5", "item_id": "flow_check", "item_name": f"{flow_gap_count} 业务流缺口",
     "decision": "auto_confirmed", "reason": "全自动模式", "decided_at": NOW},
    {"step": "Step 6", "item_id": "state_check", "item_name": f"{state_gap_count} 状态机缺口",
     "decision": "auto_confirmed", "reason": "全自动模式", "decided_at": NOW},
]
C.write_json(os.path.join(OUT, "gap-decisions.json"), decisions)

# ── Pipeline decisions ────────────────────────────────────────────────────────
C.append_pipeline_decision(
    BASE,
    "Phase 5 — feature-gap",
    f"task_gaps={task_gap_count}, screen_gaps={screen_gap_count}, "
    f"journey_gaps={journey_gap_count}, flow_gaps={flow_gap_count}, "
    f"state_gaps={state_gap_count}, total_gap_tasks={len(gap_tasks_list)}"
)

# ── Summary ───────────────────────────────────────────────────────────────────
print(f"Task gaps: {task_gap_count} (of {len(tasks)} tasks)")
print(f"Screen gaps: {screen_gap_count}")
print(f"Journey gaps: {journey_gap_count}")
print(f"Flow gaps: {flow_gap_count}")
print(f"State machine gaps: {state_gap_count}")
print(f"Gap tasks generated: {len(gap_tasks_list)}")
print(f"Flags: {dict(sorted(flag_stats.items(), key=lambda x: -x[1]))}")
print(f"\nAll files written to {OUT}/")
