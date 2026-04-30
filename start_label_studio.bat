@echo off
echo ================================
echo Label Studio 启动脚本
echo ================================
echo.

REM 设置正确的 Python 版本（避免 Python 3.14 兼容性问题）
set PYTHONPATH=
set PYTHONHOME=

echo 1. 检查 Python 版本...
python --version

echo.
echo 2. 复制预构建的静态文件到正确位置...
xcopy /e /i /y label_studio\static_build\* label_studio\core\static\

echo.
echo 3. 收集静态文件...
python label_studio/manage.py collectstatic --noinput

echo.
echo 4. 运行数据库迁移...
python label_studio/manage.py migrate

echo.
echo 5. 启动服务器...
python label_studio/manage.py runserver 0.0.0.0:8080

pause
