@echo off
chcp 65001 >nul
echo.
echo ========================================
echo   lorian-ct AI错题本 - 一键安装
echo ========================================
echo.


echo [1/5] 创建虚拟环境...
python -m venv .venv
echo.

echo [2/5] 激活虚拟环境...
call .venv\Scripts\activate.bat
echo.


echo [3/5] 安装依赖 ...
.venv\Scripts\python -m pip install flask openai python-dotenv -i https://pypi.tuna.tsinghua.edu.cn/simple
if %errorlevel% neq 0 (
    echo 依赖安装失败，请检查网络连接后重试
    pause
    exit /b 1
)
echo.

echo [4/5] 创建.env文件 ...
echo > .env
if %errorlevel% neq 0 (
    echo .env文件创建失败
    pause
    exit /b 1
)

echo [5/5] 检查模板文件夹 ...
if not exist "templates" mkdir templates
echo.

echo ========================================
echo   安装完成！

echo   请运行start.bat
echo ========================================
echo.
pause
