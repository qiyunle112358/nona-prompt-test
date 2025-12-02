# 快速开始指南

## 1. 安装依赖

```bash
cd nona
pip install -r requirements.txt
```

## 2. 配置环境变量

复制环境变量示例文件并填入你的API密钥：

```bash
cp env.example .env
```

编辑 `.env` 文件：

```bash
# OpenAI API配置
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_BASE_URL=https://api.openai.com/v1
DEFAULT_OPENAI_MODEL=gpt-4o-mini

# Anthropic API配置（可选）
ANTHROPIC_API_KEY=your-anthropic-api-key-here
DEFAULT_ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# 选择默认的LLM提供商
DEFAULT_LLM_PROVIDER=openai

# 日志级别
LOG_LEVEL=INFO
```

## 3. 使用流程

### 第一步：收集论文标题

```bash
# 收集arXiv 2025年的cs.RO论文
python scripts/collect_titles.py --source arxiv --year 2025

# 收集NeurIPS 2024的论文
python scripts/collect_titles.py --source neurips --year 2024

# 收集所有来源（推荐先小规模测试）
python scripts/collect_titles.py --all --year 2024
```

### 第二步：获取论文详细信息

```bash
# 获取前100篇论文的详细信息
python scripts/fetch_paper_info.py --limit 100

# 获取所有待处理论文的信息
python scripts/fetch_paper_info.py
```

### 第三步：下载和处理PDF

```bash
# 下载并转换前50篇论文
python scripts/process_pdfs.py --limit 50

# 只下载PDF，不转换文本
python scripts/process_pdfs.py --skip-convert

# 只转换文本，不下载PDF（假设PDF已存在）
python scripts/process_pdfs.py --skip-download
```

### 第四步：AI分析和筛选

```bash
# 分析前20篇论文（使用OpenAI）
python scripts/analyze_papers.py --limit 20 --provider openai

# 分析所有已处理的论文（使用Anthropic）
python scripts/analyze_papers.py --provider anthropic

# 设置最小相关性分数阈值
python scripts/analyze_papers.py --min-score 0.7
```

## 4. 查看结果

所有数据都存储在 SQLite 数据库中（`data/papers.db`）。

你可以使用任何 SQLite 客户端查看，或者使用 Python：

```python
from database import Database
from config import DB_PATH

db = Database(str(DB_PATH))

# 获取统计信息
stats = db.get_statistics()
print(f"总论文数: {stats['total_papers']}")
print(f"已分析: {stats['analyzed_papers']}")
print(f"相关论文: {stats['relevant_papers']}")

# 获取相关论文（分数 >= 0.7）
relevant_papers = db.get_relevant_papers(min_score=0.7)

for paper in relevant_papers[:10]:
    print(f"\n{paper['title']}")
    print(f"分数: {paper.get('relevance_score'):.2f}")
    print(f"理由: {paper.get('reasoning')}")
    print(f"总结: {paper.get('summary')[:200]}...")
```

## 5. 注意事项

1. **API费用**: AI分析会调用大语言模型API，请注意控制使用量，建议先小批量测试
2. **网络请求**: 某些会议网站可能需要特殊权限或可能临时不可访问
3. **磁盘空间**: PDF文件会占用大量空间，请确保有足够的存储空间
4. **处理时间**: PDF转文本和AI分析都比较耗时，建议分批处理

## 6. 自定义配置

### 修改相关性标签

编辑 `config.py` 中的 `RELEVANCE_TAGS`：

```python
# 在 config.py 中修改
RELEVANCE_TAGS = [
    "机器人",
    "具身智能",
    "灵巧手",
    "抓取",
    "世界模型",
    "物理智能",
    # 添加你自己的标签
]
```

### 修改会议年份映射

编辑 `collectors/` 目录下对应会议的 `.py` 文件，更新 `volume_mapping` 字典。

## 7. 故障排除

### 问题1：无法收集某个会议的论文

**解决方案**: 会议网站结构可能已变化，需要手动更新对应的收集器代码。建议访问会议官网手动获取论文列表。

### 问题2：API调用失败

**解决方案**: 
- 检查 `.env` 文件中的API密钥是否正确
- 检查网络连接
- 检查API额度是否充足

### 问题3：PDF下载失败

**解决方案**:
- 某些PDF可能不公开可访问
- 检查网络连接
- 增加重试次数

### 问题4：文本转换质量不佳

**解决方案**:
- PyMuPDF对某些PDF格式的支持有限
- 可以尝试使用其他PDF处理库（pdfplumber）
- 对于扫描版PDF，需要使用OCR功能

## 8. 高级用法

### 批量处理工作流

创建一个shell脚本一次性运行所有步骤：

```bash
#!/bin/bash

# workflow.sh

echo "第一步：收集论文标题"
python scripts/collect_titles.py --source arxiv --year 2025

echo "第二步：获取论文信息"
python scripts/fetch_paper_info.py --limit 100

echo "第三步：下载和处理PDF"
python scripts/process_pdfs.py --limit 50

echo "第四步：AI分析"
python scripts/analyze_papers.py --limit 20 --provider openai

echo "完成！"
```

运行：

```bash
chmod +x workflow.sh
./workflow.sh
```

## 9. 导出结果

你可以编写简单的Python脚本导出相关论文到CSV或JSON：

```python
import json
from database import Database
from config import DB_PATH

db = Database(str(DB_PATH))
relevant_papers = db.get_relevant_papers(min_score=0.7)

# 导出为JSON
with open('relevant_papers.json', 'w', encoding='utf-8') as f:
    json.dump(relevant_papers, f, ensure_ascii=False, indent=2)

print(f"已导出 {len(relevant_papers)} 篇相关论文")
```

