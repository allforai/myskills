# cross-exam: journey declarations

## Goal

给 cross-exam 加一种新的声明类型：**旅程（journey）**。现有声明是"功能 X 做了"，探针去证实；旅程声明是"角色 A 在情景 B 要做成可观察的进展 C"，探针去走这条路，逐步落证据，盘问官对用户事先写下的 oracle 裁决走通、卡死还是无法自证。

它解决两件事：

1. 非 meta-skill 开发的产品也能做"以产品意图为基线"的交互验收。意图由用户在对话里口述，不依赖 `.allforai/` 推导链。
2. product-review 的"在不在、走不走得完"两问有了独立取证来源。cross-exam 出旅程裁决，product-review 通过已有的 Prior evidence 机制消费，两个技能各守各的问题。

不改的：cross-exam 的全部不变量（只记账不修、有人在场、证据独立采集、实测官不可降级、通用、报告只由渲染器生成）；期望隔离（探针不拿 oracle）；两个角色硬分离。

## Non-goals

- 不做像素基线或截图 diff。旅程裁决对的是语义 oracle，不是上次的截图。
- 不做审美判断。"这个页面好不好看"是 product-review 的事。
- 不给探针 CI 级约束（固定模型、温度 0、种子数据）。cross-exam 是有人在场的取证，不是回归测试。
- 不改 megastorm、grillstorm、meta-skill 的 visual-verify。visual-verify 保留复刻语义。

## Sources borrowed

生态里没有做整件事的 skill。逐项借来的：

| 来源 | 借什么 |
|---|---|
| petrkindlmann/qa-skills@agentic-browser-testing | oracle 在代理之外，必含禁止态；步数预算用尽即失败不重试；断言用无障碍树，截图给人看 |
| alinaqi/maggy@user-journeys | 前置条件和恢复路径是一等字段 |
| mastepanoski/claude-skills@cognitive-walkthrough | 卡死分类：会试吗、找得到吗、看得懂吗、有反馈吗，加恢复路径 |
| everyinc/compound-engineering-plugin@ce-test-browser | 每一步必有状态，Skip 必带原因，步骤不许从汇总里消失 |

不借的：LLM 自评分、"没报错就算过"、CI 级确定性约束。

## Data model

### `ledger.json` 顶层新增 `journeys[]`

```json
{
  "id": "J1",
  "who": "回头客",
  "circumstance": "购物车里已有一件商品",
  "progress": "完成支付并拿到订单号",
  "preconditions": ["已登录测试账号", "购物车非空"],
  "waypoints": ["支付确认页"],
  "oracle": {
    "done_looks_like": ["URL 含 /orders/", "页面含订单号文本"],
    "stuck_looks_like": ["仍在 /cart", "出现 role=alert 的支付失败"]
  },
  "step_budget": 15,
  "status": "examined|not_examined",
  "risk": {"level": "high|medium|low", "why": "仅 not_examined：这份工作的分量 + 若真走不通的破坏面"},
  "entry_q": "J1 走得通吗？"
}
```

字段规则：

- `who` / `circumstance` / `progress` 必填，格式与 product-review 的 job 三元组相同。
- `oracle.done_looks_like` 和 `oracle.stuck_looks_like` 都必填且非空。写不出 `stuck_looks_like` 的旅程不入台账，退回用户补。
- `preconditions` 可空数组。`waypoints` 可选，是用户点名必须经过的状态。只给盘问官看，不进探针输入（2026-09-06 修订：原设计把 waypoints 发给探针并要求逐个截图，探针会主动经过它们，drift 只在 waypoint 不可达时触发，测不出"产品允许跳过必经点"）。
- `step_budget` 必填，默认 15，盘问官按旅程长度调整。
- `entry_q` 指向 `entries[]` 里那条实证 entry 的 `q`，精确匹配。规则与 `patterns[].sites[].entry_q` 相同：渲染器只认匹配到被采信 entry 的旅程为已盘问，其余一律算未盘问。`status` 字段仍写，但渲染器以 `entry_q` 匹配为准。
- `risk` 只对 `not_examined` 有意义，语义同 `facets[].risk`。

### `entries[]` 新增可选字段

```json
{
  "q": "J1 走得通吗？",
  "journey": "J1",
  "facet": "F3",
  "medium": "runtime",
  "steps": [
    {"n": 1, "action": "打开 /cart", "observed": "购物车显示 1 件商品", "status": "done", "evidence": "q05-01-cart.png"},
    {"n": 7, "action": "点击 确认支付", "observed": "按钮变灰 3 秒后恢复，页面无变化", "status": "stuck", "evidence": "q05-07-pay-noop.png"}
  ],
  "terminal_state": {"url": "/checkout/pay", "snapshot": "q05-terminal-a11y.txt"},
  "verdict": "gap",
  "stuck_kind": "no_feedback",
  "severity": "high"
}
```

- `journey` 可选。带此字段的 entry 是旅程实证 entry。`facet` 仍必填，写旅程主要触及的面。
- `steps[].status` ∈ `done | stuck | could_not`。每步必有 `evidence` 文件名（截图或输出文本），位于该 entry 的 `evidence.dir` 下。
- `terminal_state` 可选，web 目标必有 `snapshot`（无障碍树文本文件名）。
- `stuck_kind` 仅 `verdict == gap` 且带 `journey` 时必填，∈ `no_entry | not_found | misleading | no_feedback | no_recovery | broken`：
  - `no_entry`：这份工作在界面里没有入口
  - `not_found`：有入口但探针在预算内找不到
  - `misleading`：控件找到了但行为与标签不符
  - `no_feedback`：动作执行了，看不出成没成
  - `no_recovery`：失败或反向操作后没有回到主线的路
  - `broken`：系统报错、崩溃、死循环

Codex 孪生版的 `journeys[]` 条目和 `steps[]` 不加 UUID；`entry_q` 已是稳定键。

## Protocol changes

### §1 定面之后新增 §1b 旅程采集

位置：census 合并、用户勾选面之后，盘问循环之前。理由：census 已用覆盖法从代码拓扑穷举了操作面和入口，旅程候选从这里来，不另派 agent，也不让盘问官凭印象读代码定候选。

流程：

1. **整理候选**。盘问官把 census 的面按"入口 → 能推进到的终态"归成候选旅程，加上需求基准里的任务（registry、spec、README；若 `.allforai/product-map/task-inventory.json` 存在也读，它只是可选数据源）。每条候选写成三元组草稿。
2. **摆给用户**。AskUserQuestion 多选：勾选要盘的候选，用户可走 Other 补自己的旅程。零勾选零补充不阻塞，ledger 写 `journeys: []`，报告声明"无旅程声明"。
3. **改写读回**。每条选中的旅程，盘问官改写成三元组加 oracle，读回用户确认。一轮改写后仍无 `who` 或 `progress` 的不是旅程，说明缺哪部分，用户补一次，仍缺就不收。`stuck_looks_like` 空的同样退回补一次。
4. **落盘**。确认的旅程写入 `journeys[]`，`status: not_examined`，带 `risk`。未选的候选不入台账。

### §2 盘问循环新增旅程轮

旅程不走三张问题牌。它的问题固定是"`<id>` 走得通吗？"，用户在 §1b 已经选过。用户选一条旅程或一个面进入本轮；选旅程时：

- **派探针**：`Agent(general-purpose)`，prompt = prober.md 全文 + 输入 JSON。输入的 `journey` 块只含 `goal`（三元组拼成一句话）、`preconditions`、`step_budget`。**不含 oracle，也不含 waypoints。** `states_to_capture` 写"起点"和"终态"；探针每步都截图，waypoint 是否经过由盘问官事后对 steps 查。
- **收证据**：把 steps 和终态截图给用户看。
- **裁决**：
  - `done`：`done_looks_like` 全部命中，`stuck_looks_like` 无一命中，每个 waypoint 都在 `steps[].observed` 里出现过。
  - `gap`：任一 `stuck_looks_like` 命中，或探针报 `budget_exhausted`，或任一步 `stuck`。必填 `stuck_kind` 和 `severity`。
  - `drift`：终态满足 `done_looks_like`，但 `steps[]` 从未经过某个 waypoint，即产品允许用户跳过声明为必经的状态。
  - `unprovable`：前置条件造不出来，或探针因环境原因 `could_not`（起不来、缺依赖、缺浏览器）。`budget_exhausted` 不属于这一类：预算内到不了进展是产品的问题，裁 `gap`。
- **落账**：entry 带 `journey` 和 `steps`；`journeys[].entry_q` 指到它，`status` 改 `examined`。
- **扫全模式**：所有 `not_examined` 旅程并行扇出探针，一条旅程一个 fresh-context agent，收齐后逐条裁决。
- **发散照旧**：旅程 `gap` 后，下一轮从卡死点纵向出牌进 `open_threads`；多条旅程在同一种 `stuck_kind` 卡死，走"孤例还是一类"建 pattern。
- **bias-guard 照旧**：盘问官==作者时旅程 gap 从严。

### prober.md 变更

输入合同加可选 `journey` 块：

```json
"journey": {"goal": "作为回头客，购物车里已有一件商品，完成支付并拿到订单号",
            "preconditions": ["…"], "step_budget": 15}
```

纪律新增：

7. **旅程先记起点**：动手前落盘起点状态（web：URL 加无障碍树快照；cli：工作目录和环境摘要；api：初始资源状态），文件名 `qNN-00-start.*`。前置条件造不出来 → `could_not`，不猜不绕。
8. **旅程逐步落证据**：每一步一条 `steps[]` 记录加一个证据文件。web 目标每步截图，终态另存无障碍树文本。步骤不许合并，不许省略"没变化"的步。
9. **步数用尽即停**：`step_budget` 用完还没到用户描述的进展，停下，`could_not` 写 `budget_exhausted`，把已走的 steps 全部返回。不重试，不换路绕。

返回 JSON 加 `steps[]` 和 `terminal_state`。介质不限 web：cli 旅程是命令序列，每步留 stdout 文件；api 旅程是调用序列，每步留请求响应文件。

### lenses.md 新增旅程镜头

| 镜头 | 采样口 | 泄漏点示例 |
|---|---|---|
| 旅程 | 三元组 ↔ 界面入口与终态 | 任务清单里的工作在导航里找不到入口；成功后页面没有下一步；失败态没有返回主线的按钮；"提交"后按钮变灰但无任何状态文本 |

## Rendering

`render_report.py` 变更（两个孪生版）：

1. `_load` 不把 `journeys` 列为必填键；缺省为 `[]`。
2. 采信规则新增：entry 带 `journey` 但 `journeys[]` 查无此 id → 拒渲，原因"旅程引用不存在"。entry 带 `journey`、`verdict == gap` 但 `stuck_kind` 不在六种之内 → 拒渲，原因"非法卡死类型"。
3. 旅程盘问判定：`journeys[]` 每条按 `entry_q` 精确匹配被采信 entry；匹配到即已盘问，否则未盘问。`status` 字段不作为依据。
4. 总览行加"旅程 N 条，盘问 M 条"，四类裁决计数中旅程 entry 与普通 entry 分开各列一行。
5. "逐面完成度"之后新增"## 旅程完成度"节。每条已盘问旅程一段：

   ```
   ### J1 回头客 · 购物车里已有一件商品 · 完成支付并拿到订单号 — 缺口（high，no_feedback）
   走了 7 步，卡在第 7 步：点击 确认支付 → 按钮变灰 3 秒后恢复，页面无变化（证据：evidence/q05/）
   - 1 done 打开 /cart → 购物车显示 1 件商品
   - …
   ```

   `done` 旅程写"走通，N 步"。`drift` 写"走通但绕过 waypoint：<名>"。`unprovable` 写原因。无旅程时写"（无旅程声明）"。
6. 未盘问旅程按 `risk` 排进"未盘问声明"，与未盘问面同列，前缀 `旅程`。
7. "缺口清单"包含旅程 gap，行首加 `[J1]` 标签，便于 product-review 引用。
8. 红线补一条，写进模块 docstring 和 schemas.md：旅程没有自报"已查"的通道，`entry_q` 匹配不上一律未盘问。

## Peripheral changes

- **product-review.md**：Prior evidence 段落认 `J` 编号。走不通的旅程对上 scope 里的 job 时写"J1 blocks <job label>"。`depends_on` 允许 cross-exam 的 `J` 编号。示例行更新。
- **Codex 孪生版**：`codex/cross-exam-skill/SKILL.md`、`schemas.md`、`prompts/prober.md`、`lenses.md`、`scripts/render_report.py` 同步，保留其 UUID 与 severity 校验；`ledger_store.py` 的去重键不变。
- **cross-exam description** 一行提到旅程：可声明用户旅程，探针端到端走通并逐步取证。
- **CLAUDE.md** "Which entry" 表的 cross-exam 一行补"含用户旅程走通验证"。

## Testing

`test_render_report.py`（两个孪生版）新增用例：

- 旅程 `done` 进旅程计数，不进普通计数。
- 旅程 `gap` 带 `stuck_kind` 正常渲染，缺口清单行首带 `[J1]`。
- `stuck_kind` 非法 → 拒渲并点名。
- entry 引用不存在的 journey id → 拒渲并点名。
- `journeys[].entry_q` 对不上被采信 entry → 渲染为未盘问，即使 `status: examined`。
- `entry_q` 对上的是被拒渲 entry → 未盘问。
- `not_examined` 旅程按 risk 排序，缺 risk 排最后并标"未评估风险"。
- `journeys` 缺省 → 报告写"（无旅程声明）"，不报错。
- `drift` 旅程渲染绕过的 waypoint。

Skill 层按思维测试法跑失败场景，每个场景一个 fresh-context 子 agent：

- 探针输入里夹带了 oracle：期望盘问官改写输入去掉它。
- 用户给的旅程没有 `stuck_looks_like`：期望退回补一次，不入台账。
- 用户零旅程：期望 cross-exam 正常跑完，报告声明无旅程。
- cli 目标的旅程：期望探针用命令序列取证，每步留 stdout。
- 探针步数用尽：期望 `could_not: budget_exhausted`，盘问官裁 `gap`，不重派。
- 盘问官==作者，旅程 gap：期望 severity 从严。

## Open questions

无。
