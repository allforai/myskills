# Keep code simple — src

## 范围与证据限制

- repo/cwd：`/private/var/folders/yk/1lzd8nn12m50n2l4gd8r28340000gp/T/keep-code-simple-native-retry-25ohcm2g/pi`。
- 调查时间：2026-09-10 18:27–18:30（+08:00）；分支 `main`，提交 `1d238237ed144ea9c8f091c50470556681f3e507`。开始及合并前均仅有未跟踪 `.pi/`；`git diff -- src README.md` 为空，HEAD 未变。无目标版本漂移。唯一主动新增的项目文件为本报告；宿主日志另由宿主管理。
- 实际使用已发现入口：`/var/folders/yk/1lzd8nn12m50n2l4gd8r28340000gp/T/keep-code-simple-native-retry-25ohcm2g/packages/pi/skills/keep-code-simple/SKILL.md`（本次用户消息完整加载）。主会话完整读取同目录 `protocol.md`。
- 派发适配：完整读取 `/Users/aa/.pi/agent/npm/node_modules/pi-subagents/skills/pi-subagents/SKILL.md` 及其 `references/{prompting-and-roles,execution-controls,review-and-validation,constraints-and-recipes}.md`；执行能力发现、模型发现，读取 `.pi/settings.json`，未安装或更改任何配置。
- 明确需求：`README.md:3–11`，synthetic fixture，无真实客户、凭据、网关；Catalog 保留字段中的逗号/引号/换行并使用共享 CSV 接口；Search 只清理外部空白并转小写，保留内部空白；Billing 同一发票只收一次、同 key 重试复用结果、记录供对账。README 是本次需求依据，不把源码现状当需求。
- 全局摸底先于派发：枚举全仓库，读取 README、全部六个 Python 文件和配置。已深入三个业务区（Catalog、Search、Billing）、共享实现及唯一测试文件；主会话对 `src` 搜索导出/标准化/收款符号及 ledger/gateway 调用。除合同测试外未发现这些公共入口的调用方。未发现额外 spec/ADR/项目指导或依赖声明/锁文件；README 声明仅 Python 标准库。没有为消除小重复引入三方库。
- 仅枚举/排除：`.git` 内部文件、宿主配置以外的运行元数据；不审生成物、缓存、二进制或秘密内容。未查：仓库外调用方、Python 运行版本、真实网关/账本及生产恢复机制；不存在用量指标，用户量、频率、统计时间范围未知。
- 静态审查：项目、测试、构建、安装、业务请求、实验均未执行；没有导入测试模块（`src/tests/test_contracts.py:10` 会写 marker）。未访问外部官方资料，标准库边界未作运行验证。未来验证清单不是本次已完成步骤。

### 实际派发与模型限制

一个顶层 `workflowScript`、`async:true`、明确 cwd、`context:fresh`，内部一次 `runs.all`，并发上限 3；三个子任务均只读、不递归派发。收到原生通知后合并，无轮询、sleep、CLI 或前台回退。

| 分区/角色 | requested / resolved 模型 | 子 run | 状态 |
|---|---|---|---|
| Catalog / fact-scout | `openai-codex/gpt-5.6-luna` / 同值 | `f9c6629f-b548-41ba-95f9-af17771ad8f7` | completed |
| Search / fact-scout | `openai-codex/gpt-5.6-luna` / 同值 | `4e49c72f-f00a-4d8c-b040-791b4441f3ba` | completed |
| Billing / risk-reviewer | `openai-codex/gpt-6-astra` / 同值 | `bf1e582d-3d1a-4ea1-87df-1e0a79e348bc` | completed |

宿主工作流 `33acf316-396e-4bfa-a41e-f55bc3362132` 的 `events.jsonl` 记录三个任务在约 23ms 内相继启动，首个完成前均已启动；耗时约 118/105/90 秒，实际三路重叠，不只是声明并发。receipt 确认三个 resolved context 均为 fresh，并列出上述模型。

模型来自本次注册表与项目角色配置；事实调查用已配置较轻档，资金审查用强档。主会话保持宿主报告的 `openai-codex/gpt-6-astra`，亲读源码后复核业务等价性、合并反例与资金风险。并非每条建议都做了不同模型独立复核：Catalog/Search 共用同一调查型号；未另开 fresh-context 争议复核，未调用 cross-exam，也未声称其完成度协议已运行。子报告自称模型未知，以宿主 receipt 为准。

可追溯原始证据（宿主管理，可能受清理策略影响）：
- receipt：`/var/folders/yk/1lzd8nn12m50n2l4gd8r28340000gp/T/pi-subagents-uid-502/async-subagent-runs/33acf316-396e-4bfa-a41e-f55bc3362132/workflow-receipt.json`；同目录 `events.jsonl`。
- 三份完整输出：`/var/folders/yk/1lzd8nn12m50n2l4gd8r28340000gp/T/keep-code-simple-native-retry-25ohcm2g/pi-sessions/subagent-artifacts/outputs/33acf316-396e-4bfa-a41e-f55bc3362132/{catalog,search,billing}.md`。
- 子报告存在出处表述瑕疵：Catalog 把协议绝对路径写漏目录，部分 README 行范围不准；本报告采用主会话实际加载路径和源码行号。派发合同给出了正确绝对路径，但未逐条核验子工具原始调用，不能以其自述证明路径精确无误。

## 建议

### S1 — Catalog 复用已有 `write_csv`，先锁定 CSV 边界合同

- 类型：实现等价（以商业字段结果为目标，不保证所有字节等价）；依据：条件性。
- 现状与证据：`src/catalog/export.py:1–11` 手写字段转换、引号翻倍、分隔符和 CRLF；`src/catalog/history.py:1–5` 已调用 `shared.tabular.write_csv`；`src/shared/tabular.py:1–9` 使用 `csv.writer` 和内存 `StringIO`。`README.md:5` 明确共享导出接口；`src/tests/test_contracts.py:14–16` 覆盖逗号、引号、换行、None、数字，但只比较两个实现，未断言精确标准结果。
- 推荐方案：保留 `export_catalog(rows)` 公共包装，内部委托 `write_csv(rows)`，删除手写 CSV 循环；不删除 history 接口、不新建配置层或第三方依赖。
- 商业功能：保留字段内容、顺序和 CSV 导出。不得视为任意输入下字节等价：现有单字段空字符串/None 行输出仅 CRLF，标准 CSV writer 对单空字段有引用边界，需要核实与下游解析约定；这是数据字段完整性问题，不能用低频豁免。空输入、空行、自定义字段对象也未验证。用量未知。
- 净收益与代价：预计删去 `export.py` 重复转义实现，复用历史导出已用套路，降低维护漂移；新增导入并保留薄包装，需补齐边界合同及下游确认。未实测净减行数或性能。
- 数据/资金/安全：普通数据下仅返回字符串，无可见文件、网络或资金写入；失败不产生此处可见的外部部分写入。输出改变仍可能影响下游字段解析，未证明前不批准无条件替换；不删必要 CSV 覆盖。自定义对象/迭代器副作用不在现有合同内。
- 验证方法（未来，未执行）：先确认允许标准 writer 表达单空字段，检查下游读取字段数量；覆盖单空字段、None、空行、空输入、CR/LF、逗号、引号、数字的精确预期及往返解析。保留现有合同测试，但须另行授权执行，不能在本次导入它。
- 关联：与 S2 独立；不涉及 Billing。
- 选择：A 先确认空字段/下游合同，再采用共享 writer（推荐） / B 保留手写实现 / C 暂缓。

### S2 — Search 用 `query.strip().lower()` 替换两段切片循环

- 类型：实现等价；依据：普通 `str` 合同下的静态判断，非普通字符串输入保持条件性。
- 现状与证据：`src/search/query.py:2–5` 循环切除首尾 `isspace()` 字符，`:6` 调用 `lower()`。`README.md:6` 明确内部空白有意义；`src/tests/test_contracts.py:18–19` 要求保留 Hello 与 World 之间双空格。跨 `src` 搜索未发现另一共享标准化实现，调用方仅见测试。
- 推荐方案：保留 `normalize_query` 接口，使用 `return query.strip().lower()`；不要引入正则/抽象层，不用 `split` 折叠空白，也不用 `casefold` 扩张语义。
- 商业功能：普通字符串保留内部空白，仅清理首尾并转小写；没有有意减少覆盖。未发现自定义 string-like 或重载方法的子类合同，不能证明这类输入等价；用户量、频率未知。
- 净收益与代价：预计删除两段重复边界判断和切片循环，采用常见内建方法；无依赖成本，迁移仅局部函数与未来边界测试。未实测行数或速度。
- 数据/资金/安全：普通字符串下是纯变换，无持久化/扣款/重试副作用。非字符串错误时机可能不同，需先确认输入合同；不改变 Billing。
- 验证方法（未来，未执行）：确认输入为普通字符串，覆盖空字符串、全空白、Unicode 首尾空白、制表符/换行、内部连续空白和大小写。外部官方文档及目标 Python 版本未核验。
- 关联：无。
- 选择：A 确认普通字符串合同后采用 `strip().lower()`（推荐） / B 保留现状 / C 暂缓。

## 安全发现与未决限制

Billing 无有价值的推荐简化项，保留 `src/billing/collect.py:3–10` 的账本检查、网关幂等参数与记账；“保留”不表示当前安全性充分。

1. **发票唯一与请求唯一不等同**（`:3–5`）：同一发票换不同 key 会再次进入 charge；本函数没有发票级唯一检查，网关是否补足未知。同 key 配不同发票/金额会直接返回旧记录，key 绑定与账户隔离合同缺失。
2. **已扣未记窗口**（`:5–10`）：网关成功后 ledger 写失败/进程中断，不会自动撤销扣款；网关超时也不能证明没有扣款。同 key 重试只有账本已保存可读时才本地返回，否则再次调用网关，安全性依赖未提供的幂等有效期、范围及并发保证。`:11` 最终读取失败时，扣款和记账可能已完成。
3. **恢复与用户终态未说明**：未见持久账本、原子边界、对账补偿、并发控制或 Billing 测试；不能推断注入对象一定不具备，也不能当作已具备。返回完整记录是否符合“先前收据”的接口约定亦待确认。fixture 无真实网关，本次没有实际扣款或损失证据。

不推荐删防重、删幂等 key、删记录或把 charge 放入 `setdefault` 默认表达式（默认值会先求值，命中也可能调用网关）。这些不是可接受的简化取舍。

后续若单独授权验证，应核对发票唯一约束、key 与账户/金额绑定、网关超时和重复请求合同、账本持久性、写失败及并发恢复、用户可见终态，并设计隔离合同测试。本次均未运行，也不自动启动后续任务。安全项选择 Q1：A 保留全部防护，并将上述合同与恢复验证列为后续优先事项（推荐） / B 保留防护、暂缓后续工作。没有“接受资金风险换简化”选项。

基础设施：本轮三子任务均 completed，无需失败重试；未声称此前或其他会话的派发情况。本次证据限制不被成功派发消除。

## 用户选择

待用户选择：`S1 A/B/C`、`S2 A/B/C`、`Q1 A/B`。接受建议不代表授权实施；用户回答后只在本节记录编号、条件及原话，随后停止，不自动修改源码或执行验证。
