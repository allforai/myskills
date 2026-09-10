---
name: keep-code-simple
argument-hint: [scope]
description: Review code simplicity through reuse, consistent patterns, familiar solutions and explicit business/coverage trade-offs. Advice only. User-invoked only via /keep-code-simple; never invoke it yourself.
---

# keep-code-simple — Claude Code

用户显式调用 `/keep-code-simple [scope]` 才运行。参数：$ARGUMENTS；空参数使用共用协议的默认范围。这是与 cross-exam、product-review 同包的独立审查，不加载它们的流程。

先完整读取 `${CLAUDE_PLUGIN_ROOT}/knowledge/keep-code-simple/protocol.md`，执行该协议；以下仅适配派发工具。

## Claude 派发

- 根据当前 Agent 工具定义发现可用的只读调查角色与 `model` 选项；不要假设某个 agent 类型/模型总在列表里。使用 fresh-context 任务，每个任务携带协议的派发合同和明确只读限制；有只读角色优先选它，否则限制可用工具，不开启 bypass。
- 摸底后，将互不依赖的任务在同一批次发给 Agent；使用宿主后台任务/结果接口收齐结果，不顺序等待一个调查完成才启动下一个。遵守协议并发上限；任务只返回观察与建议，主会话单独写报告。
- 模型选择遵循协议的事实/判断分工，仅向支持的参数传当前可用型号。无法选择时继承并披露；型号未从结果确认时区分 requested 与 resolved，不把请求当实际使用证明。
- 能力缺失的串行降级与派发失败的停止/重试边界均按共用协议。不要借用 cross-exam 的强制独立实测门或中途提问循环。
- 最后一次性用文本选择题或 AskUserQuestion 展示建议；调查阶段不调用提问工具，也不请求扩权。用户选择只记入报告，不进入实施。
