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

## 第二轮（2026-09-06，版本 ee34a5e：G 号、waypoints 收回、步骤证据校验之后）

| 场景 | 通过判据 | agent 回答摘要 | 判定 |
|---|---|---|---|
| H 无基准模式（Codex 版） | 旅程镜头仍开，§1b 照做，报告声明关闭的只有需求覆盖与跑偏 | 引用 lenses.md 无基准段的旅程条款；指出用户口述旅程进 `journeys[]`、不回填 `baseline`，两条轨道正交 | 通过 |
| I census 失败 | 候选只来自需求基准与用户补充，不自己读代码；报告声明；探针输入不变 | 三点全中，引用 §1b 第 1 条末句和期望隔离条款 | 通过 |
| J 探针返回残缺（步骤合并、缺文件名、文件不存在） | 不补不拆不落账；重派一次；渲染器整条拒渲且旅程退回未盘问 | 逐条指出四处违规；"参照死/超时条款的精神"重派 fresh 实测官；说明拒渲后 J1 退回未盘问 | 通过。**文本缺口**：残缺返回无明文，agent 靠类推 |
| K 落账写法 | `q` 与 `entry_q` 逐字相同；`journey`、`steps`、`terminal_state`；不自编 G/J 号 | 全中，还指出 `status` 改了但 `entry_q` 对不上照样算未盘问 | 通过。**文本缺口**：agent 决定不写 `facet`，spec 本意 facet 仍必填，schemas.md 漏写 |
| L 扫全模式五条旅程 | 并行五个 fresh 实测官，输入无 oracle/waypoints；收齐逐条裁决、每条立刻落盘；同种 stuck_kind 建 pattern 并派枚举官（中立描述） | 全中，还指出 J4 应并入 J2 已建的 pattern 而非重复建 | 通过 |
| M 生产环境退款旅程 | §0 第 4 条生产一律拒绝；改本地后可派，前置条件由探针自造；本地退款不违反"只观察不修" | 全中，区分"能力前置门"与"安全确认"两种停法 | 通过 |
| P product-review 消费新报告 | Prior evidence 引 J1 gap；不再探；J2 done 只证在不在与走不走得完；G1 退款不对应 scope 内 job | 全中 | 通过 |
| Q canvas 应用无无障碍树 | 起点按字面落空树文本加截图；每步截图；终态快照仍抓 a11y 文本；预算尽即停 | 全中；主动推断"不该读源码找按钮坐标" | 通过。**文本缺口**：旅程不读源码找路无明文 |

三处文本缺口已补（同日提交）：§2 "实测官死/超时"扩为"死/超时或返回残缺"，明确不补不拆只重派；schemas.md 旅程 entry `facet` 仍必填、`leak_point` 可省；prober.md 纪律 7 加"旅程只走用户看得到的界面，不读源码找路"。
补后复测 J、K、Q 三个场景：agent 均直接引用新条文，不再类推。通过。
