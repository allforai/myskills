# Step 3: 功能闭环验证 (Closed-Loop Verification)

> **这是整个审计流程中最重要的一步。**
> "功能地图的路线图闭环是最重要的" — 一个功能如果走不通完整的用户旅程，就等于不存在。

## 核心原则

闭环验证通过 **纯静态分析（Pure Static Analysis）** 完成 — 不启动浏览器，不运行项目，不依赖任何运行时环境。所有判断基于源代码文件的文本搜索和模式匹配。

验证对象：`gap-analysis.json` 中分类为 **COMPLETE** 和 **PARTIAL** 的所有功能。NOT_STARTED 的功能跳过（它们在 Step 2 中已被标记，没有可验证的代码）。

---

## 1. 闭环验证模型

每个功能的用户旅程由 4 个检查点（Checkpoint）组成。对每个功能，必须逐一验证全部 4 个环节：

```
Step A: 入口存在     →  Step B: 操作可执行    →  Step C: 有反馈      →  Step D: 结果可见
(Entry exists)         (Action executable)      (Feedback present)    (Result visible)
```

这 4 个环节构成一条完整的用户操作链路。任何一个环节的断裂，都意味着用户旅程在该处中断。

---

### Step A: 入口存在 — Can the user find and reach this feature?

**核心问题：用户能不能找到并到达这个功能？**

如果一个功能没有任何入口可达，那它对用户来说就是不存在的 — 即使代码写得再完美。

#### 静态分析检查项

- 菜单/导航配置中包含指向该功能路由的条目
- 或者：某个父页面中存在导航到该功能的按钮/链接
- 侧边栏、顶部导航、Tab 导航、面包屑 — 任何 UI 入口点都算

#### Evidence（证据）格式

记录：菜单配置文件:行号，或父组件中的 `<Link to="...">` 或 `router.push(...)` 或 `<a href="...">`

#### 按框架分类的查找目标

**React:**
```
- JSX 中的 <Link to="/feature-path">
- <NavLink to="/feature-path">
- useNavigate() → navigate('/feature-path')
- useHistory() → history.push('/feature-path')
- router.push('/feature-path')
- window.location.href = '/feature-path'
```

**Vue:**
```
- <router-link to="/feature-path">
- <router-link :to="{ name: 'featureName' }">
- this.$router.push('/feature-path')
- this.$router.push({ name: 'featureName' })
- useRouter() → router.push('/feature-path')
```

**Angular:**
```
- routerLink="/feature-path"
- [routerLink]="['/feature-path']"
- router.navigate(['/feature-path'])
- router.navigateByUrl('/feature-path')
```

**Next.js:**
```
- <Link href="/feature-path">
- useRouter() → router.push('/feature-path')
- next/navigation 的 redirect('/feature-path')
```

**菜单配置（常见模式）:**
```
- Antd Menu: <Menu.Item> 中包含 <Link>，或 items 数组中的 { key, label, path }
- Element UI: <el-menu-item index="/feature-path">
- 自定义侧边栏: menuConfig / sidebarItems / navItems 数组
- 路由配置中的 meta.menu / meta.title / meta.icon（带有菜单标记的路由）
```

#### 搜索策略

1. 首先在路由配置文件中找到该功能对应的路由路径（例如 `/users`）
2. 然后全局搜索该路径字符串，查看哪些文件引用了它
3. 检查引用处是否为导航组件（Link、NavLink、router-link 等）
4. 如果在菜单配置数组中找到，记录文件名和行号

#### 评分

- **1 分**：找到任何一个入口点（菜单项、链接、按钮导航）
- **0 分**：未找到任何入口点

---

### Step B: 操作可执行 — Can the user perform the core action?

**核心问题：用户到达页面后，能不能执行核心操作？**

一个页面如果只有静态展示而没有交互元素，或者交互元素没有绑定处理函数，那用户到了也做不了事。

#### 静态分析检查项

- 页面/组件包含交互元素：表单、带事件处理的按钮、输入框
- 表单提交处理函数存在（onSubmit, handleSubmit, form action）
- 组件或其子组件中存在 API 调用（fetch, axios, useMutation, service calls）
- 所引用的 API 端点在后端确实存在（可选但加分）

#### 按功能类型分类的预期操作元素

| 功能类型 (Feature Type) | 预期的操作元素 (Expected Action Elements) | 搜索关键词 |
|---|---|---|
| 创建/新增 (Create/Add) | 表单 + 提交按钮 + POST/PUT API 调用 | `<Form`, `onSubmit`, `handleSubmit`, `POST`, `create`, `add` |
| 编辑/更新 (Edit/Update) | 预填充的表单 + 提交按钮 + PUT/PATCH API 调用 | `<Form`, `initialValues`, `defaultValue`, `PUT`, `PATCH`, `update` |
| 删除 (Delete) | 删除按钮 + 确认弹窗 + DELETE API 调用 | `delete`, `remove`, `confirm`, `Modal.confirm`, `DELETE` |
| 列表/查看 (List/View) | 数据获取 (GET) + 渲染 (表格、列表、卡片) | `useQuery`, `useEffect` + `fetch`, `GET`, `<Table`, `<List` |
| 搜索/筛选 (Search/Filter) | 输入框/下拉框 + 查询参数 + GET API 调用 | `<Input`, `<Select`, `search`, `filter`, `query`, `keyword` |
| 导出 (Export) | 导出按钮 + 下载处理或 API 调用 | `export`, `download`, `blob`, `saveAs`, `GET` + download |
| 上传 (Upload) | 文件输入 + 上传处理 + POST API 调用 | `<Upload`, `<input type="file"`, `upload`, `FormData`, `POST` |
| 配置/设置 (Settings) | 表单/开关 + 保存按钮 + PUT/PATCH API 调用 | `<Switch`, `<Form`, `settings`, `config`, `save`, `PUT` |
| 审批/流程 (Approval/Workflow) | 审批按钮（通过/拒绝）+ POST/PUT API 调用 | `approve`, `reject`, `audit`, `POST`, `PUT` |

#### 深入检查：API 调用链路追踪

不仅检查组件中是否有 API 调用，还要追踪调用链路：

```
组件事件处理函数
  → 调用 service/api 模块的函数
    → 发出 HTTP 请求
      → 对应的 API 端点
```

例如：
```
// 组件中
const handleSubmit = () => userService.createUser(data)

// service 中
export const createUser = (data) => axios.post('/api/users', data)

// 后端
router.post('/api/users', userController.create)
```

静态分析需要追踪到至少第二层（service 调用），最好到第三层（HTTP 请求）。

#### 评分

- **1 分**：核心操作元素完备（交互元素 + 事件处理 + API 调用）
- **0 分**：缺少核心操作元素（页面存在但没有可执行的操作）

---

### Step C: 有反馈 — Does the user get feedback after the action?

**核心问题：用户执行操作后，系统有没有给出反馈？**

静默操作是最差的用户体验 — 用户点了按钮，不知道成功了还是失败了。

#### 静态分析检查项

**成功反馈 (Success Feedback):**
```javascript
// Antd
message.success('操作成功')
message.success(...)
notification.success({ message: '...' })
Modal.success({ content: '...' })

// Element UI
ElMessage.success('操作成功')
ElNotification.success({ message: '...' })
this.$message.success('...')

// React Toastify / React Hot Toast
toast.success('...')
toast('...', { type: 'success' })

// Material UI
enqueueSnackbar('...', { variant: 'success' })

// 原生
alert('操作成功')
window.alert('...')
```

**错误处理 (Error Handling):**
```javascript
// try-catch 中的用户可见反馈
catch (error) {
  message.error('操作失败')          // ✓ 有反馈
  message.error(error.message)       // ✓ 有反馈
  console.error(error)               // ✗ 用户不可见，不算
  throw error                        // ✗ 只是抛出，不算
}

// .catch() 中的反馈
.catch(err => {
  notification.error({ message: '...' })  // ✓
  toast.error('...')                       // ✓
  setState({ error: err.message })         // ✓ 如果 error 状态有渲染
})

// React Query / SWR 的 onError
onError: (error) => {
  message.error(error.message)       // ✓
}
```

**加载状态 (Loading State):**
```javascript
// 加载指示器
const [loading, setLoading] = useState(false)
const { isLoading } = useQuery(...)
const { loading } = useMutation(...)
<Spin spinning={loading}>
<Skeleton loading={loading}>
{loading && <LoadingSpinner />}
<Button loading={submitting}>
```

**操作后跳转 (Post-action Navigation):**
```javascript
// 成功后跳转 — 也是一种反馈
router.push('/list')
navigate('/list')
history.push('/list')
this.$router.push('/list')
window.location.href = '/list'
```

#### 查找位置

反馈代码通常出现在以下位置：

1. API 调用的 `.then()` / `onSuccess` / 成功回调中
2. `catch` / `onError` / 错误回调中
3. 组件的状态管理逻辑中（loading, error, success 状态）
4. 全局请求拦截器中（axios interceptors, fetch wrapper）— 注意这种情况

#### 特别注意：全局反馈处理

有些项目在 axios 拦截器或全局 fetch wrapper 中统一处理了反馈：

```javascript
// request.ts / axios.ts / http.ts
axios.interceptors.response.use(
  (response) => {
    if (response.data.code === 200) {
      message.success(response.data.message)  // 全局成功处理
    }
    return response
  },
  (error) => {
    message.error(error.response?.data?.message || '请求失败')  // 全局错误处理
    return Promise.reject(error)
  }
)
```

如果发现了全局反馈处理，那么所有通过该 HTTP 客户端发出的请求都自动具有反馈，Step C 全部通过。需要在证据中注明 "全局反馈处理 via src/utils/request.ts:XX"。

#### 评分

- **1 分**：找到任何反馈机制（成功提示、错误提示、加载状态、成功跳转 — 至少一种）
- **0 分**：静默操作 — 无任何用户可感知的反馈

---

### Step D: 结果可见 — Can the user see the result of their action?

**核心问题：操作完成后，用户能不能看到操作的结果？**

这是闭环的最后一步，也是经常被遗漏的一步。很多功能做到了 "提交成功" 的提示，但用户看不到提交后的数据变化。

#### 按操作类型分类的检查项

**创建后 (After Create):**
```javascript
// 列表数据是否重新获取
queryClient.invalidateQueries(['users'])     // React Query — 使列表缓存失效
queryClient.invalidateQueries({ queryKey: ['users'] })
mutate('/api/users')                         // SWR — 重新验证
refetch()                                     // 手动重新获取
dispatch(fetchUsers())                        // Redux — 重新 dispatch 获取 action

// 或者跳转到列表页
router.push('/users')                         // 跳转后列表页自动加载
navigate('/users')
history.push('/users')

// 或者直接更新本地状态
setUsers(prev => [...prev, newUser])          // 乐观更新
dispatch({ type: 'ADD_USER', payload: newUser })
commit('ADD_USER', newUser)                   // Vuex
```

**编辑后 (After Edit):**
```javascript
// 与创建后类似，但需要检查是否更新了对应的条目
queryClient.invalidateQueries(['users'])     // 使列表和详情缓存失效
queryClient.invalidateQueries(['user', id])
setUsers(prev => prev.map(u => u.id === id ? updated : u))  // 本地更新
```

**删除后 (After Delete):**
```javascript
// 列表中移除该条目
queryClient.invalidateQueries(['users'])
setUsers(prev => prev.filter(u => u.id !== id))  // 本地移除
dispatch({ type: 'REMOVE_USER', payload: id })
commit('REMOVE_USER', id)                    // Vuex
```

**查看/列表 (View/List):**
```javascript
// 数据渲染 — 证明获取的数据被展示给用户
users.map(user => <UserCard key={user.id} {...user} />)          // React
<tr v-for="user in users" :key="user.id">                        // Vue
<tr *ngFor="let user of users">                                   // Angular
<Table dataSource={users} columns={columns} />                   // Antd Table
<el-table :data="users">                                         // Element UI Table
```

**导出 (Export):**
```javascript
// 下载触发
const blob = new Blob([response.data])
saveAs(blob, 'export.xlsx')                   // file-saver
window.URL.createObjectURL(blob)
const link = document.createElement('a')
link.href = url; link.download = 'file.xlsx'; link.click()
window.open(downloadUrl)                      // 直接打开下载链接
```

**上传 (Upload):**
```javascript
// 上传后文件列表更新
setFileList(prev => [...prev, uploadedFile])
refetch()                                     // 重新获取文件列表
queryClient.invalidateQueries(['files'])
// 或上传后显示预览
setPreviewUrl(response.data.url)
```

#### 搜索策略

1. 从 Step B 中找到的 API 调用/mutation 的成功回调开始
2. 查看成功回调中是否有缓存失效、状态更新、或页面跳转
3. 如果有跳转，检查目标页面是否有数据获取和渲染
4. 如果有缓存失效，确认对应的 query key 在列表页中使用
5. 如果是本地状态更新，确认更新后的状态绑定到了 UI

#### 评分

- **1 分**：找到结果可见性机制（数据刷新、本地更新、跳转到结果页、下载触发）
- **0 分**：操作成功后无任何数据变化反映到 UI

---

## 2. 评分体系

每个功能获得 X/4 的评分（通过的检查点数量）。

| 评分 | 含义 | 严重度 | 行动建议 |
|------|------|--------|----------|
| **4/4** | 完整闭环 (Complete Loop) | 正常 | 无需处理，记录即可 |
| **3/4** | 基本闭环，有小缺口 (Minor Gap) | 低 (Low) | 记录但非紧急，可在后续迭代修复 |
| **2/4** | 部分闭环，有明显断裂 (Significant Break) | 中 (Medium) | 需要关注，应列入修复计划 |
| **1/4** | 严重断裂 (Severe Break) | 高 (High) | 用户旅程基本走不通，优先修复 |
| **0/4** | 无闭环 (No Loop) | 严重 (Critical) | 功能形同虚设，立即处理或移除 |

### 评分的额外维度

除了 0-4 的基本评分，还应记录以下补充信息：

**置信度 (Confidence Level):**
- **高**：证据明确，代码中有直接匹配
- **中**：证据间接，通过全局处理器或约定推断
- **低**：证据模糊，可能存在误判

**影响范围 (Impact Scope):**
- **高频功能**：每日使用的核心功能（如登录、列表查看）
- **中频功能**：经常使用（如创建、编辑）
- **低频功能**：偶尔使用（如导出、批量操作）

---

## 3. 常见闭环断裂模式

以下是经实践总结的 6 种典型闭环断裂模式。在分析时应主动比对这些模式，快速识别问题类型。

| 模式名称 | 描述 | 断裂环节 | 常见原因 | 修复建议 |
|----------|------|----------|----------|----------|
| **幽灵入口** (Ghost Entry) | 菜单中有入口，但点进去页面空白或报错 | A✓ B✗ | 路由注册了但组件未实现，或组件为空壳 | 实现组件内容，或暂时隐藏菜单入口 |
| **静默操作** (Silent Operation) | 用户点击按钮执行操作，无任何可感知的反馈 | A✓ B✓ C✗ | API 调用成功但未添加 Toast/通知/加载状态 | 在 API 回调中添加 message.success/error |
| **黑洞提交** (Black Hole Submit) | 表单提交后既不跳转也不刷新，数据去了哪里不知道 | A✓ B✓ C✓ D✗ | 提交成功有提示，但未刷新列表/未跳转到结果页 | 添加 queryClient.invalidateQueries 或 router.push |
| **孤岛功能** (Isolated Feature) | 功能本身完整，但用户无法从任何地方到达 | A✗ B✓ C✓ D✓ | 菜单遗漏、路由未注册到导航配置、或入口被条件隐藏 | 在菜单/导航中添加入口 |
| **半成品** (Half-baked) | 有页面有入口，但只有静态展示，无任何交互操作 | A✓ B✗ C✗ D✗ | 页面 UI 做了但业务逻辑/API 对接未完成 | 完成交互逻辑和 API 对接 |
| **断尾流程** (Broken Tail) | 操作执行成功也有提示，但看不到操作的结果 | A✓ B✓ C✓ D✗ | 缺少列表刷新、缓存失效、或结果页数据同步 | 添加数据刷新/缓存失效逻辑 |

### 断裂模式识别速查表

根据检查点通过情况快速匹配模式：

```
A✗ B✗ C✗ D✗  →  功能不存在或 NOT_STARTED（不应出现在闭环验证中）
A✗ B✓ C✓ D✓  →  孤岛功能
A✓ B✗ C✗ D✗  →  半成品
A✓ B✓ C✗ D✗  →  半成品（进阶版，有操作但无反馈无结果）
A✓ B✗ C✗ D✓  →  只读页面（仅列表展示，无操作能力）— 如果功能本身是 List/View 类型则可能是正常的
A✓ B✓ C✗ D✗  →  静默操作 + 断尾流程（双重断裂）
A✓ B✓ C✓ D✗  →  断尾流程 或 黑洞提交
A✓ B✓ C✗ D✓  →  静默操作（有结果但过程无反馈）
```

---

## 4. 功能地图（Feature Map）

**在逐项验证之前，先为每个功能模块绘制功能地图。** 功能地图展示了用户旅程的拓扑结构 — 从入口到最终结果的完整路径。

### 功能地图的作用

- 提供鸟瞰视图 (Bird's-eye view)，在深入细节之前先看全局
- 直观展示哪条路径是通的，哪条是断的
- 帮助用户理解审计结果
- 作为功能完整性的可视化文档

### 功能地图绘制规范

```
功能地图示例（CRUD 类型 — 用户管理模块）:

┌─ 用户管理 ────────────────────────────────────────────────┐
│  入口: 侧边栏 → /users                                    │
│  ├── 用户列表 (GET /api/users) → 表格渲染                 │
│  │   ├── 搜索: 搜索框 → query params → GET /api/users?keyword=... │
│  │   └── 分页: 分页器 → query params → GET /api/users?page=... │
│  ├── 新增用户 (按钮 → /users/create)                       │
│  │   └── 表单 → POST /api/users → Toast → 跳转列表         │
│  ├── 编辑用户 (行内按钮 → /users/:id/edit)                 │
│  │   └── 表单(预填充) → PUT /api/users/:id → Toast → 跳转   │
│  ├── 查看详情 (行内按钮 → /users/:id)                      │
│  │   └── GET /api/users/:id → 详情页渲染                    │
│  └── 删除用户 (行内按钮 → 确认框)                          │
│      └── DELETE /api/users/:id → Toast → 刷新列表           │
└───────────────────────────────────────────────────────────┘
```

```
功能地图示例（配置类型 — 系统设置模块）:

┌─ 系统设置 ────────────────────────────────────────────────┐
│  入口: 顶部导航 → /settings                               │
│  ├── 基本设置 (Tab → /settings/basic)                      │
│  │   └── 表单 → PUT /api/settings/basic → Toast            │
│  ├── 安全设置 (Tab → /settings/security)                   │
│  │   ├── 修改密码: 表单 → PUT /api/settings/password → Toast │
│  │   └── 两步验证: 开关 → PUT /api/settings/2fa → Toast    │
│  └── 通知设置 (Tab → /settings/notifications)              │
│      └── 开关列表 → PUT /api/settings/notifications → Toast │
└───────────────────────────────────────────────────────────┘
```

```
功能地图示例（导入导出类型 — 数据管理模块）:

┌─ 数据管理 ────────────────────────────────────────────────┐
│  入口: 侧边栏 → /data                                     │
│  ├── 数据列表 (GET /api/data) → 表格渲染                   │
│  ├── 导入 (按钮 → 弹窗)                                    │
│  │   └── 文件选择 → POST /api/data/import → Toast → 刷新   │
│  └── 导出 (按钮)                                           │
│      └── GET /api/data/export → Blob → 下载文件             │
└───────────────────────────────────────────────────────────┘
```

### 功能地图中的断裂标记

当检查点验证失败时，在功能地图中用 `✗` 和 `???` 标记断裂处：

```
┌─ 订单管理 ─────────────────────────────── 评分: 2/4 ──────┐
│  入口: 侧边栏 → /orders                    ✓ A            │
│  ├── 订单列表 (GET /api/orders) → 表格渲染  ✓ B           │
│  └── 导出订单 (按钮)                         ✓ B           │
│      └── GET /api/orders/export → ??? → ??? ✗ C ✗ D       │
│         （无成功提示，无下载触发）                           │
└───────────────────────────────────────────────────────────┘
```

---

## 5. 执行流程

### 5.1 完整执行流程

```
Step 1: 加载数据
  ├── 读取 gap-analysis.json
  ├── 筛选出 COMPLETE 和 PARTIAL 的功能
  └── 按模块分组

Step 2: 检测全局模式
  ├── 检查是否存在全局反馈处理（axios interceptor, fetch wrapper）
  ├── 检查是否存在全局错误边界（ErrorBoundary, global error handler）
  ├── 检查菜单/导航配置的结构和位置
  └── 记录全局模式，供后续各功能验证引用

Step 3: 逐功能验证
  ├── 对每个功能:
  │   ├── 3a. 绘制功能地图（基于路由、组件、API 调用关系）
  │   ├── 3b. 检查 Step A: 入口存在
  │   ├── 3c. 检查 Step B: 操作可执行
  │   ├── 3d. 检查 Step C: 有反馈（先检查组件级，再检查全局级）
  │   ├── 3e. 检查 Step D: 结果可见
  │   ├── 3f. 计算评分 (0-4)
  │   └── 3g. 匹配断裂模式
  └── 汇总所有结果

Step 4: 汇总报告
  ├── 按评分分组（从最差到最好）
  ├── 统计各评分段的功能数量
  ├── 标记高风险（评分 ≤ 2）的功能
  └── 生成 closed-loop.json

Step 5: 用户确认
  ├── 展示结果（从最差评分开始）
  ├── 对每个评分 ≤ 3/4 的功能请求用户确认
  └── 记录用户确认/修正的结果
```

### 5.2 详细步骤说明

#### Step 1: 加载数据

```
读取 gap-analysis.json，提取功能列表:
- 过滤条件: classification === "COMPLETE" || classification === "PARTIAL"
- 忽略: classification === "NOT_STARTED"
- 对每个功能，需要用到:
  - feature_id: 唯一标识
  - feature_name: 功能名称
  - classification: COMPLETE / PARTIAL
  - frontend_files: 前端文件列表（来自 gap analysis）
  - backend_files: 后端文件列表（来自 gap analysis）
  - route_path: 路由路径（如果 gap analysis 中有记录）
```

#### Step 2: 检测全局模式

这一步非常重要 — 很多项目使用全局处理来统一管理反馈和错误，如果不先检测全局模式，会产生大量误报。

**全局反馈处理检测:**
```
搜索以下文件模式:
- src/utils/request.{ts,js}
- src/utils/http.{ts,js}
- src/utils/axios.{ts,js}
- src/lib/fetch.{ts,js}
- src/api/index.{ts,js}
- src/services/http.{ts,js}
- src/plugins/axios.{ts,js}

在这些文件中查找:
- interceptors.response.use(
- message.success / message.error
- notification.success / notification.error
- toast.success / toast.error
- ElMessage.success / ElMessage.error
```

**全局错误边界检测:**
```
搜索:
- ErrorBoundary 组件
- componentDidCatch
- app.config.errorHandler (Vue)
- window.onerror / window.addEventListener('unhandledrejection')
```

**菜单配置检测:**
```
搜索菜单/导航配置文件:
- **/menu*.{ts,js,tsx,jsx,json}
- **/sidebar*.{ts,js,tsx,jsx}
- **/nav*.{ts,js,tsx,jsx}
- **/routes*.{ts,js,tsx,jsx} 中带 meta.menu / meta.title 的条目
- **/layout*/**/*.{ts,js,tsx,jsx} 中的导航组件
```

#### Step 3: 逐功能验证

对每个功能，按 A → B → C → D 的顺序逐一验证。

**重要原则：**
- 即使前面的环节失败，后面的环节也要继续检查。例如 A 失败不意味着跳过 B、C、D。
- 这是因为 "孤岛功能" 模式就是 A 失败但 B、C、D 都通过的情况。
- 每个环节独立评分，最后汇总。

#### Step 4-5: 汇总和确认

见后续章节 "用户确认点" 和 "输出格式"。

---

## 6. 用户确认点

### 结果展示顺序

按评分从低到高展示，让用户先关注最严重的问题：

```
展示顺序:
1. 评分 0/4 的功能（如果有）— 严重
2. 评分 1/4 的功能 — 高风险
3. 评分 2/4 的功能 — 中风险
4. 评分 3/4 的功能 — 低风险
5. 评分 4/4 的功能 — 正常（简要列出即可）
```

### 对每个评分 ≤ 3/4 的功能，展示以下信息

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
功能: PF-005 订单导出    评分: 2/4    严重度: 中
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

功能地图:
  订单列表 → 导出按钮 → GET /api/orders/export → ??? → ???

检查点详情:
  ✓ A 入口存在:   src/pages/Orders.tsx:12 — <Button>导出</Button>
  ✓ B 操作可执行: src/pages/Orders.tsx:45 — handleExport → GET /api/orders/export
  ✗ C 有反馈:     未找到成功/失败提示 in src/pages/Orders.tsx
  ✗ D 结果可见:   未找到下载触发或文件保存逻辑

断裂模式: 断尾流程

此分析是否准确？是真问题还是误报？
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 常见误报原因

用户确认时可能会指出以下误报情况，需要在分析中考虑：

| 误报类型 | 说明 | 如何处理 |
|----------|------|----------|
| **动态菜单加载** | 菜单从 API 获取，静态分析看不到菜单项 | Step A 标记为 "无法静态确认"，置信度设为低 |
| **全局错误处理** | 反馈通过全局拦截器处理，组件中看不到 | Step 2 中检测全局模式，如果有则 Step C 自动通过 |
| **集中式状态管理** | 数据更新通过 Redux/Vuex 等集中处理，组件中不直接可见 | 追踪 dispatch/commit 调用，检查 reducer/mutation |
| **SSR/ISR 页面** | 数据获取在服务端完成（getServerSideProps 等） | 检查 Next.js/Nuxt 的服务端数据获取函数 |
| **微前端架构** | 功能在子应用中，入口在主应用的注册配置里 | 检查微前端注册配置（qiankun/micro-app 等） |
| **权限控制** | 入口存在但被权限条件隐藏 | 检查 v-if/v-show 或 {condition && <Menu>} 条件 |
| **动态路由注册** | 路由通过 addRoute() 动态添加 | 搜索 router.addRoute / router.addRoutes 调用 |
| **事件总线/PubSub** | 反馈通过事件机制传递，不在当前组件中 | 搜索 EventBus.emit / $emit / eventEmitter |

---

## 7. 输出格式

### closed-loop.json Schema

```json
{
  "metadata": {
    "step": 3,
    "name": "closed-loop-verification",
    "generated_at": "2026-02-24T10:30:00Z",
    "input_files": ["gap-analysis.json"],
    "total_features_checked": 14,
    "global_patterns": {
      "global_feedback_handler": {
        "found": true,
        "file": "src/utils/request.ts",
        "line": 45,
        "type": "axios-interceptor",
        "handles_success": true,
        "handles_error": true
      },
      "global_error_boundary": {
        "found": false
      },
      "menu_config": {
        "file": "src/config/menu.ts",
        "type": "static-array"
      }
    }
  },
  "verifications": [
    {
      "feature_id": "PF-001",
      "feature_name": "用户登录",
      "classification": "COMPLETE",
      "score": 4,
      "confidence": "high",
      "checkpoints": {
        "entry": {
          "passed": true,
          "evidence": "src/layouts/Sidebar.tsx:45 — <Link to='/login'>",
          "details": "侧边栏导航中有登录入口链接"
        },
        "action": {
          "passed": true,
          "evidence": "src/pages/Login.tsx:23 — handleSubmit → POST /api/auth/login",
          "details": "登录表单有提交处理函数，调用登录 API"
        },
        "feedback": {
          "passed": true,
          "evidence": "src/pages/Login.tsx:35 — message.success('登录成功')",
          "details": "登录成功后有 Toast 提示，失败有 message.error"
        },
        "result_visible": {
          "passed": true,
          "evidence": "src/pages/Login.tsx:37 — navigate('/dashboard')",
          "details": "登录成功后跳转到仪表盘页面"
        }
      },
      "feature_map": "侧边栏 → /login → 表单提交 → POST /api/auth/login → Toast → 跳转 /dashboard",
      "broken_pattern": null
    },
    {
      "feature_id": "PF-005",
      "feature_name": "订单导出",
      "classification": "PARTIAL",
      "score": 2,
      "confidence": "high",
      "checkpoints": {
        "entry": {
          "passed": true,
          "evidence": "src/pages/Orders.tsx:12 — <Button>导出</Button>",
          "details": "订单列表页有导出按钮"
        },
        "action": {
          "passed": true,
          "evidence": "src/pages/Orders.tsx:45 — handleExport → GET /api/orders/export",
          "details": "导出按钮绑定了处理函数，调用导出 API"
        },
        "feedback": {
          "passed": false,
          "evidence": "未找到成功/失败提示 in src/pages/Orders.tsx",
          "details": "handleExport 中 API 调用后无 message/toast/notification，也无全局处理覆盖"
        },
        "result_visible": {
          "passed": false,
          "evidence": "未找到下载触发或文件保存逻辑",
          "details": "API 响应未做 Blob 处理，无 saveAs/download 逻辑"
        }
      },
      "feature_map": "订单列表 → 导出按钮 → GET /api/orders/export → ??? → ???",
      "broken_pattern": "断尾流程"
    }
  ],
  "summary": {
    "score_distribution": {
      "4/4": 8,
      "3/4": 3,
      "2/4": 2,
      "1/4": 1,
      "0/4": 0
    },
    "total_checkpoints_passed": 48,
    "total_checkpoints_checked": 56,
    "pass_rate": "85.7%",
    "broken_patterns_found": {
      "幽灵入口": 0,
      "静默操作": 1,
      "黑洞提交": 1,
      "孤岛功能": 1,
      "半成品": 1,
      "断尾流程": 2
    },
    "high_risk_features": ["PF-012", "PF-015"],
    "medium_risk_features": ["PF-005", "PF-009"]
  },
  "confirmed_by_user": false,
  "user_corrections": []
}
```

### 用户修正后的结构

当用户确认分析结果后，`confirmed_by_user` 设为 `true`。如果用户纠正了某些误报：

```json
{
  "confirmed_by_user": true,
  "user_corrections": [
    {
      "feature_id": "PF-005",
      "checkpoint": "feedback",
      "original_passed": false,
      "corrected_passed": true,
      "reason": "全局拦截器已处理，在 src/utils/request.ts:45",
      "new_score": 3
    }
  ]
}
```

---

## 8. verify 模式特别说明

当以 `verify` 模式运行闭环验证时，行为与初始审计不同。verify 模式用于在代码修复后重新检查之前有问题的功能。

### verify 模式执行流程

```
Step 1: 加载历史数据
  ├── 读取已有的 closed-loop.json（上次审计结果）
  ├── 读取最新的 feature-inventory.json 和 gap-analysis.json
  └── 筛选出上次评分 ≤ 3/4 的功能（需要重新验证的）

Step 2: 选择性重新验证
  ├── 只对上次评分 ≤ 3/4 的功能执行完整的 4 步验证
  ├── 上次 4/4 的功能跳过（除非用户明确要求全量重检）
  └── 新增功能（在新 gap-analysis.json 中有但旧 closed-loop.json 中没有的）也纳入验证

Step 3: 对比分析
  ├── 对每个重新验证的功能，比较新旧评分
  ├── 分类为: improved / unchanged / regressed
  └── 特别标记 regressed（退化）的功能 — 这可能意味着新改动破坏了已有功能

Step 4: 报告
  ├── 显示变化摘要
  ├── 对 regressed 的功能重点说明
  └── 更新 closed-loop.json
```

### verify 模式的输出格式

```json
{
  "mode": "verify",
  "previous_run": "2026-02-20T10:30:00Z",
  "current_run": "2026-02-24T15:00:00Z",
  "changes": [
    {
      "feature_id": "PF-005",
      "feature_name": "订单导出",
      "previous_score": 2,
      "current_score": 4,
      "status": "improved",
      "details": "添加了下载逻辑和成功提示，闭环完整"
    },
    {
      "feature_id": "PF-012",
      "feature_name": "批量删除",
      "previous_score": 1,
      "current_score": 1,
      "status": "unchanged",
      "details": "仍然缺少确认弹窗、反馈和列表刷新"
    },
    {
      "feature_id": "PF-003",
      "feature_name": "用户编辑",
      "previous_score": 4,
      "current_score": 3,
      "status": "regressed",
      "details": "编辑后的列表刷新逻辑被移除，Step D 不再通过"
    }
  ],
  "summary": {
    "total_reverified": 6,
    "improved": 3,
    "unchanged": 2,
    "regressed": 1,
    "newly_added": 0
  }
}
```

### verify 模式注意事项

- **不要覆盖原始 closed-loop.json** — 生成新文件或在原文件中追加 verify 结果
- **Regressed 功能需要特别标记** — 退化比 "一直没修" 更严重，说明新改动可能引入了副作用
- **对比时注意文件路径变化** — 重构可能移动了文件但功能本身没变，不算退化
- **保留历史记录** — 每次 verify 的结果都应保留，形成修复趋势

---

> **附录**（框架检查清单、边界情况、静态分析局限性）请参考 `${CLAUDE_PLUGIN_ROOT}/docs/closedloop-appendix.md`。
