#!/bin/bash
# 创新增强流程 - 完整测试脚本
# 使用 MCP 动态模型解析（LLM 判断最新模型）

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "  创新增强流程测试 - 产品概念阶段"
echo "=========================================="
echo ""

# 检查 API Key
if [ -z "$OPENROUTER_API_KEY" ]; then
    echo "❌ OPENROUTER_API_KEY 未设置"
    exit 1
fi

echo "✅ API Key 已配置"
echo ""

# 获取最新模型
echo "📋 获取最新模型 (LLM 智能判断)..."

GPT_MODEL=$(node -e "const r=require('./dist/openrouter/resolver.js'); r.resolveLatestModel('gpt').then(m=>console.log(m))")
GEMINI_MODEL=$(node -e "const r=require('./dist/openrouter/resolver.js'); r.resolveLatestModel('gemini').then(m=>console.log(m))")
DEEPSEEK_MODEL=$(node -e "const r=require('./dist/openrouter/resolver.js'); r.resolveLatestModel('deepseek').then(m=>console.log(m))")
LLAMA_MODEL=$(node -e "const r=require('./dist/openrouter/resolver.js'); r.resolveLatestModel('llama').then(m=>console.log(m))")
QWEN_MODEL=$(node -e "const r=require('./dist/openrouter/resolver.js'); r.resolveLatestModel('qwen').then(m=>console.log(m))")

echo "  GPT:      $GPT_MODEL"
echo "  Gemini:   $GEMINI_MODEL"
echo "  DeepSeek: $DEEPSEEK_MODEL"
echo "  Llama:    $LLAMA_MODEL"
echo "  Qwen:     $QWEN_MODEL"
echo ""

# 创建测试输出目录
OUTPUT_DIR="../../.allforai/product-concept/test-output-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$OUTPUT_DIR"

echo "输出目录：$OUTPUT_DIR"
echo ""

# 测试函数
call_model() {
    local task="$1"
    local model="$2"
    local prompt="$3"
    local temperature="$4"
    local output_file="$5"
    
    echo "调用 $task ($model, temp=$temperature)..."
    
    node -e "
const { chatCompletion } = require('./dist/openrouter/client.js');

async function call() {
  const result = await chatCompletion(
    '$model',
    [{ role: 'user', content: \`$prompt\` }],
    $temperature
  );
  console.log(result.content);
}

call().catch(e => {
  console.error('ERROR:', e.message);
  process.exit(1);
});
" > "$output_file" 2>&1
    
    if [ $? -eq 0 ]; then
        echo "  ✅ 成功 → $output_file"
    else
        echo "  ❌ 失败，检查 $output_file"
        cat "$output_file"
    fi
}

echo "=========================================="
echo "Step 0 Phase C: 假设清零"
echo "=========================================="

# 挑战者 - 列出行业共识 (使用最新 Qwen)
call_model \
    "assumption_challenge" \
    "$QWEN_MODEL" \
    "列出英语教育行业的 5 条共识，每条用一句话描述" \
    "1.0" \
    "$OUTPUT_DIR/challenger-output.txt"

# 守护者 - 区分约束类型 (使用最新 Llama)
call_model \
    "constraint_classification" \
    "$LLAMA_MODEL" \
    "以下共识哪些是物理定律（不可改变），哪些是人为约定（可以挑战）？
1. 英语学习越早开始越好
2. 必须背单词才能学会
3. 需要老师指导
4. 用户注意力有限（<15 分钟）
5. 语言习得需要重复（7 次以上接触）

请逐一分类并简要说明理由。" \
    "0.3" \
    "$OUTPUT_DIR/guardian-output.txt"

echo ""
echo "=========================================="
echo "Step 3 Phase B: 对抗性生成"
echo "=========================================="

# 颠覆者 - 提出激进方案 (使用最新 Qwen)
call_model \
    "disruptive_innovation" \
    "$QWEN_MODEL" \
    "针对英语学习 APP，提出 3 个最激进的创新方案，打破所有行业惯例。
每个方案包括：
1. 方案名称
2. 核心创新点
3. 如何打破惯例" \
    "1.2" \
    "$OUTPUT_DIR/disruptor-output.txt"

# 考古学家 - 跨域案例 (使用最新 DeepSeek)
call_model \
    "cross_domain_research" \
    "$DEEPSEEK_MODEL" \
    "从以下行业各找 1 个案例，说明它们如何让用户持续使用产品：
1. 游戏行业
2. 健身行业
3. 社交媒体

每个案例包括：
- 产品名称
- 核心策略
- 可迁移到英语学习的模式" \
    "0.9" \
    "$OUTPUT_DIR/archaeologist-output.txt"

# 炼金师 - 整合方案 (使用最新 Llama)
call_model \
    "synthesis_innovation" \
    "$LLAMA_MODEL" \
    "整合以下两个观点，给出平衡的创新方案：
观点 A: 完全取消课程概念，像刷抖音一样学英语
观点 B: 保留隐性分级，避免用户挫败感

请提出一个既能保持学习趣味性，又能确保学习效果的方案。" \
    "0.8" \
    "$OUTPUT_DIR/alchemist-output.txt"

echo ""
echo "=========================================="
echo "测试完成"
echo "=========================================="
echo ""
echo "输出文件:"
ls -la "$OUTPUT_DIR"

echo ""
echo "摘要:"
for file in "$OUTPUT_DIR"/*.txt; do
    echo ""
    echo "--- $(basename "$file") ---"
    head -5 "$file"
done

echo ""
echo "💡 提示：模型缓存 24 小时有效，下次运行将直接使用缓存"
