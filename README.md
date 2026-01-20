# Nona - 论文图片Prompt测试工具

自动化批量下载论文、提取流程图、生成Prompt并重新生成图片，用于测试和优化图片生成模型的预制Prompt。

## ✨ 功能特性

- 📚 **多领域论文收集**：从12个不同arXiv分类自动收集论文（计算机视觉、NLP、机器学习、AI等）
- 🔍 **智能图片提取**：基于关键词搜索，自动提取论文中的流程图/架构图/演示图
- 🤖 **AI Prompt生成**：使用OpenRouter API（google/gemini-2.5-flash）分析图片，生成5个不同的详细Prompt
- 🎨 **图片重新生成**：使用OpenRouter API（google/gemini-3-pro-image-preview）根据每个Prompt生成新图片
- 📊 **结构化输出**：每张原图及其对应的5个Prompt和5张生成图片整理在一起，方便对比

## 🚀 快速开始

### 1. 安装依赖

```bash
git clone https://github.com/qiyunle112358/nona-prompt-test.git
cd nona-prompt-test
pip install -r requirements.txt
```

### 2. 配置API密钥

复制配置文件并填入你的OpenRouter API Key：

```bash
cp env.example .env
```

编辑 `.env` 文件：

```bash
# 使用OpenRouter API
LLM_API_KEY=sk-or-v1-your-key-here
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_MODEL=deepseek/deepseek-chat
```

获取API Key：https://openrouter.ai/keys

### 3. 运行测试

```bash
# 测试2张图（推荐先用小数量测试）
python scripts/image_prompt_test.py \
    --num-images 2 \
    --year 2024 \
    --num-prompts 5 \
    --openrouter-api-key YOUR_API_KEY \
    --output-dir data/prompt_test

# 完整运行（100张图）
python scripts/image_prompt_test.py \
    --num-images 100 \
    --year 2024 \
    --num-prompts 5 \
    --openrouter-api-key YOUR_API_KEY \
    --output-dir data/prompt_test \
    --max-papers 500
```

## 📖 详细使用说明

### 参数说明

- `--num-images`: 要收集的流程图数量（默认100）
- `--year`: 论文年份（默认2024）
- `--num-prompts`: 每个原图生成的prompt数量（默认5）
- `--openrouter-api-key`: **必需**，OpenRouter API密钥
- `--output-dir`: 输出目录（默认 `data/prompt_test`）
- `--max-papers`: 最多处理的论文数量（默认500，用于确保能找到足够的流程图）

### 工作流程

1. **收集论文**：从12个不同领域随机收集指定年份的论文
2. **获取信息**：获取论文的arXiv ID、PDF下载链接等
3. **下载PDF**：下载所有论文的PDF文件
4. **提取流程图**：
   - 在PDF全文中搜索关键词（Figure, workflow, Architecture Diagram, Flowchart等）
   - 提取关键词所在页面的图片
   - 如果论文中没有找到关键词，自动跳过并继续处理下一篇
5. **生成Prompt**：使用 `google/gemini-2.5-flash` 分析每张流程图，生成5个不同的详细Prompt
6. **生成图片**：使用 `google/gemini-3-pro-image-preview` 根据每个Prompt生成图片
7. **整理输出**：将所有结果整理到结构化文件夹中

### 输出结构

```
data/prompt_test/
└── results/
    ├── <arxiv_id_1>/
    │   ├── original.png          # 原图
    │   ├── generated_1.png       # Prompt 1生成的图片
    │   ├── generated_2.png       # Prompt 2生成的图片
    │   ├── generated_3.png       # Prompt 3生成的图片
    │   ├── generated_4.png       # Prompt 4生成的图片
    │   ├── generated_5.png       # Prompt 5生成的图片
    │   └── prompts.txt           # 所有5个prompt文本
    └── <arxiv_id_2>/
        └── ...
```

## 🔧 核心功能

### 图片提取逻辑

程序会搜索以下关键词来定位流程图/演示图：

**英文关键词**：
- `Figure`, `workflow`, `Architecture Diagram`, `Flowchart`
- `Experimental Design`, `Technical Roadmap`

**中文关键词**：
- `流程图`, `技术路线`, `框架图`, `实验设计`
- `示意图`, `工作流程`, `架构图`

如果论文中没有找到这些关键词，程序会自动跳过该论文，继续处理下一篇。

### Prompt生成

- **模型**：`google/gemini-2.5-flash`
- **功能**：分析图片并生成详细的、可用于重新生成相似图片的Prompt
- **数量**：每张原图生成5个不同的Prompt

### 图片生成

- **模型**：`google/gemini-3-pro-image-preview`
- **前置Prompt**：使用科学插图专家的预设Prompt，确保生成高质量的学术可视化图片
- **输出**：每个Prompt生成一张图片

## 📚 其他功能

### 批量下载论文

除了图片Prompt测试，这个工具还支持批量下载论文：

```bash
# 收集论文标题
python scripts/collect_titles.py --source arxiv --year 2024 --arxiv-category cs.CV --max-results 1000

# 获取论文信息
python scripts/fetch_paper_info.py --limit 100

# 下载PDF
python scripts/process_pdfs.py --limit 50
```

详细使用方法请查看：
- `快速开始-批量下载论文.md` - 批量下载论文的快速指南
- `使用指南.md` - 完整功能使用说明

### 清理数据

```bash
# 清理测试数据
python scripts/cleanup_data.py

# 清空所有数据（谨慎操作）
python scripts/clean_data.py
```

## 📋 项目结构

```
nona/
├── collectors/          # 论文收集器（arXiv、NeurIPS、ICLR等）
├── fetchers/           # 论文信息获取
├── processors/         # PDF处理和图片提取
├── analyzers/          # AI分析（可选）
├── scripts/            # 命令行脚本
│   ├── image_prompt_test.py  # 图片Prompt测试主程序
│   ├── collect_titles.py     # 收集论文标题
│   ├── fetch_paper_info.py   # 获取论文信息
│   └── process_pdfs.py       # 处理PDF
├── web/                # Web可视化界面
├── config.py           # 配置文件
├── database.py         # 数据库操作
└── requirements.txt    # 依赖列表
```

## ⚙️ 配置说明

### OpenRouter API配置

推荐使用OpenRouter，支持多个模型且性价比高：

1. 访问 https://openrouter.ai/keys 获取API Key
2. 在 `.env` 文件中配置：

```bash
LLM_API_KEY=sk-or-v1-your-key-here
LLM_BASE_URL=https://openrouter.ai/api/v1
```

### 支持的模型

- **图生文**：`google/gemini-2.5-flash`
- **文生图**：`google/gemini-3-pro-image-preview`

## 📝 注意事项

1. **API费用**：处理大量图片需要调用大量API，注意控制成本
2. **处理时间**：完整流程可能需要数小时，建议先用小数量测试
3. **存储空间**：确保有足够的磁盘空间（每张图片约几MB）
4. **网络连接**：需要稳定的网络连接下载论文和调用API

## 🐛 故障排除

### 问题1: 找不到足够的流程图

**解决**：增加 `--max-papers` 参数，处理更多论文

### 问题2: API调用失败

**解决**：
- 检查API密钥是否正确
- 检查网络连接
- 查看日志了解具体错误

### 问题3: Prompt解析错误

**解决**：程序已自动过滤总指令文本，如果仍有问题，请查看日志

## 📄 许可证

本项目采用 MIT 许可证。

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📞 联系方式

如有问题或建议，请提交Issue。

---

**开始测试你的Prompt吧！** 🚀
