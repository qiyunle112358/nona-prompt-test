#!/bin/bash
# 实时监控图片Prompt测试脚本的运行状态（精简版）

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

while true; do
    clear
    
    echo -e "${BLUE}=========================================="
    echo "图片Prompt测试 - 实时监控"
    echo "==========================================${NC}"
    echo ""
    
    # 1. 进程状态
    if ps aux | grep -E "image_prompt_test" | grep -v grep > /dev/null; then
        PID=$(ps aux | grep -E "image_prompt_test" | grep -v grep | awk '{print $2}')
        CPU=$(ps aux | grep -E "image_prompt_test" | grep -v grep | awk '{print $3}')
        MEM=$(ps aux | grep -E "image_prompt_test" | grep -v grep | awk '{print $4}')
        echo -e "${GREEN}✓ 运行中${NC} | PID: $PID | CPU: ${YELLOW}$CPU%${NC} | 内存: ${YELLOW}$MEM%${NC}"
    else
        echo -e "${RED}✗ 未运行${NC}"
    fi
    echo ""
    
    # 2. 处理进度
    RESULT_COUNT=$(find data/prompt_test/results -name "original.png" -type f 2>/dev/null | wc -l | tr -d ' ')
    TARGET=76
    PERCENTAGE=$((RESULT_COUNT * 100 / TARGET))
    echo -e "${GREEN}进度:${NC} ${GREEN}$RESULT_COUNT${NC}/${YELLOW}$TARGET${NC} 张图 (${PERCENTAGE}%)"
    echo ""
    
    # 3. 当前阶段和最新活动
    if [ -f "/tmp/image_prompt_test.log" ]; then
        # 当前阶段
        CURRENT_STAGE=$(tail -100 /tmp/image_prompt_test.log 2>/dev/null | grep -E "步骤[1-4]:" | tail -1 | sed 's/.*步骤\([0-9]\): \(.*\)/步骤\1: \2/' | sed 's/.*INFO - //')
        if [ -n "$CURRENT_STAGE" ]; then
            echo -e "${GREEN}阶段:${NC} $CURRENT_STAGE"
        fi
        
        # 最新处理的论文
        LATEST_PAPER=$(tail -30 /tmp/image_prompt_test.log 2>/dev/null | grep -E "处理论文:" | tail -1 | sed 's/.*处理论文: //' | sed 's/ (ID:.*//')
        if [ -n "$LATEST_PAPER" ]; then
            echo -e "${GREEN}当前:${NC} $LATEST_PAPER"
        fi
        
        # 最近成功处理
        LATEST_SUCCESS=$(tail -100 /tmp/image_prompt_test.log 2>/dev/null | grep -E "成功处理第" | tail -1 | sed 's/.*INFO - //')
        if [ -n "$LATEST_SUCCESS" ]; then
            echo -e "${GREEN}最新:${NC} $LATEST_SUCCESS"
        fi
    fi
    echo ""
    
    # 4. 时间戳
    echo -e "${BLUE}更新时间: $(date '+%H:%M:%S') | 按 Ctrl+C 退出${NC}"
    
    # 等待2秒后刷新
    sleep 2
done
