#!/bin/bash

# 缠论多智能体分析系统 - 启动脚本

echo "=========================================="
echo "缠论多智能体分析系统"
echo "=========================================="
echo ""

# 检查 Python 环境
if ! command -v python &> /dev/null; then
    echo "错误: 未找到 Python 环境"
    exit 1
fi

echo "Python 环境: $(python --version)"
echo ""

# 检查依赖
echo "检查依赖包..."
uv pip list | grep -E "langchain|langgraph|requests|psutil|pandas" > /dev/null
if [ $? -eq 0 ]; then
    echo "✓ 依赖包已安装"
else
    echo "✗ 依赖包缺失，请运行: uv sync"
    exit 1
fi

echo ""
echo "=========================================="
echo "开始运行测试"
echo "=========================================="
echo ""

# 运行测试
python test_chanlun.py

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "测试完成"
    echo "=========================================="
    exit 0
else
    echo ""
    echo "=========================================="
    echo "测试失败"
    echo "=========================================="
    exit 1
fi
