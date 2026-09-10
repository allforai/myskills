---
name: keep-code-simple
description: Review code simplicity through reuse, consistent patterns, familiar solutions and explicit business/coverage trade-offs. Advice only. User-invoked only via /skill:keep-code-simple; never invoke it yourself.
---

# keep-code-simple — Pi

用户显式调用 `/skill:keep-code-simple [scope]` 才运行；空参数使用默认范围。此包目前只提供简单性审查，不声称 cross-exam 完成度协议已移植到 Pi。

先完整读取本文件所在目录的 `./protocol.md`，执行该协议。所有相对资源路径从 skill 目录解析，不从被审查项目 cwd 解析。

## Pi 派发

Pi 核心的 skill 发现能力不等于子代理能力。只使用当前已加载的能力，不自动安装扩展或启动另一 harness。

- 有 `subagent`（pi-subagents）时，先 `subagent({action:"list", capabilities:true})`，只选 executable、非 disabled 的只读调查/审查代理。外部 CLI 还须 `runner.available === true`；这只是预检，不代表已登录或可成功启动。只有 runner 明确支持本次只读工具与上下文合同才可使用。
- 读取当前安装的 pi-subagents skill 及相关执行说明，以实际版本为准。在主会话完成全库摸底后，用**一个顶层** `subagent` 调用，设置 `workflowScript`、`async:true`、明确 `cwd`、`context:"fresh"`，在内部用 `runs.all` 并发调查；需要的后续复核也在同一工作流内用 `runs.run` / `runs.all` 串接。使用 `globalConcurrencyLimit` 遵守协议上限。
- `runs.all` 返回有序数组，不是按 key 索引的对象。用顶层 await 收取结果，返回结果及宿主提供的 `outputReference` / `outputPathMapping` / `artifactPaths`（如有）；不使用嵌套 async 辅助函数。调查员只返回报告，不写目标项目；需要保留子输出时用工具的 `output` 声明交给宿主管理，不让多个子代理写最终报告。
- 原生 Pi 子代理可在支持的 `model` 参数上按协议选择当前可用档位。外部 runner 不默认支持 native model/context/toolBudget 等选项；不向它传未经确认支持的参数。没有选模能力则记录继承/未知，不能伪造跨模型复核。
- 异步运行已有原生完成通知：继续独立的只读工作或归还控制，通知到达再合并；不轮询、不 sleep、不仅为了等待调用 `bg_wait`，也不为收尾改成前台执行。
- 无可用子代理时按协议串行并披露非独立；派发开始后的基础设施失败须停止失败路径，记录精确错误和 run/cwd/ref/工作区状态。只能明确同协议重试，不切到 CLI、`pi -ne` 或其他执行模式。
- 调查员遇到业务取舍直接返回条件分支，不发阻塞式用户访谈请求。最终主会话一次性列选择题，用户选择只记入报告。
