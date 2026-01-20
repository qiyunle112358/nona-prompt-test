# Einsia-O API 配置说明

## 需要配置的信息

为了使用图片分析和生成功能，需要提供以下信息：

### 1. API端点信息

请提供以下信息：

- **API基础URL**: 例如 `https://api.einsia.com/v1` 或实际端点
- **图片分析端点**: 例如 `/image/analyze` 或 `/v1/analyze`
- **图片生成端点**: 例如 `/image/generate` 或 `/v1/generate`
- **认证方式**: Bearer Token / API Key / 其他

### 2. API请求格式

请提供：

- **请求方法**: POST / GET
- **请求头**: 需要哪些headers（如Authorization）
- **请求体格式**: JSON / Form-data / Multipart
- **图片上传方式**: base64编码 / 文件上传 / URL

### 3. API响应格式

请提供：

- **成功响应格式**: JSON结构示例
- **错误响应格式**: 错误码和错误信息格式
- **Prompt字段名**: 响应中prompt的字段名（如 `prompt`, `prompts`, `description`等）

### 4. 图片生成参数

请提供：

- **支持的图片尺寸**: 如 512x512, 1024x1024等
- **支持的图片格式**: PNG / JPG等
- **其他参数**: 如风格、质量等可选参数

## 示例配置

如果你有API文档，请提供类似以下格式的信息：

```python
EINSIA_CONFIG = {
    "base_url": "https://api.einsia.com/v1",
    "analyze_endpoint": "/image/analyze",
    "generate_endpoint": "/image/generate",
    "api_key": "your-api-key-here",
    "headers": {
        "Authorization": "Bearer {api_key}",
        "Content-Type": "application/json"
    },
    "analyze_params": {
        "num_prompts": 5,
        "format": "json"
    },
    "generate_params": {
        "size": "1024x1024",
        "format": "png"
    }
}
```

## 当前状态

目前代码中使用了占位符实现，需要根据实际API文档进行修改。

请提供上述信息，我会更新代码以支持实际的API调用。
