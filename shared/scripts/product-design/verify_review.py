#!/usr/bin/env python3
"""Unified pre-verification context collector (4D + 6V + XV).

Every generation phase has a verify loop:
  Script collects context + theory-backed review questions → stdout JSON
  Claude Code reads, reviews with LLM, fixes source if issues found, re-runs.
  Loop until clean.

Phases:
  concept      — product concept (JTBD, Kano, first principles)
  map          — product map (JTBD, ERRC, state completeness)
  journey      — journey emotion map (Peak-End Rule, emotion curve)
  experience   — experience map (Nielsen, ISO 9241-11, WCAG)
  use-case     — use case tree (BDD, boundary value, equivalence partitioning)
  feature-gap  — feature gap (Kano, JTBD, state closure)
  ui-design    — UI design spec (Gestalt, design system consistency)
  wireframe    — wireframe visual (Playwright)
  ui           — UI visual (Playwright)

Usage:
  python3 verify_review.py <BASE> --phase <phase> [--xv]
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
    resolve_base_path, load_json,
    load_experience_map, load_product_concept,
    load_task_inventory, load_business_flows,
    kill_other_review_servers, xv_available, xv_call
)


# ═══════════════════════════════════════════════════════════════════════════════
# REVIEW QUESTIONS — theory-backed 4D + 6V per phase
# ═══════════════════════════════════════════════════════════════════════════════

# ── Phase 1: concept ─────────────────────────────────────────────────────────
CONCEPT_4D = {
    "D1_conclusion": [
        "mission 是否清晰表达了产品的核心价值主张？",
        "每个角色的 jobs/pains/gains 是否准确反映目标用户的真实需求？（JTBD）",
        "mechanisms 是否构成完整的产品核心体验？",
        "商业模式的 metrics 是否能衡量产品成功？",
    ],
    "D2_evidence": [
        "top_problems 的 evidence 是否有来源说明（用户访谈/竞品分析/数据）？",
        "角色定义是否基于真实用户画像而非假想？",
        "商业模式假设是否有市场验证或竞品参考？",
    ],
    "D3_constraints": [
        "是否识别了关键的技术约束？",
        "是否识别了业务约束（目标市场、合规）？",
        "是否识别了用户使用场景约束？",
        "闭环：每个 pain 是否有对应的 pain_reliever？每个 gain 是否有对应的 gain_creator？（双向映射，缺一个就是断环）",
        "闭环：每个 mechanism 是否服务于至少一个角色的 JTBD？有没有孤立机制？",
        "闭环：每个 revenue_stream 是否有对应的价值交付机制？收费项是否有功能支撑？",
    ],
    "D4_decision": [
        "scope_strategy 是否与产品阶段匹配？（第一性原理：为什么是这个范围？）",
        "为什么选择这些 mechanisms 而非其他方案？有取舍说明吗？（ERRC 框架）",
    ],
}
CONCEPT_6V = {
    "user": "产品能解决用户核心痛点吗？用户愿意付出时间/金钱吗？（JTBD: functional/social/emotional jobs）",
    "business": "商业模式可持续吗？metrics 能驱动增长吗？收入闭环：付费→价值→留存→续费 是否成立？",
    "tech": "核心技术可行吗？有技术风险吗？",
    "ux": "核心交互流程是否直觉、低摩擦？",
    "data": "metrics 是否可观测？能否用数据验证假设？",
    "risk": "最大失败风险是什么？有合规/隐私/安全风险吗？",
}

# ── Phase 2: map ─────────────────────────────────────────────────────────────
MAP_4D = {
    "D1_conclusion": [
        "core/basic 分类是否合理？核心任务是否真的最重要？（Kano: must-have vs delighter）",
        "每个任务的 main_flow 是否完整合乎逻辑？",
        "业务流步骤顺序是否反映真实用户操作路径？",
    ],
    "D2_evidence": [
        "频次标签是否基于合理推断？",
        "风险标签是否基于业务影响评估？",
    ],
    "D3_constraints": [
        "对比 concept 的 mechanisms，是否每个机制都有对应任务？有遗漏就补",
        "是否有任务冗余（两个任务实质相同）？有就合并",
        "闭环完整性：每个功能任务的四类闭环是否完整？（配置闭环：谁来配置它？监控闭环：谁来看效果？异常闭环：失败了怎么办？生命周期闭环：数据最终去哪？）",
    ],
    "D4_decision": [
        "为什么某些任务是 basic 而非 core？依据是什么？（ERRC: 哪些该 Reduce/Eliminate）",
        "业务流是否过度设计？有可简化的步骤？",
    ],
}
MAP_6V = {
    "user": "任务列表是否覆盖用户完整操作场景？有遗漏吗？（JTBD 全覆盖）",
    "business": "核心任务是否支撑商业目标（留存/转化/营收）？",
    "tech": "main_flow 是否技术可实现？有不可控依赖吗？",
    "ux": "业务流步骤是否过多？关键操作需要几步？（3-click rule）",
    "data": "能否从任务中采集关键用户行为数据？",
    "risk": "高风险任务是否有足够保护措施？（状态闭环：孤儿/幽灵状态检测）",
}

# ── Phase 3: journey ─────────────────────────────────────────────────────────
JOURNEY_4D = {
    "D1_conclusion": [
        "情感曲线是否合理？高峰和低谷出现在正确的位置吗？（Peak-End Rule）",
        "每个节点的 emotion/intensity 是否与实际用户感受一致？",
        "journey_lines 是否覆盖了所有角色的关键操作路径？",
    ],
    "D2_evidence": [
        "emotion_nodes 的情感标注是否有业务依据（高风险步骤=焦虑，成功完成=满足）？",
        "design_hint 是否与情感状态匹配（低谷处应有缓解设计）？",
    ],
    "D3_constraints": [
        "source_flow 引用的业务流是否存在？",
        "是否遗漏了关键的负面情感点（如支付失败、数据丢失）？",
        "闭环：每个情感低谷是否有对应的恢复节点？（低谷→干预→恢复，不能只标注低谷不设计恢复）",
        "闭环：每条旅程线是否有明确的起点和终点？终点情感是否正面？（Peak-End Rule: 结尾体验决定整体印象）",
    ],
    "D4_decision": [
        "情感低谷处是否有对应的设计干预策略？（Peak-End: 确保结尾体验好）",
        "高 risk 节点是否标注了足够的 design_hint？",
    ],
}
JOURNEY_6V = {
    "user": "用户在每个节点的情感是否被准确捕捉？有没有被忽略的挫败点？",
    "business": "情感低谷是否会导致用户流失？需要哪些干预？",
    "tech": "design_hint 提出的干预方案是否技术可实现？",
    "ux": "情感曲线是否有\"先苦后甜\"的节奏？结尾是否正面？（Peak-End Rule）",
    "data": "哪些情感节点可以通过数据指标验证（如跳出率、完成率）？",
    "risk": "高 risk 节点是否都有容错/恢复设计？（闭环：失败→恢复→继续，不能中断旅程）",
}

# ── Phase 4: experience-map ──────────────────────────────────────────────────
EXPERIENCE_4D = {
    "D1_conclusion": [
        "每个屏幕的 interaction_type 是否与业务语义匹配？（不是随意分配）",
        "data_fields 是否完整覆盖了任务所需的用户输入/展示字段？",
        "actions 是否覆盖了用户在此屏幕的所有操作？",
        "states 状态机是否完整（初始/中间/终止/异常）？",
    ],
    "D2_evidence": [
        "每个屏幕是否可追溯到具体的 task？（task 引用有效）",
        "screen 的 navigation/route 是否与业务流一致？",
    ],
    "D3_constraints": [
        "是否所有 core task 都有对应屏幕？（覆盖完整性）",
        "platform 标注是否正确（mobile/web/desktop）？",
        "是否考虑了离线/弱网等场景约束？（如适用）",
        "闭环-导航：每个屏幕是否既可达又可退？有没有用户进得去出不来的死胡同？（Nielsen #3: 用户控制与自由）",
        "闭环-状态机：每个状态是否都有至少一个出口转换？有没有状态死锁（进入后无法离开）？",
        "闭环-错误恢复：每个可能失败的操作，失败后是否有恢复路径回到正常流程？",
    ],
    "D4_decision": [
        "屏幕数量是否合理？有没有过度拆分或遗漏合并？（Nielsen: 简洁性）",
        "交互类型选择的依据是什么？（ISO 9241-11: 有效性/效率/满意度）",
    ],
}
EXPERIENCE_6V = {
    "user": "用户能否通过这些屏幕顺畅完成任务？导航闭环完整吗？",
    "business": "核心业务路径的屏幕是否最精简？转化漏斗有没有不必要的步骤？",
    "tech": "implementation_contract 是否技术可实现？API 依赖是否合理？",
    "ux": "同类屏幕的交互模式是否一致？（Nielsen #4: 一致性与标准）",
    "data": "data_fields 是否能支撑数据采集和分析需求？",
    "risk": "高风险操作（删除/支付/权限变更）是否有确认步骤和撤销路径？（WCAG: 错误预防）",
}

# ── Phase 6a: use-case ───────────────────────────────────────────────────────
USECASE_4D = {
    "D1_conclusion": [
        "每个用例的 Given/When/Then 是否具体、可测试？（BDD 最佳实践）",
        "用例是否覆盖了正常流程 + 异常流程 + 边界条件？（等价类划分）",
        "feature_areas 分组是否合理？",
    ],
    "D2_evidence": [
        "用例的 then 断言是否可验证（不是\"系统正常工作\"这种模糊描述）？",
        "边界值用例是否覆盖了关键数值边界？（边界值分析）",
    ],
    "D3_constraints": [
        "是否所有 core task 都有对应用例？",
        "E2E 用例是否覆盖了完整业务流？",
        "闭环：每个 happy path 是否有对应的 sad path？（正常→异常 是一对闭环，不能只测正常路径）",
        "闭环：每个数据变更操作是否验证了完整生命周期？（创建→使用→修改→删除/归档）",
    ],
    "D4_decision": [
        "用例优先级排序是否合理？高频高风险任务的用例是否最完整？",
        "是否有冗余用例（多个用例测试同一场景）？",
    ],
}
USECASE_6V = {
    "user": "用例是否覆盖了用户实际会遇到的所有场景（含极端情况）？",
    "business": "业务关键路径（注册→核心功能→付费）的用例覆盖率是否充分？",
    "tech": "用例中的前置条件和预期结果是否技术上可自动化验证？",
    "ux": "用例是否包含了体验相关的验证（加载时间、动画反馈、错误提示）？",
    "data": "用例是否验证了数据完整性（创建→读取→更新→删除全流程）？",
    "risk": "安全相关用例是否充分（未授权访问、注入、数据泄露）？",
}

# ── Phase 6b: feature-gap ────────────────────────────────────────────────────
FEATUREGAP_4D = {
    "D1_conclusion": [
        "识别的 gap 是否是真正的缺口？还是已被其他方式覆盖？",
        "gap 的优先级是否合理？（Kano: must-have gap > nice-to-have gap）",
        "gap 的 type 分类是否准确？",
    ],
    "D2_evidence": [
        "每个 gap 的 affected_tasks 引用是否正确？",
        "gap 描述是否具体到可以行动（不是笼统的\"需要改进\"）？",
    ],
    "D3_constraints": [
        "是否遗漏了状态闭环缺口？（孤儿状态、幽灵状态）",
        "是否遗漏了跨角色交互的缺口？",
    ],
    "D4_decision": [
        "高优先级 gap 是否都影响核心业务路径？（JTBD: 功能性 job 的缺口最优先）",
        "低优先级 gap 是否真的可以延后？会不会影响用户信任？",
    ],
}
FEATUREGAP_6V = {
    "user": "从用户角度看，最影响体验的缺口是否都被识别了？",
    "business": "影响营收/转化的缺口优先级是否足够高？",
    "tech": "gap 描述的解决方案是否技术可行？",
    "ux": "体验断裂点（如流程中断、无反馈）是否都被识别为 gap？",
    "data": "数据可观测性缺口是否被考虑（缺少埋点、无法追踪转化）？",
    "risk": "安全/合规缺口是否零容忍？（高风险 gap 不可标低优先级）",
}

# ── Phase 6c: ui-design ──────────────────────────────────────────────────────
UIDESIGN_4D = {
    "D1_conclusion": [
        "设计规格是否覆盖了所有屏幕？有没有遗漏的界面？",
        "颜色/字体/间距的 design token 是否定义完整？",
        "创新概念的 UI 规格是否体现了创新方向？",
    ],
    "D2_evidence": [
        "设计决策是否有理由说明（为什么用这个颜色/布局）？",
        "组件复用是否有依据（相同功能用相同组件）？（Gestalt: 相似性原则）",
    ],
    "D3_constraints": [
        "是否满足无障碍要求？（WCAG: 对比度 ≥4.5:1、可键盘操作）",
        "是否适配目标平台的设计规范（iOS HIG / Material Design）？",
        "闭环-操作反馈：每个用户操作是否都有视觉反馈？（点击→加载→结果/错误，不能点了没反应）",
        "闭环-破坏性确认：每个不可逆操作（删除/支付/发布）是否有确认+可撤销设计？",
        "闭环-表单状态：每个输入字段是否定义了完整状态？（空→输入中→合法→错误→修正）",
    ],
    "D4_decision": [
        "视觉层级是否正确？主操作是否最突出？（Gestalt: 图底关系）",
        "信息密度是否适中？不过载不过空？（Miller's Law: 7±2）",
    ],
}
UIDESIGN_6V = {
    "user": "界面是否直觉、易学？新用户能否无指导完成核心操作？（Nielsen #2: 系统与现实匹配）",
    "business": "CTA 按钮是否突出？转化路径是否视觉引导清晰？",
    "tech": "设计规格是否可精确实现？有没有模糊描述（如\"适当间距\"）？",
    "ux": "相同类型屏幕的布局/交互是否一致？（Nielsen #4: 一致性）",
    "data": "数据展示是否清晰？图表/列表是否易读？",
    "risk": "敏感操作（删除/支付）的视觉警告是否醒目？",
}


# ═══════════════════════════════════════════════════════════════════════════════
# CONTEXT COLLECTORS
# ═══════════════════════════════════════════════════════════════════════════════

def collect_concept(base):
    concept = load_product_concept(base)
    if not concept:
        return None
    ctx = {
        "mission": concept.get("mission", ""),
        "tagline": concept.get("tagline", ""),
        "top_problems": concept.get("top_problems", []),
        "roles": concept.get("roles", []),
        "business_model": concept.get("business_model", {}),
        "mechanisms": concept.get("mechanisms", []),
        "pipeline_preferences": concept.get("pipeline_preferences", {}),
        "strategy": concept.get("strategy", {}),
    }
    for name in ("adversarial-concepts", "role-value-map"):
        data = load_json(os.path.join(base, "product-concept", f"{name}.json"))
        if data:
            ctx[name.replace("-", "_")] = data
    return ctx


def collect_map(base):
    task_dict = load_task_inventory(base)
    tasks = list(task_dict.values()) if isinstance(task_dict, dict) else (task_dict or [])
    flows = load_business_flows(base)
    if not tasks:
        return None
    concept = load_product_concept(base)
    flow_list = flows if isinstance(flows, list) else (flows.get("flows", []) if flows else [])
    mechanisms = concept.get("product_mechanisms", concept.get("mechanisms", [])) if concept else []
    return {
        "concept_mission": concept.get("mission", "") if concept else "",
        "concept_mechanisms": mechanisms,
        "concept_roles": concept.get("roles", []) if concept else [],
        "tasks": tasks,
        "task_summary": {
            "total": len(tasks),
            "core": len([t for t in tasks if t.get("category") == "core"]),
            "basic": len([t for t in tasks if t.get("category") == "basic"]),
        },
        "business_flows": flow_list,
    }


def collect_journey(base):
    data = load_json(os.path.join(base, "experience-map", "journey-emotion-map.json"))
    if not data:
        return None
    concept = load_product_concept(base)
    flows = load_business_flows(base)
    flow_list = flows if isinstance(flows, list) else (flows.get("flows", []) if flows else [])
    return {
        "concept_mission": concept.get("mission", "") if concept else "",
        "journey_lines": data.get("journey_lines", []),
        "business_flows_names": [f.get("name", "") for f in flow_list],
    }


def collect_experience(base):
    lines, index, loaded = load_experience_map(base)
    if not loaded:
        return None
    concept = load_product_concept(base)
    task_dict = load_task_inventory(base)
    tasks = list(task_dict.values()) if isinstance(task_dict, dict) else (task_dict or [])
    task_ids = {t.get("id") for t in tasks}

    # Collect all screens with full detail
    screens = []
    seen = set()
    for ol in lines:
        for node in ol.get("nodes", []):
            for s in node.get("screens", []):
                sid = s.get("id", "")
                if sid and sid not in seen:
                    seen.add(sid)
                    screens.append(s)

    return {
        "concept_mission": concept.get("mission", "") if concept else "",
        "operation_lines": lines,
        "screens": screens,
        "screen_count": len(screens),
        "task_ids_in_map": list(task_ids),
        "core_task_ids": [t["id"] for t in tasks if t.get("category") == "core"],
    }


def collect_usecase(base):
    data = load_json(os.path.join(base, "use-case", "use-case-tree.json"))
    if not data:
        return None
    task_dict = load_task_inventory(base)
    tasks = list(task_dict.values()) if isinstance(task_dict, dict) else (task_dict or [])
    return {
        "use_case_tree": data,
        "summary": data.get("summary", {}),
        "core_task_ids": [t["id"] for t in tasks if t.get("category") == "core"],
        "total_tasks": len(tasks),
    }


def collect_featuregap(base):
    gaps = load_json(os.path.join(base, "feature-gap", "gap-tasks.json"))
    if not gaps:
        return None
    task_dict = load_task_inventory(base)
    tasks = list(task_dict.values()) if isinstance(task_dict, dict) else (task_dict or [])
    return {
        "gaps": gaps if isinstance(gaps, list) else gaps.get("gaps", []),
        "gap_count": len(gaps) if isinstance(gaps, list) else len(gaps.get("gaps", [])),
        "core_task_ids": [t["id"] for t in tasks if t.get("category") == "core"],
        "total_tasks": len(tasks),
    }


def collect_uidesign(base):
    spec_path = os.path.join(base, "ui-design", "ui-design-spec.md")
    if not os.path.exists(spec_path):
        return None
    with open(spec_path, encoding="utf-8") as f:
        spec_text = f.read()

    lines, index, loaded = load_experience_map(base)
    screen_count = 0
    if loaded:
        seen = set()
        for ol in lines:
            for node in ol.get("nodes", []):
                for s in node.get("screens", []):
                    sid = s.get("id", "")
                    if sid and sid not in seen:
                        seen.add(sid)
                        screen_count += 1

    return {
        "spec_text": spec_text,
        "spec_length": len(spec_text),
        "screen_count": screen_count,
    }


def collect_wireframe(base):
    lines, index, loaded = load_experience_map(base)
    if not loaded:
        return None
    items = []
    seen = set()
    for ol in lines:
        for node in ol.get("nodes", []):
            for s in node.get("screens", []):
                sid = s.get("id", "")
                if sid and sid not in seen:
                    seen.add(sid)
                    items.append({
                        "screen_id": sid,
                        "name": s.get("name", ""),
                        "interaction_type": s.get("interaction_type", "?"),
                        "field_count": len(s.get("data_fields", [])),
                        "action_count": len(s.get("actions", [])),
                        "platform": s.get("platform", "mobile"),
                    })
    items.sort(key=lambda x: x["screen_id"])
    return {"items": items}


def collect_ui(base):
    ctx = collect_wireframe(base)
    if ctx:
        for item in ctx["items"]:
            item["check_focus"] = "visual_consistency"
    return ctx


# ═══════════════════════════════════════════════════════════════════════════════
# REGISTRIES
# ═══════════════════════════════════════════════════════════════════════════════

COLLECTORS = {
    "concept": collect_concept,
    "map": collect_map,
    "journey": collect_journey,
    "experience": collect_experience,
    "use-case": collect_usecase,
    "feature-gap": collect_featuregap,
    "ui-design": collect_uidesign,
    "wireframe": collect_wireframe,
    "ui": collect_ui,
}

REVIEW_QS = {
    "concept": {"4D": CONCEPT_4D, "6V": CONCEPT_6V},
    "map": {"4D": MAP_4D, "6V": MAP_6V},
    "journey": {"4D": JOURNEY_4D, "6V": JOURNEY_6V},
    "experience": {"4D": EXPERIENCE_4D, "6V": EXPERIENCE_6V},
    "use-case": {"4D": USECASE_4D, "6V": USECASE_6V},
    "feature-gap": {"4D": FEATUREGAP_4D, "6V": FEATUREGAP_6V},
    "ui-design": {"4D": UIDESIGN_4D, "6V": UIDESIGN_6V},
    "wireframe": {"check_criteria": [
        "交互类型 vs 布局 slots 是否匹配（业务语义与渲染一致）",
        "data_fields 中的字段名是否渲染",
        "actions 中的按钮是否存在",
        "产品语言与 UI 文本是否一致",
    ]},
    "ui": {"check_criteria": [
        "HTML 预览正常加载",
        "颜色/字体/间距统一（Gestalt: 一致性）",
        "相同类型屏幕使用相同组件模式",
        "UI 文本语言与产品定位一致",
    ]},
}


# ═══════════════════════════════════════════════════════════════════════════════
# XV CROSS-MODEL VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════

def _xv_json_schema(fields):
    return ('{"issues": [{"area": str, "issue": str, "severity": "high"|"medium"|"low", "fix": str}], '
            '"strengths": [str]}')


def xv_concept(ctx):
    summary = json.dumps({
        "mission": ctx["mission"],
        "roles": [{"name": r.get("role_name", r.get("name", "")),
                    "jobs": r.get("jobs", []), "pains": r.get("pains", [])}
                   for r in ctx.get("roles", [])],
        "mechanisms": ctx.get("mechanisms", [])[:10],
        "business_model": ctx.get("business_model", {}),
    }, ensure_ascii=False, indent=2)
    return {
        "system": (
            "You are a product strategy reviewer (JTBD + Kano + first principles + closure thinking). "
            "Identify: 1) mission-role alignment 2) mechanism gaps 3) business risks 4) role issues "
            "5) closure gaps (pain without reliever, gain without creator, mechanism without JTBD, revenue without value delivery).\n"
            f"Respond with ONLY valid JSON.\n{_xv_json_schema('')}"
        ),
        "user": f"Review this product concept:\n\n{summary}",
    }


def xv_map(ctx):
    tasks_brief = [{"id": t["id"], "name": t["name"], "category": t.get("category"),
                     "owner_role": t.get("owner_role")}
                    for t in ctx["tasks"][:30]]
    summary = json.dumps({
        "mission": ctx.get("concept_mission", ""),
        "mechanisms": ctx.get("concept_mechanisms", [])[:10],
        "tasks": tasks_brief,
        "flows": [{"name": f.get("name"), "steps": len(f.get("nodes", f.get("steps", [])))}
                  for f in ctx.get("business_flows", [])],
    }, ensure_ascii=False, indent=2)
    return {
        "system": (
            "You are a product map reviewer (JTBD + ERRC + state completeness + closure thinking). "
            "Identify: 1) missing tasks 2) classification issues 3) flow gaps 4) redundancy "
            "5) closure gaps (feature without config, operation without monitoring, action without error handling, creation without lifecycle end).\n"
            f"Respond with ONLY valid JSON.\n{_xv_json_schema('')}"
        ),
        "user": f"Review this product map:\n\n{summary}",
    }


def xv_journey(ctx):
    # Summarize journey lines
    jlines = ctx.get("journey_lines", [])
    summary = json.dumps([{
        "name": jl.get("name", ""),
        "role": jl.get("role", ""),
        "node_count": len(jl.get("emotion_nodes", [])),
        "emotions": [n.get("emotion", "") for n in jl.get("emotion_nodes", [])[:10]],
        "risks": [n.get("risk", "") for n in jl.get("emotion_nodes", []) if n.get("risk") in ("medium", "high")],
    } for jl in jlines], ensure_ascii=False, indent=2)
    return {
        "system": (
            "You are a UX emotion journey reviewer (Peak-End Rule). "
            "Identify: 1) emotion curve issues 2) missing recovery points 3) end-experience quality.\n"
            f"Respond with ONLY valid JSON.\n{_xv_json_schema('')}"
        ),
        "user": f"Review these emotion journey lines:\n\n{summary}",
    }


def xv_experience(ctx):
    screens_brief = [{"id": s.get("id", ""), "name": s.get("name", ""),
                       "interaction_type": s.get("interaction_type", ""),
                       "actions": len(s.get("actions", [])),
                       "fields": len(s.get("data_fields", []))}
                      for s in ctx.get("screens", [])[:30]]
    summary = json.dumps({
        "mission": ctx.get("concept_mission", ""),
        "screen_count": ctx["screen_count"],
        "screens": screens_brief,
        "core_tasks_covered": len([s for s in ctx.get("screens", [])
                                    if any(t.get("task_id") in (ctx.get("core_task_ids") or [])
                                           for t in s.get("tasks", []))]),
    }, ensure_ascii=False, indent=2)
    return {
        "system": (
            "You are a UX experience map reviewer (Nielsen heuristics + ISO 9241-11 + closure thinking). "
            "Identify: 1) interaction type mismatches 2) missing screens 3) consistency issues "
            "4) navigation closure (dead-ends, unreachable screens) 5) state machine closure (trapped states) 6) error recovery closure.\n"
            f"Respond with ONLY valid JSON.\n{_xv_json_schema('')}"
        ),
        "user": f"Review this experience map:\n\n{summary}",
    }


def xv_usecase(ctx):
    summary = json.dumps(ctx.get("summary", {}), ensure_ascii=False, indent=2)
    return {
        "system": (
            "You are a QA use-case reviewer (BDD + boundary value analysis). "
            "Identify: 1) weak Given/When/Then 2) missing edge cases 3) coverage gaps.\n"
            f"Respond with ONLY valid JSON.\n{_xv_json_schema('')}"
        ),
        "user": f"Review use-case tree summary:\n\n{summary}\nCore tasks: {len(ctx.get('core_task_ids', []))}, Total tasks: {ctx.get('total_tasks', 0)}",
    }


def xv_featuregap(ctx):
    gaps = ctx.get("gaps", [])
    summary = json.dumps([{"id": g.get("id"), "title": g.get("title"),
                            "type": g.get("type"), "priority": g.get("priority")}
                           for g in gaps[:30]], ensure_ascii=False, indent=2)
    return {
        "system": (
            "You are a product gap analyst (Kano + JTBD + state closure). "
            "Identify: 1) false gaps 2) missed real gaps 3) priority issues.\n"
            f"Respond with ONLY valid JSON.\n{_xv_json_schema('')}"
        ),
        "user": f"Review {len(gaps)} feature gaps:\n\n{summary}",
    }


def xv_uidesign(ctx):
    # Truncate spec to ~3000 chars for XV
    spec = ctx.get("spec_text", "")[:3000]
    return {
        "system": (
            "You are a UI design reviewer (Gestalt + WCAG + design system consistency). "
            "Identify: 1) usability issues 2) accessibility gaps 3) visual inconsistencies.\n"
            f"Respond with ONLY valid JSON.\n{_xv_json_schema('')}"
        ),
        "user": f"Review UI design spec ({ctx.get('screen_count', 0)} screens):\n\n{spec}",
    }


XV_BUILDERS = {
    "concept": xv_concept,
    "map": xv_map,
    "journey": xv_journey,
    "experience": xv_experience,
    "use-case": xv_usecase,
    "feature-gap": xv_featuregap,
    "ui-design": xv_uidesign,
}


def run_xv(phase, ctx):
    if not xv_available():
        return None
    builder = XV_BUILDERS.get(phase)
    if not builder:
        return None
    prompts = builder(ctx)
    try:
        result = xv_call(f"{phase}_review", prompts["user"], system_prompt=prompts["system"])
        return result
    except Exception as e:
        print(f"XV failed: {e}", file=sys.stderr)
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# HUB (visual phases only)
# ═══════════════════════════════════════════════════════════════════════════════

HUB_PATHS = {"wireframe": "/wireframe", "ui": "/ui"}

def ensure_hub_running(base, port=None):
    if port is None:
        port = int(os.environ.get("REVIEW_HUB_PORT", "18900"))
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


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    base = resolve_base_path()
    args = sys.argv[1:]
    remaining = [a for a in args if not os.path.isdir(a)]

    phase = None
    if "--phase" in remaining:
        idx = remaining.index("--phase")
        if idx + 1 < len(remaining):
            phase = remaining[idx + 1]

    if not phase or phase not in COLLECTORS:
        print(f"Usage: {sys.argv[0]} <BASE> --phase {'|'.join(sorted(COLLECTORS))}")
        sys.exit(1)

    ctx = COLLECTORS[phase](base)
    if not ctx:
        print(json.dumps({"error": f"{phase} data not found"}))
        sys.exit(1)

    output = {
        "phase": phase,
        "context": ctx,
        "review_questions": REVIEW_QS.get(phase, {}),
    }

    if "--xv" in remaining and phase in XV_BUILDERS:
        xv = run_xv(phase, ctx)
        if xv:
            output["xv_review"] = {
                "model": xv.get("model_used", "?"),
                "response": xv.get("response", ""),
            }

    if phase in HUB_PATHS:
        port = int(os.environ.get("REVIEW_HUB_PORT", "18900"))
        if ensure_hub_running(base, port):
            output["hub_url"] = f"http://localhost:{port}{HUB_PATHS[phase]}"

    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
