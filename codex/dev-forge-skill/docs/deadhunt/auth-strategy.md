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
