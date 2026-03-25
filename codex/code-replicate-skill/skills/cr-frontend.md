---
name: cr-frontend
description: >
  Use when user wants to "replicate frontend", "component rewrite", "前端复刻",
  "React迁移", "Vue迁移", "Flutter迁移", "React Native迁移", "clone UI",
  "port frontend to", "migrate frontend", "rewrite client app", "组件复刻",
  "UI 复刻", "移动端复刻", or mentions converting existing frontend/mobile
  code to a different framework while preserving behavior.
version: "1.0.0"
---

# 前端复刻分析视角

## 概述

前端复刻专注于从客户端代码中提取完整的用户体验描述。分析目标是理解"用户能做什么、看到什么"而非"用了什么组件库"，确保迁移到任何目标框架时用户体验零丢失。

---

## 分析视角

### 页面/路由层

用户可到达的视图 — 应用的导航骨架：

- **路由定义**：路径结构、参数化路由、嵌套路由层级
- **导航结构**：主导航、侧边栏、面包屑、Tab 切换
- **深链接**：外部可直接访问的页面路径、分享链接支持
- **路由守卫**：访问控制（登录要求、角色限制、条件重定向）
- **页面布局**：布局模板、共享区域（Header/Footer/Sidebar）

> 路由层回答的问题：用户能到达哪些页面？页面之间如何跳转？哪些页面有访问限制？

### 组件层

可复用 UI 单元 — 界面的构建积木：

- **Props 接口**：组件接受的输入参数、类型、默认值、是否必填
- **事件/回调**：组件向外发出的事件、回调函数签名
- **插槽/Children**：组件的内容分发机制、具名插槽
- **组件生命周期**：初始化逻辑、销毁清理、依赖数据加载
- **组件层级**：父子关系、组合模式、高阶组件/装饰器

> 组件层回答的问题：界面由哪些可复用单元组成？它们的输入输出契约是什么？

### 状态层

数据流动 — 应用中数据如何存储和传递：

- **全局状态管理**：应用级共享状态、状态分区/模块
- **局部状态**：组件内部状态、表单状态
- **服务端状态缓存**：API 响应缓存、乐观更新、后台刷新
- **状态派生**：计算属性、选择器、数据转换管道
- **状态持久化**：本地存储、会话存储、URL 状态

> 状态层回答的问题：数据从哪里来？如何流转？在哪里被消费？

### 交互层

用户操作链 — 用户与界面的互动模式：

- **表单提交流**：校验→提交→反馈（成功/失败）→后续导航
- **搜索/筛选流**：输入→防抖→请求→结果更新→分页
- **实时更新**：WebSocket/SSE 推送→状态更新→UI 刷新
- **动画/过渡**：页面切换动画、列表增删动画、加载状态
- **手势/快捷键**：拖拽、滑动、键盘快捷键、多点触控

> 交互层回答的问题：用户执行每个操作时，系统如何响应？操作链条的完整序列是什么？

---

## Phase 2b 补充指令

模块摘要（source-summary.json 的 modules[]）时，额外提取以下前端特有信息：

### 页面清单
```
每个页面记录：
- route: 路由路径
- title: 页面标题/名称
- guard: 访问控制条件（无/登录/角色）
- layout: 使用的布局模板
```

### 组件树
```
记录组件层级关系：
- name: 组件名称
- children: 子组件列表
- props_count: Props 数量
- events_count: 事件数量
- complexity: low/medium/high（基于子组件数和逻辑量）
```

### API 调用清单
```
记录前端到后端的调用映射：
- component: 发起调用的组件/页面
- endpoint: 调用的 API 端点（method + path）
- trigger: 触发时机（mount/click/submit/interval）
- error_handling: 错误处理方式（toast/redirect/retry/inline）
```

---

## Phase 3-pre: 生成 extraction-plan

LLM 读取 source-summary.json，基于对**当前前端项目**的理解，生成 extraction-plan.json：

- `role_sources`：哪些文件定义了权限控制？（可能是路由守卫、权限组件、菜单配置...取决于项目）
- `screen_sources`：哪些文件定义了页面/视图？（可能是 pages/、app/、screens/、routes 配置...取决于项目和框架）
- `task_sources`：哪些文件包含用户操作入口？（可能是表单组件、Action 处理器、事件 Handler...取决于项目）
- `flow_sources`：哪些文件包含用户交互链？（可能是页面间导航逻辑、状态机、Store Action...取决于项目）
- `usecase_sources`：哪些文件包含条件分支？（同 screen_sources + 错误处理组件）
- `cross_cutting`：跨页面共享的机制（认证、国际化、主题、Toast...）在哪些文件中？

**禁止套用框架模板** — 必须从 source-summary 的实际模块结构、key_files 中推断。

## Phase 3: 按 extraction-plan 生成片段

按 extraction-plan 中指定的文件和提取方式，逐模块生成 JSON 片段。

### 前端分析要点

以下是前端项目常见但**不一定存在**的模式。LLM 应在 extraction-plan 中标注本项目实际使用的模式：

- **空状态和加载状态**：如果项目有数据展示页面，它们的空/加载/错误状态可能是 use-case 场景
- **响应式布局**：如果项目有多端适配逻辑，extraction-plan.screen_sources 应标注相关配置
- **离线行为**：如果项目有 Service Worker 或本地缓存，extraction-plan.constraint_sources 中应记录
- **无障碍支持**：如果项目有 ARIA/a11y 实现，extraction-plan.cross_cutting 中应标注

---

## 加载核心协议

> 核心协议详见 ./skills/code-replicate-core.md
