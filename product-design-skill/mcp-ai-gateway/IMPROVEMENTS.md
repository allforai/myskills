# 创新增强流程改进点

基于测试运行发现的问题和改进方案。

---

## 发现的问题

### 1. Prompt 设计问题

**问题**：
- Prompt 过于开放，导致模型输出冗长但不聚焦
- 没有指定输出格式，后续处理困难
- 示例：guardian 输出大量定义说明，实际分类内容被稀释

**改进**：
```bash
# 改进前
"判断以下共识哪些是物理定律，哪些是人为约定"

# 改进后
"输出格式：【编号】类别 | 理由（20 字内）"
```

---

### 2. 输出质量问题

**问题**：
- 部分输出过短（<100 bytes），信息量不足
- 没有自动重试机制
- 示例：challenger 只输出 5 条泛泛而谈的共识

**改进**：
- 添加最小输出长度检查
- 自动重试（最多 2 次）
- 约束 Prompt 聚焦可挑战的惯例

---

### 3. 测试脚本问题

**问题**：
- 每次运行创建新时间戳目录，输出分散
- 缓存日志混入模型选择输出
- 没有汇总报告

**改进**：
- 固定输出目录 `innovation-test/`
- 静默加载模型（2>/dev/null）
- 自动生成 README.md 汇总报告

---

### 4. 模型选择问题

**问题**：
- 硬编码模型 ID（如 `qwen/qwen-2.5-72b-instruct`）
- 无法自动使用最新模型

**改进**：
- 使用 `resolveLatestModel()` 动态获取
- LLM 判断 + 24 小时缓存

---

### 5. 输出内容问题

**问题**：
- 创新方案不切实际（如 VR/AR）
- 跨域案例过于宽泛
- 整合方案缺乏技术实现细节

**改进**：
- Prompt 明确约束（不要 VR/AR）
- 指定案例来源（抖音/王者荣耀/Keep）
- 要求输出技术实现要点

---

## 改进后的测试流程

```bash
cd mcp-openrouter
./test-innovation-flow.sh
```

### 输出结构

```
.allforai/product-concept/innovation-test/
├── README.md                          # 汇总报告（自动生成）
├── 01-assumption-zeroing.txt          # 假设清零
├── 02-constraint-classification.txt   # 约束分类
├── 03-innovation-opportunities.txt    # 创新机会
├── 04-disruptive-concepts.txt         # 颠覆性概念
├── 05-cross-domain-cases.txt          # 跨域案例
└── 06-synthesized-concept.txt         # 整合方案
```

### 质量检查

| 文件 | 最小长度 | 检查项 |
|------|---------|--------|
| 01-assumption-zeroing.txt | 200 bytes | ≥5 条共识 |
| 02-constraint-classification.txt | 150 bytes | ≥5 条分类 |
| 03-innovation-opportunities.txt | 300 bytes | ≥3 个方向 |
| 04-disruptive-concepts.txt | 400 bytes | ≥3 个方案 |
| 05-cross-domain-cases.txt | 300 bytes | ≥3 个案例 |
| 06-synthesized-concept.txt | 300 bytes | 完整方案 |

---

## 下一步改进建议

### 短期（本周）
1. ✅ 优化 Prompt 设计
2. ✅ 添加输出质量检查
3. ✅ 固定输出目录
4. ✅ 生成汇总报告

### 中期（本月）
1. ⏳ 添加人工评审环节
2. ⏳ 创新方案可行性评分
3. ⏳ 与 product-map 自动对接

### 长期（下季度）
1. ⏳ 建立创新方案库（历史对比）
2. ⏳ 多模型投票机制
3. ⏳ 用户反馈闭环

---

## 模型缓存说明

| 缓存类型 | 文件 | 有效期 |
|---------|------|--------|
| LLM 模型选择 | `.allforai/llm-model-cache.json` | 24 小时 |
| 模型列表 | `.allforai/models-cache.json` | 动态更新 |

缓存过期后自动重新获取，无需手动干预。
