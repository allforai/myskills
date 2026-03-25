## 智能匹配算法参考

> 本文档定义了跨层字段名比对时使用的智能匹配算法。
> 核心目标：区分命名风格差异（合法）和真正的不一致（问题）。

---

### 匹配流程总览

```
输入：Layer(n) 字段集 A, Layer(n+1) 字段集 B

          ┌─────────────────────┐
          │  Step 1: 精确匹配    │   "userName" === "userName"
          │  exact string match  │   → 直接配对，从候选池移除
          └──────────┬──────────┘
                     ↓ 未匹配字段
          ┌─────────────────────┐
          │  Step 2: 标准化匹配  │   "userName" ≈ "user_name" ≈ "UserName"
          │  tokenize → lower   │   → 词根序列相同 → 风格等价，配对
          │  → compare roots    │
          └──────────┬──────────┘
                     ↓ 未匹配字段
          ┌─────────────────────┐
          │  Step 3: 近似匹配    │   "userName" ~ "userNmae" (dist=2)
          │  edit distance ≤ T  │   → 报 TYPO 问题
          └──────────┬──────────┘
                     ↓ 未匹配字段
          ┌─────────────────────┐
          │  Step 4: 语义匹配    │   "nickname" ~ "displayName"
          │  same module,       │   → 同模块语义相似，报 SEMANTIC
          │  semantic similarity │   → 标记 needs_confirmation
          └──────────┬──────────┘
                     ↓ 仍未匹配字段
          ┌─────────────────────┐
          │  Step 5: 分类       │   A 有 B 没有 → GHOST
          │  Ghost / Stale / Gap│   B 有 A 没有 → STALE
          │                     │   L3→L2 断裂  → GAP
          └─────────────────────┘

输出：field-mapping.json（含匹配对 + 问题列表）
```

---

### Step 1: 精确匹配

最简单的一步：逐字符比较两层字段名。

```
算法：
  for field_a in layer_n_fields:
    if field_a.name in layer_n1_fields:
      field_b = layer_n1_fields[field_a.name]
      mark_matched(field_a, field_b)
      remove both from candidate pools
```

- 大小写敏感：`userName` !== `UserName`（精确匹配要求完全一致）
- 匹配成功的字段从候选池移除，不再进入后续步骤
- 预期命中率：同层同风格的字段（如后端内部 L3↔L4），精确匹配率通常 > 60%

---

### Step 2: 标准化匹配（命名风格等价）

将字段名分词、统一小写后比较词根序列。这一步的目标是消除合法的命名风格差异。

#### 分词规则

| 输入示例 | 分词结果 | 规则 |
|---------|---------|------|
| `userName` | `[user, name]` | camelCase：在大写字母前切分 |
| `UserName` | `[user, name]` | PascalCase：在大写字母前切分 |
| `user_name` | `[user, name]` | snake_case：按下划线切分 |
| `user-name` | `[user, name]` | kebab-case：按连字符切分 |
| `HTMLParser` | `[html, parser]` | 连续大写字母视为一个词（acronym） |
| `getXMLData` | `[get, xml, data]` | 混合：先处理连续大写，再处理 camel |
| `user_name_v2` | `[user, name, v2]` | 保留版本后缀作为独立 token |
| `__user_name__` | `[user, name]` | 去除前后 underscore padding |
| `_id` | `[id]` | 单个前导下划线 + 词 → 去除下划线 |

#### 分词后标准化

```
1. 分词（按上述规则）
2. 全部转小写
3. 应用缩写等价表展开
4. 比较词根序列是否一致

示例：
  "userName"    → [user, name]     → [user, name]
  "user_name"   → [user, name]     → [user, name]
  "UserName"    → [user, name]     → [user, name]
  结果：三者等价 ✅
```

#### 特殊处理：布尔前缀

布尔字段常加 `is` / `has` / `can` / `should` 前缀，不同层可能有/没有前缀：

```
"isActive"   → 尝试两种匹配：
  1. [is, active]  → 完整匹配
  2. [active]      → 去前缀匹配

"hasChildren" → 尝试两种匹配：
  1. [has, children] → 完整匹配
  2. [children]      → 去前缀匹配

匹配成功条件：任一方式与对端字段词根序列相同
```

#### 特殊处理：ID 后缀

外键字段常加实体前缀或 `_id` / `Id` 后缀：

```
"userId"    → 尝试两种匹配：
  1. [user, id]  → 完整匹配
  2. [id]        → 去前缀匹配（在同 module 下）

"user_id"   → 同上

"id" (在 User 模块中) → 也尝试匹配 "userId"
```

#### 特殊处理：中文标签

中文标签（如 `用户名`）不参与分词匹配，仅用于报告展示。

```
L1 字段可能有 label: "用户名", name: "userName"
匹配时只使用 name 属性
label 只在报告中辅助人工确认
```

#### 常见缩写等价表

以下缩写在匹配时视为等价（双向）：

| 缩写 | 完整形式 | 使用场景 |
|------|---------|---------|
| `desc` | `description` | 描述字段 |
| `addr` | `address` | 地址字段 |
| `tel` | `telephone` | 电话字段 |
| `phone` | `telephone` | 电话字段 |
| `img` | `image` | 图片字段 |
| `qty` | `quantity` | 数量字段 |
| `amt` | `amount` | 金额字段 |
| `pwd` | `password` | 密码字段 |
| `no` | `number` | 编号字段 |
| `num` | `number` | 数字/编号字段 |
| `cat` | `category` | 分类字段 |
| `cate` | `category` | 分类字段 |
| `org` | `organization` | 组织字段 |
| `dept` | `department` | 部门字段 |
| `config` | `configuration` | 配置字段 |
| `conf` | `configuration` | 配置字段 |
| `info` | `information` | 信息字段 |
| `msg` | `message` | 消息字段 |
| `stat` | `statistics` | 统计字段 |
| `stats` | `statistics` | 统计字段 |
| `auth` | `authorization` | 授权字段 |
| `authn` | `authentication` | 认证字段 |
| `params` | `parameters` | 参数字段 |
| `spec` | `specification` | 规格字段 |
| `env` | `environment` | 环境字段 |
| `repo` | `repository` | 仓库字段 |
| `prev` | `previous` | 前一个 |
| `cur` / `curr` | `current` | 当前 |
| `src` | `source` | 来源字段 |
| `dst` / `dest` | `destination` | 目标字段 |
| `ref` | `reference` | 引用字段 |
| `tmp` / `temp` | `temporary` | 临时字段 |
| `btn` | `button` | 按钮字段 |
| `ctx` | `context` | 上下文字段 |
| `seq` | `sequence` | 序列字段 |
| `idx` | `index` | 索引字段 |
| `val` | `value` | 值字段 |
| `len` | `length` | 长度字段 |
| `max` | `maximum` | 最大值 |
| `min` | `minimum` | 最小值 |
| `avg` | `average` | 平均值 |
| `cnt` | `count` | 计数 |

> **扩展方式：** 项目根目录的 `.deadhunt/field-aliases.json` 可追加项目专属缩写映射。

---

### Step 3: 近似匹配（Typo 检测）

对经过 Step 2 标准化后仍未匹配的字段，计算编辑距离（Levenshtein distance），检测拼写错误。

#### 计算方式

```
1. 对 A 中每个未匹配字段的标准化词根序列 tokensA
2. 与 B 中每个未匹配字段的标准化词根序列 tokensB
3. 将词根序列拼接为字符串（用空格连接）
4. 计算 Levenshtein 编辑距离
5. 与阈值比较
```

#### 阈值表

| 标准化后字符串长度 | 最大允许编辑距离 | 说明 | 示例 |
|------------------|----------------|------|------|
| ≤ 3 字符 | 0 | 短字段太模糊，不做 typo 检测 | `id`, `no`, `url` — 不检测 |
| 4 ~ 8 字符 | 1 | 允许 1 个字符的差异 | `name` vs `nme` (dist=1) → TYPO |
| 9 ~ 15 字符 | 2 | 允许 2 个字符的差异 | `description` vs `descrption` (dist=1) → TYPO |
| > 15 字符 | 3 | 长字段允许更多容错 | `organizationName` vs `oragnizationName` (dist=2) → TYPO |

#### 排除规则

以下情况即使编辑距离在阈值内也**不报 TYPO**：

1. **缩写表已覆盖**：如果两个字段的差异来自缩写等价表（`desc` vs `description`），已在 Step 2 处理
2. **ORM 显式映射**：Entity 字段有 `@Column(name="xxx")` 显式指定列名时，列名与字段名的差异是刻意的
3. **JSON tag 显式映射**：Go struct 有 `` `json:"xxx"` `` tag 时同理
4. **前缀/后缀差异**：如 `user` vs `userId`，属于合法的 FK 命名模式，不是 typo
5. **数字后缀差异**：如 `address1` vs `address2`，是不同字段而非拼写错误

#### 输出示例

```json
{
  "type": "TYPO",
  "severity": "critical",
  "module": "user",
  "layer_pair": "L1↔L2",
  "field_a": { "name": "userNmae", "layer": "L1", "file": "src/pages/user/list.tsx:45" },
  "field_b": { "name": "userName", "layer": "L2", "file": "src/api/types/user.ts:12" },
  "edit_distance": 2,
  "suggestion": "L1 的 'userNmae' 疑似拼写错误，应为 'userName'"
}
```

---

### Step 4: 语义匹配

对同一模块中仍未匹配的字段，尝试基于语义相似性建立关联。

#### 匹配条件

必须同时满足：
1. **同模块**：两个字段属于同一业务模块（如都在 user 模块下）
2. **语义相关**：字段名属于以下语义关联模式之一

#### 语义关联模式

| 模式 | 说明 | 示例 |
|------|------|------|
| **同义词** (Synonyms) | 不同词但指代同一数据 | `nickname` / `displayName` / `screenName` |
| **不同角度** (Different Angle) | 同一数据的不同业务视角 | `price` / `unitPrice` / `salePrice` |
| **不同粒度** (Different Scope) | 范围不同但指向同类数据 | `address` / `detailAddress` / `fullAddress` |
| **包含关系** (Containment) | 一个字段名包含另一个 | `name` / `userName` / `realName` |
| **业务等价** (Business Equivalent) | 业务上常互相替代 | `status` / `state` / `isActive` |

#### 常见语义等价组

```
# 用户相关
[nickname, displayName, screenName, showName, alias]
[avatar, photo, profileImage, headImg, portrait]
[mobile, phone, cellphone, tel, phoneNumber]
[email, mail, emailAddress]
[realName, trueName, legalName, fullName]

# 时间相关
[createdAt, createTime, gmtCreate, created, createDate]
[updatedAt, updateTime, gmtModified, modified, modifyDate, lastModified]
[deletedAt, deleteTime, gmtDelete]
[startTime, beginTime, startDate, beginDate]
[endTime, finishTime, endDate, deadline, dueDate]

# 状态相关
[status, state, isActive, enabled, isEnabled]
[deleted, isDeleted, removed, isRemoved]
[visible, isVisible, show, isShow, display]

# 描述相关
[description, desc, remark, note, memo, comment, summary]
[title, name, label, caption, heading, subject]

# 金额相关
[price, amount, fee, cost, charge, rate]
[totalPrice, totalAmount, grandTotal, totalFee]
[discount, discountAmount, couponAmount, reduction]
```

#### 语义匹配输出

所有语义匹配结果均标记 `needs_confirmation: true`，要求人工复核：

```json
{
  "type": "SEMANTIC",
  "severity": "warning",
  "module": "user",
  "layer_pair": "L1↔L2",
  "field_a": { "name": "nickname", "layer": "L1", "file": "src/pages/user/profile.tsx:23" },
  "field_b": { "name": "displayName", "layer": "L2", "file": "src/api/types/user.ts:8" },
  "pattern": "synonym",
  "confidence": "medium",
  "needs_confirmation": true,
  "question": "前端使用 'nickname'，API 返回 'displayName'，这两个字段是否指代同一数据？"
}
```

---

### 匹配结果分类

经过 4 步匹配流程后，每个字段归入以下分类：

| 匹配结果 | 问题类型 | 严重度 | 说明 | 处置 |
|---------|---------|--------|------|------|
| 精确匹配 | — | Pass | 字符串完全一致 | 无需处理 |
| 风格等价 | — | Pass | 词根相同，仅风格不同 | 无需处理 |
| 编辑距离命中 | TYPO | Critical | 疑似拼写错误 | 需修复 |
| 语义相似 | SEMANTIC | Warning | 可能指代同一数据但名字不同 | 需人工确认 |
| L(n) 有，L(n+1) 没有 | GHOST | Critical | 幽灵字段：引用了不存在的数据 | 需修复 |
| L(n+1) 有，L(n) 未使用 | STALE | Warning | 废弃字段：传输了未使用的数据 | 建议清理 |
| L3 有但 L2 未暴露 | GAP | Critical | 映射断裂：Entity 有但 DTO 未包含 | 需修复 |
| L4 有但 L3 未映射 | GAP | Critical | 映射断裂：DB 列无对应 Entity 字段 | 需修复 |

> **优先级排序**：GHOST = TYPO = GAP (Critical) > SEMANTIC = STALE (Warning)。
> Critical 问题通常意味着运行时会出现 `undefined` 或数据丢失。

---

### 跨层比对方向

每对相邻层做双向检查：

| 层级对 | 正向检查（Forward） | 反向检查（Reverse） |
|-------|-------------------|-------------------|
| **L1 ↔ L2** | L1 → L2：前端绑定的字段，API 是否返回？ <br> 未找到 → **GHOST**（页面显示 undefined） | L2 → L1：API 返回的字段，前端是否使用？ <br> 未找到 → **STALE**（冗余传输） |
| **L2 ↔ L3** | L2 → L3：DTO/VO 字段是否在 Entity 中有对应？ <br> 未找到 → **GAP**（DTO 暴露了不存在的数据） | L3 → L2：Entity 字段是否被 DTO 暴露？ <br> 未找到 → 可能是 **合法隐藏**（如 password, salt） |
| **L3 ↔ L4** | L3 → L4：Entity 字段是否有对应 DB 列？ <br> 未找到 → **GAP**（ORM 映射错误） | L4 → L3：DB 列是否被 Entity 映射？ <br> 未找到 → **STALE**（废弃列）或遗漏 |
| **L1 ↔ L4** | 端到端验证：前端显示字段能否最终追溯到 DB 列？ <br> 整条链路断裂 → 综合问题 | DB 列是否最终体现在前端？ <br> 未体现 → 可能是后台字段，合法 |

```
比对顺序（推荐）：

  L3 ↔ L4  →  L2 ↔ L3  →  L1 ↔ L2
  （从底层向上：先确保数据基础正确，再检查接口层，最后检查展示层）

  最后做 L1 ↔ L4 端到端验证（跳过中间层，检查是否有中间层修改了字段名）
```

---

### 常见合法差异（不报为问题）

以下模式是正常的工程实践，匹配算法应识别并**跳过**，不产生告警：

#### 1. 外键命名前缀

```
L4 (DB):     users.id
L3 (Entity): User.id
L2 (API):    order.userId     ← 在 Order 的 DTO 中引用 User 的 id，加了表名前缀
L1 (UI):     order.userId

规则：在关联模块中，id → {entity}Id / {entity}_id 是合法的 FK 命名
```

#### 2. 系统时间字段变体

```
以下变体全部视为等价，不报问题：
  createdAt ↔ created_at ↔ createTime ↔ create_time ↔ gmt_create ↔ created ↔ createDate
  updatedAt ↔ updated_at ↔ updateTime ↔ update_time ↔ gmt_modified ↔ modified ↔ modifyDate
  deletedAt ↔ deleted_at ↔ deleteTime ↔ delete_time ↔ gmt_delete
```

#### 3. DTO 字段少于 Entity（信息隐藏）

```
Entity (L3):
  class User {
    id, userName, email, password, salt, deletedAt, internalNote
  }

DTO (L2):
  class UserVO {
    id, userName, email    ← 故意不暴露 password, salt, deletedAt, internalNote
  }

规则：以下 Entity 字段在 DTO 中不存在时，视为合法信息隐藏，不报 GAP：
  - password, pwd, secret, salt, hash
  - deletedAt, deleted, isDeleted (软删标记)
  - internalNote, adminRemark (内部备注)
  - 任何以 _ 开头的字段 (约定为内部字段)
```

#### 4. L1 字段少于 L2（部分展示）

```
API Response (L2):
  { id, userName, email, phone, avatar, createdAt, updatedAt, role, department, ... }

UI Table (L1):
  只展示 [userName, email, phone, role]   ← 正常，列表页不必显示所有字段

规则：L1 字段数 < L2 字段数是正常的（前端只展示需要的字段）
     只有 L1 有而 L2 没有的才是 GHOST
```

#### 5. 计算字段（前端拼接）

```
API Response (L2):
  { firstName: "John", lastName: "Doe" }

UI Display (L1):
  {{ firstName + ' ' + lastName }}  ← 显示为 "John Doe"
  或
  computed: fullName = firstName + ' ' + lastName

规则：前端存在 fullName 字段但 API 没有时，如果同时存在 firstName + lastName，
     则 fullName 是计算字段，不报 GHOST
```

#### 6. 聚合字段（后端统计）

```
DB (L4):   orders 表没有 orderCount 列
Entity (L3): 没有 orderCount 字段
API (L2):   { orderCount: 5 }    ← 来自 SQL COUNT 聚合
UI (L1):    显示 orderCount

规则：L2 有但 L3/L4 没有的字段，如果字段名含有以下聚合标识，视为合法计算字段：
  - 后缀：Count, Sum, Avg, Max, Min, Total
  - 前缀：total, sum, avg, count
  - 示例：orderCount, totalAmount, avgScore, maxPrice
```

#### 7. 分页/元数据字段

```
API Response (L2):
  { list: [...], total: 100, page: 1, pageSize: 20 }

规则：以下字段是通用分页/元数据字段，不与业务 Entity 做匹配：
  - total, page, pageSize, pageNum, current, size
  - hasMore, hasNext, hasPrev
  - code, message, msg, success, timestamp
```

#### 8. 枚举显示文本

```
API (L2):   { status: 1 }
UI (L1):    { status: 1, statusText: "已发布" }   ← 前端根据枚举值生成

规则：如果字段名 = 另一字段名 + "Text" / "Label" / "Name" / "Desc"，
     且对应基础字段存在，则视为前端枚举映射字段，不报 GHOST
  示例：statusText, typeName, categoryLabel, levelDesc
```

---

### 附录：匹配算法伪代码

```python
def match_fields(layer_a_fields, layer_b_fields, module_name):
    """
    对两层字段做智能匹配，返回匹配对和问题列表。
    """
    results = []
    issues = []
    pool_a = set(layer_a_fields)
    pool_b = set(layer_b_fields)

    # Step 1: 精确匹配
    for fa in list(pool_a):
        for fb in list(pool_b):
            if fa.name == fb.name:
                results.append(Match(fa, fb, type="exact"))
                pool_a.remove(fa)
                pool_b.remove(fb)
                break

    # Step 2: 标准化匹配
    for fa in list(pool_a):
        tokens_a = normalize(fa.name)  # 分词 + 小写 + 缩写展开
        for fb in list(pool_b):
            tokens_b = normalize(fb.name)
            if tokens_a == tokens_b:
                results.append(Match(fa, fb, type="style_equivalent"))
                pool_a.remove(fa)
                pool_b.remove(fb)
                break
            # 尝试布尔前缀/ID 后缀变体
            if match_with_prefix_suffix_variants(tokens_a, tokens_b):
                results.append(Match(fa, fb, type="style_equivalent"))
                pool_a.remove(fa)
                pool_b.remove(fb)
                break

    # Step 3: 近似匹配 (Typo)
    for fa in list(pool_a):
        norm_a = " ".join(normalize(fa.name))
        best_match, best_dist = None, float("inf")
        for fb in list(pool_b):
            norm_b = " ".join(normalize(fb.name))
            dist = levenshtein(norm_a, norm_b)
            if dist < best_dist:
                best_dist = dist
                best_match = fb
        threshold = get_threshold(len(norm_a))
        if best_match and 0 < best_dist <= threshold:
            if not is_excluded_from_typo(fa, best_match):
                issues.append(Issue(fa, best_match, type="TYPO",
                                    severity="critical", distance=best_dist))
                pool_a.remove(fa)
                pool_b.remove(best_match)

    # Step 4: 语义匹配
    for fa in list(pool_a):
        for fb in list(pool_b):
            if is_semantically_similar(fa.name, fb.name, module_name):
                issues.append(Issue(fa, fb, type="SEMANTIC",
                                    severity="warning",
                                    needs_confirmation=True))
                pool_a.remove(fa)
                pool_b.remove(fb)
                break

    # Step 5: 剩余字段分类
    for fa in pool_a:
        if not is_legitimate_absence(fa, "forward"):
            issues.append(Issue(fa, None, type="GHOST", severity="critical"))
    for fb in pool_b:
        if not is_legitimate_absence(fb, "reverse"):
            issues.append(Issue(None, fb, type="STALE", severity="warning"))

    return results, issues
```

---

## 全链路矩阵交叉验证

> 此章节对应 Step 3.5，在逐对匹配（Step 2）和问题检测（Step 3）完成后执行。
> 目的：追踪每个字段在 L1/L2/L3/L4 的存在性，发现逐对匹配的盲区。

### 阶段 1: 全局字段注册表构建

```
输入：
  - field-profile.json (Step 1 产出，各层原始字段)
  - field-mapping.json (Step 2 产出，已匹配的字段对)

算法：

  registry = {}   # key: 标准化字段名, value: { L1: field|null, L2: field|null, L3: field|null, L4: field|null }

  # 1. 先从已匹配的字段对填充（高置信度）
  for module in field_mapping.modules:
    for mapping in module.field_mappings:
      key = mapping.field_key
      registry[module.name + "." + key] = {
        L1: mapping.L1,   # 有值 = 该层存在此字段
        L2: mapping.L2,   # null = 该层不存在
        L3: mapping.L3,
        L4: mapping.L4
      }

  # 2. 再处理未匹配字段（Step 5 的 GHOST/STALE 残留字段）
  for module in field_profile.modules:
    for layer in [L1, L2, L3, L4]:
      for field in module.layers[layer].fields:
        norm_key = normalize(field.name)  # 复用 Step 2 的标准化规则
        full_key = module.name + "." + norm_key
        if full_key not in registry:
          registry[full_key] = { L1: null, L2: null, L3: null, L4: null }
        registry[full_key][layer] = field

输出：每个字段的 4 层存在性向量
```

**跨层字段归一规则：**

未配对字段跨层归一时，复用 Step 2 的标准化匹配规则：
1. 分词（camelCase / snake_case / PascalCase → 词根列表）
2. 全部小写
3. 缩写展开（同 Step 2 的缩写等价表）
4. 比较词根序列是否一致

如果 L4 有 `user_name`，L1 有 `userName`，且 Step 2 没有把它们配在一起（可能因为它们属于不同的逐对匹配通道），矩阵构建时通过标准化规则发现它们是同一个字段，合并到同一行。

### 阶段 2: 模式识别

```
模式定义表（10 种有意义模式 + 1 种兜底）：

PATTERNS = {
  "FULL_CHAIN":   (True,  True,  True,  True),   # ✅ 健康
  "DTO_SKIP":     (True,  False, True,  True),   # 🔴 后端有，API 漏暴露
  "ORM_SKIP":     (True,  True,  False, True),   # 🔴 绕过 Entity
  "TUNNEL":       (True,  False, False, True),   # 🔴 UI 直连 DB
  "UI_MISSING":   (False, True,  True,  True),   # 🟡 后端完整，前端未用
  "DB_ORPHAN":    (False, False, False, True),   # 🟡 死列
  "RAW_SQL":      (False, True,  False, True),   # 🟡 绕过 ORM
  "COMPUTED":     (True,  True,  True,  False),  # ℹ️ 计算字段
  "DTO_ONLY":     (True,  True,  False, False),  # ℹ️ 聚合字段
  "BACKEND_ONLY": (False, False, True,  True),   # ℹ️ 内部字段
}

算法：

for key, entry in registry:
  vector = (entry.L1 != null, entry.L2 != null, entry.L3 != null, entry.L4 != null)
  matched_pattern = PATTERNS.get(vector, "UNCOMMON")
  entry.pattern = matched_pattern
```

**系统字段和合法隐藏字段的处理：**

- 系统字段 (`id`, `createdAt`, `updatedAt`, `deletedAt`, `version`, `tenantId`) → 跳过模式判定，不参与统计
- 合法隐藏字段 (`password`, `salt`, `secret`, `token`, `internalNotes`) → BACKEND_ONLY 不升级
- 聚合字段 (`xxxCount`, `totalXxx`, `fullName`, `xxxRate`) → DTO_ONLY/COMPUTED 是合法的

### 阶段 3: 与 Step 3 结果交叉

```
输入：
  - field-issues.json (Step 3 产出)
  - registry (阶段 2 产出，含 pattern)

交叉规则：

  # 1. 升级
  for issue in field_issues:
    entry = find_in_registry(issue.module, issue.field)
    if entry and entry.pattern in ["DTO_SKIP", "ORM_SKIP", "TUNNEL"]:
      issue.severity = "critical"  # 确认升级
      issue.matrix_pattern = entry.pattern
      issue.layers = entry.vector
      issue.cross_layer_evidence = generate_evidence(entry)
      # 例: "字段在 L1/L3/L4 均存在，仅 L2(DTO) 缺失，高置信度为 DTO 遗漏"

  # 2. 降级
  for issue in field_issues:
    if issue.type == "STALE":
      entry = find_in_registry(issue.module, issue.field)
      if entry and entry.pattern == "BACKEND_ONLY" and is_hidden_field(issue.field):
        issue.severity = "info"
        issue.cross_layer_evidence = "合法的安全隐藏字段（BACKEND_ONLY）"

  # 3. 新增（矩阵发现但 Step 3 未报告的）
  for key, entry in registry:
    if entry.pattern in ["DB_ORPHAN", "TUNNEL", "ORM_SKIP", "RAW_SQL"]:
      if not already_reported(entry):
        new_issue = create_issue(entry)
        field_issues.append(new_issue)
```

**generate_evidence 生成规则：**

| 模式 | evidence 模板 |
|------|-------------|
| DTO_SKIP | "字段在 {存在层} 均存在，仅 L2(DTO) 缺失，高置信度为 DTO 遗漏" |
| ORM_SKIP | "字段在 L1/L2/L4 存在但 L3(Entity) 缺失，可能通过 raw SQL 绕过 ORM" |
| TUNNEL | "字段仅在 L1(UI) 和 L4(DB) 存在，跳过 API 和 Entity 层，架构异常" |
| UI_MISSING | "字段在 L2/L3/L4 完整链路存在，但 L1(UI) 未展示" |
| DB_ORPHAN | "字段仅在 L4(DB) 存在，所有上层均未引用，可能是废弃列" |
| RAW_SQL | "字段在 L2(API) 和 L4(DB) 存在但 L3(Entity) 缺失，可能通过 raw SQL 直取" |

---

## Flutter 特有问题类型

> 当项目包含 Flutter 客户端和 Web/H5 客户端共享同一后端 API 时，增加以下跨平台问题检测。

### 新增问题类型

| 问题类型 | 严重度 | 场景 | 检测方式 |
|---------|--------|------|---------|
| **PLATFORM_GAP** | 🔴 Critical | Web 端有字段但 Flutter 端模型缺少（同一 API） | 对比同一 API 端点在 Web TS 类型和 Dart 模型中的字段 |
| **SERIALIZE_MISMATCH** | 🔴 Critical | Dart `@JsonKey(name:)` 映射与后端实际字段名不一致 | 对比 Dart `@JsonKey` 值与 L2 后端 DTO 字段名 |
| **NULL_SAFETY** | 🟡 Warning | 后端返回 nullable 但 Dart 模型声明为 non-null | 对比后端 DTO 的 nullable 标记与 Dart 类型的 `?` 后缀 |

### PLATFORM_GAP 检测逻辑

```
输入：同一 API 端点（如 GET /api/orders）
  - Web 端模型字段（TypeScript interface/type）
  - Flutter 端模型字段（Dart class）

算法：
  1. 对同一 API 端点，提取 Web 端和 Flutter 端的模型字段
  2. 对 Web 端有但 Flutter 端没有的字段：
     a. 检查是否为平台差异白名单字段 → 跳过
     b. 否则报 PLATFORM_GAP
  3. 对 Flutter 端有但 Web 端没有的字段：
     a. 检查是否为平台特有字段（如 deviceToken, pushEnabled）→ 跳过
     b. 否则也报 PLATFORM_GAP（可能 Web 端遗漏）

平台差异白名单：
  - Flutter 特有: deviceToken, pushToken, biometricEnabled, offlineData, localCachePath
  - Web 特有: csrfToken, sessionId, cookieConsent
```

### SERIALIZE_MISMATCH 检测逻辑

```
输入：
  - Dart 模型的 @JsonKey(name: 'xxx') 映射
  - 后端 DTO 的实际字段名

算法：
  1. 提取 Dart 模型中所有 @JsonKey 映射
  2. 对每个映射，检查 @JsonKey 的 name 值是否在后端 L2 字段中存在
  3. 不存在 → SERIALIZE_MISMATCH（Dart 模型会解析失败）
  4. 存在但拼写有误 → 同时报 SERIALIZE_MISMATCH + TYPO
```

### NULL_SAFETY 检测逻辑

```
输入：
  - Dart 模型字段的 nullable 标记（String? 或 required String）
  - 后端 DTO 字段的 nullable/required 标记

算法：
  1. 后端标记为 nullable + Dart 声明为 non-null（无 ? 后缀）→ 报 NULL_SAFETY
     "后端 API 可能返回 null，但 Dart 模型未处理 null，运行时可能抛 TypeError"
  2. 后端标记为 required + Dart 声明为 nullable → 不报（安全方向的宽松处理）
```

### Flutter 问题输出示例

```json
{
  "type": "PLATFORM_GAP",
  "severity": "critical",
  "module": "order",
  "api_endpoint": "GET /api/orders",
  "field": "cancelReason",
  "web_model": { "file": "src/api/types/order.ts:15", "name": "cancelReason", "type": "string" },
  "dart_model": null,
  "suggestion": "Flutter 端 Order 模型缺少 cancelReason 字段，该字段在 Web 端已使用"
}
```

```json
{
  "type": "SERIALIZE_MISMATCH",
  "severity": "critical",
  "module": "user",
  "field": "userName",
  "dart_json_key": "user_name",
  "backend_field": "username",
  "file": "lib/models/user.dart:12",
  "suggestion": "@JsonKey(name: 'user_name') 与后端实际字段名 'username' 不一致，API 数据无法正确解析"
}
```
