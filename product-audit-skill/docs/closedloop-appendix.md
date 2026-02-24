# 闭环验证附录

> 本文件是 `closedloop.md` 的附录，包含框架检查清单、边界情况和静态分析局限性。
> 核心验证流程请参考 `${CLAUDE_PLUGIN_ROOT}/docs/closedloop.md`。

---

## 附录 A: 框架特定的检查清单

### React (Create React App / Vite + React)

```
入口检查:
  □ src/routes 或 src/router 中的路由配置
  □ Layout 组件中的 <Link> / <NavLink>
  □ 侧边栏/头部导航中的菜单配置

操作检查:
  □ useState + handler 函数
  □ useReducer + dispatch
  □ React Hook Form / Formik 表单
  □ useMutation (React Query / Apollo)
  □ useCallback 包裹的事件处理

反馈检查:
  □ antd/message, antd/notification
  □ react-toastify / react-hot-toast
  □ useState 管理的 loading/error 状态
  □ onSuccess / onError 回调

结果可见:
  □ queryClient.invalidateQueries()
  □ refetch() 调用
  □ setState 更新本地列表
  □ navigate() / useNavigate() 跳转
```

### Vue (Vue 2 / Vue 3)

```
入口检查:
  □ src/router/index.{ts,js} 路由配置
  □ Layout 组件中的 <router-link>
  □ 菜单配置文件（通常在 src/config 或 src/layout 下）

操作检查:
  □ methods 中的处理函数 (Vue 2)
  □ setup() / <script setup> 中的函数 (Vue 3)
  □ v-model 绑定的表单
  □ @click / @submit 事件绑定

反馈检查:
  □ ElMessage / ElNotification (Element Plus)
  □ this.$message / this.$notify (Element UI)
  □ 自定义 Toast 组件
  □ Loading 指令 (v-loading)

结果可见:
  □ Vuex mutations/actions 更新状态
  □ Pinia store 更新
  □ 组件中 watch 或 computed 响应变化
  □ this.$router.push() 跳转
  □ 重新调用列表获取函数
```

### Next.js (App Router / Pages Router)

```
入口检查:
  □ app/layout.tsx 或 pages/_app.tsx 中的导航
  □ next/link 的 <Link href="...">
  □ next/navigation 的 useRouter().push()
  □ 文件系统路由（app/feature/page.tsx 即路由）

操作检查:
  □ Server Actions (use server)
  □ API Routes (pages/api 或 app/api)
  □ Client component 中的 fetch/axios
  □ Form action 属性

反馈检查:
  □ useFormStatus() 加载状态
  □ useTransition() 过渡状态
  □ toast / notification 组件
  □ revalidatePath() / revalidateTag() 后的页面更新

结果可见:
  □ revalidatePath() — 使页面缓存失效
  □ revalidateTag() — 使数据标签缓存失效
  □ router.refresh() — 刷新当前页面
  □ redirect() — 服务端重定向
```

### Angular

```
入口检查:
  □ app-routing.module.ts 路由配置
  □ <a routerLink="/..."> 或 [routerLink]
  □ 导航组件中的菜单项

操作检查:
  □ (click) / (submit) 事件绑定
  □ Reactive Forms / Template-driven Forms
  □ HttpClient.post/put/delete 调用
  □ Service 中的 API 方法

反馈检查:
  □ MatSnackBar (Angular Material)
  □ NzMessageService (NG-ZORRO)
  □ 自定义 notification service
  □ Loading 状态管理

结果可见:
  □ BehaviorSubject.next() 更新
  □ NgRx dispatch + reducer 更新
  □ router.navigate() 跳转
  □ 组件 ngOnInit 重新加载
```

---

## 附录 B: 真实世界的边界情况

### 1. 同一组件多功能

一个组件可能包含多个功能（如列表页同时包含查看、搜索、删除）。每个功能需要独立验证闭环。

```
示例: UserList.tsx 包含:
- 查看列表 (View)     → A✓ B✓(GET) C(加载态) D✓(表格渲染)
- 搜索用户 (Search)    → A✓ B✓(搜索框+API) C✓(加载态) D✓(表格更新)
- 删除用户 (Delete)    → A✓(行内按钮) B✓(DELETE API) C?(Toast?) D?(刷新?)
```

### 2. 弹窗/抽屉中的功能

有些功能不是独立页面，而是在弹窗 (Modal) 或抽屉 (Drawer) 中完成。这种情况下：
- Step A: 入口是打开弹窗的按钮（不是路由导航）
- Step D: 结果可见是关闭弹窗后父页面的数据刷新

### 3. 多步骤流程

有些功能需要多个步骤才能完成（如向导/Wizard 流程）。这种情况下：
- 将整个流程视为一个功能
- Step B: 每个步骤的操作都要检查
- Step D: 最终步骤完成后的结果可见性

### 4. 异步操作

有些操作是异步的（如文件上传处理、审批流程）。这种情况下：
- Step C: 应有 "已提交" 的即时反馈
- Step D: 应有轮询或 WebSocket 获取最终结果，或者有 "查看进度" 的入口

### 5. 权限区分的功能

同一功能对不同角色可能有不同的闭环路径。在静态分析中：
- 记录权限条件（v-if="hasPermission('admin')"）
- 对每个可能的角色路径分别验证
- 在 evidence 中注明权限条件

---

## 附录 C: 静态分析的局限性

闭环验证基于纯静态分析，存在以下固有局限性。在报告中应明确告知用户：

| 局限 | 影响 | 缓解措施 |
|------|------|----------|
| 无法执行动态代码 | 无法验证运行时计算的路由、条件渲染的结果 | 标记置信度为 "低"，建议人工验证 |
| 无法检测 CSS 隐藏 | 元素存在但 `display: none` 或被 CSS 遮挡 | 超出静态分析范围，在报告中声明 |
| 无法验证 API 可用性 | 后端 API 可能存在但不可用（部署问题、数据库问题等） | 仅验证代码中 API 调用的存在性 |
| 无法检测 JavaScript 错误 | 运行时 JS 错误可能导致功能不可用 | 超出静态分析范围 |
| 第三方库的内部逻辑 | 无法追踪 node_modules 中的逻辑 | 基于库的已知行为模式推断 |
| 环境变量和配置 | 功能可能被配置开关控制 | 搜索 .env 和配置文件中的 feature flag |

**最终原则：** 静态分析给出的是 "代码层面的闭环完整性"，不等同于 "运行时的闭环完整性"。报告应明确这一区别，并建议用户对高风险功能进行人工验证。
