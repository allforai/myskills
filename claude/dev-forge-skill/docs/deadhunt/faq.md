## FAQ (常见问题)

### 安装相关

**Q: 需要全局安装 Playwright 吗？**
不需要。`npm install -D playwright` 安装到项目本地就行，用 `npx playwright` 运行。

**Q: Chromium 下载好慢/失败怎么办？**
设置镜像源：
```bash
# 国内用户
PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright npx playwright install chromium
```

**Q: 我的项目用 pnpm/yarn 而不是 npm？**
没问题，把 `npm install` 换成 `pnpm add` 或 `yarn add` 就行。Playwright 本身不受包管理器影响。

**Q: Windows 能用吗？**
能。静态分析脚本用 Git Bash 运行。Playwright 原生支持 Windows。

### 使用相关

**Q: 静态分析和深度测试有什么区别？**
- **静态分析**：不启动应用，只看代码。速度快（秒级），能发现路由死链、孤儿路由、API 不匹配
- **深度测试**：启动应用 + 浏览器自动化。速度慢（分钟级），能发现运行时 404、数据展示异常、流程断裂

建议先跑静态分析确认大方向，再跑深度测试。

**Q: 一定要给测试账号吗？**
深度测试必须能登录。不给密码，有三种方式：
1. **最简单**：`npx playwright codegen --save-storage=.auth/admin.json http://localhost:3000`，手动登录一次保存状态
2. **最常见**：在配置里写账号密码 `{ "method": "form", "credentials": {...} }`
3. **最灵活**：直接注入 token `{ "method": "token", "token": "eyJ..." }`

**Q: 我的登录有验证码/扫码/短信，怎么办？**
推荐用 `storage_state` 方式：手动登录一次保存状态。或者让后端在测试环境关闭验证码。详见 auth-strategy.md 的"登录认证策略"章节。

**Q: 我的项目已经有 Playwright 了，会冲突吗？**
不会。验证技能用独立的 `playwright.config.ts`（在 `.allforai/deadhunt/` 目录下），测试文件也在独立目录。运行命令加 `--config=.allforai/deadhunt/playwright.config.ts` 即可。如果你项目已有 auth state（`.auth/*.json`），验证会自动复用。

**Q: 能用在生产环境吗？**
强烈不建议。深度测试会创建/编辑/删除数据（测试 CRUD 闭环），必须在测试环境运行。静态分析不影响任何环境。

**Q: 报告中 UNKNOWN 的问题怎么处理？**
就是 skill 无法自动判断该修还是该删的问题。需要你人工确认：看一下那个功能，决定是保留还是去掉，然后告诉 Claude。

**Q: 跑完一次要多久？**
- **快速扫描** (Level 1): 20-30 秒（只看代码，不启动浏览器）
- **标准验证** (Level 2): 1-3 分钟（浏览器快速遍历每个页面一次）
- **完整验证** (Level 3): 5-15 分钟（含 CRUD 闭环、流程测试)
- **增量验证**: 30-60 秒（只验证改动的模块）

如果是第二次跑（配置已初始化），会更快。

**Q: 能集成到 CI/CD 吗？**
可以。静态分析脚本可以直接在 CI 中跑。深度测试需要 CI 环境能启动应用和浏览器（大多数 CI 服务支持 Playwright）。

```yaml
# GitHub Actions 示例
- name: 产品验证 - 静态分析
  run: bash .allforai/deadhunt/scripts/static-analyzer.sh .

- name: 产品验证 - 深度测试
  run: npx playwright test --config=.allforai/deadhunt/playwright.config.ts
```

### 误报相关

**Q: 误报太多怎么办？**
最常见的原因：
1. 用了低权限账号 → 换最高权限账号
2. 测试数据库是空的 → 导入种子数据
3. 后端服务没启动 → 确认所有服务在线
4. 多端分工没配对 → 确认 validation-profile.json 中的 crud_by_client

**Q: 报告在哪里？**
- Claude 会直接给你看报告摘要
- 完整报告文件在 `.allforai/deadhunt/output/` 目录下
- `validation-report-{client}.md` — 各端的详细报告
- `fix-tasks.json` — 可导入项目管理工具的修复清单

---

## 针对不同框架的适配说明

### React + React Router

- 路由通常在 `src/router/` 或 `src/routes/` 中
- 菜单配置可能在 `src/config/menu.ts` 或内联在侧边栏组件中
- CRUD 页面通常按 `src/pages/模块名/` 组织

### Vue + Vue Router

- 路由在 `src/router/index.ts` 或模块化的 `*.routes.ts` 中
- 权限通常用 `v-permission` 或 `v-auth` 指令
- UI 库多为 Element Plus，表格和按钮模式稳定

### Next.js (App Router)

- 文件系统路由，`app/` 目录结构即路由结构
- 菜单配置在独立文件中
- API 路由在 `app/api/` 中

### Angular

- 路由在各 module 的 `*-routing.module.ts` 中
- 权限通过 Guard 控制
- 组件按 feature module 组织
