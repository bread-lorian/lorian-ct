@echo off
chcp 65001 >nul
echo.
echo ========================================
echo   lorian-ct AI错题本 - 一键安装
echo ========================================
echo.

echo [1/3] 升级 pip ...
python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
echo.

echo [2/3] 安装依赖 ...
pip install flask openai python-dotenv -i https://pypi.tuna.tsinghua.edu.cn/simple
echo.

echo [3/3] 检查模板文件夹 ...
if not exist "templates" mkdir templates
echo.

echo ========================================
echo   安装完成！
echo   请创建 .env 文件，然后运行 start.bat
echo ========================================
echo.
pause
