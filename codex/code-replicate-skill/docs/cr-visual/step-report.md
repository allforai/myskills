# Step 5: 报告合并 + 评分

> 本文档由 cr-visual orchestrator 派遣的 **report agent** 加载。
> 职责：合并 structural / data-integrity / linkage 三个 agent 的结果，计算最终评分，生成报告。

## 输入

- **structural agent 输出**：每个 screen 的 structural_score + differences
- **data-integrity agent 输出**：每个 screen 的 data_integrity_score + data_integrity_gaps[]
- **linkage agent 输出**：每个 screen 的 linkage_score + linkage_results[]
- **visual-task-plan.json**：任务清单，用于统计完成率

## 评分合并公式

```
对每个 screen：
  final_score = structural_score - data_integrity_penalties - linkage_penalties
  final_score = max(0, final_score)

  match_level 由 final_score 决定：
    ≥ 90 → high | ≥ 60 → medium | ≥ 30 → low | < 30 → mismatch

全局：
  overall_score = avg(所有 screen 的 final_score)
  structural_avg_score = avg(所有 structural_score)
  data_integrity_avg_score = avg(所有 data_integrity_score)
  linkage_avg_score = avg(所有 linkage_score)
```

## 输出文件

写入 `.allforai/code-replicate/visual-report.json`：

```json
{
  "generated_at": "ISO8601",
  "total_screens": 20,
  "compared": 18,
  "skipped": 2,
  "overall_score": 68,
  "structural_avg_score": 82,
  "data_integrity_avg_score": 65,
  "linkage_avg_score": 75,
  "total_data_integrity_gaps": 7,
  "total_linkage_failures": 3,
  "screens": [
    {
      "screen": "...", "match_level": "high", "score": 100,
      "structural_score": 100, "data_integrity_score": 100, "linkage_score": 100,
      "differences": "无明显差异", "data_integrity_gaps": [], "linkage_results": []
    }
  ]
}
```

写入 `.allforai/code-replicate/visual-report.md`：
- 每个 screen 的截图路径对（用户可直接查看）
- 结构差异描述
- **数据完整性审计结果**（空控件清单 + 溯源结论）
- **控件联动验证结果**（联动检查点清单 + 失败根因）
- 整体评分（结构分 + 数据完整性分 + 联动分 = 综合分）
- 低分 screen 的修复方案（区分结构修复 / 数据链路修复 / 联动修复）

### ⚠️ 人工视觉验收清单（HUMAN_VISUAL_REQUIRED）

> 自动化视觉对比有天然盲区。以下维度 LLM 截图对比**无法可靠覆盖**，必须人工打开目标 App 逐项确认。

```
## LLM 视觉模型的系统性盲区

(始终)             □ 动画/过渡效果 — 截图看不到动画。打开页面，验证：页面切换、弹窗、下拉展开的过渡是否流畅
(始终)             □ 滚动体验 — 长列表滚动是否流畅？有没有卡顿/跳帧？
(若有 hover 效果)  □ Hover 态 — 鼠标悬浮时按钮/卡片的样式变化是否与源 App 一致？
(若有响应式)       □ 中间断点 — 拖拽浏览器窗口到 768px/1024px，布局是否正确切换？
(若有深色模式)     □ 深色模式逐页检查 — 切换到深色模式，每个页面是否有漏染的白色/亮色区域？

## 截图无法覆盖的交互

(若有拖拽)         □ 拖拽排序 — 拖拽操作的视觉反馈（占位符、阴影）是否与源一致？
(若有手势)         □ 手势操作 — 双指缩放、长按、左滑删除等手势是否正常工作？
(若有输入法)       □ 输入法交互 — 中文输入法联想词选择是否正常？日文/韩文输入呢？
(若有剪贴板)       □ 粘贴行为 — 从 Excel/Word 粘贴到富文本框，格式是否正确处理？

## 多媒体人工确认

(若有 CANVAS_DRIFT) □ 图表数据准确性 — 人工对比源/目标图表的具体数值（pixelmatch 标记了差异区域）
(若有 BROKEN_MEDIA) □ 缺失资源修复后确认 — 修复后的图片/视频是否显示了正确的业务内容（非另一张图）？
(若有视频)         □ 视频播放完整性 — 点击播放，视频是否能完整播放到结束？中间有没有卡顿/花屏？
(若有音频)         □ 音频正确性 — 播放音频，内容是否与源 App 一致？音量/音质是否正常？

## 复刻特有验证

(始终)             □ 字体渲染 — 目标 App 的字体是否与源 App 视觉一致？（不要求同字体，但要求同风格）
(若跨平台)         □ 平台适配合理性 — mobile→desktop 的布局转换是否自然？非机械拉伸？
(若有 i18n)        □ 文案完整性 — 逐页对比，有没有漏翻/硬编码的中文/英文？
```

> 生成规则：LLM 根据项目技术栈和 visual-report 中的发现动态裁剪。附截图路径帮助人工快速定位。
