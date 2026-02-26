# 💀 DeadHunt

**Hunt down dead links, ghost APIs, and broken CRUD in your web app.**

> An [Agent Skill](https://agentskills.io) for Claude Code, OpenCode, Codex, and any SKILL.md-compatible agent.

## 30-second start (Claude Code)

```bash
# 1) Install
claude plugin add dv/deadhunt-skill

# 2) Ask your agent to run it
请用 deadhunt 技能验证我的项目。
项目路径是 /path/to/project。
应用跑在 http://localhost:3000。
```

## Common scenarios

| Scenario | Recommended command |
|---|---|
| Fast static-only scan (no app startup) | `/deadhunt static` |
| Standard end-to-end verification | `/deadhunt` |
| Full deep verification before release | `/deadhunt full` |
| Cross-layer field consistency check | `/deadhunt:fieldcheck` |

## What it does

| Problem | How it's found |
|---------|---------------|
| 🔴 Dead links (404) | 5-layer scanning: navigation → interaction → API → resource → edge cases |
| 🟡 Incomplete CRUD | Per-module check: does every module have the Create/Read/Update/Delete it needs? |
| 👻 Ghost features | Bidirectional: backend API exists but no UI button calls it |
| 🗑️ Stale UI | Intent classification: is this dead link a bug to fix, or junk to clean up? |
| 🔒 Permission blindspots | Frontend shows button but user lacks permission |
| 📊 Data display issues | Page opens but shows `undefined`, `NaN`, `Invalid Date` |
| 🔄 Broken flows | Create → Save → List doesn't show new item |
| 🏷️ Field inconsistencies | Cross-layer check: UI field ↔ API field ↔ Entity field ↔ DB column |

## Supported platforms

| Platform | Install method | Status |
|----------|---------------|--------|
| **Claude Code** | Plugin marketplace or `~/.claude/skills/` | ✅ Full support |
| **Claude.ai** | Upload as custom skill | ✅ Full support |
| **OpenCode** | `.opencode/skills/` or `~/.config/opencode/skills/` | ✅ Compatible |
| **Codex CLI** | `.agents/skills/` or `~/.codex/skills/` | ✅ Compatible |
| **Cursor / Windsurf / Roo Code** | Via [OpenSkills](https://github.com/numman-ali/openskills) loader | ✅ Compatible |

## Quick install

### Claude Code (recommended)

```bash
claude plugin add dv/deadhunt-skill
```

### Other platforms

Clone and copy the plugin to your agent's skill directory:

```bash
git clone https://github.com/dv/deadhunt-skill.git
```

## Usage

Once installed, just ask your agent:

```
请用 deadhunt 技能验证我的项目。
项目路径是 /path/to/project。
应用跑在 http://localhost:3000。
```

The agent will automatically detect and use the skill. See [SKILL.md](SKILL.md) for full documentation including:

- 6 usage scenarios (single app, multi-client, quick scan, incremental, etc.)
- Login/auth configuration (form, token, SSO, storage state)
- 3 verification levels (quick scan 30s, standard 2min, full 10min)
- FAQ with 15+ common questions

## Project structure

```
deadhunt-skill/
├── README.md                          # This file
├── LICENSE                            # MIT
├── SKILL.md                           # Main skill file
├── .claude-plugin/
│   ├── plugin.json                    # Claude Code plugin manifest
│   └── marketplace.json               # Claude Code marketplace catalog
├── commands/
│   ├── deadhunt.md                    # Main slash command
│   └── fieldcheck.md                  # Field consistency check command
├── docs/
│   ├── quick-start.md                 # Quick start guide
│   ├── workflow.md                     # Workflow overview
│   ├── auth-strategy.md               # Auth configuration
│   ├── phase0-analyze.md              # Phase 0: Project analysis
│   ├── phase1-static.md               # Phase 1: Static scan
│   ├── phase2-plan.md                 # Phase 2: Test planning
│   ├── phase3-test.md                 # Phase 3: Index (routes to sub-files)
│   ├── phase3/                        # Phase 3: Deep testing sub-files
│   │   ├── overview.md                # Performance optimization & levels
│   │   ├── 404-scanner.md             # Global monitor + Layer 1-5
│   │   ├── intent-classification.md   # Dead link intent (FIX/CLEAN/HIDE/PERM)
│   │   ├── validation.md              # CRUD + data display + business flow
│   │   ├── convergence.md             # Multi-round convergence
│   │   └── patrol.md                  # Patrol engine (Flutter)
│   ├── phase4-report.md               # Phase 4: Report generation
│   ├── phase5-supplement-test.md      # Phase 5: Supplementary tests
│   ├── faq.md                         # FAQ
│   └── fieldcheck/
│       ├── overview.md                # Field check execution flow
│       ├── extractors.md              # Layer extraction strategies
│       ├── matching.md                # Smart matching algorithm
│       └── report.md                  # Report format and schemas
```

### Field consistency check

```
/deadhunt:fieldcheck              # Full chain: UI ↔ API ↔ Entity ↔ DB
/deadhunt:fieldcheck frontend     # Frontend only: UI ↔ API
/deadhunt:fieldcheck backend      # Backend only: API ↔ Entity ↔ DB
/deadhunt:fieldcheck endtoend     # End-to-end: UI ↔ DB (skip middle layers)
/deadhunt:fieldcheck --module user # Single module
```

## Verification levels

| Level | Time | What it does | When to use |
|-------|------|-------------|-------------|
| **Quick scan** | 30s | Static analysis only (no browser) | Every commit |
| **Standard** | 2-3 min | Static + browser walkthrough | Daily |
| **Full** | 10-15 min | + CRUD flow tests + multi-client checks | Before release |

## Multi-client architecture support

Built for real-world projects with multiple frontends:

```
Backend API
├── Admin dashboard (React)      — manages everything
├── Merchant portal (Vue)        — manages own products/orders
├── Customer website (Vue)       — browses and buys
├── Customer H5 (Vue mobile)     — same as website, mobile optimized
├── Customer App (Flutter)       — native mobile
└── Customer MiniProgram (Wechat)— WeChat mini program
```

The skill understands role-based differences (admin vs merchant vs customer) and platform differences (web vs mobile vs mini program), so it won't false-positive when Admin lacks a "place order" button (that's the customer's job).

## Output

All output goes to `.allforai/deadhunt/` in your project root — completely separate from your existing Playwright config and tests.

```
your-project/
└── .allforai/deadhunt/
    ├── playwright.config.ts          # 验证专用配置（不侵入项目原有配置）
    ├── .auth/                        # 验证专用登录状态
    │   └── admin.json
    └── output/                       # 验证产出（自动生成）
        ├── validation-profile.json   # 项目概况（初始化后持久复用）
        ├── static-analysis/          # Phase 1 静态分析结果
        ├── tests/                    # 生成的验证测试脚本
        ├── dead-links-report.json    # 死链报告
        ├── validation-report-*.md    # 可读报告（按客户端分文件）
        ├── fix-tasks.json            # 修复任务清单
        └── field-analysis/           # /fieldcheck 输出
            ├── field-profile.json    # 跨层字段提取结果
            ├── field-mapping.json    # 字段对应关系
            ├── field-issues.json     # 问题清单
            └── field-report.md       # 可读报告
```

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Test your changes
4. Submit a PR

## License

MIT — see [LICENSE](LICENSE) for details.


---

## 内嵌文档（自动汇总）

> 以下内容已从子文档汇总到 README，便于单文件阅读。

### 来源文件：`docs/auth-strategy.md`

## 登录认证策略 (Auth Strategy)

> 深度测试的第一步就是登录。登录方式千差万别，必须在验证前搞清楚。

### 登录方式分类

```
登录方式              配置方式                   自动化难度
─────────────────────────────────────────────────────────
表单登录(账号+密码)    credentials: {user, pass}   ⭐ 最简单
表单+图形验证码        credentials + captcha 策略   ⭐⭐ 需要绕过
表单+滑块验证          credentials + slider 策略    ⭐⭐⭐ 较难
短信验证码登录         需要 mock 或万能验证码       ⭐⭐ 需配合后端
扫码登录(微信等)       不适合自动化                ⭐⭐⭐⭐ 建议换方式
SSO/OAuth 跳转        storageState 或 token 注入   ⭐⭐ 需要策略
Token 直接注入         token: "xxx"                 ⭐ 最简单
Cookie 注入           cookies: [{...}]             ⭐ 简单
已有 storageState     reuse_auth: "path/to/state"  ⭐ 最简单
```

### auth 配置格式

每个 client 的 `auth` 字段支持以下方式：

```json
{
  "auth": {
    "method": "form | token | cookie | storage_state | sso | custom_script",

    // ── method: "form" ──
    // 最常见：填用户名密码，点登录
    "login_url": "/login",
    "credentials": {
      "username": "admin",
      "password": "123456"
    },
    "selectors": {
      "username_input": "#username",
      "password_input": "#password",
      "submit_button": "#login-btn"
    },
    "captcha_strategy": "none | test_env_disabled | universal_code | api_bypass",
    "universal_captcha": "8888",
    "login_success_indicator": "url_changed | selector_appeared | cookie_set",
    "success_url_pattern": "/dashboard",
    "success_selector": ".user-avatar, .ant-layout-sider",

    // ── method: "token" ──
    // 最简单：直接注入 token 到 localStorage/header
    "token": "eyJhbGciOiJIUz...",
    "token_storage": "localStorage | sessionStorage | cookie",
    "token_key": "access_token",
    "token_refresh": "https://api.example.com/auth/refresh",

    // ── method: "cookie" ──
    // 直接设置 cookie
    "cookies": [
      {
        "name": "session_id",
        "value": "abc123...",
        "domain": "localhost",
        "path": "/"
      }
    ],

    // ── method: "storage_state" ──
    // 复用已有的 Playwright auth state
    "state_file": ".auth/admin.json",

    // ── method: "sso" ──
    // SSO/OAuth 跳转登录
    "sso_provider": "keycloak | auth0 | custom",
    "sso_login_url": "https://sso.example.com/auth",
    "credentials": { "username": "admin", "password": "123456" },
    "callback_url_pattern": "/auth/callback",

    // ── method: "custom_script" ──
    // 完全自定义：指向一个登录脚本
    "script": ".allforai/deadhunt/scripts/custom-login.ts"
  }
}
```

### 登录实现

```typescript
// ============================================
// auth.ts — 统一登录入口
// ============================================
import { Page, BrowserContext } from '@playwright/test';

interface AuthConfig {
  method: 'form' | 'token' | 'cookie' | 'storage_state' | 'sso' | 'custom_script';
  [key: string]: any;
}

/**
 * 根据 auth 配置执行登录
 * 所有测试的 beforeAll/beforeEach 都调用这个函数
 */
export async function authenticate(
  page: Page,
  context: BrowserContext,
  config: AuthConfig,
  baseUrl: string
): Promise<boolean> {

  switch (config.method) {

    // ────────────────────────────────────
    case 'form':
      return await loginByForm(page, baseUrl, config);

    // ────────────────────────────────────
    case 'token':
      return await loginByToken(page, context, baseUrl, config);

    // ────────────────────────────────────
    case 'cookie':
      return await loginByCookie(context, baseUrl, config);

    // ────────────────────────────────────
    case 'storage_state':
      return await loginByStorageState(context, config);

    // ────────────────────────────────────
    case 'sso':
      return await loginBySSO(page, baseUrl, config);

    // ────────────────────────────────────
    case 'custom_script':
      const customLogin = require(config.script);
      return await customLogin(page, context, baseUrl, config);

    default:
      throw new Error(`不支持的登录方式: ${config.method}`);
  }
}

// ============================================
// 各登录方式的具体实现
// ============================================

/** 方式 1: 表单登录（最常见） */
async function loginByForm(
  page: Page, baseUrl: string, config: AuthConfig
): Promise<boolean> {
  const loginUrl = `${baseUrl}${config.login_url || '/login'}`;
  await page.goto(loginUrl);
  await page.waitForLoadState('networkidle').catch(() => {});

  const selectors = config.selectors || {};

  // 找到用户名输入框
  const usernameInput = selectors.username_input
    ? page.locator(selectors.username_input)
    : page.locator([
        'input[name="username"]',
        'input[name="account"]',
        'input[name="email"]',
        'input[name="phone"]',
        'input[type="text"]',
        '#username', '#account', '#email',
      ].join(', ')).first();

  // 找到密码输入框
  const passwordInput = selectors.password_input
    ? page.locator(selectors.password_input)
    : page.locator([
        'input[name="password"]',
        'input[type="password"]',
        '#password',
      ].join(', ')).first();

  // 找到登录按钮
  const submitButton = selectors.submit_button
    ? page.locator(selectors.submit_button)
    : page.locator([
        'button[type="submit"]',
        'button:has-text("登录")',
        'button:has-text("登 录")',
        'button:has-text("Sign in")',
        'button:has-text("Log in")',
        '.login-btn', '#login-btn',
      ].join(', ')).first();

  // 填写表单
  await usernameInput.fill(config.credentials.username);
  await passwordInput.fill(config.credentials.password);

  // 处理验证码
  if (config.captcha_strategy === 'universal_code' && config.universal_captcha) {
    const captchaInput = page.locator(
      'input[name="captcha"], input[name="code"], input[name="verifyCode"], #captcha'
    ).first();
    if (await captchaInput.count() > 0) {
      await captchaInput.fill(config.universal_captcha);
    }
  }

  // 点击登录
  await submitButton.click();

  // 等待登录成功
  return await waitForLoginSuccess(page, baseUrl, config);
}

/** 方式 2: Token 注入 */
async function loginByToken(
  page: Page, context: BrowserContext, baseUrl: string, config: AuthConfig
): Promise<boolean> {
  // 先访问首页
  await page.goto(baseUrl);

  const storage = config.token_storage || 'localStorage';
  const key = config.token_key || 'access_token';
  const token = config.token;

  if (storage === 'localStorage') {
    await page.evaluate(({ k, v }) => localStorage.setItem(k, v), { k: key, v: token });
  } else if (storage === 'sessionStorage') {
    await page.evaluate(({ k, v }) => sessionStorage.setItem(k, v), { k: key, v: token });
  } else if (storage === 'cookie') {
    await context.addCookies([{
      name: key, value: token,
      domain: new URL(baseUrl).hostname, path: '/',
    }]);
  }

  // 刷新页面使 token 生效
  await page.reload();
  await page.waitForLoadState('networkidle').catch(() => {});

  return true;
}

/** 方式 3: Cookie 注入 */
async function loginByCookie(
  context: BrowserContext, baseUrl: string, config: AuthConfig
): Promise<boolean> {
  const cookies = config.cookies.map((c: any) => ({
    ...c,
    domain: c.domain || new URL(baseUrl).hostname,
    path: c.path || '/',
  }));
  await context.addCookies(cookies);
  return true;
}

/** 方式 4: 复用已有的 Playwright storageState */
async function loginByStorageState(
  context: BrowserContext, config: AuthConfig
): Promise<boolean> {
  // Playwright 原生支持：如果项目已有 auth setup
  // 在 playwright.config.ts 中 use: { storageState: '.auth/admin.json' }
  // 这里不需要额外操作，只需确认文件存在
  const fs = require('fs');
  if (!fs.existsSync(config.state_file)) {
    throw new Error(
      `storageState 文件不存在: ${config.state_file}\n` +
      `提示: 先运行 npx playwright codegen --save-storage=.auth/admin.json ${config.run_url || ''}\n` +
      `在打开的浏览器中手动登录，关闭后会自动保存登录状态。`
    );
  }
  return true;
}

/** 方式 5: SSO/OAuth 登录 */
async function loginBySSO(
  page: Page, baseUrl: string, config: AuthConfig
): Promise<boolean> {
  // 访问应用，会被重定向到 SSO 登录页
  await page.goto(baseUrl);
  await page.waitForLoadState('networkidle').catch(() => {});

  // 现在应该在 SSO 登录页
  const currentUrl = page.url();
  if (!currentUrl.includes(new URL(config.sso_login_url).hostname)) {
    // 没有被重定向到 SSO，可能已经登录了
    return true;
  }

  // 在 SSO 页面填写凭证
  // SSO 页面的表单结构因供应商而异
  const usernameInput = page.locator(
    'input[name="username"], input[name="email"], input[name="login"], #username'
  ).first();
  const passwordInput = page.locator('input[type="password"]').first();
  const submitButton = page.locator(
    'button[type="submit"], input[type="submit"], #kc-login'
  ).first();

  await usernameInput.fill(config.credentials.username);
  await passwordInput.fill(config.credentials.password);
  await submitButton.click();

  // 等待回调跳转回应用
  await page.waitForURL(`${baseUrl}/**`, { timeout: 15000 });
  return true;
}

/** 判断登录是否成功 */
async function waitForLoginSuccess(
  page: Page, baseUrl: string, config: AuthConfig
): Promise<boolean> {
  const indicator = config.login_success_indicator || 'url_changed';

  try {
    switch (indicator) {
      case 'url_changed':
        // 等待 URL 离开登录页
        await page.waitForURL(
          url => !url.toString().includes(config.login_url || '/login'),
          { timeout: 10000 }
        );
        return true;

      case 'selector_appeared':
        // 等待某个登录后才有的元素出现
        await page.waitForSelector(
          config.success_selector || '.user-avatar',
          { timeout: 10000 }
        );
        return true;

      case 'cookie_set':
        // 等待特定 cookie 出现
        await page.waitForFunction(
          (name) => document.cookie.includes(name),
          config.success_cookie || 'token',
          { timeout: 10000 }
        );
        return true;

      default:
        // 默认等一下看看
        await page.waitForTimeout(3000);
        return !page.url().includes('/login');
    }
  } catch (e) {
    console.error('❌ 登录失败:', e.message);
    await page.screenshot({ path: 'screenshots/login-failed.png' });
    return false;
  }
}
```

### 自动检测登录方式

在 Phase 0 分析项目时，自动推断登录方式：

```bash
# 检测项目中的登录相关代码
PROJECT="$1"

echo "🔍 检测登录方式..."

# 1. 检查是否有 Playwright auth setup（项目已解决登录问题）
if [ -f "$PROJECT/.auth/admin.json" ] || [ -f "$PROJECT/auth.setup.ts" ]; then
  echo "  ✅ 发现 Playwright storageState — 推荐 method: storage_state"
fi

if grep -rq "setup.*auth\|storageState\|storage.state" "$PROJECT/playwright.config"* 2>/dev/null; then
  echo "  ✅ 发现项目 Playwright 配置中有 auth setup — 推荐复用"
fi

# 2. 检查登录页面类型
LOGIN_FILE=$(find "$PROJECT/src" -iname "*login*" -name "*.tsx" -o -name "*.vue" 2>/dev/null | head -1)
if [ -n "$LOGIN_FILE" ]; then
  echo "  📝 登录组件: $LOGIN_FILE"

  # 检查是否有验证码
  if grep -qi "captcha\|验证码\|verif" "$LOGIN_FILE"; then
    echo "  ⚠️ 登录页有验证码 — 需要配置 captcha_strategy"
  fi

  # 检查是否有 SSO/OAuth
  if grep -qi "oauth\|sso\|cas\|keycloak\|auth0" "$LOGIN_FILE"; then
    echo "  ⚠️ 登录页有 SSO/OAuth — 推荐 method: sso 或 storage_state"
  fi

  # 检查是否有短信登录
  if grep -qi "sms\|短信\|手机号\|phone" "$LOGIN_FILE"; then
    echo "  ⚠️ 登录页有短信验证 — 推荐 method: token 或 storage_state"
  fi

  # 检查是否有扫码登录
  if grep -qi "qrcode\|扫码\|scan" "$LOGIN_FILE"; then
    echo "  ⚠️ 登录页有扫码 — 不适合自动化，推荐 method: token 或 storage_state"
  fi
fi

# 3. 检查 token 存储方式
if grep -rq "localStorage.*token\|setItem.*token" "$PROJECT/src" 2>/dev/null; then
  echo "  💡 Token 存在 localStorage — 可用 method: token"
fi

if grep -rq "sessionStorage.*token" "$PROJECT/src" 2>/dev/null; then
  echo "  💡 Token 存在 sessionStorage — 可用 method: token (token_storage: sessionStorage)"
fi

if grep -rq "cookie.*token\|Cookies.set" "$PROJECT/src" 2>/dev/null; then
  echo "  💡 Token 存在 Cookie — 可用 method: cookie"
fi
```

### 与项目已有 Playwright 的集成

> **原则：绝不侵入项目已有的 Playwright 配置和测试。**

```
项目已有 Playwright 时的隔离策略：

project/
├── playwright.config.ts          ← 项目自己的（不动）
├── tests/                        ← 项目自己的测试（不动）
├── .auth/                        ← 项目的 auth state（可以复用！）
│   └── admin.json
└── .allforai/deadhunt/                  ← 验证技能的独立空间
    ├── playwright.config.ts      ← 验证专用配置（独立）
    ├── output/
    │   ├── tests/                ← 生成的验证测试（独立）
    │   └── reports/
    └── scripts/
```

验证专用的 Playwright 配置：

```typescript
// .allforai/deadhunt/playwright.config.ts
import { defineConfig } from '@playwright/test';

export default defineConfig({
  // 测试文件只在验证目录下
  testDir: './output/tests',

  // 输出也在验证目录下
  outputDir: './output/test-results',

  timeout: 30000,
  retries: 1,

  use: {
    baseURL: process.env.VALIDATION_BASE_URL || 'http://localhost:3000',
    screenshot: 'only-on-failure',
    trace: 'on-first-retry',
    reducedMotion: 'reduce',

    // 关键：如果项目已有 auth state，直接复用
    // storageState: '../.auth/admin.json',
  },

  reporter: [
    ['json', { outputFile: './output/reports/test-results.json' }],
  ],
});
```

独立配置：

```bash
# 使用验证专用配置运行（不影响项目的 playwright.config）
npx playwright test --config=.allforai/deadhunt/playwright.config.ts
```

### 复用项目已有的 auth setup

如果项目已经解决了登录问题（常见于成熟项目），优先复用：

```typescript
// 检测项目中已有的 auth setup
async function detectExistingAuth(projectRoot: string): Promise<AuthConfig | null> {
  const fs = require('fs');
  const path = require('path');

  // 1. 检查 .auth/ 的 storageState 文件
  const authDir = path.join(projectRoot, '.auth');
  if (fs.existsSync(authDir)) {
    const files = fs.readdirSync(authDir).filter((f: string) => f.endsWith('.json'));
    if (files.length > 0) {
      console.log(`✅ 发现项目 auth state: ${files.join(', ')}`);
      return {
        method: 'storage_state',
        state_file: path.join(authDir, files[0]),
      };
    }
  }

  // 2. 检查 playwright.config 中的 storageState 配置
  const configFiles = ['playwright.config.ts', 'playwright.config.js'];
  for (const cf of configFiles) {
    const configPath = path.join(projectRoot, cf);
    if (fs.existsSync(configPath)) {
      const content = fs.readFileSync(configPath, 'utf-8');
      const match = content.match(/storageState:\s*['"]([^'"]+)['"]/);
      if (match) {
        console.log(`✅ 项目 Playwright 配置中已有 storageState: ${match[1]}`);
        return {
          method: 'storage_state',
          state_file: path.join(projectRoot, match[1]),
        };
      }
    }
  }

  // 3. 检查是否有 auth.setup.ts（Playwright 推荐的 auth setup 模式）
  const setupFiles = [
    'tests/auth.setup.ts', 'e2e/auth.setup.ts',
    'tests/setup/auth.ts', 'test/auth.setup.ts',
  ];
  for (const sf of setupFiles) {
    if (fs.existsSync(path.join(projectRoot, sf))) {
      console.log(`✅ 发现项目 auth setup 脚本: ${sf}`);
      console.log('  建议：先运行项目的 auth setup 生成 storageState，再跑验证');
      return null;  // 需要用户先运行 auth setup
    }
  }

  return null;  // 未发现已有 auth，需要配置
}
```

### 登录失败的处理

```typescript
/** 登录失败后的诊断和恢复 */
async function handleLoginFailure(page: Page, config: AuthConfig): Promise<string> {
  const url = page.url();
  const bodyText = await page.textContent('body').catch(() => '') || '';

  // 诊断失败原因
  if (bodyText.includes('密码错误') || bodyText.includes('incorrect password')) {
    return '❌ 密码错误 — 请检查 credentials 配置';
  }
  if (bodyText.includes('账号不存在') || bodyText.includes('user not found')) {
    return '❌ 账号不存在 — 请确认测试账号已创建';
  }
  if (bodyText.includes('验证码') || bodyText.includes('captcha')) {
    return '❌ 验证码验证失败 — 请配置 captcha_strategy 或在测试环境关闭验证码';
  }
  if (bodyText.includes('账号锁定') || bodyText.includes('locked')) {
    return '❌ 账号被锁定 — 可能是多次自动化登录触发了安全策略';
  }
  if (url.includes('/login')) {
    return '❌ 仍在登录页 — 登录未成功，请检查选择器是否匹配';
  }

  return `❌ 登录失败 (原因未知) — 当前 URL: ${url}，请截图查看`;
}

/** 生成 storageState（半自动方式） */
// 如果自动登录搞不定（有复杂验证码/扫码），用这个方式：
// 1. 打开浏览器让用户手动登录
// 2. 保存登录状态供后续自动化使用

// 命令:
// npx playwright codegen --save-storage=.allforai/deadhunt/.auth/admin.json http://localhost:3000
//
// 这会打开一个浏览器，你手动登录后关闭浏览器，
// 登录状态（cookie + localStorage）会自动保存到 .auth/admin.json
// 后续所有测试直接复用这个状态，不需要再登录
```


### 来源文件：`docs/faq.md`

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


### 来源文件：`docs/fieldcheck/extractors.md`

## 字段提取参考 — 各层提取策略

> 本文档定义了 4 层字段模型中每一层的字段提取方法。
> 每一层均提供：搜索命令、提取模式、输出 JSON 格式。
> Agent 应按 L4 → L3 → L2 → L1 的顺序逐层提取，最后进行跨层比对。

```
┌─────────────────────────────────────────────────────────┐
│  L1  UI 显示层    表格列 / 表单字段 / 模板绑定           │
│  L2  API 接口层   请求参数 / 响应字段 / DTO              │
│  L3  实体层       ORM Entity / Model / Struct            │
│  L4  数据库层     DDL / Migration / Schema 定义          │
└─────────────────────────────────────────────────────────┘
```

---

### L4: 数据库层提取

> 数据库层是字段的"事实来源"。所有字段名以数据库实际列名为准。
> 支持 9 种 ORM / Schema 定义方式 + SQL Migration 兜底。

#### Prisma

```bash
# 定位 schema 文件
find . -name "schema.prisma" -not -path "*/node_modules/*" 2>/dev/null

# 提取 model 块（含 @map 列名映射）
grep -n "^model\s\|^\s*\w.*@map\|^\s*\w.*@id\|^\s*\w.*@default\|^\s*@@map" \
  --include="*.prisma" -r prisma/ 2>/dev/null
```

提取规则：

| Prisma 语法 | 提取逻辑 |
|---|---|
| `model User {` | 表名 = `User` 的复数小写形式，或取 `@@map("xxx")` |
| `userName String` | 列名 = `userName`（Prisma 默认驼峰映射到蛇形） |
| `userName String @map("user_name")` | 列名 = `user_name`（`@map` 优先） |
| `@@map("t_user")` | 表名 = `t_user` |
| `isDeleted Boolean @default(false)` | 列名 = `isDeleted`，标记为系统字段 |
| `posts Post[]` | 跳过 — 关系字段，非数据库列 |

#### TypeORM

```bash
# 定位 Entity 文件
grep -rln "@Entity" --include="*.ts" server/src/ src/ 2>/dev/null

# 提取 @Column 及 @PrimaryGeneratedColumn
grep -n "@Column\|@PrimaryGeneratedColumn\|@Entity\|@CreateDateColumn\|@UpdateDateColumn\|@DeleteDateColumn" \
  --include="*.ts" -r server/src/ src/ 2>/dev/null
```

提取规则：

| TypeORM 语法 | 提取逻辑 |
|---|---|
| `@Entity("users")` | 表名 = `users` |
| `@Entity({ name: "t_user" })` | 表名 = `t_user` |
| `@Column()` | 列名 = 属性名 |
| `@Column({ name: "user_name" })` | 列名 = `user_name` |
| `@PrimaryGeneratedColumn()` | 列名 = 属性名，标记为主键 |
| `@CreateDateColumn()` | 列名 = 属性名，标记为系统字段 |
| `@Column({ select: false })` | 列存在但默认不查询，需标注 |

#### JPA / Hibernate (Java)

```bash
# 定位 Entity 类
grep -rln "@Entity" --include="*.java" src/ 2>/dev/null

# 提取表名和列定义
grep -n "@Table\|@Column\|@Id\|@Transient\|@JoinColumn\|@GeneratedValue" \
  --include="*.java" -r src/ 2>/dev/null
```

提取规则：

| JPA 语法 | 提取逻辑 |
|---|---|
| `@Table(name = "t_user")` | 表名 = `t_user` |
| `@Column(name = "user_name")` | 列名 = `user_name` |
| `@Column` 无 `name` | 列名 = 属性名（按 JPA 命名策略转换） |
| `@Id` + `@GeneratedValue` | 列名 = 属性名，标记为主键 |
| `@Transient` | **跳过** — 非持久化字段 |
| `@JoinColumn(name = "dept_id")` | 列名 = `dept_id`（外键列） |
| `@Enumerated(EnumType.STRING)` | 列存在，类型为 `varchar` |

#### GORM (Go)

```bash
# 定位含 gorm tag 的 struct
grep -rln 'gorm:"' --include="*.go" internal/ pkg/ models/ 2>/dev/null

# 提取字段定义
grep -n 'gorm:"\|type\s\+struct\s*{' --include="*.go" -r internal/ pkg/ models/ 2>/dev/null
```

提取规则：

| GORM 语法 | 提取逻辑 |
|---|---|
| `type User struct {` | 表名 = `users`（复数蛇形），或取 `TableName()` 方法 |
| `` UserName string `gorm:"column:user_name"` `` | 列名 = `user_name` |
| `` gorm:"primaryKey" `` | 标记为主键 |
| `` gorm:"-" `` | **跳过** — 非数据库字段 |
| `` gorm:"-:all" `` | **跳过** — 完全忽略 |
| `gorm.Model` (嵌入) | 展开为 `id`, `created_at`, `updated_at`, `deleted_at`，全部标记为系统字段 |

#### Django ORM (Python)

```bash
# 定位 models.py
find . -name "models.py" -not -path "*/migrations/*" -not -path "*/.venv/*" 2>/dev/null

# 提取字段定义
grep -n "models\.\w*Field\|class\s\+\w*(models.Model)\|db_column\|db_table" \
  --include="*.py" -r */models.py 2>/dev/null
```

提取规则：

| Django 语法 | 提取逻辑 |
|---|---|
| `class User(models.Model):` | 表名 = `{app_label}_user`，或取 `Meta.db_table` |
| `user_name = models.CharField(...)` | 列名 = `user_name` |
| `user_name = models.CharField(db_column="uname")` | 列名 = `uname` |
| `dept = models.ForeignKey(...)` | 列名 = `dept_id`（Django 自动追加 `_id`） |
| `dept = models.ForeignKey(db_column="department_id")` | 列名 = `department_id` |
| `models.OneToOneField(...)` | 同 ForeignKey，追加 `_id` |
| `models.ManyToManyField(...)` | **跳过** — 生成中间表，非当前表列 |

#### MyBatis (XML Mapper)

```bash
# 定位 mapper XML
find . -name "*Mapper.xml" -o -name "*mapper.xml" 2>/dev/null

# 提取 resultMap 映射
grep -n "<resultMap\|<result\s\|<id\s\|<association\|<collection" \
  --include="*.xml" -r src/main/resources/ mapper/ 2>/dev/null
```

提取规则：

| MyBatis 语法 | 提取逻辑 |
|---|---|
| `<resultMap type="User">` | 实体 = `User` |
| `<id column="id" property="id"/>` | 列名 = `id`，属性名 = `id`，标记主键 |
| `<result column="user_name" property="userName"/>` | 列名 = `user_name`，属性名 = `userName` |
| `<association property="dept">` | 嵌套实体，递归提取 |
| `SELECT` 语句中直接列出的列 | 兜底方案，当无 `resultMap` 时从 SQL 提取 |

#### Sequelize

```bash
# 定位 Model 定义
grep -rln "Model.init\|sequelize.define\|DataTypes\." --include="*.ts" --include="*.js" \
  server/ src/ 2>/dev/null

# 提取字段
grep -n "DataTypes\.\|type:\s*DataTypes\|field:\s*['\"]" --include="*.ts" --include="*.js" \
  -r server/ src/ 2>/dev/null
```

提取规则：

| Sequelize 语法 | 提取逻辑 |
|---|---|
| `User.init({ ... }, { tableName: 'users' })` | 表名 = `users` |
| `userName: { type: DataTypes.STRING }` | 列名 = `userName`（默认驼峰），开启 `underscored` 时为 `user_name` |
| `userName: { type: DataTypes.STRING, field: 'user_name' }` | 列名 = `user_name`（`field` 优先） |
| `{ underscored: true }` 选项 | 全局驼峰→蛇形转换 |
| `{ timestamps: true }` | 自动追加 `createdAt`, `updatedAt`，标记为系统字段 |
| `{ paranoid: true }` | 自动追加 `deletedAt`，标记为系统字段 |

#### Drizzle

```bash
# 定位 schema 文件
grep -rln "pgTable\|mysqlTable\|sqliteTable" --include="*.ts" src/ drizzle/ db/ 2>/dev/null

# 提取表和列定义
grep -n "pgTable\|mysqlTable\|sqliteTable\|varchar\|integer\|boolean\|text\|timestamp\|serial" \
  --include="*.ts" -r src/ drizzle/ db/ 2>/dev/null
```

提取规则：

| Drizzle 语法 | 提取逻辑 |
|---|---|
| `export const users = pgTable('users', { ... })` | 表名 = `users` |
| `userName: varchar('user_name', { length: 50 })` | 列名 = `user_name`（第一个参数为数据库列名） |
| `id: serial('id').primaryKey()` | 列名 = `id`，标记为主键 |
| `.notNull()` | nullable = `false` |
| `.default(...)` | 记录默认值 |

#### SQL Migration 兜底

> 当以上 ORM 均未检测到时，回退到直接解析 SQL migration 文件。

```bash
# 定位 migration 文件
find . -path "*/migrations/*" -name "*.sql" \
  -o -path "*/migrate/*" -name "*.sql" \
  -o -name "*.up.sql" \
  2>/dev/null | sort

# 提取 CREATE TABLE / ALTER TABLE
grep -n "CREATE TABLE\|ALTER TABLE\|ADD COLUMN\|DROP COLUMN" \
  --include="*.sql" -r migrations/ db/ 2>/dev/null
```

提取规则：

| SQL 语法 | 提取逻辑 |
|---|---|
| `CREATE TABLE users (` | 表名 = `users` |
| `user_name VARCHAR(50) NOT NULL` | 列名 = `user_name`，类型 = `varchar`，nullable = `false` |
| `ALTER TABLE users ADD COLUMN email VARCHAR(100)` | 追加列 `email` 到 `users` 表 |
| `ALTER TABLE users DROP COLUMN old_field` | 从结果中移除 `old_field` |
| `PRIMARY KEY (id)` | 标记 `id` 为主键 |

> **提取优先级**：ORM schema 定义 > SQL migration（因为 migration 可能包含已回滚的变更）。
> 当两者都存在时，以 ORM 为准，migration 用于交叉验证。

#### L4 输出格式

```json
{
  "layer": "L4",
  "source": "prisma/schema.prisma",
  "orm": "prisma",
  "tables": [
    {
      "name": "users",
      "raw_name": "User",
      "file": "prisma/schema.prisma",
      "line": 12,
      "columns": [
        { "name": "id", "type": "int", "nullable": false, "primary_key": true, "system_field": true },
        { "name": "user_name", "type": "varchar", "nullable": false, "primary_key": false, "system_field": false },
        { "name": "email", "type": "varchar", "nullable": false, "primary_key": false, "system_field": false },
        { "name": "dept_id", "type": "int", "nullable": true, "primary_key": false, "system_field": false },
        { "name": "created_at", "type": "timestamp", "nullable": false, "primary_key": false, "system_field": true },
        { "name": "updated_at", "type": "timestamp", "nullable": false, "primary_key": false, "system_field": true }
      ]
    }
  ]
}
```

---

### L3: 实体层提取

> 实体层是 ORM 映射后的代码表示。字段名可能与数据库列名不同（驼峰 vs 蛇形）。
> L3 的核心价值：记录 **属性名 → 列名** 的映射关系，供跨层比对使用。

#### Java Entity

```bash
# 定位 Entity 类（同 L4 JPA，但此处关注属性名而非列名）
grep -rln "@Entity" --include="*.java" src/ 2>/dev/null

# 提取类的所有字段声明
grep -n "private\s\+\w\+\s\+\w\+\s*;" --include="*.java" -r src/main/java/**/entity/ 2>/dev/null
```

提取规则：

| 代码模式 | 提取逻辑 |
|---|---|
| `private String userName;` | 属性名 = `userName` |
| `@Column(name = "user_name")` + `private String userName;` | 属性名 = `userName`，列映射 = `user_name` |
| 无 `@Column` 注解 | 列映射 = 按 JPA 命名策略推断（`ImplicitNamingStrategy`） |
| `@Transient private String fullName;` | **跳过** — 非持久化 |
| `@JsonIgnore private String password;` | 属性存在但标记为"不序列化"，L2 比对时需注意 |

#### Go Struct

```bash
# 提取 struct 字段及 tag
grep -A 1 "type\s\+\w\+\s\+struct" --include="*.go" -r internal/ pkg/ models/ 2>/dev/null

# 提取所有带 json/gorm tag 的字段
grep -n 'json:"\|gorm:"' --include="*.go" -r internal/ pkg/ models/ 2>/dev/null
```

提取规则：

| 代码模式 | 提取逻辑 |
|---|---|
| `` UserName string `json:"user_name" gorm:"column:user_name"` `` | 属性名 = `UserName`，JSON 名 = `user_name`，列名 = `user_name` |
| `` json:"-" `` | **JSON 层跳过**，但 gorm 层可能仍然存在 |
| `` json:"user_name,omitempty" `` | JSON 名 = `user_name`，omitempty 仅影响空值序列化 |
| `` gorm:"-" `` | 非数据库字段，L4 比对时排除 |
| 嵌入 `gorm.Model` | 展开为 `ID`, `CreatedAt`, `UpdatedAt`, `DeletedAt` |

#### TypeScript / Node Entity

```bash
# TypeORM Entity（属性视角）
grep -n "^\s*\w\+\s*[!?]*:" --include="*.ts" -r server/src/**/entities/ 2>/dev/null

# Prisma 生成的 Client 类型（自动生成，只读参考）
find . -path "*/node_modules/.prisma/client/index.d.ts" 2>/dev/null

# Sequelize Model 属性
grep -n "declare\s\+\w\+\s*[!?]*:" --include="*.ts" -r server/src/**/models/ 2>/dev/null
```

提取规则：

| 代码模式 | 提取逻辑 |
|---|---|
| `userName!: string;` | 属性名 = `userName` |
| `@Column({ name: "user_name" })` + `userName!: string;` | 属性名 = `userName`，列映射 = `user_name` |
| Prisma 生成的 `type User = { user_name: string }` | 属性名 = `user_name`（Prisma 客户端保持 schema 中的字段名） |

#### Python Model (Django / SQLAlchemy / Tortoise)

```bash
# Django Model 属性
grep -n "^\s*\w\+\s*=\s*models\.\w*Field" --include="*.py" -r */models.py 2>/dev/null

# SQLAlchemy Model 属性
grep -n "Column(\|mapped_column(" --include="*.py" -r app/models/ 2>/dev/null

# Tortoise ORM
grep -n "fields\.\w*Field" --include="*.py" -r app/models/ 2>/dev/null
```

提取规则：

| 代码模式 | 提取逻辑 |
|---|---|
| `user_name = models.CharField(...)` | 属性名 = `user_name` |
| `user_name = Column(String, name="uname")` | 属性名 = `user_name`，列映射 = `uname` |
| `dept = models.ForeignKey(...)` | 属性名 = `dept`，实际列 = `dept_id` |
| `class Meta: db_table = 't_user'` | 表映射用，非字段 |

#### L3 输出格式

```json
{
  "layer": "L3",
  "source": "server/src/entities/user.entity.ts",
  "entities": [
    {
      "name": "User",
      "table_mapping": "users",
      "file": "server/src/entities/user.entity.ts",
      "line": 5,
      "fields": [
        {
          "name": "id",
          "type": "number",
          "column_mapping": "id",
          "system_field": true,
          "serialization_ignored": false
        },
        {
          "name": "userName",
          "type": "string",
          "column_mapping": "user_name",
          "system_field": false,
          "serialization_ignored": false
        },
        {
          "name": "email",
          "type": "string",
          "column_mapping": "email",
          "system_field": false,
          "serialization_ignored": false
        },
        {
          "name": "password",
          "type": "string",
          "column_mapping": "password",
          "system_field": false,
          "serialization_ignored": true,
          "ignore_annotation": "@JsonIgnore"
        },
        {
          "name": "createdAt",
          "type": "Date",
          "column_mapping": "created_at",
          "system_field": true,
          "serialization_ignored": false
        }
      ]
    }
  ]
}
```

---

### L2: API 接口层提取

> API 层定义了前后端之间传输的字段。DTO/VO 中的字段名可能与 Entity 不同。
> 按置信度从高到低，共 4 种提取策略。Agent 命中第一种即可，无需继续。

#### 策略 1（最高置信度）：OpenAPI / Swagger 文档

```bash
# 定位 OpenAPI 文档
find . -name "swagger.json" -o -name "openapi.json" -o -name "swagger.yaml" \
  -o -name "openapi.yaml" -o -name "api-docs.json" 2>/dev/null

# 如果是运行时生成的 Swagger（NestJS / Spring Boot），查找配置
grep -rn "SwaggerModule\|@EnableSwagger2\|springdoc\|springfox" \
  --include="*.ts" --include="*.java" --include="*.yaml" -r . 2>/dev/null
```

提取规则：
- `paths.{endpoint}.{method}.requestBody.content.application/json.schema` → 请求字段
- `paths.{endpoint}.{method}.responses.200.content.application/json.schema` → 响应字段
- `$ref` 引用递归解析至 `components.schemas` / `definitions`
- `readOnly: true` 的字段只在响应中出现
- `writeOnly: true` 的字段只在请求中出现

#### 策略 2（高置信度）：DTO / VO 类定义

```bash
# Java DTO / VO
find . -name "*DTO.java" -o -name "*Dto.java" -o -name "*VO.java" \
  -o -name "*Vo.java" -o -name "*Request.java" -o -name "*Response.java" 2>/dev/null

# TypeScript DTO（NestJS 风格）
find . -name "*.dto.ts" -o -name "*.vo.ts" -o -name "*.request.ts" \
  -o -name "*.response.ts" 2>/dev/null | grep -v node_modules

# Python Pydantic Schema / DRF Serializer
grep -rln "BaseModel\|Serializer" --include="*.py" -r app/ */schemas/ */serializers/ 2>/dev/null
```

DTO 字段提取规则（Java）：

| 注解 | 提取逻辑 |
|---|---|
| `@JsonProperty("user_name")` | API 字段名 = `user_name`（覆盖属性名） |
| `@ApiModelProperty(hidden = true)` | **跳过** — Swagger 中隐藏 |
| `@ApiModelProperty(value = "用户名")` | 提取为字段描述 |
| `@NotNull` / `@NotBlank` | 标记为必填字段 |
| `@JsonIgnore` | **跳过** — 不参与序列化 |
| `private String userName;`（无注解） | API 字段名 = `userName` |

DTO 字段提取规则（TypeScript / NestJS）：

| 装饰器 | 提取逻辑 |
|---|---|
| `@ApiProperty()` | 标记为 Swagger 可见字段 |
| `@ApiHideProperty()` | **跳过** |
| `@Exclude()` | **跳过** — class-transformer 排除 |
| `@Expose({ name: 'user_name' })` | API 字段名 = `user_name` |
| `@IsString()` / `@IsNotEmpty()` | 标记类型和必填 |
| `@Transform(...)` | 字段存在但值可能变换，需标注 |

DTO 字段提取规则（Python Pydantic）：

| 语法 | 提取逻辑 |
|---|---|
| `user_name: str` | API 字段名 = `user_name` |
| `user_name: str = Field(alias="userName")` | API 字段名 = `userName`（alias 优先） |
| `model_config = ConfigDict(populate_by_name=True)` | 允许用属性名或 alias |
| `@field_serializer` | 字段存在但输出可能变换 |

DTO 字段提取规则（Django REST Framework Serializer）：

| 语法 | 提取逻辑 |
|---|---|
| `user_name = serializers.CharField()` | API 字段名 = `user_name` |
| `user_name = serializers.CharField(source="profile.name")` | API 字段名 = `user_name`，映射到嵌套属性 |
| `class Meta: fields = [...]` | 白名单，只有列出的字段暴露到 API |
| `class Meta: exclude = [...]` | 黑名单，排除的字段不暴露 |
| `read_only_fields = [...]` | 只在响应中出现 |

#### 策略 3（中等置信度）：前端 API 定义文件

```bash
# 前端 TypeScript 接口定义（通常与 API 调用放在一起）
find src/api/ src/services/ -name "*.ts" -o -name "*.js" 2>/dev/null | grep -v node_modules

# 提取 interface / type 定义
grep -n "interface\s\+\w\+\|type\s\+\w\+\s*=" --include="*.ts" \
  -r src/api/ src/services/ src/types/ 2>/dev/null
```

提取规则：

| 代码模式 | 提取逻辑 |
|---|---|
| `interface UserDTO { userName: string; email: string; }` | 字段 = `userName`, `email` |
| `type CreateUserReq = { user_name: string; }` | 字段 = `user_name` |
| `interface UserVO extends BaseVO { ... }` | 递归合并父接口字段 |
| `Partial<User>` | 所有字段变为可选 |
| `Pick<User, 'id' \| 'name'>` | 只取指定字段 |
| `Omit<User, 'password'>` | 排除指定字段 |

#### 策略 4（低置信度兜底）：路由 handler 推断

> 仅当策略 1-3 均无结果时使用。从 controller / route handler 代码推断字段。

```bash
# NestJS controller
grep -n "@Body\|@Query\|@Param\|@Res\|return\s" --include="*.ts" \
  -r server/src/**/controllers/ server/src/**/*.controller.ts 2>/dev/null

# Express handler
grep -n "req\.body\.\|req\.query\.\|req\.params\.\|res\.json\|res\.send" \
  --include="*.ts" --include="*.js" -r server/src/ routes/ 2>/dev/null

# FastAPI (Python)
grep -n "async def\|def\s\+\w\+(.*Request\|.*Body\|.*Query" \
  --include="*.py" -r app/api/ app/routers/ 2>/dev/null

# Gin / Echo (Go)
grep -n 'c\.Bind\|c\.ShouldBind\|c\.JSON\|c\.Query(' --include="*.go" \
  -r internal/handler/ api/ 2>/dev/null

# Spring MVC (Java)
grep -n "@RequestBody\|@RequestParam\|ResponseEntity\|return\s" \
  --include="*.java" -r src/main/java/**/controller/ 2>/dev/null
```

推断规则：

| 代码模式 | 推断逻辑 | 置信度 |
|---|---|---|
| `@Body() dto: CreateUserDto` | 请求字段 = `CreateUserDto` 的属性 | 中 — 需要找到 DTO 定义 |
| `req.body.userName` | 请求包含 `userName` 字段 | 低 — 可能不完整 |
| `const { name, email } = req.body` | 请求包含 `name`, `email` | 低 — 解构可能不完整 |
| `res.json({ id, userName, email })` | 响应包含 `id`, `userName`, `email` | 低 — 可能是部分字段 |
| `c.ShouldBindJSON(&req)` | 请求字段 = `req` 结构体的 json tag | 中 — 需要找到结构体 |

#### Dart 模型类（Dart L2）

> Flutter 客户端的 API 层字段通过 Dart 模型类（`fromJson`/`toJson`）定义。

```bash
# json_serializable 模型
grep -rln "JsonSerializable\|@JsonKey" --include="*.dart" lib/ 2>/dev/null

# freezed 模型
grep -rln "@freezed\|@Freezed" --include="*.dart" lib/ 2>/dev/null

# 手动 fromJson
grep -rln "fromJson\|toJson" --include="*.dart" lib/ 2>/dev/null

# Retrofit 定义
grep -rn "@GET\|@POST\|@PUT\|@DELETE" --include="*.dart" lib/ 2>/dev/null
```

提取规则：

| 序列化方式 | 代码模式 | 提取逻辑 |
|-----------|---------|---------|
| json_serializable | `@JsonKey(name: 'user_name') String userName` | API 字段名 = `user_name`（`@JsonKey` 优先） |
| json_serializable | `String userName` (无 @JsonKey) | API 字段名 = `userName`（属性名即字段名） |
| freezed | `@FreezedUnionValue('userType') String type` | 联合类型值 = `userType` |
| freezed | `required String userName` | API 字段名 = `userName` |
| 手动 fromJson | `userName = json['user_name'] as String` | API 字段名 = `user_name` |
| 手动 fromJson | `email = json['email'] as String?` | API 字段名 = `email`，nullable |
| Retrofit | `@GET('/api/users') Future<List<User>> getUsers()` | 关联 `User` 模型的字段 |

Dart L2 输出格式与通用 L2 格式一致，`strategy` 字段标记为 `"dart_model"`。

#### L2 输出格式

```json
{
  "layer": "L2",
  "source": "openapi.json",
  "strategy": "openapi",
  "endpoints": [
    {
      "path": "/api/users",
      "method": "POST",
      "handler_file": "server/src/modules/user/user.controller.ts",
      "handler_line": 25,
      "request_fields": [
        { "name": "userName", "type": "string", "required": true, "source": "body" },
        { "name": "email", "type": "string", "required": true, "source": "body" },
        { "name": "deptId", "type": "number", "required": false, "source": "body" }
      ],
      "response_fields": [
        { "name": "id", "type": "number", "system_field": true },
        { "name": "userName", "type": "string", "system_field": false },
        { "name": "email", "type": "string", "system_field": false },
        { "name": "createdAt", "type": "string", "system_field": true }
      ]
    },
    {
      "path": "/api/users",
      "method": "GET",
      "handler_file": "server/src/modules/user/user.controller.ts",
      "handler_line": 40,
      "request_fields": [
        { "name": "page", "type": "number", "required": false, "source": "query" },
        { "name": "pageSize", "type": "number", "required": false, "source": "query" },
        { "name": "keyword", "type": "string", "required": false, "source": "query" }
      ],
      "response_fields": [
        { "name": "list", "type": "array", "system_field": false, "items_ref": "UserVO" },
        { "name": "total", "type": "number", "system_field": false },
        { "name": "page", "type": "number", "system_field": false },
        { "name": "pageSize", "type": "number", "system_field": false }
      ]
    }
  ]
}
```

---

### L1: UI 显示层提取

> UI 层是用户可见的字段呈现。提取目标：表格列名、表单字段名、模板中绑定的数据字段。
> 按置信度分两级：高置信度（结构化配置）和中置信度（模板推断）。

#### 高置信度：表格列配置

```bash
# Ant Design / Ant Design Vue — columns 中的 dataIndex
grep -n "dataIndex" --include="*.tsx" --include="*.vue" --include="*.jsx" \
  -r src/pages/ src/views/ 2>/dev/null

# Element Plus / Element UI — prop
grep -n "el-table-column.*prop\|<el-table-column" --include="*.vue" \
  -r src/views/ 2>/dev/null

# 通用 columns 数组（React Table, AG Grid, etc.）
grep -n "columns\s*=\s*\[\|columns:\s*\[" --include="*.tsx" --include="*.ts" --include="*.vue" \
  -r src/pages/ src/views/ 2>/dev/null
```

提取规则：

| 框架 | 代码模式 | 提取字段名 | 提取标签 |
|---|---|---|---|
| Ant Design | `{ title: '用户名', dataIndex: 'userName' }` | `userName` | `用户名` |
| Ant Design | `{ title: '用户名', dataIndex: ['profile', 'name'] }` | `profile.name` | `用户名` |
| Element Plus | `<el-table-column prop="userName" label="用户名"/>` | `userName` | `用户名` |
| React Table | `{ Header: 'Name', accessor: 'userName' }` | `userName` | `Name` |
| AG Grid | `{ headerName: '用户名', field: 'userName' }` | `userName` | `用户名` |
| Naive UI | `{ title: '用户名', key: 'userName' }` | `userName` | `用户名` |

#### 高置信度：表单字段配置

```bash
# Ant Design Form — name 属性
grep -n "Form.Item.*name=\|<a-form-item.*name=" --include="*.tsx" --include="*.vue" --include="*.jsx" \
  -r src/pages/ src/views/ 2>/dev/null

# Element Plus Form — prop 属性
grep -n "el-form-item.*prop=" --include="*.vue" \
  -r src/views/ 2>/dev/null

# React Hook Form — register
grep -n "register(\|useForm\|Controller.*name=" --include="*.tsx" --include="*.jsx" \
  -r src/pages/ src/components/ 2>/dev/null

# Formik — name / Field
grep -n "<Field.*name=\|<FastField.*name=" --include="*.tsx" --include="*.jsx" \
  -r src/pages/ src/components/ 2>/dev/null
```

提取规则：

| 框架 | 代码模式 | 提取字段名 | 提取标签 |
|---|---|---|---|
| Ant Design | `<Form.Item name="userName" label="用户名">` | `userName` | `用户名` |
| Ant Design | `<Form.Item name={['profile', 'name']}>` | `profile.name` | — |
| Element Plus | `<el-form-item prop="userName" label="用户名">` | `userName` | `用户名` |
| React Hook Form | `register("userName")` | `userName` | — |
| React Hook Form | `<Controller name="userName" />` | `userName` | — |
| Formik | `<Field name="userName" />` | `userName` | — |
| VeeValidate | `<Field name="userName" />` | `userName` | — |

#### 中置信度：模板数据绑定

```bash
# Vue 模板绑定
grep -n 'v-model="\|{{ \|:prop="\|:value="' --include="*.vue" \
  -r src/views/ src/pages/ src/components/ 2>/dev/null

# React JSX 数据渲染
grep -n '{data\.\|{record\.\|{item\.\|{row\.\|props\.' --include="*.tsx" --include="*.jsx" \
  -r src/pages/ src/components/ 2>/dev/null

# Angular 模板绑定
grep -n '{{ \|\[value\]="\|\[ngModel\]="' --include="*.html" --include="*.component.ts" \
  -r src/app/ 2>/dev/null
```

提取规则：

| 框架 | 代码模式 | 提取字段名 | 置信度 |
|---|---|---|---|
| Vue | `v-model="form.userName"` | `userName` | 高 — 表单绑定 |
| Vue | `{{ item.userName }}` | `userName` | 中 — 模板插值 |
| Vue | `:label="item.userName"` | `userName` | 中 — 属性绑定 |
| React | `{data.userName}` | `userName` | 中 — JSX 表达式 |
| React | `{record.userName}` | `userName` | 中 — 表格行渲染 |
| Angular | `{{ user.userName }}` | `userName` | 中 — 模板插值 |
| Angular | `[value]="user.userName"` | `userName` | 中 — 属性绑定 |

#### 搜索/过滤字段

```bash
# 搜索表单字段（通常是 GET 请求的 query 参数在 UI 上的体现）
grep -n "搜索\|筛选\|过滤\|search\|filter\|keyword" --include="*.tsx" --include="*.vue" \
  -r src/pages/ src/views/ 2>/dev/null
```

> 搜索字段在 L2 中对应 `source: "query"` 的请求参数。跨层比对时需要匹配。

#### Flutter Widget（Dart L1）

> 当项目包含 Flutter 客户端时，L1 提取需要覆盖 Dart Widget 文件。

```bash
# DataTable 列字段
grep -rn "DataColumn\|DataCell" --include="*.dart" lib/ 2>/dev/null

# Form 字段绑定
grep -rn "TextFormField\|TextField\|DropdownButton\|DropdownButtonFormField" \
  --include="*.dart" lib/ 2>/dev/null

# 文本显示绑定
grep -rn "Text(\|TextSpan(" --include="*.dart" lib/ 2>/dev/null

# ListView / GridView 项
grep -rn "ListTile\|GridTile\|Card(" --include="*.dart" lib/ 2>/dev/null

# JSON 映射字段
grep -rn "json\['" --include="*.dart" lib/ 2>/dev/null
```

提取规则：

| 组件 | 代码模式 | 提取字段名 | 提取标签 |
|------|---------|-----------|---------|
| DataTable | `DataColumn(label: Text('用户名'))` | 从对应 `DataCell` 取字段绑定 | `用户名` |
| TextFormField | `TextFormField(controller: _nameCtrl)` | 追踪 controller → 变量名推断字段 | 取 `decoration.labelText` |
| Text | `Text(model.userName)` | `userName` | — |
| Text | `Text(item['user_name'])` | `user_name` | — |
| ListTile | `ListTile(title: Text(item.name), subtitle: Text(item.email))` | `name`, `email` | — |

#### L1 输出格式

```json
{
  "layer": "L1",
  "pages": [
    {
      "page": "用户管理",
      "file": "src/pages/user/UserList.tsx",
      "components": [
        {
          "type": "table",
          "component": "ProTable",
          "line": 45,
          "fields": [
            { "name": "userName", "context": "column", "label": "用户名", "line": 52 },
            { "name": "email", "context": "column", "label": "邮箱", "line": 53 },
            { "name": "deptName", "context": "column", "label": "部门", "line": 54 },
            { "name": "status", "context": "column", "label": "状态", "line": 55 },
            { "name": "createdAt", "context": "column", "label": "创建时间", "line": 56 }
          ]
        },
        {
          "type": "search",
          "component": "SearchForm",
          "line": 20,
          "fields": [
            { "name": "keyword", "context": "search", "label": "关键词", "line": 22 },
            { "name": "status", "context": "search", "label": "状态", "line": 25 },
            { "name": "deptId", "context": "search", "label": "部门", "line": 28 }
          ]
        }
      ]
    },
    {
      "page": "用户新增/编辑",
      "file": "src/pages/user/UserForm.tsx",
      "components": [
        {
          "type": "form",
          "component": "ProForm",
          "line": 30,
          "fields": [
            { "name": "userName", "context": "form", "label": "用户名", "line": 35 },
            { "name": "email", "context": "form", "label": "邮箱", "line": 40 },
            { "name": "phone", "context": "form", "label": "手机号", "line": 45 },
            { "name": "deptId", "context": "form", "label": "所属部门", "line": 50 },
            { "name": "roleIds", "context": "form", "label": "角色", "line": 55 }
          ]
        }
      ]
    }
  ]
}
```

---

### 通用字段过滤规则

> 系统字段在各层之间几乎必然存在命名差异（如 L4 `created_at` → L3 `createdAt` → L2 响应中存在但请求中不存在 → L1 只在表格中显示）。
> 这些差异是**合理的设计**，不应报告为问题。

#### 系统字段清单

以下字段应在提取时标记为 `system_field: true`，跨层比对时**仅做标注，不报告为缺失**：

| 类别 | 字段名变体 | 说明 |
|---|---|---|
| 主键 | `id`, `_id`, `ID`, `pk` | 主键通常自动生成，前端可能不显示 |
| 创建时间 | `createdAt`, `created_at`, `gmt_create`, `createTime`, `create_time`, `ctime` | 各框架命名习惯不同 |
| 更新时间 | `updatedAt`, `updated_at`, `gmt_modified`, `updateTime`, `update_time`, `mtime` | 同上 |
| 软删除 | `deletedAt`, `deleted_at`, `is_deleted`, `isDeleted`, `del_flag` | 通常不在 UI 层暴露 |
| 创建人 | `createdBy`, `created_by`, `creator`, `create_by` | 审计字段 |
| 更新人 | `updatedBy`, `updated_by`, `modifier`, `update_by` | 审计字段 |
| 乐观锁 | `version`, `revision`, `opt_lock_version` | 并发控制，前端不感知 |
| 多租户 | `tenantId`, `tenant_id`, `org_id` | 由框架自动注入，不在 UI 上出现 |

#### 过滤逻辑

```
对每个提取到的字段 f:
  1. 将 f 标准化（驼峰转蛇形、去前缀 is_/has_、统一小写）
  2. 与系统字段清单匹配
  3. 若匹配：
     - 标记 system_field = true
     - 跨层比对时：
       - L4 有 / L1 无 → 正常（系统字段通常不在 UI 显示）
       - L4 有 / L2 请求无 → 正常（系统字段通常自动填充）
       - L4 有 / L2 响应无 → 轻微提示（某些场景需要返回创建时间等）
  4. 若不匹配：
     - system_field = false
     - 跨层比对时正常报告缺失
```

#### 为什么需要过滤

系统字段在不同层有合理的存在差异：

| 层 | `id` | `created_at` | `password` | `deleted_at` | `tenant_id` |
|---|---|---|---|---|---|
| L4 数据库 | 存在 | 存在 | 存在 | 存在 | 存在 |
| L3 实体 | 存在 | 存在 | 存在（@JsonIgnore） | 存在 | 存在 |
| L2 响应 | 存在 | 通常存在 | **不应存在** | 不存在 | 不存在 |
| L2 请求 | 不存在（自动生成） | 不存在（自动填充） | 存在（注册时） | 不存在 | 不存在（框架注入） |
| L1 显示 | 通常隐藏 | 通常显示 | 不存在 | 不存在 | 不存在 |

如果不做过滤，每个模块都会报出大量 "L4 有 `tenant_id` 但 L1 没有" 这类误报，淹没真正有价值的发现。

> **注意**：`password` 不在系统字段清单中。如果 `password` 出现在 L2 响应中，应该报告为**安全问题**而非正常差异。


### 来源文件：`docs/fieldcheck/matching.md`

## 智能匹配算法参考

> 本文档定义了跨层字段名比对时使用的智能匹配算法。
> 核心目标：区分命名风格差异（合法）和真正的不一致（问题）。

---

### 匹配流程总览

```
输入：Layer(n) 字段集 A, Layer(n+1) 字段集 B

          ┌─────────────────────┐
          │  Step 1: 精确匹配    │   "userName" === "userName"
          │  exact string match  │   → 直接配对，从候选池移除
          └──────────┬──────────┘
                     ↓ 未匹配字段
          ┌─────────────────────┐
          │  Step 2: 标准化匹配  │   "userName" ≈ "user_name" ≈ "UserName"
          │  tokenize → lower   │   → 词根序列相同 → 风格等价，配对
          │  → compare roots    │
          └──────────┬──────────┘
                     ↓ 未匹配字段
          ┌─────────────────────┐
          │  Step 3: 近似匹配    │   "userName" ~ "userNmae" (dist=2)
          │  edit distance ≤ T  │   → 报 TYPO 问题
          └──────────┬──────────┘
                     ↓ 未匹配字段
          ┌─────────────────────┐
          │  Step 4: 语义匹配    │   "nickname" ~ "displayName"
          │  same module,       │   → 同模块语义相似，报 SEMANTIC
          │  semantic similarity │   → 标记 needs_confirmation
          └──────────┬──────────┘
                     ↓ 仍未匹配字段
          ┌─────────────────────┐
          │  Step 5: 分类       │   A 有 B 没有 → GHOST
          │  Ghost / Stale / Gap│   B 有 A 没有 → STALE
          │                     │   L3→L2 断裂  → GAP
          └─────────────────────┘

输出：field-mapping.json（含匹配对 + 问题列表）
```

---

### Step 1: 精确匹配

最简单的一步：逐字符比较两层字段名。

```
算法：
  for field_a in layer_n_fields:
    if field_a.name in layer_n1_fields:
      field_b = layer_n1_fields[field_a.name]
      mark_matched(field_a, field_b)
      remove both from candidate pools
```

- 大小写敏感：`userName` !== `UserName`（精确匹配要求完全一致）
- 匹配成功的字段从候选池移除，不再进入后续步骤
- 预期命中率：同层同风格的字段（如后端内部 L3↔L4），精确匹配率通常 > 60%

---

### Step 2: 标准化匹配（命名风格等价）

将字段名分词、统一小写后比较词根序列。这一步的目标是消除合法的命名风格差异。

#### 分词规则

| 输入示例 | 分词结果 | 规则 |
|---------|---------|------|
| `userName` | `[user, name]` | camelCase：在大写字母前切分 |
| `UserName` | `[user, name]` | PascalCase：在大写字母前切分 |
| `user_name` | `[user, name]` | snake_case：按下划线切分 |
| `user-name` | `[user, name]` | kebab-case：按连字符切分 |
| `HTMLParser` | `[html, parser]` | 连续大写字母视为一个词（acronym） |
| `getXMLData` | `[get, xml, data]` | 混合：先处理连续大写，再处理 camel |
| `user_name_v2` | `[user, name, v2]` | 保留版本后缀作为独立 token |
| `__user_name__` | `[user, name]` | 去除前后 underscore padding |
| `_id` | `[id]` | 单个前导下划线 + 词 → 去除下划线 |

#### 分词后标准化

```
1. 分词（按上述规则）
2. 全部转小写
3. 应用缩写等价表展开
4. 比较词根序列是否一致

示例：
  "userName"    → [user, name]     → [user, name]
  "user_name"   → [user, name]     → [user, name]
  "UserName"    → [user, name]     → [user, name]
  结果：三者等价 ✅
```

#### 特殊处理：布尔前缀

布尔字段常加 `is` / `has` / `can` / `should` 前缀，不同层可能有/没有前缀：

```
"isActive"   → 尝试两种匹配：
  1. [is, active]  → 完整匹配
  2. [active]      → 去前缀匹配

"hasChildren" → 尝试两种匹配：
  1. [has, children] → 完整匹配
  2. [children]      → 去前缀匹配

匹配成功条件：任一方式与对端字段词根序列相同
```

#### 特殊处理：ID 后缀

外键字段常加实体前缀或 `_id` / `Id` 后缀：

```
"userId"    → 尝试两种匹配：
  1. [user, id]  → 完整匹配
  2. [id]        → 去前缀匹配（在同 module 下）

"user_id"   → 同上

"id" (在 User 模块中) → 也尝试匹配 "userId"
```

#### 特殊处理：中文标签

中文标签（如 `用户名`）不参与分词匹配，仅用于报告展示。

```
L1 字段可能有 label: "用户名", name: "userName"
匹配时只使用 name 属性
label 只在报告中辅助人工确认
```

#### 常见缩写等价表

以下缩写在匹配时视为等价（双向）：

| 缩写 | 完整形式 | 使用场景 |
|------|---------|---------|
| `desc` | `description` | 描述字段 |
| `addr` | `address` | 地址字段 |
| `tel` | `telephone` | 电话字段 |
| `phone` | `telephone` | 电话字段 |
| `img` | `image` | 图片字段 |
| `qty` | `quantity` | 数量字段 |
| `amt` | `amount` | 金额字段 |
| `pwd` | `password` | 密码字段 |
| `no` | `number` | 编号字段 |
| `num` | `number` | 数字/编号字段 |
| `cat` | `category` | 分类字段 |
| `cate` | `category` | 分类字段 |
| `org` | `organization` | 组织字段 |
| `dept` | `department` | 部门字段 |
| `config` | `configuration` | 配置字段 |
| `conf` | `configuration` | 配置字段 |
| `info` | `information` | 信息字段 |
| `msg` | `message` | 消息字段 |
| `stat` | `statistics` | 统计字段 |
| `stats` | `statistics` | 统计字段 |
| `auth` | `authorization` | 授权字段 |
| `authn` | `authentication` | 认证字段 |
| `params` | `parameters` | 参数字段 |
| `spec` | `specification` | 规格字段 |
| `env` | `environment` | 环境字段 |
| `repo` | `repository` | 仓库字段 |
| `prev` | `previous` | 前一个 |
| `cur` / `curr` | `current` | 当前 |
| `src` | `source` | 来源字段 |
| `dst` / `dest` | `destination` | 目标字段 |
| `ref` | `reference` | 引用字段 |
| `tmp` / `temp` | `temporary` | 临时字段 |
| `btn` | `button` | 按钮字段 |
| `ctx` | `context` | 上下文字段 |
| `seq` | `sequence` | 序列字段 |
| `idx` | `index` | 索引字段 |
| `val` | `value` | 值字段 |
| `len` | `length` | 长度字段 |
| `max` | `maximum` | 最大值 |
| `min` | `minimum` | 最小值 |
| `avg` | `average` | 平均值 |
| `cnt` | `count` | 计数 |

> **扩展方式：** 项目根目录的 `.deadhunt/field-aliases.json` 可追加项目专属缩写映射。

---

### Step 3: 近似匹配（Typo 检测）

对经过 Step 2 标准化后仍未匹配的字段，计算编辑距离（Levenshtein distance），检测拼写错误。

#### 计算方式

```
1. 对 A 中每个未匹配字段的标准化词根序列 tokensA
2. 与 B 中每个未匹配字段的标准化词根序列 tokensB
3. 将词根序列拼接为字符串（用空格连接）
4. 计算 Levenshtein 编辑距离
5. 与阈值比较
```

#### 阈值表

| 标准化后字符串长度 | 最大允许编辑距离 | 说明 | 示例 |
|------------------|----------------|------|------|
| ≤ 3 字符 | 0 | 短字段太模糊，不做 typo 检测 | `id`, `no`, `url` — 不检测 |
| 4 ~ 8 字符 | 1 | 允许 1 个字符的差异 | `name` vs `nme` (dist=1) → TYPO |
| 9 ~ 15 字符 | 2 | 允许 2 个字符的差异 | `description` vs `descrption` (dist=1) → TYPO |
| > 15 字符 | 3 | 长字段允许更多容错 | `organizationName` vs `oragnizationName` (dist=2) → TYPO |

#### 排除规则

以下情况即使编辑距离在阈值内也**不报 TYPO**：

1. **缩写表已覆盖**：如果两个字段的差异来自缩写等价表（`desc` vs `description`），已在 Step 2 处理
2. **ORM 显式映射**：Entity 字段有 `@Column(name="xxx")` 显式指定列名时，列名与字段名的差异是刻意的
3. **JSON tag 显式映射**：Go struct 有 `` `json:"xxx"` `` tag 时同理
4. **前缀/后缀差异**：如 `user` vs `userId`，属于合法的 FK 命名模式，不是 typo
5. **数字后缀差异**：如 `address1` vs `address2`，是不同字段而非拼写错误

#### 输出示例

```json
{
  "type": "TYPO",
  "severity": "critical",
  "module": "user",
  "layer_pair": "L1↔L2",
  "field_a": { "name": "userNmae", "layer": "L1", "file": "src/pages/user/list.tsx:45" },
  "field_b": { "name": "userName", "layer": "L2", "file": "src/api/types/user.ts:12" },
  "edit_distance": 2,
  "suggestion": "L1 的 'userNmae' 疑似拼写错误，应为 'userName'"
}
```

---

### Step 4: 语义匹配

对同一模块中仍未匹配的字段，尝试基于语义相似性建立关联。

#### 匹配条件

必须同时满足：
1. **同模块**：两个字段属于同一业务模块（如都在 user 模块下）
2. **语义相关**：字段名属于以下语义关联模式之一

#### 语义关联模式

| 模式 | 说明 | 示例 |
|------|------|------|
| **同义词** (Synonyms) | 不同词但指代同一数据 | `nickname` / `displayName` / `screenName` |
| **不同角度** (Different Angle) | 同一数据的不同业务视角 | `price` / `unitPrice` / `salePrice` |
| **不同粒度** (Different Scope) | 范围不同但指向同类数据 | `address` / `detailAddress` / `fullAddress` |
| **包含关系** (Containment) | 一个字段名包含另一个 | `name` / `userName` / `realName` |
| **业务等价** (Business Equivalent) | 业务上常互相替代 | `status` / `state` / `isActive` |

#### 常见语义等价组

```
# 用户相关
[nickname, displayName, screenName, showName, alias]
[avatar, photo, profileImage, headImg, portrait]
[mobile, phone, cellphone, tel, phoneNumber]
[email, mail, emailAddress]
[realName, trueName, legalName, fullName]

# 时间相关
[createdAt, createTime, gmtCreate, created, createDate]
[updatedAt, updateTime, gmtModified, modified, modifyDate, lastModified]
[deletedAt, deleteTime, gmtDelete]
[startTime, beginTime, startDate, beginDate]
[endTime, finishTime, endDate, deadline, dueDate]

# 状态相关
[status, state, isActive, enabled, isEnabled]
[deleted, isDeleted, removed, isRemoved]
[visible, isVisible, show, isShow, display]

# 描述相关
[description, desc, remark, note, memo, comment, summary]
[title, name, label, caption, heading, subject]

# 金额相关
[price, amount, fee, cost, charge, rate]
[totalPrice, totalAmount, grandTotal, totalFee]
[discount, discountAmount, couponAmount, reduction]
```

#### 语义匹配输出

所有语义匹配结果均标记 `needs_confirmation: true`，要求人工复核：

```json
{
  "type": "SEMANTIC",
  "severity": "warning",
  "module": "user",
  "layer_pair": "L1↔L2",
  "field_a": { "name": "nickname", "layer": "L1", "file": "src/pages/user/profile.tsx:23" },
  "field_b": { "name": "displayName", "layer": "L2", "file": "src/api/types/user.ts:8" },
  "pattern": "synonym",
  "confidence": "medium",
  "needs_confirmation": true,
  "question": "前端使用 'nickname'，API 返回 'displayName'，这两个字段是否指代同一数据？"
}
```

---

### 匹配结果分类

经过 4 步匹配流程后，每个字段归入以下分类：

| 匹配结果 | 问题类型 | 严重度 | 说明 | 处置 |
|---------|---------|--------|------|------|
| 精确匹配 | — | Pass | 字符串完全一致 | 无需处理 |
| 风格等价 | — | Pass | 词根相同，仅风格不同 | 无需处理 |
| 编辑距离命中 | TYPO | Critical | 疑似拼写错误 | 需修复 |
| 语义相似 | SEMANTIC | Warning | 可能指代同一数据但名字不同 | 需人工确认 |
| L(n) 有，L(n+1) 没有 | GHOST | Critical | 幽灵字段：引用了不存在的数据 | 需修复 |
| L(n+1) 有，L(n) 未使用 | STALE | Warning | 废弃字段：传输了未使用的数据 | 建议清理 |
| L3 有但 L2 未暴露 | GAP | Critical | 映射断裂：Entity 有但 DTO 未包含 | 需修复 |
| L4 有但 L3 未映射 | GAP | Critical | 映射断裂：DB 列无对应 Entity 字段 | 需修复 |

> **优先级排序**：GHOST = TYPO = GAP (Critical) > SEMANTIC = STALE (Warning)。
> Critical 问题通常意味着运行时会出现 `undefined` 或数据丢失。

---

### 跨层比对方向

每对相邻层做双向检查：

| 层级对 | 正向检查（Forward） | 反向检查（Reverse） |
|-------|-------------------|-------------------|
| **L1 ↔ L2** | L1 → L2：前端绑定的字段，API 是否返回？ <br> 未找到 → **GHOST**（页面显示 undefined） | L2 → L1：API 返回的字段，前端是否使用？ <br> 未找到 → **STALE**（冗余传输） |
| **L2 ↔ L3** | L2 → L3：DTO/VO 字段是否在 Entity 中有对应？ <br> 未找到 → **GAP**（DTO 暴露了不存在的数据） | L3 → L2：Entity 字段是否被 DTO 暴露？ <br> 未找到 → 可能是 **合法隐藏**（如 password, salt） |
| **L3 ↔ L4** | L3 → L4：Entity 字段是否有对应 DB 列？ <br> 未找到 → **GAP**（ORM 映射错误） | L4 → L3：DB 列是否被 Entity 映射？ <br> 未找到 → **STALE**（废弃列）或遗漏 |
| **L1 ↔ L4** | 端到端验证：前端显示字段能否最终追溯到 DB 列？ <br> 整条链路断裂 → 综合问题 | DB 列是否最终体现在前端？ <br> 未体现 → 可能是后台字段，合法 |

```
比对顺序（推荐）：

  L3 ↔ L4  →  L2 ↔ L3  →  L1 ↔ L2
  （从底层向上：先确保数据基础正确，再检查接口层，最后检查展示层）

  最后做 L1 ↔ L4 端到端验证（跳过中间层，检查是否有中间层修改了字段名）
```

---

### 常见合法差异（不报为问题）

以下模式是正常的工程实践，匹配算法应识别并**跳过**，不产生告警：

#### 1. 外键命名前缀

```
L4 (DB):     users.id
L3 (Entity): User.id
L2 (API):    order.userId     ← 在 Order 的 DTO 中引用 User 的 id，加了表名前缀
L1 (UI):     order.userId

规则：在关联模块中，id → {entity}Id / {entity}_id 是合法的 FK 命名
```

#### 2. 系统时间字段变体

```
以下变体全部视为等价，不报问题：
  createdAt ↔ created_at ↔ createTime ↔ create_time ↔ gmt_create ↔ created ↔ createDate
  updatedAt ↔ updated_at ↔ updateTime ↔ update_time ↔ gmt_modified ↔ modified ↔ modifyDate
  deletedAt ↔ deleted_at ↔ deleteTime ↔ delete_time ↔ gmt_delete
```

#### 3. DTO 字段少于 Entity（信息隐藏）

```
Entity (L3):
  class User {
    id, userName, email, password, salt, deletedAt, internalNote
  }

DTO (L2):
  class UserVO {
    id, userName, email    ← 故意不暴露 password, salt, deletedAt, internalNote
  }

规则：以下 Entity 字段在 DTO 中不存在时，视为合法信息隐藏，不报 GAP：
  - password, pwd, secret, salt, hash
  - deletedAt, deleted, isDeleted (软删标记)
  - internalNote, adminRemark (内部备注)
  - 任何以 _ 开头的字段 (约定为内部字段)
```

#### 4. L1 字段少于 L2（部分展示）

```
API Response (L2):
  { id, userName, email, phone, avatar, createdAt, updatedAt, role, department, ... }

UI Table (L1):
  只展示 [userName, email, phone, role]   ← 正常，列表页不必显示所有字段

规则：L1 字段数 < L2 字段数是正常的（前端只展示需要的字段）
     只有 L1 有而 L2 没有的才是 GHOST
```

#### 5. 计算字段（前端拼接）

```
API Response (L2):
  { firstName: "John", lastName: "Doe" }

UI Display (L1):
  {{ firstName + ' ' + lastName }}  ← 显示为 "John Doe"
  或
  computed: fullName = firstName + ' ' + lastName

规则：前端存在 fullName 字段但 API 没有时，如果同时存在 firstName + lastName，
     则 fullName 是计算字段，不报 GHOST
```

#### 6. 聚合字段（后端统计）

```
DB (L4):   orders 表没有 orderCount 列
Entity (L3): 没有 orderCount 字段
API (L2):   { orderCount: 5 }    ← 来自 SQL COUNT 聚合
UI (L1):    显示 orderCount

规则：L2 有但 L3/L4 没有的字段，如果字段名含有以下聚合标识，视为合法计算字段：
  - 后缀：Count, Sum, Avg, Max, Min, Total
  - 前缀：total, sum, avg, count
  - 示例：orderCount, totalAmount, avgScore, maxPrice
```

#### 7. 分页/元数据字段

```
API Response (L2):
  { list: [...], total: 100, page: 1, pageSize: 20 }

规则：以下字段是通用分页/元数据字段，不与业务 Entity 做匹配：
  - total, page, pageSize, pageNum, current, size
  - hasMore, hasNext, hasPrev
  - code, message, msg, success, timestamp
```

#### 8. 枚举显示文本

```
API (L2):   { status: 1 }
UI (L1):    { status: 1, statusText: "已发布" }   ← 前端根据枚举值生成

规则：如果字段名 = 另一字段名 + "Text" / "Label" / "Name" / "Desc"，
     且对应基础字段存在，则视为前端枚举映射字段，不报 GHOST
  示例：statusText, typeName, categoryLabel, levelDesc
```

---

### 附录：匹配算法伪代码

```python
def match_fields(layer_a_fields, layer_b_fields, module_name):
    """
    对两层字段做智能匹配，返回匹配对和问题列表。
    """
    results = []
    issues = []
    pool_a = set(layer_a_fields)
    pool_b = set(layer_b_fields)

    # Step 1: 精确匹配
    for fa in list(pool_a):
        for fb in list(pool_b):
            if fa.name == fb.name:
                results.append(Match(fa, fb, type="exact"))
                pool_a.remove(fa)
                pool_b.remove(fb)
                break

    # Step 2: 标准化匹配
    for fa in list(pool_a):
        tokens_a = normalize(fa.name)  # 分词 + 小写 + 缩写展开
        for fb in list(pool_b):
            tokens_b = normalize(fb.name)
            if tokens_a == tokens_b:
                results.append(Match(fa, fb, type="style_equivalent"))
                pool_a.remove(fa)
                pool_b.remove(fb)
                break
            # 尝试布尔前缀/ID 后缀变体
            if match_with_prefix_suffix_variants(tokens_a, tokens_b):
                results.append(Match(fa, fb, type="style_equivalent"))
                pool_a.remove(fa)
                pool_b.remove(fb)
                break

    # Step 3: 近似匹配 (Typo)
    for fa in list(pool_a):
        norm_a = " ".join(normalize(fa.name))
        best_match, best_dist = None, float("inf")
        for fb in list(pool_b):
            norm_b = " ".join(normalize(fb.name))
            dist = levenshtein(norm_a, norm_b)
            if dist < best_dist:
                best_dist = dist
                best_match = fb
        threshold = get_threshold(len(norm_a))
        if best_match and 0 < best_dist <= threshold:
            if not is_excluded_from_typo(fa, best_match):
                issues.append(Issue(fa, best_match, type="TYPO",
                                    severity="critical", distance=best_dist))
                pool_a.remove(fa)
                pool_b.remove(best_match)

    # Step 4: 语义匹配
    for fa in list(pool_a):
        for fb in list(pool_b):
            if is_semantically_similar(fa.name, fb.name, module_name):
                issues.append(Issue(fa, fb, type="SEMANTIC",
                                    severity="warning",
                                    needs_confirmation=True))
                pool_a.remove(fa)
                pool_b.remove(fb)
                break

    # Step 5: 剩余字段分类
    for fa in pool_a:
        if not is_legitimate_absence(fa, "forward"):
            issues.append(Issue(fa, None, type="GHOST", severity="critical"))
    for fb in pool_b:
        if not is_legitimate_absence(fb, "reverse"):
            issues.append(Issue(None, fb, type="STALE", severity="warning"))

    return results, issues
```

---

## 全链路矩阵交叉验证

> 此章节对应 Step 3.5，在逐对匹配（Step 2）和问题检测（Step 3）完成后执行。
> 目的：追踪每个字段在 L1/L2/L3/L4 的存在性，发现逐对匹配的盲区。

### 阶段 1: 全局字段注册表构建

```
输入：
  - field-profile.json (Step 1 产出，各层原始字段)
  - field-mapping.json (Step 2 产出，已匹配的字段对)

算法：

  registry = {}   # key: 标准化字段名, value: { L1: field|null, L2: field|null, L3: field|null, L4: field|null }

  # 1. 先从已匹配的字段对填充（高置信度）
  for module in field_mapping.modules:
    for mapping in module.field_mappings:
      key = mapping.field_key
      registry[module.name + "." + key] = {
        L1: mapping.L1,   # 有值 = 该层存在此字段
        L2: mapping.L2,   # null = 该层不存在
        L3: mapping.L3,
        L4: mapping.L4
      }

  # 2. 再处理未匹配字段（Step 5 的 GHOST/STALE 残留字段）
  for module in field_profile.modules:
    for layer in [L1, L2, L3, L4]:
      for field in module.layers[layer].fields:
        norm_key = normalize(field.name)  # 复用 Step 2 的标准化规则
        full_key = module.name + "." + norm_key
        if full_key not in registry:
          registry[full_key] = { L1: null, L2: null, L3: null, L4: null }
        registry[full_key][layer] = field

输出：每个字段的 4 层存在性向量
```

**跨层字段归一规则：**

未配对字段跨层归一时，复用 Step 2 的标准化匹配规则：
1. 分词（camelCase / snake_case / PascalCase → 词根列表）
2. 全部小写
3. 缩写展开（同 Step 2 的缩写等价表）
4. 比较词根序列是否一致

如果 L4 有 `user_name`，L1 有 `userName`，且 Step 2 没有把它们配在一起（可能因为它们属于不同的逐对匹配通道），矩阵构建时通过标准化规则发现它们是同一个字段，合并到同一行。

### 阶段 2: 模式识别

```
模式定义表（10 种有意义模式 + 1 种兜底）：

PATTERNS = {
  "FULL_CHAIN":   (True,  True,  True,  True),   # ✅ 健康
  "DTO_SKIP":     (True,  False, True,  True),   # 🔴 后端有，API 漏暴露
  "ORM_SKIP":     (True,  True,  False, True),   # 🔴 绕过 Entity
  "TUNNEL":       (True,  False, False, True),   # 🔴 UI 直连 DB
  "UI_MISSING":   (False, True,  True,  True),   # 🟡 后端完整，前端未用
  "DB_ORPHAN":    (False, False, False, True),   # 🟡 死列
  "RAW_SQL":      (False, True,  False, True),   # 🟡 绕过 ORM
  "COMPUTED":     (True,  True,  True,  False),  # ℹ️ 计算字段
  "DTO_ONLY":     (True,  True,  False, False),  # ℹ️ 聚合字段
  "BACKEND_ONLY": (False, False, True,  True),   # ℹ️ 内部字段
}

算法：

for key, entry in registry:
  vector = (entry.L1 != null, entry.L2 != null, entry.L3 != null, entry.L4 != null)
  matched_pattern = PATTERNS.get(vector, "UNCOMMON")
  entry.pattern = matched_pattern
```

**系统字段和合法隐藏字段的处理：**

- 系统字段 (`id`, `createdAt`, `updatedAt`, `deletedAt`, `version`, `tenantId`) → 跳过模式判定，不参与统计
- 合法隐藏字段 (`password`, `salt`, `secret`, `token`, `internalNotes`) → BACKEND_ONLY 不升级
- 聚合字段 (`xxxCount`, `totalXxx`, `fullName`, `xxxRate`) → DTO_ONLY/COMPUTED 是合法的

### 阶段 3: 与 Step 3 结果交叉

```
输入：
  - field-issues.json (Step 3 产出)
  - registry (阶段 2 产出，含 pattern)

交叉规则：

  # 1. 升级
  for issue in field_issues:
    entry = find_in_registry(issue.module, issue.field)
    if entry and entry.pattern in ["DTO_SKIP", "ORM_SKIP", "TUNNEL"]:
      issue.severity = "critical"  # 确认升级
      issue.matrix_pattern = entry.pattern
      issue.layers = entry.vector
      issue.cross_layer_evidence = generate_evidence(entry)
      # 例: "字段在 L1/L3/L4 均存在，仅 L2(DTO) 缺失，高置信度为 DTO 遗漏"

  # 2. 降级
  for issue in field_issues:
    if issue.type == "STALE":
      entry = find_in_registry(issue.module, issue.field)
      if entry and entry.pattern == "BACKEND_ONLY" and is_hidden_field(issue.field):
        issue.severity = "info"
        issue.cross_layer_evidence = "合法的安全隐藏字段（BACKEND_ONLY）"

  # 3. 新增（矩阵发现但 Step 3 未报告的）
  for key, entry in registry:
    if entry.pattern in ["DB_ORPHAN", "TUNNEL", "ORM_SKIP", "RAW_SQL"]:
      if not already_reported(entry):
        new_issue = create_issue(entry)
        field_issues.append(new_issue)
```

**generate_evidence 生成规则：**

| 模式 | evidence 模板 |
|------|-------------|
| DTO_SKIP | "字段在 {存在层} 均存在，仅 L2(DTO) 缺失，高置信度为 DTO 遗漏" |
| ORM_SKIP | "字段在 L1/L2/L4 存在但 L3(Entity) 缺失，可能通过 raw SQL 绕过 ORM" |
| TUNNEL | "字段仅在 L1(UI) 和 L4(DB) 存在，跳过 API 和 Entity 层，架构异常" |
| UI_MISSING | "字段在 L2/L3/L4 完整链路存在，但 L1(UI) 未展示" |
| DB_ORPHAN | "字段仅在 L4(DB) 存在，所有上层均未引用，可能是废弃列" |
| RAW_SQL | "字段在 L2(API) 和 L4(DB) 存在但 L3(Entity) 缺失，可能通过 raw SQL 直取" |

---

## Flutter 特有问题类型

> 当项目包含 Flutter 客户端和 Web/H5 客户端共享同一后端 API 时，增加以下跨平台问题检测。

### 新增问题类型

| 问题类型 | 严重度 | 场景 | 检测方式 |
|---------|--------|------|---------|
| **PLATFORM_GAP** | 🔴 Critical | Web 端有字段但 Flutter 端模型缺少（同一 API） | 对比同一 API 端点在 Web TS 类型和 Dart 模型中的字段 |
| **SERIALIZE_MISMATCH** | 🔴 Critical | Dart `@JsonKey(name:)` 映射与后端实际字段名不一致 | 对比 Dart `@JsonKey` 值与 L2 后端 DTO 字段名 |
| **NULL_SAFETY** | 🟡 Warning | 后端返回 nullable 但 Dart 模型声明为 non-null | 对比后端 DTO 的 nullable 标记与 Dart 类型的 `?` 后缀 |

### PLATFORM_GAP 检测逻辑

```
输入：同一 API 端点（如 GET /api/orders）
  - Web 端模型字段（TypeScript interface/type）
  - Flutter 端模型字段（Dart class）

算法：
  1. 对同一 API 端点，提取 Web 端和 Flutter 端的模型字段
  2. 对 Web 端有但 Flutter 端没有的字段：
     a. 检查是否为平台差异白名单字段 → 跳过
     b. 否则报 PLATFORM_GAP
  3. 对 Flutter 端有但 Web 端没有的字段：
     a. 检查是否为平台特有字段（如 deviceToken, pushEnabled）→ 跳过
     b. 否则也报 PLATFORM_GAP（可能 Web 端遗漏）

平台差异白名单：
  - Flutter 特有: deviceToken, pushToken, biometricEnabled, offlineData, localCachePath
  - Web 特有: csrfToken, sessionId, cookieConsent
```

### SERIALIZE_MISMATCH 检测逻辑

```
输入：
  - Dart 模型的 @JsonKey(name: 'xxx') 映射
  - 后端 DTO 的实际字段名

算法：
  1. 提取 Dart 模型中所有 @JsonKey 映射
  2. 对每个映射，检查 @JsonKey 的 name 值是否在后端 L2 字段中存在
  3. 不存在 → SERIALIZE_MISMATCH（Dart 模型会解析失败）
  4. 存在但拼写有误 → 同时报 SERIALIZE_MISMATCH + TYPO
```

### NULL_SAFETY 检测逻辑

```
输入：
  - Dart 模型字段的 nullable 标记（String? 或 required String）
  - 后端 DTO 字段的 nullable/required 标记

算法：
  1. 后端标记为 nullable + Dart 声明为 non-null（无 ? 后缀）→ 报 NULL_SAFETY
     "后端 API 可能返回 null，但 Dart 模型未处理 null，运行时可能抛 TypeError"
  2. 后端标记为 required + Dart 声明为 nullable → 不报（安全方向的宽松处理）
```

### Flutter 问题输出示例

```json
{
  "type": "PLATFORM_GAP",
  "severity": "critical",
  "module": "order",
  "api_endpoint": "GET /api/orders",
  "field": "cancelReason",
  "web_model": { "file": "src/api/types/order.ts:15", "name": "cancelReason", "type": "string" },
  "dart_model": null,
  "suggestion": "Flutter 端 Order 模型缺少 cancelReason 字段，该字段在 Web 端已使用"
}
```

```json
{
  "type": "SERIALIZE_MISMATCH",
  "severity": "critical",
  "module": "user",
  "field": "userName",
  "dart_json_key": "user_name",
  "backend_field": "username",
  "file": "lib/models/user.dart:12",
  "suggestion": "@JsonKey(name: 'user_name') 与后端实际字段名 'username' 不一致，API 数据无法正确解析"
}
```


### 来源文件：`docs/fieldcheck/overview.md`

## FieldCheck 总览 — 字段一致性检查

> 检查前后端字段名的全链路一致性，发现幽灵字段、拼写错误、映射断裂等问题。
> 纯静态分析，不需要启动应用。

### 核心概念：4 层字段模型

```
Layer 1: UI 显示层        Layer 2: API 接口层       Layer 3: 实体层          Layer 4: 数据库层
─────────────────        ─────────────────        ─────────────────       ─────────────────
前端组件中绑定的字段       请求/响应的 JSON 字段      后端 Entity/Model        表列名/Schema

Vue:  {{ item.userName }}  POST body: { userName }  class User { userName }  column: user_name
React: data.userName       GET resp: { userName }   @Column userName         user_name VARCHAR

检查方向（双向）：
  L1 ←→ L2: 前端用的字段，API 返回了吗？API 返回的字段，前端展示了吗？
  L2 ←→ L3: DTO/VO 字段和 Entity 字段对应吗？
  L3 ←→ L4: Entity 字段和数据库列名映射正确吗？
  L1 ←→ L4: 跨层端到端，前端显示的字段最终能映射到数据库列吗？
```

### 问题分类

| 问题类型 | ID | 严重度 | 说明 | 典型后果 |
|---------|-----|--------|------|---------|
| **幽灵字段** (Ghost Field) | GHOST | 🔴 Critical | 前端显示了一个字段，但 API 不返回 | 页面显示 undefined / 空白 |
| **拼写不一致** (Typo Mismatch) | TYPO | 🔴 Critical | 语义相同但拼写不同，如 `userName` vs `userNmae` | 数据丢失或展示异常 |
| **映射断裂** (Mapping Gap) | GAP | 🔴 Critical | Entity 有但 DTO 没暴露，或 DB 有列但 Entity 没映射 | 功能不完整 |
| **废弃字段** (Stale Field) | STALE | 🟡 Warning | API 返回了字段，但前端没有任何地方使用 | 冗余传输 |
| **语义歧义** (Semantic Ambiguity) | SEMANTIC | 🟡 Warning | 不同层用不同名字指代可能相同的数据 | 混淆，需人工确认 |
| **类型不一致** (Type Mismatch) | TYPE | 🟡 Warning | 字段名一致但类型不同，如前端期望 string 但 API 返回 number | 显示格式问题 |

---

### 执行流程

```
Step 0: 项目画像获取
  ├── 检查 .allforai/deadhunt/output/validation-profile.json 是否存在
  ├── 存在 → 读取技术栈、模块列表
  └── 不存在 → 执行轻量版项目探测

Step 1: 字段提取（L4 → L3 → L2 → L1）
  ├── L4: 扫描 DB schema / ORM 定义 / migration 文件
  ├── L3: 扫描 Entity / Model 类
  ├── L2: 扫描 DTO/VO + API 路由定义 + OpenAPI spec
  └── L1: 扫描前端组件中的字段绑定

Step 2: 跨层映射构建
  ├── 按模块分组（user 模块的 L1~L4 字段归在一起）
  ├── 对每对相邻层做智能匹配
  └── 输出 field-mapping.json

Step 3: 问题检测（6 种规则）
  ├── Ghost / Typo / Gap → Critical
  └── Stale / Semantic / Type → Warning

Step 3.5: 全链路矩阵交叉验证（仅 full / backend scope）
  ├── 构建全局字段注册表，对每个字段建 [L1,L2,L3,L4] 存在性向量
  ├── 匹配 10 种异常模式（DTO_SKIP / ORM_SKIP / TUNNEL 等）
  ├── 与 Step 3 结果交叉：升级/降级/新增问题
  └── 输出 field-matrix.json

Step 4: 报告生成
  ├── 写入 .allforai/deadhunt/output/field-analysis/ 目录
  └── 在对话中输出完整报告摘要（强制）
```

---

#### Step 0: 项目画像获取

```
检查 .allforai/deadhunt/output/validation-profile.json 是否存在
├── 存在 → 读取技术栈、模块列表
└── 不存在 → 执行轻量版探测：
    1. 识别前端框架: package.json dependencies
       - Vue: vue, nuxt
       - React: react, next
       - Angular: @angular/core
    2. 识别后端框架:
       - Java Spring: pom.xml 中有 spring-boot-starter
       - Go: go.mod 中有 gin / echo / fiber 等
       - Node/NestJS: package.json 中有 @nestjs/core / express
       - Python/Django: requirements.txt 中有 django / fastapi
    3. 识别 ORM: 扫描 Entity/Model 定义模式
       - JPA: @Entity + @Column 注解
       - TypeORM: @Entity + @Column 装饰器
       - Prisma: schema.prisma 文件
       - GORM: gorm struct tags
       - Django ORM: models.Model 子类
       - MyBatis: *Mapper.xml 文件
    4. 识别模块: 按前端路由 + 后端 Controller 推断
```

**注意：** fieldcheck 不强制要求完整的 deadhunt Phase 0。如果没有 `validation-profile.json`，自行做轻量探测即可。画像确认后才能进入 Step 1。

---

#### Step 1: 字段提取

详见 `${CLAUDE_PLUGIN_ROOT}/docs/fieldcheck/extractors.md`。

**提取顺序：L4 → L3 → L2 → L1**（从稳定层到变化层，DB schema 变化频率最低，UI 变化频率最高）

```
L4 (DB):     扫描 ORM schema → 表名 + 列名 + 类型
             数据源: Prisma schema / JPA @Column / GORM tags / Django models /
                     MyBatis resultMap / Sequelize define / Drizzle schema / SQL migration

L3 (Entity): 扫描 Entity/Model 类 → 字段名 + 类型 + DB 映射
             数据源: Java Entity / Go struct / TypeScript Entity / Python Model

L2 (API):    扫描 DTO/VO/OpenAPI → 端点 + 请求字段 + 响应字段
             数据源优先级: OpenAPI spec > DTO/VO 类 > 前端 API 接口定义 > Route handler 推断

L1 (UI):     扫描前端组件 → 页面 + 绑定字段 + 上下文(表格/表单/模板)
             高置信度: 表格列配置(dataIndex/prop) + 表单字段配置(name/prop)
             中等置信度: 模板绑定({{ item.xxx }} / {data.xxx})
```

提取结果写入 `.allforai/deadhunt/output/field-analysis/field-profile.json`。

---

#### Step 2: 跨层映射构建

详见 `${CLAUDE_PLUGIN_ROOT}/docs/fieldcheck/matching.md`。

按模块分组，对每对相邻层执行智能匹配：

```
对每个模块 M:
  1. 取 M 在 L4 的字段集 F4
  2. 取 M 在 L3 的字段集 F3
  3. 对 F4 和 F3 执行匹配 → L3↔L4 映射
  4. 取 M 在 L2 的字段集 F2
  5. 对 F3 和 F2 执行匹配 → L2↔L3 映射
  6. 取 M 在 L1 的字段集 F1
  7. 对 F2 和 F1 执行匹配 → L1↔L2 映射
```

**模块分组策略：**

```
API resource name ←→ Entity name ←→ table name ←→ 前端路由/API调用

示例：
  /api/users    ←→  User (Entity)   ←→  users (table)  ←→  /users/list (前端页面)
  /api/products ←→  Product (Entity) ←→  products (table) ←→  /products (前端页面)

关联方法：
  - API resource name 对齐: /api/users → User → users
  - 前端页面通过 API 调用关联: import { getUsers } from '@/api/user' → /api/users → User 模块
  - 前端路由路径关联: /users/list → users 模块
  - 无法自动关联的字段标记为 unmatched
```

结果写入 `.allforai/deadhunt/output/field-analysis/field-mapping.json`。

---

#### Step 3: 问题检测

对匹配结果执行 6 种问题检测：

| 检测规则 | 条件 | 输出类型 |
|---------|------|---------|
| GHOST | L(n) 有字段但 L(n+1) 无匹配，且非系统字段 | 🔴 Critical |
| TYPO | 标准化后词根序列编辑距离在阈值内（短字段 ≤1，长字段 ≤2） | 🔴 Critical |
| GAP | L3 有字段但 L2 未暴露，排除合法隐藏字段（password, salt, deletedAt 等） | 🔴 Critical |
| STALE | L(n+1) 有字段但 L(n) 未使用，且超过正常未使用比例 | 🟡 Warning |
| SEMANTIC | 同模块内语义相似但名字不同的未匹配字段对 | 🟡 Warning (needs_confirmation) |
| TYPE | 同名字段跨层类型不一致（如 number vs string） | 🟡 Warning |

结果写入 `.allforai/deadhunt/output/field-analysis/field-issues.json`。

---

#### Step 3.5: 全链路矩阵交叉验证

> 单靠相邻层逐对匹配有盲区。全链路矩阵追踪每个字段在 L1/L2/L3/L4 的存在性，
> 发现跨层异常模式（如"后端全链路有、API 漏暴露"）。

**Scope 限制：** 仅 `full` 和 `backend` scope 执行此步骤。`frontend` / `endtoend` 因不足 3 层，矩阵无额外价值，跳过。

详见 `${CLAUDE_PLUGIN_ROOT}/docs/fieldcheck/matching.md` 的"全链路矩阵交叉验证"章节。

**阶段 1: 构建全局字段注册表**

从 `field-profile.json` 收集所有层的字段，按模块分组。对每个字段构建存在性向量 `[L1, L2, L3, L4]`。

字段标准化复用 Step 2 的匹配结果：
- 精确匹配和标准化匹配已配对的字段视为"同一字段"
- 未匹配的保留原名，按标准化规则（分词 + 小写 + 缩写展开）做跨层名称归一

```
模块: user
  userName  → [✅ L1, ✅ L2, ✅ L3, ✅ L4] → FULL_CHAIN ✅
  password  → [❌ L1, ❌ L2, ✅ L3, ✅ L4] → BACKEND_ONLY (合法隐藏)
  avatar    → [✅ L1, ❌ L2, ✅ L3, ✅ L4] → DTO_SKIP 🔴
  oldEmail  → [❌ L1, ❌ L2, ❌ L3, ✅ L4] → DB_ORPHAN 🟡
```

**阶段 2: 模式识别**

对每个字段的存在性向量匹配 10 种模式：

| 模式 | L1 | L2 | L3 | L4 | 严重度 | 说明 |
|------|----|----|----|----|--------|------|
| FULL_CHAIN | ✅ | ✅ | ✅ | ✅ | ✅ 健康 | 完整链路 |
| DTO_SKIP | ✅ | ❌ | ✅ | ✅ | 🔴 Critical | 后端有，API 漏暴露 |
| ORM_SKIP | ✅ | ✅ | ❌ | ✅ | 🔴 Critical | 绕过 Entity，可能 raw SQL |
| TUNNEL | ✅ | ❌ | ❌ | ✅ | 🔴 Critical | UI 直连 DB，跳过 API+Entity |
| UI_MISSING | ❌ | ✅ | ✅ | ✅ | 🟡 Warning | 后端完整，前端未使用 |
| DB_ORPHAN | ❌ | ❌ | ❌ | ✅ | 🟡 Warning | 死列，清理候选 |
| RAW_SQL | ❌ | ✅ | ❌ | ✅ | 🟡 Warning | API 从 DB 直取，绕过 ORM |
| COMPUTED | ✅ | ✅ | ✅ | ❌ | ℹ️ Info | 计算/虚拟字段 |
| DTO_ONLY | ✅ | ✅ | ❌ | ❌ | ℹ️ Info | 纯 DTO 聚合字段 |
| BACKEND_ONLY | ❌ | ❌ | ✅ | ✅ | ℹ️ Info | 内部字段（区分安全设计 vs 死代码） |

其余模式归入 `UNCOMMON`，标记 `needs_confirmation`。

**阶段 3: 与 Step 3 结果交叉**

- **升级**: Step 3 的 GAP/GHOST + 矩阵 DTO_SKIP → `cross_layer_evidence` 确认为 bug
- **降级**: Step 3 的 STALE + 矩阵 BACKEND_ONLY + 合法隐藏字段 → 降为 Info
- **新增**: 矩阵发现但 Step 3 未报告的 (DB_ORPHAN, TUNNEL, ORM_SKIP, RAW_SQL) → 新问题

结果写入 `.allforai/deadhunt/output/field-analysis/field-matrix.json`，并更新 `field-issues.json`。

---

#### Step 4: 报告生成

详见 `${CLAUDE_PLUGIN_ROOT}/docs/fieldcheck/report.md`。

**必须做两件事：**

1. **写文件**：将结构化数据写入 `.allforai/deadhunt/output/field-analysis/` 目录
   - `field-profile.json` — 各层提取的原始字段清单
   - `field-mapping.json` — 跨层映射关系
   - `field-issues.json` — 问题列表（含矩阵交叉验证结果）
   - `field-matrix.json` — 全链路存在矩阵（仅 full/backend scope）
   - `field-report.md` — 人类可读的完整报告

2. **在对话中直接输出完整报告摘要** — 不能只说"报告已保存"。摘要必须包含：
   - 总览表（每层字段数、一致率、覆盖率）
   - Critical 问题逐条列出（字段名、位置、修复建议）
   - Warning 问题逐条列出
   - 需人工确认项
   - 字段热力图（哪些模块问题最多）
   - 下一步建议

---

### Scope 模式说明

| Scope | 检查范围 | 适用场景 |
|-------|---------|---------|
| `full`（默认） | L1↔L2↔L3↔L4 全链路 | 完整检查，首次使用或发版前 |
| `frontend` | 只查 L1↔L2 | 前端开发中快速验证字段是否与 API 对齐 |
| `backend` | 只查 L2↔L3↔L4 | 后端开发中快速验证 DTO/Entity/DB 一致性 |
| `endtoend` | 只查 L1↔L4（跳过中间层） | 端到端快速对比，看前端字段能否最终映射到数据库 |

`--module <name>` 参数可限制只分析指定模块（如 `--module user`），跳过其他模块以加快分析速度。

```bash
# 完整检查
/deadhunt:fieldcheck

# 只查前端字段一致性
/deadhunt:fieldcheck frontend

# 只查后端字段一致性
/deadhunt:fieldcheck backend

# 只查用户模块
/deadhunt:fieldcheck --module user

# 组合使用
/deadhunt:fieldcheck frontend --module order
```

---

### 注意事项

1. **系统字段不参与严格比对**：`id`, `createdAt`, `updatedAt`, `deletedAt`, `createdBy`, `updatedBy`, `version`, `tenantId` 等系统字段各层命名风格不同是常态（如 `createdAt` vs `created_at` vs `gmt_create`），标记但不报为问题
2. **DTO 少于 Entity 可能是合法的**：信息隐藏是安全设计（不暴露 `password`, `salt`, `deletedAt`, `internalNotes` 等），不应报为 GAP
3. **前端少于 API 可能是合法的**：列表页只展示部分字段很正常，详情页也不一定展示所有字段。但当废弃率超过 50% 时，建议优化 API 响应粒度
4. **聚合/计算字段只在 API 层出现是合法的**：如 `orderCount`, `totalAmount`, `fullName` 等字段可能是 SQL 聚合或后端计算产生的，不在 Entity 和 DB 中存在，不应报为 GAP
5. **不确定就标 `needs_confirmation`**：宁可多问用户一次，不要产生误报（false positive）。语义歧义、合法的命名差异等情况，全部标记为需确认


### 来源文件：`docs/fieldcheck/report.md`

## 报告格式参考

> 本文档定义 fieldcheck 的输出文件格式和对话中必须展示的报告摘要模板。

### 输出文件结构

```
.allforai/deadhunt/output/field-analysis/
├── field-profile.json    ← 各层提取到的原始字段清单
├── field-mapping.json    ← 跨层映射关系（匹配结果）
├── field-issues.json     ← 发现的问题列表（含矩阵交叉验证结果）
├── field-matrix.json     ← 全链路存在矩阵（仅 full/backend scope 生成）
└── field-report.md       ← 人类可读的完整报告
```

---

### field-profile.json

各层字段提取的原始结果，合并为一个文件：

```json
{
  "generated_at": "2026-02-17T10:30:00Z",
  "project": "XX电商平台",
  "tech_stack": {
    "frontend": "vue",
    "backend": "java-spring",
    "orm": "jpa",
    "db": "mysql"
  },
  "layers": {
    "L4": {
      "source": "jpa_entity",
      "tables": [
        {
          "name": "users",
          "model_name": "User",
          "file": "server/src/entities/User.java:15",
          "columns": [
            { "name": "id", "type": "int", "primary": true },
            { "name": "user_name", "type": "varchar", "nullable": false },
            { "name": "email", "type": "varchar", "nullable": false, "unique": true },
            { "name": "avatar_url", "type": "varchar", "nullable": true },
            { "name": "created_at", "type": "datetime", "nullable": false }
          ]
        },
        {
          "name": "orders",
          "model_name": "Order",
          "file": "server/src/entities/Order.java:12",
          "columns": [
            { "name": "id", "type": "int", "primary": true },
            { "name": "user_id", "type": "int", "nullable": false },
            { "name": "order_amount", "type": "decimal", "nullable": false },
            { "name": "total_price", "type": "decimal", "nullable": false },
            { "name": "status", "type": "varchar", "nullable": false }
          ]
        }
      ]
    },
    "L3": {
      "source": "java_entity",
      "entities": [
        {
          "name": "User",
          "file": "server/src/entities/User.java:15",
          "table": "users",
          "fields": [
            { "name": "id", "type": "Long", "column": "id", "primary": true },
            { "name": "userName", "type": "String", "column": "user_name" },
            { "name": "email", "type": "String", "column": "email" },
            { "name": "avatarUrl", "type": "String", "column": "avatar_url" },
            { "name": "createdAt", "type": "LocalDateTime", "column": "created_at" }
          ]
        },
        {
          "name": "Order",
          "file": "server/src/entities/Order.java:12",
          "table": "orders",
          "fields": [
            { "name": "id", "type": "Long", "column": "id", "primary": true },
            { "name": "userId", "type": "Long", "column": "user_id" },
            { "name": "orderAmount", "type": "BigDecimal", "column": "order_amount" },
            { "name": "totalPrice", "type": "BigDecimal", "column": "total_price" },
            { "name": "status", "type": "String", "column": "status" }
          ]
        }
      ]
    },
    "L2": {
      "source": "dto_classes",
      "endpoints": [
        {
          "method": "GET",
          "path": "/api/users",
          "file": "server/src/dto/UserResponse.java:8",
          "request": [
            { "name": "keyword", "type": "string", "in": "query" },
            { "name": "page", "type": "number", "in": "query" }
          ],
          "response": [
            { "name": "id", "type": "number" },
            { "name": "userName", "type": "string" },
            { "name": "email", "type": "string" },
            { "name": "displayName", "type": "string" },
            { "name": "createdBy", "type": "string" },
            { "name": "createdAt", "type": "string" }
          ]
        },
        {
          "method": "GET",
          "path": "/api/orders",
          "file": "server/src/dto/OrderResponse.java:6",
          "request": [
            { "name": "status", "type": "string", "in": "query" }
          ],
          "response": [
            { "name": "id", "type": "number" },
            { "name": "orderAmout", "type": "number" },
            { "name": "totalPrice", "type": "number" },
            { "name": "status", "type": "string" }
          ]
        }
      ]
    },
    "L1": {
      "source": "vue_components",
      "pages": [
        {
          "path": "/users/list",
          "component": "UserList",
          "file": "src/views/user/UserList.vue",
          "fields": [
            { "name": "userName", "context": "table-column", "label": "用户名", "line": 45 },
            { "name": "email", "context": "table-column", "label": "邮箱", "line": 46 },
            { "name": "avatar", "context": "template-binding", "label": null, "line": 32 },
            { "name": "nickname", "context": "table-column", "label": "昵称", "line": 48 }
          ]
        },
        {
          "path": "/orders/list",
          "component": "OrderList",
          "file": "src/views/order/OrderList.vue",
          "fields": [
            { "name": "orderAmount", "context": "table-column", "label": "订单金额", "line": 38 },
            { "name": "totalPrice", "context": "table-column", "label": "总价", "line": 52 },
            { "name": "status", "context": "table-column", "label": "状态", "line": 55 }
          ]
        }
      ]
    }
  },
  "stats": {
    "L4_fields": 172,
    "L3_fields": 178,
    "L2_fields": 189,
    "L1_fields": 156,
    "modules_analyzed": 12
  }
}
```

---

### field-mapping.json

跨层匹配结果：

```json
{
  "generated_at": "2026-02-17T10:30:00Z",
  "mappings_by_module": [
    {
      "module": "user",
      "table": "users",
      "entity": "User",
      "field_mappings": [
        {
          "field_key": "userName",
          "L4": { "name": "user_name", "type": "varchar", "file": "prisma/schema.prisma:14" },
          "L3": { "name": "userName", "type": "String", "file": "server/src/entities/User.java:22" },
          "L2": { "name": "userName", "type": "string", "file": "server/src/dto/UserResponse.java:8" },
          "L1": { "name": "userName", "type": null, "file": "src/views/user/UserList.vue:45", "context": "table-column", "label": "用户名" },
          "match_type": "style_equivalent",
          "status": "pass"
        },
        {
          "field_key": "email",
          "L4": { "name": "email", "type": "varchar", "file": "prisma/schema.prisma:16" },
          "L3": { "name": "email", "type": "String", "file": "server/src/entities/User.java:24" },
          "L2": { "name": "email", "type": "string", "file": "server/src/dto/UserResponse.java:10" },
          "L1": { "name": "email", "type": null, "file": "src/views/user/UserList.vue:46", "context": "table-column", "label": "邮箱" },
          "match_type": "exact",
          "status": "pass"
        },
        {
          "field_key": "avatar",
          "L4": { "name": "avatar_url", "type": "varchar", "file": "prisma/schema.prisma:18" },
          "L3": { "name": "avatarUrl", "type": "String", "file": "server/src/entities/User.java:28" },
          "L2": null,
          "L1": { "name": "avatar", "type": null, "file": "src/views/user/UserList.vue:32", "context": "template-binding" },
          "match_type": null,
          "status": "issue",
          "issue": { "type": "GHOST", "severity": "critical", "detail": "L1 uses 'avatar' but L2 response does not include this field" }
        }
      ]
    },
    {
      "module": "order",
      "table": "orders",
      "entity": "Order",
      "field_mappings": [
        {
          "field_key": "orderAmount",
          "L4": { "name": "order_amount", "type": "decimal", "file": "prisma/schema.prisma:34" },
          "L3": { "name": "orderAmount", "type": "BigDecimal", "file": "server/src/entities/Order.java:34" },
          "L2": { "name": "orderAmout", "type": "number", "file": "server/src/dto/OrderDTO.java:23" },
          "L1": { "name": "orderAmount", "type": null, "file": "src/views/order/OrderList.vue:38", "context": "table-column", "label": "订单金额" },
          "match_type": "typo",
          "status": "issue",
          "issue": { "type": "TYPO", "severity": "critical", "detail": "L2 'orderAmout' is a misspelling of L3 'orderAmount' (edit distance = 1)" }
        },
        {
          "field_key": "totalPrice",
          "L4": { "name": "total_price", "type": "decimal", "file": "prisma/schema.prisma:35" },
          "L3": { "name": "totalPrice", "type": "BigDecimal", "file": "server/src/entities/Order.java:36" },
          "L2": { "name": "totalPrice", "type": "number", "file": "server/src/dto/OrderResponse.java:20" },
          "L1": { "name": "totalPrice", "type": null, "file": "src/views/order/OrderList.vue:52", "context": "table-column", "label": "总价" },
          "match_type": "style_equivalent",
          "status": "pass"
        }
      ]
    }
  ],
  "summary": {
    "L1_L2": { "total": 156, "pass": 148, "issues": 8 },
    "L2_L3": { "total": 189, "pass": 185, "issues": 4 },
    "L3_L4": { "total": 178, "pass": 176, "issues": 2 }
  }
}
```

---

### field-issues.json

所有问题的结构化列表：

```json
{
  "generated_at": "2026-02-17T10:30:00Z",
  "issues": [
    {
      "id": "FC-001",
      "type": "GHOST",
      "severity": "critical",
      "module": "user",
      "field": "avatar",
      "layers": "L1↔L2",
      "detail": "前端 UserList.vue:32 使用 `avatar` 字段显示头像，但 GET /api/users 的响应（UserResponse.java）不包含此字段，页面将显示 undefined",
      "source_file": "src/views/user/UserList.vue:32",
      "target_file": "server/src/dto/UserResponse.java",
      "suggestion": "在 UserResponse 中添加 avatar 字段，或修改前端使用 avatarUrl 与 Entity 保持一致"
    },
    {
      "id": "FC-002",
      "type": "TYPO",
      "severity": "critical",
      "module": "order",
      "field": "orderAmout → orderAmount",
      "layers": "L2↔L3",
      "detail": "OrderDTO.java:23 中字段名为 `orderAmout`（缺少字母 n），而 Entity 中为 `orderAmount`，导致序列化时字段值丢失",
      "source_file": "server/src/dto/OrderDTO.java:23",
      "target_file": "server/src/entities/Order.java:34",
      "suggestion": "修正 DTO 中的拼写：orderAmout → orderAmount"
    },
    {
      "id": "FC-003",
      "type": "STALE",
      "severity": "warning",
      "module": "user",
      "field": "createdBy",
      "layers": "L2↔L1",
      "detail": "API 响应中返回 `createdBy` 字段（UserResponse.java:12），但前端所有用户相关页面均未使用此字段，属于冗余传输",
      "source_file": "server/src/dto/UserResponse.java:12",
      "target_file": null,
      "suggestion": "如无需展示，从 UserResponse 中移除以减少传输量；或在用户详情页中展示创建者信息"
    },
    {
      "id": "FC-004",
      "type": "GAP",
      "severity": "critical",
      "module": "product",
      "field": "seoKeywords",
      "layers": "L3↔L2",
      "detail": "Product Entity 有 `seoKeywords` 字段（对应 DB 列 `seo_keywords`），但 ProductResponse、ProductDetailResponse 等所有 DTO 均未暴露此字段，前端无法获取 SEO 关键词数据",
      "source_file": "server/src/entities/Product.java:56",
      "target_file": null,
      "suggestion": "在 ProductDetailResponse 中添加 seoKeywords 字段，使前端编辑页面可以管理 SEO 关键词"
    },
    {
      "id": "FC-005",
      "type": "SEMANTIC",
      "severity": "warning",
      "module": "user",
      "field": "nickname vs displayName",
      "layers": "L1↔L2",
      "detail": "前端 UserProfile.vue:18 使用 `nickname` 字段，API 返回 `displayName` 字段。语义可能相同（都表示用户显示名），但无法自动确认是否指代同一数据",
      "source_file": "src/views/user/UserProfile.vue:18",
      "target_file": "server/src/dto/UserResponse.java:15",
      "suggestion": "确认二者是否指代同一字段。如果是，统一命名为 displayName 或 nickname",
      "needs_confirmation": true
    },
    {
      "id": "FC-006",
      "type": "TYPE",
      "severity": "warning",
      "module": "order",
      "field": "totalPrice",
      "layers": "L2↔L1",
      "detail": "API 返回 totalPrice 类型为 number（后端 BigDecimal），但前端表格列直接渲染未做格式化，可能显示为长浮点数（如 99.90000000001）",
      "source_file": "server/src/dto/OrderResponse.java:20",
      "target_file": "src/views/order/OrderList.vue:52",
      "suggestion": "前端列渲染时添加金额格式化（如 toFixed(2)、currency filter 或 Intl.NumberFormat）"
    },
    {
      "id": "FC-007",
      "note": "与 FC-001 为同一字段问题，经 Step 3.5 矩阵交叉验证升级",
      "type": "GAP",
      "severity": "critical",
      "module": "user",
      "field": "avatar",
      "layers": "L1↔L2",
      "detail": "前端 UserList.vue:32 使用 `avatar` 字段，API 未返回此字段",
      "source_file": "src/views/user/UserList.vue:32",
      "target_file": "server/src/dto/UserResponse.java",
      "suggestion": "在 UserResponse 中添加 avatar 字段",
      "matrix_pattern": "DTO_SKIP",
      "cross_layer_evidence": "字段在 L1/L3/L4 均存在，仅 L2(DTO) 缺失，高置信度为 DTO 遗漏"
    },
    {
      "id": "FC-008",
      "type": "DB_ORPHAN",
      "severity": "warning",
      "module": "user",
      "field": "old_email",
      "layers": "L4",
      "detail": "数据库 users 表有 old_email 列，但所有上层（Entity/API/UI）均未引用",
      "source_file": null,
      "target_file": "users.old_email (DB column)",
      "suggestion": "确认是否为废弃列，如是则执行 migration 删除",
      "matrix_pattern": "DB_ORPHAN",
      "cross_layer_evidence": "字段仅在 L4(DB) 存在，所有上层均未引用，可能是废弃列",
      "needs_confirmation": true
    }
  ],
  "stats": {
    "total": 8,
    "critical": 4,
    "warning": 4,
    "needs_confirmation": 2,
    "matrix_enhanced": 2
  }
}
```

---

### field-matrix.json

全链路字段存在矩阵（仅 `full` 和 `backend` scope 生成）：

```json
{
  "generated_at": "2026-02-17T10:30:00Z",
  "scope": "full",
  "modules": {
    "user": {
      "fields": {
        "userName": { "L1": true, "L2": true, "L3": true, "L4": true, "pattern": "FULL_CHAIN" },
        "email": { "L1": true, "L2": true, "L3": true, "L4": true, "pattern": "FULL_CHAIN" },
        "avatar": { "L1": true, "L2": false, "L3": true, "L4": true, "pattern": "DTO_SKIP" },
        "password": { "L1": false, "L2": false, "L3": true, "L4": true, "pattern": "BACKEND_ONLY" },
        "oldEmail": { "L1": false, "L2": false, "L3": false, "L4": true, "pattern": "DB_ORPHAN" }
      },
      "pattern_summary": { "FULL_CHAIN": 10, "DTO_SKIP": 1, "BACKEND_ONLY": 2, "DB_ORPHAN": 1 }
    },
    "order": {
      "fields": {
        "orderAmount": { "L1": true, "L2": true, "L3": true, "L4": true, "pattern": "FULL_CHAIN" },
        "totalPrice": { "L1": true, "L2": true, "L3": true, "L4": true, "pattern": "FULL_CHAIN" },
        "refundNote": { "L1": true, "L2": true, "L3": false, "L4": true, "pattern": "ORM_SKIP" }
      },
      "pattern_summary": { "FULL_CHAIN": 16, "ORM_SKIP": 1, "UI_MISSING": 2 }
    }
  },
  "global_summary": {
    "total_fields": 87,
    "FULL_CHAIN": 65,
    "DTO_SKIP": 2,
    "ORM_SKIP": 1,
    "UI_MISSING": 8,
    "BACKEND_ONLY": 4,
    "DB_ORPHAN": 3,
    "COMPUTED": 3,
    "DTO_ONLY": 1
  }
}
```

---

### 对话中报告摘要模板（强制输出）

分析完成后，**必须**在对话中直接展示以下格式的完整报告。不能只说"报告已保存"或只给统计数字。

````
## 字段一致性检查报告

> 分析时间: {ISO timestamp}
> 分析范围: {模块数} 个模块, {scope} 模式
> 字段总数: L1={n} / L2={n} / L3={n} / L4={n}
> 技术栈: 前端 {framework} / 后端 {backend} / ORM {orm}

### 总览

| 层级对比 | 字段数 | 一致 | 不一致 | 覆盖率 |
|---------|--------|------|--------|--------|
| L1↔L2 (UI↔API)       | xxx | xxx | xxx | xx.x% |
| L2↔L3 (API↔Entity)   | xxx | xxx | xxx | xx.x% |
| L3↔L4 (Entity↔DB)    | xxx | xxx | xxx | xx.x% |

### 全链路矩阵总览（full/backend scope）

| 模块 | 总字段 | 全链路✅ | DTO_SKIP🔴 | ORM_SKIP🔴 | UI_MISSING🟡 | DB_ORPHAN🟡 | BACKEND_ONLY |
|------|--------|---------|-----------|-----------|-------------|------------|-------------|
| 用户管理 | 15 | 10 | 1 | 0 | 1 | 1 | 2 |
| 订单管理 | 22 | 16 | 0 | 1 | 2 | 0 | 3 |

### 🔴 严重问题 (Critical)

| # | 类型 | 模块 | 字段 | L1 | L2 | L3 | L4 | 位置 | 修复建议 |
|---|------|------|------|----|----|----|----|------|---------|
| FC-001 | GHOST (DTO_SKIP) | 用户管理 | avatar | ✅ | ❌ | ✅ | ✅ | UserList.vue:32 → UserResponse 无此字段 | DTO 添加 avatar 字段 |
| FC-002 | TYPO | 订单管理 | orderAmout | ✅ | ✅ | ✅ | ✅ | OrderDTO.java:23 | 修正为 orderAmount |
| FC-004 | GAP | 商品管理 | seoKeywords | ❌ | ❌ | ✅ | ✅ | Product.java:56 → 所有 DTO 未暴露 | ProductDetailResponse 添加 |

### 🟡 警告 (Warning)

| # | 类型 | 模块 | 字段 | 层级 | 位置 | 建议 |
|---|------|------|------|------|------|------|
| FC-003 | STALE | 用户管理 | createdBy | L2↔L1 | API 返回但前端未使用 | 移除或展示 |
| FC-005 | SEMANTIC | 用户管理 | nickname/displayName | L1↔L2 | 前端和 API 命名不同 | 确认是否同一字段 |
| FC-006 | TYPE | 订单管理 | totalPrice | L2↔L1 | number 未格式化 | 前端添加金额格式化 |

### ❓ 需人工确认

| # | 模块 | 字段 | 原因 |
|---|------|------|------|
| FC-005 | 用户管理 | nickname vs displayName | 语义可能相同但无法自动判定，需确认是否指代同一数据 |

### 字段热力图

| 模块 | 🔴 | 🟡 | 总问题 |
|------|-----|-----|--------|
| 用户管理 | 1 | 2 | 3 |
| 订单管理 | 1 | 1 | 2 |
| 商品管理 | 1 | 0 | 1 |
| 其他模块 | 0 | 0 | 0 |

### 下一步建议

1. 优先修复 🔴 Critical — 幽灵字段(GHOST)导致页面显示 undefined，拼写错误(TYPO)导致数据丢失
2. 对 ❓ 需确认项逐个告诉我是否为同一字段
3. STALE 字段建议在下次迭代中清理，减少 API 响应体积
4. 修复后重新运行 `/deadhunt:fieldcheck` 验证

> 完整报告: `.allforai/deadhunt/output/field-analysis/field-report.md`
> 问题清单: `.allforai/deadhunt/output/field-analysis/field-issues.json`
> 字段映射: `.allforai/deadhunt/output/field-analysis/field-mapping.json`
> 字段矩阵: `.allforai/deadhunt/output/field-analysis/field-matrix.json`
````

**关键：摘要必须包含具体的问题列表和修复建议，不能只给统计数字。用户看完摘要就能知道出了什么问题、在哪里、怎么修。**


### 来源文件：`docs/phase0-analyze.md`

## Phase 0: 项目分析

> 先理解项目，再做验证。这是最关键的一步。

### 0.1 识别技术栈

执行以下命令来判断项目类型：

```bash
# 检查 package.json 确定前端框架
cat package.json | jq '.dependencies, .devDependencies' 2>/dev/null

# 检查是否为 monorepo
ls -la packages/ apps/ 2>/dev/null

# 检查路由配置文件位置
find . -maxdepth 5 -type f \( \
  -name "router.*" -o -name "routes.*" -o \
  -name "*.routes.*" -o -name "routing.module.*" \
  -o -name "next.config.*" -o -name "nuxt.config.*" \
  -o -name "app.config.*" \
\) 2>/dev/null | head -30

# 检查 API 路由
find . -maxdepth 5 -type f -path "*/api/*" -name "*.ts" -o -name "*.js" 2>/dev/null | head -30

# 检查菜单/导航配置
grep -rl "menu\|sidebar\|navigation\|nav" --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" --include="*.vue" --include="*.json" -l 2>/dev/null | head -20
```

### 0.2 识别模块类型

将项目中的模块分为以下几类，以确定各自的 CRUD 完整性要求：

| 模块类型 | 描述 | CRUD 要求 | 示例 |
|---------|------|----------|------|
| **标准业务模块** | 核心业务实体 | 完整 CRUD (创建/读取列表/读取详情/更新/删除) | 用户管理、商品管理、订单管理 |
| **配置模块** | 系统配置 | CR(U) — 通常不需要独立删除 | 系统设置、参数配置 |
| **只读模块** | 日志/审计/报表 | R 只读（列表 + 详情/导出） | 操作日志、审计日志、统计报表 |
| **关联模块** | 依附于父模块 | 在父模块内操作，不需要独立入口 | 订单项、评论回复 |
| **工作流模块** | 有状态流转 | CRUD + 状态操作（审批/驳回等） | 审批流、工单 |
| **认证模块** | 登录/注册 | 专用流程，不套用 CRUD | 登录、注册、找回密码 |
| **跨端协作模块** | CRUD 分布在多个客户端 | 按当前端的职责判定，见 0.3 节 | 用户反馈(App创建+后台管理)、UGC内容 |

### 0.3 多端架构感知 (Multi-Client Architecture)

> **核心概念**：一个业务模块的完整 CRUD 可能分布在多个客户端上，每个客户端只承担一部分职责。验证时必须以"当前客户端应承担的职责"为基准，而不是盲目要求完整 CRUD。

#### 架构类型

首先识别项目属于哪种多端架构：

| 架构类型 | 描述 | 示例 |
|---------|------|------|
| **单前端 + 单后端** | 最简单，直接验证完整 CRUD | 一个 Admin 后台 |
| **多前端 + 单后端** | 多个前端共享一个 API 后端，按角色分工 | Admin + 商户 + 客户 H5 + 客户 App |
| **多前端 + 多后端(BFF)** | 每个前端有自己的 BFF 层 | Admin→admin-api, App→app-api, 共享 core-api |
| **微前端** | 多个子应用组合成一个大应用 | qiankun/Module Federation 架构 |

#### 多前端角色模型

在多前端架构中，每个前端有两个维度的定位：

1. **角色 (role)** — 决定能做什么操作（Admin/商户/客户）
2. **平台 (platform)** — 决定怎么做和做的范围（Web/H5/App/小程序）

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           共享后端 API                                   │
└──┬──────────┬───────────┬──────────┬──────────┬──────────┬─────────────┘
   │          │           │          │          │          │
┌──▼──┐  ┌───▼───┐  ┌────▼───┐ ┌───▼───┐ ┌───▼───┐ ┌───▼────┐
│Admin│  │商户后台│  │客户 Web│ │客户 H5│ │客户App│ │客户小程序│
│后台 │  │       │  │(Vue)  │ │(Vue) │ │(Flut)│ │(原生)  │
└─────┘  └───────┘  └───────┘ └──────┘ └──────┘ └───────┘
角色:超管  角色:商户   角色:客户  角色:客户  角色:客户  角色:客户
平台:web  平台:web   平台:web  平台:h5  平台:app 平台:miniprogram
                    ╰──────── 同角色 peer group ──────────╯
                    核心功能应一致，差异来自平台能力
```

**同角色的多个端构成一个 "peer group"（对等组）**，它们之间：
- **核心业务功能应该一致**（都能下单、都能查看订单、都能评价）
- **平台专属功能允许差异**（App 有推送/扫码/AR，小程序有微信支付/分享，Web 有批量操作）
- **一个端有但对等端没有的核心功能 = 大概率缺失**

#### 平台能力边界

不同平台有不同的技术能力，某些功能只在特定平台有意义：

| 平台能力 | Web (PC) | H5 (移动浏览器) | App (Flutter/RN/原生) | 小程序 |
|---------|----------|----------------|---------------------|--------|
| 文件上传/下载 | ✅ 完整 | ⚠️ 受限 | ✅ 完整 | ⚠️ 受限 |
| 批量操作 | ✅ 适合 | ❌ 屏幕小 | ❌ 屏幕小 | ❌ 屏幕小 |
| 推送通知 | ❌ | ❌ | ✅ | ✅ (订阅消息) |
| 扫码 | ❌ | ⚠️ 需调用摄像头 | ✅ | ✅ |
| 生物识别 | ❌ | ❌ | ✅ | ✅ |
| 支付 | ✅ 网页支付 | ✅ 移动支付 | ✅ 原生支付 | ✅ 微信支付 |
| AR/VR | ❌ | ❌ | ✅ | ❌ |
| 定位 | ⚠️ 精度低 | ✅ | ✅ | ✅ |
| 社交分享 | ⚠️ 链接分享 | ✅ 微信分享 | ✅ 系统分享 | ✅ 微信原生分享 |
| 离线使用 | ❌ | ❌ | ✅ | ⚠️ 有限 |
| 富文本编辑 | ✅ | ⚠️ 体验差 | ⚠️ 体验差 | ❌ |
| 复杂表格/报表 | ✅ | ❌ 不适合 | ❌ 不适合 | ❌ 不适合 |
| 键盘快捷键 | ✅ | ❌ | ❌ | ❌ |

当某个客户端缺少某功能时，需要区分：
- **平台不支持** → 正常，不报问题（如 Web 端没有扫码功能）
- **平台支持但没做** → 如果对等端有，大概率是缺失

每种角色对同一模块的 CRUD 期望不同：

| 模块 | Admin 后台 | 商户后台 | 客户 Web | 客户 H5 | 客户 App | 客户小程序 |
|------|-----------|---------|---------|---------|---------|----------|
| 商品 | CRUD+审核 | CRU(自己的) | R | R | R+AR | R |
| 订单 | RUD+退款 | R+发货 | CR+取消 | CR+取消 | CR+取消 | CR+取消 |
| 评价 | RD(审核) | R+回复 | CR | CR | CR | CR |
| 个人中心 | — | RU(自己) | RU | RU | RU+生物识别 | RU |
| 消息通知 | CRUD | R | R | R | R+推送 | R+订阅消息 |

#### 角色默认期望模板

当无法精确判断时，按角色类型给出默认期望：

```json
{
  "role_defaults": {
    "super_admin": {
      "description": "超级管理员后台，全局管理所有数据",
      "default_crud": {
        "standard":  { "C": true,  "R": true,  "U": true,  "D": true  },
        "config":    { "C": true,  "R": true,  "U": true,  "D": false },
        "readonly":  { "C": false, "R": true,  "U": false, "D": false },
        "workflow":  { "C": false, "R": true,  "U": true,  "D": true, "extra": ["审批","驳回"] }
      },
      "notes": "Admin 通常有最完整的 CRUD，但某些用户产生的数据(评价/反馈)通常不需要新增入口"
    },
    "merchant": {
      "description": "商户/租户后台，管理自己名下的数据",
      "default_crud": {
        "standard":  { "C": true,  "R": true,  "U": true,  "D": "maybe" },
        "config":    { "C": false, "R": true,  "U": true,  "D": false },
        "readonly":  { "C": false, "R": true,  "U": false, "D": false }
      },
      "notes": "商户通常能创建和编辑自己的数据，但删除权可能受限；看不到其他商户的数据",
      "scope_filter": "数据隔离：只能操作自己的数据"
    },
    "customer_web": {
      "description": "C 端用户 Web/H5 前端",
      "default_crud": {
        "standard":  { "C": "maybe", "R": true,  "U": "maybe", "D": false },
        "config":    { "C": false,   "R": false, "U": false,   "D": false },
        "readonly":  { "C": false,   "R": true,  "U": false,   "D": false }
      },
      "notes": "用户端以浏览和下单为主，创建操作限于订单/评价/反馈等用户行为数据"
    },
    "customer_app": {
      "description": "C 端用户移动 App (Flutter/RN/原生)",
      "default_crud": {
        "standard":  { "C": "maybe", "R": true,  "U": "maybe", "D": false },
        "config":    { "C": false,   "R": false, "U": false,   "D": false },
        "readonly":  { "C": false,   "R": true,  "U": false,   "D": false }
      },
      "notes": "与 customer_web 类似，但可能有推送、扫码等 App 专有功能"
    }
  }
}
```

> **`"maybe"` 表示需要根据具体模块判断**，不能一刀切。例如用户端的"订单"模块需要 Create（下单），但"商品"模块不需要 Create。

#### 检测方法

**Step 1: 识别所有前端项目**

```bash
# 检查 monorepo 中的多个前端
ls -d packages/*/  apps/*/ 2>/dev/null

# 通过目录名和 package.json 中的 name 字段识别角色
for dir in apps/*/  packages/*/; do
  if [ -f "$dir/package.json" ]; then
    name=$(cat "$dir/package.json" | jq -r '.name // empty')
    echo "$dir -> $name"
  fi
done

# 常见命名模式:
#   admin / dashboard / management   → super_admin
#   merchant / seller / vendor / shop → merchant
#   client / customer / h5 / mobile / web / wap / m → customer_web
#   app / flutter / rn              → customer_app

# 检查是否有 Flutter 项目
find . .. -maxdepth 4 -name "pubspec.yaml" 2>/dev/null

# 检查是否有小程序项目
find . .. -maxdepth 4 -name "project.config.json" 2>/dev/null

# 检查是否有 React Native 项目
find . .. -maxdepth 4 -name "react-native.config.js" 2>/dev/null

# 关键信号：多个前端指向同一个 API
grep -r "baseURL\|BASE_URL\|API_URL\|apiPrefix" \
  --include="*.ts" --include="*.js" --include="*.dart" --include="*.env*" \
  . 2>/dev/null | head -30
```

**Step 2: 识别 API 前缀分段**

很多项目通过 API 路径前缀区分不同角色的接口：

```bash
# 常见 API 前缀分段模式
# /admin/xxx    → Admin 后台专用接口
# /merchant/xxx → 商户后台专用接口
# /api/xxx      → C 端通用接口
# /app/xxx      → App 端专用接口
# /open/xxx     → 开放接口(无需登录)

# 从后端代码中提取 API 分组
grep -rn "@Controller\|@RequestMapping\|@RestController\|router\.\|app\.\(use\|get\|post\)" \
  --include="*.ts" --include="*.java" --include="*.py" --include="*.go" \
  server/ backend/ api/ 2>/dev/null | \
  grep -oP "['\"]/(admin|merchant|seller|vendor|api|app|open|client|h5|web)/[^'\"]*['\"]" | \
  sort -u

# 从 Swagger/OpenAPI 提取 tags 或 paths 分组
cat swagger.json 2>/dev/null | jq '[.paths | keys[] | split("/")[1]] | unique'
```

**Step 3: 从每个前端代码中提取实际调用的 API**

```bash
# 对每个前端分别扫描
for client_dir in apps/admin apps/merchant apps/customer-h5 ../flutter-app; do
  echo "=== $client_dir ==="

  # 提取所有 API 调用路径
  grep -rn "api/\|/admin/\|/merchant/\|/app/" \
    --include="*.ts" --include="*.tsx" --include="*.js" --include="*.dart" \
    "$client_dir" 2>/dev/null | \
    grep -oP "['\"]/?[a-z]+/[^'\"]+['\"]" | sort -u

  # 提取 HTTP 方法
  grep -rn "\.get(\|\.post(\|\.put(\|\.patch(\|\.delete(" \
    --include="*.ts" --include="*.tsx" --include="*.dart" \
    "$client_dir" 2>/dev/null | \
    grep -v "node_modules\|test" | wc -l
done
```

**Step 4: 构建跨端分工矩阵**

将所有前端的 API 调用汇总，按资源和操作生成矩阵：

```
资源        Admin后台    商户后台     客户H5     客户App
─────────────────────────────────────────────────────
orders      CRUD+退款   R+发货      CR+取消    CR+取消
products    CRUD+审核   CRU         R          R
reviews     RD(审核)    R           CR         CR
users       CRUD        R           RU(自己)   RU(自己)
merchants   CRUD        RU(自己)    —          —
coupons     CRUD        CR          R+领取     R+领取
settings    CRUD        —           —          —
```

#### 职责分工判断规则

当无法确定分工时（比如没有其他客户端的代码），按以下优先级推断：

1. **API 前缀分段**是最可靠的信号：
   - `/admin/orders` 只被 admin 前端调用 → Admin 专属
   - `/api/orders` 被所有 C 端调用 → C 端共用
   - `/merchant/orders` 只被商户端调用 → 商户专属

2. **角色默认期望**作为兜底：
   - Admin 后台默认期望完整 CRUD（用户行为数据除外）
   - 商户后台默认期望 CRU 自己的数据
   - C 端默认期望 R + 特定的 C（下单/评价/反馈）

3. **特殊操作的归属规则**：
   - **审核/审批**：通常只在 Admin 或上级角色端
   - **发货/配送**：通常在商户端
   - **下单/支付**：通常在 C 端
   - **退款**：可能在 Admin（强制退款）和 C 端（申请退款）都有
   - **导出**：通常在 Admin 和商户端，C 端少见
   - **软删除 vs 硬删除**：C 端可能有"取消"(软删除)，Admin 有"删除"(硬删除)

4. **同功能多端的情况**：
   - 客户 H5 和客户 App 通常功能高度一致
   - 如果 H5 有某功能但 App 没有（或反之），大概率是缺失而非分工

5. **不确定的一律标记为 `needs_confirmation`**，让用户确认

### 0.4 输出项目概况文件

分析完成后，生成 `validation-profile.json`：

```json
{
  "project": {
    "name": "XX电商平台",
    "architecture": "multi_frontend_single_backend",
    "api_style": "rest",
    "api_base": "https://api.example.com",
    "api_doc": "https://api.example.com/swagger",
    "is_monorepo": true
  },
  "clients": [
    {
      "id": "admin",
      "name": "Admin 管理后台",
      "role": "super_admin",
      "platform": "web",
      "peer_group": null,
      "framework": "react",
      "ui_library": "antd",
      "router": "react-router",
      "path": "apps/admin",
      "api_prefix": "/admin",
      "run_url": "http://localhost:3000",
      "validate": true,
      "validate_method": "playwright",
      "auth": {
        "method": "form",
        "login_url": "/login",
        "credentials": { "username": "superadmin", "password": "xxx" }
      }
    },
    {
      "id": "merchant",
      "name": "商户后台",
      "role": "merchant",
      "platform": "web",
      "peer_group": null,
      "framework": "vue",
      "ui_library": "element-plus",
      "router": "vue-router",
      "path": "apps/merchant",
      "api_prefix": "/merchant",
      "run_url": "http://localhost:3001",
      "validate": true,
      "validate_method": "playwright",
      "auth": {
        "method": "form",
        "login_url": "/login",
        "credentials": { "username": "test_merchant", "password": "xxx" }
      }
    },
    {
      "id": "customer_web",
      "name": "客户 PC 网站",
      "role": "customer",
      "platform": "web",
      "peer_group": "customer",
      "framework": "vue",
      "ui_library": "element-plus",
      "router": "vue-router",
      "path": "apps/web",
      "api_prefix": "/api",
      "run_url": "http://localhost:3002",
      "validate": true,
      "validate_method": "playwright",
      "auth": {
        "method": "form",
        "login_url": "/login",
        "credentials": { "username": "test_customer", "password": "xxx" }
      },
      "platform_capabilities": ["batch_ops", "rich_editor", "keyboard_shortcuts", "file_download"],
      "platform_limitations": ["no_push", "no_scan", "no_biometric"]
    },
    {
      "id": "customer_h5",
      "name": "客户 H5 (移动端)",
      "role": "customer",
      "platform": "h5",
      "peer_group": "customer",
      "framework": "vue",
      "ui_library": "vant",
      "router": "vue-router",
      "path": "apps/h5",
      "api_prefix": "/api",
      "run_url": "http://localhost:3003",
      "validate": true,
      "validate_method": "playwright",
      "auth": {
        "method": "form",
        "login_url": "/login",
        "credentials": { "username": "test_customer", "password": "xxx" }
      },
      "platform_capabilities": ["wechat_share", "mobile_pay", "geolocation"],
      "platform_limitations": ["no_push", "no_scan", "no_batch_ops", "no_rich_editor"]
    },
    {
      "id": "customer_app",
      "name": "客户 App (Flutter)",
      "role": "customer",
      "platform": "app",
      "peer_group": "customer",
      "framework": "flutter",
      "path": "../flutter-app",
      "api_prefix": "/app",
      "validate": true,
      "validate_method": "patrol",
      "platform_capabilities": ["push", "scan", "biometric", "ar", "offline", "native_pay", "camera"],
      "platform_limitations": ["no_batch_ops", "no_rich_editor"],
      "notes": "Flutter 端使用 Patrol 做深度测试，flutter_test 做单元测试"
    },
    {
      "id": "customer_mp",
      "name": "客户微信小程序",
      "role": "customer",
      "platform": "miniprogram",
      "peer_group": "customer",
      "framework": "taro",
      "path": "apps/miniprogram",
      "api_prefix": "/api",
      "validate": true,
      "validate_method": "miniprogram_automator",
      "platform_capabilities": ["wechat_pay", "subscribe_msg", "scan", "share", "geolocation"],
      "platform_limitations": ["no_push", "no_batch_ops", "no_rich_editor", "no_ar", "limited_file"]
    }
  ],
  "modules": [
    {
      "name": "商品",
      "api_resource": "products",
      "type": "standard",
      "crud_by_client": {
        "admin": {
          "route": "/products",
          "menu_path": "商品管理 > 商品列表",
          "crud": { "C": true, "R": true, "U": true, "D": true },
          "extra_actions": ["审核上架", "批量导入", "导出"],
          "notes": ""
        },
        "merchant": {
          "route": "/products",
          "menu_path": "我的商品",
          "crud": { "C": true, "R": true, "U": true, "D": false },
          "extra_actions": ["上下架"],
          "notes": "商户只能管理自己的商品，不能硬删除，只能下架"
        },
        "customer_web": {
          "route": "/products",
          "crud": { "C": false, "R": true, "U": false, "D": false },
          "extra_actions": ["收藏", "加购物车", "对比"],
          "notes": "PC 端可做商品对比（平台专属：大屏适合对比）"
        },
        "customer_h5": {
          "route": "/products",
          "crud": { "C": false, "R": true, "U": false, "D": false },
          "extra_actions": ["收藏", "加购物车", "分享到微信"],
          "notes": "H5 有微信分享（平台专属）"
        },
        "customer_app": {
          "route": "/products",
          "crud": { "C": false, "R": true, "U": false, "D": false },
          "extra_actions": ["收藏", "加购物车", "AR 预览", "扫码搜索"],
          "notes": "App 有 AR 预览和扫码（平台专属）"
        },
        "customer_mp": {
          "route": "/products",
          "crud": { "C": false, "R": true, "U": false, "D": false },
          "extra_actions": ["收藏", "加购物车", "分享"],
          "notes": "小程序有原生微信分享"
        }
      }
    },
    {
      "name": "订单",
      "api_resource": "orders",
      "type": "workflow",
      "crud_by_client": {
        "admin": {
          "route": "/orders",
          "menu_path": "订单管理 > 订单列表",
          "crud": { "C": false, "R": true, "U": true, "D": true },
          "extra_actions": ["强制退款", "备注", "导出"],
          "notes": "Admin 不创建订单，只管理和处理异常"
        },
        "merchant": {
          "route": "/orders",
          "menu_path": "订单管理",
          "crud": { "C": false, "R": true, "U": false, "D": false },
          "extra_actions": ["发货", "确认收款"],
          "notes": "商户只能查看和发货自己的订单"
        },
        "customer_h5": {
          "route": "/orders",
          "crud": { "C": true, "R": true, "U": false, "D": false },
          "extra_actions": ["取消订单", "申请退款", "确认收货", "评价"],
          "notes": "用户下单和管理自己的订单"
        },
        "customer_app": {
          "route": "/orders",
          "crud": { "C": true, "R": true, "U": false, "D": false },
          "extra_actions": ["取消订单", "申请退款", "确认收货", "评价"],
          "notes": "同 H5"
        }
      }
    },
    {
      "name": "用户评价",
      "api_resource": "reviews",
      "type": "standard",
      "crud_by_client": {
        "admin": {
          "route": "/reviews",
          "menu_path": "运营管理 > 评价管理",
          "crud": { "C": false, "R": true, "U": false, "D": true },
          "extra_actions": ["审核", "置顶"],
          "notes": "Admin 不创建评价，只审核和删除"
        },
        "merchant": {
          "route": "/reviews",
          "menu_path": "评价管理",
          "crud": { "C": false, "R": true, "U": false, "D": false },
          "extra_actions": ["回复"],
          "notes": "商户只能查看和回复自己商品的评价"
        },
        "customer_h5": {
          "route": null,
          "crud": { "C": true, "R": true, "U": true, "D": true },
          "extra_actions": [],
          "notes": "用户在订单详情中评价，评价列表在商品详情中"
        },
        "customer_app": {
          "route": null,
          "crud": { "C": true, "R": true, "U": true, "D": true },
          "extra_actions": [],
          "notes": "同 H5"
        }
      }
    },
    {
      "name": "操作日志",
      "api_resource": "audit_logs",
      "type": "readonly",
      "crud_by_client": {
        "admin": {
          "route": "/system/logs",
          "menu_path": "系统管理 > 操作日志",
          "crud": { "C": false, "R": true, "U": false, "D": false },
          "extra_actions": ["导出"],
          "notes": "全局日志，只读"
        },
        "merchant": {
          "route": "/logs",
          "menu_path": "操作记录",
          "crud": { "C": false, "R": true, "U": false, "D": false },
          "notes": "只能看自己的操作记录"
        },
        "customer_h5": null,
        "customer_app": null
      }
    }
  ],
  "validation_scope": {
    "mode": "single|batch|all",
    "target_clients": ["admin"],
    "notes": "可以一次验证一个端，也可以批量验证多个端"
  }
}
```

**重要**：生成后需要请用户确认和补充，特别是：
- 每个前端的测试账号信息
- 每个模块在每个端的 CRUD 分工是否正确（**这是误判的最大来源**）
- 哪些前端需要验证，哪些跳过（如 Flutter 需要单独的测试方案）
- 模块分类是否正确

#### 批量验证模式

当需要验证多个前端时，skill 支持三种模式：

```
# 模式 1: 单端验证（默认）
请验证 admin 后台。项目路径 /path/to/project。

# 模式 2: 批量验证指定端
请验证 admin 后台和商户后台。项目路径 /path/to/project。

# 模式 3: 全端验证
请验证所有可验证的前端。项目路径 /path/to/project。
```

批量模式下，每个前端独立执行完整的验证流程，最终生成一份汇总报告，包含：
- 每个端的独立结果
- 跨端一致性检查（如 H5 有的功能 App 是否也有）
- 全局覆盖率（所有端合计是否覆盖了模块的完整 CRUD）


### 来源文件：`docs/phase1-static.md`

## Phase 1: 静态分析

> 不运行应用，仅通过代码分析发现问题。
> **核心原则：双向分析**

```
方向 A: 界面 → 数据 (Forward)          方向 B: 数据 → 界面 (Reverse)
"界面上有的，后面能通吗？"              "后端有的，界面上找得到吗？"

 菜单入口 ──→ 路由存在？                 API 端点 ──→ 有前端调用？
 链接跳转 ──→ 目标有效？                 路由定义 ──→ 有菜单/按钮指向？
 按钮操作 ──→ API 存在？                 数据库表 ──→ 有对应管理界面？
 表单提交 ──→ 后端处理？                 后端权限 ──→ 前端有对应控制？

两方向交叉得出四种状态：
┌──────────────┬──────────────────┬─────────────────────┐
│              │ 数据层存在        │ 数据层不存在          │
├──────────────┼──────────────────┼─────────────────────┤
│ 界面有入口    │ ✅ 健康           │ 🔴 死链 (点了就 404)  │
│ 界面无入口    │ 🔴 幽灵功能       │ ✅ 正常 (未实现)      │
│              │ (不可达的功能)     │                     │
└──────────────┴──────────────────┴─────────────────────┘
```

### 1.1 方向 A（界面→数据）: 路由完整性分析

**目标**：找出所有注册的路由，与菜单/导航配置做交叉对比。

```bash
# 策略根据框架不同而异，以下是通用模式：

# React Router (v6)
grep -rn "path:" --include="*.tsx" --include="*.ts" --include="*.jsx" src/
grep -rn "<Route" --include="*.tsx" --include="*.jsx" src/

# Vue Router
grep -rn "path:" --include="*.ts" --include="*.js" src/router/

# Next.js (file-based routing)
find app/ pages/ -name "page.tsx" -o -name "page.jsx" -o -name "*.tsx" -path "*/pages/*" 2>/dev/null

# Angular
grep -rn "path:" --include="*.ts" -l src/app/ | xargs grep "path:"
```

输出：`static-analysis/routes.json`
```json
{
  "registered_routes": [
    { "path": "/users", "component": "UserList", "file": "src/pages/users/index.tsx" },
    { "path": "/users/create", "component": "UserCreate", "file": "src/pages/users/create.tsx" },
    { "path": "/users/:id", "component": "UserDetail", "file": "src/pages/users/[id].tsx" }
  ],
  "menu_entries": [
    { "path": "/users", "label": "用户管理", "parent": "系统管理" }
  ],
  "orphan_routes": [
    { "path": "/users/create", "reason": "路由已注册但无菜单入口" }
  ],
  "dead_menu_entries": [
    { "path": "/reports/daily", "reason": "菜单配置了但无对应组件" }
  ]
}
```

### 1.2 方向 A（界面→数据）: 链接目标有效性

```bash
# 找出代码中所有的路由跳转目标
grep -rn "navigate\|push\|replace\|href\|to=" --include="*.tsx" --include="*.ts" --include="*.vue" --include="*.jsx" src/ | \
  grep -oP "(to|href|navigate\(|push\()[\s\"'=]*[\"'](/[^\"']+)[\"']" | sort -u

# 与注册路由做对比，找出跳转目标不存在的死链
```

输出：`static-analysis/link-targets.json`

### 1.3 方向 A（界面→数据）: CRUD 完整性检查

对每个标准业务模块，检查是否存在：

| 操作 | 常见代码模式 |
|------|-------------|
| Create (新增) | 新增按钮、`/xxx/create` 路由、`<XxxForm>` 组件、`POST /api/xxx` |
| Read List (列表) | 列表页、`/xxx` 路由、`<XxxList>` 或 `<XxxTable>` 组件、`GET /api/xxx` |
| Read Detail (详情) | 详情页、`/xxx/:id` 路由、`<XxxDetail>` 组件、`GET /api/xxx/:id` |
| Update (编辑) | 编辑按钮、`/xxx/:id/edit` 路由或编辑弹窗、`PUT/PATCH /api/xxx/:id` |
| Delete (删除) | 删除按钮/确认框、`DELETE /api/xxx/:id` |

```bash
# 对每个模块搜索代码中的 CRUD 模式
MODULE="user"

# 检查新增入口
grep -rn "新增\|添加\|create\|Create\|Add\|add" --include="*.tsx" --include="*.vue" src/ | grep -i "$MODULE"

# 检查删除入口
grep -rn "删除\|delete\|Delete\|remove\|Remove" --include="*.tsx" --include="*.vue" src/ | grep -i "$MODULE"

# 检查 API 调用
grep -rn "POST\|PUT\|PATCH\|DELETE" --include="*.ts" --include="*.js" src/ | grep -i "$MODULE"
```

输出：`static-analysis/crud-coverage.json`

### 1.4 方向 B（数据→界面）: API 端点反向覆盖分析

> **这是发现"幽灵功能"的关键步骤。**
> 后端已经提供了 API，但前端没有任何地方调用它 → 要么是前端漏做了，要么是废弃 API。

```bash
# ============================================
# Step 1: 提取后端所有 API 端点
# ============================================

# 从 Swagger/OpenAPI 文档
cat swagger.json | jq -r '.paths | to_entries[] | "\(.value | keys[]) \(.key)"' | sort

# 从 NestJS 后端代码
grep -rn "@Get\|@Post\|@Put\|@Patch\|@Delete" --include="*.ts" \
  server/src/ 2>/dev/null | \
  grep -oP "@(Get|Post|Put|Patch|Delete)\(['\"]([^'\"]*)['\"]" | sort -u

# 从 Express 后端代码
grep -rn "router\.\(get\|post\|put\|patch\|delete\)" --include="*.ts" --include="*.js" \
  server/ 2>/dev/null | \
  grep -oP "\.(get|post|put|patch|delete)\(['\"]([^'\"]*)['\"]" | sort -u

# 从 Spring Boot
grep -rn "@GetMapping\|@PostMapping\|@PutMapping\|@DeleteMapping" --include="*.java" \
  server/src/ 2>/dev/null | \
  grep -oP "@\w+Mapping\(['\"]([^'\"]*)['\"]" | sort -u

# ============================================
# Step 2: 提取前端所有 API 调用
# ============================================

# 从前端 API 定义文件（通常集中在 src/api/ 或 src/services/）
grep -rn "get(\|post(\|put(\|patch(\|delete(" --include="*.ts" --include="*.js" \
  src/api/ src/services/ 2>/dev/null | \
  grep -oP "(get|post|put|patch|delete)\(['\"]([^'\"]*)['\"]" | sort -u

# 如果前端代码是 OpenAPI generator / swagger-codegen，直接找生成的文件
find src/ -name "*.api.ts" -o -name "*Api.ts" -o -name "*Service.ts" 2>/dev/null

# ============================================
# Step 3: 差集 = 后端有但前端没调用的 API
# ============================================
# backend_apis.txt - frontend_apis.txt = ghost_apis.txt
```

输出：`static-analysis/api-reverse-coverage.json`
```json
{
  "backend_api_count": 87,
  "frontend_call_count": 72,
  "coverage_rate": "82.7%",
  "ghost_apis": [
    {
      "method": "DELETE",
      "path": "/admin/coupons/batch",
      "backend_file": "server/src/modules/coupon/coupon.controller.ts:45",
      "severity": "high",
      "analysis": "后端有批量删除优惠券接口，但前端没有任何地方调用",
      "possible_reason": "前端漏做 | 废弃接口 | 计划中功能",
      "needs_confirmation": true
    },
    {
      "method": "GET",
      "path": "/admin/users/export",
      "backend_file": "server/src/modules/user/user.controller.ts:78",
      "severity": "medium",
      "analysis": "后端有用户导出接口，但前端没有导出按钮",
      "possible_reason": "前端漏做导出功能",
      "needs_confirmation": true
    },
    {
      "method": "PUT",
      "path": "/api/user/avatar",
      "backend_file": "server/src/modules/user/user.controller.ts:92",
      "severity": "high",
      "analysis": "后端有头像更新接口，但所有客户端都没调用",
      "possible_reason": "所有客户端都漏做了头像上传功能",
      "needs_confirmation": true
    }
  ],
  "orphan_frontend_apis": [
    {
      "method": "GET",
      "path": "/admin/dashboard/realtime",
      "frontend_file": "src/api/dashboard.ts:34",
      "severity": "critical",
      "analysis": "前端调用了此接口，但后端没有对应的路由",
      "result": "运行时必然 404"
    }
  ]
}
```

### 1.5 方向 B（数据→界面）: 路由反向可达性分析

> 路由注册了，但界面上没有任何入口（菜单、按钮、链接）能到达。

```bash
# 已注册路由
ROUTES=$(grep -rn "path:" --include="*.ts" src/router/ | grep -oP "path:\s*['\"]([^'\"]+)" | sed "s/path:\s*['\"]//")

# 菜单中引用的路由
MENU_REFS=$(grep -rn "path\|href\|to" --include="*.ts" --include="*.json" src/config/menu* src/layout/ | \
  grep -oP "['\"]/([\w/-]+)['\"]" | sort -u)

# 代码中所有 navigate/push/Link 跳转目标
CODE_REFS=$(grep -rn "navigate\|push\|to=" --include="*.tsx" --include="*.vue" src/ | \
  grep -oP "['\"]/([\w/-]+)['\"]" | sort -u)

# 合并为 UI 层可以到达的路由
ALL_UI_REFS=$(echo -e "$MENU_REFS\n$CODE_REFS" | sort -u)

# 路由存在但 UI 层不可达的 = 幽灵路由
comm -23 <(echo "$ROUTES" | sort) <(echo "$ALL_UI_REFS" | sort)
```

输出：`static-analysis/unreachable-routes.json`
```json
{
  "unreachable_routes": [
    {
      "path": "/products/import",
      "component": "ProductImport",
      "file": "src/pages/products/import.tsx",
      "severity": "high",
      "analysis": "商品导入页面已开发，路由已注册，但界面上没有任何按钮或链接指向此页面",
      "suggestion": "在商品列表页的工具栏添加'导入'按钮"
    },
    {
      "path": "/system/backup",
      "component": "SystemBackup",
      "file": "src/pages/system/backup.tsx",
      "severity": "medium",
      "analysis": "系统备份页面存在但无导航入口",
      "suggestion": "在系统设置菜单下添加'数据备份'入口"
    }
  ]
}
```

### 1.6 方向 B（数据→界面）: 数据模型反向覆盖

> 如果有数据库 schema，检查是否有数据表/模型完全没有对应的管理界面。

```bash
# 从后端 ORM 模型提取实体列表
# Prisma
grep -r "^model " prisma/schema.prisma | awk '{print $2}'

# TypeORM
grep -rn "@Entity" --include="*.ts" server/src/ | grep -oP "name:\s*['\"](\w+)" | sed "s/name:\s*['\"]//g"

# Sequelize
grep -rn "sequelize.define\|Model.init" --include="*.ts" --include="*.js" server/ | grep -oP "['\"](\w+)['\"]" | head -1

# Django
grep -rn "class.*models.Model" --include="*.py" | grep -oP "class\s+(\w+)" | awk '{print $2}'

# 对比前端模块列表，找出没有管理界面的数据实体
```

输出：`static-analysis/model-coverage.json`
```json
{
  "backend_models": ["User", "Product", "Order", "Coupon", "Review", "AuditLog", "SystemConfig", "Notification", "PaymentRecord"],
  "frontend_modules": ["User", "Product", "Order", "Coupon", "Review", "AuditLog", "SystemConfig"],
  "uncovered_models": [
    {
      "model": "Notification",
      "table": "notifications",
      "type": "standard",
      "severity": "high",
      "analysis": "通知表有数据，但后台没有通知管理界面",
      "needs_confirmation": true,
      "possible_reason": "前端漏做 | 通过其他方式管理 | 计划中"
    },
    {
      "model": "PaymentRecord",
      "table": "payment_records",
      "type": "readonly",
      "severity": "medium",
      "analysis": "支付记录表存在但后台没有查看入口",
      "needs_confirmation": true,
      "possible_reason": "应在订单详情中查看 | 需要独立管理页面"
    }
  ]
}
```

### 1.6b Flutter/Dart 静态分析补充

> 当 Phase 0 检测到 Flutter 客户端时（`pubspec.yaml` 存在），对 `.dart` 文件执行以下补充分析。
> 与 Web 端的分析逻辑相同（双向、6 步），但 grep 模式和路由结构不同。

#### Dart 路由提取

```bash
# GoRouter（最常用）
grep -rn "GoRoute\|path:" --include="*.dart" lib/ 2>/dev/null

# auto_route
grep -rn "@RoutePage\|AutoRoute(" --include="*.dart" lib/ 2>/dev/null

# GetX
grep -rn "GetPage(" --include="*.dart" lib/ 2>/dev/null

# Navigator 原生
grep -rn "pushNamed\|Navigator.push\|MaterialPageRoute" --include="*.dart" lib/ 2>/dev/null
```

提取规则：

| 路由库 | 代码模式 | 提取逻辑 |
|--------|---------|---------|
| GoRouter | `GoRoute(path: '/orders', builder: ...)` | 路径 = `/orders`，递归提取 `routes:` 子路由 |
| GoRouter | `GoRoute(path: '/orders/:id')` | 动态路由，`:id` 为参数 |
| auto_route | `AutoRoute(path: '/orders', page: OrderRoute.page)` | 路径 = `/orders`，页面 = `OrderRoute` |
| GetX | `GetPage(name: '/orders', page: () => OrderPage())` | 路径 = `/orders`，页面 = `OrderPage` |
| Navigator | `Navigator.pushNamed(context, '/orders')` | 导航目标 = `/orders` |
| Navigator | `MaterialPageRoute(builder: (_) => OrderPage())` | 导航目标 = `OrderPage` Widget |

#### Dart API 调用提取

```bash
# Dio（最常用）
grep -rn "dio\.\(get\|post\|put\|patch\|delete\)\|\.get(\|\.post(\|\.put(" \
  --include="*.dart" lib/ 2>/dev/null

# Dio baseUrl
grep -rn "baseUrl\|BaseOptions" --include="*.dart" lib/ 2>/dev/null

# http 包
grep -rn "http\.\(get\|post\|put\|patch\|delete\)\|Uri\.parse" \
  --include="*.dart" lib/ 2>/dev/null

# Retrofit 注解
grep -rn "@GET\|@POST\|@PUT\|@PATCH\|@DELETE" --include="*.dart" lib/ 2>/dev/null

# Chopper
grep -rn "@Get\|@Post\|@Put\|@Patch\|@Delete" --include="*.dart" lib/ 2>/dev/null
```

提取规则：

| HTTP 库 | 代码模式 | 提取逻辑 |
|---------|---------|---------|
| Dio | `dio.get('/api/orders')` | 方法 = GET, 路径 = `/api/orders` |
| Dio | `dio.post('/api/orders', data: body)` | 方法 = POST, 路径 = `/api/orders` |
| Retrofit | `@GET('/api/orders')` | 方法 = GET, 路径 = `/api/orders` |
| Retrofit | `@POST('/api/orders')` | 方法 = POST, 路径 = `/api/orders` |
| http | `http.get(Uri.parse('$baseUrl/api/orders'))` | 方法 = GET, 需拼接 baseUrl |

#### Dart Widget 导航链

```bash
# GoRouter 编程式导航
grep -rn "context\.go\|context\.push\|context\.replace\|GoRouter\.of" \
  --include="*.dart" lib/ 2>/dev/null

# GetX 编程式导航
grep -rn "Get\.to\|Get\.toNamed\|Get\.off\|Get\.offNamed" \
  --include="*.dart" lib/ 2>/dev/null

# auto_route 编程式导航
grep -rn "AutoRouter\.of\|context\.router\.push\|context\.pushRoute" \
  --include="*.dart" lib/ 2>/dev/null

# Navigator 原生
grep -rn "Navigator\.\(push\|pop\|pushReplacement\|pushNamed\)" \
  --include="*.dart" lib/ 2>/dev/null
```

#### Dart 状态管理层扫描

> 追踪数据从 API 到 UI 的流动路径，辅助发现 Ghost Features。

```bash
# Provider / Riverpod
grep -rn "ChangeNotifierProvider\|StateNotifierProvider\|FutureProvider\|StreamProvider\|ref\.watch\|ref\.read" \
  --include="*.dart" lib/ 2>/dev/null

# Bloc / Cubit
grep -rn "BlocProvider\|BlocBuilder\|BlocListener\|emit(\|Cubit<" \
  --include="*.dart" lib/ 2>/dev/null

# GetX
grep -rn "GetxController\|\.obs\|Obx(\|GetBuilder" \
  --include="*.dart" lib/ 2>/dev/null
```

| 状态管理 | 数据流模式 | 分析方式 |
|---------|-----------|---------|
| Riverpod | `Provider` → `ref.watch` → Widget | 追踪 Provider 中的 API 调用，检查 Widget 是否消费 |
| Bloc | `Event` → `Bloc.emit(State)` → `BlocBuilder` | 追踪 Event handler 中的 API 调用，检查 State 字段是否被 UI 使用 |
| GetX | `Controller.method()` → `.obs` → `Obx()` | 追踪 Controller 中的 API 调用，检查 `.obs` 变量是否被 `Obx` 包裹 |

### 1.7 权限配置分析

如果项目有权限系统，分析哪些功能被权限控制：

```bash
# 常见权限控制模式
grep -rn "permission\|authorize\|role\|access\|v-permission\|v-auth\|hasPermission\|checkPermission" \
  --include="*.tsx" --include="*.ts" --include="*.vue" --include="*.jsx" src/ | head -50
```

### 1.8 双向分析汇总

所有静态分析完成后，生成汇总矩阵 `static-analysis/bidirectional-matrix.json`：

```json
{
  "summary": {
    "forward_issues": {
      "dead_menu_entries": 3,
      "dead_link_targets": 5,
      "crud_missing_in_ui": 4
    },
    "reverse_issues": {
      "ghost_apis": 8,
      "unreachable_routes": 3,
      "uncovered_models": 2
    },
    "cross_validated": {
      "ui_has_and_data_has": 72,
      "ui_has_but_data_missing": 5,
      "data_has_but_ui_missing": 13,
      "neither_has": 0
    }
  },
  "health_score": {
    "forward": "93.5%",
    "reverse": "84.7%",
    "overall": "89.1%"
  }
}
```

---

## 多轮收敛机制

> 单次分析容易漏掉问题：grep 模式覆盖不全、双向分析缺乏闭环反馈、问题模块的邻居未被排查。
> 收敛机制通过逐轮递进，让每一轮都比上一轮更精准。

### 收敛循环结构

```
Round 1 (基础扫描):  执行上述 1.1 - 1.8 全部步骤，建立 baseline
                      记录 findings 数量 = count_r1
        ↓
Round 2 (模式学习):  从 Round 1 结果提取模式 → 用新模式搜同类问题
                      delta_r2 = 新发现数量
        ↓
Round 3 (交叉验证):  方向A结果反查方向B遗漏，方向B结果反查方向A遗漏
                      delta_r3 = 新发现数量
        ↓
Round 4 (扩散搜索):  对问题模块的关联模块做排查
                      delta_r4 = 新发现数量
        ↓
收敛检查: if (delta_r2 + delta_r3 + delta_r4 > 0) && (iteration < 3)
            → 回到 Round 2，用扩大后的 findings 再来一轮
          else → 收敛完成，输出最终结果到 bidirectional-matrix.json
```

**最大周期数：3**（Round 2-4 为一个周期，最多重复 3 个周期。含 Round 1 基础扫描，总计最多 10 轮）。

每轮的新发现都需要标记 `source` 字段，用于追踪和报告：
- Round 1: `source: "baseline"`
- Round 2: `source: "pattern_learning"`
- Round 3: `source: "cross_validation"`
- Round 4: `source: "diffusion"`

---

### 1.9 Round 2: 模式学习

> 从上轮 findings 中提取模式，用新模式搜索同类问题。
> **只搜索上轮没覆盖到的范围，不重复已检查的内容。**

#### 模式提取规则

对上轮每个 finding，按以下规则提取模式并生成新的搜索动作：

| 发现类型 | 提取的模式 | 新搜索动作 |
|---------|-----------|-----------|
| 死链 `/admin/users/detail` | 路径模式: `/admin/*/detail` | grep 所有匹配 `/admin/.*/detail` 的路由，逐一验证目标是否存在 |
| 幽灵 API `DELETE /api/coupons/batch` | 操作模式: `*/batch` 端点 | grep 所有包含 `batch` 的后端端点，检查前端是否调用 |
| 孤儿路由 `src/pages/reports/daily.tsx` | 目录模式: `reports/` 下所有页面 | 遍历 `reports/` 目录下每个组件文件，检查是否有菜单/链接入口 |
| 动态路由拼接 `navigate('/xxx' + id)` | 代码模式: 字符串拼接路由 | grep `navigate\(.*\+\|navigate\(.*\$\{` 以及 `push\(.*\+\|push\(.*\$\{` 找所有动态拼接的路由 |
| CRUD 缺失: 用户管理缺删除 | CRUD 模式: 某类操作缺失 | 对所有标准业务模块检查是否也缺少同类操作（如：都缺删除？都缺导出？） |
| 404 API 路径含 `/v2/` | 版本模式: API 版本前缀 | grep 所有 `/v2/` 的 API 调用，检查后端是否都支持 v2 |

#### 执行步骤

1. **遍历上轮 findings**，对每个 finding 按上表规则提取模式
2. **去重合并模式**（如多个 findings 都指向同一个路径模式，只搜一次）
3. **对每个模式生成 grep/分析命令**：
   ```bash
   # 示例：路径模式 /admin/*/detail
   grep -rn "path.*admin.*detail\|/admin/[^/]*/detail" --include="*.tsx" --include="*.ts" src/

   # 示例：操作模式 */batch
   grep -rn "batch" --include="*.ts" server/src/ | grep -i "@Get\|@Post\|@Put\|@Delete\|router\."

   # 示例：代码模式 — 字符串拼接路由
   grep -rn "navigate(.*+\|navigate(.*\${\|push(.*+\|push(.*\${" --include="*.tsx" --include="*.ts" src/
   ```
4. **执行搜索**，对每个匹配结果做验证（目标路由是否存在、API 是否被调用）
5. **新发现加入 findings**，标记 `source: "pattern_learning"`
6. **记录 delta_r2** = 本轮新发现数量

---

### 1.10 Round 3: 交叉验证

> 方向 A（界面→数据）和方向 B（数据→界面）的结果互相审查，找出对方的盲区。

#### A → B 反查：用界面侧结果追查数据侧遗漏

对方向 A 的每个 finding，检查方向 B 是否有对应条目：

```
方向A发现死链 /admin/reports/daily
  → 反查方向B: 这个路由对应的后端 API 是什么？
  → grep 后端代码中 "reports" 或 "daily" 相关的 controller/handler
  → 如果方向B没检查到这个 API → 补查
  → 可能发现: 后端有 @Get('reports/daily') 但方向B的 grep 没匹配到（写法差异）

方向A发现 CRUD 缺删除入口
  → 反查方向B: 后端有 DELETE 端点吗？
  → grep "DELETE\|@Delete\|delete(" 在对应模块的 controller 中
  → 有 DELETE 端点 → 前端确实遗漏（加强方向A的结论）
  → 没有 DELETE 端点 → 后端也没做（修正判定：不是前端问题）
```

#### B → A 反查：用数据侧结果追查界面侧遗漏

对方向 B 的每个 finding，检查方向 A 是否有对应条目：

```
方向B发现幽灵 API: POST /api/users/import
  → 反查方向A: 有没有导入按钮？
  → grep "导入\|import\|Import" 在用户管理相关组件中
  → 可能发现: 按钮存在但被 v-if="false" 或 display:none 隐藏了（新问题类型）

方向B发现不可达路由: /products/import
  → 反查方向A: 有没有任何入口指向它？
  → 补查所有间接引用: onClick → navigate('/products/import')
  → 不只查菜单配置，也查按钮点击事件和编程式导航
```

#### 执行步骤

1. 取方向 A 所有 findings → 对每个检查方向 B 是否有对应条目
   - 有对应 → 跳过（已覆盖）
   - 无对应 → 生成反向查询并执行
2. 取方向 B 所有 findings → 对每个检查方向 A 是否有对应条目
   - 同上反向操作
3. 新发现标记 `source: "cross_validation"`
4. 如果交叉验证修正了已有 finding 的判定（如：方向A报"前端缺失"但方向B发现后端也没做），更新该 finding 的 `reason` 和 `action`
5. 记录 delta_r3 = 本轮新发现数量

---

### 1.11 Round 4: 扩散搜索

> 问题会扎堆。一个模块有问题，它的邻居大概率也有。
> 从已知问题点向关联模块扩散排查，**只扩散一层，不递归**。

#### 关联关系定义

对每个问题模块，按以下 5 种关系找到关联模块：

1. **同目录兄弟**
   ```bash
   # src/pages/order/list.tsx 有问题 → 排查 src/pages/order/ 下所有文件
   ls src/pages/order/
   ```

2. **同路由前缀**
   ```bash
   # /admin/order/list 有问题 → 排查所有 /admin/order/* 路由
   grep -rn "path.*admin/order" --include="*.ts" --include="*.tsx" src/
   ```

3. **共享 API 前缀**
   ```bash
   # /api/order/ 相关接口有问题 → 排查所有 /api/order/* 端点
   grep -rn "/api/order" --include="*.ts" src/api/ server/src/
   ```

4. **共享组件**
   ```bash
   # OrderTable 组件关联页面有问题 → 谁还 import 了 OrderTable？
   grep -rn "import.*OrderTable\|from.*OrderTable" --include="*.tsx" --include="*.vue" src/
   ```

5. **同批次修改**
   ```bash
   # 找到问题文件最近的 commit，看同一个 commit 还改了什么
   git log --oneline -1 --format=%H -- src/pages/order/
   git show --name-only <commit_hash> | grep "src/"
   ```

#### 执行步骤

1. 收集所有 Round 1-3 的问题模块，去重得到问题模块列表
2. 对每个问题模块，按上述 5 种关联关系找到关联模块
3. 合并所有关联模块，去重
4. **过滤掉已被 Round 1-3 充分检查过的模块**（避免重复劳动）
5. 对剩余关联模块执行：路由完整性(1.1) + CRUD 覆盖(1.3) + API 反向覆盖(1.4) 检查
6. 新发现标记 `source: "diffusion"`
7. 记录 delta_r4 = 本轮新发现数量

---

### 1.12 收敛追踪

每轮执行完毕后，记录收敛数据到 `static-analysis/convergence.json`：

```json
{
  "phase": "static",
  "max_iterations": 3,
  "rounds": [
    { "round": 1, "cycle": 0, "type": "baseline",         "new_findings": 12, "total": 12 },
    { "round": 2, "cycle": 1, "type": "pattern_learning",  "new_findings": 5,  "total": 17 },
    { "round": 3, "cycle": 1, "type": "cross_validation",  "new_findings": 3,  "total": 20 },
    { "round": 4, "cycle": 1, "type": "diffusion",         "new_findings": 2,  "total": 22 },
    { "round": 5, "cycle": 2, "type": "pattern_learning",  "new_findings": 1,  "total": 23 },
    { "round": 6, "cycle": 2, "type": "cross_validation",  "new_findings": 0,  "total": 23 },
    { "round": 7, "cycle": 2, "type": "diffusion",         "new_findings": 0,  "total": 23 }
  ],
  "converged_at_round": 7,
  "baseline_findings": 12,
  "convergence_bonus": 11,
  "bonus_rate": "91.7%"
}
```

`convergence_bonus` 和 `bonus_rate` 是收敛机制的价值证明——让用户看到"多找几轮"到底多找出了多少。

在 `bidirectional-matrix.json` 的汇总中也加入收敛信息：

```json
{
  "summary": { ... },
  "health_score": { ... },
  "convergence": {
    "total_rounds": 7,
    "baseline_findings": 12,
    "final_findings": 23,
    "bonus_rate": "91.7%"
  }
}
```


### 来源文件：`docs/phase2-plan.md`

## Phase 2: 制定测试计划

基于静态分析的结果，生成测试计划 `test-plan.json`：

```json
{
  "generated_at": "2026-02-16T12:00:00Z",
  "summary": {
    "total_modules": 15,
    "modules_to_test": 12,
    "skipped_modules": 3,
    "estimated_test_cases": 48,
    "static_issues_found": 7
  },
  "test_cases": [
    {
      "id": "TC-001",
      "module": "用户管理",
      "category": "crud_completeness",
      "action": "verify_create_entry",
      "description": "验证用户管理列表页，点击后能否正常打开新增表单",
      "steps": [
        "1. 导航到用户管理页面 /system/users",
        "2. 查找新增/添加按钮",
        "3. 点击按钮",
        "4. 验证打开了新增表单或跳转到新增页面",
        "5. 验证页面返回状态码不是 404/500"
      ],
      "expected": "存在可点击的新增入口，点击后正常展示新增界面",
      "priority": "high",
      "source": "static_analysis|manual"
    },
    {
      "id": "TC-002",
    "module": "全局",
      "category": "dead_link",
      "action": "verify_menu_link",
      "description": "验证菜单'日报管理'链接 /reports/daily 是否有效",
      "steps": [
        "1. 点击侧边栏菜单 '日报管理'",
        "2. 验证页面正常加载",
        "3. 验证不是 404/500/空白页"
      ],
      "expected": "页面正常展示，无 404 错误",
      "priority": "critical",
      "source": "static_analysis"
    }
  ],
  "skip_list": [
    {
      "module": "操作日志",
      "reason": "只读模块，不需要创建/编辑/删除",
      "still_test": ["read_list", "read_detail", "dead_link"]
    }
  ]
}
```

**测试用例生成规则：**

1. **读取 `crud_by_client` 中当前端的配置**，只生成该端应有操作的测试用例
2. 对每个模块，按该端的 `crud` 字段生成对应用例（有 C 则测新增，有 D 则测删除...）
3. 对每个模块的 `extra_actions` 生成额外操作验证用例
4. 对每个**静态分析发现的死链**，生成 1 个链接有效性验证用例
5. 对每个**孤儿路由**，生成 1 个可达性验证用例
6. 对**导航菜单所有入口**，生成遍历测试用例
7. **跨端一致性**（批量模式）：对同角色的不同端（如 H5 vs App），检查功能是否一致
8. **全局覆盖率**（批量模式）：检查所有端合计是否覆盖了 API 提供的所有操作


### 来源文件：`docs/phase3/404-scanner.md`

## 3.2 全局 404 监控器

在所有测试之前，先注入一个全局监控器，捕获**整个测试过程中**的所有 404：

```typescript
import { test, expect, Page, BrowserContext, Response } from '@playwright/test';

// ============================================
// 全局 404 收集器
// ============================================

interface DeadLinkRecord {
  type: 'navigation' | 'api' | 'resource' | 'interaction';
  layer: string;          // 1a, 2a, 3a, 4a, 5a...
  url: string;            // 404 的 URL
  status: number;         // HTTP 状态码
  source_page: string;    // 在哪个页面发现的
  source_element?: string;// 从哪个元素触发的 (如 "侧边栏 > 用户管理")
  resource_type: string;  // document, xhr, fetch, script, stylesheet, image, font
  timestamp: string;
  screenshot?: string;    // 截图文件路径
}

class DeadLinkCollector {
  records: DeadLinkRecord[] = [];
  private apiPatterns: RegExp[] = [];
  private ignorePatterns: RegExp[] = [];

  constructor(options?: {
    apiPatterns?: RegExp[];   // 识别 API 请求的模式，如 /api/, /admin/
    ignorePatterns?: RegExp[]; // 忽略的 URL 模式，如 analytics, hot-update
  }) {
    this.apiPatterns = options?.apiPatterns || [
      /\/api\//i, /\/admin\//i, /\/merchant\//i, /\/v[0-9]+\//i
    ];
    this.ignorePatterns = options?.ignorePatterns || [
      /hot-update/i, /sockjs/i, /__webpack/i, /favicon\.ico/i,
      /analytics/i, /tracking/i, /\.map$/i
    ];
  }

  /** 注入到页面，监听所有网络请求 */
  attach(page: Page, sourcePageName: string) {
    page.on('response', (response: Response) => {
      const url = response.url();
      const status = response.status();

      // 忽略不关心的请求
      if (this.ignorePatterns.some(p => p.test(url))) return;

      // 只关注 4xx 和 5xx
      if (status < 400) return;

      const request = response.request();
      const resourceType = request.resourceType();

      // 分类 404 类型
      let type: DeadLinkRecord['type'];
      let layer: string;

      if (resourceType === 'document') {
        type = 'navigation';
        layer = '1a';  // 会在后续流程中细化
      } else if (resourceType === 'xhr' || resourceType === 'fetch') {
        type = 'api';
        layer = status === 404 ? '3a' : '3b';
      } else if (['script', 'stylesheet', 'font'].includes(resourceType)) {
        type = 'resource';
        layer = resourceType === 'script' ? '4a' :
                resourceType === 'stylesheet' ? '4a' : '4c';
      } else if (resourceType === 'image') {
        type = 'resource';
        layer = '4b';
      } else {
        type = 'resource';
        layer = '4d';
      }

      this.records.push({
        type,
        layer,
        url,
        status,
        source_page: sourcePageName,
        resource_type: resourceType,
        timestamp: new Date().toISOString(),
      });
    });

    // 监听 JS 中的 chunk 加载失败（懒加载路由 404）
    page.on('pageerror', (error) => {
      if (/loading chunk|failed to fetch dynamically imported module|import.*failed/i
            .test(error.message)) {
        this.records.push({
          type: 'resource',
          layer: '4d',
          url: error.message,
          status: 404,
          source_page: sourcePageName,
          resource_type: 'chunk',
          timestamp: new Date().toISOString(),
        });
      }
    });
  }

  /** 生成去重后的报告 */
  report() {
    // 按 URL 去重，保留第一次出现
    const seen = new Set<string>();
    const unique = this.records.filter(r => {
      const key = `${r.status}:${r.url}`;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });

    // 按严重程度排序
    const severityOrder = { navigation: 0, interaction: 1, api: 2, resource: 3 };
    unique.sort((a, b) => severityOrder[a.type] - severityOrder[b.type]);

    return {
      total: unique.length,
      by_type: {
        navigation: unique.filter(r => r.type === 'navigation').length,
        interaction: unique.filter(r => r.type === 'interaction').length,
        api: unique.filter(r => r.type === 'api').length,
        resource: unique.filter(r => r.type === 'resource').length,
      },
      by_status: {
        '404': unique.filter(r => r.status === 404).length,
        '403': unique.filter(r => r.status === 403).length,
        '500': unique.filter(r => r.status >= 500).length,
        'other': unique.filter(r => r.status >= 400 && r.status !== 404 && r.status !== 403 && r.status < 500).length,
      },
      records: unique,
    };
  }
}
```

### 3.3 Layer 1: 导航级 404 扫描

```typescript
test.describe('Layer 1: 导航级 404 扫描', () => {
  let collector: DeadLinkCollector;

  test.beforeAll(() => {
    collector = new DeadLinkCollector();
  });

  // === 1a. 菜单遍历 ===
  test('1a: 遍历所有菜单项', async ({ page }) => {
    await login(page);
    collector.attach(page, '菜单遍历');

    // 展开所有菜单（支持多级折叠菜单）
    const subMenus = await page.locator(
      '.ant-menu-submenu-title, .el-submenu__title, [data-menu-id]'
    ).all();
    for (const sub of subMenus) {
      await sub.click().catch(() => {});
      await page.waitForTimeout(300);
    }

    // 收集所有叶子菜单项
    const menuLinks = await page.locator(
      '[role="menuitem"] a, .ant-menu-item a, .el-menu-item a, ' +
      '.nav-link, .menu-link, [data-menu-leaf]'
    ).all();

    for (const link of menuLinks) {
      const href = await link.getAttribute('href');
      const text = (await link.textContent())?.trim();
      if (!href || href === '#' || href.startsWith('http') || href.startsWith('javascript:')) continue;

      await link.click();
      await page.waitForLoadState('networkidle').catch(() => {});
      await page.waitForTimeout(500);

      // 检查页面状态
      const bodyText = await page.textContent('body').catch(() => '') || '';
      const is404 = /404|not found|页面不存在|page not found/i.test(bodyText);
      const isBlank = bodyText.trim().length < 10;
      const is500 = /500|internal server error|服务器错误/i.test(bodyText);

      if (is404 || isBlank || is500) {
        collector.records.push({
          type: 'navigation',
          layer: '1a',
          url: page.url(),
          status: is404 ? 404 : is500 ? 500 : 0,
          source_page: '侧边栏菜单',
          source_element: `菜单: ${text} → ${href}`,
          resource_type: 'document',
          timestamp: new Date().toISOString(),
          screenshot: `screenshots/menu-${text?.replace(/\s/g, '_')}.png`,
        });
        await page.screenshot({ path: `screenshots/menu-${text?.replace(/\s/g, '_')}.png` });
      }

      // 返回，准备下次点击
      await page.goBack().catch(() => page.goto('/'));
      await page.waitForLoadState('networkidle').catch(() => {});
    }
  });

  // === 1b. 面包屑导航 ===
  test('1b: 检查面包屑导航', async ({ page }) => {
    await login(page);
    collector.attach(page, '面包屑');

    // 先访问几个深层页面
    const deepPages = [/* 从 validation-profile.json 读取 */];
    for (const dp of deepPages) {
      await page.goto(dp);
      await page.waitForLoadState('networkidle').catch(() => {});

      // 找到所有面包屑链接
      const breadcrumbs = await page.locator(
        '.ant-breadcrumb a, .el-breadcrumb__inner a, nav[aria-label="breadcrumb"] a, ' +
        '.breadcrumb a, [class*="breadcrumb"] a'
      ).all();

      for (const crumb of breadcrumbs) {
        const href = await crumb.getAttribute('href');
        const text = (await crumb.textContent())?.trim();
        if (!href || href === '#') continue;

        await crumb.click();
        await page.waitForLoadState('networkidle').catch(() => {});

        const bodyText = await page.textContent('body').catch(() => '') || '';
        if (/404|not found/i.test(bodyText) || bodyText.trim().length < 10) {
          collector.records.push({
            type: 'navigation',
            layer: '1b',
            url: page.url(),
            status: 404,
            source_page: dp,
            source_element: `面包屑: ${text} → ${href}`,
            resource_type: 'document',
            timestamp: new Date().toISOString(),
          });
        }
        await page.goBack().catch(() => {});
      }
    }
  });

  // === 1c. Tab / 子导航 ===
  test('1c: 检查 Tab 切换和子导航', async ({ page }) => {
    await login(page);
    collector.attach(page, 'Tab导航');

    const modulePages = [/* 从 validation-profile.json 读取所有模块路由 */];
    for (const mp of modulePages) {
      await page.goto(mp);
      await page.waitForLoadState('networkidle').catch(() => {});

      // 找所有 Tab
      const tabs = await page.locator(
        '.ant-tabs-tab, .el-tabs__item, [role="tab"], [data-tab]'
      ).all();

      for (const tab of tabs) {
        const text = (await tab.textContent())?.trim();
        await tab.click();
        await page.waitForLoadState('networkidle').catch(() => {});
        await page.waitForTimeout(500);

        const bodyText = await page.textContent('body').catch(() => '') || '';
        if (/404|not found/i.test(bodyText)) {
          collector.records.push({
            type: 'navigation',
            layer: '1c',
            url: page.url(),
            status: 404,
            source_page: mp,
            source_element: `Tab: ${text}`,
            resource_type: 'document',
            timestamp: new Date().toISOString(),
          });
        }
      }
    }
  });
});
```

### 3.4 Layer 2: 页面内交互级 404 扫描

```typescript
test.describe('Layer 2: 页面内交互 404 扫描', () => {
  let collector: DeadLinkCollector;

  // === 2a + 2b. 表格行操作和列表链接 ===
  test('2a/2b: 表格行可点击元素', async ({ page }) => {
    await login(page);
    collector = new DeadLinkCollector();
    collector.attach(page, '表格行操作');

    const listPages = [/* 所有列表页路由 */];
    for (const lp of listPages) {
      await page.goto(lp);
      await page.waitForLoadState('networkidle').catch(() => {});

      // 检查表格是否有数据
      const rows = page.locator('tbody tr, .ant-table-row');
      if (await rows.count() === 0) continue;

      // 收集第一行中所有可点击的元素
      const firstRow = rows.first();
      await firstRow.hover();
      await page.waitForTimeout(300);

      // 行内链接（点击名称跳转详情）
      const rowLinks = await firstRow.locator('a[href]').all();
      for (const link of rowLinks) {
        const href = await link.getAttribute('href');
        const text = (await link.textContent())?.trim();
        if (!href || href === '#' || href.startsWith('javascript:')) continue;

        const currentUrl = page.url();
        await link.click();
        await page.waitForLoadState('networkidle').catch(() => {});
        await page.waitForTimeout(500);

        const bodyText = await page.textContent('body').catch(() => '') || '';
        if (/404|not found|页面不存在/i.test(bodyText) || bodyText.trim().length < 10) {
          collector.records.push({
            type: 'interaction',
            layer: '2b',
            url: page.url(),
            status: 404,
            source_page: lp,
            source_element: `行链接: ${text} → ${href}`,
            resource_type: 'document',
            timestamp: new Date().toISOString(),
          });
          await page.screenshot({
            path: `screenshots/row-link-${lp.replace(/\//g, '_')}-${text}.png`
          });
        }
        await page.goto(currentUrl); // 返回列表
        await page.waitForLoadState('networkidle').catch(() => {});
      }

      // 行内操作按钮（查看、编辑、删除）
      const actionButtons = await firstRow.locator(
        'button, a, .ant-btn, .el-button, [role="button"]'
      ).all();

      for (const btn of actionButtons) {
        const text = (await btn.textContent())?.trim();
        // 跳过删除类按钮（避免误删数据）和不会跳转的按钮
        if (!text || /删除|移除|delete|remove|启用|禁用|enable|disable/i.test(text)) continue;

        const currentUrl = page.url();
        const navPromise = page.waitForNavigation({ timeout: 3000 }).catch(() => null);
        await btn.click().catch(() => {});
        const nav = await navPromise;

        // 如果发生了页面跳转，检查目标页面
        if (nav || page.url() !== currentUrl) {
          const bodyText = await page.textContent('body').catch(() => '') || '';
          if (/404|not found|页面不存在/i.test(bodyText) || bodyText.trim().length < 10) {
            collector.records.push({
              type: 'interaction',
              layer: '2a',
              url: page.url(),
              status: 404,
              source_page: lp,
              source_element: `行操作: "${text}" 按钮`,
              resource_type: 'document',
              timestamp: new Date().toISOString(),
            });
          }
          await page.goto(currentUrl);
          await page.waitForLoadState('networkidle').catch(() => {});
        } else {
          // 没跳转，可能打开了弹窗，关闭它
          await page.keyboard.press('Escape');
          await page.waitForTimeout(300);
        }
      }
    }
  });

  // === 2d. 页头操作按钮 ===
  test('2d: 页头工具栏按钮', async ({ page }) => {
    await login(page);
    collector = new DeadLinkCollector();
    collector.attach(page, '页头操作');

    const listPages = [/* 所有列表页路由 */];
    for (const lp of listPages) {
      await page.goto(lp);
      await page.waitForLoadState('networkidle').catch(() => {});

      // 找页头区域的操作按钮（新增、导入、导出等）
      const headerButtons = await page.locator(
        '.ant-page-header button, .page-header button, ' +
        '.toolbar button, .action-bar button, ' +
        '[class*="header"] button:not(tbody button), ' +
        '[class*="toolbar"] button'
      ).all();

      for (const btn of headerButtons) {
        const text = (await btn.textContent())?.trim();
        if (!text) continue;

        const currentUrl = page.url();
        const navPromise = page.waitForNavigation({ timeout: 3000 }).catch(() => null);
        await btn.click().catch(() => {});
        const nav = await navPromise;

        if (nav || page.url() !== currentUrl) {
          const bodyText = await page.textContent('body').catch(() => '') || '';
          if (/404|not found|页面不存在/i.test(bodyText) || bodyText.trim().length < 10) {
            collector.records.push({
              type: 'interaction',
              layer: '2d',
              url: page.url(),
              status: 404,
              source_page: lp,
              source_element: `页头按钮: "${text}"`,
              resource_type: 'document',
              timestamp: new Date().toISOString(),
            });
          }
          await page.goto(currentUrl);
          await page.waitForLoadState('networkidle').catch(() => {});
        } else {
          await page.keyboard.press('Escape');
          await page.waitForTimeout(300);
        }
      }
    }
  });
});
```

### 3.5 Layer 3: API 级 404 扫描

这一层不需要额外的测试脚本——**全局 DeadLinkCollector 会自动捕获所有 API 404**。
但需要对捕获的 API 404 做分类和优先级判断：

```typescript
function analyzeApi404s(records: DeadLinkRecord[]): AnalyzedRecord[] {
  return records
    .filter(r => r.type === 'api')
    .map(r => {
      // 解析 API 路径
      const urlObj = new URL(r.url);
      const path = urlObj.pathname;

      // 判断严重程度
      let severity: 'critical' | 'high' | 'medium' | 'low';
      let category: string;

      if (/\/list|\/page|\/query|\/search/i.test(path) || r.source_page.includes('列表')) {
        // 列表页加载数据的接口 404 → 严重（页面直接无法使用）
        severity = 'critical';
        category = '列表数据接口 404 — 页面将显示空白或报错';
      } else if (/\/detail|\/info|\/get\/\d+/i.test(path)) {
        // 详情接口 404
        severity = 'high';
        category = '详情接口 404 — 详情页无法显示';
      } else if (/\/create|\/add|\/save|\/update|\/edit|\/delete|\/remove/i.test(path)) {
        // 操作接口 404
        severity = 'high';
        category = '操作接口 404 — 增删改操作将失败';
      } else if (/\/export|\/download|\/upload|\/import/i.test(path)) {
        // 文件操作接口
        severity = 'medium';
        category = '文件操作接口 404';
      } else if (/\/config|\/setting|\/option|\/dict/i.test(path)) {
        // 配置/字典接口
        severity = 'medium';
        category = '配置/字典接口 404 — 下拉框可能为空';
      } else {
        severity = 'medium';
        category = '其他 API 404';
      }

      return { ...r, severity, category };
    });
}
```

### 3.6 Layer 4: 资源级 404 扫描

同样由全局收集器自动捕获。补充一个主动检查：

```typescript
test('Layer 4: 检查页面资源加载', async ({ page }) => {
  await login(page);
  const collector = new DeadLinkCollector();
  collector.attach(page, '资源检查');

  // 遍历所有主要页面
  const allPages = [/* 所有列表页 + 详情页 + 表单页 */];
  for (const p of allPages) {
    await page.goto(p);
    await page.waitForLoadState('networkidle').catch(() => {});

    // 检查页面中的图片是否加载成功
    const brokenImages = await page.evaluate(() => {
      const imgs = document.querySelectorAll('img');
      return Array.from(imgs)
        .filter(img => !img.complete || img.naturalHeight === 0)
        .map(img => img.src);
    });

    for (const src of brokenImages) {
      if (src && !src.startsWith('data:')) {
        collector.records.push({
          type: 'resource',
          layer: '4b',
          url: src,
          status: 404,
          source_page: p,
          source_element: `<img src="${src}">`,
          resource_type: 'image',
          timestamp: new Date().toISOString(),
        });
      }
    }
  }
});
```

### 3.7 Layer 5: 边界情况 404 扫描

```typescript
test.describe('Layer 5: 边界情况', () => {

  // === 5a. 无效动态路由参数 ===
  test('5a: 不存在的 ID 路由', async ({ page }) => {
    await login(page);

    // 对所有带 :id 参数的路由，用不存在的 ID 访问
    const dynamicRoutes = [
      { path: '/users/999999999', name: '不存在的用户' },
      { path: '/orders/999999999', name: '不存在的订单' },
      { path: '/products/999999999', name: '不存在的商品' },
      // ... 从 validation-profile.json 中的路由生成
    ];

    for (const route of dynamicRoutes) {
      await page.goto(route.path);
      await page.waitForLoadState('networkidle').catch(() => {});

      const bodyText = await page.textContent('body').catch(() => '') || '';

      // 应该显示友好的"未找到"提示，而不是 crash/白屏/原始404
      const hasErrorHandling =
        /不存在|未找到|no data|empty|no result/i.test(bodyText) ||
        (await page.locator('.ant-empty, .el-empty, [class*="empty"]').count()) > 0;

      const isCrash =
        bodyText.trim().length < 10 ||
        /cannot read|undefined|null|error/i.test(bodyText);

      if (isCrash) {
        // 白屏或 JS 报错 → 严重
        console.error(`❌ ${route.path}: 白屏或 JS 报错 (无效 ID 未处理)`);
      } else if (!hasErrorHandling) {
        // 没有友好提示 → 警告
        console.warn(`⚠️ ${route.path}: 无效 ID 没有友好提示`);
      }
    }
  });

  // === 5b. 无权限路由 ===
  test('5b: 低权限账号访问受限路由', async ({ page }) => {
    // 用低权限账号登录
    await login(page, 'low_privilege_user', 'password');

    const protectedRoutes = [
      { path: '/system/settings', name: '系统设置 (需 admin)' },
      { path: '/users', name: '用户管理 (需 admin)' },
      // ... 从权限配置中提取
    ];

    for (const route of protectedRoutes) {
      await page.goto(route.path);
      await page.waitForLoadState('networkidle').catch(() => {});

      // 应该重定向到 403 页面或首页，不应该 404
      const bodyText = await page.textContent('body').catch(() => '') || '';
      if (/404|not found/i.test(bodyText)) {
        console.error(`❌ ${route.path}: 无权限时显示 404 而不是 403`);
      }
    }
  });

  // === 5d. 直接 URL 访问（刷新页面） ===
  test('5d: SPA 路由刷新不丢失', async ({ page }) => {
    await login(page);

    const spaRoutes = [/* 所有 SPA 路由 */];
    for (const route of spaRoutes) {
      // 直接在地址栏输入 URL（模拟刷新或分享链接）
      await page.goto(route, { waitUntil: 'networkidle' });

      const bodyText = await page.textContent('body').catch(() => '') || '';
      if (/404|not found/i.test(bodyText) || bodyText.trim().length < 10) {
        // SPA history fallback 没配置，刷新就 404
        console.error(`❌ ${route}: 直接访问 404 — 可能是服务端 history fallback 未配置`);
      }
    }
  });
});
```


### 来源文件：`docs/phase3/convergence.md`

## 多轮收敛机制（深度测试）

> 与 Phase 1 静态分析相同的逐轮递进思想，但驱动方式从 grep 换成浏览器交互。
> 浏览器操作成本更高，因此最大迭代次数为 **2**（1 轮基础 + 最多 2 轮收敛 = 最多 3 轮）。

### 收敛循环结构

```
Round 1 (基础遍历):  执行 3.3 - 3.14 全部步骤（5层扫描 + CRUD + 数据展示）
                      记录 findings 数量 = count_r1
        ↓
Round 2 (模式学习):  从 Round 1 结果提取 URL/交互模式 → 用新模式访问同类页面
                      delta_r2 = 新发现数量
        ↓
Round 3 (交叉验证):  用 Phase 1 静态分析结果反查深度测试遗漏，反之亦然
                      delta_r3 = 新发现数量
        ↓
Round 4 (扩散搜索):  对问题模块的关联模块做完整交互测试（非快速遍历）
                      delta_r4 = 新发现数量
        ↓
收敛检查: if (delta_r2 + delta_r3 + delta_r4 > 0) && (iteration < 2)
            → 回到 Round 2
          else → 收敛完成
```

标记方式同 Phase 1：`source: "pattern_learning" / "cross_validation" / "diffusion"`

---

### 3.15 Round 2: 模式学习（深度测试）

> 从上轮浏览器测试结果中提取 URL 模式和交互模式，对同类页面做补充测试。

#### 模式提取规则

| 发现类型 | 提取的模式 | 新测试动作 |
|---------|-----------|-----------|
| `/order/detail` 页面 404 | URL 模式: `*/detail` | 浏览器直接访问所有 `*/detail` 路由（`/user/detail`, `/product/detail` ...） |
| `/api/order/*` 前缀的 API 全部 404 | API 前缀模式 | 访问所有依赖 `/api/order/*` 的页面，检查是否同样受影响 |
| 某个 UI 框架组件（如 `ant-table`）的操作按钮不可达 | 交互模式: 表格行操作 | 对其他使用同类表格的列表页补充行操作测试 |
| 某页面的面包屑链接 404 | 导航模式: 面包屑 | 补充检查其他深层页面的面包屑是否都可用 |
| 某 chunk 加载 404（懒加载失败） | 资源模式: chunk | 尝试访问所有懒加载路由，检查 chunk 是否都能加载 |

#### 执行步骤

1. 遍历 Round 1 深度测试 findings
2. 按上表提取 URL 模式和交互模式
3. 去重合并，生成新的页面访问列表和交互动作列表
4. **只访问 Round 1 没覆盖到的页面/路由**
5. 对每个新访问的页面，执行 `visitAndCollectAll()`（3.0 中的单次遍历多层收集函数）
6. 新发现标记 `source: "pattern_learning"`

---

### 3.16 Round 3: 交叉验证（深度测试）

> Phase 1 静态分析和 Phase 3 深度测试互相验证，填补对方的盲区。

#### Phase 1 → Phase 3 反查

用静态分析结果驱动深度测试补充：

```
静态分析发现幽灵路由 /products/import
  → 浏览器实际访问此路由，确认页面是否可用
  → 从商品列表页尝试各种交互（点击按钮、展开下拉），看是否有入口

静态分析发现幽灵 API: DELETE /api/coupons/batch
  → 浏览器打开优惠券列表页
  → 尝试勾选多条记录，看是否出现批量操作栏
  → 监听网络请求，检查是否有调用此 API 的交互

静态分析发现 CRUD 缺失: 商品管理缺导入功能
  → 浏览器打开商品列表页
  → 检查工具栏是否有导入按钮（可能被权限/feature flag 隐藏）
```

#### Phase 3 → Phase 1 反哺

深度测试发现的问题反馈给静态分析结果：

```
深度测试发现某按钮点击后 API 404: POST /api/settings/backup
  → 回查 Phase 1 静态分析的 api-reverse-coverage.json
  → 如果静态分析没有标记此 API → 补记到静态分析结果中
  → 说明静态分析的 grep 模式遗漏了这种 API 注册方式

深度测试发现某页面加载时 chunk 404
  → 回查 Phase 1 的 routes.json，检查此路由是否被标记
  → 可能发现路由注册方式是 React.lazy() 动态导入，Phase 1 的 grep 没覆盖
```

#### 执行步骤

1. 读取 Phase 1 的 `static-analysis/` 下所有 JSON 结果
2. 对 Phase 1 发现但 Phase 3 Round 1 未触及的条目：
   - 生成浏览器访问和交互动作
   - 执行测试
3. 对 Phase 3 Round 1 发现但 Phase 1 未标记的条目：
   - 补记到 `static-analysis/` 对应的 JSON 中，具体写入规则：
     - API 404 → 写入 `api-reverse-coverage.json` 的 `orphan_frontend_apis`
     - 路由不可达 → 写入 `unreachable-routes.json`
     - CRUD 缺失 → 写入 `crud-coverage.json`
   - 示例：Phase 3 发现 POST /api/settings/backup 返回 404
     ```json
     // 写入 static-analysis/api-reverse-coverage.json → orphan_frontend_apis[]
     {
       "method": "POST",
       "path": "/api/settings/backup",
       "frontend_file": "src/pages/settings/backup.tsx:42",
       "severity": "critical",
       "analysis": "前端调用了此接口，但后端没有对应路由（Phase 3 浏览器测试发现）",
       "result": "运行时 404",
       "source": "cross_validation_p3"
     }
     ```
4. 新发现标记 `source: "cross_validation"`

---

### 3.17 Round 4: 扩散搜索（深度测试）

> 对问题模块的关联模块做**完整交互测试**，而非 Round 1 的快速遍历。

#### 关联关系（同 Phase 1）

1. 同目录兄弟
2. 同路由前缀
3. 共享 API 前缀
4. 共享组件
5. 同批次修改

#### 与 Phase 1 扩散的区别

Phase 1 扩散搜索只做 grep 分析。Phase 3 扩散搜索用浏览器做完整交互：

| Phase 1 扩散 | Phase 3 扩散 |
|-------------|-------------|
| grep 路由是否注册 | 浏览器实际访问该路由 |
| grep 是否有 CRUD 代码模式 | 浏览器点击新增/编辑/删除按钮 |
| grep API 是否被调用 | 浏览器操作并监听实际 API 请求 |

#### 执行步骤

1. 收集 Round 1-3 所有问题模块
2. 按 5 种关联关系找到关联模块
3. 过滤掉已被 Round 1-3 访问过的模块
4. 对剩余关联模块：
   - 访问页面，执行 `visitAndCollectAll()` 全层收集
   - 如果是列表页，额外测试表格行操作和工具栏按钮
5. 新发现标记 `source: "diffusion"`

---

### 3.18 深度测试收敛追踪

记录到 `reports/convergence-deep.json`：

```json
{
  "phase": "deep",
  "max_iterations": 2,
  "rounds": [
    { "round": 1, "type": "baseline",         "new_findings": 8, "total": 8 },
    { "round": 2, "type": "pattern_learning",  "new_findings": 3, "total": 11 },
    { "round": 3, "type": "cross_validation",  "new_findings": 1, "total": 12 },
    { "round": 4, "type": "diffusion",         "new_findings": 0, "total": 12 }
  ],
  "converged_at_round": 4,
  "baseline_findings": 8,
  "convergence_bonus": 4,
  "bonus_rate": "50%"
}
```

合并到 `dead-links-report.json` 的顶层：

```json
{
  "scan_time": "...",
  "client": "admin",
  "convergence": {
    "total_rounds": 4,
    "baseline_findings": 8,
    "final_findings": 12,
    "bonus_rate": "50%"
  },
  "summary": { ... },
  "records": [ ... ]
}
```

---


### 来源文件：`docs/phase3/intent-classification.md`

### 3.8 死链意图判定 (Intent Classification)

> **发现死链只是第一步，判断它该修还是该删才是关键。**
> 不做意图判定的后果：开发者花两天修复一个"查看详情"按钮，结果发现这个功能早就被产品经理砍掉了。

#### 四种意图分类

```
┌──────────────────────────────────────────────────────────────────────┐
│                    死链意图判定 (Intent)                              │
├──────────┬───────────────────────────────────────────────────────────┤
│ 🔴 FIX   │ 前端/路由坏了 → 修复代码                                  │
│ 🟡 CLEAN │ 功能已废弃/砍掉了，入口残留 → 删除入口                      │
│ 🟠 HIDE  │ 功能开发中/未上线，入口提前暴露 → 隐藏入口                   │
│ 🔵 PERM  │ 当前用户/角色不该看到这个入口 → 修复权限控制                  │
└──────────┴───────────────────────────────────────────────────────────┘
```

#### 判定信号矩阵

通过交叉多个信号来推断意图：

```typescript
interface IntentSignals {
  // —— 后端信号 ——
  api_exists: boolean;           // 后端有对应 API 吗？
  api_returns_data: boolean;     // API 返回了有效数据吗？（不是 404/500）
  db_model_exists: boolean;      // 数据库有对应表/模型吗？
  db_has_data: boolean;          // 表里有数据吗？

  // —— 前端信号 ——
  route_registered: boolean;     // 前端路由注册了吗？
  component_exists: boolean;     // 对应的组件文件存在吗？
  component_is_stub: boolean;    // 组件是占位/空壳？（< 20 行或只有 TODO）
  other_clients_have: boolean;   // 其他客户端有这个功能吗？

  // —— 代码历史信号 ——
  recently_modified: boolean;    // 相关代码最近改过吗？（30 天内）
  has_todo_or_fixme: boolean;    // 代码里有 TODO/FIXME/WIP 注释吗？
  in_feature_branch: boolean;    // 是否在未合并的 feature 分支？
  has_feature_flag: boolean;     // 是否受 feature flag 控制？

  // —— 配置信号 ——
  in_menu_config: boolean;       // 菜单配置里有这个入口吗？
  permission_controlled: boolean;// 入口有权限控制吗？
  disabled_or_hidden_attr: boolean; // 元素有 disabled/hidden/v-if=false？
}
```

#### 判定规则

```typescript
function classifyIntent(link: DeadLinkRecord, signals: IntentSignals): Intent {

  // ═══════════════════════════════════════════
  // 规则 1: FIX (该修) — 后端一切正常，前端坏了
  // ═══════════════════════════════════════════
  if (signals.api_exists && signals.api_returns_data && signals.route_registered
      && signals.component_exists && !signals.component_is_stub) {
    // 后端有数据，前端有组件，路由有注册，但就是 404
    // → 大概率是路由路径拼写问题
    return {
      intent: 'FIX',
      confidence: 'high',
      reason: '后端 API 正常，前端组件存在，路由已注册，但页面 404 — 检查路由配置和路径拼写',
      action: '修复路由配置或路径引用',
    };
  }

  if (signals.api_exists && !signals.api_returns_data && signals.db_model_exists) {
    // API 端点在但返回错误 → 后端 bug
    return {
      intent: 'FIX',
      confidence: 'high',
      reason: 'API 端点存在但返回错误',
      action: '修复后端接口',
    };
  }

  if (signals.other_clients_have) {
    // 其他客户端有这个功能 → 当前客户端应该也有
    return {
      intent: 'FIX',
      confidence: 'high',
      reason: '其他客户端有此功能 — 当前客户端是遗漏',
      action: '补全当前客户端的功能',
    };
  }

  // ═══════════════════════════════════════════
  // 规则 2: CLEAN (该删) — 后端也没有了
  // ═══════════════════════════════════════════
  if (!signals.api_exists && !signals.route_registered) {
    // 后端没 API，前端没路由，但菜单/按钮还在
    return {
      intent: 'CLEAN',
      confidence: 'high',
      reason: '后端无 API，前端无路由 — 纯 UI 残留',
      action: '删除菜单项/按钮/链接',
    };
  }

  if (!signals.api_exists && signals.route_registered
      && signals.component_exists && !signals.recently_modified) {
    // 有路由有组件但后端 API 已删除，且代码很久没动
    return {
      intent: 'CLEAN',
      confidence: 'high',
      reason: '后端 API 已不存在，组件长期未维护 — 废弃功能',
      action: '删除路由、组件和入口',
    };
  }

  if (signals.component_exists && !signals.recently_modified
      && !signals.api_exists && !signals.db_has_data) {
    // 组件存在但后端什么都没有，数据库也没数据
    return {
      intent: 'CLEAN',
      confidence: 'medium',
      reason: '前端有壳但后端完全没有对应实现 — 可能是被砍掉的功能',
      action: '确认后删除相关前端代码',
    };
  }

  // ═══════════════════════════════════════════
  // 规则 3: HIDE (该藏) — 开发中，还没做完
  // ═══════════════════════════════════════════
  if (signals.component_is_stub || signals.has_todo_or_fixme) {
    return {
      intent: 'HIDE',
      confidence: 'high',
      reason: '组件是占位/有 TODO 注释 — 功能开发中',
      action: '用 feature flag 或权限控制隐藏入口，完成后再开放',
    };
  }

  if (signals.recently_modified && signals.in_feature_branch) {
    return {
      intent: 'HIDE',
      confidence: 'high',
      reason: '代码在 feature 分支且最近修改 — 开发中功能提前暴露',
      action: '隐藏入口直到功能完成并合并',
    };
  }

  if (signals.recently_modified && !signals.api_returns_data) {
    return {
      intent: 'HIDE',
      confidence: 'medium',
      reason: '前端最近修改但后端还没跟上 — 前后端开发进度不同步',
      action: '暂时隐藏入口，等后端完成后开放',
    };
  }

  // ═══════════════════════════════════════════
  // 规则 4: PERM (权限问题)
  // ═══════════════════════════════════════════
  if (signals.permission_controlled && signals.api_exists) {
    return {
      intent: 'PERM',
      confidence: 'high',
      reason: 'API 存在且有权限控制，但当前账号能看到入口 — 前端权限过滤失效',
      action: '修复前端权限指令/组件，隐藏无权限的入口',
    };
  }

  if (signals.disabled_or_hidden_attr) {
    return {
      intent: 'PERM',
      confidence: 'medium',
      reason: '入口有 disabled/hidden 属性但未生效',
      action: '检查条件渲染逻辑',
    };
  }

  // ═══════════════════════════════════════════
  // 兜底: 无法判定 → 标记让用户确认
  // ═══════════════════════════════════════════
  return {
    intent: 'UNKNOWN',
    confidence: 'low',
    reason: '无法自动判定 — 需要人工确认',
    action: '请确认此功能是否需要保留',
  };
}
```

#### 信号采集方法

```bash
# —— 后端信号 ——

# API 是否存在 (对运行中的后端做探测)
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/admin/reports/daily

# 数据库模型/表是否存在
# MySQL
mysql -e "SHOW TABLES LIKE '%report%';"
# PostgreSQL
psql -c "\dt *report*"

# —— 前端信号 ——

# 组件文件是否存在
find . -name "*Report*" -o -name "*report*" | grep -v node_modules

# 组件是否是占位/空壳 (少于 20 行有效代码)
wc -l src/pages/reports/daily.tsx
grep -c "TODO\|FIXME\|WIP\|PLACEHOLDER\|暂未实现\|开发中\|待完善" src/pages/reports/daily.tsx

# —— 代码历史信号 ——

# 最近是否修改过 (30 天内)
git log --since="30 days ago" --oneline -- src/pages/reports/
# 如果没有输出 → 长期未动

# 是否有 feature flag 控制
grep -rn "featureFlag\|feature_flag\|FEATURE_\|isEnabled" \
  --include="*.ts" --include="*.tsx" --include="*.vue" src/ | grep -i "report"

# 是否在未合并的分支中
git branch --contains $(git log --oneline -1 --format=%H -- src/pages/reports/) 2>/dev/null
```

#### 批量信号采集脚本

```bash
#!/bin/bash
# collect-intent-signals.sh — 对每个死链批量采集判定信号
# 用法: ./collect-intent-signals.sh <dead-links-report.json> <project-root>

REPORT="$1"
PROJECT="$2"
BACKEND_URL="${3:-http://localhost:8080}"

# 对 report 中的每条记录
cat "$REPORT" | jq -r '.records[] | "\(.url)\t\(.source)"' | while IFS=$'\t' read -r url source; do

  echo "=== 分析: $url ==="

  # 推断资源名
  resource=$(echo "$url" | grep -oP '/\K[a-z]+' | head -1)

  # 后端信号
  api_status=$(curl -s -o /dev/null -w "%{http_code}" "${BACKEND_URL}${url}" 2>/dev/null)
  echo "  API 状态: $api_status"

  # 前端信号: 路由是否注册
  route_found=$(grep -r "path.*${url}" --include="*.ts" "$PROJECT/src/router/" 2>/dev/null | wc -l)
  echo "  路由: $( [ "$route_found" -gt 0 ] && echo 'YES' || echo 'NO' )"

  # 前端信号: 组件是否存在
  component=$(find "$PROJECT/src" -iname "*${resource}*" -name "*.tsx" -o -name "*.vue" 2>/dev/null | head -1)
  echo "  组件文件: ${component:-NOT FOUND}"

  # 组件是否是空壳
  if [ -n "$component" ]; then
    lines=$(wc -l < "$component")
    todos=$(grep -c "TODO\|FIXME\|WIP" "$component" 2>/dev/null || echo 0)
    echo "  组件行数: $lines (TODO/FIXME: $todos)"
  fi

  # 代码历史
  if [ -n "$component" ]; then
    recent=$(git -C "$PROJECT" log --since="30 days ago" --oneline -- "$component" 2>/dev/null | wc -l)
    echo "  近期修改: $( [ "$recent" -gt 0 ] && echo "YES ($recent commits)" || echo 'NO (30天内无修改)' )"
  fi

  echo ""
done
```

### 3.9 404 扫描报告汇总（含意图判定）

所有 Layer 完成后，汇总生成 `dead-links-report.json`：

```json
{
  "scan_time": "2026-02-16T12:00:00Z",
  "client": "admin",
  "summary": {
    "total_dead_links": 23,
    "by_intent": {
      "FIX": 8,
      "CLEAN": 7,
      "HIDE": 4,
      "PERM": 2,
      "UNKNOWN": 2
    },
    "by_layer": {
      "L1_navigation": 3,
      "L2_interaction": 5,
      "L3_api": 8,
      "L4_resource": 4,
      "L5_boundary": 3
    }
  },
  "records": [
    {
      "layer": "1a",
      "url": "/reports/daily",
      "source": "侧边栏菜单: 日报管理 → /reports/daily",
      "intent": "CLEAN",
      "confidence": "high",
      "signals": {
        "api_exists": false,
        "route_registered": true,
        "component_exists": true,
        "component_lines": 12,
        "has_todo": true,
        "recently_modified": false,
        "other_clients_have": false
      },
      "reason": "后端 API 已不存在，组件只有 12 行含 TODO — 废弃功能",
      "action": "删除菜单配置中的'日报管理'入口，删除路由和空壳组件",
      "file_hints": ["src/config/menu.ts:45", "src/router/report.ts:12", "src/pages/reports/daily.tsx"]
    },
    {
      "layer": "2a",
      "url": "/users/detail",
      "source": "用户管理列表 > 行操作 > 查看按钮",
      "intent": "FIX",
      "confidence": "high",
      "signals": {
        "api_exists": true,
        "api_returns_data": true,
        "route_registered": true,
        "component_exists": true,
        "component_lines": 180,
        "recently_modified": true,
        "other_clients_have": true
      },
      "reason": "后端 API 正常，组件完整且最近修改 — 路由路径不匹配",
      "action": "检查路由配置，/users/:id/detail 可能应为 /users/:id",
      "file_hints": ["src/router/user.ts:23"]
    },
    {
      "layer": "1a",
      "url": "/data-center",
      "source": "侧边栏菜单: 数据中心 → /data-center",
      "intent": "HIDE",
      "confidence": "high",
      "signals": {
        "api_exists": false,
        "route_registered": true,
        "component_exists": true,
        "component_lines": 35,
        "has_todo": true,
        "recently_modified": true,
        "has_feature_flag": false
      },
      "reason": "组件有 TODO 且最近修改 — 功能开发中但入口已暴露",
      "action": "在菜单配置中添加 feature flag 控制，开发完成后再开放",
      "file_hints": ["src/config/menu.ts:67"]
    },
    {
      "layer": "2d",
      "url": "/system/audit",
      "source": "系统设置 > 审计管理按钮",
      "intent": "PERM",
      "confidence": "high",
      "signals": {
        "api_exists": true,
        "api_returns_data": true,
        "route_registered": true,
        "component_exists": true,
        "permission_controlled": true,
        "current_user_has_permission": false
      },
      "reason": "API 存在且正常，但当前测试账号无权限却能看到入口 — 前端权限控制失效",
      "action": "检查权限指令 v-permission='audit:view' 是否生效",
      "file_hints": ["src/pages/system/index.tsx:34"]
    },
    {
      "layer": "1a",
      "url": "/legacy/reports",
      "source": "侧边栏菜单: 旧版报表 → /legacy/reports",
      "intent": "CLEAN",
      "confidence": "high",
      "signals": {
        "api_exists": false,
        "route_registered": false,
        "component_exists": false,
        "recently_modified": false,
        "in_menu_config": true
      },
      "reason": "后端无 API，前端无路由、无组件 — 菜单配置纯残留",
      "action": "从菜单配置中删除此条目",
      "file_hints": ["src/config/menu.ts:89"]
    }
  ]
}
```


### 来源文件：`docs/phase3/overview.md`

## Phase 3: 深度测试

> 通过 Playwright 或浏览器自动化实际执行测试。

### 3.0 性能优化策略

> 一个 15 模块的 admin 后台，未优化需要 13 分钟。

#### 优化 1: 单次遍历，多层收集（最关键）

当前问题：Layer 1 遍历菜单、Layer 2 遍历列表页、Layer 4 遍历所有页面……**同一个页面被访问了 3-4 次**。

优化方案：**每个页面只访问一次，一次性收集所有层级的信息。**

```typescript
/**
 * 单次页面访问，同时执行所有检测
 * 而不是 Layer 1 遍历一次、Layer 2 又遍历一次
 */
async function visitAndCollectAll(
  page: Page,
  url: string,
  collector: DeadLinkCollector,
  options: {
    checkBreadcrumbs: boolean;
    checkTabs: boolean;
    checkTableActions: boolean;
    checkToolbarButtons: boolean;
    checkBadText: boolean;
    checkImages: boolean;
  }
) {
  // 全局 collector 已经在自动监听 API 404 (L3) 和资源 404 (L4)
  // 不需要额外代码

  await page.goto(url);
  await page.waitForLoadState('networkidle').catch(() => {});

  const bodyText = await page.textContent('body').catch(() => '') || '';

  // ── L1: 页面本身是否 404 ──
  if (/404|not found|页面不存在/i.test(bodyText) || bodyText.trim().length < 10) {
    collector.add({ layer: '1a', url, type: 'navigation', status: 404 });
    return; // 页面都 404 了，下面不用检查了
  }

  // ── L1b: 面包屑（在当前页面上顺便检查） ──
  if (options.checkBreadcrumbs) {
    await checkBreadcrumbsOnPage(page, url, collector);
  }

  // ── L1c: Tab 切换（在当前页面上顺便检查） ──
  if (options.checkTabs) {
    await checkTabsOnPage(page, url, collector);
  }

  // ── L2: 表格行操作（如果是列表页） ──
  if (options.checkTableActions) {
    await checkTableActionsOnPage(page, url, collector);
  }

  // ── L2d: 工具栏按钮 ──
  if (options.checkToolbarButtons) {
    await checkToolbarButtonsOnPage(page, url, collector);
  }

  // ── L4b: 图片检查（顺便） ──
  if (options.checkImages) {
    await checkImagesOnPage(page, url, collector);
  }

  // ── 数据展示异常（顺便） ──
  if (options.checkBadText) {
    await checkBadTextOnPage(page, url, bodyText);
  }

  // L3 (API) 和 L4a (JS/CSS) 由全局 collector 自动捕获，不需要额外代码
}

/**
 * 主遍历循环 — 每个页面只访问一次
 */
async function runAllChecks(page: Page, modulePages: string[], collector: DeadLinkCollector) {
  for (const url of modulePages) {
    await visitAndCollectAll(page, url, collector, {
      checkBreadcrumbs: true,
      checkTabs: true,
      checkTableActions: true,     // 只对列表页
      checkToolbarButtons: true,   // 只对列表页
      checkBadText: true,
      checkImages: true,
    });
  }
}
```

**效果**：15 个模块原来要访问 60-80 个页面（每个页面 3-4 次），现在只访问 15-20 个页面各 1 次。

#### 优化 2: 并行浏览器上下文

**不同模块之间没有依赖关系**，可以并行。

```typescript
import { chromium, BrowserContext } from '@playwright/test';

async function runParallel(
  clients: ClientConfig[],
  modules: ModuleConfig[],
  maxConcurrency: number = 3
) {
  const browser = await chromium.launch();

  // 每个并行任务用独立的 BrowserContext（隔离 cookie/storage）
  const tasks = modules.map(module => async () => {
    const context = await browser.newContext({
      storageState: '.allforai/deadhunt/.auth/admin.json',  // 复用登录状态
    });
    const page = await context.newPage();
    const collector = new DeadLinkCollector();
    collector.attach(page, module.name);

    try {
      await visitAndCollectAll(page, module.listUrl, collector, {
        checkBreadcrumbs: true,
        checkTabs: true,
        checkTableActions: true,
        checkToolbarButtons: true,
        checkBadText: true,
        checkImages: true,
      });
    } finally {
      await context.close();
    }
    return collector.records;
  });

  // 控制并发数
  const results = await runWithConcurrency(tasks, maxConcurrency);
  return results.flat();
}

/** 并发控制器 */
async function runWithConcurrency<T>(
  tasks: (() => Promise<T>)[],
  limit: number
): Promise<T[]> {
  const results: T[] = [];
  const executing = new Set<Promise<void>>();

  for (const task of tasks) {
    const p = task().then(r => { results.push(r); });
    executing.add(p);
    p.finally(() => executing.delete(p));
    if (executing.size >= limit) {
      await Promise.race(executing);
    }
  }
  await Promise.all(executing);
  return results;
}
```

**效果**：3 个并行 context × 15 个模块 ≈ 5 轮，比串行 15 轮快 3 倍。

#### 优化 3: 静态分析结果指导深度测试（跳过不必要的检查）

静态分析已经告诉我们哪些模块有问题、哪些是干净的。**没必要对每个模块都做全量深度测试。**

```typescript
type TestDepth = 'full' | 'quick' | 'skip';

function decideTestDepth(module: ModuleConfig, staticResult: StaticAnalysis): TestDepth {
  // 静态分析发现问题的模块 → 全量测试
  if (staticResult.has_dead_links || staticResult.has_orphan_routes || staticResult.crud_incomplete) {
    return 'full';
  }

  // 静态分析干净、且上次验证通过、且代码没改 → 跳过
  if (staticResult.clean && module.last_passed && !module.code_changed) {
    return 'skip';
  }

  // 其他 → 快速检查（只验证页面能打开、API 不 404）
  return 'quick';
}

// quick 模式：只访问页面 + 全局 collector 被动收集，不做交互操作
// full 模式：访问页面 + 点按钮 + 检查表格行 + 测试 CRUD 闭环
// skip 模式：完全跳过
```

**效果**：15 个模块中，通常只有 3-5 个需要 full，5-7 个 quick，剩下 skip。时间减少 60-70%。

#### 优化 4: 智能等待替代固定等待

```typescript
// ❌ 慢：固定等待 500ms（不管页面是否已就绪）
await page.waitForTimeout(500);

// ✅ 快：等待关键元素出现，最多等 5s，通常 100-200ms 就够了
await page.waitForSelector('tbody tr, .ant-empty', { timeout: 5000 }).catch(() => {});

// ✅ 更快：直接等待网络空闲（API 请求完成）
await page.waitForLoadState('networkidle').catch(() => {});

// ✅ 最快：等待特定 API 返回（精准等待）
await page.waitForResponse(
  resp => resp.url().includes('/api/users') && resp.status() === 200,
  { timeout: 5000 }
).catch(() => {});
```

**效果：删除所有 `waitForTimeout`，改用条件等待。**

#### 优化 5: 意图判定信号批量采集

```bash
# ❌ 慢：逐个死链串行采集（每个 curl + git log 约 1-2 秒）
for link in dead_links; do
  curl "$link"          # 1s
  git log -- "$file"    # 0.5s
done
# 20 个死链 × 1.5s = 30s

# ✅ 快：批量并行
# 所有 curl 并行发出
for link in dead_links; do
  curl -s -o /dev/null -w "%{http_code}" "$link" &
done
wait  # 等待全部完成
# 20 个死链并行 ≈ 2s

# 所有 git log 一次性提取
git log --since="30 days ago" --name-only --oneline | sort -u > recent_files.txt
# 然后用 grep 匹配，0.1s
```

#### 优化 6: 分级验证策略

不是所有验证都需要一次跑完。提供三个级别：

```
Level 1: 快速扫描 (30 秒)
─────────────────────────
• 只跑静态分析
• 不启动浏览器
• 发现: 死链、孤儿路由、API 不匹配
• 适用: 每次 git commit 前

Level 2: 标准验证 (2-3 分钟)
─────────────────────────────
• 静态分析 + 浏览器快速遍历
• 每个页面访问一次，收集所有层级
• 不做 CRUD 闭环测试
• 适用: 每日开发结束前

Level 3: 完整验证 (10-15 分钟)
─────────────────────────────
• 全部 Phase 1-4
• 包括 CRUD 闭环、流程完整性、边界情况
• 包括多端一致性检查
• 适用: 发版前、Sprint 结束
```

```
# 使用方式
请用 deadhunt 做快速扫描。            # Level 1
请用 deadhunt 做标准验证。            # Level 2
请用 deadhunt 做完整验证。            # Level 3
请验证我的项目。                      # 默认 Level 2
```

#### 优化效果对比

| 场景 | 未优化 | 优化后 | 提升 |
|------|--------|--------|------|
| 15 模块全量 (Level 3) | 12 分钟 | 3-4 分钟 | 3x |
| 15 模块标准 (Level 2) | 12 分钟 | 1-2 分钟 | 8x |
| 静态扫描 (Level 1) | 12 分钟 | 20 秒 | 36x |
| 增量验证 (3 个变更模块) | 12 分钟 | 30-60 秒 | 12x |
| 多端验证 (3 端 × 15 模块) | 36 分钟 | 6-8 分钟 | 5x |

404/死链问题有多种来源，必须逐层覆盖：

```
404 来源分类
├── Layer 1: 导航级 (点击菜单/面包屑就 404)
│   ├── 1a. 侧边栏/顶部菜单链接
│   ├── 1b. 面包屑导航
│   └── 1c. Tab 页/子导航切换
│
├── Layer 2: 页面内交互级 (进了页面，点按钮 404)
│   ├── 2a. 表格行操作按钮 (查看/编辑/删除 跳转)
│   ├── 2b. 列表点击名称跳转详情
│   ├── 2c. 卡片/图片/标签等可点击元素
│   ├── 2d. 页头操作按钮 (新增/导入/导出)
│   └── 2e. 弹窗/抽屉内的跳转链接
│
├── Layer 3: API 级 (页面打开了，但接口 404)
│   ├── 3a. 页面加载时的数据请求 404
│   ├── 3b. 操作时的接口请求 404 (提交表单、删除等)
│   ├── 3c. 分页/筛选/搜索时的接口 404
│   └── 3d. 文件上传/下载接口 404
│
├── Layer 4: 资源级 (页面看起来能用，但缺东西)
│   ├── 4a. JS/CSS 文件加载 404
│   ├── 4b. 图片/图标加载 404
│   ├── 4c. 字体文件 404
│   └── 4d. 动态加载的 chunk 404 (懒加载路由)
│
└── Layer 5: 边界情况
    ├── 5a. 动态路由参数无效 (/users/不存在的id)
    ├── 5b. 权限不足时的重定向目标 404
    ├── 5c. 登录过期后的跳转目标 404
    └── 5d. 直接输入 URL 访问 (非 SPA 内部跳转)
```


### 来源文件：`docs/phase3/patrol.md`

## Patrol 深度测试引擎（Flutter 端）

> 当 Phase 0 检测到 Flutter 客户端时，Phase 3 使用 Patrol 替代 Playwright 做深度测试。
> 两个引擎独立执行，结果汇入同一个 `reports/convergence-deep.json` 格式。

### 架构：双引擎并行

```
Phase 3: 深度测试
├── Web/H5 客户端 → Playwright 引擎（上文所述）
└── Flutter 客户端 → Patrol 引擎（本节）
    ├── 测试代码生成 → .dart 文件
    ├── 执行 → patrol test
    └── 结果收集 → 统一 JSON 格式
```

### Flutter 5 层检测模型

Playwright 的 5 层 404 分类适配到 Flutter 原生语境：

| 层级 | Playwright (Web) | Patrol (Flutter) |
|------|-----------------|-----------------|
| **L1a: 导航** | 菜单/面包屑点击 → 检查 URL | BottomNav/Drawer/AppBar 点击 → 检查当前路由 |
| **L1b: 页面交互** | 页面按钮/链接 → 检查跳转 | Widget 按钮/ListTile → 检查 Navigator 栈 |
| **L2: 页内交互** | 表格操作/表单提交 | ListView 项操作/表单提交/Dialog |
| **L3: API 层** | 拦截 XHR/Fetch → 检查 4xx/5xx | 拦截 Dio/http 响应 → 检查错误状态 |
| **L4: 资源层** | JS/CSS/图片 404 | 图片加载失败(`errorBuilder`)、字体缺失、资源文件 |
| **L5: 边界情况** | 无效 URL、SPA 刷新 | 无效 deep link 路由、权限拒绝、网络断开 |

### Flutter 错误检测信号

与 Web 端检测 HTTP 404 不同，Patrol 端检测以下信号：

| 信号 | 代码检测方式 | 对应问题类型 |
|------|-------------|------------|
| `ErrorWidget` 出现 | `expect(find.byType(ErrorWidget), findsNothing)` | 死链 / 代码错误 |
| 显示 `null`/`undefined` 文本 | `expect(find.text('null'), findsNothing)` | Ghost Feature / 字段不一致 |
| Navigator 栈异常 | 路由跳转后 `find.byType(TargetPage)` 失败 | 死链 |
| `DioException` | 捕获 Dio interceptor 中的错误状态码 | API 死链 |
| 加载卡住 | `CircularProgressIndicator` 超时仍存在 | API 超时 / 接口不存在 |
| 权限弹窗未处理 | Patrol 的 `$.native.grantPermissionWhenInUse()` 检测 | 权限盲点 |

### Patrol 测试生成策略

对每个 Flutter 模块生成 Patrol 测试代码，保存到 `.allforai/deadhunt/patrol/` 目录：

```dart
// 自动生成: .allforai/deadhunt/patrol/order_module_test.dart
import 'package:patrol/patrol.dart';

void main() {
  patrolTest('订单模块 - L1a 导航可达', ($) async {
    // 从首页通过 BottomNav 导航到订单页
    await $(BottomNavigationBar).tap();
    await $(#orderTab).tap();

    // 验证路由正确到达
    expect($.tester.widget<OrderPage>(find.byType(OrderPage)), isNotNull);
  });

  patrolTest('订单模块 - L2 列表操作', ($) async {
    // 点击订单详情
    await $(ListTile).first.tap();

    // 验证详情页加载，无错误 Widget
    expect(find.byType(ErrorWidget), findsNothing);
    expect(find.text('订单详情'), findsOneWidget);
  });

  patrolTest('订单模块 - L3 API 响应', ($) async {
    // 进入订单列表，检查数据加载
    await $(#orderTab).tap();
    await $.pumpAndSettle();

    // 验证无空数据/错误状态
    expect(find.text('加载失败'), findsNothing);
    expect(find.text('null'), findsNothing);
    expect(find.byType(ErrorWidget), findsNothing);
  });
}
```

### Widget 查找策略

Playwright 通过 CSS selector 定位元素，Patrol 需要适配 Widget tree：

| 优先级 | 查找方式 | 示例 | 适用场景 |
|--------|---------|------|---------|
| 1 | Key | `$(Key('order_list'))` | Widget 有显式 Key |
| 2 | Type | `$(OrderListPage)` | Widget 类型唯一 |
| 3 | Text | `$(find.text('订单管理'))` | 文本内容唯一 |
| 4 | Semantics | `$(find.bySemanticsLabel('订单'))` | 有 Semantics 标签 |
| 5 | 组合 | `$(ListView).$(ListTile).first` | 需要层级定位 |

> **选择顺序**：优先用 Key（最稳定），其次 Type，最后 Text。避免依赖 Text（多语言会变）。

### 执行与收敛

```
执行流程：
  1. 生成 Patrol 测试文件 → .allforai/deadhunt/patrol/*.dart
  2. 执行 patrol test --target .allforai/deadhunt/patrol/
  3. 收集结果 → 解析 test report
  4. 转换为统一 JSON 格式 → 合并到 convergence-deep.json

收敛循环：
  与 Playwright 相同结构（2 cycle × 最多 3-4 轮）
  Round 1: 基础扫描（生成并执行所有模块的 Patrol 测试）
  Round 2-4: 模式学习 → 交叉验证 → 扩散搜索（根据失败结果调整测试）
```

### Patrol 环境要求

| 要求 | 说明 |
|------|------|
| Flutter SDK | 项目已有 |
| Patrol CLI | `dart pub global activate patrol_cli` |
| 模拟器/真机 | Android emulator 或 iOS Simulator |
| 项目依赖 | `pubspec.yaml` 中已有 `patrol` |

### Patrol 限制与应对

| 限制 | 应对策略 |
|------|---------|
| 需要模拟器/真机 | 文档说明环境要求；支持 CI 中 Android emulator |
| 执行速度较慢 | 静态分析优先过滤，只测有嫌疑的模块 |
| 无法像 Playwright 拦截网络 | 通过 Dio interceptor 或日志收集 API 响应状态 |
| Widget key 不一定存在 | 支持多种查找策略：Key → Type → Text → Semantics |
| 无法并行多实例 | 模块间串行执行（不同于 Playwright 的并行 context） |

### 结果格式

Patrol 结果转换为与 Playwright 相同的 JSON 格式：

```json
{
  "engine": "patrol",
  "client": "flutter-app",
  "module": "order",
  "findings": [
    {
      "layer": "1a",
      "type": "navigation",
      "description": "从 BottomNav 点击订单 Tab 后未到达 OrderPage",
      "signal": "find.byType(OrderPage) failed",
      "severity": "critical",
      "intent": "FIX"
    },
    {
      "layer": "3",
      "type": "api",
      "description": "订单列表 API 返回错误",
      "signal": "DioException: 404",
      "severity": "critical",
      "intent": "FIX"
    }
  ]
}
```

此格式与 Playwright 引擎的 findings 格式一致，Phase 4 报告生成无需区分引擎来源。


### 来源文件：`docs/phase3/validation.md`

### 3.9 方向 B（数据→界面）: 运行时反向验证

> 静态分析已发现"幽灵 API"和"不可达路由"，通过运行时确认。

```typescript
test.describe('方向 B: 数据→界面 反向验证', () => {

  // === 从 API 文档验证每个端点是否有 UI 入口 ===
  test('幽灵 API 验证：后端有但前端没调用的接口', async ({ page }) => {
    await login(page);

    // 从 static-analysis/api-reverse-coverage.json 读取
    const ghostApis = [
      { method: 'DELETE', path: '/admin/coupons/batch', description: '批量删除优惠券' },
      { method: 'GET', path: '/admin/users/export', description: '用户导出' },
      { method: 'PUT', path: '/api/user/avatar', description: '更新头像' },
    ];

    // 对每个幽灵 API，尝试从 UI 找到触发它的操作
    for (const api of ghostApis) {
      // 推断：DELETE /admin/coupons/batch → 应该在优惠券列表页有批量删除按钮
      // 推断：GET /admin/users/export → 应该在用户列表页有导出按钮
      const guessedPage = guessPageForApi(api.path); // 根据路径推断所在页面
      if (!guessedPage) continue;

      await page.goto(guessedPage);
      await page.waitForLoadState('networkidle').catch(() => {});

      // 收集页面上的所有网络请求
      const requests: string[] = [];
      page.on('request', req => requests.push(`${req.method()} ${new URL(req.url()).pathname}`));

      // 尝试各种交互：点击按钮、展开下拉菜单、hover 行操作
      await interactWithAllElements(page);

      // 检查是否有任何请求匹配该 API
      const matched = requests.some(r =>
        r.includes(api.method) && r.includes(api.path.replace(/\/admin|\/api|\/merchant/g, ''))
      );

      if (!matched) {
        console.log(`🔴 幽灵 API 确认: ${api.method} ${api.path} — 界面上无任何操作能触发此接口`);
      }
    }
  });

  // === 从路由定义验证每个页面是否可达 ===
  test('不可达路由验证：路由存在但界面无入口', async ({ page }) => {
    await login(page);

    // 从 static-analysis/unreachable-routes.json 读取
    const unreachableRoutes = [
      { path: '/products/import', name: '商品导入' },
      { path: '/system/backup', name: '系统备份' },
    ];

    for (const route of unreachableRoutes) {
      // 先确认页面本身能正常打开（排除死路由）
      await page.goto(route.path);
      await page.waitForLoadState('networkidle').catch(() => {});
      const bodyText = await page.textContent('body').catch(() => '') || '';
      const pageWorks = bodyText.trim().length > 10 && !/404|not found/i.test(bodyText);

      if (pageWorks) {
        // 页面能用但找不到入口 → 功能被藏起来了
        console.log(`🔴 不可达功能确认: ${route.name} (${route.path}) — 页面正常但界面上无入口`);
      } else {
        // 页面也不能用 → 废弃路由
        console.log(`⚠️ 废弃路由: ${route.name} (${route.path}) — 路由注册但页面不可用`);
      }
    }
  });

  // === 从后端模型验证是否有对应管理界面 ===
  test('无管理界面的数据模型', async ({ page }) => {
    await login(page);

    // 从 static-analysis/model-coverage.json 读取
    const uncoveredModels = [
      { model: 'Notification', guessedMenu: '通知', guessedRoute: '/notifications' },
      { model: 'PaymentRecord', guessedMenu: '支付记录', guessedRoute: '/payments' },
    ];

    for (const model of uncoveredModels) {
      // 方法 1: 搜索菜单中是否有对应入口
      const menuText = await page.textContent('[class*="menu"], [class*="sidebar"], nav');
      const hasMenuEntry = menuText && new RegExp(model.guessedMenu, 'i').test(menuText);

      // 方法 2: 直接访问推测的路由
      await page.goto(model.guessedRoute);
      await page.waitForLoadState('networkidle').catch(() => {});
      const bodyText = await page.textContent('body').catch(() => '') || '';
      const routeWorks = bodyText.trim().length > 10 && !/404|not found/i.test(bodyText);

      if (!hasMenuEntry && !routeWorks) {
        console.log(`🔴 无管理界面: 数据模型 ${model.model} 在数据库存在，但后台没有管理入口`);
      } else if (!hasMenuEntry && routeWorks) {
        console.log(`⚠️ 隐藏入口: ${model.model} 页面存在 (${model.guessedRoute}) 但菜单中找不到`);
      }
    }
  });
});

/** 推断 API 路径对应的前端页面 */
function guessPageForApi(apiPath: string): string | null {
  // /admin/coupons/batch → /coupons
  // /admin/users/export → /users
  // /api/orders/:id/refund → /orders
  const parts = apiPath
    .replace(/^\/(admin|merchant|api)\//, '')
    .split('/')
    .filter(p => p && !p.startsWith(':') && !['batch', 'export', 'import', 'list', 'detail'].includes(p));
  return parts.length > 0 ? `/${parts[0]}` : null;
}

/** 尝试与页面上所有可交互元素互动，触发隐藏的 API 调用 */
async function interactWithAllElements(page: Page) {
  // 点击所有可见按钮（排除危险操作）
  const buttons = await page.locator('button:visible, a.ant-btn:visible, .el-button:visible').all();
  for (const btn of buttons) {
    const text = (await btn.textContent())?.trim() || '';
    if (/删除|移除|清空|drop|truncate/i.test(text)) continue; // 跳过危险按钮

    const currentUrl = page.url();
    await btn.click().catch(() => {});
    await page.waitForTimeout(500);

    // 如果跳转了就回去
    if (page.url() !== currentUrl) {
      await page.goto(currentUrl).catch(() => {});
      await page.waitForLoadState('networkidle').catch(() => {});
    }
    // 如果打开了弹窗就关闭
    await page.keyboard.press('Escape');
    await page.waitForTimeout(200);
  }

  // 展开所有下拉菜单
  const dropdowns = await page.locator('.ant-dropdown-trigger:visible, .el-dropdown:visible').all();
  for (const dd of dropdowns) {
    await dd.click().catch(() => {});
    await page.waitForTimeout(300);
    await page.keyboard.press('Escape');
  }

  // 如果有表格，hover 第一行
  const firstRow = page.locator('tbody tr, .ant-table-row').first();
  if (await firstRow.count() > 0) {
    await firstRow.hover();
    await page.waitForTimeout(300);
  }
}
```

### 3.10 CRUD 完整性测试

(独立于 404 扫描，检查每个模块的操作入口是否存在)

### 3.11 数据展示验证

> 页面不是 404 不代表它是正常的。一个"能打开"的页面可能：列表永远为空、字段显示 undefined、金额显示 NaN、时间显示 Invalid Date。

```typescript
test.describe('数据展示验证', () => {

  test('列表页应有数据或有空状态提示', async ({ page }) => {
    await login(page);
    const listPages = [/* 从 validation-profile 读取 */];

    for (const lp of listPages) {
      await page.goto(lp);
      await page.waitForLoadState('networkidle').catch(() => {});

      // 检查是否有表格数据
      const rowCount = await page.locator('tbody tr, .ant-table-row, .el-table__row').count();
      // 检查是否有空状态组件
      const hasEmpty = await page.locator('.ant-empty, .el-empty, [class*="empty"], [class*="no-data"]').count() > 0;
      // 检查是否有加载中
      const isLoading = await page.locator('.ant-spin, .el-loading, [class*="loading"]').count() > 0;

      if (rowCount === 0 && !hasEmpty && !isLoading) {
        console.warn(`⚠️ ${lp}: 列表无数据且无空状态提示 — 可能是接口问题或忘了加 Empty 组件`);
      }
    }
  });

  test('检查页面中的异常文本', async ({ page }) => {
    await login(page);
    const allPages = [/* 所有页面路由 */];

    // 不应出现在已上线页面中的异常文本模式
    const badPatterns = [
      { pattern: /undefined|NaN|\[object Object\]/g, desc: '未处理的空值' },
      { pattern: /Invalid Date|1970-01-01|NaN-NaN/g, desc: '日期处理错误' },
      { pattern: /TODO|FIXME|HACK|XXX|PLACEHOLDER/gi, desc: '开发调试残留' },
      { pattern: /lorem ipsum|测试数据|test data|asdf/gi, desc: '测试数据残留' },
      { pattern: /localhost:\d+/g, desc: '硬编码本地地址' },
      { pattern: /sk-[a-zA-Z0-9]{20,}|AKIA[A-Z0-9]{16}/g, desc: '疑似泄露的密钥' },
    ];

    for (const p of allPages) {
      await page.goto(p);
      await page.waitForLoadState('networkidle').catch(() => {});

      const bodyText = await page.textContent('body').catch(() => '') || '';

      for (const { pattern, desc } of badPatterns) {
        const matches = bodyText.match(pattern);
        if (matches && matches.length > 0) {
          console.warn(`⚠️ ${p}: 发现 ${desc} — "${matches[0]}"`);
        }
      }
    }
  });

  test('检查图片和资源加载', async ({ page }) => {
    await login(page);
    const allPages = [/* 所有页面路由 */];

    for (const p of allPages) {
      await page.goto(p);
      await page.waitForLoadState('networkidle').catch(() => {});

      // 检查破损图片
      const brokenImages = await page.evaluate(() => {
        return Array.from(document.querySelectorAll('img'))
          .filter(img => img.src && !img.src.startsWith('data:') && (!img.complete || img.naturalHeight === 0))
          .map(img => ({ src: img.src, alt: img.alt }));
      });

      for (const img of brokenImages) {
        console.warn(`⚠️ ${p}: 图片加载失败 — ${img.src} (alt: ${img.alt})`);
      }

      // 检查空的图标占位
      const emptyIcons = await page.evaluate(() => {
        return Array.from(document.querySelectorAll('i, .icon, [class*="icon"]'))
          .filter(el => el.textContent?.trim() === '' && getComputedStyle(el).content === 'none')
          .length;
      });

      if (emptyIcons > 3) {
        console.warn(`⚠️ ${p}: 发现 ${emptyIcons} 个空图标 — 可能是图标库未加载`);
      }
    }
  });
});
```

### 3.12 业务流程完整性验证

> CRUD 不是孤立的操作，它们组成**流程**。新增→保存→列表能看到→编辑→保存→数据变了→删除→列表看不到了。任何一步断了都是问题。

```typescript
test.describe('业务流程完整性', () => {

  /**
   * 标准 CRUD 闭环测试模板
   * 按 validation-profile 中每个模块的 crud_by_client 生成
   */
  test('完整 CRUD 闭环: 用户管理', async ({ page }) => {
    await login(page);
    await page.goto('/users');
    await page.waitForLoadState('networkidle').catch(() => {});

    // 记录初始列表数量
    const initialCount = await page.locator('tbody tr').count();

    // === Step 1: 新增 ===
    // 点新增按钮
    await page.getByText(/新增|添加|创建/).first().click();
    await page.waitForLoadState('networkidle').catch(() => {});

    // 填写表单（最小必填字段）
    // 注意：需要根据模块具体字段生成，这里是示例
    const testName = `test_${Date.now()}`;
    await page.getByLabel(/用户名|姓名|名称/).first().fill(testName);
    // ... 其他必填字段

    // 提交
    await page.getByText(/保存|提交|确定/).first().click();
    await page.waitForLoadState('networkidle').catch(() => {});

    // === Step 2: 验证新增成功 — 返回列表能找到 ===
    await page.goto('/users');
    await page.waitForLoadState('networkidle').catch(() => {});

    const afterAddCount = await page.locator('tbody tr').count();
    const newRowVisible = await page.getByText(testName).count() > 0;

    if (!newRowVisible) {
      console.error('🔴 流程断裂: 新增后返回列表找不到刚创建的数据');
      // 可能的原因：
      // - 新增 API 成功但列表没刷新
      // - 新增 API 失败但前端没提示
      // - 默认排序/分页导致新数据不在第一页
    }

    // === Step 3: 编辑 ===
    if (newRowVisible) {
      const row = page.locator('tbody tr').filter({ hasText: testName }).first();
      await row.hover();
      await row.getByText(/编辑|修改/).first().click();
      await page.waitForLoadState('networkidle').catch(() => {});

      // 修改某个字段
      const editedName = `${testName}_已编辑`;
      await page.getByLabel(/用户名|姓名|名称/).first().fill(editedName);
      await page.getByText(/保存|提交|确定/).first().click();
      await page.waitForLoadState('networkidle').catch(() => {});

      // 验证编辑生效
      await page.goto('/users');
      await page.waitForLoadState('networkidle').catch(() => {});
      const editedVisible = await page.getByText(editedName).count() > 0;
      if (!editedVisible) {
        console.error('🔴 流程断裂: 编辑保存后列表数据未更新');
      }
    }

    // === Step 4: 删除 ===
    if (newRowVisible) {
      const row = page.locator('tbody tr').filter({ hasText: testName }).first();
      await row.hover();
      await row.getByText(/删除|移除/).first().click();
      // 确认弹窗
      await page.getByText(/确认|是/).first().click();
      await page.waitForLoadState('networkidle').catch(() => {});

      // 验证删除成功 — 列表中不再有此数据
      await page.waitForTimeout(500);
      const deletedStillVisible = await page.getByText(testName).count() > 0;
      if (deletedStillVisible) {
        console.error('🔴 流程断裂: 删除后列表中仍然有此数据');
      }
    }

    // === Step 5: 数据清理 ===
    // 如果以上任何步骤失败导致数据残留，尝试通过 API 直接删除
    // 避免测试数据污染
  });
});
```

### 3.13 增量验证（回归检测）

> 不是每次都需要全量扫描。代码变更后只需验证**受影响的模块**。

```
增量验证触发条件：
1. Git diff 中涉及的文件 → 反推受影响的模块和路由
2. 只对受影响的模块重跑验证
3. 与上次全量报告 (baseline) 对比，只报告新增/变化的问题

使用方式：
请用 deadhunt 技能做增量验证。
项目路径是 /path/to/project。
只验证最近一次变更。
```

```bash
#!/bin/bash
# incremental-check.sh — 基于 git diff 确定受影响的模块
# 用法: ./incremental-check.sh [base_commit]

BASE="${1:-HEAD~1}"
PROJECT_ROOT="."

echo "🔄 增量验证: 对比 $BASE..HEAD"

# 获取变更的文件列表
CHANGED_FILES=$(git diff --name-only "$BASE"..HEAD)
echo "变更文件数: $(echo "$CHANGED_FILES" | wc -l)"

# 提取涉及的模块（通过目录名推断）
AFFECTED_MODULES=$(echo "$CHANGED_FILES" | \
  grep -oP "src/(pages|views|modules|features)/\K[^/]+" | \
  sort -u)
echo "受影响模块: $AFFECTED_MODULES"

# 提取涉及的路由文件
ROUTE_CHANGES=$(echo "$CHANGED_FILES" | grep -i "router\|route")
if [ -n "$ROUTE_CHANGES" ]; then
  echo "⚠️ 路由配置有变更 — 需要检查死链"
fi

# 提取涉及的菜单配置
MENU_CHANGES=$(echo "$CHANGED_FILES" | grep -i "menu\|sidebar\|nav")
if [ -n "$MENU_CHANGES" ]; then
  echo "⚠️ 菜单配置有变更 — 需要检查导航"
fi

# 提取涉及的 API 定义
API_CHANGES=$(echo "$CHANGED_FILES" | grep -i "api/\|services/\|request")
if [ -n "$API_CHANGES" ]; then
  echo "⚠️ API 定义有变更 — 需要检查接口连通性"
fi

# 提取涉及的权限配置
PERM_CHANGES=$(echo "$CHANGED_FILES" | grep -i "permission\|auth\|guard\|role")
if [ -n "$PERM_CHANGES" ]; then
  echo "⚠️ 权限配置有变更 — 需要检查权限遮蔽"
fi

# 输出增量验证范围
echo ""
echo "📋 增量验证范围:"
echo "  模块: $AFFECTED_MODULES"
echo "  路由检查: $( [ -n "$ROUTE_CHANGES" ] && echo 'YES' || echo 'NO' )"
echo "  菜单检查: $( [ -n "$MENU_CHANGES" ] && echo 'YES' || echo 'NO' )"
echo "  API 检查: $( [ -n "$API_CHANGES" ] && echo 'YES' || echo 'NO' )"
echo "  权限检查: $( [ -n "$PERM_CHANGES" ] && echo 'YES' || echo 'NO' )"
```

### 3.14 验证结果稳定性

> 自动化测试最怕 flaky（时灵时不灵）。同一个问题跑两次结果不同就没人信任报告了。

**导致不稳定的常见因素及应对：**

| 因素 | 现象 | 应对 |
|------|------|------|
| 异步加载时序 | 有时找不到元素 | 用 `waitForSelector` 替代固定 `waitForTimeout` |
| 动态数据 | 列表数据每次不同，行操作结果不一致 | 用固定的测试数据或 mock 数据 |
| 动画/过渡效果 | 元素在动画中点不到 | 禁用动画：`page.emulateMedia({ reducedMotion: 'reduce' })` |
| 弹窗/通知遮挡 | 通知弹窗遮住了按钮 | 每次操作前关闭所有浮层 |
| 验证码/人机验证 | 测试环境有验证码 | 测试环境关闭验证码，或用万能验证码 |
| 并发冲突 | 多人同时跑测试修改同一条数据 | 每次测试用唯一前缀的数据 |
| 分页/排序 | 新增的数据不在当前页 | 搜索或排序定位到测试数据 |

```typescript
// 稳定性增强工具函数

/** 等待元素可见且稳定（不在动画中） */
async function waitForStable(page: Page, selector: string, timeout = 10000) {
  await page.waitForSelector(selector, { state: 'visible', timeout });
  // 等待位置稳定（连续两次位置相同）
  let lastBox = null;
  for (let i = 0; i < 5; i++) {
    const box = await page.locator(selector).first().boundingBox();
    if (lastBox && box &&
        Math.abs(box.x - lastBox.x) < 1 && Math.abs(box.y - lastBox.y) < 1) {
      return;
    }
    lastBox = box;
    await page.waitForTimeout(200);
  }
}

/** 关闭所有浮层（弹窗、通知、抽屉） */
async function dismissAllOverlays(page: Page) {
  // 关闭 Ant Design 通知
  const closeButtons = await page.locator(
    '.ant-notification-close, .ant-message-close, .el-notification__closeBtn, .el-message__closeBtn'
  ).all();
  for (const btn of closeButtons) {
    await btn.click().catch(() => {});
  }
  // 按 Escape 关闭可能的弹窗
  await page.keyboard.press('Escape');
  await page.waitForTimeout(200);
}

/** 生成唯一测试数据标识 */
function testDataId(): string {
  return `_autotest_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`;
}
```

---


### 来源文件：`docs/phase3-test.md`

## Phase 3: 深度测试

> 通过 Playwright（Web/H5）或 Patrol（Flutter）自动化执行测试。
> 本文档已拆分为子文件，按需加载以节省上下文空间。

### 子文件索引

| 文件 | 内容 | 何时加载 |
|------|------|---------|
| `${CLAUDE_PLUGIN_ROOT}/docs/phase3/overview.md` | 性能优化策略、5 层分类、分级验证 | 总是加载 |
| `${CLAUDE_PLUGIN_ROOT}/docs/phase3/404-scanner.md` | 全局 404 监控器 + Layer 1-5 扫描实现 | deep/full 模式 |
| `${CLAUDE_PLUGIN_ROOT}/docs/phase3/intent-classification.md` | 死链意图判定 (FIX/CLEAN/HIDE/PERM) + 报告汇总 | deep/full 模式 |
| `${CLAUDE_PLUGIN_ROOT}/docs/phase3/validation.md` | 方向 B 反向验证 + CRUD 闭环 + 数据展示 + 业务流程 + 增量验证 + 稳定性 | deep/full 模式 |
| `${CLAUDE_PLUGIN_ROOT}/docs/phase3/convergence.md` | 多轮收敛机制（模式学习→交叉验证→扩散搜索） | full 模式 |
| `${CLAUDE_PLUGIN_ROOT}/docs/phase3/patrol.md` | Patrol 深度测试引擎（Flutter 端） | Flutter 项目 |

### 加载策略

- **quick 模式**: 不加载 Phase 3（仅静态分析）
- **deep/full 模式**: 先加载 `overview.md`，再按需加载其他子文件
- **Flutter 项目**: 额外加载 `patrol.md`
- **incremental 模式**: 加载 `overview.md` + `404-scanner.md`（只验证变更模块）


### 来源文件：`docs/phase4-report.md`

## Phase 4: 报告生成

### 4.0 保存基线 & 增量对比

每次验证完成后，保存当前结果作为基线：

```typescript
// 保存基线
async function saveBaseline(outputDir: string, report: ValidationReport) {
  const baselinePath = path.join(outputDir, 'reports', 'baseline.json');
  const baseline = {
    saved_at: new Date().toISOString(),
    summary: report.summary,
    dead_links: report.dead_links.map(l => ({ url: l.url, layer: l.layer, intent: l.intent })),
    crud_issues: report.crud_issues.map(i => ({ module: i.module, missing: i.missing })),
    ghost_apis: report.ghost_apis.map(a => ({ method: a.method, path: a.path })),
  };
  fs.writeFileSync(baselinePath, JSON.stringify(baseline, null, 2));
}

// 与上次对比
function compareWithBaseline(
  current: ValidationReport, baselinePath: string
): IncrementalDiff {
  const baseline = JSON.parse(fs.readFileSync(baselinePath, 'utf-8'));

  return {
    new_issues: current.all_issues.filter(i =>
      !baseline.all_issues.some((b: any) => b.url === i.url && b.layer === i.layer)
    ),
    fixed_issues: baseline.all_issues.filter((b: any) =>
      !current.all_issues.some((i: any) => i.url === b.url && i.layer === b.layer)
    ),
    unchanged_issues: current.all_issues.filter(i =>
      baseline.all_issues.some((b: any) => b.url === i.url && b.layer === i.layer)
    ),
  };
}
```

增量报告在报告顶部显示变化摘要：

```markdown
## 📈 与上次对比 (baseline: 2026-02-14)

| 变化 | 数量 |
|------|------|
| 🆕 新增问题 | 3 |
| ✅ 已修复 | 5 |
| ⏳ 未变化 | 8 |

### 🆕 新增问题
| 类型 | 位置 | 说明 |
|------|------|------|
| 死链 L2 | 商品 > 新按钮 | 新加的按钮指向 404 |

### ✅ 已修复（上次有这次没有）
| 类型 | 位置 | 说明 |
|------|------|------|
| 死链 L1 | 菜单 > 日报管理 | 菜单已清理 ✅ |
| 死链 L2 | 用户 > 查看按钮 | 路由已修复 ✅ |
```

### 4.0.1 收敛分析报告

如果本次验证执行了多轮收敛，在报告中展示收敛过程。

读取 `static-analysis/convergence.json` 和 `reports/convergence-deep.json`（如果存在），生成以下段落：

```markdown
### 收敛分析

| 阶段 | 基线发现 | 收敛追加 | 追加率 | 收敛轮次 |
|------|---------|---------|--------|---------|
| 静态分析 | {baseline} | +{bonus} | +{rate}% | {rounds}轮 |
| 深度测试 | {baseline} | +{bonus} | +{rate}% | {rounds}轮 |

> 如果不做多轮收敛，将漏掉 {total_bonus} 个问题（总 {total} 个中的 {miss_rate}%）
```

**每个 finding 的 source 标签也体现在详细问题列表中**，让用户知道哪些问题是收敛追加轮次发现的：

```markdown
| 层级 | 位置 | 问题 | 发现方式 | 建议 |
|------|------|------|---------|------|
| L1 | 菜单 > 日报管理 | /reports/daily 404 | 基线扫描 | 删菜单 |
| L2 | 商品 > 智能推荐按钮 | /products/ai-recommend 404 | 模式学习 | 隐藏按钮 |
| L3 | 用户 > 导入接口 | POST /api/users/import 无入口 | 交叉验证 | 添加导入按钮 |
| L1 | 支付 > 退款列表 | /payments/refund 404 | 扩散搜索 | 修复路由 |
```

`发现方式` 列取自 finding 的 `source` 字段，映射为中文：
- `baseline` → `基线扫描`
- `pattern_learning` → `模式学习`
- `cross_validation` → `交叉验证`
- `diffusion` → `扩散搜索`

### 4.1 单端报告

每个前端生成独立的 `validation-report-{client_id}.md`：

```markdown
# 产品验证报告 — Admin 后台

> 验证对象: Admin 管理后台 (super_admin)
> 验证时间: 2026-02-16
> 运行地址: http://localhost:3000

## 总览

| 指标 | 数值 |
|------|------|
| 本端涉及模块 | 12 |
| 已测试 | 12 |
| 测试用例总数 | 48 |
| 通过 | 39 |
| 失败 | 7 |
| 警告 | 2 |
| 跨端分工（正常跳过） | 3 |

## 🔴 严重问题 (需立即修复)

### 1. 死链 / 404 问题（按处置意图分类）

#### 🔴 FIX — 功能需要，修复代码 (8 个)
| 层级 | 位置 | 问题 | 判定依据 | 建议 |
|------|------|------|---------|------|
| L2 | 用户列表 > 查看按钮 | /users/123/detail 404 | API✅ 组件✅ 其他拼写 |
| L3 | 仪表盘加载 | GET /admin/dashboard/stats 404 | 页面需要此数据 | 修复后端接口 |
| L3 | 订单筛选 | GET /admin/orders?status=refund 404 | 筛选条件必需 | 后端缺少筛选参数支持 |

#### 🟡 CLEAN — 功能已废弃，清理入口 (7 个)
| 层级 | 位置 | 问题 | 判定依据 | 清理范围 |
|------|------|------|---------|---------|
| L1 | 菜单 > 日报管理 | /reports/daily 404 | API❌ 组件12行 TODO 30天未动 | 删菜单+删路由+删组件 |
|  | 菜单 > 旧版报表 | /legacy/reports 404 | API❌ 路由❌ 组件❌ | 删菜单配置 |
| L4 | 全局 | /assets/ReportPage-xxx.js chunk 404 | 关联的日报管理已废弃 | 随日报管理一起清理 |

#### 🟠 HIDE — 开发中，隐藏入口 (4 个)
| 层级 | 位置 | 问题 | 判定依据 | 建议 |
|------|------|------|---------|------|
| L1 | 菜单 > 数据中心 | /data-center 白屏 | 组件有 TODO 最近有修改 | 菜单加 feature flag |
| L2 | 商品列表 > 智能推荐 | /products/ai-recommend 404 | API 还没做 前端刚提交 | 按钮加 v-if 控制 |

#### 🔵 PERM — 不该看到，修复权限 (2 个)
| 层级 | 位置 | 问题 | 判定依据 | 建议 |
|------|------|------|---------|------|
| L2 | 系统设置 > 审计管理 | 普通用户能看到按钮 | API 有权限控制但前端没过滤 | v-permission 失效 |

#### ❓ UNKNOWN — 需人工确认 (2 个)
| 层级 | 位置 | 问题 | 现有线索 |
|------|------|------|---------|
| L2 | 商品列表 > 对比功能 | /products/compare 404 | 组件存在(80行) 但30天未动, API 存在但返回 500 |
| L3 | 个人中心 | GET /api/user/points 404 | 积分系统不确定是否上线 |

### 2. 模块不完整（本端职责范围内的缺失）
| 模块 | 缺失功能 | 本端应有? | 建议 |
|------|---------|----------|------|
| 商品管理 | 无批量导入 | ✅ 是 (admin 应有) | 添加导入按钮 |
| 订单管理 | 无导出 | ✅ 是 (admin 应有) | 添加导出功能 |

## 🟢 跨端正常分工（非问题）
 | 本端无此操作 | 原因 | 负责端 |
|------|------------|------|--------|
| 订单 | 无新增入口 | 下单由客户端完成 | customer_h5, customer_app |
| 评价 | 无新增入口 | 评价由客户端提交 | customer_h5, customer_app |
| 评价 | 无编辑入口 | 用户自行修改评价 | customer_h5, customer_app |

## 🟡 警告 (建议修复)
... (同之前)

## ✅ 通过的模块
- 商品管理 (CRUD + 审核上架 完整)
- 用户管理 (CRUD 完整)
- 商户管理 (CRUD 完整)
- 系统配置 (CR 正常)
```

### 4.2 跨端汇总报告（批量验证时生成）

当验证多个前端时，额外生成 `validation-report-summary.md`：

```markdown
# 跨端验证汇总报告

## 验证范围
| 前端 | 角色 | 平台 | Peer Group | 测试方式 | 状态 | 问题数 |
|------|------|------|-----------|---------|------|-------|
| Admin 后台 | super_admin | web | — | Playwright | ✅ 已验证 | 7 |
| 商户后台 | merchant | web | — | Playwright | ✅ 已验证 | 5 |
| 客户 PC 网站 | customer | web | customer | Playwright | ✅ 已验证 | 2 |
| 客户 H5 | customer | h5 | customer | Playwright | ✅ 已验证 | 3 |
| 客户 App | customer | app | customer | patrol | ✅ 已验证 | 4 |
| 客户小程序 | customer | miniprogram | customer | mp_automator | ✅ 已验证 | 6 |

## 全局 CRUD 覆盖率
> 所有前端合计，每个模块的 CRUD 是否被完整覆盖

| 模块 | C | R | U | D | 额外操作 | 全覆盖? |
|------|---|---|---|---|---------|--------|
| 商品 | ✅ admin+merchant | ✅ 全部 | ✅ admin+merchant | ✅ admin | 审核✅ 导入✅ | ✅ |
| 订单 | ✅ customer | ✅ 全部 | ✅ admin | ✅ admin | 发货✅ 退款✅ | ✅ |
| 评价 | ✅ customer | ✅ 全部 | ✅ customer | ✅ admin | 审核✅ 回复✅ | ✅ |
| 优惠券 | ✅ admin+merchant | ✅ 全部 | ✅ admin | ✅ admin | 领取✅ | ✅ |
| 通知 | ✅ admin | ✅ 全部 | ✅ admin | ✅ admin | — | ⚠️ 商户端缺少通知列表 |

## 跨端一致性检查 (Peer Group)
> 同角色 (peer_group=customer) 的多端功能是否一致
> 差异分为：🟢平台专属(正常) vs 🔴核心缺失(问题)

| 模块 | 核心功能 | customer_web | customer_h5 | customer_app | customer_mp | 一致? |
|------|---------|-------------|-------------|-------------|-------------|-------|
| 商品浏览 | R+收藏+加购 | ✅ +对比🟢 | ✅ +微信分享🟢 | ✅ +AR🟢+扫码🟢 | ✅ +分享🟢 | ✅ 核心一致 |
| 下单 | CR+取消 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 评价 | CR | ✅ | ✅ | ✅ | 🔴 缺少评价入口 | ❌ 小程序缺失 |
| 个人中心 | RU | ✅ | ✅ | ✅ +生物识别🟢 | ✅ | ✅ 核心一致 |
| 退款 | 申请退款 | ✅ | ✅ | ✅ | 🔴 无退款入口 | ❌ 小程序缺失 |

> 🟢 = 平台专属差异 (platform_capabilities 中定义的能力)
> 🔴 = 核心功能缺失 (对等端有但此端没有，且非平台限制)

## 🔴 全局问题
> API 提供了操作但所有前端都没有对应入口

| API 端点 | 方法 | 各端是否有入口 | 结论 |
|----------|------|--------------|-----|
| /admin/coupons/batch-delete | DELETE | admin ❌ merchant ❌ | ⚠️ 批量删除无入口 |
| /api/user/avatar | PUT | h5 ❌ app ❌ | 🔴 用户无法更换头像 |
```

### 4.3 修复任务清单

输出 `fix-tasks.json`，每个任务标注归属的前端：

```json
{
  "tasks": [
    {
      "id": "FIX-001",
      "client": "admin",
      "title": "[死链] 侧边栏 > 日报管理 链接404",
      "severity": "critical",
      "module": "导航",
      "description": "菜单中的'日报管理'指向 /reports/daily，但该路由对应的组件不存在",
      "suggestion": "1. 创建日报管理页面组件\n2. 或从菜单配置中移除该入口",
      "file_hints": ["apps/admin/src/config/menu.ts:45"]
    },
    {
      "id": "FIX-002",
      "client": "merchant",
      "title": "[不完整] 商户后台-通知模块缺少列表入口",
      "severity": "high",
      "module": "通知",
      "description": "通知模块在商户后台没有入口，商户无法查看系统通知",
      "suggestion": "在商户后台菜单添加通知列表入口",
      "file_hints": ["apps/merchant/src/config/menu.ts"]
    },
    {
      "id": "FIX-003",
      "client": "customer_h5,customer_app",
      "title": "[不完整] 用户端缺少头像更换功能",
      "severity": "high",
      "module": "个人中心",
      "description": "API 提供了 PUT /api/user/avatar 但 H5 和 App 都没有对应的入口",
      "suggestion": "在个人中心页面添加头像更换功能",
      "file_hints": ["apps/h5/src/pages/profile/", "../flutter-app/lib/pas/profile/"]
    }
  ]
}
```


### 来源文件：`docs/phase5-supplement-test.md`

## Phase 5: 补充测试

> 报告输出后，补充测试用例。包含两部分：
> 1. **补全现有测试的覆盖盲区** — 项目已有测试但覆盖不到的模块/场景
> 2. **为新发现的问题添加回归测试** — 防止问题修复后再次出现

### 5.1 检测项目现有测试模式

先探测项目用了什么测试框架，**按项目现有模式来写测试**：

1. **单元测试框架检测**（按优先级）：
   - 检查 `package.json` 的 devDependencies: `vitest`, `jest`, `mocha`, `ava`
   - 检查配置文件: `vitest.config.*`, `jest.config.*`, `.mocharc.*`
   - 检查现有测试文件位置: `__tests__/`, `*.test.*`, `*.spec.*`

2. **E2E 测试框架检测**：
   - 检查 devDependencies: `playwright`, `cypress`
   - 检查配置文件: `playwright.config.*`, `cypress.config.*`
   - 检查现有 E2E 测试位置: `e2e/`, `tests/`, `cypress/`

3. **确定测试风格**：
   - 读取 2-3 个现有测试文件，学习项目的命名风格、断言方式、组织结构
   - 跟随项目约定（describe/it 风格 vs test 风格，中文描述 vs 英文描述，等）

4. **Flutter 测试框架检测**（当 Phase 0 检测到 Flutter 客户端时）：
   - 检查 `pubspec.yaml` 的 dev_dependencies: `patrol`, `flutter_test`, `integration_test`
   - 检查现有测试位置: `test/`, `integration_test/`, `test_driver/`
   - 检查 Patrol 配置: `patrol.yaml` 或 `pubspec.yaml` 中的 `patrol` 配置
   - 读取 2-3 个现有 `.dart` 测试文件，学习项目的测试风格

### 5.2 分析现有测试覆盖盲区

**在生成新测试之前，先分析项目已有测试的覆盖情况：**

1. **扫描所有测试文件**，建立已覆盖的模块/页面/API 清单
2. **与 Phase 0 的模块列表对比**，找出没有被任何测试覆盖的模块
3. **对已有测试文件做缺口分析**：
   - 有列表测试但没有 CRUD 测试的模块
   - 有正向测试但没有异常/边界测试的场景
   - 有单元测试但没有 E2E 测试的关键流程（或反过来）
   - 路由/导航相关的测试缺失

| 盲区类型 | 说明 | 补测优先级 |
|---------|------|----------|
| 模块完全无测试 | 项目有测试框架，但某些模块一个测试都没有 | 🔴 高 |
| CRUD 覆盖不全 | 只测了列表/查看，没测新增/编辑/删除 | 🔴 高 |
| 关键流程无 E2E | 核心业务流程（下单、支付、审核）没有端到端测试 | 🔴 高 |
| 只有 happy path | 没有异常输入、空数据、权限不足等边界测试 | 🟡 中 |
| 导航/路由无测试 | 菜单链接、面包屑、路由守卫没有测试 | 🟡 中 |

### 5.3 生成测试策略

根据检测到的框架，为**覆盖盲区 + 发现的问题**生成对应类型的测试：

| 项目现有框架 | 生成的测试类型 | 测试内容 |
|------------|-------------|---------|
| 有单元测试 (vitest/jest) | 单元测试 | 路由配置完整性、菜单配置正确性、组件是否存在、未覆盖模块的基础测试 |
| 有 Playwright E2E | Playwright 测试 | 页面可访问性、导航链接有效性、CRUD 流程、未覆盖的关键流程 |
| 有 Cypress E2E | Cypress 测试 | 同上，用 Cypress 语法 |
| 两种都有 | 两种都写 | 单元测试覆盖配置层和逻辑层，E2E 覆盖运行时和关键流程 |
| 有 Patrol (Flutter) | Patrol 测试 | Flutter 端页面可达性、导航有效性、CRUD 流程、错误状态检测 |
| 有 flutter_test | flutter_test 单元测试 | 路由配置完整性、模型序列化、Widget 存在性 |
| 都没有 | 跳过，在报告中建议用户建立测试体系 | — |

### 5.4 测试生成规则

**必须遵循：**

1. **写在项目现有测试目录中**，不要创建新的目录结构。跟随项目现有的文件组织方式
2. **文件命名跟随项目约定**：如果项目用 `*.test.ts` 就用这个后缀，用 `*.spec.ts` 就用那个
3. **不要修改项目现有测试**，只添加新的测试文件
4. **测试分两类文件组织**：
   - `deadhunt-regression.{test|spec}.ts` — 针对本次发现的问题的回归测试
   - `deadhunt-coverage.{test|spec}.ts` — 补全现有测试覆盖盲区的测试
5. **回归测试用例**必须：
   - 关联报告中的问题编号（FIX-001, FIX-002...）
   - 在问题修复前会失败，修复后会通过
6. **覆盖补全用例**必须：
   - 注明补全的模块和缺失的测试类型
   - 覆盖基本的 CRUD 操作和页面可访问性

### 5.5 测试生成示例

**回归测试**（针对发现的问题）：
```typescript
describe('DeadHunt 回归测试', () => {
  it('FIX-001: 侧边栏日报管理链接不应该 404', () => { ... })
  it('FIX-002: 商户后台通知模块应有列表入口', () => { ... })
})
```

**覆盖补全**（现有测试缺失的部分）：
```typescript
describe('DeadHunt 覆盖补全 - 商品管理', () => {
  // 项目原有测试只覆盖了列表，以下补全 CRUD
  it('应能新增商品', () => { ... })
  it('应能编辑商品', () => { ... })
  it('应能删除商品', () => { ... })
  it('空数据时应显示空状态', () => { ... })
})

describe('DeadHunt 覆盖补全 - 路由守卫', () => {
  // 项目原有测试完全没有路由相关测试
  it('未登录访问受保护路由应跳转登录页', () => { ... })
  it('无权限访问应显示 403 页面', () => { ... })
})
```

**Playwright E2E 补全**：
```typescript
test.describe('DeadHunt 覆盖补全 - 订单流程 E2E', () => {
  // 项目原有 E2E 没有覆盖订单模块
  test('完整下单流程: 加购 → 提交 → 支付 → 查看订单', async ({ page }) => { ... })
  test('订单列表分页和筛选', async ({ page }) => { ... })
})
```

**Patrol 回归测试**（Flutter 端发现的问题）：
```dart
// deadhunt-regression.patrol_test.dart
import 'package:patrol/patrol.dart';

void main() {
  patrolTest('FIX-001: 订单 Tab 导航应到达订单页', ($) async {
    await $(BottomNavigationBar).tap();
    await $(#orderTab).tap();
    expect(find.byType(OrderPage), findsOneWidget);
  });

  patrolTest('FIX-002: 订单详情页不应显示 ErrorWidget', ($) async {
    // 导航到订单详情
    await $(ListTile).first.tap();
    expect(find.byType(ErrorWidget), findsNothing);
  });
}
```

**Patrol 覆盖补全**（Flutter 端现有测试缺失的部分）：
```dart
// deadhunt-coverage.patrol_test.dart
import 'package:patrol/patrol.dart';

void main() {
  group('DeadHunt 覆盖补全 - 订单模块', () {
    patrolTest('应能查看订单列表', ($) async {
      await $(#orderTab).tap();
      await $.pumpAndSettle();
      expect(find.byType(ListView), findsOneWidget);
    });

    patrolTest('应能查看订单详情', ($) async {
      await $(ListTile).first.tap();
      expect(find.text('订单详情'), findsOneWidget);
    });

    patrolTest('空数据时应显示空状态', ($) async {
      expect(find.text('暂无数据').evaluate().isNotEmpty ||
             find.byType(EmptyState).evaluate().isNotEmpty, isTrue);
    });
  });

  group('DeadHunt 覆盖补全 - 导航完整性', () {
    patrolTest('所有 BottomNav Tab 应可达', ($) async {
      final tabs = $(BottomNavigationBar).$(BottomNavigationBarItem);
      for (var i = 0; i < tabs.length; i++) {
        await tabs.at(i).tap();
        await $.pumpAndSettle();
        expect(find.byType(ErrorWidget), findsNothing);
      }
    });
  });
}
```

### 5.6 报告中展示补测情况

在报告摘要末尾追加一节：

```
### 🧪 补充的测试

#### 回归测试（针对本次发现的问题）
| 测试文件 | 框架 | 用例数 | 覆盖问题 |
|---------|------|-------|---------|
| src/__tests__/deadhunt-regression.test.ts | vitest | 5 | FIX-001 ~ FIX-005 |
| e2e/deadhunt-regression.spec.ts | playwright | 3 | FIX-001, FIX-002, FIX-006 |

#### 覆盖补全（现有测试的盲区）
| 测试文件 | 框架 | 用例数 | 补全内容 |
|---------|------|-------|---------|
| src/__tests__/deadhunt-coverage.test.ts | vitest | 8 | 商品CRUD、路由守卫、权限校验 |
| e2e/deadhunt-coverage.spec.ts | playwright | 4 | 订单流程E2E、用户中心E2E |

#### 覆盖率变化
| 指标 | 补测前 | 补测后 |
|------|-------|-------|
| 有测试的模块占比 | 6/12 (50%) | 11/12 (92%) |
| CRUD 覆盖完整的模块 | 3/12 (25%) | 9/12 (75%) |
| 有 E2E 的关键流程 | 2/5 (40%) | 5/5 (100%) |

> 运行: `npm test` / `npx playwright test`

#### Flutter 端测试（Patrol）
| 测试文件 | 框架 | 用例数 | 覆盖内容 |
|---------|------|-------|---------|
| integration_test/deadhunt-regression.patrol_test.dart | patrol | 3 | FIX-001, FIX-002, FIX-005 |
| integration_test/deadhunt-coverage.patrol_test.dart | patrol | 6 | 订单模块CRUD、导航完整性 |

> 运行: `patrol test --target integration_test/deadhunt-*.patrol_test.dart`
```

**如果项目没有任何测试框架，在报告中说明：**

```
### 🧪 测试补充

当前项目未检测到测试框架（无 jest/vitest/playwright/cypress）。
建议：
1. 安装测试框架: `npm install -D vitest` 或 `npm install -D playwright`
2. 建立基础测试后，重新运行 `/deadhunt:deadhunt` 会自动补充测试
```


### 来源文件：`docs/quick-start.md`

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
# Claude Code 插件安装
claude plugin add dv/deadhunt-skill
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


### 来源文件：`docs/workflow.md`

## 整体工作流

```
首次使用:                           后续使用:

  Phase 0: 项目分析 ──→ 保存          检测 .allforai/deadhunt/output/
  (Claude 自动初始化)                  (直接跑)
       ↓                  ↓                ↓
  Phase 1: 静态分析      ↓          有 validation-profile.json?
       ↓                  ↓            ├── 有 → 跳过 Phase 0，直接用
  Phase 2: 制定测试计划   ↓            └── 没有 → 走首次流程
       ↓                  ↓
  Phase 3: 深度测试      ↓          有 .auth/*.json?
       ↓                  ↓            ├── 有 → 跳过登录，直接用
  Phase 4: 报告          ↓            └── 没有 → 重新登录
                         ↓
              .allforai/deadhunt/output/    有 上次报告?
              (所有状态都保存在这里)    ├── 有 → 增量对比，只报告变化
                                     └── 没有 → 全量报告
```

### 核心原则：初始化一次，后续复用

```
.allforai/deadhunt/output/
├── validation-profile.json    ← Phase 0 的产出，持久保存
├── static-analysis/           ← Phase 1 的产出，每次更新
│   ├── routes.json
│   ├── crud-coverage.json
│   ├── api-reverse-coverage.json
│   └── bidirectional-matrix.json
├── test-plan.json             ← Phase 2 的产出，profile 不变就不变
├── tests/                     ← 生成的测试脚本，profile 不变就不变
├── reports/                   ← Phase 4 的产出，每次更新
│   ├── dead-links-report.json
│   ├── validation-report-admin.md
│   └── baseline.json          ← 上次的结果快照，用于增量对比
└── fix-tasks.json

.allforai/deadhunt/.auth/
├── admin.json                 ← 登录状态，长期有效（直到 token 过期）
├── merchant.json
└── customer.json
```

### 状态检测与流程决策

Claude 在开始验证时，**第一步**是检查 `.allforai/deadhunt/output/` 下已有的状态：

```typescript
// 概念逻辑 — Claude 应通过 Read/Glob/Grep 工具实现以下检测，而非直接执行此代码

interface ValidationState {
  profile: 'missing' | 'exists' | 'outdated';
  auth: Record<string, 'missing' | 'valid' | 'expired'>;
  static_analysis: 'missing' | 'exists' | 'outdated';
  test_plan: 'missing' | 'exists';
  last_report: 'missing' | 'exists';
}

/**
 * 检测已有状态，决定跳过哪些步骤
 */
async function detectState(validationDir: string): Promise<ValidationState> {
  const fs = require('fs');
  const path = require('path');
  const outputDir = path.join(validationDir, 'output');

  const state: ValidationState = {
    profile: 'missing',
    auth: {},
    static_analysis: 'missing',
    test_plan: 'missing',
    last_report: 'missing',
  };

  // 1. 检查 validation-profile.json
  const profilePath = path.join(outputDir, 'validation-profile.json');
  if (fs.existsSync(profilePath)) {
    const profile = JSON.parse(fs.readFileSync(profilePath, 'utf-8'));
    const profileAge = Date.now() - new Date(profile._meta?.updated_at || 0).getTime();
    const projectMtime = getProjectLastModified(profile.project?.path);

    if (profileAge > 7 * 24 * 3600 * 1000) {
      // 超过 7 天，建议更新（但不强制）
      state.profile = 'outdated';
    } else {
      state.profile = 'exists';
    }
  }

  // 2. 检查 auth state
  const authDir = path.join(validationDir, '.auth');
  if (fs.existsSync(authDir)) {
    const authFiles = fs.readdirSync(authDir).filter((f: string) => f.endsWith('.json'));
    for (const f of authFiles) {
      const clientId = f.replace('.json', '');
      const authData = JSON.parse(fs.readFileSync(path.join(authDir, f), 'utf-8'));

      // 检查 cookie/token 是否过期
      const isExpired = checkAuthExpired(authData);
      state.auth[clientId] = isExpired ? 'expired' : 'valid';
    }
  }

  // 3. 检查静态分析结果
  const staticDir = path.join(outputDir, 'static-analysis');
  if (fs.existsSync(path.join(staticDir, 'routes.json'))) {
    state.static_analysis = 'exists';
  }

  // 4. 检查测试计划
  if (fs.existsSync(path.join(outputDir, 'test-plan.json'))) {
    state.test_plan = 'exists';
  }

  // 5. 检查上次报告
  if (fs.existsSync(path.join(outputDir, 'reports', 'baseline.json'))) {
    state.last_report = 'exists';
  }

  return state;
}

/** 检查 auth state 中的 cookie/token 是否过期 */
function checkAuthExpired(authData: any): boolean {
  if (authData.cookies) {
    const now = Date.now() / 1000;
    return authData.cookies.some((c: any) => c.expires && c.expires > 0 && c.expires < now);
  }
  // localStorage 中的 token 无法从 state 文件判断过期
  // 保守处理：state 文件超过 24 小时视为可能过期
  const stat = require('fs').statSync(authData._path || '');
  return Date.now() - stat.mtimeMs > 24 * 3600 * 1000;
}
```

### 流程决策逻辑

```typescript
// 概念逻辑 — Claude 根据此决策树决定执行哪些 Phase

async function decideWorkflow(state: ValidationState): Promise<Phase[]> {
  const phases: Phase[] = [];

  // ── Profile ──
  if (state.profile === 'missing') {
    console.log('📋 未发现项目配置 — 需要初始化 (Phase 0)');
    phases.push('phase0_analyze');
  } else if (state.profile === 'outdated') {
    console.log('📋 项目配置超过 7 天 — 建议更新，但可以先用旧的');
    // 不强制重新分析，用户可以选择
  } else {
    console.log('✅ 项目配置已存在 — 跳过 Phase 0');
  }

  // ── Auth ──
  // 对每个需要验证的 client 检查 auth
  // 有效的直接用，过期的重新登录，没有的需要初始化
  for (const [clientId, authState] of Object.entries(state.auth)) {
    if (authState === 'valid') {
      console.log(`✅ ${clientId} 登录状态有效 — 直接复用`);
    } else if (authState === 'expired') {
      console.log(`⚠️ ${clientId} 登录状态已过期 — 需要重新登录`);
      phases.push(`auth_${clientId}`);
    }
  }

  // ── 静态分析 ──
  // 静态分析每次都跑（快，且代码可能变了）
  phases.push('phase1_static');

  // ── 测试计划 ──
  if (state.test_plan === 'exists' && state.profile !== 'missing') {
    console.log('✅ 测试计划已存在 — 检查是否需要更新');
    // 如果静态分析发现新的路由/模块，测试计划需要更新
  } else {
    phases.push('phase2_plan');
  }

  // ── 深度测试 ──
  phases.push('phase3_test');

  // ── 报告 ──
  if (state.last_report === 'exists') {
    console.log('📊 发现上次报告 — 将生成增量对比');
  }
  phases.push('phase4_report');

  return phases;
}
```

### profile 中的元信息

`validation-profile.json` 需要记录创建和更新时间：

```json
{
  "_meta": {
    "version": "1.0",
    "created_at": "2026-02-16T10:00:00Z",
    "updated_at": "2026-02-16T14:30:00Z",
    "created_by": "deadhunt skill",
    "project_hash": "abc123",
    "notes": "用户确认过模块分类"
  },
  "project": { ... },
  "clients": [ ... ],
  "modules": [ ... ]
}
```

`project_hash` 是项目关键文件（路由配置、菜单配置、package.json）的哈希值。如果哈希变了，说明项目结构可能变了，建议重新分析。

### 用户交互：初始化 vs 直接跑

Claude 在收到验证请求时的决策流程：

```
用户说: "请验证我的项目"
          │
          ▼
  检查 .allforai/deadhunt/output/validation-profile.json
          │
    ┌─────┴──────┐
    │            │
  不存在        存在
    │            │
    ▼            ▼
  "我来分析      "上次配置还在，
   你的项目..."     直接开跑？"
    │            │
    ▼        ┌───┴───┐
  Phase 0     │       │
  (首次初始化)  用户: 对  用户: 重新分析
    │         │       │
    ▼         ▼       ▼
  请用户确认   跳过 Phase 0  重跑 Phase 0
  模块分类     直接 Phase 1→
```

**关键对话模式：**

```
# 首次使用
用户: 请验证我的项目，路径 /home/david/my-shop。
Claude: 这是第一次验证这个项目，让我先分析结构...
        [执行 Phase 0]
        请确认模块分类...

# 后续使用（有配置）
用户: 请验证我的项目。
Claude: 检测到上次的验证配置（2天前创建，15 个模块）。
        登录状态: admin ✅有效  merchant ✅有效
        直接开始验证？还是需要更新配置？
用户: 直接跑。
Claude: [跳过 Phase 0，直接 Phase 1 → Phase 4]

# 后续使用（配置过期）
用户: 请验证我的项目。
Claude: 检测到上次的验证配置（10天前）。
        但项目路由文件有变更，建议更新配置。
        要更新还是先用旧的？
用户: 更新吧。
Claude: [重跑 Phase 0，但保留之前的模块分类作为参考]

# 后续使用（auth 过期）
用户: 请验证我的项目。
Claude: 项目配置 ✅ 有效。
        但 admin 的登录状态已过期（超过 24 小时）。
        需要重新登录。账号密码还是 admin/123456 吗？
用户: 对。
Claude: [只重新登录，不重跑 Phase 0]
```
