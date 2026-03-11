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
