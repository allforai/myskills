# 页面交互类型体系

> 本文档是页面交互类型的**单一事实来源**（Single Source of Truth）。
> 各阶段技能引用本文档，不重复定义类型。

## 引用关系

```
docs/interaction-types.md（本文档 — 定义层）
  ↑ 引用
  ├── screen-map.md     → Step 1 推断 interaction_type，写入 screen-map.json
  ├── ui-design.md      → Step 4 按 interaction_type 生成视觉规格
  └── design-to-spec.md → Step 2 按 interaction_type 生成实现规格（技术栈映射）
```

---

## 八种交互类型（A–H）

| 类型 | 代号 | 描述 | 典型占比 |
|------|------|------|---------|
| **A. 只读列表** | `readonly-list` | 仅查看+筛选，无增删改操作 | ~55% |
| **B. 完整 CRUD** | `full-crud` | 新建+编辑+删除+列表，实体生命周期完整 | ~10% |
| **C. 状态机驱动** | `state-machine` | 无直接字段编辑，通过操作触发状态流转 | ~10% |
| **D. 审批流** | `approval` | 查看详情+批准/驳回（可选附加评语） | ~6% |
| **E. 主从详情** | `master-detail` | 主实体详情+嵌套子实体列表（Tabs） | ~6% |
| **F. 树形管理** | `tree-crud` | 父子嵌套结构，支持层级 CRUD | ~2% |
| **G. 仪表盘** | `dashboard` | 统计卡片+图表，无数据变更 | ~3% |
| **H. 配置页** | `config-form` | 单页表单编辑，无列表 | ~8% |

### 组合类型

一个页面可同时具有多个类型（用 `+` 连接）：
- 订单详情 = `master-detail` + `state-machine`
- 用户详情 = `master-detail` + `config-form`（编辑基本信息）

---

## 推断规则

> screen-map Step 1 梳理界面时，根据 actions 自动推断 interaction_type。

```
优先级从高到低（命中即停）：

1. screen 名含 dashboard/overview/报表/ダッシュボード
   → G. dashboard

2. 有 approve/reject/audit/review actions
   → D. approval

3. 有 ship/cancel/suspend/restore/freeze/activate/deactivate actions
   且无 create/edit（非字段编辑，而是状态操作）
   → C. state-machine

4. 有子实体列表（tabs/nested table/TabPane）
   → E. master-detail

5. entities 有 parentId/children/parent_id/treeData 字段
   → F. tree-crud

6. screen 名含 settings/config/profile/設定/資料/设置
   且无 list/列表 相关 action
   → H. config-form

7. 有 create + edit + delete actions
   → B. full-crud

8. actions 仅有 view/filter/search/export/download
   → A. readonly-list

9. 以上均不命中
   → A. readonly-list（默认）
```

### 推断输入

| 数据源 | 用途 |
|--------|------|
| screen.actions[].crud | C/R/U/D 分类 |
| screen.actions[].label | 操作名称（匹配状态操作关键词） |
| screen.name | 界面名称（匹配 dashboard/settings 等关键词） |
| screen.tasks → task.outputs.states | 是否有状态机定义 |
| screen 内是否有嵌套子表/Tabs | 判定 master-detail |
| 关联 entity 是否有 parentId | 判定 tree-crud |

---

## 各类型特征表

### A. 只读列表

| 维度 | 特征 |
|------|------|
| 数据操作 | 仅读取（GET list + GET detail），无写操作 |
| 典型页面 | 审计日志、积分历史、结算记录、通知列表 |
| 工具栏 | 筛选条件 + 可选导出按钮，无「新建」 |
| 操作列 | 仅「查看详情」链接跳转 |
| 状态处理 | empty（空数据提示）、loading、error |
| Service 函数 | `getXList(params)` — 仅一个 |

### B. 完整 CRUD

| 维度 | 特征 |
|------|------|
| 数据操作 | 完整生命周期：Create + Read + Update + Delete |
| 典型页面 | 商品管理、分类管理、角色管理、团队成员 |
| 工具栏 | 「新建」按钮（toolBarRender） |
| 操作列 | 编辑 + 删除（+ 可选状态切换） |
| 表单模式 | 简单实体（≤8 字段）→ 弹窗表单；复杂实体 → 独立页面 |
| 编辑回填 | **强制**：打开编辑时必须回填旧值到表单 |
| 删除确认 | **强制**：删除前弹确认框 |
| Service 函数 | `getXList` / `getX(id)` / `createX` / `updateX` / `deleteX` |

### C. 状态机驱动

| 维度 | 特征 |
|------|------|
| 数据操作 | 状态流转操作，无通用编辑 |
| 典型页面 | 订单管理、退款管理、商户状态 |
| 操作列 | 根据当前状态动态显示可用操作（条件渲染） |
| 操作形式 | 简单操作 → 确认弹窗；带输入 → 弹窗表单（如拒绝填理由） |
| 必须产物 | 状态流转图（stateDiagram） |
| 无 | 编辑按钮、删除按钮、通用 updateX |
| Service 函数 | `getXList` / `getX(id)` / `approveX` / `rejectX` / `shipX` 等操作函数 |

### D. 审批流

| 维度 | 特征 |
|------|------|
| 数据操作 | 查看+批准/驳回决策 |
| 典型页面 | 商品审核、退款审批、广告审核、商户入驻 |
| 列表筛选 | 默认筛选「待审批」状态 |
| 操作列 | 「审核」链接跳转到详情页（不在列表行内操作） |
| 详情页 | 只读展示实体信息 + 审核操作面板（批准/驳回） |
| 驳回 | 弹窗表单填写驳回原因 |
| 可选 | 批量审批（rowSelection + 批量操作） |
| Service 函数 | `getXList` / `getXDetail(id)` / `approveX(id)` / `rejectX(id, reason)` |

### E. 主从详情

| 维度 | 特征 |
|------|------|
| 数据操作 | 主实体查看 + 多个子实体列表浏览/操作 |
| 典型页面 | 用户详情（→订单/积分）、商户详情（→订单/结算）、订单详情（→商品项） |
| 路由 | `/entities/:id` |
| 布局 | 头部（主实体关键信息）+ Tabs（子实体列表） |
| Tab 列表 | 每个 Tab 独立数据源、独立分页 |
| 内嵌操作 | 主实体操作 → 弹窗表单；子实体操作 → 子表 reload |
| Service 函数 | `getX(id)` + `getXOrders(id, params)` + `getXPoints(id, params)` |

### F. 树形管理

| 维度 | 特征 |
|------|------|
| 数据操作 | 父子层级 CRUD |
| 典型页面 | 分类管理、组织架构 |
| 布局 | 左侧树 + 右侧编辑（或弹窗） |
| 新建 | 选中父节点 → 带 parentId 的表单 |
| 刷新 | 所有操作后重新加载整棵树 |
| 可选 | 拖拽排序 |
| Service 函数 | `getXTree()` / `createX({ parentId })` / `updateX(id)` / `deleteX(id)` |

### G. 仪表盘

| 维度 | 特征 |
|------|------|
| 数据操作 | 纯读取聚合数据 |
| 典型页面 | 首页 Dashboard、数据报表 |
| 布局 | 网格：统计卡片 + 图表 + 待办列表 |
| 无 | 表单、删除、新建等写操作 |
| 可选 | 时间范围筛选、定时刷新 |
| Service 函数 | `getDashboard()` / `getStatistics(params)` |

### H. 配置页

| 维度 | 特征 |
|------|------|
| 数据操作 | 加载 → 编辑 → 保存（单实体） |
| 典型页面 | 系统设置、店铺资料、安全设置 |
| 布局 | 单页表单（无列表） |
| 无 | 列表、删除、新建 |
| 回填 | **强制**：加载时必须回填已有值到表单 |
| Service 函数 | `getSettings()` / `updateSettings(values)` — 仅两个 |

---

## 字段→组件映射

> 适用于所有含表单的交互类型（B / C.带输入操作 / D.驳回表单 / F / H）。

| 字段类型 | 抽象组件 | 说明 |
|---------|---------|------|
| 文本 | TextInput | 单行输入 |
| 多行文本 | TextArea | rows ≥ 3 |
| 枚举/状态 | Select / Dropdown | 选项来自枚举定义，**禁止用 TextInput** |
| 数字 | NumberInput | 设置 min/max/precision |
| 布尔 | Switch / Toggle | |
| 日期 | DatePicker | |
| 图片 | ImageUpload | 限制数量和格式 |
| 关联实体 | AsyncSelect | 从 API 动态获取选项 |

---

## 枚举管理规范

| 规范 | 要求 |
|------|------|
| 定义位置 | 集中在 `constants/enums` 或等效位置 |
| 标签 | 多语言标签与枚举值分离 |
| 使用一致 | 列表列筛选、表单下拉、详情标签共用同一套枚举 |
| 颜色 | 状态枚举带颜色/Tag 映射（如 pending→黄, approved→绿） |

---

## 多语言规范

| 规范 | 要求 |
|------|------|
| 文本获取 | 所有用户可见文本通过 i18n 函数获取，禁止硬编码 |
| 同步 | 新增文本必须同步所有语言文件 |
| Key 命名 | 按 `{模块}.{页面}.{元素}` 分层 |
| 参数化 | 动态内容用参数插值，不拼接字符串 |
| 枚举标签 | 枚举显示文本也走 i18n |

---

## 各阶段使用指南

### screen-map 阶段

**输入**：task-inventory.json → actions
**动作**：为每个 screen 推断 `interaction_type`，写入 screen-map.json
**输出**：screen-map.json 中每个 screen 增加 `interaction_type` 字段

```json
{
  "id": "S001",
  "name": "订单管理",
  "interaction_type": "state-machine",
  ...
}
```

组合类型用数组：
```json
{
  "interaction_type": ["master-detail", "state-machine"]
}
```

### ui-design 阶段

**输入**：screen-map.json（含 interaction_type）
**动作**：按 interaction_type 生成视觉布局规格
**输出**：ui-design-spec.md 中每个界面标注交互类型 + 对应的布局模式

| 交互类型 | 推荐布局模式 |
|---------|------------|
| readonly-list | 侧边导航 + 表格区（筛选栏 + 数据表 + 分页） |
| full-crud | 侧边导航 + 表格区 + 工具栏（新建按钮） |
| state-machine | 侧边导航 + 表格区（状态筛选 Tab + 条件操作列） |
| approval | 列表页（待审筛选）+ 详情页（信息卡 + 审核面板） |
| master-detail | 头部信息区 + Tab 切换子表 |
| tree-crud | 左右分栏（左树右编辑） |
| dashboard | 网格布局（统计卡 + 图表区 + 快捷入口） |
| config-form | 居中单列表单 |

### design-to-spec 阶段

**输入**：screen-map.json（含 interaction_type）+ project-manifest.json（技术栈）
**动作**：按 interaction_type × 技术栈 生成实现级数据流规格
**输出**：design.md 中每个页面标注类型 + 组件选型 + Service 函数签名

design-to-spec 需在自身文档中维护技术栈映射表（因技术栈由 project-forge 决定，不属于产品设计层）。
