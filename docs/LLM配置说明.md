# LLM API 配置说明

本项目使用通用的 HTTP API 调用方式，支持任何兼容 OpenAI API 格式的服务。

## 配置方法

1. 复制配置文件：
```bash
cp env.example .env
```

2. 编辑 `.env` 文件，配置以下参数：

```bash
# 设置提供商
DEFAULT_LLM_PROVIDER=custom

# 配置API信息
LLM_API_KEY=your-api-key-here
LLM_BASE_URL=https://api.example.com/v1
LLM_MODEL=model-name
```

## 支持的服务

### OpenRouter（推荐 - 一个API访问多个模型）

```bash
DEFAULT_LLM_PROVIDER=custom
LLM_API_KEY=sk-or-v1-your-key-here
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_MODEL=deepseek/deepseek-chat
```

获取API密钥：https://openrouter.ai/keys

支持的模型：
- `deepseek/deepseek-chat` - DeepSeek聊天模型（性价比高）
- `google/gemini-2.0-flash-exp:free` - Gemini 2.0 Flash（免费）
- `anthropic/claude-3.5-sonnet` - Claude 3.5 Sonnet
- `openai/gpt-4o-mini` - GPT-4o Mini
- 更多模型：https://openrouter.ai/models

### DeepSeek（性价比高）

```bash
DEFAULT_LLM_PROVIDER=custom
LLM_API_KEY=sk-your-key-here
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat
```

获取API密钥：https://platform.deepseek.com

### Google Gemini（免费额度大）

```bash
DEFAULT_LLM_PROVIDER=custom
LLM_API_KEY=your-google-api-key
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
LLM_MODEL=gemini-2.0-flash-exp
```

获取API密钥：https://aistudio.google.com/apikey

### 智谱AI（国内服务）

```bash
DEFAULT_LLM_PROVIDER=custom
LLM_API_KEY=your-zhipu-key
LLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4/
LLM_MODEL=glm-4-flash
```

获取API密钥：https://open.bigmodel.cn

### 硅基流动（中转平台）

```bash
DEFAULT_LLM_PROVIDER=custom
LLM_API_KEY=your-siliconflow-key
LLM_BASE_URL=https://api.siliconflow.cn/v1
LLM_MODEL=deepseek-ai/DeepSeek-V3
```

获取API密钥：https://siliconflow.cn

### OpenAI（官方）

```bash
DEFAULT_LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
OPENAI_BASE_URL=https://api.openai.com/v1
DEFAULT_OPENAI_MODEL=gpt-4o-mini
```

获取API密钥：https://platform.openai.com/api-keys

## 测试配置

配置完成后，运行测试脚本验证：

```bash
python tests/test_llm_config.py
```

如果配置正确，会显示：
```
✓ 配置检查通过！
✓ API连接测试成功！
```

## 技术说明

本项目使用标准的 OpenAI Chat Completions API 格式：

```
POST {BASE_URL}/chat/completions
Authorization: Bearer {API_KEY}

{
    "model": "{MODEL}",
    "messages": [...],
    "temperature": 0.3
}
```

只要你使用的服务支持这种格式，就可以直接使用。

## 常见问题

### Q: 如何选择服务？

**推荐顺序**：
1. **OpenRouter** - 一个API访问多个模型，灵活方便
2. **DeepSeek** - 性价比最高
3. **Gemini** - 免费额度大
4. **智谱AI** - 国内服务，稳定

### Q: 如何切换服务？

修改 `.env` 文件中的配置，然后重新运行脚本即可。

### Q: API调用失败怎么办？

1. 运行 `python tests/test_llm_config.py` 测试配置
2. 检查API密钥是否正确
3. 检查Base URL是否正确（注意结尾的 /v1）
4. 检查模型名称是否正确
5. 查看日志中的详细错误信息

### Q: 如何估算费用？

建议先用 `--limit 10` 测试少量论文，观察token消耗：
- 每篇论文约消耗 2000-5000 tokens（输入）
- LLM响应约 200-500 tokens（输出）

根据你选择的服务商定价计算总成本。

## 进阶配置

### 自定义超时时间

在调用时可以设置更长的超时时间（适用于网络较慢的情况）：

修改 `llm_client.py` 中的 `timeout` 参数。

### 使用代理

如果需要通过代理访问，可以设置环境变量：

```bash
export HTTP_PROXY=http://proxy.example.com:8080
export HTTPS_PROXY=http://proxy.example.com:8080
```

或在代码中配置 `requests` 的代理参数。

