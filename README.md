# 具身智能论文Survey工具

一个用于自动收集、处理和筛选具身智能领域论文的Python工具。

## 功能特点

- 📚 **论文收集**: 从NeurIPS、ICLR、ICML、CoRL、RSS、ICRA、IROS和arXiv自动收集论文标题
- 🔍 **信息获取**: 使用arXiv和OpenAlex API获取论文详细信息
- 📄 **PDF处理**: 下载PDF并使用OCR转换为结构化文本
- 🤖 **AI分析**: 使用大语言模型判断论文相关性并生成总结

## 项目结构

```
nona/
├── config.py              # 配置管理
├── database.py            # SQLite数据库操作
├── collectors/            # 模块1: 论文标题收集
│   ├── __init__.py
│   ├── arxiv.py
│   ├── neurips.py
│   ├── iclr.py
│   ├── icml.py
│   ├── corl.py
│   ├── rss.py
│   ├── icra.py
│   └── iros.py
├── fetchers/              # 模块2: 论文信息获取
│   ├── __init__.py
│   └── paper_fetcher.py
├── processors/            # 模块3: PDF处理
│   ├── __init__.py
│   ├── pdf_downloader.py
│   └── pdf_to_text.py
├── analyzers/             # 模块4: AI分析
│   ├── __init__.py
│   └── relevance_filter.py
├── scripts/               # 执行脚本
│   ├── collect_titles.py
│   ├── fetch_paper_info.py
│   ├── process_pdfs.py
│   └── analyze_papers.py
├── tests/                 # 测试模块
│   ├── test_config.py
│   ├── test_database.py
│   ├── test_collectors.py
│   ├── test_fetchers.py
│   ├── test_processors.py
│   ├── test_analyzers.py
│   └── run_all_tests.py
└── data/                  # 数据目录
    ├── papers.db
    ├── pdfs/
    └── texts/
```

## 安装

1. 克隆项目：
```bash
git clone <repository-url>
cd nona
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 配置环境变量：
```bash
cp .env.example .env
# 编辑 .env 文件，填入你的API密钥
```

## 使用方法

### 1. 收集论文标题

```bash
# 收集NeurIPS 2024的论文
python scripts/collect_titles.py --source neurips --year 2024

# 收集arXiv 2025年的cs.RO论文
python scripts/collect_titles.py --source arxiv --year 2025

# 收集所有来源
python scripts/collect_titles.py --all
```

### 2. 获取论文详细信息

```bash
# 获取待处理论文的详细信息
python scripts/fetch_paper_info.py

# 限制处理数量
python scripts/fetch_paper_info.py --limit 100
```

### 3. 处理PDF文件

```bash
# 下载并处理PDF
python scripts/process_pdfs.py

# 限制处理数量
python scripts/process_pdfs.py --limit 50
```

### 4. AI分析和筛选

```bash
# 分析论文相关性
python scripts/analyze_papers.py

# 使用特定的LLM提供商
python scripts/analyze_papers.py --provider anthropic

# 限制处理数量
python scripts/analyze_papers.py --limit 20
```

## 数据库状态

论文在处理流程中的状态变化：

1. `pending` - 刚收集的标题，等待获取详细信息
2. `downloaded` - 已获取详细信息，等待下载PDF
3. `processed` - PDF已下载并转换为文本
4. `analyzed` - 已完成AI分析

## 配置说明

### API密钥

在 `.env` 文件中配置：

- `OPENAI_API_KEY`: OpenAI API密钥
- `ANTHROPIC_API_KEY`: Anthropic API密钥
- `DEFAULT_LLM_PROVIDER`: 默认使用的LLM提供商

### 相关性标签

在 `config.py` 中的 `RELEVANCE_TAGS` 列表中配置需要筛选的研究主题。

## 注意事项

- 确保有足够的磁盘空间存储PDF文件
- API调用可能产生费用，建议先小批量测试
- 某些会议网站可能需要额外的访问权限
- OCR处理较慢，建议分批处理

## 依赖库

主要依赖：

- `requests`: HTTP请求
- `PyMuPDF/pdfplumber`: PDF处理
- `openai/anthropic`: LLM API
- `beautifulsoup4`: 网页解析
- `tqdm`: 进度显示

详见 `requirements.txt`

## 许可证

MIT License

