---
name: keep-code-simple
description: Review code simplicity through reuse, consistent patterns, familiar solutions and explicit business/coverage trade-offs. Advice only. User-invoked only via /skill:keep-code-simple; never invoke it yourself.
---

# keep-code-simple — Pi

用户显式调用 `/skill:keep-code-simple [scope]` 才运行；空参数使用默认范围。不要加载或执行同包的 cross-exam 完成度协议。

先完整读取本文件所在目录的 `./protocol.md`，执行该协议。所有相对资源路径从 skill 目录解析，不从被审查项目 cwd 解析。

## Pi 派发

Pi 核心的 skill 发现能力不等于子代理能力。只使用当前已加载的能力，不自动安装扩展或启动另一 harness。

- 有 `subagent`（pi-subagents）时，先 `subagent({action:"list", capabilities:true})`，只选 executable、非 disabled 的**原生 Pi** 只读调查/审查代理（如 `reviewer`、`scout`、`oracle`、`delegate`）。**不要选外部 CLI runner**（`codex-exec`、`claude-code`、`cursor-agent`）：它们启动另一个 harness 和另一套模型，跑的不是本次会话的模型；`runner.available === true` 只说明命令在 PATH 上，不构成使用理由，也不是已登录或可启动的证明。
- 读取当前安装的 pi-subagents skill 及相关执行说明，以实际版本为准。在主会话完成全库摸底后，用**一个顶层** `subagent` 调用，设置 `workflowScript`、`async:true`、明确 `cwd`、`context:"fresh"`，在内部用 `runs.all` 并发调查；需要的后续复核也在同一工作流内用 `runs.run` / `runs.all` 串接。使用 `globalConcurrencyLimit` 遵守协议上限。
- `runs.all` 返回有序数组，不是按 key 索引的对象。用顶层 await 收取结果，返回结果及宿主提供的 `outputReference` / `outputPathMapping` / `artifactPaths`（如有）；不使用嵌套 async 辅助函数。调查员只返回报告，不写目标项目；需要保留子输出时用工具的 `output` 声明交给宿主管理，不让多个子代理写最终报告。
- **模型只用当前会话默认模型。** 子代理缺省继承会话模型，不传 `model` 去换 provider 或模型家族，不启用外部 CLI 来假装多模型。协议《模型分工》里的跨模型分工在本 Pi 适配下替换为：同一会话模型 + 不同思考等级 + fresh 上下文；**「已授权的不同模型可用时优先互补模型」在 Pi 不适用**——环境里就算有其它可用模型（含 Codex 一类），复核也只用当前会话模型的独立 fresh 上下文。其余（独立判断、合并、冲突保留）不变。
- **用思考等级控制成本与能力。** 省略时继承 agent 默认档位；需要显式分档时，只传当前会话模型自己的 `provider/id:<level>` 后缀（`off/minimal/low/medium/high/xhigh/max`），等级不超过宿主与用户配置的上限。定位、枚举、依赖资料收集用低档；业务等价性、抽象是否成立、跨模块冲突、数据/资金/安全风险复核用高档。**注册表里有 ≠ 额度可用**：优先用会话当前那条路由（额度状态已知）；按订阅或额度计费的其它路由即便出现在模型列表里也不代表可用，不要为了分档把通道铺到别的路由上。
- 子代理的模型与等级按宿主 metadata/receipt 记录；只能写成继承（inherited）或实际 receipt 型号，拿不到就写未知，不写“跨模型复核”。
- **派复核前先核对工具合同：** 协议要求「先查它为何存在」，靠的是 `git log` / `blame` / `-S` 这类只读 git 元数据。复核通道要给能跑它们的只读代理；只读审查类角色没有 shell 时，它的 git 结论只能标「无法核对」，关键提交归属由主会话自己核对，不采二手摘要。
- 异步运行已有原生完成通知：继续独立的只读工作或归还控制，通知到达再合并；不轮询、不 sleep、不仅为了等待调用 `bg_wait`，也不为收尾改成前台执行。
- 无可用子代理时按协议串行并披露非独立；派发开始后的基础设施失败须停止失败路径，记录精确错误和 run/cwd/ref/工作区状态。只能明确**同协议重试**，不切到 CLI、`pi -ne`、前台或其他执行模式。额度或容量耗尽属于可补跑的失败：**同一路由**、同协议、同一顶层工作流形态重试；补跑与仍在跑的通道合计不得超过协议并发上限（原工作流剩 1 条时补跑设 `globalConcurrencyLimit: 2`）。**该路由不可用不是换路由的理由**——把受影响的通道标未查，交用户决定，不自行换 provider / 模型家族。
- 失败通道算**未查**，不当作正常输入进入复核：复核只拿到部分报告时，报告的「派发」里要写明哪一分区没有覆盖，别让缺口看起来像已查过多遍。
- 派发时记下 `git rev-parse HEAD` 与工作区状态，收口时重查一次；目标在调查期间漂移（例如未提交的改动被提交）就重读受影响位置并在报告里标出。
- 调查员遇到业务取舍直接返回条件分支，不发阻塞式用户访谈请求。最终主会话一次性列选择题，用户选择只记入报告。
