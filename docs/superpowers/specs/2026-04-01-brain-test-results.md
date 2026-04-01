# Brain Test: Product Concept Closure Mechanisms

> Mental simulation of the full bootstrap → run → concept-acceptance flow
> across diverse project types to validate the new mechanisms.

---

## Test Project 1: PetMart (宠物电商)

### Product Concept (假设)

```json
{
  "mission": "让宠物主人一站式完成宠物用品选购、健康管理和社区交流",
  "features": [
    "商品浏览与搜索（按宠物种类/品牌/功能筛选）",
    "购物车与结算",
    "在线支付（微信/支付宝/信用卡）",
    "订单管理与物流追踪",
    "宠物健康档案（疫苗记录、体检提醒）",
    "社区帖子（图文分享、评论、点赞）",
    "宠物医生在线咨询",
    "会员积分与等级",
    "优惠券与促销活动",
    "消息推送（订单状态、健康提醒、社区回复）"
  ],
  "errc_highlights": {
    "must_have": ["商品浏览", "购物车", "支付", "订单管理"],
    "differentiators": ["宠物健康档案", "医生在线咨询"],
    "eliminate": ["直播带货", "二手交易"]
  },
  "roles": [
    { "id": "R1", "name": "宠物主人", "app": "mobile-app" },
    { "id": "R2", "name": "宠物医生", "app": "web-admin" },
    { "id": "R3", "name": "运营管理员", "app": "web-admin" }
  ]
}
```

### Bootstrap Step 3: LLM 可能生成的节点

```
1. product-analysis         → 逆向/生成产品地图
2. implement-api            → 后端 API
3. implement-mobile-app     → 移动端 UI
4. implement-admin          → 管理后台
5. demo-forge               → 填充数据
6. e2e-test-mobile          → 移动端 E2E
7. e2e-test-admin           → 管理后台 E2E
```

### Step 3.5 Coverage Self-Check 模拟

**Level 1 — 直接覆盖检查：**

| 功能点 | 覆盖节点 | 状态 |
|--------|---------|------|
| 商品浏览与搜索 | implement-api + implement-mobile-app | covered |
| 购物车与结算 | implement-api + implement-mobile-app | covered |
| 在线支付 | implement-api | covered |
| 订单管理与物流追踪 | implement-api + implement-mobile-app | covered |
| 宠物健康档案 | implement-api + implement-mobile-app | covered |
| 社区帖子 | implement-api + implement-mobile-app | covered |
| 宠物医生在线咨询 | ??? | **GAP** — 实时通信需要 WebSocket/IM 基础设施 |
| 会员积分与等级 | implement-api | covered（但边界情况可能遗漏） |
| 优惠券与促销活动 | implement-api + implement-admin | covered |
| 消息推送 | ??? | **GAP** — 需要推送基础设施（APNs/FCM） |

**Level 2 — 闭环检查：**

| 闭环类型 | 发现 | Ring |
|---------|------|------|
| Exception Closure | 支付失败 → 退款流程缺失 | Ring 1 |
| Lifecycle Closure | 帖子创建 → 帖子删除/归档缺失 | Ring 1 |
| Mapping Closure | 创建订单 ↔ 取消订单缺失 | Ring 1 |
| Config Closure | 推送配置（APNs 证书）→ 无配置节点 | Ring 0 |

**Auto-Fix 动作：**

1. **扩展 implement-api** — 增加 WebSocket 实时通信 goal
2. **新建 setup-push-infra** — 推送基础设施节点（Ring 0）
3. **扩展 implement-api** — 退款流程、订单取消（Ring 1）
4. **扩展 implement-mobile-app** — 帖子删除 UI（Ring 1）

**收敛检查：**
- Ring 0 + Ring 1 共发现 4 个 gap，全部可修复
- 无 scale reversal（每个 gap 都小于父功能）
- 停止：零输出（所有功能 + 一阶闭环已覆盖）

**结论：Step 3.5 有效。** 发现了 LLM 在自由规划时容易遗漏的基础设施类功能（推送、实时通信）和闭环操作（退款、取消、删除）。

---

### Concept-Acceptance 模拟

假设开发完成后：

**静态验收：**

| 维度 | 得分 | 说明 |
|------|------|------|
| 价值主张 | 85 | 一站式体验基本实现 |
| 核心功能 | 90 | must_have 全部实现 |
| 差异化 | 60 | 医生咨询功能实现了但体验差——响应慢，无预约机制 |
| 角色覆盖 | 75 | 医生端管理后台功能简陋 |
| 商业模型 | 80 | 支付流程完整 |
| 删除项 | 100 | 直播和二手交易确认未实现 |

**动态验收（Playwright + Flutter E2E）：**
- 宠物主人流程：商品→购物车→支付→订单 ✅ 流畅
- 宠物主人流程：健康档案→添加疫苗记录→设置提醒 ✅ 基本可用
- 宠物主人流程：发帖→评论→删除帖子 ⚠️ 删除后无确认反馈
- 医生流程：登录→查看咨询→回复 ❌ 回复延迟 5s+，无实时感

**Overall Score: 78/100, verdict: needs_iteration**

Core gap: 医生咨询体验 (severity: core)

**iteration-feedback.json 输出：**
```json
{
  "recommended_actions": [
    { "type": "fix_gap", "target": "医生在线咨询", "suggestion": "WebSocket 实时通信延迟过高，需优化连接管理" },
    { "type": "simplify_flow", "target": "帖子删除", "suggestion": "添加删除确认和成功反馈" },
    { "type": "reconsider_concept", "target": "医生端体验", "suggestion": "医生管理后台过于简陋，建议增加排班/预约功能或降低差异化预期" }
  ]
}
```

**结论：concept-acceptance 有效。** 发现了代码层面"实现了"但体验层面"不好用"的问题（医生咨询延迟），这是 product-verify 无法发现的。

---

## Test Project 2: devctl (开发者 CLI 工具)

### Product Concept (假设)

```json
{
  "mission": "统一管理多云环境的开发者 CLI 工具",
  "features": [
    "多云身份认证（AWS/GCP/Azure 统一登录）",
    "集群管理（列表/切换/状态查看）",
    "日志聚合查看（实时 tail + 搜索）",
    "配置同步（本地↔远端配置双向同步）",
    "插件系统（第三方扩展）"
  ],
  "errc_highlights": {
    "must_have": ["多云认证", "集群管理", "日志查看"],
    "differentiators": ["配置同步", "插件系统"],
    "eliminate": ["GUI 界面", "监控告警"]
  }
}
```

### Step 3.5 模拟

**特殊性：CLI 工具无 UI、无角色（单用户）。**

Step 3.5 需要适配非标准项目类型。按 product-analysis capability 的 Specialization Guidance:
> CLI tool: No roles (single user). Command tree replaces tasks. No screens.

**Level 1 检查：**

| 功能点 | 覆盖节点 | 状态 |
|--------|---------|------|
| 多云身份认证 | implement-auth-module | covered |
| 集群管理 | implement-cluster-module | covered |
| 日志聚合查看 | implement-log-module | covered |
| 配置同步 | implement-sync-module | covered |
| 插件系统 | ??? | **GAP** — LLM 可能遗漏插件加载机制 |

**Level 2 闭环检查：**

| 闭环类型 | 发现 | Ring |
|---------|------|------|
| Config Closure | 多云认证需要凭证存储 → 无凭证管理节点 | Ring 1 |
| Exception Closure | 配置同步冲突 → 无冲突解决逻辑 | Ring 1 |
| Lifecycle Closure | 插件安装 → 插件卸载/更新缺失 | Ring 1 |
| Mapping Closure | 配置推送 ↔ 配置拉取都需要 | covered (双向同步) |

**Auto-Fix：**
1. 新建 implement-plugin-system（Ring 0）
2. 扩展 implement-auth-module — 凭证安全存储（Ring 1）
3. 扩展 implement-sync-module — 冲突解决策略（Ring 1）
4. 扩展 implement-plugin-system — 卸载/更新命令（Ring 1）

**结论：Step 3.5 对非标准项目类型同样有效。** CLI 没有 UI/角色但闭环思维仍适用——凭证存储、冲突解决、插件生命周期都是典型闭环缺失。

---

### Concept-Acceptance 模拟（CLI 特殊性）

**动态验收工具：Shell script execution**（不是 Playwright）

验收方式：
```bash
# 认证流程
devctl auth login --provider aws → 验证能否完成 OAuth
devctl auth status → 验证凭证已存储

# 集群管理
devctl cluster list → 验证输出格式
devctl cluster switch prod → 验证切换成功

# 日志
devctl logs tail -f myservice → 验证实时输出
devctl logs search "error" --since 1h → 验证搜索

# 配置同步
devctl config push → 验证上传
devctl config pull → 验证下载
devctl config diff → 验证冲突检测

# 插件
devctl plugin install myplugin → 验证安装
devctl plugin list → 验证列出
devctl plugin remove myplugin → 验证卸载
```

**结论：concept-acceptance 对 CLI 项目可行。** 用 shell 脚本替代 Playwright，验收逻辑不变。bootstrap 根据 tech_stacks 特化工具选择机制正确工作。

---

## Test Project 3: DungeonCraft (Roguelike 手游)

### Product Concept (假设)

```json
{
  "mission": "程序生成地牢 + 策略战斗 + 装备收集的单机 Roguelike",
  "features": [
    "程序生成地牢（每层随机布局、怪物配置、宝箱分布）",
    "回合制战斗系统（攻击/防御/技能/道具）",
    "装备系统（武器/防具/饰品，随机词缀）",
    "角色成长（经验值/等级/技能树）",
    "商店系统（金币购买/出售装备）",
    "排行榜（最深层数/最高伤害/最快通关）",
    "每日挑战（固定种子地牢）",
    "成就系统"
  ],
  "errc_highlights": {
    "must_have": ["地牢生成", "战斗系统", "装备系统", "角色成长"],
    "differentiators": ["每日挑战", "随机词缀装备"],
    "eliminate": ["多人联机", "内购"]
  }
}
```

### Step 3.5 模拟

**特殊性：游戏项目，产品分析需要特殊处理。**

按 product-analysis capability:
> Game: Roles = player types. System spec replaces tasks. Config schema replaces constraints.

**Level 1 检查：**

LLM 可能生成的节点：
```
1. design-core-combat-loop
2. design-dungeon-generation
3. design-loot-economy
4. implement-combat-system
5. implement-dungeon-generator
6. implement-inventory-ui
7. implement-shop
8. e2e-test (Flutter integration)
```

| 功能点 | 覆盖节点 | 状态 |
|--------|---------|------|
| 程序生成地牢 | design-dungeon-generation + implement-dungeon-generator | covered |
| 回合制战斗 | design-core-combat-loop + implement-combat-system | covered |
| 装备系统 | design-loot-economy + implement-inventory-ui | covered |
| 角色成长 | ??? | **GAP** — 没有专门的经验值/等级/技能树节点 |
| 商店系统 | implement-shop | covered |
| 排行榜 | ??? | **GAP** — 纯单机但排行榜需要本地持久化 |
| 每日挑战 | ??? | **GAP** — 固定种子机制需要日期→种子映射 |
| 成就系统 | ??? | **GAP** — 事件监听 + 条件判断 + 持久化 |

**Level 2 闭环检查：**

| 闭环类型 | 发现 | Ring |
|---------|------|------|
| Lifecycle Closure | 角色死亡 → 存档清除 + 排行榜记录 | Ring 1 |
| Config Closure | 难度配置（怪物数值表）→ 无配置节点 | Ring 1 |
| Mapping Closure | 装备获取 ↔ 装备丢弃/分解 | Ring 1 |
| Exception Closure | 战斗中 app 崩溃 → 战斗状态恢复 | Ring 1 |

**Auto-Fix：**
1. 新建 implement-progression-system — 经验值/等级/技能树（Ring 0）
2. 新建 implement-meta-features — 排行榜 + 每日挑战 + 成就（Ring 0）
3. 扩展 implement-combat-system — 战斗状态持久化/恢复（Ring 1）
4. 扩展 implement-inventory-ui — 装备分解 UI（Ring 1）
5. 扩展 design-loot-economy — 数值配置表（Ring 1）

**收敛：** Ring 0 补了 2 个节点，Ring 1 扩展了 3 个。未触发 scale reversal。停止。

**结论：Step 3.5 对游戏项目有效。** 游戏的"系统"本质上也是功能点，闭环思维同样适用（角色死亡→存档管理、装备获取→分解）。

---

### Concept-Acceptance 模拟

**动态验收工具：Flutter integration_test/**

```dart
// 核心流程：进入地牢 → 战斗 → 获得装备 → 升级
testWidgets('core gameplay loop', (tester) async {
  // 1. 开始新游戏
  await tester.tap(find.text('New Game'));
  // 2. 进入地牢第一层
  expect(find.byType(DungeonView), findsOneWidget);
  // 3. 遇到怪物，进入战斗
  await tester.tap(find.byType(EnemySprite));
  expect(find.byType(CombatView), findsOneWidget);
  // 4. 使用攻击，击败怪物
  await tester.tap(find.text('Attack'));
  // 5. 获得装备
  expect(find.byType(LootDialog), findsOneWidget);
  // 6. 检查经验值增长
  expect(playerExp, greaterThan(0));
});
```

**可能发现的体验问题：**
- 战斗节奏太慢（每回合动画 2s+，概念说的是"策略战斗"不是"慢战斗"）
- 装备随机词缀不够随机（总是出同样的词缀组合）
- 角色死亡后没有"再来一次"按钮（Navigation Closure gap）

**结论：concept-acceptance 对游戏同样有效。** "战斗节奏"这类体验问题只有动态验收能发现。

---

## Test Project 4: 边界测试 — 无 product-concept.json 的项目

### 场景

用户运行 `/bootstrap` 选择 (e) 代码治理，目标是 `goals: ["tune"]`。没有 product-concept.json。

### Step 3.5 行为

**Trigger 检查：** `has_product_concept` = false → **跳过 Step 3.5**。

### Concept-Acceptance 行为

**Auto-append 检查：** goals 不包含 translate/rebuild/create → **不追加 concept-acceptance 节点**。

### 结论

对不需要概念闭环的工作流（治理、分析、质量检查），两个新机制完全透明——不干扰、不增加开销。

---

## Test Project 5: 迭代场景 — 第二轮 bootstrap

### 场景

PetMart 第一轮 concept-acceptance 失败（score 78），生成了 iteration-feedback.json。用户调整了概念（降低医生咨询优先级），重新运行 `/bootstrap`。

### Step 1.0 检测

```
has_product_concept: true
has_iteration_feedback: true  ← 新检测
has_bootstrap: true
has_code: true
has_product_artifacts: true
```

### Step 2.5 加载

读取 iteration-feedback.json：
- 上轮得分 78，verdict: needs_iteration
- Gap: 医生咨询体验差
- User decision: "医生咨询降为 v2 功能"

### Step 3 规划

LLM 参考反馈：
- 不再为医生咨询生成实时通信节点（用户决策）
- 重点修复帖子删除反馈、推送稳定性
- concept-acceptance 节点的 pass_threshold 不变

### Step 3.5 覆盖率检查

product-concept.json 已更新（医生咨询从 must_have 移到 post_launch）：
- 所有 must_have 功能有对应节点 ✓
- 闭环检查通过 ✓
- 覆盖率 100%

### 第二轮 Concept-Acceptance 预期

- 医生咨询不再是 must_have → 不影响 core gap 判定
- 帖子删除修复 → score 提升
- Overall score: 88 → **pass**

### 结论

迭代机制有效。iteration-feedback.json 正确驱动了第二轮规划：
1. 用户决策被尊重（医生咨询推迟）
2. 上轮 gap 被优先修复
3. 第二轮通过验收

---

## 发现的问题和改进建议

### 问题 1: Step 3.5 的 "Skip to Step 3.4" 措辞

当前写的是 "skip to Step 3.4"，但 Step 3.4 的编号在 3.5 之后。读者可能困惑。

**建议：** 改为 "skip to Step 3.4 (Confirm with User)"，明确目标。

**严重程度：** Minor（措辞优化）

### 问题 2: concept-acceptance 的 pass_threshold 硬编码为 80

不同类型项目的验收标准应该不同：
- MVP/原型：60 可能就够了
- 正式产品：80 合理
- 高标准消费品：90+

**建议：** 在 bootstrap-profile.json 中增加 `acceptance_threshold` 字段，默认 80，用户在 Step 1.5 可自定义。concept-acceptance 读取此值而非硬编码。

**严重程度：** Important（影响不同项目类型的适用性）

### 问题 3: CLI/API-only 项目的动态验收证据

对 CLI 项目，"截图"不适用。当前 concept-acceptance 说 "capture evidence (screenshots/recordings/logs per platform)"，但没有明确 CLI 的证据格式。

**建议：** 在 capability 文件中补充 CLI 证据规范：command output + exit code + timing。

**严重程度：** Minor（capability 只定义原则，具体由 bootstrap 特化）

### 问题 4: 多平台项目的 concept-acceptance 拆分

PetMart 有 mobile + admin 两个前端。当前设计的 Composition Hints 提到 "Split Static vs Dynamic"，但没说按平台拆。如果 mobile 通过但 admin 失败，整个 verdict 是 needs_iteration，但反馈应该区分。

**建议：** acceptance-report.json 的 dimensions 增加 per-platform breakdown。

**严重程度：** Minor（影响反馈精度，不影响功能）

### 问题 5: iteration-feedback 的 user_decisions 填充时机

当前设计说 "user_decisions 在用户做出选择后由下一轮 bootstrap 记录"。但 bootstrap Step 1.5 是收集用户目标，不是收集对上轮反馈的决策。

**建议：** 在 Step 2.5 加载 iteration-feedback 后，如果有 recommended_actions 且 user_decisions 为空，用 AskUserQuestion 让用户确认每个建议的处置方式。但这可能违反"不打断执行流"的原则。

**替代方案：** LLM 在 Step 3 规划时根据用户在 Step 1.5 选择的目标 + 修改后的 product-concept.json 自动推断 user_decisions，无需额外交互。

**严重程度：** Medium（影响迭代闭环的完整性）
