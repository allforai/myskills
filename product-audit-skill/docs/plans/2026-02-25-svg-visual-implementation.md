# SVG 可视化 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在 product-map 技能的 Step 3 和 Step 6 各新增一段 SVG 生成指令，让 Claude 在执行技能时自动输出 `business-flows-visual.svg` 和 `product-map-visual.svg`。

**Architecture:** 只修改 `skills/product-map.md` 一个文件，在两个指定位置插入 SVG 生成指令段落，并更新输出文件结构清单和版本号。不新增任何代码文件，SVG 由 Claude 在技能执行时动态生成并写入磁盘。

**Tech Stack:** Markdown skill 文件编辑；SVG 1.1 内联生成（Claude 在运行时输出）

---

## Task 1：在 Step 3 末尾插入 business-flows-visual.svg 生成指令

**Files:**
- Modify: `product-audit-skill/skills/product-map.md`（Step 3 末尾，"输出：`.allforai/product-map/business-flows.json`…" 那一行之后）

**Step 1：Read 当前文件，确认插入锚点**

用 Read 工具读取 `product-audit-skill/skills/product-map.md` 第 400–410 行，确认锚点文字为：

```
输出：`.allforai/product-map/business-flows.json`、`.allforai/product-map/business-flows-report.md`
```

**Step 2：用 Edit 工具插入 SVG 生成指令**

将下方 `old_string` 替换为 `new_string`：

old_string（精确匹配）：
```
输出：`.allforai/product-map/business-flows.json`、`.allforai/product-map/business-flows-report.md`

---

### Step 4：冲突 & 冗余检测
```

new_string（插入 SVG 指令段落）：
```
输出：`.allforai/product-map/business-flows.json`、`.allforai/product-map/business-flows-report.md`

#### SVG 生成：business-flows-visual.svg

`business-flows.json` 写入磁盘后，立即生成 `.allforai/product-map/business-flows-visual.svg`。

**数据来源**：刚写入的 `business-flows.json`

**布局规则**：
- 画布宽：780px，高：动态累计
- 顶部 padding：24px
- 每条流区块：流标题栏 32px + 参与泳道数 × 60px + 底部间距 16px
- 泳道标签列宽：100px，节点区起始 x：120px
- 节点：宽 150px，高 40px，水平间距 40px（节点间净距）
- 节点 x = 120 + (seq-1) × 190
- 泳道顺序：按该流中节点 seq 首次出现的 role/system 排列

**颜色规范**：

| 元素 | 颜色 |
|------|------|
| 流标题栏背景 | `#1E293B`，白色文字 14px bold |
| 泳道标签背景 | `#F1F5F9`，`#475569` 文字 12px |
| 泳道分割线 | `#E2E8F0`，stroke-dasharray="4 2" |
| 正常节点 border | `#3B82F6`，fill `#EFF6FF`，文字 `#1E3A8A` 12px |
| 缺口节点 border | `#EF4444` 虚线 stroke-dasharray="4 2"，fill `#FEF2F2`，文字 `#991B1B` |
| 缺口节点右上角 | ⚠ 文字标记，`#EF4444`，14px |
| handoff 箭头 | `#64748B`，marker-end arrow |
| handoff 标签 | `#64748B`，10px，箭头上方 |
| seq 圆 | fill `#3B82F6`，白色文字 10px，半径 10px，节点左上角偏移(-6,-6) |

**SVG 结构**：

```
<svg xmlns="..." width="780" height="{total_height}" viewBox="0 0 780 {total_height}">
  <defs>
    <marker id="arrow" ...>  <!-- 箭头标记 -->
  </defs>
  <!-- 遍历 flows 数组 -->
  <!-- 每条流：标题栏矩形+文字 → 泳道背景+标签+分割线 → 节点矩形+seq圆+文字 → handoff箭头+标签 -->
</svg>
```

**生成逻辑**（逐步）：
1. 遍历 `flows` 数组，对每条流收集参与的 role（去重，按 seq 首次出现排序）
2. 计算该流区块高度 = 32 + 参与 role 数 × 60 + 16
3. 绘制流标题栏（x=0，宽 780，高 32）+ 流名称文字
4. 绘制每条泳道（标签矩形 + 文字 + 底部分割线）
5. 按 seq 顺序绘制每个节点：
   - 确定节点所在泳道 index → y = 流起点 + 32 + 泳道index × 60 + 10
   - x = 120 + (seq-1) × 190
   - 绘制矩形（gap=true 用虚线红框，否则实线蓝框）
   - 绘制节点名称文字（超过 14 字截断加 …）
   - 绘制 seq 圆（左上角偏移 -6,-6）
   - gap=true 时右上角绘制 ⚠ 文字
6. 连接相邻 seq 节点的 handoff 箭头；若 handoff.mechanism 非空，在箭头路径中点上方绘制标签
7. 累加 currentY，进入下一条流

写入 `.allforai/product-map/business-flows-visual.svg`

---

### Step 4：冲突 & 冗余检测
```

**Step 3：Read 修改后的文件验证插入结果**

读取修改后第 400–440 行，确认：
- 包含 `#### SVG 生成：business-flows-visual.svg` 标题
- 包含颜色规范表格
- Step 4 标题仍在 SVG 段落之后
- 没有多余空行或格式破损

**Step 4：提交**

```bash
git add product-audit-skill/skills/product-map.md
git commit -m "feat(product-map): Step 3 新增 business-flows-visual.svg 生成指令"
```

---

## Task 2：在 Step 6 末尾插入 product-map-visual.svg 生成指令

**Files:**
- Modify: `product-audit-skill/skills/product-map.md`（Step 6 末尾，"输出：`.allforai/product-map/product-map.json`…" 那一行之后）

**Step 1：Read 当前文件，确认插入锚点**

读取第 550–565 行，确认锚点文字为：

```
输出：`.allforai/product-map/product-map.json`、`.allforai/product-map/product-map-report.md`
```

**Step 2：用 Edit 工具插入 SVG 生成指令**

old_string（精确匹配）：
```
输出：`.allforai/product-map/product-map.json`、`.allforai/product-map/product-map-report.md`

---

### Step 7：校验
```

new_string（插入 SVG 指令段落）：
```
输出：`.allforai/product-map/product-map.json`、`.allforai/product-map/product-map-report.md`

#### SVG 生成：product-map-visual.svg

`product-map-report.md` 写入磁盘后，立即生成 `.allforai/product-map/product-map-visual.svg`。

**数据来源**：
- `.allforai/product-map/role-profiles.json`（roles 数组，取 status != "user_removed" 的角色）
- `.allforai/product-map/task-inventory.json`（tasks 数组，按 owner_role 分组，取 status != "user_removed" 的任务）

**布局规则**：
- 画布宽：540px，高：动态
- 顶部 padding：48px（图例区）
- 角色框：x=20，宽 150px，高 40px，圆角 6px
- 任务框：x=220，宽 240px，高 36px，圆角 4px
- 同角色内任务垂直间距：10px
- 角色框在 y 轴上与其任务组**居中对齐**
- 角色组之间额外间距：20px
- 连线折点：x=195（角色框右中心 x=170 → 折点 x=195 → 任务框左中心 x=220）

**颜色规范**：

| 元素 | 颜色 |
|------|------|
| 角色框 | fill `#3B82F6`，白色文字 13px bold，圆角 6px |
| 任务框·frequency="高" | fill `#22C55E`，白色文字 12px |
| 任务框·frequency="中" | fill `#F59E0B`，白色文字 12px |
| 任务框·frequency="低" | fill `#9CA3AF`，白色文字 12px |
| 连线 | stroke `#CBD5E1`，stroke-width 1，fill none |
| 风险徽章（risk_level="高"） | fill `#EF4444`，半径 6px，位于任务框右侧外 (task_x+244, task_y-4) |
| 跨部门徽章（cross_dept=true） | fill `#8B5CF6`，半径 6px，紧贴风险徽章左侧 8px |
| 冲突 Flag（flags 不为空） | 橙色三角 `#F97316`，顶点 (task_x+240, task_y-8)，底边 12px |

**图例（y=8 起，画布顶部）**：

横向排列，色块 14×14px + 说明文字 12px：

```
■绿 高频   ■黄 中频   ■灰 低频   ●红 高风险   ●紫 跨部门   ▲橙 冲突
```

**SVG 结构**：

```
<svg xmlns="..." width="540" height="{total_height}" viewBox="0 0 540 {total_height}">
  <!-- 图例行 y=8 -->
  <!-- 遍历每个角色 -->
  <!-- 先绘连线，再绘任务框+徽章，最后绘角色框（确保角色框在最上层） -->
</svg>
```

**生成逻辑**（逐步）：
1. 绘制图例行（固定 y=8）
2. currentY = 48（图例区底部）
3. 遍历 role-profiles.json 中每个角色（status ≠ "user_removed"）：
   a. 取该角色 owner_role 对应的所有任务（status ≠ "user_removed"），若无任务则跳过
   b. 计算该角色组高度 = 任务数 × (36+10) - 10
   c. 角色框 cy = currentY + 角色组高度 / 2
   d. 对每个任务 i（0-indexed）：
      - task_y = currentY + i × 46
      - task_cy = task_y + 18
      - 绘制连线（折线：170,角色cy → 195,角色cy → 195,task_cy → 220,task_cy）
      - 绘制任务框（x=220，y=task_y，按 frequency 填色）
      - 绘制任务名文字（x=228，y=task_y+22，超过 18 字截断加 …）
      - 按优先级绘制徽章（flags不空 → 三角；risk_level="高" → 红圆；cross_dept=true → 紫圆）
   e. 绘制角色框（x=20，y=currentY+角色组高度/2-20，填蓝色）
   f. 绘制角色名文字（截断超过 10 字的名字）
   g. currentY += 角色组高度 + 20
4. 画布总高度 = currentY + 20

写入 `.allforai/product-map/product-map-visual.svg`

---

### Step 7：校验
```

**Step 3：Read 修改后的文件验证**

读取修改后对应行段，确认：
- 包含 `#### SVG 生成：product-map-visual.svg` 标题
- 包含图例和颜色规范表格
- Step 7 标题仍紧跟其后
- 无格式破损

**Step 4：提交**

```bash
git add product-audit-skill/skills/product-map.md
git commit -m "feat(product-map): Step 6 新增 product-map-visual.svg 生成指令"
```

---

## Task 3：更新输出文件结构 + 版本号

**Files:**
- Modify: `product-audit-skill/skills/product-map.md`（输出文件结构清单 + frontmatter version）

**Step 1：更新输出文件结构清单**

old_string（精确匹配）：
```
├── business-flows.json         # Step 3: 业务流（跨角色/跨系统链路）
├── business-flows-report.md    # Step 3: 业务流摘要（人类可读）
```

new_string：
```
├── business-flows.json         # Step 3: 业务流（跨角色/跨系统链路）
├── business-flows-report.md    # Step 3: 业务流摘要（人类可读）
├── business-flows-visual.svg   # Step 3: 业务流泳道图（可视化）
```

---

old_string（精确匹配）：
```
├── product-map.json            # Step 6: 汇总文件（供其他技能加载）
├── product-map-report.md       # Step 6: 可读报告
```

new_string：
```
├── product-map.json            # Step 6: 汇总文件（供其他技能加载）
├── product-map-report.md       # Step 6: 可读报告
├── product-map-visual.svg      # Step 6: 角色-任务树（可视化）
```

**Step 2：更新 frontmatter version**

old_string：
```
version: "2.1.0"
```

new_string：
```
version: "2.2.0"
```

**Step 3：Read 验证**

读取第 1–15 行确认 version 为 `"2.2.0"`，读取输出文件结构清单确认两个 `.svg` 行已插入。

**Step 4：提交**

```bash
git add product-audit-skill/skills/product-map.md
git commit -m "chore(product-map): v2.2.0 — 输出结构新增两个 SVG 文件"
```

---

## Task 4：更新 README/SKILL.md 中的版本号和输出说明

**Files:**
- Modify: `product-audit-skill/README.md`（product-map 版本号和输出文件列表）
- Modify: `product-audit-skill/SKILL.md`（同上）

**Step 1：Read README.md 和 SKILL.md**

搜索两个文件中涉及 product-map 版本号（`2.1.0`）和输出文件列表的段落。

**Step 2：更新 README.md**

- 将 product-map 相关的 `2.1.0` → `2.2.0`
- 在 product-map 输出文件列表中补充两行 svg 说明（如有该列表）

**Step 3：更新 SKILL.md**

同 README.md 操作。

**Step 4：Read 验证两个文件**

确认版本号已更新，svg 文件已列出。

**Step 5：提交**

```bash
git add product-audit-skill/README.md product-audit-skill/SKILL.md
git commit -m "docs: product-map v2.2.0 — README/SKILL.md 同步 SVG 输出说明"
```
