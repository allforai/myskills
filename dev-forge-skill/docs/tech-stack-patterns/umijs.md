# UmiJS + Ant Design Pro 套路（admin / merchant 类）

## 公共基础层

**请求层**（所有类型共用）：

| 层次 | 规范 |
|------|------|
| HTTP 客户端 | `@umijs/max` 的 `request` 函数，全局配置在 `requestConfig.ts` |
| Token 管理 | requestConfig.ts 统一处理 Authorization header、token 刷新（mutex）、401 重定向 |
| Service 文件 | 每个域一个文件（`src/services/products.ts`），函数按操作命名 |
| 类型定义 | `src/services/typings.d.ts`，响应统一 `API.Response<T>` / `API.PageResponse<T>` |

**枚举管理**（所有类型共用）：

```
定义: constants/enums.ts — 枚举值（数字或字符串常量）
标签: constants/enumLabels.ts — 多语言标签 + 颜色/Tag 映射
使用: 列表列 valueEnum + 表单 Select options + 详情页 Tag 共用同一套枚举
```

**字段→组件映射**（所有含表单的类型共用，抽象映射见 `docs/interaction-types.md`）：

| 字段类型 | UmiJS + AntD Pro 组件 | 备注 |
|---------|------|------|
| 文本 | `Input` / `ProFormText` | |
| 多行文本 | `Input.TextArea` / `ProFormTextArea` | rows ≥ 3 |
| 枚举/状态 | `Select` / `ProFormSelect` | 选项来自 `constants/enums.ts`，禁止用 Input |
| 数字 | `InputNumber` / `ProFormDigit` | 设置 min/max/precision |
| 布尔 | `Switch` / `ProFormSwitch` | |
| 日期 | `DatePicker` / `ProFormDatePicker` | |
| 图片 | `Upload`（listType="picture-card"） | 限制数量和格式 |
| 关联实体 | `Select`（动态从 API 获取 options） | 如「分类选择」 |

---

## MG1 只读列表

> 类型特征见 `docs/interaction-types.md`。以下为 UmiJS + AntD Pro 实现规范。

```
组件: ProTable<API.Entity> + useRef<ActionType>()
数据源: request prop → service 函数 → { data, total, success }
筛选: 列定义 valueType: 'select' + valueEnum，或 dateRange 搜索
操作列: 仅「查看详情」Link 跳转，无编辑/删除按钮
分页: params.current → page，defaultPageSize: 10/20
搜索: search={{ labelWidth: 'auto' }}
特征: 无 ModalForm、无 Modal.confirm、无 mutation API 调用
```

Service 层仅需 `getXList()` 函数，无 create/update/delete。

---

## MG2 CRUD 实体集群

> 类型特征见 `docs/interaction-types.md`。以下为 UmiJS + AntD Pro 实现规范。

**列表页**：
```
组件: ProTable + ActionRef
操作列: 编辑 + 删除（+ 可选的状态切换）
工具栏: 新建按钮（toolBarRender）
```

**新建/编辑表单**：

| 场景 | 组件 | 数据流 |
|------|------|--------|
| 简单实体（≤8 字段） | `ModalForm` + `ProForm*` 字段 | `onFinish` 返回 boolean → 成功关闭 → `actionRef.current?.reload()` |
| 复杂实体（>8 字段 / 含嵌套） | 独立页面 `Form` | `useEffect` fetch → `form.setFieldsValue()` 回填 → 提交 → `history.push()` |

**编辑回填（强制）**：
- ModalForm：打开前 `form.setFieldsValue(record)` 或传 `initialValues`
- 独立页面：`useEffect` 中 fetch → `form.setFieldsValue(res.data)`
- 图片/文件：URL 转 `UploadFile[]`（`{ uid, name, status: 'done', url }`）

**删除操作**：
```
确认: Modal.confirm({ title, content: 实体名, okType: 'danger' }) 或 Popconfirm
执行: onOk → deleteX(id) → message.success → actionRef.current?.reload()
```

Service 层完整：`getXList()` / `getX(id)` / `createX()` / `updateX()` / `deleteX()`

---

## MG3 状态机驱动

> 类型特征见 `docs/interaction-types.md`。以下为 UmiJS + AntD Pro 实现规范。

**列表页**：
```
组件: ProTable + 状态筛选（valueEnum 按状态着色）
操作列: 根据当前状态动态显示可用操作按钮（条件渲染）
  如: 待发货 → 显示「发货」；已发货 → 显示「查看物流」
无: 编辑按钮、删除按钮
```

**状态操作**：
```
简单操作（无额外输入）:
  Modal.confirm({ title: '确认发货？', onOk: () => shipOrder(id) })
  → message.success → actionRef.current?.reload()

带输入的操作（如拒绝需填理由）:
  ModalForm({ title: '拒绝退款' })
    → ProFormTextArea name="reason" rules=[{ required: true }]
    → onFinish: rejectRefund(id, { reason }) → reload
```

**状态流转图**（design.md 必须包含 Mermaid stateDiagram）：
```
design.md 中为每个状态机实体生成:
  stateDiagram-v2
    [*] --> pending
    pending --> approved : approve()
    pending --> rejected : reject(reason)
    approved --> suspended : suspend(reason)
    suspended --> approved : restore()
```

Service 层：`getXList()` / `getX(id)` / `approveX(id)` / `rejectX(id, reason)` / `shipX(id, data)` 等操作函数，无 `updateX()` 通用编辑。

---

## MG4 审批流

> 类型特征见 `docs/interaction-types.md`。以下为 UmiJS + AntD Pro 实现规范。

**列表页**：
```
组件: ProTable，status 列默认筛选为「待审批」
操作列: 「审核」Link 跳转到详情页
可选: 批量审批（rowSelection + 工具栏批量操作按钮）
```

**审核详情页**：
```
布局:
  Card(实体完整信息 — Descriptions / 只读展示，不可编辑)
  Card(审核操作面板)
    → 审核检查项（可选 Checkbox 清单）
    → 批准按钮 (Filled, type="primary")
    → 驳回按钮 (Outlined, danger)
    → 驳回时弹出 ModalForm 填写驳回原因

数据流:
  批准: Modal.confirm → approveX(id) → message.success → history.push(列表)
  驳回: ModalForm → rejectX(id, { reason, comment }) → history.push(列表)
```

Service 层：`getXList()` / `getXDetail(id)` / `approveX(id)` / `rejectX(id, reason)`，可选 `batchApproveX(ids[])`。

---

## MG5 主从详情

> 类型特征见 `docs/interaction-types.md`。以下为 UmiJS + AntD Pro 实现规范。

```
路由: /entities/:id
取数: useParams() → useEffect fetchEntity() → setState

布局:
  PageContainer
    Card(头部 — Avatar/名称/关键指标 Statistic)
    Card(基本信息 — Descriptions column={2})
    Card(关联数据 — Tabs)
      TabPane("订单") → ProTable + 独立 ActionRef（request 内带 entityId 筛选）
      TabPane("积分") → ProTable + 独立 ActionRef
      TabPane("日志") → ProTable（只读）

内嵌操作:
  主实体操作: 按钮 → ModalForm → fetchEntity() 刷新主信息
  子实体操作: 子表操作列 → Modal.confirm → 子表 actionRef.current?.reload()
```

Service 层：`getX(id)` + `getXOrders(id, params)` + `getXPoints(id, params)` 等子实体查询。

---

## MG6 树形管理

> 类型特征见 `docs/interaction-types.md`。以下为 UmiJS + AntD Pro 实现规范。

```
取数: useEffect fetchTree() → setState（一次加载全树，或懒加载子节点）

布局:
  左侧: Tree 组件展示层级
  右侧/弹窗: 选中节点的编辑表单

新建: 选中父节点 → 打开 ModalForm（带 parentId）→ createX({ ...values, parentId })
编辑: 选中节点 → form.setFieldsValue(node.data) → updateX(id, values)
删除: Popconfirm → deleteX(id)
排序: 拖拽或 sort 字段编辑

刷新: 所有操作后 fetchTree()（重建整棵树）
```

Service 层：`getXTree()` / `createX({ parentId })` / `updateX(id)` / `deleteX(id)` / 可选 `reorderX(id, sort)`。

---

## MG7 仪表盘

> 类型特征见 `docs/interaction-types.md`。以下为 UmiJS + AntD Pro 实现规范。

```
取数: useEffect → 调用 getDashboard() / getStatistics() → setState
布局:
  Row + Col 网格:
    Statistic 卡片（关键指标：总订单数、待处理、销售额）
    图表（可选: @ant-design/charts — Line/Bar/Pie）
    待办事项列表（Link 跳转到对应管理页）

刷新: 无自动刷新（或可选定时轮询）
```

Service 层：`getDashboard()` / `getStatistics(params)` 聚合查询。

---

## MG8 配置页

> 类型特征见 `docs/interaction-types.md`。以下为 UmiJS + AntD Pro 实现规范。

```
取数: useEffect → getSettings() → form.setFieldsValue(res.data)

布局:
  PageContainer
    Card(表单)
      Form + Form.Item（字段按业务分组，可用 Divider 分隔）
      提交按钮（固定在底部或浮动）

提交: form.validateFields() → updateSettings(values) → message.success
特征: 无列表、无删除、无新建。只有「加载 → 编辑 → 保存」。
```

Service 层：`getSettings()` / `updateSettings(values)`，仅两个函数。
