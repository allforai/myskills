# Step 4: 结构级对比

> 本文档由 cr-visual orchestrator 派遣的 **structural-compare agent** 加载。
> 职责：逐屏对比源/目标截图的 UI 结构，输出 structural_score。
> **本 agent 只关注结构**，不检查数据完整性和联动（由其他 agent 负责）。

## 对比协议

对每对截图（source/screen_name.png vs target/screen_name.png），LLM 用 Read 查看两张图片，评估：

**结构级对比（做）**：
- 区域划分是否等价？（头部/内容/底部/侧边栏）
- 关键 UI 元素是否存在？（按钮、输入框、列表、卡片）
- 数据展示区域的位置是否合理？
- 导航入口是否可见？（菜单、Tab、返回按钮）
- 信息层级是否一致？（标题 > 副标题 > 正文的层次感）

**不做**：
- 像素级颜色对比（目标可以换主题色）
- 字体/字号精确匹配（目标可以用不同字体）
- 间距/留白精确匹配（目标可以重新设计间距）
- 动画/过渡效果（截图看不到）
- 控件内数据检查（由 data-integrity agent 负责）
- 控件联动检查（由 linkage agent 负责）

**跨平台调整**：
- 如果 stack-mapping 有 `platform_adaptation.ux_transformations`
- 按转换期望评估：mobile 单列 → desktop 多面板不算 gap
- mobile 底部导航 → desktop 侧边栏不算 gap

## 输出

对每个 screen 返回：
```json
{
  "screen": "screen name",
  "structural_match": "high | medium | low | mismatch",
  "structural_score": 100,
  "differences": "LLM 自由描述差异",
  "source_screenshot": "visual/source/xxx.png",
  "target_screenshot": "visual/target/xxx.png"
}
```

> 此阶段仅输出 `structural_match` / `structural_score`，最终 `match_level` / `score` 由 orchestrator 合并计算。
