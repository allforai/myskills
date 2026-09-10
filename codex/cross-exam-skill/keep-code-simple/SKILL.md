---
name: keep-code-simple
description: Review code simplicity through reuse, consistent patterns, familiar solutions and explicit business/coverage trade-offs. Advice only. Run only when the user explicitly names keep-code-simple; never start it automatically.
---

# keep-code-simple — Codex

这是 cross-exam 安装包内可独立发现的第三个 skill。用户显式调用 `$keep-code-simple [scope]`，或通过 cross-exam 包路由点名它才运行。空参数使用默认范围，不加载完成度或产品审查流程。

先完整读取本文件所在目录的 `./protocol.md`，执行该协议；所有相对路径从本 skill 目录解析，不从被审查项目的 cwd 解析。

## Codex 派发

- 检查当前实际工具定义中的 `spawn_agent` 与等待/收取结果工具（不同版本名称可能不同）。缺任一必要能力时在派发前选择串行，不编造工具或参数。
- 只用当前支持的 fresh-context/read-only 配置，不继承整段作者对话。给每个任务共用协议的派发合同，限定文件读取/搜索工具，返回结果而非修改项目。不能提供独立上下文时披露限制。
- 摸底后，先启动一批互不依赖的调查任务，再使用宿主等待/结果接口收齐；遵守共用并发上限，主会话单独写报告。
- 仅在工具确实提供 `model` 参数时按协议分工，从实际可用列表选择模型。否则省略并继承会话模型，不改宿主全局配置或另起外部 CLI 来假装多模型。报告区分 requested/resolved；无法观察实际型号就写未知。
- 能力缺失可在预检时降级；已启动的派发失败按协议保留错误与未查范围，不自动切执行方式。
- 所有建议在调查结束后一次性用文本选择题呈现。选择只记入报告，不改代码、不自动派实施任务。
