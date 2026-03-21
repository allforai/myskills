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

## 2.3 source-summary.json — 模块摘要

LLM 逐模块读 key_files → 输出：
- responsibility 单句描述
- exposed_interfaces 列表
- 核心 entities
- 大模块（>50 文件）优先分析 key_files

**非代码配置文件也可能含业务逻辑**（nginx.conf, routes.yaml, OpenAPI spec 等）。引用根目录文件时使用 `"module": null`。

> 分析原则详见 ${CLAUDE_PLUGIN_ROOT}/docs/analysis-principles.md

## 2.4 project_archetype — 项目特征识别

LLM 判断项目**核心价值类型**，写入 replicate-config.json 的 `project_archetype` 字段（自由描述，不限枚举）。

影响后续所有阶段：产物格式、测试向量模型、验证维度。
