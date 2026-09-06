# cross-exam Journey Declarations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** cross-exam 新增"旅程"声明：用户口述三元组加 oracle，fresh-context 探针端到端走一遍并逐步落证据，盘问官对 oracle 裁决，渲染器出"旅程完成度"节。

**Architecture:** 数据进 `ledger.json` 顶层 `journeys[]`，实证 entry 带 `journey` 与 `steps[]`；渲染器只认 `entry_q` 精确匹配到被采信 entry 的旅程为已盘问。协议在定面之后加 §1b 旅程采集，盘问循环加旅程轮；探针只拿目标不拿 oracle。Claude（`claude/superstorm/`）与 Codex（`codex/cross-exam-skill/`）两个孪生版同步改。

**Tech Stack:** Python 3 标准库（渲染器）、unittest、Markdown skill 文件。

**Spec:** `docs/superpowers/specs/2026-09-05-cross-exam-journey-declarations-design.md`

## Global Constraints

- cross-exam 全部不变量不变：只记账不修、有人在场、证据独立采集、实测官不可降级、通用、报告只由 `render_report.py` 渲染。
- 期望隔离：探针输入的 `journey` 块**不含 oracle**。
- `stuck_kind` 六种：`no_entry | not_found | misleading | no_feedback | no_recovery | broken`。
- `journeys[]` 顶层键可缺省，缺省视为 `[]`，渲染器不报错。
- 旅程已盘问的唯一判据：`journeys[].entry_q` 精确匹配到一条被采信 entry，且该 entry 的 `journey` 等于该旅程 `id`。`status` 字段不作依据。
- Codex 渲染器保留其 severity 校验（gap/drift 缺合法 severity 拒渲）和 UUID 字段；`journeys[]` 与 `steps[]` 不加 UUID。
- 所有文件 UTF-8，中文文案与现有 skill 文件一致。
- 提交信息末尾带：
  ```
  Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
  Claude-Session: https://claude.ai/code/session_01WMtG82xCvdD6Q4BbWm5YXR
  ```
- 渲染器测试运行方式：`cd claude/superstorm/scripts && python3 -m pytest test_render_report.py -q`；Codex 版 `cd codex/cross-exam-skill/scripts && python3 -m pytest test_render_report.py -q`。pre-commit 会跑 meta-skill 测试和 skill 校验，提交失败即修。

---

## File map

| 文件 | 改动 |
|---|---|
| `claude/superstorm/scripts/render_report.py` | journeys 采信、旅程完成度节、计数分列、未盘问旅程、拒渲原因 |
| `claude/superstorm/scripts/test_render_report.py` | 新增 `TestJourneys` |
| `codex/cross-exam-skill/scripts/render_report.py` | 同上，保留 severity 校验 |
| `codex/cross-exam-skill/scripts/test_render_report.py` | 同上 |
| `claude/superstorm/knowledge/cross-exam/schemas.md`、`codex/cross-exam-skill/schemas.md` | `journeys[]`、entry 新字段、红线第 4 条 |
| `claude/superstorm/knowledge/cross-exam/prompts/prober.md`、`codex/cross-exam-skill/prompts/prober.md` | `journey` 输入块、纪律 7 至 9、返回字段 |
| `claude/superstorm/knowledge/cross-exam/lenses.md`、`codex/cross-exam-skill/lenses.md` | 旅程镜头一行 |
| `claude/superstorm/skills/cross-exam.md`、`codex/cross-exam-skill/SKILL.md` | description、§1b、§2 旅程轮 |
| `claude/superstorm/skills/product-review.md`、`codex/cross-exam-skill/product-review.md` | Prior evidence 认 `J` 编号 |
| `codex/cross-exam-skill/AGENTS.md` | 一句提到旅程 |
| `CLAUDE.md` | cross-exam 行补旅程 |
| `claude/superstorm/.claude-plugin/plugin.json`、`marketplace.json` | 版本 0.22.0 → 0.23.0 |

---

### Task 1: Claude 渲染器支持 journeys

**Files:**
- Modify: `claude/superstorm/scripts/render_report.py`
- Test: `claude/superstorm/scripts/test_render_report.py`

**Interfaces:**
- Consumes: 现有 `render(run_dir) -> str`、`_has_evidence`、`_risk_key`、`VERDICT_LABELS`、`SEVERITY_ORDER`。
- Produces: 模块常量 `STUCK_KINDS`（dict）；函数 `_refusal_reason(e, journey_ids) -> str`、`_journey_title(j) -> str`、`_journey_block(j, e) -> list[str]`、`_not_examined_line(item, prefix="")`。报告新节标题 `## 旅程完成度`，总览行 `旅程裁决：…`，头行片段 ` · 旅程 N 条，盘问 M 条`。Task 2 按同名移植。

- [ ] **Step 1: 给测试文件加 journeys 注入辅助和失败用例**

在 `test_render_report.py` 的 `_entry` 之后追加：

```python
def _journey(jid="J1", entry_q="J1 走得通吗？", status="examined", risk=None):
    j = {"id": jid, "who": "回头客", "circumstance": "购物车里已有一件商品",
         "progress": "完成支付并拿到订单号",
         "preconditions": ["已登录测试账号"], "waypoints": ["支付确认页"],
         "oracle": {"done_looks_like": ["URL 含 /orders/"],
                    "stuck_looks_like": ["仍在 /cart"]},
         "step_budget": 15, "status": status, "entry_q": entry_q}
    if risk:
        j["risk"] = risk
    return j


def _jentry(q="J1 走得通吗？", jid="J1", verdict="done", ev_dir="evidence/q5/",
            severity=None, stuck_kind=None, steps=None, missed_waypoints=None):
    e = _entry(q, verdict=verdict, ev_dir=ev_dir, severity=severity)
    e["journey"] = jid
    e["steps"] = steps if steps is not None else [
        {"n": 1, "action": "打开 /cart", "observed": "购物车显示 1 件商品",
         "status": "done", "evidence": "q05-01-cart.png"},
        {"n": 2, "action": "点击 结账", "observed": "跳到 /orders/1001",
         "status": "done", "evidence": "q05-02-order.png"}]
    if stuck_kind:
        e["stuck_kind"] = stuck_kind
    if missed_waypoints is not None:
        e["missed_waypoints"] = missed_waypoints
    return e


def _with_journeys(run, journeys):
    L = json.loads((run / "ledger.json").read_text(encoding="utf-8"))
    L["journeys"] = journeys
    (run / "ledger.json").write_text(json.dumps(L, ensure_ascii=False), encoding="utf-8")
    return run
```

在文件末尾（`if __name__` 之前，若无则直接末尾）追加测试类：

```python
class TestJourneys(unittest.TestCase):
    FACETS = [{"id": "F1", "name": "面一", "status": "examined"}]

    def test_journey_done_counted_separately_from_plain(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = _mk_run(tmp, self.FACETS, [_jentry()])
            _with_journeys(run, [_journey()])
            report = render(run)
            overview = report[:report.index("## 逐面完成度")]
            self.assertIn("旅程 1 条，盘问 1 条", overview)
            self.assertIn("旅程裁决：实证完成：1", overview)
            self.assertIn("实证完成：0 · 缺口：0", overview)   # 普通计数不含旅程
            sec = report[report.index("## 旅程完成度"):report.index("## 缺口清单")]
            self.assertIn("J1 回头客 · 购物车里已有一件商品 · 完成支付并拿到订单号", sec)
            self.assertIn("走通，2 步", sec)
            self.assertIn("- 1 done 打开 /cart → 购物车显示 1 件商品", sec)
            facet_sec = report[report.index("## 逐面完成度"):report.index("## 旅程完成度")]
            self.assertNotIn("J1 走得通吗？", facet_sec)

    def test_journey_gap_renders_stuck_step_kind_and_tag(self):
        with tempfile.TemporaryDirectory() as tmp:
            steps = [
                {"n": 1, "action": "打开 /cart", "observed": "购物车显示 1 件商品",
                 "status": "done", "evidence": "q05-01-cart.png"},
                {"n": 7, "action": "点击 确认支付", "observed": "按钮变灰 3 秒后恢复，页面无变化",
                 "status": "stuck", "evidence": "q05-07-pay-noop.png"}]
            e = _jentry(verdict="gap", severity="high", stuck_kind="no_feedback", steps=steps)
            run = _mk_run(tmp, self.FACETS, [e])
            _with_journeys(run, [_journey()])
            report = render(run)
            sec = report[report.index("## 旅程完成度"):report.index("## 缺口清单")]
            self.assertIn("缺口（high，无反馈）", sec)
            self.assertIn("走了 2 步，卡在第 7 步：点击 确认支付 → 按钮变灰 3 秒后恢复，页面无变化", sec)
            gap_sec = report[report.index("## 缺口清单"):report.index("## 无法自证清单")]
            self.assertIn("[J1]", gap_sec)
            self.assertIn("旅程裁决：实证完成：0 · 缺口：1", report)

    def test_journey_gap_with_illegal_stuck_kind_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            e = _jentry(verdict="gap", severity="high", stuck_kind="lost")
            run = _mk_run(tmp, self.FACETS, [e])
            _with_journeys(run, [_journey()])
            report = render(run)
            self.assertIn("违规裁决", report)
            self.assertIn("非法卡死类型：lost", report)
            self.assertIn("旅程 1 条，盘问 0 条", report)
            unex = report[report.index("## 未盘问声明"):report.index("## 未拉的线")]
            self.assertIn("旅程 J1", unex)

    def test_entry_referencing_unknown_journey_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            e = _jentry(jid="J9", q="J9 走得通吗？")
            run = _mk_run(tmp, self.FACETS, [e])
            _with_journeys(run, [_journey()])
            report = render(run)
            self.assertIn("违规裁决", report)
            self.assertIn("旅程引用不存在：J9", report)
            self.assertIn("旅程裁决：实证完成：0", report)

    def test_journey_entry_q_unmatched_is_unexamined_despite_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = _mk_run(tmp, self.FACETS, [_jentry()])
            _with_journeys(run, [_journey(entry_q="nope", status="examined")])
            report = render(run)
            self.assertIn("旅程 1 条，盘问 0 条", report)
            unex = report[report.index("## 未盘问声明"):report.index("## 未拉的线")]
            self.assertIn("旅程 J1", unex)
            self.assertIn("未评估风险", unex)

    def test_journey_linked_to_refused_entry_is_unexamined(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = _mk_run(tmp, self.FACETS, [_jentry()], make_evidence=False)
            _with_journeys(run, [_journey()])
            report = render(run)
            self.assertIn("违规裁决", report)
            self.assertIn("旅程 1 条，盘问 0 条", report)
            unex = report[report.index("## 未盘问声明"):report.index("## 未拉的线")]
            self.assertIn("旅程 J1", unex)

    def test_not_examined_journeys_sorted_by_risk_after_facets(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = _mk_run(tmp, self.FACETS, [_entry("q1")])
            _with_journeys(run, [
                _journey("J1", entry_q="", status="not_examined",
                         risk={"level": "low", "why": "次要路径"}),
                _journey("J2", entry_q="", status="not_examined",
                         risk={"level": "high", "why": "主线收入"}),
                _journey("J3", entry_q="", status="not_examined")])
            report = render(run)
            unex = report[report.index("## 未盘问声明"):report.index("## 未拉的线")]
            self.assertLess(unex.index("旅程 J2"), unex.index("旅程 J1"))
            self.assertLess(unex.index("旅程 J1"), unex.index("旅程 J3"))
            self.assertIn("主线收入", unex)
            self.assertIn("未评估风险", unex)
            self.assertIn("实证完成：1", report)   # 未盘问旅程不进计数

    def test_journeys_key_absent_renders_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = _mk_run(tmp, self.FACETS, [_entry("q1")])
            report = render(run)
            self.assertIn("## 旅程完成度", report)
            sec = report[report.index("## 旅程完成度"):].split("\n## ")[0]
            self.assertIn("（无旅程声明）", sec)
            self.assertNotIn("旅程裁决", report)
            self.assertNotIn("旅程 0 条", report)

    def test_journey_drift_lists_missed_waypoints(self):
        with tempfile.TemporaryDirectory() as tmp:
            e = _jentry(verdict="drift", severity="medium", missed_waypoints=["支付确认页"])
            run = _mk_run(tmp, self.FACETS, [e])
            _with_journeys(run, [_journey()])
            report = render(run)
            sec = report[report.index("## 旅程完成度"):report.index("## 缺口清单")]
            self.assertIn("跑偏（medium）", sec)
            self.assertIn("走通但绕过 waypoint：支付确认页", sec)

    def test_journey_unprovable_shows_reason(self):
        with tempfile.TemporaryDirectory() as tmp:
            e = _jentry(verdict="unprovable", steps=[])
            e["evidence"]["key_observation"] = "测试账号无法登录，前置条件造不出"
            run = _mk_run(tmp, self.FACETS, [e])
            _with_journeys(run, [_journey()])
            report = render(run)
            sec = report[report.index("## 旅程完成度"):report.index("## 缺口清单")]
            self.assertIn("无法自证：测试账号无法登录，前置条件造不出", sec)
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd claude/superstorm/scripts && python3 -m pytest test_render_report.py -q -k Journeys`
Expected: 10 个用例 FAIL（`## 旅程完成度` 不存在、`旅程裁决` 不存在等）。现有用例仍 PASS。

- [ ] **Step 3: 实现渲染器**

在 `render_report.py` 顶部常量区（`SEVERITY_ORDER` 之后）加：

```python
STUCK_KINDS = {"no_entry": "无入口", "not_found": "找不到", "misleading": "误导",
               "no_feedback": "无反馈", "no_recovery": "无恢复路径", "broken": "系统报错"}
```

把 `_not_examined_line` 改成带前缀：

```python
def _not_examined_line(item, prefix=""):
    risk = item.get("risk") or {}
    level = risk.get("level")
    if level in SEVERITY_ORDER:
        tag = f"风险 {level}：{risk.get('why', '')}"
    else:
        tag = "未评估风险"
    name = f"{prefix}{item.get('name') or _journey_title(item)}"
    return f"- {name}（{item['id']}）— 未盘问，不计入任何完成度 · {tag}"
```

`_entry_line` 加旅程标签（`facet_tag` 之前）：

```python
def _entry_line(e):
    label = VERDICT_LABELS.get(e.get("verdict"), e.get("verdict"))
    jtag = f" [{e['journey']}]" if e.get("journey") else ""
    facet_tag = f" [{e.get('facet', '?')}]"
    ref = f" [{e['requirement_ref']}]" if e.get("requirement_ref") else ""
    ev = e.get("evidence", {})
    return (f"- **{label}**{jtag}{facet_tag}{ref} {e.get('q', '?')} — {ev.get('key_observation', '')}"
            f"（证据：{ev.get('dir', '')}）")
```

新增三个函数（放在 `_entry_line` 之后）：

```python
def _refusal_reason(e, journey_ids):
    verdict = e.get("verdict")
    if verdict not in VERDICT_LABELS:
        return f"非法裁决：{verdict}"
    if e.get("journey") and e["journey"] not in journey_ids:
        return f"旅程引用不存在：{e['journey']}"
    if e.get("journey") and verdict == "gap" and e.get("stuck_kind") not in STUCK_KINDS:
        return f"非法卡死类型：{e.get('stuck_kind')}"
    return "无证据目录"


def _journey_title(j):
    return (f"{j.get('id', '?')} {j.get('who', '?')} · {j.get('circumstance', '?')}"
            f" · {j.get('progress', '?')}")


def _journey_block(j, e):
    steps = e.get("steps", [])
    verdict = e.get("verdict")
    label = VERDICT_LABELS[verdict]
    ev = e.get("evidence", {})
    if verdict == "done":
        head = f"走通，{len(steps)} 步"
    elif verdict == "gap":
        label = f"{label}（{e.get('severity', '?')}，{STUCK_KINDS.get(e.get('stuck_kind'))}）"
        stuck = next((s for s in steps if s.get("status") == "stuck"), None)
        if stuck:
            head = (f"走了 {len(steps)} 步，卡在第 {stuck.get('n', '?')} 步："
                    f"{stuck.get('action', '')} → {stuck.get('observed', '')}")
        else:
            head = f"走了 {len(steps)} 步，预算内未到进展"
    elif verdict == "drift":
        label = f"{label}（{e.get('severity', '?')}）"
        head = "走通但绕过 waypoint：" + "、".join(e.get("missed_waypoints", []))
    else:
        head = f"无法自证：{ev.get('key_observation', '')}"
    out = ["", f"### {_journey_title(j)} — {label}",
           f"{head}（证据：{ev.get('dir', '')}）"]
    out.extend(f"- {s.get('n', '?')} {s.get('status', '?')} {s.get('action', '')}"
               f" → {s.get('observed', '')}" for s in steps)
    return out
```

改 `render()`：

采信循环替换为：

```python
    journeys = ledger.get("journeys") or []
    journey_ids = {j.get("id") for j in journeys}
    admitted, refused = [], []
    for e in ledger["entries"]:
        if _refusal_reason(e, journey_ids) != "无证据目录":
            refused.append(e)
        elif _has_evidence(e, run_dir):
            admitted.append(e)
        else:
            refused.append(e)
    plain = [e for e in admitted if not e.get("journey")]
    admitted_by_q = {e.get("q"): e for e in admitted}
    examined_j = [(j, admitted_by_q[j.get("entry_q")]) for j in journeys
                  if j.get("entry_q") in admitted_by_q
                  and admitted_by_q[j.get("entry_q")].get("journey") == j.get("id")]
    examined_j_ids = {j["id"] for j, _ in examined_j}
    unexamined_j = [j for j in journeys if j.get("id") not in examined_j_ids]
```

计数改为普通与旅程分开：

```python
    counts = {v: 0 for v in VERDICT_LABELS}
    for e in plain:
        counts[e["verdict"]] += 1
    jcounts = {v: 0 for v in VERDICT_LABELS}
    for _, e in examined_j:
        jcounts[e["verdict"]] += 1
```

头行与总览：

```python
    head = (f"需求基准：{ledger['baseline']} · 共 {len(ledger['facets'])} 面，"
            f"盘问 {len(examined)} 面 · 实测 {len(plain)} 问")
    if journeys:
        head += f" · 旅程 {len(journeys)} 条，盘问 {len(examined_j)} 条"
    out.append(head)
    out.append("")
    out.append("## 总览")
    out.append("")
    out.append(" · ".join(f"{VERDICT_LABELS[v]}：{counts[v]}" for v in VERDICT_LABELS))
    if journeys:
        out.append("旅程裁决：" + " · ".join(f"{VERDICT_LABELS[v]}：{jcounts[v]}"
                                          for v in VERDICT_LABELS))
```

逐面完成度里只列普通 entry：`fe = [e for e in plain if e.get("facet") == f["id"]]`。

逐面之后、缺口清单之前插入旅程节：

```python
    out.append("")
    out.append("## 旅程完成度")
    if examined_j:
        for j, e in examined_j:
            out.extend(_journey_block(j, e))
    else:
        out.append("（无旅程声明）" if not journeys else "（旅程均未盘问，见未盘问声明）")
```

缺口清单和无法自证清单继续用 `admitted`（含旅程 entry，行首自带 `[J1]`）。

未盘问声明合并面与旅程：

```python
    out.append("")
    out.append("## 未盘问声明（按风险排序）")
    unexamined_items = ([(f, "") for f in not_examined]
                        + [(j, "旅程 ") for j in unexamined_j])
    if unexamined_items:
        unexamined_items.sort(key=lambda it: _risk_key(it[0]))
        out.extend(_not_examined_line(it, prefix) for it, prefix in unexamined_items)
    else:
        out.append("（所有面均已盘问或部分盘问）")
```

patterns 节里已有的 `admitted_by_q` 定义删掉，复用上面的。

违规裁决段：

```python
        for e in refused:
            out.append(f"- {e.get('q', '?')}（{_refusal_reason(e, journey_ids)}）")
```

模块 docstring 追加一段：

```
可选 `journeys`（旅程声明）渲染为"旅程完成度"专节。旅程没有自报"已查"的通道：
`entry_q` 精确匹配到被采信 entry 且该 entry 的 `journey` 等于旅程 id 才算已盘问，
否则进"未盘问声明"（前缀"旅程"）并按 risk 排序。entry 带 `journey` 但 journeys 里
查无此 id、或旅程 gap 的 `stuck_kind` 不在六种之内，一律拒渲并点名。旅程裁决计数与
普通裁决计数分列，互不掺入。
```

- [ ] **Step 4: 跑全部渲染器测试**

Run: `cd claude/superstorm/scripts && python3 -m pytest test_render_report.py -q`
Expected: 全部 PASS，含原有用例（`test_not_examined_sorted_by_risk_with_why` 仍通过，因为面的行文案未变）。

- [ ] **Step 5: 提交**

```bash
git add claude/superstorm/scripts/render_report.py claude/superstorm/scripts/test_render_report.py
git commit -m "cross-exam: renderer reads journeys, separate journey verdict counts.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01WMtG82xCvdD6Q4BbWm5YXR"
```

---

### Task 2: Codex 渲染器移植

**Files:**
- Modify: `codex/cross-exam-skill/scripts/render_report.py`
- Test: `codex/cross-exam-skill/scripts/test_render_report.py`

**Interfaces:**
- Consumes: Task 1 的全部函数名与文案。
- Produces: 与 Claude 版行为一致，另保留 severity 校验。

- [ ] **Step 1: 复制 Task 1 的测试辅助与 `TestJourneys` 到 Codex 测试文件**

`_journey`、`_jentry`、`_with_journeys`、`TestJourneys` 原样追加（Codex 的 `_mk_run` 和 `_entry` 签名相同）。再加一个 Codex 专属用例到 `TestJourneys`：

```python
    def test_journey_gap_without_severity_is_refused_codex(self):
        with tempfile.TemporaryDirectory() as tmp:
            e = _jentry(verdict="gap", stuck_kind="no_feedback")   # 无 severity
            run = _mk_run(tmp, self.FACETS, [e])
            _with_journeys(run, [_journey()])
            report = render(run)
            self.assertIn("非法严重度：None", report)
            self.assertIn("旅程 1 条，盘问 0 条", report)
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd codex/cross-exam-skill/scripts && python3 -m pytest test_render_report.py -q -k Journeys`
Expected: 11 个 FAIL。

- [ ] **Step 3: 移植实现**

按 Task 1 Step 3 逐项修改 Codex 版，`_refusal_reason` 改为含 severity 校验：

```python
def _refusal_reason(e, journey_ids):
    verdict = e.get("verdict")
    if verdict not in VERDICT_LABELS:
        return f"非法裁决：{verdict}"
    if verdict in ("gap", "drift") and e.get("severity") not in SEVERITY_ORDER:
        return f"非法严重度：{e.get('severity')}"
    if e.get("journey") and e["journey"] not in journey_ids:
        return f"旅程引用不存在：{e['journey']}"
    if e.get("journey") and verdict == "gap" and e.get("stuck_kind") not in STUCK_KINDS:
        return f"非法卡死类型：{e.get('stuck_kind')}"
    return "无证据目录"
```

采信循环同 Task 1（`_refusal_reason(...) != "无证据目录"` 即拒），删掉原来的 severity 分支和违规段里的 if 链，统一走 `_refusal_reason`。

- [ ] **Step 4: 跑 Codex 全部测试**

Run: `cd codex/cross-exam-skill/scripts && python3 -m pytest -q`
Expected: 全部 PASS（含 `test_ledger_store.py`）。

- [ ] **Step 5: 提交**

```bash
git add codex/cross-exam-skill/scripts/render_report.py codex/cross-exam-skill/scripts/test_render_report.py
git commit -m "cross-exam (codex): renderer reads journeys, keeps severity guard.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01WMtG82xCvdD6Q4BbWm5YXR"
```

---

### Task 3: schemas.md 两个孪生版

**Files:**
- Modify: `claude/superstorm/knowledge/cross-exam/schemas.md`
- Modify: `codex/cross-exam-skill/schemas.md`

**Interfaces:**
- Produces: 文档化 `journeys[]`、entry 的 `journey/steps/terminal_state/stuck_kind/missed_waypoints`、红线第 4 条。Task 6 的协议文本引用这里的字段名。

- [ ] **Step 1: 在 ledger.json 示例的 `entries` 数组之后（`]` 之前的最后一个 entry 后）加一条旅程 entry 示例，并在顶层加 `journeys`**

在示例 JSON 的 `"entries": [ … ]` 后追加（两个文件同样，Codex 版的 entry 多一个 `"id": "stable UUID"`）：

```json
  "journeys": [
    {"id": "J1",
     "who": "回头客", "circumstance": "购物车里已有一件商品", "progress": "完成支付并拿到订单号",
     "preconditions": ["已登录测试账号", "购物车非空"],
     "waypoints": ["支付确认页"],
     "oracle": {"done_looks_like": ["URL 含 /orders/", "页面含订单号文本"],
                "stuck_looks_like": ["仍在 /cart", "出现 role=alert 的支付失败"]},
     "step_budget": 15,
     "status": "examined|not_examined",
     "risk": {"level": "high|medium|low", "why": "仅 not_examined：这份工作的分量 + 若真走不通的破坏面"},
     "entry_q": "J1 走得通吗？"}
  ]
```

- [ ] **Step 2: 在字段说明列表（`- 顶层可选 patterns` 之后）追加**

```markdown
- 顶层可选 `journeys`（旅程声明=用户口述的意图基线）：`who / circumstance / progress` 三元组与
  product-review 的 job 同格式；`oracle.done_looks_like` 与 `oracle.stuck_looks_like` 都必填非空，
  写不出 `stuck_looks_like` 的旅程不入台账；`waypoints` 可选，是用户点名必经的状态；`step_budget`
  必填，默认 15。**oracle 只给盘问官看，绝不进探针输入。**
  旅程的实证 entry 带 `journey: "J1"` 与 `steps[]`（每步 `{n, action, observed, status: done|stuck|could_not,
  evidence}`，`evidence` 是该 entry `evidence.dir` 下的文件名），web 目标另带 `terminal_state: {url, snapshot}`。
  旅程 `gap` 必填 `stuck_kind` ∈ `no_entry`（无入口）| `not_found`（找不到）| `misleading`（误导）|
  `no_feedback`（无反馈）| `no_recovery`（无恢复路径）| `broken`（系统报错）；旅程 `drift` 必填
  `missed_waypoints[]`。
  旅程**没有自报"已查"的通道**：`journeys[].entry_q` 精确匹配到一条被采信 entry 且该 entry 的
  `journey` 等于旅程 id 才算已盘问；`status` 字段照写但渲染器不看它。未盘问旅程按 `risk` 与未盘问面
  同列渲染，前缀"旅程"，不进任何计数。
```

- [ ] **Step 3: completion-report.md 顺序段落更新**

把"逐面完成度 … → 缺口清单" 改为 "逐面完成度（只含普通 entry）→ 旅程完成度（每条已盘问旅程：走通 N 步 / 卡在第 K 步加卡死类型 / 绕过的 waypoint / 无法自证原因，逐步状态列表）→ 缺口清单（含旅程 gap，行首 `[J1]`）"。总览一句补"旅程裁决计数与普通裁决计数分列"。

- [ ] **Step 4: 红线加第 4 条**

```markdown
4. 旅程同样没有自报"已查"的通道：`entry_q` 匹配不到被采信 entry 一律渲染为未盘问；entry 带
   `journey` 但 journeys 里查无此 id、或旅程 gap 的 `stuck_kind` 不在六种之内，拒渲并点名。
```

- [ ] **Step 5: 校验两个文件差异只在 UUID 处**

Run: `diff claude/superstorm/knowledge/cross-exam/schemas.md codex/cross-exam-skill/schemas.md`
Expected: 只有原有的 `schema_version`、`run_id`、`id: stable UUID`、`ledger_store.py` 段差异。

- [ ] **Step 6: 提交**

```bash
git add claude/superstorm/knowledge/cross-exam/schemas.md codex/cross-exam-skill/schemas.md
git commit -m "cross-exam: schema for journey declarations and step evidence.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01WMtG82xCvdD6Q4BbWm5YXR"
```

---

### Task 4: prober.md 两个孪生版

**Files:**
- Modify: `claude/superstorm/knowledge/cross-exam/prompts/prober.md`
- Modify: `codex/cross-exam-skill/prompts/prober.md`

**Interfaces:**
- Consumes: Task 3 的 `steps[]` 字段形状。
- Produces: 探针输入 `journey` 块 `{goal, preconditions, waypoints, step_budget}`；返回 `steps[]`、`terminal_state`、`could_not` 里的 `budget_exhausted` 字样。Task 6 的协议按这些名字派发和裁决。

- [ ] **Step 1: 输入合同加 `journey` 块**

把输入合同 JSON 改为：

```json
{"question": "...", "target": {"how_to_run": "...", "entry": "...", "type": "web|cli|api"},
 "states_to_capture": ["..."], "evidence_dir": ".../evidence/qNN/",
 "context_paths": ["可选：只读对账材料路径"],
 "journey": {"goal": "可选：作为<谁>，在<情景>下，<做成什么可观察的进展>",
             "preconditions": ["..."], "waypoints": ["..."], "step_budget": 15}}
```

- [ ] **Step 2: 纪律追加 7、8、9**

在纪律 6 之后追加：

```markdown
7. **旅程先记起点**（仅 `journey` 存在时）：动手前落盘起点状态，文件名 `qNN-00-start.*`——
   web：URL 加无障碍树快照文本；cli：工作目录与环境摘要；api：初始资源状态。前置条件造不出来
   → `could_not` 写清哪条造不出，不猜不绕。
8. **旅程逐步落证据**：每一步一条 `steps[]` 记录加一个证据文件（web 每步截图，终态另存无障碍树
   文本到 `terminal_state.snapshot`；cli 每步 stdout 文件；api 每步请求响应文件）。步骤不许合并，
   "没变化"的步也要记。`observed` 写你看到的，不写你以为的。
9. **步数用尽即停**：`step_budget` 用完还没到 `goal` 描述的进展，停下，`could_not` 写
   `budget_exhausted: 走了 N 步，最后停在 <状态>`，已走的 steps 全部返回。不重试，不换路绕。
   你不知道"做成"长什么样是有意的：到了就到了，到不了就如实记。
```

- [ ] **Step 3: 返回 JSON 加字段**

```json
{"steps_taken": ["..."], "observations": ["..."], "exit_codes": {"cmd": 0},
 "output_excerpts": ["..."], "screenshots": ["evidence_dir 下的文件名"],
 "could_not": ["测不了的部分 + 原因（无则空数组）"],
 "steps": [{"n": 1, "action": "...", "observed": "...", "status": "done|stuck|could_not", "evidence": "文件名"}],
 "terminal_state": {"url": "web 才有", "snapshot": "终态无障碍树文件名（web）或最后输出文件名"}}
```

加一行说明："`steps` 与 `terminal_state` 仅旅程输入时必填，其余问题省略。"

- [ ] **Step 4: 两个文件保持完全相同**

Run: `diff claude/superstorm/knowledge/cross-exam/prompts/prober.md codex/cross-exam-skill/prompts/prober.md && echo identical`
Expected: `identical`

- [ ] **Step 5: 提交**

```bash
git add claude/superstorm/knowledge/cross-exam/prompts/prober.md codex/cross-exam-skill/prompts/prober.md
git commit -m "cross-exam: prober walks journeys step by step within a budget, never sees the oracle.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01WMtG82xCvdD6Q4BbWm5YXR"
```

---

### Task 5: lenses.md 旅程镜头

**Files:**
- Modify: `claude/superstorm/knowledge/cross-exam/lenses.md`
- Modify: `codex/cross-exam-skill/lenses.md`

- [ ] **Step 1: 镜头表加一行（契约 census 行之后）**

```markdown
| 旅程 | 三元组 ↔ 界面入口与终态 | 任务清单里的工作在导航里找不到入口；成功后页面没有下一步；失败态没有返回主线的按钮；"提交"后按钮变灰但无任何状态文本 |
```

- [ ] **Step 2: 在"契约 census 与前四镜头不同"段之后加一段**

```markdown
**旅程镜头不出问题牌**：旅程的问题固定是"J 走得通吗"，用户在 §1b 已经选过；这个镜头的用处是
旅程 gap 之后的纵向发散——卡死点周围还有哪些泄漏点（同一状态的其它出口、反向操作、错误恢复），
以及多条旅程在同一种 `stuck_kind` 卡死时提示"孤例还是一类"。
```

- [ ] **Step 3: 校验两文件相同并提交**

Run: `diff claude/superstorm/knowledge/cross-exam/lenses.md codex/cross-exam-skill/lenses.md && echo identical`
Expected: `identical`

```bash
git add claude/superstorm/knowledge/cross-exam/lenses.md codex/cross-exam-skill/lenses.md
git commit -m "cross-exam: journey lens.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01WMtG82xCvdD6Q4BbWm5YXR"
```

---

### Task 6: 协议文本（cross-exam.md 与 Codex SKILL.md）

**Files:**
- Modify: `claude/superstorm/skills/cross-exam.md`
- Modify: `codex/cross-exam-skill/SKILL.md`
- Modify: `codex/cross-exam-skill/AGENTS.md:10`

**Interfaces:**
- Consumes: Task 3 字段名、Task 4 探针输入块与返回字段。

- [ ] **Step 1: description 补一句（两个文件）**

Claude 版 frontmatter `description:` 在 "Generic — works on any delivery" 之前插入：`Accepts user-declared journeys (who / circumstance / progress + oracle) and walks each one end-to-end with a fresh-context prober.`

Codex 版 frontmatter `description:` 里 "cross-exam — evidence-backed completion cross-examination" 后加 `, including user-declared journeys walked end-to-end`。

Codex `AGENTS.md` 第 10 行末尾加一句：`Users may declare journeys (who / circumstance / progress with an oracle); each is walked end-to-end by a fresh-context prober and judged against the oracle by the examiner.`

- [ ] **Step 2: 在 §1 定面末尾（"渲染器会在总览点明。"之后）插入 §1b**

Claude 版：

```markdown
## 1b. 旅程采集（定面之后，盘问循环之前）

旅程 = 用户声明的意图基线：`who / circumstance / progress` 三元组（与 product-review 的 job 同格式）
加 oracle。它回答"这份工作在这个交付里走不走得通"，是 product-review "在不在、走不走得完"两问的
独立取证来源。

1. **整理候选**：把 census 的操作面按"入口 → 能推进到的终态"归成候选旅程，加上需求基准里的任务
   （registry、spec、README；`.allforai/product-map/task-inventory.json` 存在也读，它只是可选数据源）。
   每条候选写成三元组草稿。**不另派 agent 读代码，也不凭印象读代码定候选**——census 已经用覆盖法
   列过入口了。
2. **摆给用户**：AskUserQuestion 多选，勾选要盘的候选；用户永远可以走 Other 补自己的旅程。零勾选
   零补充不阻塞：ledger 写 `journeys: []`，报告声明"无旅程声明"。
3. **改写读回**：每条选中的旅程改写成三元组加 oracle（`done_looks_like` + `stuck_looks_like`），读
   回用户确认。一轮改写后仍无 `who` 或 `progress` 的不是旅程——说明缺哪部分，用户补一次，仍缺就
   不收。`stuck_looks_like` 空的同样退回补一次："没报错"不是 oracle，要写出卡死长什么样。
4. **落盘**：确认的旅程写入 `journeys[]`，`status: not_examined`，带 `risk`（这份工作的分量 + 若真走
   不通的破坏面）。未选的候选不入台账。`step_budget` 默认 15，按旅程长度调。
```

Codex 版同文，第 2 条改为："一次只问用户一个选择，逐条确认要盘的候选；用户永远可以补自己的旅程。"

- [ ] **Step 3: §2 盘问循环加旅程轮**

在 "两种模式，按目标选" 段之后、"- **问题牌**" 之前插入：

```markdown
**旅程轮（用户选中一条旅程时）**：不出三张牌，问题固定是"`<id>` 走得通吗？"。

- **派实测官**：输入 JSON 加 `journey` 块——只含 `goal`（三元组拼成一句话）、`preconditions`、
  `waypoints`、`step_budget`；`states_to_capture` 写"起点"、各 waypoint、"终态"。**oracle 绝不进
  输入**：探针不知道"做成"长什么样，到了就到了，到不了就如实记——这是旅程版的期望隔离。
- **收证据**：把 `steps[]` 和终态截图给用户看。
- **裁决**（对着 `journeys[].oracle`）：
  `done` = `done_looks_like` 全部命中、`stuck_looks_like` 无一命中、每个 waypoint 都在某步
  `observed` 里出现过；
  `gap` = 任一 `stuck_looks_like` 命中，或探针 `could_not` 含 `budget_exhausted`，或任一步 `stuck`；
  必填 `stuck_kind`（no_entry 无入口 / not_found 找不到 / misleading 误导 / no_feedback 无反馈 /
  no_recovery 无恢复路径 / broken 系统报错）与 severity；
  `drift` = 终态满足 `done_looks_like` 但绕过了某个 waypoint，必填 `missed_waypoints`；
  `unprovable` = 前置条件造不出来，或探针因环境原因 `could_not`（起不来、缺依赖、缺浏览器）。
  预算用尽不是 unprovable：预算内到不了进展是产品的问题。
- **落账**：entry 带 `journey`、`steps`、`terminal_state`；`journeys[].entry_q` 指到该 entry 的 `q`，
  `status` 改 `examined`。
- **扫全模式下**：所有 `not_examined` 旅程并行扇出，一条旅程一个 fresh-context 实测官，收齐后逐条裁决。
- **发散与 bias-guard 照旧**：旅程 gap 后下一轮从卡死点纵向出牌进 `open_threads`；多条旅程在同一种
  `stuck_kind` 卡死，走"孤例还是一类"建 pattern；盘问官==作者时旅程 gap 从严。
```

Codex 版同文（派发方式沿用其 `spawn_agent` 措辞）。

- [ ] **Step 4: §3 收敛出报告一句补旅程**

"报告四类裁决计数、逐面…" 改为 "报告四类裁决计数（普通与旅程分列）、逐面"X 问中 Y 问实证通过"、旅程完成度（每条走通 N 步或卡在第 K 步加卡死类型）、缺口清单…"。

- [ ] **Step 5: 校验 skill 文件引用与提交**

Run: `cd claude/superstorm/scripts && python3 check_skill_refs.py 2>&1 | tail -3`
Expected: 无错误（脚本存在时）。若脚本要求参数，按其 `--help`。

```bash
git add claude/superstorm/skills/cross-exam.md codex/cross-exam-skill/SKILL.md codex/cross-exam-skill/AGENTS.md
git commit -m "cross-exam: journey intake after census, journey round in the loop.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01WMtG82xCvdD6Q4BbWm5YXR"
```

---

### Task 7: product-review 认 J 编号

**Files:**
- Modify: `claude/superstorm/skills/product-review.md:76,102,132-133`
- Modify: `codex/cross-exam-skill/product-review.md`（对应段落）

- [ ] **Step 1: Prior evidence 段改写**

把第 76 行段落改为：

```markdown
**Prior evidence.** If `docs/cross-exam/*/completion-report.md` exists, read the newest one. Its gap list and its 旅程完成度 section are prior evidence: for each gap (`G` id) or journey verdict (`J` id) that blocks a job in scope, list it on the `Prior evidence` line with that job. A journey that cross-exam walked through (`done`) is evidence for 在不在 and 走不走得完 on the matching job; a journey `gap` with its `stuck_kind` is the observation, do not re-probe it. A known gap or blocked journey never becomes an `R` item; items that wait on it write its id in `depends_on` (`G1`, `J1`). Absent → write `Prior evidence: none`.
```

- [ ] **Step 2: `depends_on` 行与模板行**

第 102 行：`- \`depends_on\` other \`R\` ids, cross-exam \`G\` or \`J\` ids, or empty`

模板第 133 行：`docs/cross-exam/<run>/completion-report.md — G1 blocks J1; J2 (gap, no_feedback) blocks J1; G2, G3 no job in scope | none`

注意：模板里 product-review 自己的 job 也用 `J1` 编号。为避免与 cross-exam 的旅程 id 撞名，把 product-review 的 job 编号前缀改为 `JOB1`：在 Jobs in scope 模板、Decision tree 的 `job: J1`、Prior evidence 示例、"No item survived" 示例中全部替换 `J1` → `JOB1`。改完 grep 确认文件内不再有裸的 `J1` 指 job。

- [ ] **Step 3: Codex 版同样改动，diff 确认两版只差平台措辞**

Run: `diff claude/superstorm/skills/product-review.md codex/cross-exam-skill/product-review.md`
Expected: 仅原有的平台差异（AskUserQuestion 等）。

- [ ] **Step 4: 提交**

```bash
git add claude/superstorm/skills/product-review.md codex/cross-exam-skill/product-review.md
git commit -m "product-review: consume cross-exam journey verdicts as prior evidence; job ids become JOBn.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01WMtG82xCvdD6Q4BbWm5YXR"
```

---

### Task 8: 版本、CLAUDE.md、发布检查

**Files:**
- Modify: `claude/superstorm/.claude-plugin/plugin.json:5`
- Modify: `claude/superstorm/.claude-plugin/marketplace.json:9`
- Modify: `CLAUDE.md:207`

- [ ] **Step 1: 版本 0.22.0 → 0.23.0 两处**

```bash
sed -i '' 's/"version": "0.22.0"/"version": "0.23.0"/' claude/superstorm/.claude-plugin/plugin.json claude/superstorm/.claude-plugin/marketplace.json
grep -n '"version"' claude/superstorm/.claude-plugin/plugin.json claude/superstorm/.claude-plugin/marketplace.json
```

Expected: 两处均 `0.23.0`。

- [ ] **Step 2: CLAUDE.md 第 207 行 cross-exam 行的 Why 列末尾加**

`; user-declared journeys walked end-to-end and judged against an oracle`

- [ ] **Step 3: 全量测试**

```bash
cd claude/superstorm/scripts && python3 -m pytest -q
cd ../../../codex/cross-exam-skill/scripts && python3 -m pytest -q
```

Expected: 全部 PASS。

- [ ] **Step 4: 提交**

```bash
git add claude/superstorm/.claude-plugin/plugin.json claude/superstorm/.claude-plugin/marketplace.json CLAUDE.md
git commit -m "superstorm 0.23.0: cross-exam journey declarations.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01WMtG82xCvdD6Q4BbWm5YXR"
```

---

### Task 9: 思维测试（skill 文本的失败场景）

**Files:**
- Read: `claude/superstorm/skills/cross-exam.md`、`claude/superstorm/knowledge/cross-exam/prompts/prober.md`、`schemas.md`
- Create: `docs/superpowers/plans/2026-09-05-cross-exam-journey-thought-tests.md`（记录结果）

每个场景派一个 fresh-context `Agent(general-purpose)`，prompt 只给：cross-exam.md 全文、prober.md 全文、schemas.md 全文、场景描述、要求"按 skill 文本说明你下一步会做什么，引用具体条文"。不给期望答案。判定标准写在下面，由主会话对照。

- [ ] **Step 1: 场景 A，oracle 泄漏**

场景：盘问官准备派旅程探针，草拟的输入 JSON 里 `journey` 块含 `"oracle": {...}`。问：这份输入能发吗？
通过判据：agent 指出 oracle 不进探针输入，引用 §2 旅程轮"oracle 绝不进输入"，并给出去掉后的 JSON。

- [ ] **Step 2: 场景 B，缺 stuck_looks_like**

场景：用户口述"回头客要能结账"，盘问官改写后 `stuck_looks_like` 为空。问：下一步？
通过判据：退回用户补一次，引用 §1b 第 3 条；不入台账。

- [ ] **Step 3: 场景 C，零旅程**

场景：候选列了 4 条，用户一条不勾也不补。问：cross-exam 还跑吗？ledger 怎么写？
通过判据：继续跑，`journeys: []`，报告"无旅程声明"。

- [ ] **Step 4: 场景 D，cli 旅程**

场景：目标是一个 CLI 工具，旅程"数据工程师在空目录里初始化项目并成功跑通第一次同步"。问：探针怎么取证？
通过判据：命令序列，每步 stdout 文件，起点记工作目录与环境摘要，引用纪律 7、8。

- [ ] **Step 5: 场景 E，预算用尽**

场景：探针返回 `could_not: ["budget_exhausted: 走了 15 步，最后停在 /checkout/pay"]`，steps 里无 `stuck`。问：裁决是什么？要不要重派？
通过判据：`gap`，不是 `unprovable`；不重派；`stuck_kind` 按 steps 的最后观察定；引用"预算用尽不是 unprovable"。

- [ ] **Step 6: 场景 F，作者自审的旅程 gap**

场景：`examiner_is_author: true`，旅程 gap，盘问官想判 low。问：可以吗？
通过判据：需要额外独立证据，引用 bias-guard。

- [ ] **Step 7: 记录与修正**

把六个场景的 agent 回答摘要与判定写入 `docs/superpowers/plans/2026-09-05-cross-exam-journey-thought-tests.md`。任一场景不通过 → 修 skill 文本对应条文，重跑该场景，直到通过。提交：

```bash
git add docs/superpowers/plans/2026-09-05-cross-exam-journey-thought-tests.md claude/superstorm codex/cross-exam-skill
git commit -m "cross-exam: journey thought tests and wording fixes.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01WMtG82xCvdD6Q4BbWm5YXR"
```

---

## Self-review

**Spec coverage**：数据模型 → Task 1/2/3；§1b → Task 6；旅程轮与裁决 → Task 6；prober 变更 → Task 4；镜头 → Task 5；渲染八条 → Task 1/2（1 缺省、2 拒渲、3 判定、4 计数、5 节、6 未盘问、7 标签、8 红线均有测试或代码）；product-review → Task 7；Codex 孪生 → 每个 Task 都双写；description 与 CLAUDE.md → Task 6/8；渲染器测试九项 → Task 1 十个用例覆盖（含 unprovable 额外一项）；思维测试六场景 → Task 9。

**Spec 之外的补充**：product-review 自己的 job 编号从 `J1` 改成 `JOB1`，避免与 cross-exam 旅程 id 撞名（Task 7）。spec 未提及，属实现时发现的命名冲突。

**类型一致性**：`STUCK_KINDS`、`_refusal_reason(e, journey_ids)`、`_journey_title(j)`、`_journey_block(j, e)`、`_not_examined_line(item, prefix="")` 在 Task 1、2 一致；entry 字段 `journey / steps / terminal_state / stuck_kind / missed_waypoints` 在 Task 1 测试、Task 3 schema、Task 4 prober、Task 6 协议一致；探针输入 `journey.{goal, preconditions, waypoints, step_budget}` 在 Task 4 与 Task 6 一致。
