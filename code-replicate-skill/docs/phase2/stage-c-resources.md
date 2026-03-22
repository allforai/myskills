# Phase 2 Stage C — 资源发现

> 项目带什么素材？需要什么基础数据？有哪些复用模式？UI 长什么样？

---

## 2.10 asset-inventory.json — 前端素材（仅 frontend/fullstack）

LLM 扫描静态资源目录，盘点所有与代码有引用关系的素材。

每个素材分类迁移方式：
- `copy` — 直接复制（图片、字体、音视频、Lottie JSON）
- `transform` — 格式转换（主题变量、i18n key 格式）
- `replace` — 框架格式替换（React SVG 组件 → Vue SFC）

含 `theme_system` 子结构（主题实现方式、变量数量、迁移方式）。

## 2.11 seed-data-inventory.json — 后端基础数据（仅 backend/fullstack）

LLM 读 seed 脚本 / fixture 文件 / 数据库迁移 → 提取系统运行所需的基础数据。

基础数据 = 没有它系统能启动但业务不能用（字典、角色、配置、初始分类）。

每组数据记录：category, table, records（具体数据内容）, purpose, required。

## 2.12 abstractions + cross_cutting — 复用模式 + 横切关注

LLM 读 key_files → 提取：
- **abstractions**：代码复用模式（基类、mixin、DI、装饰器等，LLM 自由分类）
- **cross_cutting**：跨模块关注点（认证、日志、错误处理），含 `phase` 字段（如有阶段式中间件）
- **架构风格**：monolith / microservice / modular-monolith / serverless

## 2.12.5 角色-界面差异矩阵 → `role-view-matrix.json`（仅 frontend/fullstack）

LLM 读源码中的权限控制逻辑（路由守卫、v-if/v-show 权限判断、按钮级 RBAC、数据范围过滤），提取**不同角色在同一页面看到的差异**：

```json
{
  "generated_at": "ISO8601",
  "roles_with_credentials": [
    {"role_id": "R001", "login": {"username": "admin@demo.com", "password": "admin123"}},
    {"role_id": "R002", "login": {"username": "ops@demo.com", "password": "ops123"}}
  ],
  "differences": [
    {
      "screen": "用户管理页",
      "route": "/admin/users",
      "by_role": {
        "R001": {"visible": true, "actions": ["查看", "编辑", "删除", "导出"], "data_scope": "全部"},
        "R002": {"visible": true, "actions": ["查看", "编辑"], "data_scope": "本部门"},
        "R003": {"visible": false}
      }
    }
  ]
}
```

**Phase 1 补充**：`source_app.login` 扩展为**多角色凭证列表**（不是单一账号）。LLM 在 Phase 1 向用户收集每个角色的测试账号。

**用途**：
- Phase 2.13 截图/录像：按每个角色分别登录截图（不只用管理员截一遍）
- cr-visual：按角色对比（管理员视角 vs 管理员视角，运营视角 vs 运营视角）
- cr-fidelity F4：验证权限控制的精确还原

## 2.12.8 动态效果清单 → `interaction-recordings.json`（仅 frontend/fullstack）

LLM 读源码中的动画/过渡/交互效果（CSS transition/animation、Lottie、拖拽库、页面切换过渡等），标注哪些页面有需要录制的动态效果：

```json
{
  "generated_at": "ISO8601",
  "recordings": [
    {
      "screen": "页面名或路由",
      "interaction": "LLM 描述要录制的动态效果",
      "trigger": "LLM 描述如何触发（导航到页面/hover 按钮/点击添加/拖拽元素）",
      "duration_hint": "预估录制时长（秒）",
      "source_file": "动画/过渡效果定义的源码文件"
    }
  ]
}
```

**LLM 判断什么需要录制** — 不录所有页面（太多），只录有明显动态效果的交互。标准的页面加载不录，有特殊动画（Lottie、拖拽排序、转场过渡、实时数据刷新）才录。

## 2.13 源 App 截图 + 录像（仅 frontend/fullstack 且源 App 可运行）

在 Phase 2 阶段采集源 App 截图和动态录像 — 不等到流程末尾（源项目环境可能被清理）。

前置条件（全部硬性，不降级）：
- 后端运行（backend_start_command）
- 数据就绪（seed_command）
- 登录成功（login + bypass_command）

### 静态截图

**多角色截图**：如果 `role-view-matrix.json` 存在且 `roles_with_credentials` 有多个角色：
- 逐角色登录 → 截该角色可见的所有页面
- 保存到 `visual/source/{role_id}/{route}.png`
- route-map.json 按角色分组

**单角色截图**（无角色矩阵时）：用最高权限账号截全量页面。

截图基于**源码路由配置**（此时 experience-map 尚未生成），支持：
- URL 直达路由
- 参数化路由（LLM 从运行中的 App 获取真实 ID）
- 非 URL 页面（记录导航步骤）

### 动态录像

如果 `interaction-recordings.json` 存在 → 按清单逐项录制：

```
对每个 recording:
  1. 导航到对应页面
  2. 启动 Playwright video 录制（video: { dir: 'visual/source/recordings/' }）
  3. 执行 trigger 操作（hover/click/drag）
  4. 等待 duration_hint 秒
  5. 停止录制 → 保存 {screen}_{interaction}.mp4
```

**录像用 Playwright 的内置 video 功能**（不是屏幕录制），每段 1-3 秒的短片段。

### 保存

```
visual/source/
  ├── {role_id}/           (静态截图按角色分组)
  │   ├── dashboard.png
  │   └── users.png
  ├── recordings/          (动态录像)
  │   ├── dashboard_loading-animation.mp4
  │   ├── kanban_drag-reorder.mp4
  │   └── page_transition.mp4
  └── route-map.json       (路由 + 录像映射)
```
