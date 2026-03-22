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

## 2.12.8 交互行为清单 → `interaction-recordings.json`（仅 frontend/fullstack）

LLM 读源码中的**所有用户交互行为**（不只是动画效果），标注每个页面的关键操作和预期结果：

```json
{
  "generated_at": "ISO8601",
  "recordings": [
    {
      "screen": "页面名或路由",
      "type": "visual_effect | functional_action",
      "interaction": "LLM 描述交互行为",
      "steps": [
        {"action": "操作（click/type/drag/hover/submit）", "target": "操作目标（按钮/输入框/元素）", "value": "输入值（如有）"},
        {"action": "wait", "condition": "等待条件（如 modal 出现/列表刷新/提示消失）"}
      ],
      "expected_result": {
        "screenshot_after": "操作完成后应该看到什么（LLM 描述）",
        "ui_changes": ["哪些 UI 元素应该变化（出现/消失/更新/移动）"],
        "navigation": "是否跳转（跳到哪个页面/路由）",
        "feedback": "用户反馈（成功提示/错误提示/loading 状态）"
      },
      "source_file": "交互逻辑定义的源码文件"
    }
  ]
}
```

**两种类型**：
- `visual_effect` — 动画/过渡/hover 效果（录像验证）
- `functional_action` — 按钮点击/表单提交/删除确认（操作+截图验证）

**LLM 提取哪些交互**：
- 每个页面的**主要操作**（不是每个按钮 — 核心 CTA 和关键流程）
- 从源码的事件处理函数（onClick/onSubmit/onDrag）中推断操作和预期结果
- 从路由跳转逻辑推断导航目标
- 从 toast/modal/alert 调用推断反馈方式

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

### 交互行为采集

如果 `interaction-recordings.json` 存在 → 按清单逐项执行并采集：

```
对每个 recording:
  type = visual_effect:
    1. 导航到对应页面
    2. 启动 video 录制（LLM 选择适合当前平台的录制工具）
    3. 执行 steps 中的操作
    4. 停止录制 → 保存 recordings/{screen}_{interaction}.mp4

  type = functional_action:
    1. 导航到对应页面
    2. 截图（操作前状态）→ 保存 interactions/{screen}_{interaction}_before.png
    3. 启动 video 录制
    4. 逐步执行 steps（click/type/submit/drag）
    5. 等待 expected_result 的条件满足
    6. 截图（操作后状态）→ 保存 interactions/{screen}_{interaction}_after.png
    7. 停止录制 → 保存 recordings/{screen}_{interaction}.mp4
    8. 记录实际结果 → interactions/{screen}_{interaction}_result.json:
       {"navigation": "实际跳转目标", "feedback": "实际提示内容",
        "ui_changes": ["实际变化的元素"], "console_errors": []}
```

**四种证据**：
- **before/after 截图** → 证明操作前后 UI 变化正确
- **操作录像** → 证明操作过程流畅（动画/过渡）
- **结果 JSON** → 结构化记录实际 UI 行为（跳转/提示/元素变化）
- **API 日志** → 该操作触发的所有网络请求和响应（供接口级对比）

### 通信日志采集（HTTP + WebSocket）

每个 functional_action 执行期间，LLM 同时抓取**所有通信**（HTTP + WebSocket）：

```
对每个 functional_action:
  1. 启动 HTTP 拦截（LLM 用适合当前平台的网络拦截方式）
  2. 启动 WebSocket 拦截（捕获发送和接收的消息帧）
  3. 执行操作步骤（click/submit/drag）
  4. 等待操作完成
  5. 停止拦截 → 保存：
     interactions/{screen}_{interaction}_api.json:
     {
       "http": [
         {"method": "POST", "url": "/api/orders", "request_body": {...}, "status": 201, "response_body": {...}}
       ],
       "websocket": [
         {"direction": "received", "data": {"event": "inventory:updated", "payload": {...}}}
       ]
     }
```

**HTTP + WebSocket 都记录** — 有些操作触发 HTTP 请求同时收到 WebSocket 推送（如下单后库存实时更新）。只记录 HTTP 会遗漏推送消息。

**只记录业务通信**（过滤掉静态资源、analytics、CDN、WebSocket 心跳）。LLM 判断哪些是业务消息。

### 保存

```
visual/source/
  ├── {role_id}/               (静态截图按角色分组)
  │   ├── dashboard.png
  │   └── users.png
  ├── recordings/              (动态录像)
  │   ├── kanban_drag-reorder.mp4
  │   └── page_transition.mp4
  ├── interactions/            (交互行为证据)
  │   ├── users_create_before.png
  │   ├── users_create_after.png
  │   ├── users_create_result.json
  │   ├── users_create_api.json     ← API 日志
  │   ├── orders_delete_before.png
  │   ├── orders_delete_after.png
  │   ├── orders_delete_result.json
  │   └── orders_delete_api.json    ← API 日志
  └── route-map.json
```

### 采集闭环验证

截图和录像采集完成后，LLM 自检覆盖度 — 漏了的重试，直到全覆盖：

```
检查 1: 角色覆盖
  role-view-matrix 中的每个角色都成功登录并截图了吗？
  → 某角色登录失败 → 重试登录（不同方式）→ 仍失败 → 标记原因，不跳过

检查 2: 页面覆盖
  路由列表中每个页面都有对应截图吗？
  → 缺失 → 重新导航截图
  → 导航失败（404/权限不足）→ 记录原因

检查 3: 交互覆盖
  interaction-recordings 中每个 action 都执行了吗？
  → 缺失 → 重试操作
  → 操作失败（按钮不可用/页面变了）→ 记录原因

检查 4: API 日志覆盖
  每个 functional_action 都有 api.json 吗？
  → 缺失 → 重新采集

检查 5: 截图质量
  LLM 查看每张截图 → 是否为空白页/错误页/纯 loading 状态？
  → 质量差 → 等待页面加载完成 → 重新截图

检查 6: 录像质量
  LLM 查看每段录像 → 是否黑屏/卡住/未完成操作？
  → 质量差 → 重新录制

汇总: 输出 visual/source/capture-report.json
  {
    "total_screens": 60,
    "captured": 58,
    "failed": 2,
    "failed_reasons": [...],
    "total_interactions": 7,
    "recorded": 7,
    "quality_issues": 0
  }
```

**不降级** — 能采集的必须采集成功。采集失败的记录原因但不假装成功。
