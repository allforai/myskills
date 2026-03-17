## FieldCheck 总览 — 字段一致性检查

> 检查前后端字段名的全链路一致性，发现幽灵字段、拼写错误、映射断裂等问题。
> 纯静态分析，不需要启动应用。

### 核心概念：4 层字段模型

```
Layer 1: UI 显示层        Layer 2: API 接口层       Layer 3: 实体层          Layer 4: 数据库层
─────────────────        ─────────────────        ─────────────────       ─────────────────
前端组件中绑定的字段       请求/响应的 JSON 字段      后端 Entity/Model        表列名/Schema

Web:    {{ item.userName }}   POST body: { userName }  class User { userName }  column: user_name
Mobile: Text(user.userName)  GET resp: { userName }   @JsonKey userName        user_name VARCHAR
（示例为通用概念，适用于任意前端框架 + 后端框架 + ORM + DB 组合）

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
| **Envelope 双重解包** (Double Unwrap) | DOUBLE_UNWRAP | 🔴 Critical | HTTP client 拦截器/wrapper 已解包 API response envelope，但调用侧仍多访问一层 | 全站数据渲染失败 |
| **DTO 字段名不匹配** (DTO Mismatch) | DTO_MISMATCH | 🔴 Critical | 前端请求/响应类型定义的字段名 ≠ 后端 DTO 序列化字段名 | 400/422 或数据丢失 |
| **Model-Migration 列不同步** (Schema Desync) | SCHEMA_DESYNC | 🔴 Critical | ORM model 有字段但 DB schema/migration 无对应列（反之亦然） | INSERT/UPDATE 500 |
| **Raw SQL 标识符拼写** (SQL Identifier Typo) | SQL_TYPO | 🔴 Critical | 手写 SQL 中的表名/列名与 DB schema 定义不匹配 | 查询/JOIN 失败 |
| **实时通道 URL 不匹配** (Realtime URL Mismatch) | RT_MISMATCH | 🔴 Critical | 前端 WebSocket/SSE/gRPC-stream 连接 URL ≠ 后端注册的路由路径 | 连接 404 |
| **i18n 键缺失** (i18n Missing Key) | I18N_MISSING | 🔴 Critical | 代码引用的 i18n 键在语言文件中不存在 | 页面显示原始键名 |
| **表单缺必填字段** (Form Field Missing) | FORM_FIELD_MISSING | 🔴 Critical | 前端表单未包含后端 DTO required 字段 | 提交必然 400/422 |
| **序列化格式不匹配** (Format Mismatch) | FORMAT_MISMATCH | 🔴 Critical | 前后端对同一字段的序列化格式不同（日期/枚举/数值） | 解析失败 |
| **ORM Preload 缺失** (Preload Missing) | ORM_PRELOAD_MISSING | 🟡 Warning | DTO 引用关联实体字段但查询未 Preload/JOIN | 返回空值 |
| **Null 安全风险** (Null Safety Risk) | NULL_SAFETY_RISK | 🟡 Warning | 前端声明非 nullable 但后端可返回 null | 运行时 TypeError |
| **枚举值不匹配** (Enum Mismatch) | ENUM_MISMATCH | 🔴 Critical | 前端使用的枚举值 ≠ 后端合法枚举值 | 过滤/提交静默失效 |
| **响应结构形状不匹配** (Shape Mismatch) | SHAPE_MISMATCH | 🔴 Critical | List API 返回数组但前端期望分页对象（或反之） | 数据渲染失败 |
| **平台 API 缺守卫** (Platform Guard Missing) | PLATFORM_GUARD_MISSING | 🔴 Critical | 跨平台代码使用平台特定 API 未做平台检查 | 新平台启动即崩溃 |
| **跨客户端 Envelope 不一致** (Envelope Inconsistent) | ENVELOPE_INCONSISTENT | 🔴 Critical | 同项目不同 client 的 response 解包方式不同 | 某端数据访问必崩 |

---

### 接缝检查规则（Seam Checks）

> 以下检查专门针对"两端各自正确但接缝不匹配"的系统性问题。
> 这类问题**单元测试因 mock 边界无法发现，E2E 测试成本高且发现晚**。
> fieldcheck 通过纯静态代码分析秒级检出。

#### 两层规则架构

```
Layer 1: 内置规则（SC-1 ~ SC-14）
  跨项目通用的高频接缝模式，适用于大多数全栈项目。
  由 skill 预定义，每次执行都检查。

Layer 2: 项目派生规则（SC-P-xxx）
  LLM 在 Step 0 分析项目架构后，自动推导该项目特有的接缝风险点。
  每个项目不同，每次执行时动态生成。

  推导流程（在 Step 0 项目画像完成后执行）：
  1. LLM 读取项目的关键架构文件：
     - HTTP client / API 网关 / 代理配置
     - ORM 配置 / 数据库连接 / migration
     - 认证/授权中间件
     - 构建配置 / monorepo 共享包
     - 微服务间通信（gRPC proto / OpenAPI / event schema）

  2. LLM 推导该项目特有的接缝点：
     - "这个项目用了 XXX 模式，这里可能出现 YYY 不一致"
     - 例如：
       · monorepo 共享类型包 → 检查各子项目是否用同一版本
       · gRPC proto 文件 → 检查 proto 与实现是否同步
       · GraphQL schema → 检查 resolver 是否覆盖所有 field
       · 多数据库 → 检查 migration 是否在所有库都执行
       · Feature flag → 检查前后端 flag 名是否一致
       · 环境变量 → 检查 .env.example 与代码引用是否匹配

  3. 每个推导出的规则记录为 SC-P-001, SC-P-002, ...
     格式同内置规则：{ id, name, 原理, 检测逻辑, 产出 }

  4. 产出写入 .allforai/deadhunt/output/field-analysis/project-seam-rules.json
     下次执行时作为 resume 缓存复用（项目架构不变则规则不变）

  5. 报告中单独列出："项目派生规则" 章节
```

> **为什么需要两层**：内置规则覆盖 80% 的通用接缝，但每个项目都有独特的架构决策
> （消息队列、缓存层、CDN 配置、第三方 SDK 集成等）产生独特的接缝点。
> 只靠预设规则会遗漏项目特有的风险；只靠 LLM 推导没有基线保障。两层互补。

> **执行方式分类**：
> - **LLM 驱动**（SC-1, SC-9, SC-12, SC-13, SC-14, 所有 SC-P-xxx）：需要 LLM 读代码理解项目特定的逻辑后推导检测规则
> - **结构化比对**（SC-2~SC-8, SC-10, SC-11）：可通过提取 + 比对字段/标识符集合完成，LLM 辅助匹配

#### SC-1: Response Envelope 解包一致性检测

```
原理：
  多数项目在 HTTP client 层统一解包 API 返回的 envelope。
  解包后，调用侧拿到的已经是 payload。
  但调用侧可能按"未解包结构"访问，导致多余的一层访问 → undefined。

  **每个项目的拦截器写法不同、嵌套层数不同、解包策略不同。
  不能硬编码 grep 模式。必须用 LLM 理解拦截器代码后，针对该项目推导检测规则。**

检测逻辑（LLM 驱动，非 grep 硬编码）：

Step 1: 理解项目的解包逻辑
   - Read HTTP client 配置文件（Phase 0 已识别位置）
   - LLM 分析 response interceptor / middleware / wrapper 的代码逻辑
   - 推导：经过拦截器后，调用侧拿到的 response.data 的实际形状是什么？
   - 记录解包规则，例如：
     "拦截器将 { code, data, meta } 的 data 字段赋给 response.data。
      如果有 meta，则 response.data = { items: data, ...meta }。
      如果无 meta，则 response.data = data 本身。"

Step 2: 扫描所有调用侧
   - 对每个 service/store/page 文件中调用 API client 的代码
   - LLM 读代码，判断调用侧的访问路径是否与 Step 1 推导的实际形状一致
   - 判定标准：
     a. 调用侧访问了拦截器已剥离的层级（如拦截器已剥 .data，调用侧又 .data）→ DOUBLE_UNWRAP
     b. 调用侧按"原始 API 嵌套结构"取子字段（如 .product/.order），但拦截器已将
        该实体提升到顶层 → DOUBLE_UNWRAP
     c. 调用侧直接使用 response.data 且与实际形状一致 → OK

Step 3: 对比后端 API 的实际响应
   - 如果 Step 2 无法确定（前端代码两种写法都有），
     则 Read 对应的后端 handler，确认该 API 实际返回的结构
   - 结合拦截器规则 + 后端实际返回 → 确定调用侧应该怎么写

产出: { file, line, access_pattern, expected_pattern, interceptor_file, diagnosis }

关键：这不是 grep 模式匹配，是 LLM 代码理解。
每个项目只需 Step 1 做一次（理解拦截器），Step 2 批量扫描所有调用侧。
```

#### SC-2: 前端请求/响应类型 ↔ 后端 DTO 逐字段比对

```
原理：
  前端定义了 TypeScript interface / Dart class / Kotlin data class 描述请求/响应结构。
  后端定义了 DTO/VO struct/class 并通过序列化 tag（json/JsonProperty/JsonKey）映射字段。
  两端独立维护，字段名 drift 是高频 bug。

检测逻辑（技术栈无关）：
1. 提取前端类型定义
   - 识别命名模式：*Request, *Response, *Params, *Payload, *DTO
   - 提取字段名列表（规范化为统一 case）

2. 提取后端 DTO 定义
   - 识别命名模式：*Request, *Response, *DTO, *VO
   - 提取序列化字段名（json tag / @JsonProperty / @JsonKey / @SerializedName）
   - 规范化为统一 case

3. 按类型名匹配同语义 DTO 对（如 CreateOrderRequest 前后端各一个）

4. 逐字段比对：
   - 前端有 fieldA 但后端无 → GHOST（前端发了但后端忽略）
   - 后端有 fieldB 但前端无 → GAP（后端返回但前端没取）
   - 名称相近但不同（编辑距离 ≤ 2）→ DTO_MISMATCH

产出: { frontend_type, frontend_file, backend_type, backend_file, mismatched_fields[] }
```

#### SC-3: ORM Model ↔ DB Schema 列同步

```
原理：
  ORM model 定义的字段与 DB schema（migration/DDL）的列必须一一对应。
  新加 model 字段忘了加 migration、或 migration 加了列但 model 没更新 → 运行时 500。

检测逻辑（技术栈无关）：
1. 提取 ORM model 字段
   - 识别 model 文件（按项目约定：model/, entity/, domain/ 目录）
   - 提取字段名 + 列名映射（ORM column tag / 命名策略推断）
   - 排除标记为忽略的字段（gorm:"-" / @Transient / @JsonIgnore 等）

2. 提取 DB schema 列
   - 来源优先级：migration 文件 > schema.sql > ORM auto-migrate 记录
   - 解析 CREATE TABLE / ALTER TABLE ADD COLUMN 语句

3. 对每个 model-table 对，比对列集合：
   - model 有但 schema 无 → SCHEMA_DESYNC（Critical）
   - schema 有但 model 无 → 可能 STALE（Warning）

产出: { model_file, field, expected_column, schema_file, status }
```

#### SC-4: 手写 SQL 标识符验证

```
原理：
  ORM 的 raw SQL / 自定义查询中的表名和列名是硬编码字符串，不受 ORM 约束。
  ORM 可能用复数表名（User → users）但手写 SQL 用单数（user），导致查询失败。

检测逻辑（技术栈无关）：
1. Grep 后端代码中的 raw SQL（常见 pattern：Raw(, Exec(, Query(, queryRow(, @Query 等）
2. 用简单 SQL 解析提取引用的表名（FROM/JOIN/INTO/UPDATE 后的标识符）和列名
3. 与 DB schema 的表名和列名集合比对
4. 不在 schema 中 → SQL_TYPO

产出: { file, line, identifier, type: "table"|"column", closest_match, schema_source }
```

#### SC-5: 实时通道 URL 一致性

```
原理：
  WebSocket / SSE / gRPC-stream 等实时通道的 URL 路径前后端独立定义。
  前端常量文件定义连接地址，后端路由注册监听地址。两者不匹配 → 连接失败。

检测逻辑（技术栈无关）：
1. 提取前端实时通道连接 URL
   - Grep: WebSocket / EventSource / gRPC stream 连接代码
   - 提取 URL 路径部分（去掉 host:port）

2. 提取后端实时通道路由
   - Grep: WebSocket upgrade handler / SSE endpoint / stream endpoint 注册
   - 提取路由路径

3. 比对路径：前端路径 ≠ 后端路由 → RT_MISMATCH

产出: { frontend_file, frontend_url, backend_file, backend_route, channel_type }
```

#### SC-6: i18n 键完整性检查

```
原理：
  前端模板/代码中引用的 i18n 键必须在所有语言文件中存在。
  缺少键 → 页面显示原始键名（如 "status.paid"）而非翻译文本。
  这是 E2E 测试中最高频的 bug 类型（占 21%），但完全可以静态检出。

检测逻辑（技术栈无关）：
1. 提取所有 i18n 键引用
   - 模板：$t('key') / t('key') / {{ $t('key') }} / i18n.t('key') / l10n.key 等
   - 代码：useTranslations / useI18n / AppLocalizations / getString 等

2. 提取所有语言文件定义的键
   - JSON 文件（.json）/ YAML / ARB (.arb) / properties / .ts 导出对象
   - 按项目支持的语言数，确认每种语言都有定义

3. 比对：
   - 代码引用但语言文件无 → I18N_MISSING（Critical）
   - 语言文件有但代码未引用 → I18N_UNUSED（Warning）
   - 某种语言有但其他语言缺 → I18N_INCOMPLETE（Critical）

产出: { file, line, key, missing_in_locales[], type }
```

#### SC-7: 表单字段 ↔ 后端 required 标注比对

```
原理：
  前端表单的输入字段集合必须覆盖后端 DTO 的所有 required 字段。
  表单缺少必填字段 → 提交必然 400/422。
  SC-2 比对字段名是否匹配，SC-7 进一步检查 required 字段是否被遗漏。

检测逻辑（技术栈无关）：
1. 提取后端 DTO 的 required 字段
   - Go: binding:"required" / validate:"required"
   - Java: @NotNull / @NotBlank / @NotEmpty
   - Python: Field(required=True) / 无 Optional 标注
   - Dart: required 关键字

2. 提取前端表单的字段集合
   - 表单组件的 name/v-model/formControlName 属性
   - FormData 构建代码中的键
   - API 调用时构建的 request body 键

3. 比对：
   - 后端 required 但前端表单无对应输入 → FORM_FIELD_MISSING（Critical）

产出: { frontend_form_file, backend_dto_file, missing_fields[], dto_name }
```

#### SC-8: 序列化格式一致性

```
原理：
  前端和后端对同一字段的序列化格式必须一致。
  常见不匹配：日期格式（YYYY-MM-DD vs ISO8601）、数值（string vs number）、
  枚举值（"active" vs 1）、JSON 字符串 vs 对象。

检测逻辑（技术栈无关）：
1. 提取前端序列化/格式化代码
   - 日期：format('YYYY-MM-DD') / toISOString() / value-format 属性
   - 数值：parseInt / Number() / .toString()

2. 提取后端反序列化约束
   - 日期：time.RFC3339 / @DateTimeFormat / @JsonFormat
   - 枚举：binding:"oneof=..." / @Enum

3. 比对格式规范：
   - 前端日期格式 ≠ 后端期望格式 → FORMAT_MISMATCH（Critical）
   - 前端发送 string 但后端期望 number → TYPE_SERIAL_MISMATCH（Critical）

产出: { frontend_file, backend_file, field, frontend_format, backend_format }
```

#### SC-9: ORM 查询完整性（Preload / JOIN 检查）

```
原理：
  API 响应类型包含关联实体的字段（如 product_name, customer_email），
  但 ORM 查询没有 Preload/Include/Join 这些关联 → 返回 null/零值。
  前端收到空数据 → 显示空白列。

检测逻辑（技术栈无关）：
1. 提取 API 响应类型/DTO 中引用了关联实体的字段
   - 判定依据：字段名含其他实体名（如 ProductName, MerchantEmail, UserAvatar）
   - 或 DTO 嵌套了其他 model（如 Product Product, User User）

2. 检查对应的 repository/service 查询代码
   - 是否有 Preload("Product") / Include(x => x.Product) / .select_related()
   - 是否有 JOIN 语句加载关联数据

3. DTO 引用了关联字段但查询无 Preload/JOIN → ORM_PRELOAD_MISSING（Warning）

产出: { dto_file, dto_field, repo_file, query_method, missing_preload }
```

#### SC-10: 前端 Prop/参数 null 安全检查

```
原理：
  前端组件声明 prop 类型为 T[]（非 nullable），但 API 可能返回 null。
  组件内直接调用 .length / .map() → 运行时 TypeError。

检测逻辑（技术栈无关）：
1. 提取前端组件的 prop/参数类型声明
   - 识别数组类型（string[], T[], Array<T>）和对象类型
   - 检查是否标注了 nullable（T[] | null, Optional<T[]>）

2. 检查对应 API 响应字段在后端 model 中的定义
   - 后端字段是指针/nullable（*[]string, NullableField）→ API 可能返回 null

3. 前端声明非 nullable 但后端可返回 null → NULL_SAFETY_RISK（Warning）

产出: { component_file, prop_name, declared_type, backend_field, nullable_in_backend }
```

#### SC-11: 枚举值一致性检查

```
原理：
  前端 UI 中使用的枚举值（dropdown 选项、filter 值、status badge 映射）
  必须与后端定义的枚举值完全匹配。
  常见 drift：前端用 "pending" 但后端定义 "pending_review"，
  或前端用 "approve" 但后端期望 "approve_refund"。
  字段名匹配（SC-2 检查），但值不匹配 → 功能静默失效。

检测逻辑（技术栈无关）：
1. 提取后端枚举定义
   - binding:"oneof=active pending_review draft" / const 块 / enum 类型
   - 提取每个字段的合法值集合

2. 提取前端使用的枚举值
   - Select/Dropdown 的 option value
   - Filter/query 参数的硬编码值
   - Status badge / switch-case 的 case 值
   - API 调用时传入的字符串常量

3. 比对：
   - 前端值不在后端合法集合中 → ENUM_MISMATCH（Critical）
   - 后端有值但前端无对应处理 → ENUM_UNHANDLED（Warning）

产出: { frontend_file, frontend_value, backend_file, backend_enum, valid_values[] }
```

#### SC-12: API 响应结构形状一致性

```
原理：
  同一项目中，list 类 API 的响应结构应该统一。
  混用两种格式（数组 [] vs 分页对象 {items, total}）
  会导致前端类型定义只覆盖一种格式，碰到另一种就崩。

检测逻辑（技术栈无关）：
1. 提取所有 list 类 API 的响应结构
   - 后端：扫描 handler/controller 中 list 方法的返回格式
   - 判定是否返回分页对象（含 items + total/meta）还是裸数组

2. 提取前端对应的类型期望
   - 前端 service/store 中如何访问 list 响应：
     response.data.items（期望分页对象）vs response.data（期望数组）

3. 比对：
   - 后端返回数组但前端期望 .items → SHAPE_MISMATCH（Critical）
   - 后端返回分页对象但前端直接当数组用 → SHAPE_MISMATCH（Critical）
   - 同一项目内不同 list API 格式不统一 → SHAPE_INCONSISTENT（Warning）

产出: { endpoint, backend_shape: "array"|"paginated", frontend_access, file }
```

#### SC-13: 平台特定 API 守卫检查（跨平台项目专用）

```
原理：
  跨平台代码（Flutter/RN/KMP）中使用平台特定 API（dart:io、NativeModules 等）
  在不支持的平台上会崩溃。必须用平台守卫（kIsWeb、Platform.OS）保护。
  这是给已有项目添加新平台时最常见的崩溃原因。

检测逻辑（LLM 驱动，仅跨平台项目触发）：
1. Phase 0 已识别跨平台框架和目标平台
2. 扫描代码中的平台特定 import 和 API 调用：
   - Flutter: import 'dart:io'（Platform.isAndroid/isIOS/...）
   - Flutter: import 'dart:html'（仅 web 可用）
   - RN: import { NativeModules, Platform } from 'react-native'
   - KMP: expect/actual 声明中的平台实现
3. 对每个调用点，LLM 检查是否有前置平台守卫：
   - kIsWeb / !kIsWeb 在 dart:io 调用之前
   - Platform.OS !== 'web' 在 NativeModules 调用之前
4. 无守卫 → PLATFORM_GUARD_MISSING（Critical）
5. 守卫条件不完整（如只判 isAndroid 但没防 web）→ PLATFORM_GUARD_INCOMPLETE（Warning）

产出: { file, line, api_call, missing_guard, target_platforms_affected[] }
```

#### SC-14: 跨客户端 Envelope 处理一致性

```
原理：
  同一项目的多个 API client（如 website 的 axios、admin 的 axios、mobile 的 Dio）
  对 API 响应 envelope 的处理方式可能不同。
  有的有拦截器自动解包，有的没有。
  共享的 service 层代码模式（如 response.data.xxx）在不同 client 下行为不同 → 某端必崩。

检测逻辑（LLM 驱动）：
1. Phase 0 已识别每个子项目的 HTTP client 类型
2. 对每个 client，LLM 分析 envelope 处理方式（复用 SC-1 Step 1）：
   - 记录：client_name, has_unwrap_interceptor, unwrap_result_shape
3. 比对所有 client 的处理方式：
   - 全部一致（都解包或都不解包）→ OK
   - 不一致 → ENVELOPE_INCONSISTENT（Critical）
4. 对不一致的 client，检查其 service/调用层是否适配了差异：
   - 是否做了 `(body['data'] ?? body)` 等兼容处理
   - 无兼容处理 → ENVELOPE_ACCESS_BUG（Critical）

产出: { clients: [{ name, type, has_unwrap }], inconsistent: bool, affected_files[] }
```

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
