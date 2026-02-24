# Demo Forge — 执行流程与规范总览

> 本文档是 demo-forge 技能的中枢文档，定义执行流程、模式、交互规范和铁律。

---

## 1. 执行流程总览

```
Step 0: 项目分析
  │  扫描数据模型（struct/entity/model）+ API 端点（Controller/Handler/View）
  │  检测 API 缺口（有模型无端点、有创建无上传等）
  │  输出: project-analysis.json, api-gaps.json
  │  ▸ 用户确认模型 + API 映射 + API 缺口
  ▼
Step 1: 行业画像
  │  根据用户提供的行业关键词，通过 WebSearch 提取风格维度
  │  （名称风格、价格范围、分类结构、图片关键词、数据量级）
  │  输出: industry-profile.json
  │  ▸ 用户确认行业风格
  ▼
Step 2: 数据规划
  │  基于数据模型 + 行业画像，生成完整数据计划
  │  （实体列表、字段风格、依赖排序、图片需求汇总）
  │  输出: forge-plan.json
  │  ▸ 用户确认数据量 + 字段风格 + 创建顺序
  ▼
Step 3: 素材采集                              ← 需要应用运行（fill 模式从此开始）
  │  按 forge-plan.json 的 image_requirements 采集图片
  │  来源: 竞品网站（优先）→ Unsplash → Pexels → 占位图（兜底）
  │  输出: assets-manifest.json, assets/ 目录
  │  （自动执行，无需用户确认）
  ▼
Step 4: 数据灌入
  │  登录 → 按 creation_order 逐实体调用 API 创建数据 → 上传图片
  │  记录每条数据的创建状态和返回 ID
  │  灌入过程中发现的 API 缺口合并到 api-gaps.json
  │  输出: forge-log.json, forge-data.json, api-gaps.json（更新）
  │  （自动执行，无需用户确认）
  ▼
Done — 灌入日志 + 数据清单 + API 缺口报告
```

---

## 2. 执行模式

| 模式 | 参数 | 执行步骤 | 需要应用运行 | 适用场景 |
|------|------|----------|-------------|----------|
| **full**（默认） | 无参数 或 `full` | Step 0 → 1 → 2 → 3 → 4 | 是 | 首次灌入，完整流程 |
| **plan** | `plan` | Step 0 → 1 → 2 | 否 | 先规划，看看数据计划对不对，不需要启动应用 |
| **fill** | `fill` | Step 3 → 4 | 是 | 加载已有 forge-plan.json，直接采集素材 + 灌入 |
| **clean** | `clean` | 根据 forge-data.json 逆序 DELETE | 是 | 清理已灌入的演示数据 |

### 模式前置条件

```
full / plan      → 无前置条件，从零开始

fill             → 必须已有 forge-plan.json
                   否则提示: "请先运行 /demo-forge plan 生成数据规划"

clean            → 必须已有 forge-data.json
                   否则提示: "未找到 forge-data.json，无数据可清理"
```

---

## 3. 交互模式

### 核心原则：Step 0-2 必须有用户确认，Step 3-4 自动执行

Step 0-2 是分析和规划阶段，决策权在用户；Step 3-4 是执行阶段，按已确认的计划自动运行。

### 确认检查点

| Step | 确认内容 | 询问方式 |
|------|----------|----------|
| Step 0 | 数据模型识别 + API 映射 + API 缺口 | "我识别到以下数据模型和 API 映射：{列表}。发现以下 API 缺口：{列表}。请确认是否准确？" |
| Step 1 | 行业风格维度 | "基于 {行业} 行业，我提取了以下风格参考：{名称风格/价格范围/图片关键词}。是否需要调整？" |
| Step 2 | 数据量 + 字段风格 + 创建顺序 | "数据规划如下：{实体}×{数量}，创建顺序：{顺序}。每个实体的数据量和字段风格满意吗？" |
| Step 3 | 无需确认 | 按 forge-plan.json 自动下载素材 |
| Step 4 | 无需确认 | 按 creation_order 自动灌入数据 |

### 交互流程示意

```
Claude: [执行 Step N]
Claude: "Step N 完成。结果如下：..."
Claude: "请确认以上结果，或指出需要调整的地方。"
        ← 等待用户回复 →
用户:   "Product 的数量改成 80 个"
Claude: "已更新。确认继续下一步？"
用户:   "继续"
Claude: [执行 Step N+1]
```

**禁止行为**：
- 不得将多个 Step 合并执行后一次性展示
- 不得在用户未回复时自动跳到下一个 Step（Step 0-2）
- 不得用 "如果没问题我继续了" 然后不等回复就继续
- Step 3-4 则相反：确认 Step 2 后应自动连续执行，无需中间等待

---

## 4. 输出文件

所有输出文件位于项目根目录下的 `.allforai/seed-forge/` 目录：

| 文件 | 产出 Step | 内容 | 格式 |
|------|-----------|------|------|
| `project-analysis.json` | Step 0 | 数据模型列表 + API 端点映射（model → endpoint） | JSON |
| `api-gaps.json` | Step 0 + Step 4 | API 缺口报告（静态分析 + 灌入实测合并） | JSON |
| `industry-profile.json` | Step 1 | 行业画像（名称风格、价格范围、图片关键词等） | JSON |
| `forge-plan.json` | Step 2 | 完整数据规划（实体、字段、数量、依赖、图片需求） | JSON |
| `assets-manifest.json` | Step 3 | 素材清单（每张图片的来源 URL + 本地路径 + 许可证） | JSON |
| `assets/` | Step 3 | 下载的图片文件（按实体分子目录） | 目录 |
| `forge-log.json` | Step 4 | 灌入日志（每条数据的创建状态：成功/失败/跳过） | JSON |
| `forge-data.json` | Step 4 | 已创建数据清单（含返回 ID，供 clean 和 fill 使用） | JSON |

### 目录结构

```
your-project/
└── .allforai/seed-forge/
    ├── project-analysis.json    # Step 0: 数据模型 + API 映射
    ├── api-gaps.json            # Step 0+4: API 缺口报告
    ├── industry-profile.json    # Step 1: 行业画像
    ├── forge-plan.json          # Step 2: 数据规划
    ├── assets-manifest.json     # Step 3: 素材清单
    ├── assets/                  # Step 3: 下载的图片
    │   ├── avatars/
    │   ├── products/
    │   └── banners/
    ├── forge-log.json           # Step 4: 灌入日志
    └── forge-data.json          # Step 4: 已创建数据清单
```

---

## 5. 铁律速查

| # | 铁律 | 一句话 | 违规示例 |
|---|------|--------|----------|
| 1 | **竞品优先** | 优先爬竞品真实图片（仅限内部演示），Unsplash/Pexels 兜底，不访问登录页 | ~~只用免费图库不用竞品图~~ |
| 2 | **灌入走 API，清理走数据库** | 灌入通过 API 保证一致性，清理直连数据库求速度 | ~~`INSERT INTO products ...`~~ |
| 3 | **可清理** | 灌入的所有数据都可通过 `clean` 命令删除 | ~~灌入后不记录 ID，无法回滚~~ |
| 4 | **用户确认** | Step 0-2 每步确认，不自动灌入 | ~~分析完直接开始调 API 创建数据~~ |
| 5 | **API 缺口如实报告** | 发现缺口就报告，不替用户补 API | ~~自动生成缺失的 API 端点代码~~ |

### 速记口诀

```
竞品优先 — 爬竞品真实图片，图库兜底
不碰数据库 — 统一走 API
可清理 — 灌了能删，forge-data.json 记账
用户确认 — 规划阶段用户说了算
如实报告 — 发现缺口只报告不动手
```

---

## 6. 与 feature-audit 的协同

demo-forge 在分析 API 和灌入数据的过程中，天然能发现 API 缺口（有模型无端点、有创建无上传等）。这些缺口报告可与 feature-audit 的审计结果交叉印证。

### 协同示意

```
feature-audit 发现:                    demo-forge 验证:
PF-005 订单导出 → PARTIAL              灌入订单数据后 → 导出功能可实测
PF-003 批量导入 → MISSING              尝试灌入时 → 确认无批量创建 API

demo-forge 发现:                       feature-audit 可印证:
Product 模型无 POST API → API_GAP      PF-008 商品管理 → PARTIAL (无创建功能)
上传接口 404 → API_GAP                 闭环验证 → Step B 操作不可执行
```

### 协同方式

| 场景 | feature-audit 视角 | demo-forge 视角 | 交叉价值 |
|------|-------------------|-----------------|----------|
| 有模型无创建 API | 功能 PARTIAL（无创建入口） | `API_GAP: 无创建接口` | 双重确认功能缺失 |
| 上传接口异常 | 闭环 Step B 断裂（操作不可执行） | `API_GAP: 上传接口 404` | 定位到具体 API 层面 |
| 批量操作缺失 | MISSING（需求有但未实现） | 灌入效率低（无批量端点） | 印证需求未实现 |

feature-audit 从**需求层**检查功能完整性，demo-forge 从**数据层**检查 API 可用性。两者结合，缺口无处遁形。

---

## 7. 增量运行

### forge-plan.json 和 forge-data.json 的持久化作用

`forge-plan.json` 和 `forge-data.json` 是增量运行的基础，使得 `fill` 和 `clean` 模式无需重新执行分析和规划。

### fill 模式：跳过分析，直接灌入

```
/demo-forge fill
      │
      ▼
  检查 .allforai/seed-forge/forge-plan.json 是否存在
      │
      ├── 不存在 → 报错: "请先运行 /demo-forge plan 生成数据规划"
      │
      └── 存在 → 加载 forge-plan.json
            │
            ▼
      Step 3: 按 image_requirements 采集素材
            │
            ▼
      Step 4: 按 creation_order 灌入数据
            │
            ▼
      生成 forge-log.json + forge-data.json
```

### 典型使用场景

```
第一次: /demo-forge plan          → 执行 Step 0-2，用户确认数据规划
        （用户调整 forge-plan.json 中的数据量或字段风格）
第二次: /demo-forge fill          → 执行 Step 3-4，按调整后的规划灌入
第三次: /demo-forge clean         → 清理灌入的数据
第四次: /demo-forge fill          → 重新灌入（换一批数据做演示）
```

### 持久化的关键数据

| 文件 | 持久化内容 | 被谁消费 |
|------|-----------|----------|
| `forge-plan.json` | 实体列表、字段风格、数量、creation_order、image_requirements | `fill` 模式读取，跳过 Step 0-2 |
| `forge-data.json` | 每条已创建数据的 entity + ID + API 端点 | `clean` 模式读取，执行 DELETE |
| `api-gaps.json` | 静态分析 + 灌入实测的缺口合集 | 用户参考，与 feature-audit 交叉印证 |

---

## 8. clean 机制

**灌入走 API，清理走数据库。** 灌入时通过 API 保证业务逻辑一致性，清理时直接连数据库批量删除，速度快。

### forge-data.json 的记账结构

`forge-data.json` 记录灌入过程中每条成功创建的数据，包含 ID 和表名以支持数据库直删：

```json
{
  "_meta": {
    "forged_at": "2026-02-24T15:30:00Z",
    "base_url": "http://localhost:8080",
    "total_created": 135
  },
  "created": [
    {
      "entity": "Category",
      "table": "categories",
      "id": "cat-001",
      "api": "POST /api/categories",
      "created_at": "2026-02-24T15:30:01Z",
      "order": 1
    },
    {
      "entity": "User",
      "table": "users",
      "id": "user-001",
      "api": "POST /api/users",
      "created_at": "2026-02-24T15:30:02Z",
      "order": 2
    },
    {
      "entity": "Product",
      "table": "products",
      "id": "prod-001",
      "api": "POST /api/products",
      "depends_on": ["cat-001"],
      "created_at": "2026-02-24T15:30:05Z",
      "order": 3
    }
  ]
}
```

### 两种清理方式

| 方式 | SQL | 适用场景 | 需要确认 |
|------|-----|----------|----------|
| **精确删除**（默认） | `DELETE FROM {table} WHERE id IN (...)` | 数据库有其他数据需保留 | 一次确认 |
| **整表清空** | `TRUNCATE TABLE {table} CASCADE` | 纯演示环境，清空重来 | **二次确认** |

### 逆序删除：先删子表，再删父表

```
灌入顺序 (creation_order):          清理顺序 (reverse):
1. Category                         1. Order        ← 先删最后创建的
2. User                             2. Product
3. Product                          3. User
4. Order                            4. Category     ← 最后删最先创建的
```

### clean 执行流程

```
/demo-forge clean
      │
      ▼
  检查 .allforai/seed-forge/forge-data.json 是否存在
      │
      ├── 不存在 → 报错: "未找到 forge-data.json，无数据可清理"
      │
      └── 存在 → 加载 forge-data.json
            │
            ▼
      获取数据库连接
      │   优先从项目配置自动检测(.env, prisma, ormconfig, settings.py)
      │   检测不到 → 询问用户
            │
            ▼
      询问清理方式: 精确删除（默认） / 整表清空（需二次确认）
            │
            ▼
      按逆序分表执行 SQL
      │   精确: DELETE FROM {table} WHERE id IN (...)
      │   清空: TRUNCATE TABLE {table} CASCADE
            │
            ▼
      更新 forge-data.json（精确模式：移除已删除的记录）
      输出清理摘要
```

### clean 的安全设计

| 安全措施 | 说明 |
|----------|------|
| 精确删除默认 | 只删 forge-data.json 中记录的 ID，不误删其他数据 |
| 整表清空需二次确认 | 明确告知用户"会删除所有数据"后才执行 |
| 逆序删除 | 避免外键约束报错 |
| 从项目配置读取连接 | 不要求用户手输数据库密码 |
| 精确模式实时更新 forge-data.json | 断点可续 |
| 图片素材不删除 | 本地图片可复用，用户手动 rm 即可 |
| 竞品爬取仅限公开页 | 不访问登录页面，不复制竞品文案，图片仅用于内部演示 |
