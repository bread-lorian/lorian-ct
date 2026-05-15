#!/bin/bash
set -e

echo ""
echo "========================================"
echo "  lorian-ct AI错题本"
echo "========================================"
echo ""

# [1] 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo "[!] 未找到虚拟环境，正在创建..."
    python3 -m venv .venv || { echo "[✗] 创建虚拟环境失败，请确认已安装 Python 3"; exit 1; }
    echo "[✓] 虚拟环境创建完成"
else
    echo "[✓] 虚拟环境已就绪"
fi

# [2] 检查依赖
if ! .venv/bin/python -c "import flask" 2>/dev/null; then
    echo "[!] 正在安装依赖..."
    .venv/bin/python -m pip install flask openai python-dotenv -i https://pypi.tuna.tsinghua.edu.cn/simple 2>/dev/null || \
    .venv/bin/python -m pip install flask openai python-dotenv
    if [ $? -ne 0 ]; then
        echo "[✗] 依赖安装失败，请检查网络连接"
        exit 1
    fi
    echo "[✓] 依赖安装完成"
else
    echo "[✓] 依赖已就绪"
fi

# [3] 检查必要目录
mkdir -p templates static

# [4] 检查 .env
[ ! -f ".env" ] && touch .env

echo ""
echo "浏览器打开 http://localhost:5000"
echo "按 Ctrl+C 停止服务"
echo "========================================"
echo ""

.venv/bin/python app.py
