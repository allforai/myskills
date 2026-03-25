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

