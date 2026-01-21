#!/bin/bash
# 查看图片Prompt测试脚本的运行状态

echo "=========================================="
echo "图片Prompt测试 - 运行状态检查"
echo "=========================================="
echo ""

# 1. 检查进程是否运行
echo "【1. 进程状态】"
if ps aux | grep -E "image_prompt_test" | grep -v grep > /dev/null; then
    echo "✓ 进程正在运行"
    ps aux | grep -E "image_prompt_test" | grep -v grep | awk '{print "  进程ID: " $2 " | CPU: " $3 "% | 内存: " $4 "%"}'
else
    echo "✗ 进程未运行"
fi
echo ""

# 2. 检查已处理的图片数
echo "【2. 处理进度】"
RESULT_COUNT=$(find data/prompt_test/results -name "original.png" -type f 2>/dev/null | wc -l | tr -d ' ')
echo "已处理原图: $RESULT_COUNT / 76 张"
PROGRESS=$(cat data/prompt_test/.progress 2>/dev/null | wc -l | tr -d ' ')
if [ -n "$PROGRESS" ] && [ "$PROGRESS" -gt 0 ]; then
    echo "进度文件记录: $PROGRESS 篇论文"
fi
echo ""

# 3. 查找最新日志文件
echo "【3. 最新日志文件】"
# 优先使用 /tmp/image_prompt_test.log
if [ -f "/tmp/image_prompt_test.log" ]; then
    LATEST_LOG="/tmp/image_prompt_test.log"
    echo "日志文件: $LATEST_LOG"
    echo "文件大小: $(ls -lh "$LATEST_LOG" | awk '{print $5}')"
    echo "最后修改: $(ls -l "$LATEST_LOG" | awk '{print $6, $7, $8}')"
else
    LATEST_LOG=$(ls -t ~/.cursor/projects/Users-qiyunle-Desktop-MyCode-Projects-nona/terminals/*.txt 2>/dev/null | head -1)
    if [ -n "$LATEST_LOG" ]; then
        echo "日志文件: $LATEST_LOG"
        echo "文件大小: $(ls -lh "$LATEST_LOG" | awk '{print $5}')"
        echo "最后修改: $(ls -l "$LATEST_LOG" | awk '{print $6, $7, $8}')"
    else
        echo "未找到日志文件"
    fi
fi
echo ""

# 4. 显示最新日志（最后20行）
echo "【4. 最新日志（最后20行）】"
if [ -n "$LATEST_LOG" ] && [ -f "$LATEST_LOG" ]; then
    tail -20 "$LATEST_LOG" 2>/dev/null | tail -15
else
    echo "无法读取日志"
fi
echo ""

# 5. 检查最近的活动
echo "【5. 最近活动】"
if [ -n "$LATEST_LOG" ] && [ -f "$LATEST_LOG" ]; then
    echo "最近处理:"
    tail -100 "$LATEST_LOG" 2>/dev/null | grep -E "处理论文|成功处理|提取图片|生成prompt" | tail -5
    echo ""
    echo "最近错误:"
    tail -100 "$LATEST_LOG" 2>/dev/null | grep -i "error\|failed\|失败" | tail -3
fi
echo ""

# 6. 检查输出目录
echo "【6. 输出目录状态】"
if [ -d "data/prompt_test/results" ]; then
    RESULT_DIRS=$(ls -d data/prompt_test/results/*/ 2>/dev/null | wc -l | tr -d ' ')
    echo "结果文件夹数: $RESULT_DIRS"
    CURATED_DIRS=$(ls -d data/prompt_test/curated_results/*/ 2>/dev/null | wc -l | tr -d ' ')
    if [ -n "$CURATED_DIRS" ] && [ "$CURATED_DIRS" -gt 0 ]; then
        echo "精选结果文件夹数: $CURATED_DIRS"
    fi
else
    echo "结果目录不存在"
fi
echo ""

echo "=========================================="
echo "实时监控命令:"
if [ -f "/tmp/image_prompt_test.log" ]; then
    echo "1. 实时监控脚本: bash 实时监控.sh"
    echo "2. 实时日志: tail -f /tmp/image_prompt_test.log"
else
    echo "tail -f $LATEST_LOG"
fi
echo "=========================================="
