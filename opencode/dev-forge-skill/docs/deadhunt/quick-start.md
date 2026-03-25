# 快速开始 (5 分钟上手)

### 前提条件

```bash
# 必须有
node -v      # >= 18.x
npm -v       # >= 9.x
git --version # 任意版本
bash --version # 任意版本（Mac/Linux 自带，Windows 用 Git Bash）

# 深度测试需要（仅静态分析不需要）
npx playwright --version  # 如果没有，安装步骤会自动处理

# 可选（增强功能）
python3 --version  # >= 3.8，用于 API 文档解析
jq --version       # 用于 JSON 处理，大多数 Linux 自带
curl --version     # 用于 API 探测，大多数系统自带
```

### 安装

```bash
# 安装
bash opencode/install.sh  # deadhunt 已合并入 dev-forge
```

安装后，Claude 会在首次运行验证时自动在你的项目中创建 `.allforai/deadhunt/` 目录，包括：
- ✅ 独立的验证配置（`.allforai/deadhunt/playwright.config.ts`）
- ✅ 自动发现并复用项目已有的登录状态（`.auth/*.json`）
- ✅ 所有验证产出保存在 `.allforai/deadhunt/output/`

### 三步跑通第一次验证

**第一步：静态分析（不需要启动应用）**

```bash
# 对 Claude 说：
请用 deadhunt 技能对我的项目做静态分析。
项目路径是 /path/to/my-project。
```

Claude 会：
1. 自动检测技术栈（React/Vue/Angular/...）
2. 识别所有业务模块
3. 扫描路由和菜单配置
4. **输出一份模块列表请你确认**

你需要做的：**确认模块分类是否正确，补充遗漏的模块**。

**第二步：确认项目概况**

Claude 生成 `validation-profile.json` 后会问你确认：

```
Claude: 我识别到以下模块，请确认：
1. 用户管理 — 标准 CRUD
2. 订单管理 — 工作流
3. 操作日志 — 只读
4. 仪表盘   — 展示型

模块分类正确吗？有遗漏的模块吗？
```

你只需要回答：`对的` 或 `商品管理漏了，加上`。

**第三步：深度测试（需要启动应用 + 登录）**

```bash
# 先确保应用在跑
npm run dev  # 或你的启动命令

# 然后解决登录（选一种方式）:

# 方式 A: 手动登录一次，保存状态（最万能，什么登录方式都行）
npx playwright codegen --save-storage=.allforai/deadhunt/.auth/admin.json http://localhost:3000
# → 在打开的浏览器中手动登录，关闭后状态自动保存

# 方式 B: 直接告诉 Claude 账号密码（简单表单登录）
# → 在下面的对话中告诉 Claude 就行

# 方式 C: 如果项目已有 .auth/admin.json
# → 不需要做任何事，Claude 会自动发现并复用
```

```bash
# 对 Claude 说：
请用 deadhunt 技能做深度测试。
应用跑在 http://localhost:3000。
测试账号：admin / 123456。
# 或者：登录状态已保存在 .allforai/deadhunt/.auth/admin.json
```

Claude 会自动：
1. 打开浏览器登录
2. 遍历所有菜单检查死链
3. 检查每个模块的 CRUD 入口
4. 监控所有 API 请求
5. 生成验证报告

### 完整流程演示

```
你: 请用 deadhunt 技能验证我的项目。
    项目路径 /home/david/my-ecommerce。
    这是 admin 后台，跑在 http://localhost:3000。
    测试账号 admin / admin123。

Claude: 好的，让我先分析项目结构...
        [执行 Phase 0: 读取项目文件]

        检测到：
        - 框架: React + Ant Design
        - 路由: React Router v6
        - 15 个业务模块
        - 是 monorepo，发现商户后台(apps/merchant)和 H5(apps/h5)

        请确认以下模块分类：
        ...（列出模块）

你: 对的，不过"日报管理"那个功能已经砍了。

Claude: 收到，"日报管理"标记为废弃。开始静态分析...
        [执行 Phase 1: 静态分析]

        静态分析发现：
        - 3 个菜单入口指向不存在的路由
        - 2 个路由已注册但无入口可达
        - 5 个后端 API 无前端调用

        开始深度测试...
        [执行 Phase 3: 打开浏览器，登录，遍历]

        ✅ 验证完成，生成报告。

        📊 验证报告摘要：
        - 🔴 FIX (该修): 5 个
        - 🟡 CLEAN (该删): 3 个（含你说的日报管理）
        - 🟠 HIDE (该藏): 2 个
        - ✅ 正常: 38 个
```

### 只跑静态分析（最轻量）

如果你只想快速扫一遍代码，不想启动应用：

```
# 对 Claude 说：
请用 deadhunt 技能，只做静态分析，不需要深度测试。
项目路径 /path/to/project。
```

Claude 会输出分析结果到 `.allforai/deadhunt/output/static-analysis/`：
- `routes.json` — 路由分析
- `crud-coverage.json` — CRUD 覆盖率
- `multi-client.json` — 多端检测

### 文件结构

```
your-project/
├── playwright.config.ts         # 你项目的（不动！）
├── tests/                       # 你项目的测试（不动！）
├── .auth/                       # 你项目的 auth state（会被复用）
│   └── admin.json
└── .allforai/deadhunt/                 # ← 验证技能的独立空间（由 Claude 运行时生成）
    ├── playwright.config.ts     # 验证专用配置（独立于项目的）
    ├── .auth/                   # 验证专用的登录状态
    │   └── admin.json           # (手动登录后保存在这里)
    └── output/                  # 验证产出（自动生成）
        ├── validation-profile.json
        ├── static-analysis/
        ├── tests/               # 生成的验证测试脚本
        ├── reports/
        ├── dead-links-report.json
        ├── validation-report-{client}.md
        └── fix-tasks.json
```
