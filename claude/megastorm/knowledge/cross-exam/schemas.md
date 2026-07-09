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
- 顶层可选 `open_threads`（防弃牌蒸发）：出过牌但未实测的线，
  `[{"q": "...", "facet": "F1", "leak_point": "..."}]`。每轮发牌后把未选中的牌
  **立即**记入；某线后来被实测则移入 entries 并从这里删除。渲染为"未拉的线"专节，
  不进任何计数；续盘时它是起手牌候选。

## completion-report.md（仅由 scripts/render_report.py 渲染，禁止口述生成）

依次：总览（面/问/四类裁决计数；baseline=none 时声明关闭的镜头）→ 逐面完成度
（"X 问中 Y 问实证通过"，逐条链证据）→ 缺口清单（gap+drift 按 severity 排）→
无法自证清单 → 未盘问声明（not_examined 面）→ 未拉的线（open_threads）→
拒渲声明（如有）。

## 诚实性红线（写死在 render_report.py，不是嘱咐）

1. `not_examined` 的面不进任何完成度统计，只进未盘问声明；
2. 无 evidence 目录（缺 key / 目录不存在 / 目录为空）的 entry 拒绝渲染进正文与计数，
   在"违规裁决"段落点名——合法裁决必有证据（含 could_not 原因文件），被拒的只可能是
   绕过实测的口头裁决。evidence 目录必须位于 run 目录的 `evidence/` 之下（"." /
   run 目录本身 / 逃逸路径一律拒收，即使目录非空也不算证据）；verdict 不在
   done|gap|drift|unprovable 内的 entry 同样拒渲并点名（非法裁决），即使它带着
   看似合法的证据目录。
