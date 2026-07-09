# cross-exam 实证完成度盘问技能 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新建独立通用插件 `claude/cross-exam` v0.1.0（苏格拉底式实证完成度盘问），附带 megastorm Phase 2 一句邀请（patch bump 0.11.1）。

**Architecture:** 盘问官（主会话 skill）与实测官（fresh-context 子 agent，prompts/prober.md）硬分离；证据逐问落盘；完成度报告由确定性脚本 `render_report.py` 从 `ledger.json` 渲染，诚实性红线写死在脚本里。

**Tech Stack:** Claude Code plugin（markdown skill + commands）、Python 3 标准库（脚本零依赖）、unittest。

**Spec:** `docs/superpowers/specs/2026-07-09-cross-exam-design.md`（所有行为定义以 spec 为准）。

## Global Constraints

- **通用性**：技能本体零项目痕迹、零技术栈硬编码；megastorm 只是可选数据源之一（spec §2）。
- **只记账不修**；**只在有人在场时运行**（无人值守不盘）（spec §2）。
- **每问必落证据目录，无一例外**：`could_not` 落原因文件；读代码介质落"路径+行号+原文引用"摘录文件（spec §6.6）。
- **实测官期望隔离**：输入仅 spec §6 的 JSON 合同（含可选 `context_paths`，只传路径不传解读）；禁止对项目源码 Edit/Write，唯一可写路径 `evidence_dir`（spec §6.7）。
- **诚实性红线在脚本**：`not_examined` 面不进统计；无证据 entry 拒渲（spec §7）。
- **版本**：新插件 0.1.0 三处一致（plugin.json / marketplace.json / skills/cross-exam.md frontmatter）；megastorm 0.11.0 → 0.11.1 两处 manifest。
- 文档/skill 正文语言：中文为主、术语英文，风格对齐 `claude/megastorm/skills/megastorm.md`。
- python 脚本测试跑法：`cd claude/cross-exam/scripts && python3 test_render_report.py`。

---

### Task 1: 插件脚手架 + manifest + 斜杠入口 + install.sh 接线

**Files:**
- Create: `claude/cross-exam/.claude-plugin/plugin.json`
- Create: `claude/cross-exam/.claude-plugin/marketplace.json`
- Create: `claude/cross-exam/commands/cross-exam.md`
- Modify: `claude/install.sh`（插件循环一行）

**Interfaces:**
- Produces: 目录骨架 `claude/cross-exam/{.claude-plugin,commands,skills,knowledge/prompts,scripts}`；后续任务只往里放文件。

- [ ] **Step 1: 写 plugin.json**

```json
{
  "name": "cross-exam",
  "description": "Evidence-backed completion cross-examination: Socratic question cards from leak points, fresh-context probers test the delivery themselves (code / runtime+screenshots / ledger), deterministic completion report. Audit-only, interactive-only. Global command /cross-exam.",
  "version": "0.1.0",
  "author": { "name": "dv" }
}
```

- [ ] **Step 2: 写 marketplace.json**

```json
{
  "name": "cross-exam",
  "owner": {
    "name": "dv"
  },
  "plugins": [
    {
      "name": "cross-exam",
      "version": "0.1.0",
      "source": "./",
      "description": "Socratic completion cross-examination producing an evidence-backed completion report. Explicit /cross-exam trigger."
    }
  ]
}
```

- [ ] **Step 3: 写 commands/cross-exam.md**

```markdown
---
name: cross-exam
description: 对"自称完成"的交付做实证盘问，产出带证据的完成度报告（只记账不修）。
arguments:
  - name: target
    description: 被盘问的交付物/项目（可留空，进入定靶对话）
    required: false
---

Invoke the cross-exam skill to cross-examine the delivery: $ARGUMENTS

> Read ${CLAUDE_PLUGIN_ROOT}/skills/cross-exam.md and follow its protocol, starting at 定靶 (intake).
```

- [ ] **Step 4: install.sh 插件循环加 cross-exam**

`claude/install.sh` 中：

```bash
  for plugin in meta-skill megastorm; do
```

改为：

```bash
  for plugin in meta-skill megastorm cross-exam; do
```

- [ ] **Step 5: 验证**

Run: `python3 -c "import json;[json.load(open(p)) for p in ['claude/cross-exam/.claude-plugin/plugin.json','claude/cross-exam/.claude-plugin/marketplace.json']];print('JSON-OK')" && bash -n claude/install.sh && echo SH-OK`
Expected: `JSON-OK` 和 `SH-OK`

- [ ] **Step 6: Commit**

```bash
git add claude/cross-exam claude/install.sh
git commit -m "feat(cross-exam): plugin scaffold, manifests, /cross-exam entry, install wiring"
```

---

### Task 2: schemas.md + render_report.py（TDD，红线在代码里）

**Files:**
- Create: `claude/cross-exam/knowledge/schemas.md`
- Create: `claude/cross-exam/scripts/test_render_report.py`
- Create: `claude/cross-exam/scripts/render_report.py`

**Interfaces:**
- Consumes: 无（本任务定义合同）。
- Produces: `ledger.json` schema（target/baseline/facets/entries，见 Step 1）；CLI `python3 render_report.py <run_dir>`：读 `<run_dir>/ledger.json`，写 `<run_dir>/completion-report.md`，退出码 0（拒渲仍为 0，报告内声明）/ 1（ledger 不可读或缺必填键）。函数 `render(run_dir: Path) -> str` 返回完整 markdown（供测试断言）。verdict 机器值 `done|gap|drift|unprovable`，中文标签 实证完成/缺口/跑偏/无法自证。

- [ ] **Step 1: 写 knowledge/schemas.md**

````markdown
# cross-exam — ledger 与报告结构

## ledger.json（盘问官逐问实时落盘，中断不丢）

```json
{
  "target": "被盘问对象（人类可读名）",
  "baseline": "megastorm-registry|spec|readme|user|none",
  "started": "YYYY-MM-DD",
  "facets": [
    {"id": "F1", "name": "退款流程", "status": "examined|partial|not_examined"}
  ],
  "entries": [
    {
      "q": "同一笔订单退两次会怎样？",
      "facet": "F1",
      "leak_point": "接口返回无幂等键，测试名单里无 duplicate 字样",
      "medium": "runtime|code|ledger",
      "evidence": {
        "dir": "evidence/q03/",
        "files": ["q03-01-first-refund.png", "q03-02-second-refund.png"],
        "key_observation": "第二次退款返回 200 且重复扣减"
      },
      "verdict": "done|gap|drift|unprovable",
      "requirement_ref": "R-09（可选）",
      "severity": "high|medium|low（仅 gap|drift；done/unprovable 不带）"
    }
  ]
}
```

- `evidence.dir` 相对 run 目录；**每个 entry 必有非空 evidence 目录**（spec §6.6）：
  runtime → 截图/输出文件；code → 摘录文件（路径+行号+原文引用）；ledger → 对账摘录；
  `could_not`/无法自证 → 原因文件（尝试了什么、卡在哪）。
- verdict 语义：`done` 实证完成 / `gap` 缺口（实测打脸）/ `drift` 跑偏（做了但不是需求
  的意思）/ `unprovable` 无法自证（需真设备/人工，如实挂账不猜）。

## completion-report.md（仅由 scripts/render_report.py 渲染，禁止口述生成）

依次：总览（面/问/四类裁决计数；baseline=none 时声明关闭的镜头）→ 逐面完成度
（"X 问中 Y 问实证通过"，逐条链证据）→ 缺口清单（gap+drift 按 severity 排）→
无法自证清单 → 未盘问声明（not_examined 面）→ 拒渲声明（如有）。

## 诚实性红线（写死在 render_report.py，不是嘱咐）

1. `not_examined` 的面不进任何完成度统计，只进未盘问声明；
2. 无 evidence 目录（缺 key / 目录不存在 / 目录为空）的 entry 拒绝渲染进正文与计数，
   在"违规裁决"段落点名——合法裁决必有证据（含 could_not 原因文件），被拒的只可能是
   绕过实测的口头裁决。
````

- [ ] **Step 2: 写失败测试 test_render_report.py**

```python
# claude/cross-exam/scripts/test_render_report.py
import json
import tempfile
import unittest
from pathlib import Path

from render_report import render


def _mk_run(tmp, facets, entries, baseline="spec", make_evidence=True):
    run = Path(tmp)
    for e in entries:
        d = e.get("evidence", {}).get("dir")
        if d and make_evidence:
            p = run / d
            p.mkdir(parents=True, exist_ok=True)
            (p / "note.txt").write_text("evidence", encoding="utf-8")
    (run / "ledger.json").write_text(json.dumps({
        "target": "demo", "baseline": baseline, "started": "2026-07-09",
        "facets": facets, "entries": entries}, ensure_ascii=False), encoding="utf-8")
    return run


def _entry(q, facet="F1", verdict="done", ev_dir="evidence/q1/", severity=None):
    e = {"q": q, "facet": facet, "leak_point": "lp", "medium": "runtime",
         "evidence": {"dir": ev_dir, "files": [], "key_observation": "obs"},
         "verdict": verdict}
    if severity:
        e["severity"] = severity
    return e


class TestRedLines(unittest.TestCase):
    def test_entry_without_evidence_dir_is_refused(self):
        # 两条 entry：一条有证据、一条 evidence.dir 指向不存在的目录 → 后者被拒渲：
        # 不进计数，出现在"违规裁决"段。
        with tempfile.TemporaryDirectory() as tmp:
            good = _entry("q-good", ev_dir="evidence/q1/")
            bad = _entry("q-oral", ev_dir="evidence/q2/")
            run = _mk_run(tmp, [{"id": "F1", "name": "面一", "status": "examined"}],
                          [good, bad])
            # 只给 q1 建证据目录，q2 的目录不存在
            import shutil
            shutil.rmtree(run / "evidence/q2", ignore_errors=True)
            report = render(run)
            self.assertIn("q-good", report)
            self.assertIn("违规裁决", report)
            self.assertIn("q-oral", report)
            self.assertIn("实证完成：1", report)  # bad 不进计数

    def test_empty_evidence_dir_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            e = _entry("q-empty", ev_dir="evidence/q1/")
            run = _mk_run(tmp, [{"id": "F1", "name": "面一", "status": "examined"}],
                          [e], make_evidence=False)
            (run / "evidence/q1").mkdir(parents=True)  # 存在但为空
            report = render(run)
            self.assertIn("违规裁决", report)
            self.assertIn("实证完成：0", report)

    def test_not_examined_facet_excluded_from_stats(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = _mk_run(tmp, [
                {"id": "F1", "name": "面一", "status": "examined"},
                {"id": "F2", "name": "面二", "status": "not_examined"}],
                [_entry("q1")])
            report = render(run)
            self.assertIn("盘问 1 面", report)      # F2 不计
            self.assertIn("未盘问声明", report)
            self.assertIn("面二", report)


class TestRendering(unittest.TestCase):
    def test_verdict_counts_and_facet_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            entries = [
                _entry("q1", verdict="done", ev_dir="evidence/q1/"),
                _entry("q2", verdict="gap", ev_dir="evidence/q2/", severity="high"),
                _entry("q3", verdict="unprovable", ev_dir="evidence/q3/"),
            ]
            run = _mk_run(tmp, [{"id": "F1", "name": "面一", "status": "examined"}],
                          entries)
            report = render(run)
            self.assertIn("实证完成：1", report)
            self.assertIn("缺口：1", report)
            self.assertIn("无法自证：1", report)
            self.assertIn("3 问中 1 问实证通过", report)

    def test_gap_list_sorted_by_severity(self):
        with tempfile.TemporaryDirectory() as tmp:
            entries = [
                _entry("q-low", verdict="gap", ev_dir="evidence/q1/", severity="low"),
                _entry("q-high", verdict="drift", ev_dir="evidence/q2/", severity="high"),
            ]
            run = _mk_run(tmp, [{"id": "F1", "name": "面一", "status": "examined"}],
                          entries)
            report = render(run)
            self.assertLess(report.index("q-high"), report.index("q-low"))

    def test_baseline_none_declares_closed_lenses(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = _mk_run(tmp, [{"id": "F1", "name": "面一", "status": "examined"}],
                          [_entry("q1")], baseline="none")
            report = render(run)
            self.assertIn("需求覆盖", report)
            self.assertIn("无基准", report)

    def test_missing_required_key_exits(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp)
            (run / "ledger.json").write_text('{"target": "x"}', encoding="utf-8")
            with self.assertRaises(SystemExit):
                render(run)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: 跑测试确认失败**

Run: `cd claude/cross-exam/scripts && python3 test_render_report.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'render_report'`

- [ ] **Step 4: 写 render_report.py**

```python
#!/usr/bin/env python3
"""cross-exam 完成度报告渲染器（确定性，禁止口述生成报告）。

诚实性红线在这里、在代码里，不在嘱咐里：
- status=="not_examined" 的面不进任何完成度统计，只进"未盘问声明"；
- 无证据 entry（缺 evidence.dir / 目录不存在 / 目录为空）拒绝渲染进正文与计数，
  在"违规裁决"段点名。合法裁决必有证据（could_not 也要落原因文件），被拒的
  只可能是绕过实测的口头裁决。

Usage: python3 render_report.py <run_dir>    # run_dir 内含 ledger.json
写出 <run_dir>/completion-report.md。exit 0=渲染成功（有拒渲仍为 0，报告内声明）；
exit 1=ledger 不可读或缺必填键。
"""
import json
import sys
from pathlib import Path

VERDICT_LABELS = {"done": "实证完成", "gap": "缺口",
                  "drift": "跑偏", "unprovable": "无法自证"}
SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}
BASELINE_NONE_NOTE = ("需求基准缺失（baseline: none）：需求覆盖、需求跑偏两镜头"
                      "因无基准关闭，本报告未盘问这两个维度。")


def _load(run_dir):
    path = run_dir / "ledger.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise SystemExit(f"ledger unreadable: {path}: {e}")
    for key in ("target", "baseline", "facets", "entries"):
        if key not in data:
            raise SystemExit(f"ledger missing required key: {key}")
    return data


def _has_evidence(entry, run_dir):
    d = (entry.get("evidence") or {}).get("dir")
    if not d:
        return False
    p = Path(d) if Path(d).is_absolute() else run_dir / d
    return p.is_dir() and any(p.iterdir())


def _entry_line(e):
    label = VERDICT_LABELS.get(e.get("verdict"), e.get("verdict"))
    ref = f" [{e['requirement_ref']}]" if e.get("requirement_ref") else ""
    ev = e.get("evidence", {})
    return (f"- **{label}**{ref} {e['q']} — {ev.get('key_observation', '')}"
            f"（证据：{ev.get('dir', '')}）")


def render(run_dir):
    run_dir = Path(run_dir)
    ledger = _load(run_dir)
    admitted, refused = [], []
    for e in ledger["entries"]:
        (admitted if _has_evidence(e, run_dir) else refused).append(e)

    examined = [f for f in ledger["facets"] if f.get("status") != "not_examined"]
    not_examined = [f for f in ledger["facets"] if f.get("status") == "not_examined"]
    counts = {v: 0 for v in VERDICT_LABELS}
    for e in admitted:
        if e.get("verdict") in counts:
            counts[e["verdict"]] += 1

    out = [f"# 完成度报告 — {ledger['target']}", ""]
    out.append(f"需求基准：{ledger['baseline']} · 共 {len(ledger['facets'])} 面，"
               f"盘问 {len(examined)} 面 · 实测 {len(admitted)} 问")
    out.append("")
    out.append("## 总览")
    out.append("")
    out.append(" · ".join(f"{VERDICT_LABELS[v]}：{counts[v]}" for v in VERDICT_LABELS))
    if ledger["baseline"] == "none":
        out.append("")
        out.append(f"> {BASELINE_NONE_NOTE}")

    out.append("")
    out.append("## 逐面完成度")
    for f in examined:
        fe = [e for e in admitted if e.get("facet") == f["id"]]
        done = sum(1 for e in fe if e.get("verdict") == "done")
        out.append("")
        out.append(f"### {f['name']}（{f['id']}）— {len(fe)} 问中 {done} 问实证通过")
        out.extend(_entry_line(e) for e in fe)

    gaps = [e for e in admitted if e.get("verdict") in ("gap", "drift")]
    gaps.sort(key=lambda e: SEVERITY_ORDER.get(e.get("severity"), 3))
    out.append("")
    out.append("## 缺口清单（按严重度）")
    out.extend(f"- **{e.get('severity', '?')}** {_entry_line(e)[2:]}" for e in gaps) \
        if gaps else out.append("（无）")

    unprov = [e for e in admitted if e.get("verdict") == "unprovable"]
    out.append("")
    out.append("## 无法自证清单（待人工验证，不计为完成也不计为失败）")
    out.extend(_entry_line(e) for e in unprov) if unprov else out.append("（无）")

    out.append("")
    out.append("## 未盘问声明")
    if not_examined:
        out.extend(f"- {f['name']}（{f['id']}）— 未盘问，不计入任何完成度"
                   for f in not_examined)
    else:
        out.append("（所有面均已盘问或部分盘问）")

    if refused:
        out.append("")
        out.append("## 违规裁决（无证据，已拒渲）")
        out.append(f"以下 {len(refused)} 条 entry 无有效证据目录，"
                   "不计入任何统计：")
        out.extend(f"- {e.get('q', '?')}" for e in refused)

    out.append("")
    return "\n".join(out)


def main(argv):
    if len(argv) != 2:
        raise SystemExit(__doc__)
    run_dir = Path(argv[1])
    report = render(run_dir)
    (run_dir / "completion-report.md").write_text(report, encoding="utf-8")
    print(f"wrote {run_dir / 'completion-report.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

注意 `out.extend(...) if gaps else out.append("（无）")` 这种三元表达式副作用写法在
Python 合法但丑：实现时展开成普通 if/else（两处：缺口清单、无法自证清单）。

- [ ] **Step 5: 跑测试确认通过**

Run: `cd claude/cross-exam/scripts && python3 test_render_report.py`
Expected: `OK`（7 tests）

- [ ] **Step 6: Commit**

```bash
git add claude/cross-exam/knowledge/schemas.md claude/cross-exam/scripts/
git commit -m "feat(cross-exam): ledger schema + deterministic report renderer with honesty red lines (TDD)"
```

---

### Task 3: knowledge/lenses.md + knowledge/prompts/prober.md

**Files:**
- Create: `claude/cross-exam/knowledge/lenses.md`
- Create: `claude/cross-exam/knowledge/prompts/prober.md`

**Interfaces:**
- Consumes: schemas.md 的 evidence 落盘约定（Task 2）。
- Produces: 盘问官 skill（Task 4）引用 `$ROOT/knowledge/lenses.md`（扫泄漏点）与 `$ROOT/knowledge/prompts/prober.md`（派实测官）。实测官返回 JSON：`{steps_taken, observations, exit_codes, output_excerpts, screenshots, could_not}`。

- [ ] **Step 1: 写 lenses.md**

````markdown
# 四镜头泄漏点扫描指南

泄漏点 = **如果 X 真做完了就不该长这样的细节**（侧信道信号），不是"看起来没做完"。
扫描浅而快：只找值得问的线头，绝不自己下结论——结论必须等实测官的证据。
每轮只扫当前面，不做全库深扫。

| 镜头 | 采样口 | 泄漏点示例 |
|------|--------|-----------|
| 需求覆盖 | 需求基准 ↔ 台账/代码对账 | 需求说"退款可追踪"，全库 grep 不到 refund_id；某需求无任何任务/测试引用 |
| 集成缝隙 | 接口两侧形状对比 | 生产者写 snake_case、消费者读 camelCase；配置项定义了无人读；A 调的端点 B 没注册 |
| 需求跑偏 | 需求原文 ↔ 实现语义 | 需求"离线可用"，实现"断网弹提示"；验收测的是函数存在而非行为对 |
| 细节质量 | 状态空间穷举 | 只有 happy path 的测试名；错误分支裸 500；空列表/超长输入/并发无处理痕迹 |

**无基准模式**：需求基准完全缺失时，需求覆盖、需求跑偏两镜头关闭（报告会声明），
只开集成缝隙 + 细节质量。

## 问题牌硬约束（每轮 3 张）

1. **每张牌挂一个泄漏点** — 牌面三要素：问题、触发它的泄漏点、预期照亮哪个面；
2. **必须可实测** — 实测官能翻译成具体动作；"代码质量好吗"这类不可测的题不许出；
3. **3 张覆盖不同泄漏点** — 不许全戳同一疑点推销自己的怀疑；
4. **UI/流程牌注明状态清单**（加载/空/错误/成功…）→ 实测官逐状态截图。

一问挖出缺口后，下一轮从该缺口继续发散（幂等没做 → 并发双击呢？重试队列会放大它吗？）。
用户随时可以插自己的问题——牌是引导，不是限制。
````

- [ ] **Step 2: 写 prober.md**

````markdown
# 实测官（prober）— fresh-context 取证 agent

你是实测官：对一个"自称完成"的交付物实测一个问题，带回**原始观察**。
你收到的输入是全部上下文——没有人告诉你预期答案，这是有意的：测出什么就是什么。

## 输入合同

```json
{"question": "...", "target": {"how_to_run": "...", "entry": "...", "type": "web|cli|api"},
 "states_to_capture": ["..."], "evidence_dir": ".../evidence/qNN/",
 "context_paths": ["可选：只读对账材料路径"]}
```

## 纪律

1. **自选介质并翻译为动作**：读代码即可实证的问题不必起服务；需要运行时行为的，
   起服务/调接口/用浏览器自动化走 UI/造边角输入。用户不动手。
2. **运行时取证逐状态截图**：`states_to_capture` 每个状态一张，存 `evidence_dir`，
   文件名带序号和状态语义（如 `q07-02-waiting-35s.png`）；CLI/API 留原始输出文本文件。
3. **只观察不修**：禁止对项目源码 Edit/Write；唯一可写路径是 `evidence_dir`。
   运行时副作用仅限输入指定的本地靶。
4. **返回原始观察，不下结论**："重连后消息列表为空"是观察；"重连有 bug"是结论——
   结论不是你的活。
5. **测不了如实返回**：环境起不来、缺依赖 → `could_not` + 原因，绝不编造。
6. **每问必落证据（无一例外）**：读代码 → 摘录文件（路径+行号+原文引用）；
   台账对账 → 对账摘录；`could_not` → 原因文件（尝试了什么、卡在哪）。
   空手而归 = 违规，你的结果会被渲染器拒收。

## 返回（最终文本 = 此 JSON，别的不要）

```json
{"steps_taken": ["..."], "observations": ["..."], "exit_codes": {"cmd": 0},
 "output_excerpts": ["..."], "screenshots": ["evidence_dir 下的文件名"],
 "could_not": ["测不了的部分 + 原因（无则空数组）"]}
```
````

- [ ] **Step 3: 对 spec 校验**

Run: `grep -c "泄漏点" claude/cross-exam/knowledge/lenses.md && grep -c "evidence_dir" claude/cross-exam/knowledge/prompts/prober.md`
Expected: 两个非零计数。人工核对：lenses.md 含四镜头表 + 4 条牌规 + 无基准模式；prober.md 含输入合同（含 context_paths）、6 条纪律、返回 JSON 形状——逐条对 spec §5/§6。

- [ ] **Step 4: Commit**

```bash
git add claude/cross-exam/knowledge/
git commit -m "feat(cross-exam): four-lens leak-scan guide + prober contract prompt"
```

---

### Task 4: skills/cross-exam.md（盘问官主协议）

**Files:**
- Create: `claude/cross-exam/skills/cross-exam.md`

**Interfaces:**
- Consumes: `$ROOT/knowledge/lenses.md`、`$ROOT/knowledge/prompts/prober.md`、`$ROOT/knowledge/schemas.md`、`$ROOT/scripts/render_report.py`（$ROOT = `${CLAUDE_PLUGIN_ROOT}`）。
- Produces: `/cross-exam` 的完整会话协议；run 产物 `docs/cross-exam/<日期>-<目标slug>/{ledger.json, evidence/, completion-report.md}`。

- [ ] **Step 1: 写 skills/cross-exam.md**

````markdown
---
name: cross-exam
description: Evidence-backed completion cross-examination — Socratic question cards from leak points; the skill probes and screenshots the delivery itself, then renders a deterministic completion report. Audit-only (record, never fix), interactive-only (never unattended). Explicitly invoked via /cross-exam.
version: 0.1.0
---

# cross-exam — 实证完成度盘问

`$ROOT` = `${CLAUDE_PLUGIN_ROOT}`。四镜头：`$ROOT/knowledge/lenses.md`；
实测官 prompt：`$ROOT/knowledge/prompts/prober.md`；schema：`$ROOT/knowledge/schemas.md`；
报告渲染：`$ROOT/scripts/render_report.py`。

**不变式：**
- **只记账不修** — 缺口带证据入台账，修复是用户另一个决定；盘问官没有"把问题修掉"的动机。
- **只在有人在场时运行** — 无人值守不盘；被别的流程在自治阶段调用时直接拒绝。
- **结论必须来自独立采集的证据** — 每条裁决链到实测官落盘的证据文件；口头裁决会被渲染器拒收。
- **通用** — 零项目痕迹、零技术栈硬编码；流水线台账（如 megastorm registry）只是可选数据源。
- **报告只由 `render_report.py` 渲染** — 禁止口述生成完成度报告。

## 两个角色，硬分离

- **盘问官（你，主会话）**：扫泄漏点、出问题牌、对话、解读证据、下裁决、记台账。
  你持有全部上下文与怀疑。
- **实测官（每问一个 fresh-context 子 agent）**：只拿到 prober.md 的输入合同，
  看不到你的怀疑与对话史。带回原始观察，不下结论。
  **期望隔离是本技能的诚实性根基：绝不在派发输入里夹带你预期的答案。**

## 0. 定靶（intake）

1. 确认被测对象与访问方式（怎么跑起来：web/cli/api？入口？）。
2. **需求基准探测**（依次）：megastorm overview registry（R-*，在
   `docs/superpowers/specs/*-overview.md` 的 registry 标记内）→ `docs/superpowers/specs/`
   下相关 spec → README → 问用户 → **无基准模式**（需求覆盖/跑偏两镜头关闭，
   报告声明，只开集成缝隙+细节质量）。
3. 环境能力探测：能否真跑起来；有无浏览器自动化（截图能力）。缺截图能力时
   UI 类问题只能裁"无法自证"，起手就告诉用户。
4. **安全确认（必须）**：实测会造真实调用（退款、删除这类）。与用户确认靶子是
   本地/开发实例后才放开手；生产系统一律拒绝盘问。
5. **run 目录**：`docs/cross-exam/<日期>-<目标slug>/`。检测到未收敛 run
   （`ledger.json` 存在且 `completion-report.md` 不存在）→ 问用户续接还是新开。
6. 初始化/载入 `ledger.json`（schema 见 `$ROOT/knowledge/schemas.md`）。

## 1. 定面（facet map）

从需求基准 + 代码拓扑摆出交付的面（如：退款流程、通知、断线重连…），
AskUserQuestion 让用户勾选盘哪些、先盘哪个。没选的面在 ledger 里记
`status: "not_examined"`——渲染器会把它们列进"未盘问声明"，绝不算进完成度。

## 2. 盘问循环（每轮一个面）

```
扫泄漏点（读 lenses.md，浅而快）→ 出 3 张问题牌 → 用户选一张（或自己出题）
  → 派实测官（fresh context）→ 带回证据 → 你对证据下裁决 → 入台账 → 下一轮
```

- **问题牌**：遵守 lenses.md 的 4 条硬约束（挂泄漏点、可实测、覆盖不同疑点、
  UI 牌注明状态清单）。牌用 AskUserQuestion 呈现，用户永远可以走"Other"自己出题。
- **派实测官**：`Agent(general-purpose)`，prompt = `$ROOT/knowledge/prompts/prober.md`
  全文 + 输入 JSON（question / target / states_to_capture / evidence_dir /
  可选 context_paths——只传路径不传你的解读）。**不夹带怀疑。**
- **收证据**：把关键观察和截图路径给用户看，再对照需求基准下裁决。
- **裁决四种**：`done` 实证完成 / `gap` 缺口 / `drift` 跑偏 / `unprovable` 无法自证
  （需真设备/人工，如实挂账不猜）。`gap|drift` 定 severity（high|medium|low，
  依据：需求引用的分量 + 实测后果的破坏面）。
- **每问立刻落盘 ledger.json**（中断不丢），entry 按 schemas.md。
- **发散**：挖出缺口后，下一轮的牌从缺口继续发散。
- **实测官死/超时**：重派一次（基础设施失败不算数）；再失败该问记 `could_not`
  证据（原因文件），裁 `unprovable`，绝不编造。
- **靶子起不来**：本身就是一条集成缝隙 `gap`（"声称可跑，实测失败"，实测官的
  失败输出就是证据），盘问降级为 code/ledger 介质继续。

## 3. 收敛出报告

用户喊停或选中的面盘完 →
`python3 $ROOT/scripts/render_report.py docs/cross-exam/<run>/` →
把 completion-report.md 呈给用户。报告四类裁决计数、逐面"X 问中 Y 问实证通过"、
缺口清单（可直接转修复任务）、无法自证清单、未盘问声明——**没有编造的总百分比**。
````

- [ ] **Step 2: 引用完整性校验**

Run: `for f in knowledge/lenses.md knowledge/prompts/prober.md knowledge/schemas.md scripts/render_report.py; do test -f claude/cross-exam/$f && echo "OK $f"; done`
Expected: 4 行 OK（skill 引用的文件全部存在）。

- [ ] **Step 3: Commit**

```bash
git add claude/cross-exam/skills/
git commit -m "feat(cross-exam): interrogator protocol skill — intake, facet map, exam loop, report"
```

---

### Task 5: megastorm Phase 2 邀请句 + patch bump 0.11.1

**Files:**
- Modify: `claude/megastorm/skills/megastorm.md`（Phase 2 — Report 节末尾）
- Modify: `claude/megastorm/.claude-plugin/plugin.json`（version）
- Modify: `claude/megastorm/.claude-plugin/marketplace.json`（version）

**Interfaces:**
- Consumes: `/cross-exam` 命令存在（Task 1）。
- Produces: megastorm 收尾报告邀请一句，不自动进入、不产生依赖。

- [ ] **Step 1: 邀请句**

`claude/megastorm/skills/megastorm.md` 的 "## Phase 2 — Report" 节内、
"**Mandatory escalation + skip accounting**" 段之前，在
"Update the overview and write a final report: ..." 段落末尾追加一句：

```markdown
After delivering the report, add one closing line inviting the user to run
`/cross-exam` for an evidence-backed completion cross-examination of this
delivery (a standalone, interactive-only skill — do NOT auto-enter it, and
do not treat it as installed: skip the line if the command is unavailable).
```

- [ ] **Step 2: bump 两处 manifest**

`claude/megastorm/.claude-plugin/plugin.json` 与 `marketplace.json`：
`"version": "0.11.0"` → `"version": "0.11.1"`（各一处）。

- [ ] **Step 3: 验证**

Run: `grep -c '"version": "0.11.1"' claude/megastorm/.claude-plugin/plugin.json claude/megastorm/.claude-plugin/marketplace.json && grep -c "cross-exam" claude/megastorm/skills/megastorm.md && cd claude/megastorm/scripts && python3 check_skill_refs.py`
Expected: 两个 manifest 各计数 1；megastorm.md 计数 ≥1；`OK: all 14 referenced files present`

- [ ] **Step 4: Commit**

```bash
git add claude/megastorm/
git commit -m "chore(megastorm): 0.11.1 — invite /cross-exam after Phase 2 report"
```

---

### Task 6: 端到端夹具渲染 + 安装验证

**Files:**
- Create: 临时夹具（scratchpad，不入库）
- 无源码改动；发现问题则回改对应任务的文件

**Interfaces:**
- Consumes: Task 1–5 全部产物。

- [ ] **Step 1: 造一个真实形状的 run 夹具并渲染**

在 scratchpad 建 `demo-run/`：2 个面（F1 examined、F2 not_examined）、4 条 entry
（done/gap(high, requirement_ref=R-09)/unprovable 各带非空 evidence 目录 + 1 条
故意无证据目录的口头裁决），内容仿 Task 2 测试的 `_mk_run`。然后：

Run: `python3 claude/cross-exam/scripts/render_report.py <scratchpad>/demo-run/ && cat <scratchpad>/demo-run/completion-report.md`
Expected: 报告含——总览计数"实证完成：1 · 缺口：1 · 跑偏：0 · 无法自证：1"、
"### …（F1）— 3 问中 1 问实证通过"、缺口清单含 **high** 和 [R-09]、
未盘问声明含 F2、违规裁决段点名口头裁决那条。逐段人工核对与 spec §7 报告结构一致。

- [ ] **Step 2: 全量测试回归**

Run: `cd claude/cross-exam/scripts && python3 test_render_report.py && cd ../../megastorm/scripts && python3 test_build_task_dag.py && python3 test_check_closure.py`
Expected: 全部 `OK`

- [ ] **Step 3: 本地安装并确认命令可见**

Run: `bash claude/install.sh`
Expected: 输出含 `Installing cross-exam@cross-exam...` + `installed`（或 CLI 缺席时的
Warning——那样改为人工核对 `claude plugin marketplace add claude/cross-exam` 后
`claude` 会话内 `/cross-exam` 出现在命令列表）。

- [ ] **Step 4: 提交收尾（如有回改）并向用户报告**

```bash
git status --short   # 应干净；有回改则按所属任务的 message 风格提交
```

向用户报告：插件已装。**真正的活体 dogfood（找一个真实小项目故意留 2-3 个已知
缺口跑一次 /cross-exam，验证缺口被晃出且截图落档）需要用户在场交互**，作为安装后
第一次使用一起做——这是 spec §9 的第二条测试，不能由无人值守的执行者代跑。
````

---

## Self-Review

**Spec coverage**：§2 决策（通用/只记账/交互式/邀请句）→ Task 1/4/5；§3 结构 → Task 1–4；§4 流程（intake/定面/循环/收敛/续跑/无基准）→ Task 4；§5 四镜头+牌规 → Task 3；§6 实测官合同（含 §6.6 每问必证、§6.7 工具面）→ Task 3/4；§7 schema+报告+红线 → Task 2；§8 错误处理 → Task 4（循环节）+ Task 2（exit 语义）；§9 测试 → Task 2（单测）+ Task 6（夹具 E2E + 活体 dogfood 留给用户在场）。无缺口。

**Placeholder scan**：无 TBD/TODO；所有代码/文档步骤给了全文。

**Type consistency**：verdict 机器值 `done|gap|drift|unprovable` 在 schemas.md / render_report.py / 测试 / skill 一致；`render(run_dir) -> str` 与测试调用一致；evidence 结构 `{dir, files, key_observation}` 三处一致；输入合同字段与 prober.md/skill 派发一致。
