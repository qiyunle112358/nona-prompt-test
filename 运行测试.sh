#!/bin/bash
# 图片Prompt测试 - 快速测试脚本

# 使用方法：
# 1. 将你的OpenRouter API Key填入下面的变量
# 2. 运行: bash 运行测试.sh

OPENROUTER_API_KEY="your-openrouter-api-key-here"

# 检查API Key
if [ "$OPENROUTER_API_KEY" = "your-openrouter-api-key-here" ]; then
    echo "❌ 请先设置 OPENROUTER_API_KEY"
    echo "编辑此文件，将 'your-openrouter-api-key-here' 替换为你的实际API Key"
    exit 1
fi

echo "🚀 开始测试 - 收集5张流程图"
echo "=================================="

python3 scripts/image_prompt_test.py \
    --num-images 5 \
    --year 2024 \
    --num-prompts 5 \
    --openrouter-api-key "$OPENROUTER_API_KEY" \
    --output-dir data/prompt_test \
    --max-papers 30

echo ""
echo "✅ 测试完成！"
echo "结果保存在: data/prompt_test/results/"
