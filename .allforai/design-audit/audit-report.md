# 设计审计报告

## 摘要

- 执行模式: full
- 可用层: product-map, screen-map, use-case, feature-gap, feature-prune, ui-design
- 逆向追溯: 252 项检查, 252 PASS, 0 ORPHAN
- 覆盖洪泛: 180 项检查, 180 COVERED, 0 GAP, 覆盖率 100%
- 横向一致性: 49 项检查, 45 OK, 3 CONFLICT, 1 WARNING
- 信息保真: 追溯完整率 100% (PASS) · 视角覆盖率 100% (PASS)

## CONFLICT（跨层矛盾）

| # | 检查项 | 任务 | 说明 |
|---|--------|------|------|
| 1 | X1 | 分享学习成果 | feature-gap 报 T016 有缺口，但 feature-prune 标为 CUT — 矛盾 |
| 2 | X1 | 管理个人设置 | feature-gap 报 T040 有缺口，但 feature-prune 标为 CUT — 矛盾 |
| 3 | X1 | 设置角色偏好 | feature-gap 报 T019 有缺口，但 feature-prune 标为 CUT — 矛盾 |

## WARNING（风险）

| # | 检查项 | 任务 | 说明 |
|---|--------|------|------|
| 1 | X3 | 创建场景对话脚本 | 高频任务 T009 的操作 '预览场景对话' click_depth=3 ≥ 3（被埋深） |
