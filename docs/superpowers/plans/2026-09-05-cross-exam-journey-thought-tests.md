# cross-exam journey declarations — 思维测试记录

日期：2026-09-05。被测文本：`claude/megastorm/skills/cross-exam.md`、`knowledge/cross-exam/prompts/prober.md`、`knowledge/cross-exam/schemas.md`，提交 e2575e8。
方法：每个场景一个 fresh-context 子 agent，只给三份文本和场景描述，不给期望答案，要求按条文说明下一步并引用原句。判定由主会话对照计划里的通过判据。

| 场景 | 通过判据 | agent 回答摘要 | 判定 |
|---|---|---|---|
| A 探针输入夹带 oracle | 指出 oracle 不进探针输入，引用"oracle 绝不进输入"，给出去掉后的 JSON | 结论"不能直接发"；引用 §2 旅程轮原句与 schemas.md"oracle 只给盘问官看，绝不进探针输入"；给出只含 goal/preconditions/waypoints/step_budget 的 JSON，oracle 留在 ledger 供盘问官裁决 | 通过 |
| B 旅程缺 stuck_looks_like | 退回用户补一次，引用 §1b 第 3 条；不入台账 | "不落盘该旅程，就地打回用户补"；引用 schemas.md 必填非空与 §1b 第 3 条"'没报错'不是 oracle"；明确此刻不入台账 | 通过 |
| C 用户零旅程 | 继续跑，`journeys: []`，报告"无旅程声明" | 继续跑；`"journeys": []`，不把候选硬塞入台账（引用 §1b 第 4 条）；报告在旅程完成度处显式声明"无旅程声明"，旅程计数全零不进完成度 | 通过 |
| D cli 目标的旅程 | 命令序列，每步 stdout 文件，起点记工作目录与环境摘要，引用纪律 7、8 | 起点 `q08-00-start.txt` 记 pwd/ls/env 摘要（token 打码）；每步一条 steps 加一个 stdout 文件，不合并；终态落最后输出文件；引用条款 1、2、3、4、5、7、8、9；前置条件造不出即 could_not | 通过。附注：回答把"不下结论"归给渲染器而非盘问官，无害误读 |
| E 探针预算用尽 | `gap` 非 `unprovable`；不重派；引用"预算用尽不是 unprovable" | 裁 gap，理由是三个触发条件为"或"关系，budget_exhausted 单独满足；不重派，重派只覆盖死/超时；stuck_kind=no_feedback，severity=high（核心链路阻断）；写出 entry 与 journeys[].entry_q 回指；还主动提到"孤例还是一类" | 通过 |
| F 作者自审的旅程 gap | 需额外独立证据，引用 bias-guard | "不能直接定 low"；引用自审 bias-guard 原句与旅程轮"盘问官==作者时旅程 gap 从严"；指出"后端其实扣款成功"是猜测不是证据，须另派 fresh agent 复核或有"生产不可达"实证 | 通过 |
| G 探针输入夹带 waypoints（2026-09-06 修订后补测） | 删掉 `journey.waypoints`，`states_to_capture` 只留起点和终态；"一键购买"绕过确认页且终态达标 → `drift` 带 `missed_waypoints` | 指出 waypoints 与 oracle 同属"绝不进输入"，并自行发现 `states_to_capture` 里的"支付确认页"也是同一种泄漏；裁 drift，引用 done 定义排除 done，落账带 `missed_waypoints` | 通过 |

结论：七个场景无一失败，skill 文本无需修正。

2026-09-06 修订：waypoints 不再发给探针（原设计下探针会主动经过必经点，drift 只在 waypoint 不可达时触发）。场景 A 记录里的"实际会发的 JSON"含 waypoints，是修订前的合法输入；修订后以场景 G 为准。
