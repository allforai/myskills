---
name: wireframe-review
description: >
  Use when the user says "wireframe-review", "review wireframes", "IA review",
  "线框审核", "交互审核", "结构审核".
  Low-fidelity structural review of IA and screen flows before visual design.
  Validates features, flows, and screen structure — issues route to product-map or experience-map.
arguments:
  - name: mode
    description: "start (launch review server) | process (read feedback and iterate)"
    required: false
    default: "start"
---

# Wireframe Review — 线框交互审核

## 模式

| 模式 | 触发 | 行为 |
|------|------|------|
| `start` | `/wireframe-review` 或 `/wireframe-review start` | 启动线框审核服务器 |
| `process` | `/wireframe-review process` | 读取反馈，路由到上游修复 |

---

## Mode: start

启动低保真线框审核服务器，供用户验证 IA 结构、屏幕流转和功能完整性。

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/wireframe_review_server.py <BASE> [--port 18902]
```

- `<BASE>` = `.allforai` 目录路径
- 服务器启动后会自动打开浏览器，**禁止**再用 Playwright `browser_navigate` 或其他方式重复打开同一 URL
- 局域网访问：加 `--host 0.0.0.0`
- 界面按**角色**或**情感旅程线**分组展示（By Role / By Journey 切换）
- 每个界面显示低保真线框图（灰色区块 + 动作按钮 + 情感指示 + 约束条件）
- 用户点击线框任意位置添加 pin 评论，并选择反馈类别：
  - **Flow/Structure** → 路由到 experience-map（流程不通、屏幕结构问题）
  - **Feature/Task** → 路由到 product-map（功能缺失/多余、任务分解问题）
  - **Concept** → 路由到 product-concept（产品方向问题）
- 审核完毕点击 "Submit Feedback" → 生成 `review-feedback.json` → 服务器自动关闭
- **服务器退出后**：Bash 输出包含反馈摘要（approved/revision 数量及评论内容），**自动进入 process 模式**处理反馈，无需用户手动运行 `/wireframe-review process`

---

## Mode: process

读取 `.allforai/wireframe-review/review-feedback.json`，按反馈类别路由到上游修复。

### 流程

```
1. 读取 .allforai/wireframe-review/review-feedback.json
   - 不存在 → 提示用户先运行 /wireframe-review start
   - submitted_at = null → 提示用户先在审核服务器提交反馈

2. 统计反馈
   - 输出：N 个界面已审核，M 个通过，K 个需修改
   - K = 0 → 全部通过，结构锁定，无需迭代，终止

3. 按反馈类别汇总 pin comments：
   a. category="product-map" 的 pins → 汇总为产品地图修改建议
      - 输出需要增删改的 task 列表
      - 提示用户手动调整 product-map 后重跑 experience-map
   b. category="experience-map" 的 pins → 汇总为体验地图修改建议
      - 输出需要调整的屏幕流转、screen 结构
      - 提示用户重跑 experience-map（或手动修改）
   c. category="concept" 的 pins → 汇总为概念级问题
      - 输出产品方向建议
      - 提示用户回到 product-concept 重新评估

4. 输出修复行动清单：
   「线框审核发现 K 个问题：
     - product-map 类: X 个（建议重跑 /product-map）
     - experience-map 类: Y 个（建议重跑 /experience-map）
     - concept 类: Z 个（建议重新评估 /product-concept）
   修复后运行 /wireframe-review start 重新审核。」

5. 更新 review-feedback.json：
   - round += 1
   - 修改过的界面 status 重置为 "pending"
   - 保留已通过界面的 status = "approved"
```

### Pin Comments 的解读

每个 pin 包含 `{x, y, comment, category}`：
- `x, y` — 线框预览中的相对坐标（百分比）
- `comment` — 反馈内容
- `category` — 路由目标：`product-map` | `experience-map` | `concept`

### 安全护栏

- 线框审核**不直接修改**上游产物（product-map、experience-map）
- 只输出修复建议，由用户决定是否执行上游重跑
- 每轮审核记入 pipeline-decisions.json
