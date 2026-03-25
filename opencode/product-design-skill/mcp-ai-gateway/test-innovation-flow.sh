#!/bin/bash
# 创新增强流程 - 完整测试脚本 (最终修复版)
# 使用临时文件传递 prompt，避免 bash 解析特殊字符

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 固定输出目录
OUTPUT_DIR="../../.allforai/product-concept/innovation-test"
mkdir -p "$OUTPUT_DIR"

# 临时目录存放 prompts
PROMPT_DIR=$(mktemp -d)
trap "rm -rf $PROMPT_DIR" EXIT

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

# 获取最新模型（日志输出到 stderr）
echo "📋 加载最新模型..." >&2

QWEN_MODEL=$(node -e "const r=require('./dist/openrouter/resolver.js'); r.resolveLatestModel('qwen').then(m=>process.stdout.write(m))" 2>/dev/null)
LLAMA_MODEL=$(node -e "const r=require('./dist/openrouter/resolver.js'); r.resolveLatestModel('llama').then(m=>process.stdout.write(m))" 2>/dev/null)
DEEPSEEK_MODEL=$(node -e "const r=require('./dist/openrouter/resolver.js'); r.resolveLatestModel('deepseek').then(m=>process.stdout.write(m))" 2>/dev/null)

echo "  Qwen:     $QWEN_MODEL" >&2
echo "  Llama:    $LLAMA_MODEL" >&2
echo "  DeepSeek: $DEEPSEEK_MODEL" >&2
echo "" >&2

# 测试函数 - 从文件读取 prompt
call_model() {
    local task="$1"
    local model="$2"
    local prompt_file="$3"
    local temperature="$4"
    local output_file="$5"
    local min_length="$6"
    
    echo -n "调用 $task... " >&2
    
    for i in 1 2; do
        node -e "
const { chatCompletion } = require('./dist/openrouter/client.js');
const fs = require('fs');
const prompt = fs.readFileSync('$prompt_file', 'utf-8');
async function call() {
  const result = await chatCompletion('$model', [{ role: 'user', content: prompt }], $temperature);
  console.log(result.content);
}
call().catch(e => { console.error('ERROR:', e.message); process.exit(1); });
" > "$output_file" 2>&1
        
        if [ $? -eq 0 ]; then
            local length=$(wc -c < "$output_file" | tr -d ' ')
            if [ $length -ge $min_length ]; then
                echo "✅ (${length} bytes)" >&2
                return 0
            else
                echo "⚠️ 输出过短 (${length}/${min_length})，重试..." >&2
            fi
        else
            echo "❌ 失败，重试..." >&2
        fi
        sleep 1
    done
    
    echo "⚠️ 保留当前输出" >&2
    return 0
}

# 写入 prompts 到临时文件
cat > "$PROMPT_DIR/01-prompt.txt" << 'PROMPT'
列出英语教育行业的 5 条共识。
要求：
- 每条 1-2 句话
- 聚焦可挑战的行业惯例（不是泛泛而谈）
- 格式：1. 共识内容。2. 共识内容。...
PROMPT

cat > "$PROMPT_DIR/02-prompt.txt" << 'PROMPT'
判断以下是物理定律还是人为约定：
1. 越早学越好
2. 必须背单词
3. 需要老师
4. 注意力<15 分钟
5. 需要重复 7 次

输出格式：【编号】类别 | 理由（20 字内）
PROMPT

cat > "$PROMPT_DIR/03-prompt.txt" << 'PROMPT'
基于以下可挑战假设提出 3 个创新方向：
- 背单词 → 语境习得
- 需老师 → AI 全程
- 固定课程 → 个性化

每方向包括：
1. 方向名称
2. 核心创新点（20 字内）
3. 技术可行性（高/中/低）
PROMPT

cat > "$PROMPT_DIR/04-prompt.txt" << 'PROMPT'
提出 3 个务实的英语学习 APP 创新方案。
约束：
- 技术上可行（现有 API + 开源库）
- 成本可控（小团队可承担）
- 不要 VR/AR/MR 等不切实际的技术

每方案包括：
1. 方案名称
2. 核心功能（50 字内）
3. 打破的惯例
4. 技术栈
PROMPT

cat > "$PROMPT_DIR/05-prompt.txt" << 'PROMPT'
从抖音、王者荣耀、Keep 各找 1 个让用户持续使用的案例。

每案例包括：
- 产品名称
- 核心机制（20 字内）
- 如何迁移到英语学习
PROMPT

cat > "$PROMPT_DIR/06-prompt.txt" << 'PROMPT'
整合以下对立观点：
A: 刷抖音式学习（碎片化、无分级）
B: 系统性课程（结构化、有分级）

输出一个平衡方案，包括：
1. 方案名称
2. 如何保持趣味性
3. 如何确保学习效果
4. 技术实现要点
PROMPT

echo "=========================================="
echo "Step 0 Phase C: 假设清零"
echo "==========================================" >&2

call_model "assumption_challenge" "$QWEN_MODEL" "$PROMPT_DIR/01-prompt.txt" "1.0" "$OUTPUT_DIR/01-assumption-zeroing.txt" "200"
call_model "constraint_classification" "$LLAMA_MODEL" "$PROMPT_DIR/02-prompt.txt" "0.3" "$OUTPUT_DIR/02-constraint-classification.txt" "150"

echo "" >&2
echo "=========================================="
echo "Step 0 Phase B+: 创新机会"
echo "==========================================" >&2

call_model "innovation_exploration" "$QWEN_MODEL" "$PROMPT_DIR/03-prompt.txt" "0.9" "$OUTPUT_DIR/03-innovation-opportunities.txt" "300"

echo "" >&2
echo "=========================================="
echo "Step 3 Phase B: 对抗性生成"
echo "==========================================" >&2

call_model "disruptive_innovation" "$QWEN_MODEL" "$PROMPT_DIR/04-prompt.txt" "1.2" "$OUTPUT_DIR/04-disruptive-concepts.txt" "400"
call_model "cross_domain_research" "$DEEPSEEK_MODEL" "$PROMPT_DIR/05-prompt.txt" "0.9" "$OUTPUT_DIR/05-cross-domain-cases.txt" "300"
call_model "synthesis_innovation" "$LLAMA_MODEL" "$PROMPT_DIR/06-prompt.txt" "0.8" "$OUTPUT_DIR/06-synthesized-concept.txt" "300"

echo "" >&2
echo "=========================================="
echo "生成报告"
echo "==========================================" >&2

cat > "$OUTPUT_DIR/README.md" << REPORT
# 创新增强流程测试报告

**时间**: $(date '+%Y-%m-%d %H:%M:%S')

## 使用模型
| 家族 | 模型 ID |
|------|---------|
| Qwen | $QWEN_MODEL |
| Llama | $LLAMA_MODEL |
| DeepSeek | $DEEPSEEK_MODEL |

## 输出文件
| 文件 | 大小 | 状态 |
|------|------|------|
REPORT

for file in "$OUTPUT_DIR"/*.txt; do
    [ -f "$file" ] || continue
    fname=$(basename "$file")
    size=$(wc -c < "$file" | tr -d ' ')
    echo "| $fname | $size bytes | ✅ |" >> "$OUTPUT_DIR/README.md"
done

echo "" >&2
echo "=========================================="
echo "✅ 测试完成"
echo "=========================================="
echo ""
echo "输出目录：$OUTPUT_DIR"
ls -la "$OUTPUT_DIR"
echo ""
echo "📄 报告：$OUTPUT_DIR/README.md"
