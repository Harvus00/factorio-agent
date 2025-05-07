#!/bin/bash

if ! conda env list | grep -q "factorio_agent_env"; then
    echo "Creating new conda environment factorio_agent_env..."
    conda create -n factorio_agent_env python=3.11
    # Activate conda environment
    conda activate factorio_agent_env

    # Install dependencies
    pip install -r requirements.txt
else
    echo "Conda environment factorio_agent_env already exists"
fi

# Get current directory
CURRENT_DIR=$(pwd)
FACTORIO_MOD_DIR="$HOME/Library/Application Support/factorio/mods/sup-MQTT"

# 启动两个 Python 脚本
osascript -e "tell application \"Terminal\" to do script \"cd '$CURRENT_DIR' && conda activate factorio_agent_env && python mqtt_subscriber.py\""
osascript -e "tell application \"Terminal\" to do script \"cd '$FACTORIO_MOD_DIR' && conda activate factorio_agent_env && python publisher.py\""