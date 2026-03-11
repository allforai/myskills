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

详见 `${CLAUDE_PLUGIN_ROOT}/docs/deadhunt/fieldcheck/extractors.md`。

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

详见 `${CLAUDE_PLUGIN_ROOT}/docs/deadhunt/fieldcheck/matching.md`。

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

详见 `${CLAUDE_PLUGIN_ROOT}/docs/deadhunt/fieldcheck/matching.md` 的"全链路矩阵交叉验证"章节。

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

详见 `${CLAUDE_PLUGIN_ROOT}/docs/deadhunt/fieldcheck/report.md`。

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
