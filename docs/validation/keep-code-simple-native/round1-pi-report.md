# Keep code simple — src

## 范围与证据限制

- repo/cwd：`/private/var/folders/yk/1lzd8nn12m50n2l4gd8r28340000gp/T/keep-code-simple-native-2v5evcm7/pi`；共享原工作区，未创建 worktree。
- 分支 `main`；提交 `1d238237ed144ea9c8f091c50470556681f3e507`。调查时间：2026-09-10 10:18–10:21 UTC。开始及派发结束后的 Git 查询均仅有未跟踪 `.pi/`，暂存及未暂存 tracked diff 为空；目标无已发现版本漂移。随后主会话仅新建本报告，不覆盖既有报告。
- 已发现并完整加载的 skill：`/var/folders/yk/1lzd8nn12m50n2l4gd8r28340000gp/T/keep-code-simple-native-2v5evcm7/packages/pi/skills/keep-code-simple/SKILL.md`。
- 已完整加载的协议：`/var/folders/yk/1lzd8nn12m50n2l4gd8r28340000gp/T/keep-code-simple-native-2v5evcm7/packages/pi/skills/keep-code-simple/protocol.md`。
- 已加载安装版 `/Users/aa/.pi/agent/npm/node_modules/pi-subagents/skills/pi-subagents/SKILL.md` 及 `references/{prompting-and-roles,execution-controls,review-and-validation,constraints-and-recipes}.md`，并读取项目代理与设置。未调用 cross-exam 或其他审查 skill。
- 明确需求：`README.md:3–11`。Catalog 保留 CSV 字段中的逗号、引号与换行；Search 仅裁剪外侧空白并转小写，内部空白有意义；Billing 每张发票仅收一次、同键重试复用回执、记账供对账。README 明确为无真实客户、网关和凭据的夹具，无用量指标；不能把夹具当生产运行证据。
- 全库地图在派发前完成：主会话完整读取 README、全部六个 Python 文件（Catalog 两个、Search/Billing/Shared/Tests 各一个）；跨 `src` 搜索导出、规范化、收款及公共实现符号。入口为各模块函数，仓库内调用证据仅测试和 history→shared；未发现应用入口、其他指导/spec/ADR、依赖声明或锁文件。标准库约束依据 README 与源码 import，不是安装环境检测。
- 分区覆盖：Billing 已深入独立静态调查并由主会话合并；Catalog、Search 已由主会话在摸底时完整读源码及相关测试，但委派调查失败，独立调查与等价性复核未完成。它们的下述候选仅为派发前证据形成的待证假设，不是失败后的串行替代执行。Shared/Tests 已读；`.pi/` 仅检查调度配置；Git 对象、hooks、缓存、生成物、秘密文件不作业务审查。仓库外调用者、部署、真实存储与网关未查。
- 静态审查：未运行项目、测试、构建、安装、迁移、业务请求或实验；尤其未导入 `src/tests/test_contracts.py`（第 10 行顶层写 marker）。没有运行验证、基准或净行数测量，也未查询外部官方资料；Python 精确版本未确认。未增加新依赖。

### 实际派发与模型限制

单一顶层 `workflowScript`，`async:true`、明确 cwd、`context:fresh`，内部一次 `runs.all`，并发上限 3、派发预算 3。均为发现列表中的 executable、非 disabled 原生只读代理，工具限 read/grep/find/ls；未使用外部 CLI。

工作流 `efaa1c00-435c-4ca3-a492-7fd0c77ee968` 已完成，但三个子任务并非全部成功：

| 分区/角色 | requested（代理配置） / 宿主记录模型 | child run | 状态 |
|---|---|---|---|
| Catalog / fact-scout | `openai-codex/gpt-5.4-mini` / 同名，但服务拒绝，未成功推理 | `070f9eee-e2dc-446d-8d27-b2750ebe5707` | failed，未返回调查证据 |
| Search / fact-scout | `openai-codex/gpt-5.4-mini` / 同名，但服务拒绝，未成功推理 | `c1bb3546-cceb-4c6d-b94d-6d729922c123` | failed，未返回调查证据 |
| Billing / risk-reviewer | `openai-codex/gpt-6-astra` / `openai-codex/gpt-6-astra` | `ce505749-ece9-4d29-94bc-1a7d828e81d1` | completed |

两个失败的精确错误相同：

```text
Run fan-out: 3/3 used, 0 remaining
Codex error: The 'gpt-5.4-mini' model is not supported when using Codex with a ChatGPT account.
```

事件记录显示三个任务在 `1789035559550`、`1789035559566`、`1789035559572` ms 启动，前两者约 2 秒后失败，Billing 约 97.8 秒完成：实际发生并发派发/启动重叠，但只有一个调查成功，不能宣称完成至少两个并发只读调查或成功跨模型复核。能力发现不等于账号模型可用性；未更换账号、安装服务、重试或切换 CLI/前台/其他 harness。失败路径已停止，预算已用完。Billing 子报告自报模型未知，以上 resolved 型号来自宿主 receipt，而非推测；主会话精确型号未查询。

证据文件（宿主管理，不是调查员写目标项目）：
- receipt：`/var/folders/yk/1lzd8nn12m50n2l4gd8r28340000gp/T/pi-subagents-uid-502/async-subagent-runs/efaa1c00-435c-4ca3-a492-7fd0c77ee968/workflow-receipt.json`
- 同目录 `events.jsonl`：并发及完成/失败时间证据。
- Billing 原报告：`/var/folders/yk/1lzd8nn12m50n2l4gd8r28340000gp/T/keep-code-simple-native-2v5evcm7/pi-sessions/subagent-artifacts/outputs/efaa1c00-435c-4ca3-a492-7fd0c77ee968/billing.md`。已完整读取；其源码证据也由主会话直接读取。

## 建议

### S1 — 待验证后让 Catalog 复用现有 write_csv

- 类型：实现等价（目标）；依据：条件性，独立调查失败，未完成边界等价性复核。
- 现状与证据：`src/catalog/export.py:1–11` 手工转字符串、转义引号、连接字段与 CRLF；`src/catalog/history.py:1–5` 已调用 `shared.tabular.write_csv`；`src/shared/tabular.py:1–9` 已使用 `csv.writer` 与 `StringIO(newline="")`。明确需求见 README:5；`src/tests/test_contracts.py:13–16` 用逗号、引号、换行、None、整数与普通字符串比较两种导出。跨 src 搜索未发现其他 CSV 实现。
- 推荐方案：先核查有效输入域与 CSV 边界，再把 export_catalog 的手工实现换为与 export_history 相同的委托；保留公开函数，不新建框架或模式参数。
- 商业功能：目标保留标准 CSV 内容、转义与行尾；无意减少功能。空单字段行等手工 writer 与标准 writer 的输出差异须确认是否属于承诺格式，不能声称所有输入字节等价。实际用户量与频率未知。
- 净收益与代价：预计删除 export.py 中手工转义和拼接循环，统一既有导出规则，不增加依赖；需要补齐边界契约与测试，未实测删除行数或迁移成本。
- 数据/资金/安全：函数返回字符串，所见实现无写盘、网络或扣款；但 CSV 格式错误仍可能损害下游数据解释，不能以用量低豁免。失败时未见持久副作用；仓库外消费和恢复方式未知。
- 验证方法：未来比较空 rows、空 row、单空字段、None、引号、逗号、CR/LF、Unicode、数字与约定输入容器，确认 CRLF 与有效 CSV 语义；本次未执行，现有测试也未运行。
- 关联：无。
- 选择：A 先完成同协议调查与边界验证，再判断复用（推荐） / B 保留现状 / C 暂缓。

### S2 — 待确认字符串契约后以 strip().lower() 替换 Search 两段循环

- 类型：实现等价（目标）；依据：条件性，独立调查失败，未完成等价性复核。
- 现状与证据：`src/search/query.py:1–6` 用 isspace 与切片循环裁剪两端，再 lower；README:6 要求内部空白保留；`src/tests/test_contracts.py:18–19` 仅覆盖 `'  Hello  World\n'`。跨 src 搜索未发现其他规范化工具或调用者（除测试）。
- 推荐方案：确认支持普通 Python 字符串输入后，直接返回 `query.strip().lower()`；不引入正则、新依赖或共享抽象。
- 商业功能：目标保留两端空白裁剪、小写转换及内部空白；不采用 split/join（会改变内部空白）或 casefold（不同大小写语义）。不擅自承诺非字符串、自定义对象的行为等价。用户量、频率与输入类型完整契约未知。
- 净收益与代价：预计删除 query.py 两段手动扫描/反复切片，使用常见标准方法；需验证输入契约及边界，未测性能或净行数。
- 数据/资金/安全：已见链路仅返回字符串，无写入或资金副作用；若误改内部空白会改变检索意义，必须保留。外部搜索系统及错误处理未查。
- 验证方法：未来覆盖空字符串、全空白、混合及 Unicode 边缘空白、无边缘空白、内部连续空白、Unicode lower，并界定非字符串输入；本次不执行。
- 关联：无。
- 选择：A 先完成同协议调查并确认输入/空白等价性（推荐） / B 保留现状 / C 暂缓。

### Billing 观察 — 不推荐缩减现有防护

已深入调查，没有查证值得推荐的等价简化。`src/billing/collect.py:3–11` 的本地命中返回、gateway 幂等键、包含发票/金额/回执的 ledger 记录均应保留。删除 ledger 违反对账要求；仅依赖网关会丢失本地直接返回语义；`setdefault(key, gateway.charge(...))` 会先求值默认参数，已有键也可能发起 charge。为单一函数增加通用支付框架没有已证明的删除收益。不把这些方案列为可接受选项。

## 安全发现与未决限制

以下是已有静态保证缺口，不是实际事故证据，也不是简化收益；不存在让用户接受资金或数据风险换简化的选项。

1. **发票级唯一收款未在本地建立**：`collect.py:3–5` 仅按 request_key 去重，同一 invoice_id 使用不同键会再次进入 charge。README:7 要求一张发票只能收一次；实际能否重复扣款取决于未知网关/上游契约。
2. **扣款与记账之间的失败窗口**：第 5 行 charge 后第 6–10 行才记账。响应丢失、写入失败或进程中断可能留下已扣款未记账；重试又进入 charge，其安全性依赖网关幂等范围、期限、重放与恢复能力。异常传播不是回滚；代码未给出确定终态、补账或对账恢复途径。
3. **并发、键复用与隔离契约缺失**：检查、charge、写入并非可见原子操作；同键不同发票/金额直接返回旧记录；ledger 持久性和账号范围未知。不能断言一定发生跨账号污染，也不能声称已保证安全。
4. 未来应先明确网关、存储和上游契约，再验证同键重试、同发票异键、同键异参数、并发、扣款后响应丢失、记账/读取失败、重启和幂等期限边界下的回执恢复与补账。现有测试没有 Billing 覆盖；上述验证及修复均未执行，不由本次审查授权。
5. Catalog/Search 失败路径不继续；如选择重试，需要明确同协议重试、确认当前账号可用模型与新预算，并再次检查工作区。不得把发现列表中的型号当成功运行证明。此次仅保存预先读到的候选，三分区完整独立审查目标未完成。

集中限制选择：
- **R1**：A 后续明确同协议重试失败的两个调查，先确认可用模型与预算（推荐） / B 暂缓这两区审查。该选择只记入报告，不在本次自动重派。
- **B1**：A 保留 Billing 防护，优先另行验证上述资金保证（推荐） / B 保留防护并暂缓评估。两项均不表示现状已安全，不允许自动接入真实资金场景。

## 用户选择

待用户选择：S1、S2、R1、B1。接受建议不代表授权实施或运行测试；用户选择只记入本节。尚未收到任何选择，未实施任何建议。
