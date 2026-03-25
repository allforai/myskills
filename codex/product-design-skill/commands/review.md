---
name: review
description: >
  Use when the user says "review", "审核", "review hub", "审核站点", "启动审核".
  Unified review hub — one site, 6 tabs covering product concept to dev spec.
  Replaces individual concept-review, map-review, wireframe-review, ui-review, data-model-review commands.
arguments:
  - name: mode
    description: "start (launch hub) | process (read all feedback) | process <tab> (process specific tab: concept/map/data-model/wireframe/ui/spec)"
    required: false
    default: "start"
---

# Review Hub — 统一审核站点

## 模式

| 模式 | 触发 | 行为 |
|------|------|------|
| `start` | `/review` 或 `/review start` | 启动审核站点 |
| `process` | `/review process` | 处理所有 tab 的反馈 |
| `process <tab>` | `/review process concept` | 处理指定 tab 的反馈 |

---

## Mode: start

启动统一审核站点，一个端口覆盖 6 个 tab。

```
python3 ../../shared/scripts/product-design/review_hub_server.py <BASE> --port 18900
```

- `<BASE>` = `.allforai` 目录路径
- 服务器启动后打印 URL: `http://localhost:18900/`
- **自动弹浏览器**（加 `--no-open true` 可禁用）
- 6 个 tab: 概念 / 地图 / 数据模型 / 线框 / UI / 规格
- 没有产物的 tab 灰显不可点击
- 每个 tab 独立保存反馈，提交后站点**不关闭**（可继续审核其他 tab）
- 局域网访问：加 `--host 0.0.0.0`

### Tab 说明

| Tab | 内容 | 展现形式 | 数据源 |
|-----|------|---------|--------|
| 概念 | 产品概念脑图 | XMind 径向脑图 | product-concept.json |
| 地图 | 角色/任务/业务流/共性模式 | XMind 径向脑图 | role-profiles + task-inventory + business-flows + patterns |
| 数据模型 | 实体/API/VO | XMind 径向脑图 | entity-model + api-contracts + view-objects |
| 线框 | 低保真线框 + 4D/6V | 左树 + 右预览面板 | experience-map.json |
| UI | 高保真视觉稿 | 左树 + 右预览面板 | ui-design-spec + preview/*.html |
| 规格 | 开发规格 | XMind 径向脑图 | project-forge/sub-projects/*/design.json |

### 审核操作

**脑图类 tab（概念/地图/数据模型/规格）：**
- 点击节点展开/折叠子树
- 点击节点打开评论面板（右侧）
- 选择评论类别 → 输入评论 → 标记 Approved 或 Needs Revision
- 点击 "Submit" 保存当前 tab 的反馈

**预览类 tab（线框/UI）：**
- 左侧屏幕树选择屏幕
- 右侧显示线框/UI 预览
- 点击预览区域添加 pin 评论
- 选择评论类别 → 输入评论
- 标记每个屏幕 Approved 或 Needs Revision
- 点击 "Submit" 保存当前 tab 的反馈

---

## Mode: process

读取所有 tab（或指定 tab）的反馈文件，汇总修改建议。

### 支持的 tab 名

| tab | 反馈文件 | 路由目标 |
|-----|---------|---------|
| concept | `.allforai/concept-review/review-feedback.json` | product-concept |
| map | `.allforai/product-map-review/review-feedback.json` | product-map |
| data-model | `.allforai/data-model-review/review-feedback.json` | product-map Step 7/8 |
| wireframe | `.allforai/wireframe-review/review-feedback.json` | experience-map / product-map |
| ui | `.allforai/ui-review/review-feedback.json` | ui-design |
| spec | `.allforai/project-forge/spec-review-feedback.json` | design-to-spec |

### 流程

```
1. 读取指定（或全部）反馈文件
   - 不存在 → 提示先执行 review 工作流 start 并在站点上审核
   - submitted_at = null → 提示先在站点上提交反馈

2. 统计：N 个节点/界面已审核，M 通过，K 需修改

3. K = 0（全部 approved）→ 删除 `constraints/<tab>.json`（如果存在）
   - 输出 "<tab> 审核全部通过，约束已清除"

4. K > 0 → 按类别汇总修改建议：
   - 脑图 tab: 按节点分组展示 revision comments
   - 预览 tab: 按界面分组展示 pin comments，按 category 路由
     - category="product-map" → 汇总为产品地图修改建议
     - category="experience-map" → 汇总为体验地图修改建议
     - category="concept" → 汇总为概念级问题

5. **生成约束文件** → `.allforai/constraints/<tab>.json`
   - 每条 needs_revision / rejected 评论转为一个约束条目
   - 约束 ID = `{tab}_{pin_id}` 或 `{tab}_{node_id}`（幂等，重复 process 不重复）
   - target 推断规则：
     - 脑图 tab: concept→product-concept, map→product-map, data-model→product-map, spec→dev-forge
     - 预览 tab: pin 的 category 字段（"product-map" / "experience-map" / "ui"→"ui-design"）
   - severity: 默认 "must"
   - 约束文件格式：
     ```json
     {
       "source_tab": "<tab>",
       "created_at": "<ISO>",
       "constraints": [...]
     }
     ```
   - 输出提示："已写入 N 条约束到 constraints/<tab>.json，下次重跑相关脚本时自动生效"

6. 输出修复行动清单

7. 更新 review-feedback.json: round += 1
```

### 安全护栏

- 不直接修改上游产物
- 只输出修复建议，由用户决定是否执行上游重跑
- 每轮审核记入 pipeline-decisions.json

### 约束文件说明

约束文件存储在 `.allforai/constraints/` 目录下，按 tab 分文件。所有 `gen_*.py` 脚本在运行时通过 `load_full_context()` 自动读取约束，作为硬约束注入生成结果。

- 约束在对应 tab 全部通过审核后自动清除
- 约束文件提交到 git，便于追踪审核历史
- 同一条评论重复 process 不会产生重复约束（幂等 ID）
