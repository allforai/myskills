# keep-code-simple — 三端原生会话验收

日期：2026-09-10。**入口、实际并发调查、报告生成：三端均已验证；Claude/Pi 有实际多型号消息证据，Codex 只能确认选模请求，resolved 子模型未知。** 输出质量仍有观察项，不以 CLI 退出码或模型自述代替验收。

本文记录修改前的历史基线；后续规则修订与验证见[证据措辞定向回归](keep-code-simple-evidence-regression.md)。原始报告和源码摘要保留，不用新版本覆盖旧验收。

## 环境与范围

- Claude Code 2.1.267；Codex CLI 0.153.4；Pi 0.85.1 + 已安装 pi-subagents 0.66.0。
- 同一份合成项目的独立副本，各有 Catalog、Search、Billing 三个分区、共享 CSV writer 和两个只读测试样例。无真实网关、账户资料或客户数据。
- 原始输入：[fixture README](keep-code-simple-native/fixture-readme.md)；源文件模板：[native fixture](../../fixtures/keep-code-simple/native/)。测试在仓库中存为 `.py.fixture`，仅在隔离副本中改名，避免普通测试发现误执行。运行前为 README/src 建立逐文件 SHA256 与临时 Git 基线。
- 临时加载：Claude `--plugin-dir`；Codex 项目 `.agents/skills/cross-exam/`（包括嵌套入口）；Pi `-e <本地包>` 加已安装的 pi-subagents。没有修改全局安装、配置或真实业务源码。
- 明确要求真实运行已发现的 skill，不把协议内联进提示，不允许入口未发现时猜路径代替加载。并发要求是本次验收参数；不把这么小的项目必须并发固化到 skill 默认流程中。
- Claude 使用 restricted/dontAsk，保留原有用户调用 hook，仅允许报告路径写入；Codex 使用 workspace-write/never，未绕过沙箱；Pi 使用临时只读角色与项目选模配置。Pi 不是 OS 级沙箱，实际权限行为另由工具记录和文件快照核对。
- [证据索引](keep-code-simple-native/evidence.json) 保存命令、运行目录、版本、原始日志路径及摘要、源码基线、入口/协议摘要、派发与模型记录。报告原件已复制入库；更大的会话日志仍在宿主存储，不保证永久保留。

## 验收矩阵

| 项目 | Claude | Codex | Pi |
|---|---|---|---|
| 原生入口发现/加载 | 注册 `superstorm:keep-code-simple`；本次 `/keep-code-simple src` 成功扩展 | 原生消息中明确扩展嵌套 `keep-code-simple/SKILL.md` | 包内 skill 通过 `/skill:keep-code-simple src` 加载 |
| 包内协议 | 已读取，和仓库源摘要一致 | 已读取，和仓库源摘要一致 | 已读取，和仓库源摘要一致 |
| 实际并发 | 同批 3 个 Agent，子消息交错返回，非顺序执行 | 3 次 spawn 成功均早于首个子任务完成；3 份任务消息返回 | 一次 async workflow/runs.all，3 个 fresh 子任务在约 23ms 内启动，均完成 |
| 实际模型证据 | 子消息 metadata：Catalog/Billing 为 `claude-opus-5`，Search 为 `claude-sonnet-5` | requested 为 `gpt-5.6-luna` ×2、`gpt-6-astra` ×1；未暴露 resolved，不宣称已证实不同模型执行 | 子会话 metadata：Catalog/Search 为 `openai-codex/gpt-5.6-luna`，Billing 为 `openai-codex/gpt-6-astra` |
| 报告产出 | 有，含具体建议和集中选择 | 有，含具体建议和集中选择 | 有，含具体建议和集中选择 |
| 源码完整性 | 基线文件摘要/文件集合未变 | 基线文件摘要/文件集合未变 | 基线文件摘要/文件集合未变 |
| 测试/业务执行 | 转发工具轨迹只有读取/搜索，主会话仅写报告；无 marker | 可见主会话轨迹无项目执行；子任务完整工具轨迹不可见，无 marker | 子会话轨迹为读取/搜索及非阻塞进度通知，无 shell/业务执行，无 marker |
| 中途业务决策/实施 | 无 AskUserQuestion；报告后才列选择，没有实施 | 可见轨迹未出现中途业务决策，报告后列选择，没有实施 | 无阻塞式访谈；报告后列选择，没有实施 |

Codex 的 CLI JSON 流未呈现 spawn 细节；上表的并发判断来自**原生持久化 rollout**，不是报告自称并发。Claude 的模型判断来自按 `parent_tool_use_id` 关联的 assistant metadata，而非子代理自报。Pi 的模型判断来自 receipt 与子会话 assistant metadata 交叉检查。

## 两轮执行与失败保留

### 首轮

- Claude：CLI exit 1，模型尚未启动。原始错误：`Input must be provided either through stdin or as a prompt argument when using --print`。原因是测试命令的可变长 `--allowedTools` 吞掉了位置 prompt；不是 skill 加载失败。
- Codex：完成入口加载、三路调查与报告；约 249 秒。过程中有一次只读 exec 的进程创建失败，后续仍使用原生工具处理，没有切换 harness。
- Pi：入口加载、三路派发成功，但 Catalog/Search 的 `gpt-5.4-mini` 被当前 ChatGPT 账号拒绝：`The 'gpt-5.4-mini' model is not supported when using Codex with a ChatGPT account.` Billing 正常完成。该端正确标出未查/条件性建议，保留失败 run，没有换 CLI、换账号或让主会话冒充失败调查。

首轮报告：[Codex](keep-code-simple-native/round1-codex-report.md)、[Pi 部分报告](keep-code-simple-native/round1-pi-report.md)。Pi workflow：`efaa1c00-435c-4ca3-a492-7fd0c77ee968`。

### 同协议重试

先核验并保留失败现场与源码基线，再创建新隔离副本：

- Claude：仅为原 CLI 增加 `--`，明确分隔选项与 prompt；没有关闭 hook 或绕过权限。约 412 秒，3 子任务完成。
- Pi：原 Pi CLI 与 pi-subagents 协议不变；仅将临时 fact-scout 模型配置换为目录中可用、此次实跑成功的 `gpt-5.6-luna`，保留强风险角色。没有改 skill 型号规则或全局配置。约 330 秒，3 子任务完成。
- Codex 已成功，不重复运行。

重试报告：[Claude](keep-code-simple-native/round2-claude-report.md)、[Pi](keep-code-simple-native/round2-pi-report.md)；[明确重试理由](keep-code-simple-native/retry-reason.json)。Pi workflow：`33acf316-396e-4bfa-a41e-f55bc3362132`；Claude session：`136e57a3-a6e9-4500-8b90-be97e5469277`。

## 输出质量观察

这些不是入口/调度阻塞，但仍需人审，不应把运行成功理解为所有判断正确：

1. **Claude 对部分未知外部后果用词过强。** 报告 D2 写“同一发票被扣两次”、D3 写“一笔扣款彻底失去记录”，同时又承认网关/账本实现未知。源码可证明再次进入 charge 的路径，不能单凭这份 fixture 断定真实网关必然扣款或已造成损失。合理结论应是“本地保证缺口，后果取决于未提供的外部契约”。该报告仍保留全部资金防护，没有提出接受资金风险的选择。
2. **Claude 的 resolved 栏使用子代理自报，虽然旁注披露未确认。** 外部验收已用 metadata 证实实际型号，但报告自身最好在缺宿主确认时写 unknown/self-reported，而不是把自报当 resolved。现有适配已要求不把请求/自报当运行证明；本轮不以补更多规则掩盖模型遵循的方差。
3. **三端对 CSV 边界的深入程度不同。** Claude/Pi 指出单空字段与测试互比退化问题，Codex 更倾向于将复用列为实现等价并给边界限制。这正说明“商业功能保持”仍需要证据和人审，而不是跨平台照抄同一条建议。
4. Pi 子调查实际出现 `contact_supervisor(progress_update)`，属于非阻塞进度，不是对用户提问；没有项目执行或扩大权限。验收脚本一度把工具种类判得过窄，已按实际无副作用调用核实，未把它伪报成 skill 失败。

## 尚未覆盖

- 全局市场安装、更新/缓存刷新、所有版本的宿主兼容；本轮用原生临时/项目发现机制。
- 用户接受选项之后的原生续会话流程（先前只做过思维测试），以及真实大项目、长期中断恢复、跨模型争议复核的稳定性。
- Codex 子任务的完整底层调用与实际模型路由；当前只能确认请求、返回、源码状态及可见轨迹。
- “没有执行测试”的结论不是仅凭 marker：Claude/Pi 有可见工具轨迹佐证；Codex 子任务轨迹限制保留，不声称系统级禁止执行已被证明。

**本轮没有修改 skill 协议或平台适配。** 两处重试修正都在验证命令/临时配置中。若继续提高报告可靠性，优先复核上述证据措辞和真实项目表现，而非增加通用调度框架。
