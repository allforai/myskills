#!/bin/bash
# 测试 OpenRouter MCP 服务器连接

cd /home/hello/Documents/myskills/product-design-skill/mcp-openrouter

echo "=== OpenRouter MCP 连接测试 ==="
echo ""

# 检查 API Key
if [ -z "$OPENROUTER_API_KEY" ]; then
    echo "❌ OPENROUTER_API_KEY 未设置"
    exit 1
else
    echo "✅ OPENROUTER_API_KEY 已设置：${OPENROUTER_API_KEY:0:15}..."
fi

# 测试 API 连接
echo ""
echo "测试 OpenRouter API 连接..."
RESPONSE=$(curl -s -X POST "https://openrouter.ai/api/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -d '{
    "model": "qwen/qwen-2.5-72b-instruct",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 5
  }')

if echo "$RESPONSE" | grep -q "choices"; then
    echo "✅ OpenRouter API 连接成功"
else
    echo "❌ OpenRouter API 连接失败"
    echo "响应：$RESPONSE"
    exit 1
fi

# 检查 MCP 服务器已编译
if [ -f "dist/index.js" ]; then
    echo "✅ MCP 服务器已编译：dist/index.js"
else
    echo "❌ MCP 服务器未编译，运行 npm run build"
    npm run build
fi

# 检查路由配置
echo ""
echo "=== 已配置的 Task 路由 ==="
grep -A 50 "defaultRouting" src/config/defaults.ts | head -50

echo ""
echo "=== 测试完成 ==="
