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
