# Phase 4: 综合评分与报告生成

> code-tuner 最终阶段：汇总 Phase 1-3 的所有发现，计算五维评分，生成结构化报告和重构任务清单。

---

## 五维评分体系

采用扣分制（deduction-based scoring），每个维度以 100 分为基准，根据发现的问题逐项扣分，最低为 0 分。五个维度按权重加权汇总为总分。

---

### 架构合规度（25%）

衡量项目是否遵循分层架构规范，包括层间依赖方向、职责分配、禁止的跨层调用等。

**评分公式：**

```
arch_score = max(0, 100 - (critical_count * 15) - (warning_count * 5) - (info_count * 1))
```

**扣分规则：**

| 违规级别 | 每次扣分 | 典型示例 |
|---------|---------|---------|
| Critical | -15 | Controller 直接调用 DAO；Entity 出现在 Controller 参数中 |
| Warning | -5 | Service 调用另一个 Service 的 DAO；工具类放在错误的 module 中 |
| Info | -1 | 建议但非强制的命名规范偏差；可选的注解缺失 |

**计算示例：**

假设检测到 2 个 Critical violation、3 个 Warning violation、5 个 Info violation：

```
arch_score = max(0, 100 - (2 * 15) - (3 * 5) - (5 * 1))
           = max(0, 100 - 30 - 15 - 5)
           = 50
```

---

### 代码重复率（25%）

衡量项目中代码重复和冗余的严重程度，涵盖代码片段重复、passthrough method、DTO 字段重叠。

**评分公式：**

```
dup_score = max(0, 100
  - (high_sim_pairs * 8)       // similarity > 90%
  - (mid_sim_pairs * 4)        // similarity 70%-90%
  - (passthrough_count * 3)    // passthrough service methods
  - (dto_overlap_pairs * 3))   // DTO overlap > 70%
```

**扣分规则：**

| 重复类型 | 每次扣分 | 判定条件 |
|---------|---------|---------|
| 高相似度代码对 | -8 | 两个代码片段 similarity > 90% |
| 中相似度代码对 | -4 | 两个代码片段 similarity 70%-90% |
| Passthrough service method | -3 | Service 方法仅透传调用 DAO，无业务逻辑 |
| DTO 字段重叠对 | -3 | 两个 DTO 类字段重叠率 > 70% |

**计算示例：**

假设检测到 3 对高相似度代码、2 对中相似度代码、4 个 passthrough method、2 对 DTO 重叠：

```
dup_score = max(0, 100 - (3 * 8) - (2 * 4) - (4 * 3) - (2 * 3))
          = max(0, 100 - 24 - 8 - 12 - 6)
          = 50
```

---

### 抽象合理度（20%）

衡量抽象层次是否恰当——既不缺失必要的抽象，也不存在过度抽象。

**评分公式：**

```
abs_score = max(0, 100
  - (missing_vertical * 10)     // 缺失纵向抽象
  - (missing_horizontal * 6)    // 缺失横向抽象
  - (api_consolidation * 4)     // API 可合并
  - (over_abstraction * 5))     // 过度抽象
```

**扣分规则：**

| 问题类型 | 每次扣分 | 判定条件 |
|---------|---------|---------|
| 缺失纵向抽象 | -10 | 3 个及以上相似类可抽取公共基类/接口 |
| 缺失横向抽象 | -6 | 同一代码片段在 3 个及以上位置重复出现 |
| API 合并机会 | -4 | 多个相似 API endpoint 可合并为参数化接口 |
| 过度抽象 | -5 each | 不必要的 interface、util class、中间层 |

**计算示例：**

假设检测到 1 个缺失纵向抽象、2 个缺失横向抽象、1 个 API 合并机会、1 个过度抽象：

```
abs_score = max(0, 100 - (1 * 10) - (2 * 6) - (1 * 4) - (1 * 5))
          = max(0, 100 - 10 - 12 - 4 - 5)
          = 69
```

---

### 验证规范度（15%）

衡量数据验证是否在正确的层执行、是否存在重复验证、错误响应是否一致。

**评分公式：**

```
val_score = max(0, 100
  - (wrong_layer * 8)            // 验证在错误层
  - (dup_validation * 5)         // 重复验证逻辑
  - (strict_in_loose_out * 10)   // strict-in-loose-out 反模式
  - (inconsistent_error * 8))    // 错误响应不一致
```

**扣分规则：**

| 问题类型 | 每次扣分 | 判定条件 |
|---------|---------|---------|
| 验证在错误层 | -8 each | 格式校验在 Service 层；业务校验在 Controller 层 |
| 重复验证逻辑 | -5 each | 同一验证逻辑在多处重复实现 |
| Strict-in-loose-out 反模式 | -10 each | 入参严格但出参宽松，或反之 |
| 错误响应不一致 | -8 | 同类验证失败返回不同格式的错误信息 |

**计算示例：**

假设检测到 2 个验证在错误层、1 个重复验证、0 个 strict-in-loose-out、1 个错误响应不一致：

```
val_score = max(0, 100 - (2 * 8) - (1 * 5) - (0 * 10) - (1 * 8))
          = max(0, 100 - 16 - 5 - 0 - 8)
          = 71
```

---

### 数据模型规范度（15%）

衡量 Entity、DTO、VO 等数据模型的设计规范程度。

**评分公式：**

```
model_score = max(0, 100
  - (missing_base_fields * 10)   // 公共字段未抽取（仅扣一次）
  - (dto_vo_overlap * 5)         // DTO/VO 字段重叠
  - (entity_exposed * 5)         // Entity 暴露在 Entry 层
  - (missing_relation * 3))      // 缺失关联关系
```

**扣分规则：**

| 问题类型 | 每次扣分 | 判定条件 |
|---------|---------|---------|
| 公共字段未抽取到基类 | -10（仅一次） | `createTime`、`updateTime` 等公共字段未提取到 `BaseEntity` |
| DTO/VO 字段重叠 | -5 per pair | 两个 DTO 或 VO 类字段重叠率 > 70% |
| Entity 暴露在 Entry 层 | -5 each | Controller 方法直接接收或返回 Entity |
| 缺失关联关系 | -3 each | 外键字段存在但未建立 JPA/MyBatis 关联映射 |

**注意：** `missing_base_fields` 是布尔性质的扣分——不论有多少个 Entity 缺失公共字段，只扣一次 10 分。

**计算示例：**

假设公共字段未抽取（扣 1 次）、2 对 DTO/VO 重叠、1 个 Entity 暴露、2 个缺失关联：

```
model_score = max(0, 100 - (1 * 10) - (2 * 5) - (1 * 5) - (2 * 3))
            = max(0, 100 - 10 - 10 - 5 - 6)
            = 69
```

---

### 总分计算

将五个维度按权重加权求和：

```
total = arch_score  * 0.25
      + dup_score   * 0.25
      + abs_score   * 0.20
      + val_score   * 0.15
      + model_score * 0.15
```

以上述示例数据计算：

```
total = 50 * 0.25 + 50 * 0.25 + 69 * 0.20 + 71 * 0.15 + 69 * 0.15
      = 12.5 + 12.5 + 13.8 + 10.65 + 10.35
      = 59.8
```

该项目评分为 59.8，等级为 D。

---

## 分数解读

| 分数范围 | 等级 | 含义 |
|---------|------|------|
| 90-100 | A 优秀 | 架构清晰，极少重复，抽象合理 |
| 75-89 | B 良好 | 少量问题，值得优化但不紧急 |
| 60-74 | C 需要关注 | 明显的结构问题，应尽快优化 |
| 40-59 | D 较差 | 大量重复和违规，需要系统性重构 |
| 0-39 | F 严重 | 架构混乱，建议重新规划 |

对于等级的使用建议：

- **A / B 等级**：维持现状，在日常开发中保持规范即可。运行 `code-tuner` 做定期检查。
- **C 等级**：安排专项优化迭代，按 `tuner-tasks.json` 中的任务清单逐步修复。
- **D / F 等级**：停止新功能开发，优先解决结构性问题。建议按 `pre-launch` 模式排序任务，从影响最大的问题开始。

---

## 报告模板 (tuner-report.md)

生成的 `tuner-report.md` 包含以下完整章节：

### 第一节：摘要

展示总分、各维度分数、项目基本信息。

```markdown
# Code Tuner 分析报告

**生成时间：** 2026-02-17 10:30:00
**项目路径：** /path/to/project
**分析模式：** pre-launch

## 摘要

| 指标 | 分数 | 等级 |
|------|------|------|
| **总分** | **59.8** | **D 较差** |
| 架构合规度 | 50 / 100 | |
| 代码重复率 | 50 / 100 | |
| 抽象合理度 | 69 / 100 | |
| 验证规范度 | 71 / 100 | |
| 数据模型规范度 | 69 / 100 | |

**项目概况：**
- 扫描文件数：87
- 扫描代码行数：12,450
- 发现问题总数：23（Critical: 2, Warning: 8, Info: 13）
- 预估可消除重复代码行：320 行
```

### 第二节：问题列表

按严重程度排序（Critical → Warning → Info），每条问题包含完整上下文。

```markdown
## 问题列表

### Critical

#### [T-01] Controller 直接调用 DAO
- **文件：** `src/main/java/com/example/controller/OrderController.java:34`
- **描述：** `OrderController` 直接注入并调用 `OrderMapper`，跳过 Service 层
- **修复建议：**
  - **pre-launch：** 将 DAO 调用移至 `OrderService`，Controller 改为调用 Service 方法
  - **maintenance：** 新建 `OrderService.findById()` 方法封装此调用，Controller 切换到新方法

#### [G-03] 跨模块 Service 直接调用
- **文件：** `src/main/java/com/example/order/service/OrderService.java:78`
- **描述：** `OrderService` 直接调用 `UserMapper`，跨越模块边界直接访问 DAO
- **修复建议：**
  - **pre-launch：** 通过 `UserService` 暴露查询接口，`OrderService` 改为调用 `UserService`
  - **maintenance：** 同 pre-launch，但添加 Facade 层做防腐

### Warning

#### [DUP-001] 高相似度代码片段
- **文件：** `src/.../UserService.java:23-45` ↔ `src/.../OrderService.java:67-89`
- **描述：** 两段分页查询逻辑相似度 93%，仅查询对象不同
- **修复建议：**
  - **pre-launch：** 抽取通用分页查询方法到 `BaseService`
  - **maintenance：** 新建 `PageQueryHelper` 工具类，逐步替换

### Info
...
```

### 第三节：重复热力图

以 Module x Module 矩阵展示模块间的重复代码对数量。

```markdown
## 重复热力图

模块间重复代码对数量：

```
            | user | order | product | payment |
  user      |  -   |   3   |    1    |    0    |
  order     |  3   |   -   |    2    |    1    |
  product   |  1   |   2   |   -     |    0    |
  payment   |  0   |   1   |    0    |    -    |
```

**热点分析：**
- `user` ↔ `order` 模块间重复最多（3 对），建议优先处理
- `order` ↔ `product` 存在 2 对重复，多为分页和查询逻辑
```

### 第四节：各 Phase 详细发现

按分析阶段组织，展示每个 Phase 的完整发现。

```markdown
## 各 Phase 详细发现

### Phase 1: 架构合规检查

扫描规则 16 条，触发 8 条：
- T-01 (Critical): 1 处 — OrderController 直接调用 DAO
- G-03 (Warning): 2 处 — 跨模块 Service 调用
- ...

### Phase 2: 重复与冗余检测

代码片段重复：5 对（高相似 3 对，中相似 2 对）
Passthrough method：4 个
DTO 重叠：2 对
预估可消除行数：320 行

详细列表：
1. `UserService.java:23-45` ↔ `OrderService.java:67-89` — similarity 93%
2. ...

### Phase 3: 抽象与验证分析

缺失抽象：
- 纵向：`UserService`, `OrderService`, `ProductService` 可抽取 `BaseCrudService`
- 横向：分页查询片段在 4 处重复

验证问题：
- `OrderService.java:45` 手机号格式校验应在 Controller 层
- ...
```

### 第五节：趋势对比

如果 `.allforai/code-tuner/` 目录下存在上次报告，展示变化趋势。

```markdown
## 趋势对比

**对比基准：** 2026-02-10 报告

| 指标 | 上次 | 本次 | 变化 |
|------|------|------|------|
| 总分 | 52.3 | 59.8 | +7.5 ↑ |
| 架构合规度 | 40 | 50 | +10 ↑ |
| 代码重复率 | 45 | 50 | +5 ↑ |
| 抽象合理度 | 65 | 69 | +4 ↑ |
| 验证规范度 | 68 | 71 | +3 ↑ |
| 数据模型规范度 | 65 | 69 | +4 ↑ |

**新增问题（2）：**
- [DUP-005] `PaymentService.java:30-52` ↔ `RefundService.java:10-32`
- [T-08] `ReportController` 直接访问 `OrderMapper`

**已修复问题（5）：**
- ~~[T-02] UserController 包含业务逻辑~~ — 已移至 UserService
- ~~[DUP-002] 用户查询逻辑重复~~ — 已抽取到 BaseService
- ...
```

若无上次报告，显示 `> 首次分析，无历史对比数据。` 并跳过此节。

---

## 重构任务清单 (tuner-tasks.json)

生成结构化 JSON 任务清单，供下游工具或开发者直接消费。

### 完整 Schema

```json
{
  "generated_at": "2026-02-17T10:30:00Z",
  "lifecycle": "pre-launch|maintenance",
  "total_score": 67.75,
  "dimension_scores": {
    "architecture": 50,
    "duplication": 50,
    "abstraction": 69,
    "validation": 71,
    "data_model": 69
  },
  "tasks": [
    {
      "id": "TASK-001",
      "phase": "phase1",
      "rule": "T-03",
      "severity": "warning",
      "title": "手机号格式校验应从 OrderService 移到 OrderController",
      "description": "OrderService.java:45 包含手机号正则校验，这是格式验证，应在入口层完成",
      "files": [
        "src/main/java/com/example/order/service/OrderService.java:45",
        "src/main/java/com/example/order/controller/OrderController.java"
      ],
      "effort": "low",
      "estimated_lines_reduced": 5,
      "suggestion": {
        "pre-launch": "直接将校验逻辑移到 OrderController，在 Service 中删除",
        "maintenance": "在 OrderController 中添加校验，Service 中的暂时保留，标记 @Deprecated"
      }
    },
    {
      "id": "TASK-002",
      "phase": "phase2",
      "rule": "DUP-001",
      "severity": "warning",
      "title": "UserService 和 OrderService 分页查询逻辑重复",
      "description": "两处分页查询逻辑相似度 93%，仅查询实体不同，可抽取泛型基类",
      "files": [
        "src/main/java/com/example/user/service/UserService.java:23-45",
        "src/main/java/com/example/order/service/OrderService.java:67-89"
      ],
      "effort": "medium",
      "estimated_lines_reduced": 40,
      "suggestion": {
        "pre-launch": "创建 BaseCrudService<T> 泛型基类，将分页逻辑下沉到基类",
        "maintenance": "新建 PageQueryHelper 工具类封装分页逻辑，逐步替换各 Service 中的实现"
      }
    }
  ]
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 任务唯一标识，格式 `TASK-NNN`，按排序后的顺序编号 |
| `phase` | string | 来源阶段：`phase1`、`phase2`、`phase3` |
| `rule` | string | 触发的规则 ID，如 `T-01`、`G-03`、`DUP-001`、`ABS-V01` |
| `severity` | string | `critical` / `warning` / `info` |
| `title` | string | 一句话描述任务内容，使用中文 |
| `description` | string | 详细说明问题位置和原因 |
| `files` | string[] | 涉及的文件路径，含行号 |
| `effort` | string | 预估工作量：`low`（< 30 min）、`medium`（30 min - 2 h）、`high`（> 2 h） |
| `estimated_lines_reduced` | number | 预估可消除的重复/冗余代码行数 |
| `suggestion` | object | 按 lifecycle 分别给出修复建议 |

---

## 任务排序逻辑

根据 `lifecycle` 参数采用不同的排序策略。

### Pre-launch 模式：按质量影响降序

上线前追求最大质量改善，优先修复对代码质量影响最大的问题。

排序优先级（从高到低）：

1. **Critical architecture violations**（结构性问题）
   - 层间违规调用、禁止的依赖方向等
   - 不修复会导致后续开发持续产生问题
2. **High duplication**（高重复度问题）
   - similarity > 90% 的代码对
   - 消除后可大量减少代码行数
3. **Missing abstractions**（缺失抽象）
   - 纵向/横向抽象缺失
   - 修复后可系统性消除重复模式
4. **Validation issues**（验证问题）
   - 验证层错位、重复验证
5. **Data model issues**（数据模型问题）
   - DTO/VO 重叠、Entity 暴露等

### Maintenance 模式：按变更风险升序

维护期追求最小变更风险，优先做低风险的改善。

排序优先级（从低风险到高风险）：

1. **Low-risk utility extraction**（低风险工具抽取）
   - 新建文件，不修改已有代码
   - 例如：创建 `PageQueryHelper` 工具类
2. **Validation placement fix**（验证位置修正）
   - 在文件间移动代码，影响范围可控
   - 例如：将格式校验从 Service 移到 Controller
3. **DTO consolidation**（DTO 合并）
   - 合并高重叠的 DTO/VO 类
   - 需要修改引用方，但类型安全保障了正确性
4. **Service passthrough removal**（Passthrough 方法消除）
   - 删除透传方法，调用方需要调整
   - 中等风险，需要确认所有调用链路
5. **Architecture restructuring**（架构重组）
   - 跨模块调用修正、层级调整
   - 最高风险，涉及多文件多模块改动，排在最后

### 同一优先级内的子排序

在同一优先级内，按以下规则子排序：

- `estimated_lines_reduced` 降序（优先处理收益大的）
- `effort` 升序（同等收益下优先处理工作量小的）
- `files` 数组长度升序（涉及文件少的优先）

---

## 报告输出规范

### 文件输出

1. 将 `tuner-report.md` 保存到 `.allforai/code-tuner/tuner-report.md`
2. 将 `tuner-tasks.json` 保存到 `.allforai/code-tuner/tuner-tasks.json`
3. 如果 `.allforai/code-tuner/` 目录不存在，自动创建
4. 如果已存在上次报告，将旧报告重命名为 `tuner-report-{timestamp}.md` 作为历史归档

### 会话内摘要展示

保存文件后，在会话中直接展示摘要信息。禁止仅输出"报告已保存"而不展示内容。

摘要必须包含以下内容：

1. **总分和等级**：明确显示数字和等级
2. **各维度分数**：列出五个维度的具体分数
3. **关键问题摘要**：至少列出所有 Critical 问题和前 3 个 Warning 问题，包含具体文件路径
4. **重构建议**：根据当前 lifecycle 模式给出排在前三的任务
5. **文件位置**：告知报告和任务清单的保存路径

示例会话输出格式：

```
## Code Tuner 分析完成

**总分：59.8 / 100（D 较差）**

| 维度 | 分数 |
|------|------|
| 架构合规度 | 50 |
| 代码重复率 | 50 |
| 抽象合理度 | 69 |
| 验证规范度 | 71 |
| 数据模型规范度 | 69 |

### 关键问题

- **[Critical] T-01** `OrderController.java:34` — Controller 直接调用 DAO
- **[Critical] G-03** `OrderService.java:78` — 跨模块直接访问 DAO
- **[Warning] DUP-001** `UserService.java:23` ↔ `OrderService.java:67` — 分页逻辑重复（93%）
- **[Warning] T-03** `OrderService.java:45` — 格式校验在 Service 层
- **[Warning] DUP-003** `UserDTO.java` ↔ `UserVO.java` — 字段重叠 85%

### 优先处理任务（pre-launch 模式）

1. TASK-001: 修复 OrderController 直接调用 DAO（effort: medium）
2. TASK-002: 抽取 UserService/OrderService 公共分页逻辑（effort: medium）
3. TASK-003: 将手机号校验从 OrderService 移到 Controller（effort: low）

详细报告：`.allforai/code-tuner/tuner-report.md`
任务清单：`.allforai/code-tuner/tuner-tasks.json`
```

### 趋势对比展示

若 `.allforai/code-tuner/` 中存在上次的 `tuner-report.md`，在保存新报告前先解析旧报告的分数和问题列表，进行对比。

对比逻辑：

1. 提取旧报告中的总分和各维度分数
2. 按 Rule ID + 文件路径匹配问题，找出新增和已修复的问题
3. 在新报告的"趋势对比"章节和会话摘要中都展示变化

若不存在旧报告，在报告中注明"首次分析"并跳过趋势对比章节。
