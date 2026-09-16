"""Evidence-bound rule review, shared by host renderers; no natural-language inference.

`evaluate` reads a frozen review once and returns report lines plus the done gate.
`done_reason` applies that gate to an entry's requirement references. Candidate
conflicts never enter implementation verdict counts or acquire G/J identifiers.
"""
import hashlib
import json
from datetime import datetime
from pathlib import Path

KINDS = {"behavior_conflict", "scope_dependency", "unreachable_condition",
         "version_conflict", "exception_ambiguity", "needs_clarification"}
DISPOSITIONS = {"confirmed_conflict": "确认冲突，尚未解决", "clarified": "已澄清",
                "deferred": "暂缓决定"}
TITLE = "## 规则一致性（规则 ↔ 规则；候选不计为产品缺陷）"


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _strings(value):
    return isinstance(value, list) and all(_text(v) for v in value)


def _index(rows, label):
    _require(isinstance(rows, list), label + " 须是列表")
    result = {}
    for row in rows:
        _require(isinstance(row, dict) and _text(row.get("id")), label + " 缺 id")
        _require(row["id"] not in result, label + " 重复 id：" + row["id"])
        result[row["id"]] = row
    return result


def _read_bound(run_dir, ref, digest):
    _require(_text(ref) and not Path(ref).is_absolute(), "引用须是 run 内相对路径")
    path = (run_dir / ref).resolve()
    root = (run_dir / "evidence").resolve()
    _require(root.is_relative_to(run_dir.resolve()) and path.is_relative_to(root), "引用逃逸 evidence：" + ref)
    data = path.read_bytes()
    _require(hashlib.sha256(data).hexdigest() == digest, "摘要不匹配：" + ref)
    return data.decode("utf-8")


def requirements_digest(requirements):
    """Bind IDs AND text; keeping an ID does not make a changed requirement the same input."""
    data = json.dumps(requirements, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _report(review, ledger, run_dir):
    sources = _index(review.get("sources"), "sources")
    _require(bool(sources), "reviewed 缺规则来源")
    texts = {}
    for sid, source in sources.items():
        _require(_text(source.get("origin")), "来源缺 origin：" + sid)
        texts[sid] = _read_bound(run_dir, source.get("ref"), source.get("sha256"))
    _require(_text(review.get("agent_task")) and _text(review.get("agent_model")), "缺独立审查任务/模型记录")
    report = json.loads(_read_bound(run_dir, review.get("report_ref"), review.get("report_digest")))
    _require(isinstance(report, dict) and report.get("schema_version") == 1, "非法规则报告版本")
    reviewer = report.get("reviewer")
    _require(isinstance(reviewer, dict) and reviewer.get("independent") is True
             and _text(reviewer.get("session_id")), "缺独立规则审查官标识")
    ids = report.get("source_ids")
    _require(_strings(ids) and len(ids) == len(set(ids)) and set(ids) == set(sources), "报告未覆盖全部来源")
    _require(report.get("source_digests") == {sid: s["sha256"] for sid, s in sources.items()},
             "审查时来源摘要与当前快照不符，须重新独立审查")
    _require(report.get("requirements_digest") == requirements_digest(ledger.get("requirements", [])),
             "审查时需求摘要与当前点名册不符，须重新独立审查")
    _require(_strings(report.get("could_not")), "could_not 须是列表")
    rules = _index(report.get("rules"), "rules")
    requirements = _index(ledger.get("requirements", []), "requirements")
    mapped = set()
    for rid, rule in rules.items():
        source = rule.get("source_id")
        _require(isinstance(source, str) and source in texts, "规则来源不存在：" + rid)
        start, end = rule.get("start_line"), rule.get("end_line")
        lines = texts[source].splitlines()
        _require(type(start) is int and type(end) is int and 1 <= start <= end <= len(lines), "规则行号无效：" + rid)
        _require(_text(rule.get("quote")) and rule["quote"] == "\n".join(lines[start - 1:end]), "规则原文不匹配：" + rid)
        scope = rule.get("scope")
        _require(isinstance(scope, dict) and all(_text(scope.get(k)) for k in
                 ("release", "platform", "role", "condition")), "规则缺适用范围：" + rid)
        _require(_text(rule.get("subject")) and _text(rule.get("effect")), "规则缺对象/行为：" + rid)
        _require(_strings(rule.get("exceptions")) and _strings(rule.get("supersedes")), "规则缺例外/覆盖记录：" + rid)
        _require(set(rule["supersedes"]) <= set(rules) - {rid}, "规则覆盖引用无效：" + rid)
        refs = rule.get("requirement_refs")
        _require(_strings(refs) and set(refs) <= set(requirements), "规则需求引用无效：" + rid)
        mapped.update(refs)
    _require(mapped == set(requirements), "需求未被规则提取覆盖：" + "、".join(sorted(set(requirements) - mapped)))
    findings = _index(report.get("findings"), "findings")
    for fid, finding in findings.items():
        _require(isinstance(finding.get("kind"), str) and finding["kind"] in KINDS, "候选类型无效：" + fid)
        refs = finding.get("rule_refs")
        _require(_strings(refs) and len(set(refs)) >= 2 and set(refs) <= set(rules), "候选须引用至少两条已摘录规则：" + fid)
        _require(all(_text(finding.get(k)) for k in ("scope_overlap", "reason", "question")), "候选缺条件/依据/澄清问题：" + fid)
    groups = report.get("comparison_groups")
    _require(isinstance(groups, list), "comparison_groups 须是列表")
    grouped, linked = set(), set()
    for group in groups:
        _require(isinstance(group, dict), "比较组须是对象")
        refs = group.get("rule_refs")
        _require(_strings(refs) and bool(refs) and set(refs) <= set(rules), "比较组规则引用无效")
        _require(group.get("result") in ("compatible", "findings") and _text(group.get("basis")), "比较组缺结果/依据")
        hits = {fid for fid, f in findings.items() if set(f["rule_refs"]) <= set(refs)}
        _require(bool(hits) == (group["result"] == "findings"), "比较组结果与候选不符")
        grouped.update(refs)
        linked.update(hits)
    _require(grouped == set(rules) and linked == set(findings), "规则/候选未被比较分组覆盖")
    return report, sources, rules, findings


def _decisions(review, findings):
    rows = review.get("decisions", [])
    _require(isinstance(rows, list), "decisions 须是列表")
    current, stale = {}, 0
    for decision in rows:
        _require(isinstance(decision, dict), "decision 须是对象")
        if decision.get("report_digest") != review.get("report_digest"):
            stale += 1
            continue
        fid, disposition = decision.get("finding_id"), decision.get("disposition")
        _require(isinstance(fid, str) and fid in findings, "决策引用未知候选")
        _require(isinstance(disposition, str) and disposition in DISPOSITIONS, "决策类型无效")
        _require(_text(decision.get("confirmation")), "决策缺用户原话")
        stamp = decision.get("confirmed_at")
        _require(_text(stamp), "决策缺确认时间")
        dt = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
        _require(dt.utcoffset() is not None, "确认时间缺时区")
        if disposition == "clarified":
            _require(_text(decision.get("effective_rule")), "澄清缺有效规则")
        current[fid] = decision   # append-only user history; last decision for this report wins
    return current, stale


def evaluate(ledger, run_dir):
    """Return {lines, blocked}; blocked=None means every done is blocked, set() means none."""
    run_dir = Path(run_dir)
    out = ["", TITLE]
    review = ledger.get("rule_consistency")
    if review is None and ledger.get("ledger_version", 1) < 3:
        return {"lines": out + ["历史台账未做规则对比；不追溯拒收原裁决。"], "blocked": set()}
    try:
        _require(isinstance(review, dict), "新 run 缺 rule_consistency")
        status = review.get("status")
        if status == "not_applicable":
            _require(ledger.get("baseline") == "none" and not ledger.get("requirements")
                     and not ledger.get("journeys") and not ledger.get("visual_acceptance")
                     and not review.get("sources") and not review.get("report_ref"), "存在规则或验收基线，不能声明 not_applicable")
            _require(_text(review.get("reason")), "not_applicable 缺原因")
            return {"lines": out + ["无规则可比（不是审查通过）：" + review["reason"]], "blocked": set()}
        if status in ("not_examined", "unavailable"):
            _require(_text(review.get("reason")), "未审/无法审查须记录原因")
            return {"lines": out + ["规则审查未完成：" + review["reason"]], "blocked": None}
        _require(status == "reviewed", "规则审查状态无效")
        report, sources, rules, findings = _report(review, ledger, run_dir)
        decision_error = ""
        try:
            decisions, stale = _decisions(review, findings)
        except (ValueError, TypeError, KeyError) as exc:
            # Invalid user bookkeeping must not erase valid independent evidence.
            decisions, stale = {}, 0
            decision_error = str(exc)
        out.append(f"来源 {len(sources)} 份 · 规则 {len(rules)} 条 · 比较组 {len(report['comparison_groups'])} 个 · 候选 {len(findings)} 条")
        out.append("仅核对本轮材料；语义覆盖、来源完整性与用户确认真实性须核对独立审查记录。")
        out.append("独立审查：" + review["agent_task"] + " · " + review["agent_model"])
        for sid, source in sources.items():
            out.append(f"- 来源 {sid}：{source['origin']}（{source['ref']}）")
        for group in report["comparison_groups"]:
            out.append(f"- 比较 {' / '.join(group['rule_refs'])}：{group['result']} — {group['basis']}")
        blocked = set()
        for fid, finding in findings.items():
            decision = decisions.get(fid, {})
            disposition = decision.get("disposition")
            label = DISPOSITIONS.get(disposition, "待用户澄清")
            out.extend(["", f"### {fid} · {finding['kind']} · {label}",
                        f"共同条件：{finding['scope_overlap']}", finding["reason"], "待确认：" + finding["question"]])
            affected = set()
            unmapped = False
            for rid in finding["rule_refs"]:
                rule = rules[rid]
                affected.update(rule["requirement_refs"])
                unmapped = unmapped or not rule["requirement_refs"]
                out.append(f"- {rid} {rule['source_id']}:{rule['start_line']}-{rule['end_line']} · "
                           + " / ".join(f"{k}={v}" for k, v in rule["scope"].items()))
                out.extend("> " + line for line in rule["quote"].splitlines())
            if decision:
                out.append(f"用户于 {decision['confirmed_at']}：{decision['confirmation']}")
                if disposition == "clarified":
                    out.append("有效规则：" + decision["effective_rule"])
            if disposition != "clarified":
                if unmapped or not affected:
                    blocked = None
                elif blocked is not None:
                    blocked.update(affected)
        if stale:
            out.append(f"过期确认 {stale} 条未采信：新报告不继承旧结论。")
        if report["could_not"]:
            out.extend("未能审查：" + reason for reason in report["could_not"])
            blocked = None
        elif not findings:
            out.append("本次材料未发现冲突候选（不等于证明无矛盾）。")
        if decision_error:
            out.append("决策不可采信（候选证据保留）：" + decision_error)
            blocked = None
        return {"lines": out, "blocked": blocked,
                "requirements": {r["id"] for r in ledger.get("requirements", [])}}
    except (ValueError, OSError, TypeError, KeyError) as exc:
        return {"lines": out + ["规则审查不可采信：" + str(exc)], "blocked": None}


def done_reason(state, requirement_refs):
    """Missing or unknown IDs cannot masquerade as an unrelated, reviewed requirement."""
    blocked = state["blocked"]
    unknown = set(requirement_refs) - state.get("requirements", set())
    if blocked is None or (blocked and (unknown or not requirement_refs or blocked.intersection(requirement_refs))):
        return "规则基线未澄清或审查未完成，不能据此判 done（见规则一致性）"
    return ""
