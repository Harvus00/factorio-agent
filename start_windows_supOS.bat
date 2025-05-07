@echo off

REM 检查环境是否存在
conda env list | findstr /C:"factorio_mqtt" >nul
if errorlevel 1 (
    echo 创建新的 conda 环境 factorio_mqtt...
    call conda create -y -n factorio_mqtt python=3.11
) else (
    echo 环境 factorio_mqtt 已存在
)

REM 激活环境
call conda activate factorio_mqtt

REM 安装依赖
pip install -r requirements.txt

REM 获取当前目录
set CURRENT_DIR=%CD%
set FACTORIO_MOD_DIR=%appdata%\Factorio\mods\sup-MQTT

REM 启动两个 Python 脚本
start cmd /k "cd /d %CURRENT_DIR% && conda activate factorio_mqtt && python mqtt_subscriber.py"
start cmd /k "cd /d %FACTORIO_MOD_DIR% && conda activate factorio_mqtt && python publisher.py" 