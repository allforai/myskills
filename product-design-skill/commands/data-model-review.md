---
name: data-model-review
description: >
  Use when the user says "data-model-review", "review data model", "数据模型审核",
  "审核数据模型", "审核实体", "审核接口", "review entities", "review APIs",
  "review view objects", "data model mind map".
  Interactive mind map review of data model — validate entities, fields,
  API contracts, and view objects before proceeding to experience-map.
arguments:
  - name: mode
    description: "start (launch review server) | process (read feedback and route)"
    required: false
    default: "start"
---

# Data Model Review — 数据模型脑图审核

## 模式

| 模式 | 触发 | 行为 |
|------|------|------|
| `start` | `/data-model-review` 或 `/data-model-review start` | 启动脑图审核服务器 |
| `process` | `/data-model-review process` | 读取反馈，汇总修改建议 |

---

## Mode: start

启动数据模型脑图审核服务器，展示实体-字段-接口-视图对象的树形结构。

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/datamodel_review_server.py <BASE> --port 18904
```

- 服务器启动后会自动打开浏览器，**禁止**再用 Playwright `browser_navigate` 或其他方式重复打开同一 URL
- 脑图包含：
  - 实体列表（字段、类型、约束）
  - 状态机（状态流转规则）
  - API 接口（method + path + 请求/响应）
  - 视图对象（VO 字段 + Action Binding）
  - 实体关系（1:N / N:N）
- 点击任意节点展开/折叠子树
- 点击节点添加评论，选择评论类别：
  - `entity`: 实体定义问题
  - `api`: 接口设计问题
  - `vo`: 视图对象问题
  - `action`: Action Binding 问题
  - `state-machine`: 状态机问题
  - `product-map`: 根源性问题（需回到产品地图）
- 审核完毕点击 "Submit Feedback" → 生成反馈文件 → 服务器自动关闭
- **服务器退出后**：Bash 输出包含反馈摘要（approved/revision 数量及评论内容），**自动进入 process 模式**处理反馈，无需用户手动运行 `/data-model-review process`

---

## Mode: process

读取 `.allforai/data-model-review/review-feedback.json`，汇总反馈。

### 流程

```
1. 读取 .allforai/data-model-review/review-feedback.json
   - 不存在 → 提示先运行 /data-model-review start
   - submitted_at = null → 提示先提交反馈

2. 统计：N 个节点已审核，M 个通过，K 个需修改

3. K = 0 → 数据模型确认，进入 journey-emotion → experience-map

4. K > 0 → 按类别汇总修改建议：
   - entity/api/state-machine 类 → 修改 entity-model.json，重跑 Step 7 (gen_data_model.py)
   - vo/action 类 → 修改 view-objects.json，重跑 Step 8 (gen_view_objects.py)
   - product-map 类 → 回到 /product-map 修改，重跑全链
   - 提示用户修改后重跑对应步骤

5. 更新 review-feedback.json: round += 1
```

### 安全护栏

- 不直接修改 data-model 产物
- 只输出修复建议，由用户决定
