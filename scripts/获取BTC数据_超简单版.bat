@echo off
chcp 65001 >nul
title 获取BTC最新数据
color 0A

echo ========================================
echo   🚀 获取BTC最新数据
echo ========================================
echo.
echo 正在启动Python脚本...
echo.

python "%~dp0get_btc_ultra_simple.py"

if errorlevel 1 (
    echo.
    echo ========================================
    echo   ❌ 运行失败
    echo ========================================
    echo.
    echo 可能的原因：
    echo   1. 未安装Python
    echo   2. 未安装requests库
    echo.
    echo 解决方法：
    echo   1. 安装Python: https://www.python.org/downloads/
    echo   2. 安装requests: pip install requests
    echo.
)

echo.
echo ========================================
echo   按任意键关闭
echo ========================================
pause
