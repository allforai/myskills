# Extraction Plan Review

> Phase 3-pre 末尾，extraction-plan.json 生成后立即执行。
> 本文档由 code-replicate-core.md 按需加载，不要提前阅读。

LLM 切换到**审查者视角**，审视自己刚生成的 extraction-plan，输出 `plan_review`（写入 extraction-plan.json 的 `plan_review` 字段）：

```json
{
  "plan_review": {
    "modules_examined": [
      {
        "module": "M003",
        "total_files": 78,
        "key_files_selected": 4,
        "coverage_assessment": "key_files 仅覆盖顶层入口（主 widget + 状态管理）。子目录 widgets/message_types/ 有 24 个文件处理不同消息类型渲染，chat_input/ 有 8 个文件处理输入交互（语音/拖拽/粘贴/表情）。这些子文件承载独立的用户可见功能，不被顶层入口覆盖。",
        "blind_spots": ["描述未覆盖的子目录/文件及其承载的用户功能"],
        "decision": "扩充 key_files：追踪入口文件 import 链，加入承载独立用户功能的子文件。预计从 4 → 22 个。",
        "rationale": "这些不是工具类文件——每个都承载用户可直接感知的功能。漏掉任何一个 = 目标产物缺失该功能。"
      }
    ],
    "overall_confidence": "审查后覆盖率从 5% 提升至 28%。剩余 72% 为工具类/模型类/配置类，不含独立用户功能。"
  }
}
```

## 审查推理指引（非硬阈值）

- **用户影响测试**：对每个模块，问自己："如果用户打开目标应用，哪些功能会因 key_files 未覆盖而缺失？用户会注意到吗？"
- **Import 链追踪**：从每个 key_file 出发，沿 import 链向下走一层，检查被引用文件是否承载独立功能（vs 纯 utility）
- **事件绑定链追踪（UI 项目重点）**：不只追踪 import，还要追踪**事件绑定**——按钮 onTap → Navigator.push → 独立页面（如转发面板、搜索覆盖层、全屏预览页）。这些二级入口不在 import 链上，但承载完整用户功能
- **枚举/switch 检测**：如果 key_file 中有 switch(type) 且 case > 5，每个 case 对应的渲染文件值得加入
- **子目录采样**：对未被 import 链覆盖的子目录，读取前 3 个文件头部（class 名 + 公开方法签名），判断是否有遗漏的用户功能
- **平台集成搜索**：主动搜索平台集成代码——系统级 UI（锁屏控件/通知栏/系统媒体中心）、语音助手集成、CarPlay/Android Auto、Widget/快捷方式等。这些在 app UI 之外但用户可感知（消失测试通过）。发现的平台集成功能加入 task_sources，category 标记为 `platform_integration`

审查完毕后，LLM 根据 plan_review 的结论更新 extraction-plan.json 的各 `*_sources` 字段（补充新发现的 key_files），然后继续。
