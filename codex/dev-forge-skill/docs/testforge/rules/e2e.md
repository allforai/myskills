# 铁律 — E2E 组（Path B/C Agent 遵守）

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

### 20. Mock 数据必须反映真实格式
JWT mock、API response mock、时间格式 — 必须和真实服务返回的格式一致。Chain 0 后对比真实 JWT 和 mock JWT 结构。

### 21. E2E 断言必须穿透数据流
必须用强断言：`expect(page).toContain(createdEntity.uniqueField)`。不接受弱断言（"页面不是空白"）。

### 22. 接缝层是 bug 密度最高的地方
优先级：Chain 0 接缝验证 > 业务链 E2E > 集成测试 > 单元测试。

### 23. E2E 外部服务禁止 mock（除非明确无法调用）
有 Key 且可达 → 必须真实调用。有 sandbox → 用 sandbox。无 Key → 标记 `NOT_VERIFIED`。纯辅助服务可 mock。
