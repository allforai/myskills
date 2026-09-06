# Cross-exam visual acceptance implementation validation

实现：Claude/Codex 同构可选视觉 facet；共享 SwiftUI 验收摘编与 MIT 许可；完整矩阵生成；逐类确认基线；独立单审/双审及失败降级；renderer 证据门。

验证命令：

```sh
python3 -m pytest codex/cross-exam-skill/scripts codex/cross-exam-skill/visual -q
python3 -m pytest claude/superstorm/scripts/test_render_report.py claude/superstorm/scripts/test_check_skill_refs.py claude/superstorm/knowledge/cross-exam/visual -q
python3 shared/visual-acceptance/sync.py --check
```

结果（思维测试修复后）：Codex 81 passed，Claude 77 passed。包含旧 ledger 兼容、renderer 缺图拒渲、基线确认/摘要、环境不匹配、假图片、路径逃逸、审图遗漏、双审并集/降级、未测/不适用计数及 2,187 项笛卡尔积无截断测试。Skill frontmatter 校验通过。

本轮补齐：冻结页面清单与完整矩阵对账，漏页仍显示未测；稳定内容用例 ID；构建、视觉/交互基线及清单/矩阵共同绑定；禁止双审静默改单审；参考图片和实际审图内容摘要绑定；Pillow 真实解码；动态帧拒绝重复路径、重复像素（含不同编码）及缺失/倒序/非有限/负数时间。单审、动态帧正常路径和 renderer 集成均有回归用例。两端镜像一致性与 git diff --check 通过。Pillow 依赖随包声明，缺失时不能降低图片验证标准。

SwiftUI capture smoke：`python3 shared/visual-acceptance/smoke_swiftui.py /tmp/cross-exam-visual-smoke-20260906` 成功构建并在新建临时 Simulator 启动小样，采集正常/加载/空/错误 × 浅/深色共 8 张截图。临时模拟器已关闭删除；截图与 capture-context.json 保留在上述临时目录。

人工图像检查：normal-light 确认真实 Home/Tab/按钮渲染，但初次系统 Apple Intelligence 通知遮挡顶部；error-dark 确认错误文案与深色渲染且无遮挡。这里仅证明构建/运行/截图通路，不能作为正式视觉验收通过或完整设备/字号/语言覆盖的证据。

边界：本次未对真实产品运行用户逐类确认和 Claude/Codex 付费 CLI 双审会话；双审校验以结构化 fixture 测试。本轮证据门修复未重跑上面的 Simulator smoke。文件存在、图片可解码、摘要和 reviewer 自报无法单独证明视觉真实性，协议仍要求主会话核对实际工具取证和看图记录。
