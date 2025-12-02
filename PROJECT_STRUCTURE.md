# 项目结构说明

## 📁 最终项目结构

```
nona/                              # 项目根目录
├── __init__.py                    # Python包初始化文件
├── config.py                      # 配置管理（API密钥、路径等）
├── database.py                    # SQLite数据库操作
├── requirements.txt               # 项目依赖
├── env.example                    # 环境变量示例
├── README.md                      # 项目说明文档
├── QUICKSTART.md                  # 快速开始指南
├── example_workflow.py            # 完整工作流示例
│
├── collectors/                    # 模块1：论文标题收集
│   ├── __init__.py
│   ├── arxiv.py                  # arXiv论文收集
│   ├── neurips.py                # NeurIPS会议论文
│   ├── iclr.py                   # ICLR会议论文
│   ├── icml.py                   # ICML会议论文
│   ├── corl.py                   # CoRL会议论文
│   ├── rss.py                    # RSS会议论文
│   ├── icra.py                   # ICRA会议论文
│   └── iros.py                   # IROS会议论文
│
├── fetchers/                      # 模块2：论文信息获取
│   ├── __init__.py
│   └── paper_fetcher.py          # 使用arXiv和OpenAlex API
│
├── processors/                    # 模块3：PDF处理和OCR
│   ├── __init__.py
│   ├── pdf_downloader.py         # PDF下载器
│   └── pdf_to_text.py            # PDF转文本
│
├── analyzers/                     # 模块4：AI分析和筛选
│   ├── __init__.py
│   └── relevance_filter.py       # LLM相关性分析
│
├── scripts/                       # 执行脚本
│   ├── __init__.py
│   ├── collect_titles.py         # 收集论文标题
│   ├── fetch_paper_info.py       # 获取论文信息
│   ├── process_pdfs.py           # 处理PDF文件
│   └── analyze_papers.py         # 分析论文相关性
│
├── tests/                         # 测试模块（与功能模块同层）
│   ├── README.md                 # 测试说明
│   ├── TESTING_GUIDE.md          # 详细测试指南
│   ├── test_config.py            # 配置模块测试
│   ├── test_database.py          # 数据库模块测试
│   ├── test_collectors.py        # 收集器测试
│   ├── test_fetchers.py          # 信息获取器测试
│   ├── test_processors.py        # PDF处理器测试
│   ├── test_analyzers.py         # AI分析器测试
│   ├── run_all_tests.py          # 运行所有测试
│   └── temp/                     # 测试临时文件（自动创建）
│
└── data/                          # 数据目录（自动创建）
    ├── papers.db                 # SQLite数据库
    ├── pdfs/                     # PDF文件存储
    └── texts/                    # 文本文件存储
```

## 🔄 结构变化说明

### 从旧结构迁移

**旧结构**（已删除）:
```
nona/
├── embodied_survey/    (或 nona/nona/)
│   └── [所有项目文件]
├── Reference/          (已删除)
└── tests/
```

**新结构**:
```
nona/
├── collectors/
├── fetchers/
├── processors/
├── analyzers/
├── scripts/
├── tests/              (与功能模块同层)
├── config.py
├── database.py
└── ...
```

### 主要变化

1. ✅ **扁平化结构**：移除了内层嵌套，所有模块直接在项目根目录下
2. ✅ **删除Reference**：删除了参考项目文件夹
3. ✅ **测试同层**：`tests/` 文件夹现在与其他功能模块（collectors、fetchers等）在同一层级
4. ✅ **更新导入**：所有导入路径已更新，不再使用 `embodied_survey.` 前缀

## 📝 导入语句变化

### 旧导入方式（已废弃）
```python
from embodied_survey.config import DB_PATH
from embodied_survey.database import Database
from embodied_survey import collectors
from embodied_survey.fetchers import fetch_paper_info
```

### 新导入方式（当前）
```python
from config import DB_PATH
from database import Database
import collectors
from fetchers import fetch_paper_info
```

## 🚀 使用方法

### 运行脚本
```bash
# 收集论文标题
python scripts/collect_titles.py --source arxiv --year 2025

# 获取论文信息
python scripts/fetch_paper_info.py --limit 100

# 处理PDF
python scripts/process_pdfs.py --limit 50

# 分析论文
python scripts/analyze_papers.py --limit 20
```

### 运行测试
```bash
# 运行所有测试
python tests/run_all_tests.py

# 运行单个测试
python tests/test_config.py
python tests/test_database.py
python tests/test_collectors.py
```

### 运行示例工作流
```bash
python example_workflow.py
```

## 📦 Python导入机制

由于项目采用扁平化结构，确保在运行脚本时：

1. **从项目根目录运行**：
   ```bash
   cd nona
   python scripts/collect_titles.py
   ```

2. **或者使用绝对路径**：
   ```bash
   python D:\C++\nona\scripts\collect_titles.py
   ```

3. **脚本会自动添加项目根目录到Python路径**：
   ```python
   sys.path.insert(0, str(Path(__file__).parent.parent))
   ```

## ⚙️ 配置文件位置

- **环境变量**：`nona/.env`（复制自 `env.example`）
- **数据目录**：`nona/data/`
- **PDF存储**：`nona/data/pdfs/`
- **文本存储**：`nona/data/texts/`
- **数据库**：`nona/data/papers.db`

## 📚 文档位置

- **项目说明**：`README.md`
- **快速开始**：`QUICKSTART.md`
- **项目结构**：`PROJECT_STRUCTURE.md`（本文件）
- **测试说明**：`tests/README.md`
- **测试指南**：`tests/TESTING_GUIDE.md`

## ✅ 验证结构正确性

运行配置测试以验证项目结构：

```bash
python tests/test_config.py
```

如果测试通过，说明项目结构配置正确！

## 🎯 下一步

1. 复制 `env.example` 到 `.env` 并配置API密钥
2. 运行测试验证功能：`python tests/run_all_tests.py --skip-api`
3. 开始使用：参考 `QUICKSTART.md`

