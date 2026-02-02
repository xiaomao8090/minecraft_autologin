#!/bin/bash

echo "本地测试启动脚本"
echo "=================="
echo ""

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
echo "安装依赖..."
pip install -q flask flask-cors flask-socketio pymysql cryptography python-dotenv

# 复制配置文件
if [ ! -f ".env" ]; then
    echo "复制配置文件..."
    cp .env.local .env
    echo "请编辑 .env 文件，设置MySQL密码"
    echo ""
fi

# 提示数据库设置
echo "请确保MySQL已安装并运行"
echo "创建测试数据库："
echo "  mysql -u root -p"
echo "  CREATE DATABASE minecraft_autologin_test;"
echo "  source init_db.sql;"
echo ""

# 启动应用
echo "启动应用..."
python app.py
