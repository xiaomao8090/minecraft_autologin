#!/bin/bash
# MSMC macOS 启动脚本

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_PATH="$SCRIPT_DIR/venv"

# 检查虚拟环境是否存在
if [ ! -d "$VENV_PATH" ]; then
    echo "创建虚拟环境..."
    python3 -m venv "$VENV_PATH"
    echo "安装依赖..."
    "$VENV_PATH/bin/pip" install -r "$SCRIPT_DIR/requirements.txt"
fi

# 激活虚拟环境并运行 MSMC
"$VENV_PATH/bin/python3" "$SCRIPT_DIR/MSMC.py"
