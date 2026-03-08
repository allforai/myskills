---
name: concept-review
description: >
  Use when the user says "concept-review", "review concept", "概念审核",
  "审核产品概念", "concept mind map".
  Interactive mind map review of product concept — validate product direction,
  target users, value proposition, and innovation concepts before building product map.
arguments:
  - name: mode
    description: "start (launch review server) | process (read feedback and route)"
    required: false
    default: "start"
---

# Concept Review — 产品概念脑图审核

## 模式

| 模式 | 触发 | 行为 |
|------|------|------|
| `start` | `/concept-review` 或 `/concept-review start` | 启动脑图审核服务器 |
| `process` | `/concept-review process` | 读取反馈，汇总修改建议 |

---

## Mode: start

启动产品概念脑图审核服务器，展示产品概念的树形结构供用户验证。

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/mindmap_review_server.py <BASE> --source concept --port 18900
```

- 服务器启动后会自动打开浏览器，**禁止**再用 Playwright `browser_navigate` 或其他方式重复打开同一 URL
- 脑图包含：产品定位、目标用户（角色+痛点+增益）、商业模式、产品机制、创新概念、流水线偏好
- 点击任意节点展开/折叠子树
- 点击节点添加评论，选择评论类别（General / Feature / Concept / Flow）
- 每个节点可标记 Approved 或 Needs Revision
- 审核完毕点击 "Submit Feedback" → 生成反馈文件 → 服务器自动关闭
- **服务器退出后**：Bash 输出包含反馈摘要（approved/revision 数量及评论内容），**自动进入 process 模式**处理反馈，无需用户手动运行 `/concept-review process`

---

## Mode: process

读取 `.allforai/concept-review/review-feedback.json`，汇总反馈。

### 流程

```
1. 读取 .allforai/concept-review/review-feedback.json
   - 不存在 → 提示先运行 /concept-review start
   - submitted_at = null → 提示先提交反馈

2. 统计：N 个节点已审核，M 个通过，K 个需修改

3. K = 0 → 概念确认，进入 product-map

4. K > 0 → 汇总修改建议：
   - 按节点分组展示所有 revision comments
   - 提示用户修改 product-concept.json 或重跑 /product-concept

5. 更新 review-feedback.json: round += 1
```

### 安全护栏

- 不直接修改 product-concept.json
- 只输出修复建议，由用户决定
