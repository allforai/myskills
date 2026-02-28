#!/bin/bash
# 创新增强流程 - 完整测试脚本 (修复版)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 固定输出目录
OUTPUT_DIR="../../.allforai/product-concept/innovation-test"
mkdir -p "$OUTPUT_DIR"

echo "=========================================="
echo "  创新增强流程测试 - 产品概念阶段"
echo "=========================================="
echo ""
echo "输出目录：$OUTPUT_DIR"
echo ""

# 检查 API Key
if [ -z "$OPENROUTER_API_KEY" ]; then
    echo "❌ OPENROUTER_API_KEY 未设置"
    exit 1
fi

# 获取最新模型（分离日志和输出）
echo "📋 加载最新模型..."

QWEN_MODEL=$(node -e "const r=require('./dist/openrouter/resolver.js'); r.resolveLatestModel('qwen').then(m=>process.stdout.write(m))" 2>/dev/null)
LLAMA_MODEL=$(node -e "const r=require('./dist/openrouter/resolver.js'); r.resolveLatestModel('llama').then(m=>process.stdout.write(m))" 2>/dev/null)
DEEPSEEK_MODEL=$(node -e "const r=require('./dist/openrouter/resolver.js'); r.resolveLatestModel('deepseek').then(m=>process.stdout.write(m))" 2>/dev/null)

echo "  Qwen:     $QWEN_MODEL"
echo "  Llama:    $LLAMA_MODEL"
echo "  DeepSeek: $DEEPSEEK_MODEL"
echo ""

# 测试函数
call_model() {
    local task="$1"
    local model="$2"
    local prompt="$3"
    local temperature="$4"
    local output_file="$5"
    local min_length="$6"
    
    echo -n "调用 $task... "
    
    for i in 1 2; do
        node -e "
const { chatCompletion } = require('./dist/openrouter/client.js');
async function call() {
  const result = await chatCompletion('$model', [{ role: 'user', content: \`$prompt\` }], $temperature);
  console.log(result.content);
}
call().catch(e => { console.error('ERROR:', e.message); process.exit(1); });
" > "$output_file" 2>&1
        
        if [ $? -eq 0 ]; then
            local length=$(wc -c < "$output_file" | tr -d ' ')
            if [ $length -ge $min_length ]; then
                echo "✅ (${length} bytes)"
                return 0
            else
                echo "⚠️ 输出过短 (${length}/${min_length})，重试..."
            fi
        else
            echo "❌ 失败，重试..."
        fi
        sleep 1
    done
    
    echo "⚠️ 保留当前输出"
    return 0
}

echo "=========================================="
echo "Step 0 Phase C: 假设清零"
echo "=========================================="

call_model "assumption_challenge" "$QWEN_MODEL" \
    "列出英语教育行业的 5 条共识。要求：每条 1-2 句话，聚焦可挑战的行业惯例。" \
    "1.0" "$OUTPUT_DIR/01-assumption-zeroing.txt" "200"

call_model "constraint_classification" "$LLAMA_MODEL" \
    "判断以下是物理定律还是人为约定：1.越早学越好 2.必须背单词 3.需要老师 4.注意力<15 分钟 5.需要重复 7 次。格式：【编号】类别 | 理由（20 字内）" \
    "0.3" "$OUTPUT_DIR/02-constraint-classification.txt" "150"

echo ""
echo "=========================================="
echo "Step 0 Phase B+: 创新机会"
echo "=========================================="

call_model "innovation_exploration" "$QWEN_MODEL" \
    "基于可挑战假设提出 3 个创新方向：背单词→语境习得、需老师→AI 全程、固定课程→个性化。每方向：名称 + 核心点 (20 字)+ 可行性 (高/中/低)" \
    "0.9" "$OUTPUT_DIR/03-innovation-opportunities.txt" "300"

echo ""
echo "=========================================="
echo "Step 3 Phase B: 对抗性生成"
echo "=========================================="

call_model "disruptive_innovation" "$QWEN_MODEL" \
    "3 个务实英语学习 APP 方案。约束：技术可行 (现有 API)、成本可控、不要 VR/AR。每方案：名称 + 功能 (50 字)+ 打破惯例 + 技术栈" \
    "1.2" "$OUTPUT_DIR/04-disruptive-concepts.txt" "400"

call_model "cross_domain_research" "$DEEPSEEK_MODEL" \
    "从抖音、王者荣耀、Keep 各找 1 个用户留存案例。每案例：核心机制 (20 字)+ 如何迁移到英语学习" \
    "0.9" "$OUTPUT_DIR/05-cross-domain-cases.txt" "300"

call_model "synthesis_innovation" "$LLAMA_MODEL" \
    "整合：A 刷抖音式学习 (碎片无分级) vs B 系统课程 (结构有分级)。输出：方案名 + 如何保持趣味 + 如何确保效果 + 技术要点" \
    "0.8" "$OUTPUT_DIR/06-synthesized-concept.txt" "300"

echo ""
echo "=========================================="
echo "生成报告"
echo "=========================================="

cat > "$OUTPUT_DIR/README.md" << REPORT
# 创新增强流程测试报告

**时间**: $(date '+%Y-%m-%d %H:%M:%S')

## 模型
| 家族 | 模型 |
|------|------|
| Qwen | $QWEN_MODEL |
| Llama | $LLAMA_MODEL |
| DeepSeek | $DEEPSEEK_MODEL |

## 输出
| 文件 | 大小 |
|------|------|
REPORT

for file in "$OUTPUT_DIR"/*.txt; do
    [ -f "$file" ] || continue
    fname=$(basename "$file")
    size=$(wc -c < "$file" | tr -d ' ')
    echo "| $fname | $size bytes |" >> "$OUTPUT_DIR/README.md"
done

echo ""
echo "=========================================="
echo "✅ 测试完成"
echo "=========================================="
echo ""
ls -la "$OUTPUT_DIR"
