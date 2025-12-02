# 测试说明

本目录包含所有模块的单元测试，测试代码与运行代码完全分离。

## 测试结构

```
tests/
├── README.md                    # 本文件
├── test_config.py              # 测试配置
├── test_collectors.py          # 测试论文收集模块
├── test_fetchers.py            # 测试信息获取模块
├── test_processors.py          # 测试PDF处理模块
├── test_analyzers.py           # 测试AI分析模块
├── test_database.py            # 测试数据库模块
├── run_all_tests.py            # 运行所有测试
└── sample_data/                # 测试用的样本数据
    ├── sample_titles.json      # 样本标题列表
    ├── sample_paper.pdf        # 样本PDF
    └── sample_paper.txt        # 样本文本
```

## 测试策略

### 1. 模块1：论文收集器测试
- **测试方式**: 每个来源收集1-3篇论文
- **验证点**: 返回格式、数据完整性
- **时间**: 约1-2分钟/来源

### 2. 模块2：信息获取测试
- **测试方式**: 使用预定义的3个论文标题
- **验证点**: arXiv ID、PDF URL、作者、摘要
- **时间**: 约30秒

### 3. 模块3：PDF处理测试
- **测试方式**: 使用1个样本PDF
- **验证点**: 下载成功、文本提取、格式正确
- **时间**: 约10秒

### 4. 模块4：AI分析测试
- **测试方式**: 使用1个样本文本（约500字）
- **验证点**: 分析结果格式、分数范围、总结质量
- **时间**: 约10-20秒
- **注意**: 会产生少量API费用（约$0.01）

## 运行测试

### 运行单个模块测试

```bash
# 测试配置
python tests/test_config.py

# 测试数据库
python tests/test_database.py

# 测试收集器（只测试arXiv，不会测试所有会议）
python tests/test_collectors.py

# 测试信息获取
python tests/test_fetchers.py

# 测试PDF处理
python tests/test_processors.py

# 测试AI分析（会产生少量API费用）
python tests/test_analyzers.py
```

### 运行所有测试

```bash
python tests/run_all_tests.py
```

### 只运行不需要API的测试

```bash
python tests/run_all_tests.py --skip-api
```

## 测试数据

所有测试使用的是真实但最小化的数据：
- 论文收集：最多3篇
- 信息获取：3个已知论文
- PDF处理：1个样本PDF（约2-3页）
- AI分析：1个短文本（约500字）

## 预期结果

每个测试会输出：
- ✓ 通过的测试项
- ✗ 失败的测试项
- 详细的错误信息（如果有）
- 执行时间

## 注意事项

1. **API密钥**: AI分析测试需要配置.env文件
2. **网络连接**: 收集器和获取器需要网络连接
3. **磁盘空间**: 测试会在tests/temp/目录创建临时文件
4. **API费用**: AI分析测试约花费$0.01-0.02

