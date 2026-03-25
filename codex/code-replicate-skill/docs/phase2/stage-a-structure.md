# Phase 2 Stage A — 结构发现

> 项目长什么样？模块边界在哪？核心价值是什么？

---

## 2.1 discovery-profile.json — 模块结构

LLM 读取项目根目录信息（文件列表、清单文件、前 2 层目录树），生成项目专属发现规则。

**产出字段**（全部可选，缺失保持内置默认）：
- `module_paths` — 最高优先级：LLM 直接列出所有模块路径 + 是否 atomic
- `module_boundaries` — 项目清单文件（.csproj, package.json 等），含此文件的目录不可拆分
- `source_roots` / `skip_dirs` / `code_extensions` — fallback 用
- `mega_threshold` — 文件数拆分阈值（默认 50）

LLM **必须**基于对项目结构的理解生成，不可套用模板。

> Schema 详见 ./docs/schema-reference.md#discovery-profile

## 2.2 cr_discover.py — 文件扫描

运行 `cr_discover.py --profile discovery-profile.json` → source-summary.json 骨架。
- 优先使用 profile 中的 `module_paths`
- 无 profile 时 fallback 到内置启发式
- 输出 modules 列表（path, key_files, file_count）

## 2.3 source-summary.json — 模块摘要（初步）

LLM 逐模块读 key_files → 输出初步摘要：
- responsibility 单句描述
- exposed_interfaces 列表
- 核心 entities

**非代码配置文件也可能含业务逻辑**（nginx.conf, routes.yaml, OpenAPI spec 等）。引用根目录文件时使用 `"module": null`。

> 分析原则详见 ./docs/analysis-principles.md

**文件卡片生成**：读完每个 key_file 后，LLM 立即输出该文件的结构化卡片（JSON），包含 path、module、kind、symbols、dependencies、business_summary。卡片在读文件时注意力最集中的时刻生成，确保信息完整。

**symbols 过滤**：只记录有业务意义的公开接口。跳过纯模板方法（getter/setter/toString/hashCode/equals/构造函数的无参重载等）— 这些不含业务逻辑，记录它们只会膨胀卡片、稀释有价值的信息。

卡片生成后立即执行 **Quiz 验证**（自答 3 题）：
1. 这个文件的入口函数/导出接口是什么？
2. 它依赖哪些外部服务/模块？
3. 它处理的核心业务场景是什么？

Quiz 答案包含**卡片中没有的信息**（Quiz 提到了卡片遗漏的函数/依赖/场景）→ 重读文件 → 重新生成卡片。最多重试 2 次，仍不一致则标记 `"confidence": "low"` 继续。注意：Quiz 答案是卡片的子集（Quiz 只列了 5 个方法，卡片有 30 个）是正常的 — 不触发重读。只有 Quiz 发现卡片**遗漏**才算不一致。

**Quiz 示例**：
```
文件: order_service.go
卡片: symbols=[CreateOrder, GetOrder], dependencies=[user_service, order_repo]
Quiz: Q1=CreateOrder, CancelOrder, GetOrder  ← CancelOrder 不在卡片中！
      Q2=user_service, order_repo, payment_api ← payment_api 不在卡片中！
→ 不一致 → 重读 → 重新生成
```

模块摘要（responsibility、exposed_interfaces 等）在该模块所有文件卡片生成完毕后再总结，确保摘要与卡片一致。

source-summary.abstractions 中的文件，其卡片须标记 `is_abstraction: true` 和 `abstraction_consumers`（iron law 12）。

> 卡片 Schema 详见 ./docs/schema-reference.md#file-catalog

## 2.3.5 文件覆盖扫描 — 防偷懒

> **LLM 最大的风险不是"不知道该查什么"，而是"没认真读文件就按文件名猜测跳过"。**
> 不靠硬编码"必须查 X 功能"来覆盖（项目千变万化），靠确保 LLM 不跳过文件（对所有项目适用）。

**Step 1: 覆盖率统计**

LLM 对每个模块记录：
```json
{
  "file_count": 22,
  "files_read": ["encrypt.dart", "http_tunnel.dart", "api_executor.dart", "auto_conn.dart"],
  "files_read_count": 4,
  "files_skipped": ["secure_file.dart", "media_cache.dart", ...],
  "coverage": "18%"
}
```

**Step 2: 头部扫描**

对 `files_skipped` 中的文件进行**采样阅读** — 不读全文，读几个关键位置快速判断文件价值：
- **前面**：跳过 import → 读到第一个 class/function 定义（知道"是什么"）
- **中间**：跳到文件中部 → 扫几个方法签名（知道"能做什么"）

LLM 自行决定采样位置和数量。目标是用最少的阅读量判断"这个文件值不值得完整读取"。

**大模块（>100 文件）的扫描优化**：不逐个全扫（token 成本太高），按优先级分层：
- **第一层**（必扫）：被已读文件 import/require 的文件 — 被引用 = 一定有用
- **第二层**（必扫）：文件行数 >100 行的大文件 — 大文件 = 可能有独立功能
- **第三层**（按需）：其余小文件 — 如果前两层扫完 coverage 仍 < 50% 才继续

20 行足以判断：
- 看到 class 定义 + 加密相关字段 → 不是工具类，是核心协议
- 看到 Server.bind / Isolate.spawn → 不是简单缓存，是独立服务
- 看到 mixin + insertXxx / updateXxx → 不是数据类，是持久化层

**Step 3: 发现重要文件 → 补读**

头部扫描发现重要组件 → 加入 key_files → 完整读取 → 更新模块摘要。

补读的文件也按 2.3 相同流程生成卡片 + Quiz 验证。

**Step 4: 写入覆盖率**

最终 source-summary 中每个模块带 `coverage` 字段。Phase 2.14 用户确认时展示覆盖率 — 用户看到"网络模块覆盖率 18%"就会要求补读。

**底线**：coverage < 50% 的模块必须补读到 ≥ 50%。不允许"22 个文件只读了 4 个就声称理解了这个模块"。

## 2.3.7 知识库构建

Step 2.3 和 2.3.5 生成的所有文件卡片，在此步骤汇总为结构化知识库：

**a. 组装 file-catalog.json**
- 收集所有文件卡片 → 写入 `.allforai/code-replicate/file-catalog.json`
- 同时按模块拆分为切片文件：`file-catalog-M001.json`、`file-catalog-M002.json`、...
- 根级文件（`module: null`）写入 `file-catalog-root.json`
- file-catalog.json 原子写入 — 文件存在即代表 2.3.7 完成。崩溃后重启时，若 file-catalog.json 不存在则从 2.3 最后完成的模块继续

**b. 构建 code-index.json**
- 从所有卡片的 business_intent + business_summary 提取业务概念 → `concepts` 倒排索引
- 从 source-summary.data_entities 提取实体 + 从卡片补充 `used_by` → `entities` 索引
- 从卡片中 kind=controller/handler 的 symbols 提取 API 端点 → `api_surface` 索引
- 写入 `.allforai/code-replicate/code-index.json`

**c. 更新进度**
- 写入 replicate-config.progress step `"2.3.7"`

> Schema 详见 ./docs/schema-reference.md#file-catalog 和 #code-index

## 2.4 project_archetype — 项目特征识别

LLM 判断项目**核心价值类型**，写入 replicate-config.json 的 `project_archetype` 字段（自由描述，不限枚举）。

影响后续所有阶段：产物格式、测试向量模型、验证维度。
