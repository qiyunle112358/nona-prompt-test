# 图片Prompt测试工具使用说明

## 功能概述

这个工具可以：
1. 从不同领域随机收集2024年的论文
2. 下载论文PDF
3. **智能筛选流程图/演示图**（排除实验图表和素材图）
4. 使用OpenRouter API（google/gemini-2.5-flash）分析图片，生成5个不同的prompt
5. 使用OpenRouter API（google/gemini-3-pro-image-preview）根据每个prompt生成图片
6. 将原图、prompt和生成图片整理到结构化文件夹中

## 使用前准备

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置OpenRouter API Key

在 `.env` 文件中配置，或直接在命令行参数中提供。

## 使用方法

### 基本用法

```bash
python scripts/image_prompt_test.py \
    --num-images 100 \
    --year 2024 \
    --num-prompts 5 \
    --openrouter-api-key YOUR_OPENROUTER_API_KEY \
    --output-dir data/prompt_test
```

### 参数说明

- `--num-images`: 要收集的流程图数量（默认100）
- `--year`: 论文年份（默认2024）
- `--num-prompts`: 每个原图生成的prompt数量（默认5）
- `--openrouter-api-key`: **必需**，OpenRouter API密钥
- `--output-dir`: 输出目录（默认 `data/prompt_test`）
- `--max-papers`: 最多处理的论文数量（默认500，用于确保能找到足够的流程图）

### 完整示例

```bash
# 收集100张流程图，每张生成5个prompt和5张图片
python scripts/image_prompt_test.py \
    --num-images 100 \
    --year 2024 \
    --num-prompts 5 \
    --openrouter-api-key sk-or-v1-your-key-here \
    --output-dir data/prompt_test_results \
    --max-papers 500
```

## 工作流程

脚本会自动执行以下步骤：

1. **收集论文标题**
   - 从12个不同arXiv分类随机收集论文
   - 包括：计算机视觉、NLP、机器学习、AI、机器人学、图形学、光学、医学物理、生物学、数学、统计学等

2. **获取论文详细信息**
   - 获取arXiv ID、PDF下载链接、作者、摘要等

3. **下载PDF**
   - 下载所有论文的PDF文件

4. **智能提取流程图**
   - 从每篇论文的PDF中提取所有图片
   - **智能筛选**：只保留流程图/演示图
   - **排除**：实验图表、素材图、照片等
   - 如果论文中没有流程图，自动跳过并删除该论文记录
   - 继续处理下一篇论文，直到收集到指定数量的流程图

5. **生成Prompt**
   - 使用 `google/gemini-2.5-flash` 分析每张流程图
   - 为每张图生成指定数量的prompt（默认5个）

6. **生成图片**
   - 使用 `google/gemini-3-pro-image-preview` 根据每个prompt生成图片
   - 使用预设的科学插图专家prompt作为前置提示

7. **整理输出**
   - 将每张原图及其对应的prompt和生成图片整理到独立文件夹
   - 生成总结报告

## 输出结构

```
data/prompt_test/
├── original_images/          # 提取的原图（按论文ID组织）
│   ├── 2301.12345/
│   │   └── flowchart_page_0_img_0.png
│   └── 2302.23456/
│       └── flowchart_page_1_img_2.png
├── generated_images/         # 生成的图片（按论文ID组织）
│   ├── 2301.12345/
│   │   ├── prompt_1.png
│   │   ├── prompt_2.png
│   │   └── ...
│   └── 2302.23456/
│       └── ...
├── results/                  # 整理后的结果（方便对比）
│   ├── 2301.12345/
│   │   ├── original.png      # 原图
│   │   ├── generated_1.png   # 第1个prompt生成的图片
│   │   ├── generated_2.png   # 第2个prompt生成的图片
│   │   ├── generated_3.png   # 第3个prompt生成的图片
│   │   ├── generated_4.png   # 第4个prompt生成的图片
│   │   ├── generated_5.png   # 第5个prompt生成的图片
│   │   └── prompts.txt       # 所有prompt文本
│   └── 2302.23456/
│       └── ...
└── summary.txt               # 总结报告
```

## 流程图筛选逻辑

程序使用启发式方法智能识别流程图/演示图：

**包含的图片类型：**
- ✅ 流程图（包含箭头、框、连接线）
- ✅ 架构图（系统结构、组件关系）
- ✅ 演示图（概念可视化、方法示意图）
- ✅ 科学图表（结构化的技术图表）

**排除的图片类型：**
- ❌ 实验图表（包含大量数据点、曲线图）
- ❌ 素材图（照片、简单图标）
- ❌ 过于复杂或简单的图片

**判断标准：**
- 颜色种类相对较少（流程图通常颜色简单）
- 有较多白色/浅色背景
- 长宽比不会太极端
- 尺寸适中（不会太小或太大）

## 注意事项

1. **API费用**: 处理100张图片需要调用大量API，注意控制成本
2. **处理时间**: 完整流程可能需要数小时，建议先用小数量测试
3. **存储空间**: 确保有足够的磁盘空间（每张图片约几MB）
4. **网络连接**: 需要稳定的网络连接下载论文和调用API
5. **论文筛选**: 如果某篇论文没有流程图，会自动跳过并继续处理下一篇

## 故障排除

### 问题1: 找不到足够的流程图

**原因**: 某些领域的论文可能流程图较少

**解决**:
- 增加 `--max-papers` 参数，处理更多论文
- 检查日志，了解哪些论文被跳过了

### 问题2: API调用失败

**原因**: API密钥错误、网络问题、API限制

**解决**:
- 检查API密钥是否正确
- 检查网络连接
- 查看日志了解具体错误
- 可能需要等待API限制重置

### 问题3: 生成的图片质量不佳

**原因**: Prompt不够详细或模型限制

**解决**:
- 程序会自动生成多个不同的prompt
- 可以手动查看 `prompts.txt` 文件，了解生成的prompt
- 后续可以基于这些prompt进行优化

## 输出文件说明

### prompts.txt

每张原图对应一个 `prompts.txt` 文件，包含：
- 论文信息（标题、来源、arXiv ID）
- 所有生成的prompt（编号列表）

### summary.txt

总结报告包含：
- 生成时间
- 统计信息（目标数量、实际数量、处理论文数）
- 每张图片的简要信息

## 后续使用

1. **查看结果**: 进入 `results/<arxiv_id>/` 目录
2. **对比效果**: 打开原图和生成的5张图片进行对比
3. **分析prompt**: 查看 `prompts.txt` 了解哪些prompt效果更好
4. **优化流程**: 基于结果优化prompt生成策略

## 快速测试

先用小数量测试：

```bash
python scripts/image_prompt_test.py \
    --num-images 5 \
    --year 2024 \
    --num-prompts 3 \
    --openrouter-api-key YOUR_KEY \
    --max-papers 20
```

这样可以快速验证流程是否正常。

---

**开始测试吧！** 🚀
