---
name: map-review
description: >
  Use when the user says "map-review", "review product map", "地图审核",
  "审核产品地图", "功能审核", "product map mind map".
  Interactive mind map review of product map — validate roles, tasks,
  and business flows before proceeding to downstream skills.
arguments:
  - name: mode
    description: "start (launch review server) | process (read feedback and route)"
    required: false
    default: "start"
---

# Map Review — 产品地图脑图审核

## 模式

| 模式 | 触发 | 行为 |
|------|------|------|
| `start` | `/map-review` 或 `/map-review start` | 启动脑图审核服务器 |
| `process` | `/map-review process` | 读取反馈，汇总修改建议 |

---

## Mode: start

启动产品地图脑图审核服务器，展示角色-任务-业务流的树形结构。

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/mindmap_review_server.py <BASE> --source product-map --port 18901
```

- 服务器启动后会自动打开浏览器，**禁止**再用 Playwright `browser_navigate` 或其他方式重复打开同一 URL
- 脑图包含：
  - 角色列表（audience type 标签）
  - 每个角色的核心任务 / 基本任务（频次 + 风险标签）
  - 业务流（步骤 + 角色流转 + GAP 标记）
- 点击任意节点展开/折叠子树
- 点击节点添加评论，选择评论类别
- 审核完毕点击 "Submit Feedback" → 生成反馈文件 → 服务器自动关闭
- **服务器退出后**：Bash 输出包含反馈摘要（approved/revision 数量及评论内容），**自动进入 process 模式**处理反馈，无需用户手动运行 `/map-review process`

---

## Mode: process

读取 `.allforai/product-map-review/review-feedback.json`，汇总反馈。

### 流程

```
1. 读取 .allforai/product-map-review/review-feedback.json
   - 不存在 → 提示先运行 /map-review start
   - submitted_at = null → 提示先提交反馈

2. 统计：N 个节点已审核，M 个通过，K 个需修改

3. K = 0 → 地图确认，进入 journey-emotion

4. K > 0 → 汇总修改建议：
   - 角色类问题：角色增删改
   - 任务类问题：任务增删改、频次/风险调整
   - 业务流问题：流程断裂、缺失步骤
   - 提示用户修改后重跑 /product-map 或手动调整

5. 更新 review-feedback.json: round += 1
```

### 安全护栏

- 不直接修改 product-map 产物
- 只输出修复建议，由用户决定
