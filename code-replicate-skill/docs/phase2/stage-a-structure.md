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

> Schema 详见 ${CLAUDE_PLUGIN_ROOT}/docs/schema-reference.md#discovery-profile

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

> 分析原则详见 ${CLAUDE_PLUGIN_ROOT}/docs/analysis-principles.md

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

**Step 4: 写入覆盖率**

最终 source-summary 中每个模块带 `coverage` 字段。Phase 2.14 用户确认时展示覆盖率 — 用户看到"网络模块覆盖率 18%"就会要求补读。

**底线**：coverage < 50% 的模块必须补读到 ≥ 50%。不允许"22 个文件只读了 4 个就声称理解了这个模块"。

## 2.4 project_archetype — 项目特征识别

LLM 判断项目**核心价值类型**，写入 replicate-config.json 的 `project_archetype` 字段（自由描述，不限枚举）。

影响后续所有阶段：产物格式、测试向量模型、验证维度。
