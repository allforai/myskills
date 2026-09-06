# cross-exam — ledger 与报告结构

## 可选视觉扩展

视觉模式的数据合同见 [visual/visual-acceptance.md](visual/visual-acceptance.md)。
新增 visual_acceptance、visual_cases，以及 entry 的 visual_case_ids、
evidence_manifest、review_reports、review_mode、reconciliation_ref、degradation_ref、
visual_failure_ref。旧 ledger 无需这些字段。所有视觉 facet 必须登记 facet_ids，
防止遗漏 visual_case_ids 绕过证据校验。基线引用相对 run，其余视觉文件引用相对
run/evidence；现有 evidence.dir 仍遵循原合同。

visual/validation.py 校验逐类确认、SHA-256、运行介质、图像签名、原图审查覆盖、
双审身份和阻断项并集；失败裁决拒渲，未关联有效裁决的用例一律未验收。
文件结构校验无法证明图片来源或模型确实看图，主会话必须核对取证工具记录。

## ledger.json（盘问官逐问实时落盘，中断不丢）

```json
{
  "schema_version": 1,
  "run_id": "stable UUID",
  "target": "被盘问对象（人类可读名）",
  "baseline": "superstorm-registry|spec|readme|user|none",
  "started": "YYYY-MM-DD",
  "examiner_is_author": false,
  "requirements": [
    {"id": "R-09", "text": "退款可追踪"}
  ],
  "surfaces": [
    {"id": "S5", "name": "退款", "entry": "POST /api/orders/:id/refund"}
  ],
  "facets": [
    {"id": "F1", "name": "退款流程", "status": "examined|partial|not_examined",
     "surface_ids": ["S5"], "requirement_refs": ["R-09"],
     "risk": {"level": "high|medium|low", "why": "仅 not_examined 面：需求引用的分量 + 若真坏的破坏面"}}
  ],
  "entries": [
    {
      "id": "stable UUID",
      "q": "同一笔订单退两次会怎样？",
      "facet": "F1",
      "leak_point": "接口返回无幂等键，测试名单里无 duplicate 字样",
      "medium": "runtime|code|ledger",
      "agent_model": "sonnet（取证该 entry 的子 agent 模型字面量；Codex 如 gpt-5.6-luna）",
      "evidence": {
        "dir": "evidence/q03/",
        "files": ["q03-01-first-refund.png", "q03-02-second-refund.png"],
        "key_observation": "第二次退款返回 200 且重复扣减"
      },
      "verdict": "done|gap|drift|unprovable",
      "surfaces": ["S5"],
      "requirement_refs": ["R-09"],
      "requirement_ref": "R-09（旧字段，可选）",
      "severity": "high|medium|low（仅 gap|drift；done/unprovable 不带）"
    }
  ],
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
}
```

- `entries[].agent_model` 新 entry 必填（分层前的旧 run 可缺，渲染器不拒）：派发取证的子 agent 实际用的模型字面量（实测官取证档、视觉 reviewer
  判断档；harness 不能按 agent 指定模型时记会话模型名加 `(session)`）。顶层 `census_model` 与
  `patterns[].enumerator_model` 同理。档位表见 SKILL.md "模型分层"；这些字段让报告读者能核对
  "这条裁决的证据是谁取的"，渲染器不据此改任何计数。
- 顶层 `surfaces[]`（覆盖分母，新 run 必填；旧 ledger 可缺，渲染器不据此拒渲）：普查官返回的操作面
  **原样**入账（`dead_contracts` 也各作一行）。`facets[].surface_ids` 写该面包含的 surface id；
  `entries[].surfaces` 写这问的证据实际触及的 surface id。**操作面的"触及"没有自报通道**：渲染器只认
  被采信 entry 的 `surfaces` 里、且在顶层 `surfaces[]` 登记过的 id；未登记的 id 不算触及并点名，
  没写 `surfaces` 的 entry 逐条点名。逐面标题渲染"操作面 K 个，裁决触及 T 个，未触及：…逐个点名"；
  facet 没写 `surface_ids` 时标"操作面未登记，覆盖不可算"。
- **facet 的"盘过"由渲染器推导**：有至少一条被采信 entry 的面才算盘问过；`status` 照写，但一问都没落账的
  面无论写什么都进"未盘问声明"（缺 risk 则标"未评估风险"）。
- 顶层 `requirements[]`（需求侧点名册；baseline 非 none 时必填，旧 ledger 可缺）：需求基准逐条
  `{id, text}`。`facets[].requirement_refs` 写该面承接的需求；`entries[].requirement_refs` 写这问引用的需求
  （旧字段 `requirement_ref` 字符串仍认，按分隔符切 token 匹配）。渲染器出"需求覆盖"专节：一条需求有裁决，
  当且仅当某条被采信 entry 引用了它；无裁决的按"落在哪个面、该面盘没盘"点名，没落任何面的单独点名。
- 顶层可选 `examiner_is_author`：盘问官==交付作者时为 true，渲染器在总览点明"作者自审，
  bias-guard 生效"，续盘时该条件不丢。
- `facets[].risk` 可选，只对 `not_examined` 面有意义：渲染器按 level 排序未盘问声明并打印 why；
  缺 risk 的未盘问面排在最后并标"未评估风险"。
- `evidence.dir` 相对 run 目录；**每个 entry 必有非空 evidence 目录**（spec §6.6）：
  runtime → 截图/输出文件；code → 摘录文件（路径+行号+原文引用）；ledger → 对账摘录；
  `could_not`/无法自证 → 原因文件（尝试了什么、卡在哪）。
- verdict 语义：`done` 实证完成 / `gap` 缺口（实测打脸）/ `drift` 跑偏（做了但不是需求
  的意思）/ `unprovable` 无法自证（需真设备/人工，如实挂账不猜）。
- 顶层可选 `open_threads`（防弃牌蒸发）：出过牌但未实测的线，
  `[{"id":"stable UUID", "q": "...", "facet": "F1", "leak_point": "..."}]`。每轮发牌后把未选中的牌
  **立即**记入；某线后来被实测则移入 entries 并从这里删除。渲染为"未拉的线"专节，
  不进任何计数；续盘时它是起手牌候选。
- 顶层可选 `patterns`（缺陷模式=同类位点清点，防同类嫌疑蒸发）：

  ```json
  {"pattern_id": "P1", "hypothesis": "写端点普遍缺幂等键",
   "enumerated": true,
   "sites": [
     {"site": "POST /api/refunds", "facet": "F1", "entry_q": "同一笔订单退两次会怎样？"},
     {"site": "POST /api/orders", "facet": "F2"}
   ]}
  ```

  `enumerated` 可选：枚举官两次派发都无返回时写 false，`sites` 只含已实测的首例；渲染器在该
  pattern 标题标"同类位点全集未清点"，让"未查 0"不被误读为"只有这一处"。
  某条 `gap|drift` 被判为"一类的实例"时建 pattern：`hypothesis` 一句话缺陷模式，
  `sites` 由枚举官覆盖法列出的全部同类位点。位点**没有 status 字段——不许自报
  "已查"**：某位点被实测后，把它的 `entry_q` 指到那条 entry 的 `q`（精确匹配）；
  渲染器只认"entry_q 匹配到被采信 entry"为实证，其余（无 entry_q / 对不上 /
  对上的是被拒渲裁决）一律算未查并逐个点名。
- 顶层可选 `journeys`（旅程声明=用户口述的意图基线）：`who / circumstance / progress` 三元组与
  product-review 的 job 同格式；`oracle.done_looks_like` 与 `oracle.stuck_looks_like` 都必填非空，
  写不出 `stuck_looks_like` 的旅程不入台账；`waypoints` 可选，是用户点名必经的状态；`step_budget`
  必填，默认 15。**oracle 和 waypoints 都只给盘问官看，绝不进探针输入**——探针自选路径，盘问官事后
  对 `steps[]` 查有没有经过 waypoint；探针若知道必经点就会主动经过它，"产品允许跳过"永远测不出来。
  旅程的实证 entry 带 `journey: "J1"` 与 `steps[]`；`facet` 仍必填（写旅程主要触及的面），`leak_point`
  可省（旅程不挂泄漏点）。`steps[]` 每步 `{n, action, observed, status: done|stuck|could_not,
  evidence}`，`evidence` 是该 entry `evidence.dir` 下的文件名），web 目标另带 `terminal_state: {url, snapshot}`。
  旅程 `gap` 必填 `stuck_kind` ∈ `no_entry`（无入口）| `not_found`（找不到）| `misleading`（误导）|
  `no_feedback`（无反馈）| `no_recovery`（无恢复路径）| `broken`（系统报错）；旅程 `drift` 必填
  `missed_waypoints[]`。
  旅程**没有自报"已查"的通道**：`journeys[].entry_q` 精确匹配到一条被采信 entry 且该 entry 的
  `journey` 等于旅程 id 才算已盘问；`status` 字段照写但渲染器不看它。未盘问旅程按 `risk` 与未盘问面
  同列渲染，前缀"旅程"，不进任何计数。

`ledger.json` 通过 `scripts/ledger_store.py` 整文件原子替换，不做文本 append。
同一 run 只允许一个 examiner lock；entry/open-thread 按 UUID + 内容去重，冲突拒绝。

## completion-report.md（仅由 scripts/render_report.py 渲染，禁止口述生成）

依次：总览（面/问/四类裁决计数，实证完成按介质分列"运行时 / 代码 / 台账"，旅程裁决计数与普通裁决计数
分列；有 `surfaces` 时加"操作面 N 个，裁决触及 M 个"；baseline=none 时声明关闭的镜头）→
需求覆盖（有 `requirements` 时："基准 N 条，有裁决 M 条，无裁决 K 条"，逐条列裁决或点名落在哪个面）→
逐面完成度（只含普通 entry，"X 问中 Y 问实证通过 · 操作面 K 个，裁决触及 T 个，未触及逐个点名"，
逐条链证据）→ 旅程完成度（每条已盘问旅程：走通
N 步 / 卡在第 K 步加卡死类型 / 绕过的 waypoint / 无法自证原因，逐步状态列表）→ 缺口清单（gap+drift 按 severity 排；普通缺口行首带 `[G1]`——G 号由渲染器按 ledger 里 entries 的先后顺序编，不按严重度，续盘只追加不重排所以稳定，被拒渲的不占号；旅程 gap 行首带 `[J1]`，不占 G 号。product-review 的 `depends_on` 引用的就是 G/J 号）→
无法自证清单 → 未盘问声明（not_examined 面与未盘问旅程，按 risk 同列）→ 未拉的线（open_threads）→
缺陷模式（patterns：每类"共 N 位点，实证 M，未查 K"，未查位点逐个点名）→
拒渲声明（如有）。

## 诚实性红线（写死在 render_report.py，不是嘱咐）

1. `not_examined` 的面不进任何完成度统计，只进未盘问声明；
2. 无 evidence 目录（缺 key / 目录不存在 / 目录为空）的 entry 拒绝渲染进正文与计数，
   在"违规裁决"段落点名——合法裁决必有证据（含 could_not 原因文件），被拒的只可能是
   绕过实测的口头裁决。evidence 目录必须位于 run 目录的 `evidence/` 之下（"." /
   run 目录本身 / 逃逸路径一律拒收，即使目录非空也不算证据）；verdict 不在
   done|gap|drift|unprovable 内的 entry 同样拒渲并点名（非法裁决），即使它带着
   看似合法的证据目录。
3. patterns 的位点没有自报"已查"的通道：`entry_q` 精确匹配到被采信 entry 才算
   实证，匹配不上（含匹配到被拒渲裁决）一律渲染为"未查"并逐个点名，不进任何计数。
4. 旅程同样没有自报"已查"的通道：`entry_q` 匹配不到被采信 entry 一律渲染为未盘问；entry 带
   `journey` 但 journeys 里查无此 id、或旅程 gap 的 `stuck_kind` 不在六种之内，拒渲并点名。
   旅程 drift 缺 `missed_waypoints` 同样拒渲并点名。
   旅程 entry 的 `steps[].evidence` 每步必写且文件必须真在 `evidence.dir` 下，`terminal_state.snapshot`
   同理；缺一个整条拒渲并点名缺的文件——编造的步骤列表过不了渲染器。
5. 覆盖没有自报通道：facet 的"盘过"按被采信 entry 推导；操作面的"触及"只认被采信 entry 引用的、
   且在 `surfaces[]` 登记过的 id；需求的"有裁决"只认被采信 entry 的引用。零证据的面、未登记的
   面 id、没人引用的需求，一律渲染为未盘问 / 未触及 / 无裁决并逐个点名，不进任何计数。
