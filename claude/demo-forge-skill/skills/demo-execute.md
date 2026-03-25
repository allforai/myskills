---
name: demo-execute
description: >
  Use when the user asks to "populate demo data", "fill demo environment",
  "demo-execute", "灌入演示数据", "生成演示数据", "demo populate",
  or mentions data population, demo data generation, database seeding.
  Requires demo-plan.json + style-profile.json + upload-mapping.json.
  Requires a running application for data population.
version: "1.0.0"
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
| 应用运行中 | 用户 | API 可访问、数据库可连接 |

四项缺任何一项则终止并提示用户补齐。

---

## 快速开始

```
/demo-forge execute            # 完整流程（E1-E4）
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

### E3: 数据灌入

**灌入顺序由场景链路决定**（不是按实体字母顺序），确保外键依赖正确：

```
1. DB 灌入：配置表、字典表、API_GAP 实体（无业务逻辑的基础数据）
2. API 灌入：用户账号（所有场景链路依赖用户）
3. 混合灌入：按场景优先级（高频 → 中频 → 低频）
   - 每个场景内按链路顺序：父实体 → 子实体 → 关联实体
   - 每个实体按 demo-plan Step 1-C-2 标注的方式选择 API 或 DB
```

**DB 灌入注意事项**：
- 直接写入跳过业务逻辑（触发器、回调），派生字段需 E4 手动补写
- ORM 的 `created_at` / `updated_at` 自动填充不生效，需显式指定
- DB 灌入的记录同样写入 `forge-data.json`，clean 时直接 DELETE

**失败处理策略**：
- **独立实体失败**：写入日志，继续灌入其他实体
- **父实体失败**：跳过该链路下所有子实体（避免外键悬空），整条链路标记为 `CHAIN_FAILED`
- **灌入结束**：汇总失败链路数量和原因，提示用户排查后可重试

**输出**：
- `forge-data.json` — 已创建数据清单（临时 ID 替换为真实服务端 ID）
- `forge-log.json` — 灌入日志（每条记录的操作状态）

---

### E4: 派生数据修正（DB 灌入后）

DB 直写跳过业务逻辑，需手动修正派生字段：

| 修正类型 | 操作 |
|---------|------|
| 聚合字段 | `SELECT SUM(amount) FROM details WHERE parent_id=?` → `UPDATE parent SET total=?` |
| 计数字段 | `SELECT COUNT(*) FROM children WHERE parent_id=?` → `UPDATE parent SET count=?` |
| 余额/库存 | 按全部流水记录正向计算最终值 |
| 搜索索引 | 若存在全文搜索，触发 reindex |

**输出**：更新 `forge-log.json`，追加 E4 修正记录。

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
3. DB 灌入的基础数据（配置表、字典表）
```

**清理方式**：
- 统一走数据库 DELETE（不走 API，速度快且可批量删除）
- 按 `forge-data.json` 中记录的 `id` 和 `table` 逐条或批量 DELETE
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
| 外键断裂 | 检查 forge-data.json，补灌缺失的父记录或修正外键指向 |
| CHAIN_FAILED | 重试该链路的完整灌入 |
| 派生不一致 | 重跑 E4 派生数据修正 |

---

## 输出文件

| 文件 | 路径 | 说明 |
|------|------|------|
| `forge-data-draft.json` | `.allforai/demo-forge/` | E1 生成的完整数据集（临时 ID） |
| `forge-data.json` | `.allforai/demo-forge/` | E3 灌入后的数据清单（真实 ID） |
| `forge-log.json` | `.allforai/demo-forge/` | 灌入日志（操作状态 + E4 修正记录） |

---

## 铁律

1. **优先 API，按需直写数据库** — API 灌入触发完整业务逻辑，DB 直写仅用于 API 不支持的场景
2. **派生字段必须数学计算，不靠 LLM 估算** — SUM/COUNT/余额全部由确定性查询得出
3. **链路顺序灌入，父先于子** — 任何子实体灌入前其父实体必须已存在
4. **失败不静默，链路失败显式标记** — 独立失败记日志继续，父失败则整条链路标记 CHAIN_FAILED
5. **灌入后立即验证可用性** — 用户账号创建后立即用认证 API 验证登录（不留到 demo-verify 才发现密码不对）；数据关联创建后查询确认链路完整（父→子关系可查到）。灌入验证失败 → 修正后重试，不静默跳过
