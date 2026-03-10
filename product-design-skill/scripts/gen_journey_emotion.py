#!/usr/bin/env python3
"""Phase 3: Generate journey-emotion-map.json from business-flows + role-profiles.

Creates initial emotion annotations for each business flow node.
All values are heuristic defaults — user review in Step 3 is required
(except in auto mode where only critical-risk nodes need confirmation).

Output schema (canonical):
{
  "journey_lines": [
    {
      "id": "JL01",
      "name": "...",
      "role": "R1",
      "source_flow": "F01",
      "emotion_nodes": [
        {"step": 1, "action": "...", "role": "R1",
         "emotion": "neutral", "intensity": 3, "risk": "low", "design_hint": ""}
      ]
    }
  ]
}

Usage:
    python3 gen_journey_emotion.py <BASE_PATH> [--mode auto] [--shard experience-map]
"""

import os
import sys
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C

# ── Emotion inference rules ──────────────────────────────────────────────────
# Based on task name keyword patterns (Chinese + English).
# Order matters: first match wins.

_EMOTION_RULES = [
    # Payment/subscription → anxiety
    (r"付费|订阅|支付|购买|subscribe|pay|purchase|checkout",
     {"emotion": "anxious", "intensity": 4, "risk": "high",
      "design_hint": "明确展示价值和权益对比，降低决策焦虑"}),
    # Content creation/generation → anticipation
    (r"生成|创建|创作|generate|create",
     {"emotion": "neutral", "intensity": 3, "risk": "medium",
      "design_hint": "显示进度和预估时间，管理等待预期"}),
    # Review/audit → focus
    (r"审核|审批|检查|approve|review|verify",
     {"emotion": "neutral", "intensity": 3, "risk": "medium",
      "design_hint": "结构化审核界面，高亮关键检查点"}),
    # Learning → curiosity
    (r"学习|练习|复习|阅读|浏览|learn|practice|review|read|browse",
     {"emotion": "neutral", "intensity": 3, "risk": "low",
      "design_hint": "保持内容新鲜感，适时鼓励"}),
    # Testing → tension
    (r"测试|考试|拼写|填空|选词|quiz|test|exam",
     {"emotion": "neutral", "intensity": 4, "risk": "medium",
      "design_hint": "即时反馈减轻焦虑，错误时提供鼓励和解释"}),
    # Download → anticipation
    (r"下载|安装|获取|download|install",
     {"emotion": "neutral", "intensity": 2, "risk": "low",
      "design_hint": "显示下载进度和预估时间"}),
    # Statistics/dashboard → reflection
    (r"统计|数据|仪表|报告|查看|dashboard|analytics|stats",
     {"emotion": "neutral", "intensity": 2, "risk": "low",
      "design_hint": "突出关键指标，渐进式展示细节"}),
    # Settings/config → focus
    (r"设置|配置|管理|编辑|setting|config|manage|edit",
     {"emotion": "neutral", "intensity": 2, "risk": "low",
      "design_hint": "分组归类参数，提供预设推荐"}),
    # Registration/onboarding
    (r"注册|登录|引导|signup|login|onboard",
     {"emotion": "neutral", "intensity": 3, "risk": "medium",
      "design_hint": "最小化步骤数，展示价值预览"}),
    # Publish → accomplishment
    (r"发布|上架|publish",
     {"emotion": "satisfied", "intensity": 4, "risk": "medium",
      "design_hint": "发布成功后给予成就感反馈"}),
    # Delete/remove → caution
    (r"删除|移除|下架|撤回|禁用|delete|remove|disable",
     {"emotion": "neutral", "intensity": 3, "risk": "high",
      "design_hint": "二次确认 + 可恢复机制"}),
    # Feedback
    (r"反馈|建议|评价|feedback|report",
     {"emotion": "neutral", "intensity": 2, "risk": "low",
      "design_hint": "简化表单，提供模板选项"}),
]


def _infer_emotion(task, is_first=False, is_last=False):
    """Infer emotion annotation for a task node.

    Returns dict with emotion/intensity/risk/design_hint.
    """
    name = task.get("name", "").lower()

    # Check keyword rules
    for pattern, result in _EMOTION_RULES:
        if re.search(pattern, name):
            return dict(result)  # return a copy

    # Position-based defaults
    if is_first:
        return {"emotion": "neutral", "intensity": 2, "risk": "low",
                "design_hint": "清晰的入口指引"}
    if is_last:
        return {"emotion": "satisfied", "intensity": 3, "risk": "low",
                "design_hint": "明确的完成反馈"}

    return {"emotion": "neutral", "intensity": 3, "risk": "low",
            "design_hint": "保持操作流畅性"}


# ── Setup ────────────────────────────────────────────────────────────────────
BASE, args = C.parse_args()
OUT = os.path.join(BASE, "experience-map")
C.ensure_dir(OUT)
NOW = C.now_iso()

# ── Load inputs ──────────────────────────────────────────────────────────────
flows = C.load_business_flows(BASE)
tasks = C.load_task_inventory(BASE)

roles_data = C.load_json(os.path.join(BASE, "product-map/role-profiles.json"))
role_map = {}
if roles_data and "roles" in roles_data:
    for r in roles_data["roles"]:
        role_map[r["id"]] = r

if not flows:
    print("ERROR: No business flows found. Run /product-map first.", file=sys.stderr)
    sys.exit(1)

# ── Generate journey lines ───────────────────────────────────────────────────
journey_lines = []
jl_counter = 0

for flow in flows:
    fid = flow.get("id", "")
    fname = flow.get("name", "")
    nodes = C.get_flow_nodes(flow)

    if not nodes:
        print(f"  WARN: Flow {fid} ({fname}) has no nodes, skipped")
        continue

    jl_counter += 1
    emotion_nodes = []

    for i, node in enumerate(nodes):
        # Extract task_ref from node (string or dict)
        if isinstance(node, str):
            task_ref = node
            node_role = ""
        else:
            task_ref = node.get("task_ref", "")
            node_role = node.get("role", "")

        task = tasks.get(task_ref, {})
        if not task:
            continue

        is_first = (i == 0)
        is_last = (i == len(nodes) - 1)

        emo = _infer_emotion(task, is_first, is_last)

        emotion_nodes.append({
            "step": i + 1,
            "action": task.get("name", ""),
            "role": node_role or task.get("owner_role", ""),
            "task_ref": task_ref,
            "emotion": emo["emotion"],
            "intensity": emo["intensity"],
            "risk": emo["risk"],
            "design_hint": emo["design_hint"],
        })

    if not emotion_nodes:
        continue

    # Determine primary role
    roles_in_flow = list(set(n["role"] for n in emotion_nodes if n["role"]))
    primary_role = roles_in_flow[0] if roles_in_flow else "R1"

    journey_lines.append({
        "id": f"JL{jl_counter:02d}",
        "name": fname,
        "role": primary_role,
        "source_flow": fid,
        "emotion_nodes": emotion_nodes,
        "human_decision": False,
    })

# ── Emotion summary ──────────────────────────────────────────────────────────
emotion_counts = {}
risk_counts = {}
for jl in journey_lines:
    for node in jl["emotion_nodes"]:
        emotion_counts[node["emotion"]] = emotion_counts.get(node["emotion"], 0) + 1
        if node["risk"] != "low":
            risk_counts[node["risk"]] = risk_counts.get(node["risk"], 0) + 1

# ── Write output ─────────────────────────────────────────────────────────────
output = {
    "generated_at": NOW,
    "source": "business-flows.json + task-inventory.json",
    "journey_count": len(journey_lines),
    "total_nodes": sum(len(jl["emotion_nodes"]) for jl in journey_lines),
    "emotion_distribution": emotion_counts,
    "risk_distribution": risk_counts,
    "journey_lines": journey_lines,
}

out_path = C.write_json(os.path.join(OUT, "journey-emotion-map.json"), output)

# ── Pipeline decision ────────────────────────────────────────────────────────
C.append_pipeline_decision(
    BASE,
    "Step 3 — journey-emotion",
    f"journey_lines={len(journey_lines)}, total_nodes={output['total_nodes']}",
    shard=args.get("shard"),
)

# ── Summary ──────────────────────────────────────────────────────────────────
print(f"OK: {out_path}")
print(f"  Journey lines: {len(journey_lines)}")
print(f"  Total nodes: {output['total_nodes']}")
print(f"  Emotions: {emotion_counts}")
print(f"  Risks: {risk_counts}")
