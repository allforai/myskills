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

