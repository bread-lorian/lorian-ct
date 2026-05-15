@echo off
chcp 65001 >nul

echo.
echo ========================================
echo   lorian-ct AI错题本
echo ========================================
echo.

:: [1] 检查虚拟环境
if not exist ".venv\" (
    echo [!] 未找到虚拟环境，正在创建...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [✗] 创建虚拟环境失败，请确认已安装 Python 3
        pause
        exit /b 1
    )
    echo [✓] 虚拟环境创建完成
) else (
    echo [✓] 虚拟环境已就绪
)

:: [2] 检查依赖
.venv\Scripts\python -c "import flask" >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] 正在安装依赖...
    .venv\Scripts\python -m pip install flask openai python-dotenv -i https://pypi.tuna.tsinghua.edu.cn/simple
    if %errorlevel% neq 0 (
        .venv\Scripts\python -m pip install flask openai python-dotenv
    )
    if %errorlevel% neq 0 (
        echo [✗] 依赖安装失败，请检查网络连接
        pause
        exit /b 1
    )
    echo [✓] 依赖安装完成
) else (
    echo [✓] 依赖已就绪
)

:: [3] 检查必要目录
if not exist "templates" mkdir templates
if not exist "static" mkdir static

:: [4] 检查 .env
if not exist ".env" type nul > .env

echo.
echo 浏览器打开 http://localhost:5000
echo 按 Ctrl+C 停止服务
echo ========================================
echo.

.venv\Scripts\python app.py
pause
