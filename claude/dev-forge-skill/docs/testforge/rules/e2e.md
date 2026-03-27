# 铁律 — E2E 组（Path B/C/E Agent 遵守）

### 14. E2E 选择器先看后写
写 Web UI E2E 测试前，必须先 `browser_navigate` + `browser_snapshot` 看真实 DOM 结构，基于快照中的实际元素编写选择器。**严禁不看页面凭猜测写 CSS 选择器。**

### 15. 路由模式必须探测
Flutter Web 默认 hash routing，SPA 框架可能用 hash 或 history。E2E 测试生成前必须探测路由模式（Phase 0 Step 2.5），hash 模式下所有 URL 加 `/#` 前缀。

### 16. E2E = 模拟用户，不是测试代码

E2E 严禁以下捷径：

| 严禁 | 原因 |
|------|------|
| cookie/localStorage inject 跳过登录 | 登录表单提交不了也测不出来 |
| 直接设置 Pinia/Redux store 状态 | SSR hydration 不一致测不出来 |
| 绕过 CORS（后端直调代替浏览器调） | CORS 中间件顺序错误测不出来 |
| 用 mock JWT 替代真实认证 token | JWT 算法不匹配测不出来 |
| 用 API 调用替代 UI 操作 | 按钮 click handler 没绑定测不出来 |
| 后端开着 dev auth bypass 跑 E2E | 认证链路 bug 全部逃逸 |

后端必须以接近生产的配置运行。唯一允许的捷径：Chain 0 真实登录后保存 storageState 复用。

### 17. E2E Chain 0 是一切的前提

Chain 0 验证清单（全部通过才继续）：
- .env 存在且含必要变量
- 前端页面能渲染（非白屏/500）
- 登录表单能交互
- 认证服务可达（返回 JWT）
- 后端 API 可达（JWT 验证通过）
- 登录后成功跳转
- browser console 无 error 级日志

### 18. .env 必须存在且完整
E2E 启动前检查每个子项目的 .env。缺失/不完整 → 自动推导生成。

### 19. WebGL 不稳定环境降级
WSL2/CI 无 GPU 时：用 `--web-renderer html` 构建，Playwright 加 `retries: 3` + `workers: 1`。

### 20. 禁止 Mock API 响应（升级为 #29）
不 mock HTTP API 响应。所有前端测试必须连真实后端。后端不可用 = 测试标记 NOT_TESTED，不生成假绿的 mock 测试。详见 base.md #29。

### 21. E2E 断言必须穿透数据流
必须用强断言：`expect(page).toContain(createdEntity.uniqueField)`。不接受弱断言（"页面不是空白"）。

### 22. 接缝层是 bug 密度最高的地方
优先级：Chain 0 接缝验证 > 业务链 E2E > 集成测试 > 单元测试。

### 23. E2E 外部服务禁止 mock（除非明确无法调用）
有 Key 且可达 → 必须真实调用。有 sandbox → 用 sandbox。无 Key → 标记 `NOT_VERIFIED`。纯辅助服务可 mock。

### 27. 异步接缝四态测试（零 mock）

每个跨网络 Action（API 调用、WebSocket 消息、文件上传等）必须测试 4 种动态边界状态。**全部用真实手段触发，禁止 mock 响应结果。**

| 状态 | 真实触发方式 | 验证要点 |
|------|------------|---------|
| **Pending** | Playwright `network.throttle('Slow 3G')` 减速后操作 | 有 skeleton/spinner？按钮 disabled？表单锁定？ |
| **Resolved** | 正常网速下操作 | 数据正确显示？乐观更新（如有）最终一致？ |
| **Rejected** | 发送畸形数据（空必填字段、非法 ID、超长文本）触发真实 4xx；停依赖服务触发真实 5xx | 友好错误提示？非白屏/堆栈追踪？表单数据保留？ |
| **Timeout** | Playwright `browser.offline` 或停后端进程 | 超时提示？自动重试？离线后恢复时数据不丢？ |

**执行协议**：
```
对每个跨网络 Action（从 business-flows 或 API 端点列表提取）：
1. Resolved 测试：正常操作 → 验证成功结果（这是现有 E2E 已做的）
2. Pending 测试：throttle 慢网 → 操作 → 截图 loading 态 → 验证防护措施
3. Rejected 测试：构造真实错误输入 → 操作 → 验证错误处理 UI
4. Timeout 测试：断网/停服务 → 操作 → 验证超时/离线处理

每种状态的测试独立生成，标记 test_category: "async_seam_4state"
```

**不需要全量覆盖**：优先覆盖用户高频操作的异步接缝（登录、核心 CRUD、支付），低频操作可标记 `DEFERRED`。

**为什么禁止 mock**：mock 500 → 前端对 mock 的标准 JSON 错误体显示了"服务器错误" → 通过。但真实 500 可能返回 HTML 错误页 → 前端 JSON.parse 炸了 → bug 逃逸。真实触发才能暴露真实行为。

### 31. CRUD 负向操作必测（Negative CRUD）

对每个 delete/update/状态变更操作，**必须测至少一个负向路径**：

- DELETE 有关联数据的实体 → 验证 409 拒绝 + 错误 toast + 数据仍在
- UPDATE 为无效值 → 验证 400 + 表单错误提示
- STATE 非法转换 → 验证拒绝
- CREATE 重复/无效数据 → 验证 409/400 + 错误提示

**负向 DELETE 是最高优先级**：FK 约束 → 后端 409 → interceptor → mutation onError → toast — 这条 5 节点接缝链最容易断。

### 32. E2E 链禁止只读（No Read-Only Chains）

没有写操作的 E2E 链 = 烟雾测试，不能标记为 E2E 链。E2E 链的核心价值 = 验证操作的因果关系跨页面正确传播。
