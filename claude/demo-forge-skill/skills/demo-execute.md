---
name: demo-execute
description: >
  Use when the user asks to "populate demo data", "fill demo environment",
  "demo-execute", "灌入演示数据", "生成演示数据", "demo populate",
  or mentions data population, demo data generation, database seeding.
  Requires demo-plan.json + style-profile.json + upload-mapping.json.
  Requires a running application for API-based data population.
version: "2.0.0"
---

# Demo Execute — 数据生成与灌入

> 把设计方案变成应用里的真实数据。

## 定位

```
demo-forge 内部三阶段:
  demo-design            →  media-forge + demo-execute（本技能）  →  demo-verify
  规划该生成什么数据          采集素材 + 灌入数据                       打开产品逐项验证
  纯设计不执行               消费设计方案                             产出问题清单路由回修
```

**本技能职责**：消费 demo-plan + style-profile + upload-mapping，生成具体数据记录并灌入运行中的应用。

---

## 前提

| 条件 | 来源 | 说明 |
|------|------|------|
| `demo-plan.json` | demo-design | 演示数据方案（实体、链路、约束、枚举、时间分布） |
| `style-profile.json` | demo-design | 行业风格 + 文本模板 |
| `upload-mapping.json` | media-forge | 本地素材 -> 服务端 URL/ID 映射 |
| 应用运行中 | 用户 | API 可访问 |

四项缺任何一项则终止并提示用户补齐。

---

## 快速开始

```
/demo-forge execute            # 完整流程（E1-E3）
/demo-forge execute --dry-run  # 仅生成数据，不灌入（只跑 E1-E2）
/demo-forge clean              # 清理已灌入数据
```

---

## 工作流

### E1: 数据生成（确定性为主）

读取 `demo-plan.json` + `style-profile.json` + `upload-mapping.json`，按场景链路逐条生成记录。

**字段生成策略**：

| 字段类型 | 生成方式 |
|---------|---------|
| 文本字段 | 从 style-profile 模板随机选取，相邻记录不重复 |
| 数值字段 | 在约束范围内取值 + 包含边界值 |
| 时间字段 | 加权采样（近密远疏分布 + 工作时间集中 + 月度波动 ±15%） |
| 状态字段 | 按枚举覆盖需求分配，确保每个值都有记录（含终态/异常态） |
| 媒体字段 | 直接读 upload-mapping.json 的 server_url / server_id |
| 外键字段 | 链路依赖自动关联（父 -> 子顺序生成，子引用父的临时 ID） |
| 派生字段 | 数学计算（汇总 = 明细之和，计数 = 实际记录数） |

**行为分布**：

```
10% 重度用户 -> 产生 ~50% 的数据
30% 普通用户 -> 产生 ~35% 的数据
60% 轻度用户 -> 产生 ~15% 的数据
```

**输出**：`forge-data-draft.json`（所有记录使用临时 ID，如 TEMP-001、TEMP-002）。

---

### E2: 灌入前自检

逐项确认数据质量，发现问题分两类处理：

```
□ 实体完整性 — 无零记录实体（每个实体至少有一条数据）
□ 枚举覆盖   — 每个状态字段所有值都有记录（包括终态/异常态 REJECTED/CANCELED/EXPIRED/FAILED）
□ 外键完整性 — 每个外键 ID 在数据集中都有对应记录
□ 派生一致性 — 汇总字段 = 明细之和，计数字段 = 实际记录数
□ 时间逻辑   — created_at < updated_at，父实体时间早于子实体
□ 媒体关联   — 所有媒体字段引用 upload-mapping 条目（无外部 URL）
□ 行为分布   — 重度用户产生约 50% 的数据
□ 文本去重   — 无相邻记录使用完全相同的文本
```

**处理方式**：
- 数学类问题（派生不一致、计数错误）：**自动修正**
- 其他问题：标记为 `PREFLIGHT_ISSUE`，汇报给用户

`--dry-run` 模式在 E2 完成后停止，不进入 E3。

---

### E3: 数据灌入（全部走 API）

**核心原则**：灌入过程即集成测试 — 每次 API 调用验证认证、权限、校验、业务逻辑、级联、派生字段。灌入失败 = 真实 BIZ_BUG，直接记录到 forge-log 交给修复流程。

**灌入顺序由依赖关系决定**（父先于子），全部通过 API 端点：

```
1. 用户账号（所有场景链路依赖用户）
2. 配置/字典数据（通过管理 API 创建）
3. 业务数据：按场景优先级（高频 → 中频 → 低频）
   - 每个场景内按链路顺序：父实体 → 子实体 → 关联实体
```

**API_MISSING_BLOCKER 处理**：

若某实体在 `api-gaps.json` 中标记为 `API_MISSING_BLOCKER`，处理方式：
- 跳过该实体及其依赖的子实体链路
- 输出到 `.allforai/demo-forge/api-gap-tasks.md` 供 dev-forge 补建 API
- forge-log 记录阻断原因，提示用户先补 API 再重灌

**UPSTREAM_DEFECT 信号**：发现 `API_MISSING_BLOCKER` 时，除记录到 forge-log 外，还必须在阶段摘要中返回 UPSTREAM_DEFECT 信号：
{"signal":"UPSTREAM_DEFECT","source_phase":"demo-forge.execute","target_phase":"dev-forge.task-execute","defect_type":"API_MISSING_BLOCKER","evidence":"<具体缺失的 API 端点列表>","severity":"blocker","suggested_fix":"补建缺失的 API 端点，详见 api-gap-tasks.md"}

**失败处理策略**：
- **独立实体失败**：写入日志（含 API 响应状态码和错误体），继续灌入其他实体。灌入失败 = 真实 BIZ_BUG，记录到 forge-log
- **父实体失败**：跳过该链路下所有子实体（避免外键悬空），整条链路标记为 `CHAIN_FAILED`
- **灌入结束**：汇总失败链路数量和原因，提示用户排查后可重试

**派生字段**：全部由 API 业务逻辑自动计算（聚合、计数、余额、索引），无需手动修正。若 API 返回的派生字段与预期不符，视为 BIZ_BUG 记录到 forge-log。

**输出**：
- `forge-data.json` — 已创建数据清单（临时 ID 替换为真实服务端 ID）
- `forge-log.json` — 灌入日志（每条记录的操作状态）

---

### E5: 界面覆盖验证（灌入后即时检查）

> **下游消费是上游质量最好的保证。** 灌入完成后立即验证每个界面有数据，不留到 verify 阶段才发现空页面。

**执行方式**: `subagent` — 主流程 dispatch subagent 执行覆盖检查，自身继续准备 forge-data.json 的输出。subagent 发现空页面则主流程回到 E3 补灌。

**subagent 任务描述**:
> 加载 `page-entity-mapping.json`。对每个界面条目，检查其依赖的实体在数据库中是否有记录。
> 若 `page-entity-mapping.json` 不存在，阅读客户端代码自行发现界面清单和数据依赖。
> 返回覆盖检查结果：每个界面的实际记录数 vs 要求记录数。

**subagent 输入**: `page-entity-mapping.json`（或项目根目录）+ 数据库连接信息
**subagent 输出**: 覆盖检查结果 JSON（界面名、实际记录数、是否达标）

**主流程收到结果后**：
- 记录数 < `min_records` 的界面 → **立即补灌**（回到 E3 针对该实体补充数据）
- 补灌后再次 dispatch subagent 检查，直到所有界面的数据需求满足

**输出**：更新 `forge-log.json`，追加 E5 覆盖检查记录。

---

## forge-data-draft.json vs forge-data.json

| 文件 | 产出阶段 | ID 类型 | 用途 |
|------|---------|---------|------|
| `forge-data-draft.json` | E1 生成后 | 临时占位（TEMP-001） | 数据蓝图，clean 后可复用 |
| `forge-data.json` | E3 灌入后 | 真实服务端 ID | clean 和 verify 的依据 |

draft 保留不删，clean 后可直接重灌不必重新生成数据。

---

## Clean 模式

`/demo-forge clean` 读取 `forge-data.json`，按灌入逆序删除所有已灌入数据。

**清理顺序**（与灌入相反，确保外键约束不报错）：

```
1. 子实体 → 父实体（按 forge-data.json 记录的灌入顺序逆序）
2. 用户账号（最后删除，其他实体可能引用 user_id）
3. 配置/字典数据
```

**清理方式**：
- 优先走删除 API（与灌入一致，触发级联清理逻辑）
- 按 `forge-data.json` 中记录的 `id` 和删除端点逐条或批量删除
- 若有 cascade delete 配置，只需删除顶层父实体；若无，严格按逆序逐层删除

**清理范围**：
- 清空 `forge-data.json`、`forge-log.json`
- **保留** `demo-plan.json`、`style-profile.json`、`assets/`、`upload-mapping.json`（设计方案 + 素材不删，方便复用）
- **保留** `forge-data-draft.json`（可直接重灌）

---

## 重入模式

当 `verify-issues.json` 中存在 `route_to="execute"` 的问题项时，进入重入模式——只修复问题，不全量重灌：

| 问题类型 | 处理方式 |
|---------|---------|
| 外键断裂 | 检查 forge-data.json，通过 API 补灌缺失的父记录或修正外键指向 |
| CHAIN_FAILED | 重试该链路的完整 API 灌入 |
| 派生不一致 | 视为 BIZ_BUG，记录到 forge-log 路由给 dev-forge 修复业务逻辑 |
| API_MISSING_BLOCKER | 等待 dev-forge 补建 API 后重试灌入 |

---

## 输出文件

| 文件 | 路径 | 说明 |
|------|------|------|
| `forge-data-draft.json` | `.allforai/demo-forge/` | E1 生成的完整数据集（临时 ID） |
| `forge-data.json` | `.allforai/demo-forge/` | E3 灌入后的数据清单（真实 ID） |
| `forge-log.json` | `.allforai/demo-forge/` | 灌入日志（操作状态 + BIZ_BUG 记录） |

---

## 铁律

1. **全部走 API，无例外** — 所有数据灌入通过 API 端点，不直写数据库。API 缺失 = `API_MISSING_BLOCKER`，必须先补 API 再灌数据
2. **灌入过程即集成测试** — 每次 API 调用验证认证、权限、校验、业务逻辑、级联、派生字段。灌入失败 = 真实 BIZ_BUG，直接记录到 forge-log 交给修复流程
3. **派生字段由 API 业务逻辑自动计算** — 聚合/计数/余额/索引全部由服务端业务逻辑处理，无需手动修正。派生不一致 = BIZ_BUG
4. **链路顺序灌入，父先于子** — 任何子实体灌入前其父实体必须已存在
5. **失败不静默，链路失败显式标记** — 独立失败记日志继续，父失败则整条链路标记 CHAIN_FAILED
6. **灌入后立即验证可用性** — 用户账号创建后立即用认证 API 验证登录（不留到 demo-verify 才发现密码不对）；数据关联创建后查询确认链路完整（父→子关系可查到）。灌入验证失败 → 修正后重试，不静默跳过
7. **下游消费验证上游完整性** — 灌入完成后必须对照客户端界面清单逐个检查数据覆盖（E5），不能只按 plan 灌完就结束。界面空 = 灌入未完成
8. **灌入失败即 UPSTREAM_DEFECT** — API 返回 4xx/5xx 且非数据问题（如端点不存在、认证配置错误、CORS 拒绝），视为接缝层 bug，返回 UPSTREAM_DEFECT 信号（target: dev-forge.task-execute，severity: blocker）。数据校验失败（如必填字段缺失）视为 demo-design 问题，返回 UPSTREAM_DEFECT（target: demo-forge.design，severity: warning）
