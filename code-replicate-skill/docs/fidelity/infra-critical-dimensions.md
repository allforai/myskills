# 关键基础设施维度 (I1-I4)

> 仅当 infrastructure-profile.json 存在且含 `cannot_substitute: true` 的组件时加载。
> 这些组件的任何近似替代都是致命的 — 服务端会拒绝连接、数据会损坏、wrapper 会崩溃。
> 与 F8（flexible 组件）分开评分，避免 flexible 的高分掩盖 critical 的致命问题。

---

## I1 — 协议精确还原

**适用条件**：infrastructure-profile 中有 `cannot_substitute: true` 且 category 涉及通信/协议的组件

对比 protocol_spec 与目标代码的协议实现：
- 帧格式（字段偏移、长度、编码）是否与 protocol_spec.frame_format 一致？
- 状态机（转换规则）是否与 protocol_spec.state_machine 一致？
- 与服务端/其他客户端的线上兼容性 — 如果 test-vectors 存在，R3 的结果直接纳入此维度
- 评分 = 精确还原的协议组件数 / 总 cannot_substitute 协议组件数 × 100
- **0 分容忍度**：任何协议组件不精确 → 该维度整体评 0 分（一个协议错 = 全部通信断裂）

## I2 — 加密精确还原

**适用条件**：infrastructure-profile 中有 `cannot_substitute: true` 且 category 涉及加密的组件

对比加密组件的 test_vectors 与目标代码的加密输出：
- 同密钥 + 同明文 → 密文是否 bit-for-bit 一致？
- 密钥派生（KDF）是否使用相同参数？
- IV/Nonce 生成方式是否一致？
- 评分 = test-vectors 通过率（R3 中加密相关向量）
- **0 分容忍度**：加密输出不一致 → 服务端解密失败 → 整体评 0 分

## I3 — 原生依赖还原

**适用条件**：infrastructure-profile 中有 category 涉及 native_sdk / 二进制依赖的组件

对比原生二进制依赖：
- 每个 .a/.dll/.framework/.aar 是否获取了目标平台的等价版本？
- 如果供应商提供了目标平台构建 → 是否正确集成？
- 如果供应商未提供 → 是否有替代方案且与 API 契约兼容？
- 评分 = 已解决的原生依赖数 / 总原生依赖数 × 100

## I4 — 代码生成一致性

**适用条件**：infrastructure-profile 中有 category 涉及 code_generation 的组件

对比代码生成产物：
- protobuf/thrift/OpenAPI 等 IDL 文件是否存在于目标项目？
- 是否用**同一工具**生成目标代码（不是手写实体类）？
- 生成的目标代码与源码的 IDL 版本是否一致？
- 评分 = 正确使用代码生成的组件数 / 总代码生成组件数 × 100

---

## 与 F8 的关系

```
infrastructure-profile.json 中的组件
    ↓
  cannot_substitute: true?
    ├── 是 → I1-I4（关键基础设施，0 分容忍度）
    └── 否 → F8（flexible 基础设施，功能等价即可）
```

**综合评分时 I1-I4 的权重应高于 F8** — 一个 F8 组件缺失只是功能降级，一个 I1 组件错误是整个系统不可用。

cr-fidelity 骨架的评分公式中，I 维度有任何一个评 0 分 → 综合分直接标记为 `CRITICAL_INFRA_FAILURE`，不管其他维度多高分。
