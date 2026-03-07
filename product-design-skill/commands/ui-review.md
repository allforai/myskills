---
name: ui-review
description: >
  Use when the user says "ui-review", "review UI feedback", "process UI comments",
  "UI 审核", "处理审核反馈", "UI 迭代".
  Reads review-feedback.json from the UI review server, re-generates only
  screens that need revision based on pin comments.
arguments:
  - name: mode
    description: "start (launch review server) | process (read feedback and iterate)"
    required: false
    default: "start"
---

# UI Review — 审核反馈处理

## 模式

| 模式 | 触发 | 行为 |
|------|------|------|
| `start` | `/ui-review` 或 `/ui-review start` | 启动审核服务器 |
| `process` | `/ui-review process` | 读取反馈，局部迭代 |

---

## Mode: start

启动本地审核服务器，供用户浏览界面、标注意见。

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/ui_review_server.py <BASE> [--port 3200]
```

- `<BASE>` = `.allforai` 目录路径
- 服务器自动打开浏览器
- 局域网访问：加 `--host 0.0.0.0`
- 用户在浏览器中审核所有界面，点击预览任意位置添加 pin 评论
- 审核完毕点击 "Submit Feedback" → 生成 `review-feedback.json` → 服务器自动关闭

---

## Mode: process

读取 `review-feedback.json`，仅对标记为 `revision` 的界面重新生成设计。

### 流程

```
1. 读取 .allforai/ui-design/review-feedback.json
   - 不存在 → 提示用户先运行 /ui-review start
   - submitted_at = null → 提示用户先在审核服务器提交反馈

2. 统计反馈
   - 输出：N 个界面已审核，M 个通过，K 个需修改
   - K = 0 → 提示全部通过，无需迭代，终止

3. 对每个 status="revision" 的界面：
   a. 收集该界面的所有 pin comments
   b. 读取现有 ui-design-spec.json 中该界面的当前设计
   c. 读取 experience-map.json 中该界面的结构信息
   d. 将 comments 作为修改指令，重新生成该界面的：
      - ui-design-spec.json 中的对应 screen 条目
      - ui-design-spec.md 中的对应段落
   e. 如果 Stitch MCP 可用且该界面有 stitch 产出：
      - 调用 edit_screens() 修改 Stitch 视觉稿
      - 重新获取 HTML + 截图

4. 更新 review-feedback.json：
   - round += 1
   - 修改过的界面 status 重置为 "pending"
   - 保留已通过界面的 status = "approved"

5. 提示用户：
   「已重新生成 K 个界面。运行 /ui-review start 查看修改结果。」
```

### Pin Comments 的解读

每个 pin 包含 `{x, y, comment}`，其中 x/y 是界面预览中的相对坐标（百分比）。

坐标位置帮助定位反馈针对的区域：
- y < 15% → 顶部导航/头部区域
- 15% < y < 75% → 主内容区域
- y > 75% → 底部操作区/分页器

将坐标与 ui-design-spec.json 的 `sections` 列表对应，确定修改哪个 section。

### 安全护栏

- 只修改 status="revision" 的界面，绝不触碰 approved 的
- 修改前备份当前 ui-design-spec.json 为 ui-design-spec.json.bak
- 每轮迭代记入 pipeline-decisions.json
