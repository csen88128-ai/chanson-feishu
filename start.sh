#!/bin/bash

# 缠论多智能体分析系统 - 启动脚本

echo "🚀" 60
echo "  缠论多智能体分析系统 v7.0"
echo "🚀" 60
echo ""

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo "❌ 虚拟环境不存在，请先运行: uv sync"
    exit 1
fi

# 激活虚拟环境
echo "📦 激活虚拟环境..."
source .venv/bin/activate

# 显示Python版本
echo "🐍 Python 版本:"
python --version
echo ""

# 显示已安装的主要包
echo "📚 主要依赖包:"
pip list | grep -E "(langchain|langgraph|fastapi|uvicorn)" || echo "  （未找到主要包）"
echo ""

# 运行部署验证
echo "🔍 运行部署验证..."
python verify_deployment.py
echo ""

# 询问是否启动系统
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  部署验证完成！"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "可用命令:"
echo "  1. python verify_deployment.py  - 部署验证"
echo "  2. python src/main.py           - 启动系统"
echo "  3. python test_algorithms.py    - 测试算法"
echo "  4. python test_deployment.py    - 测试部署"
echo ""
echo "文档:"
echo "  - CHANLUN_README.md             - 系统说明"
echo "  - DEPLOYMENT_SUCCESS.md         - 部署报告"
echo "  - docs/                         - 详细文档"
echo ""
