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

## 2.13 源 App 截图（仅 frontend/fullstack 且源 App 可运行）

在 Phase 2 阶段采集源 App 截图 — 不等到流程末尾（源项目环境可能被清理）。

前置条件（全部硬性，不降级）：
- 后端运行（backend_start_command）
- 数据就绪（seed_command）
- 登录成功（login + bypass_command）

截图基于**源码路由配置**（此时 experience-map 尚未生成），支持：
- URL 直达路由
- 参数化路由（LLM 从运行中的 App 获取真实 ID）
- 非 URL 页面（记录导航步骤）

保存到 `visual/source/` + `visual/route-map.json`。
