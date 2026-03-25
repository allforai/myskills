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

