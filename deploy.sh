#!/bin/bash

# Minecraft Auto Login 部署脚本
# 使用方法: ./deploy.sh YOUR_GITHUB_TOKEN

if [ -z "$1" ]; then
    echo "错误: 需要提供GitHub Token"
    echo "使用方法: ./deploy.sh YOUR_GITHUB_TOKEN"
    echo ""
    echo "获取Token: https://github.com/settings/tokens"
    echo "需要勾选 'repo' 权限"
    exit 1
fi

TOKEN=$1
REPO_URL="https://${TOKEN}@github.com/xiaomao8090/minecraft_autologin.git"

echo "=========================================="
echo "开始部署 Minecraft Auto Login"
echo "=========================================="

# 1. 检查是否已存在
if [ -d "minecraft_autologin" ]; then
    echo "[1/8] 检测到已存在项目，更新代码..."
    cd minecraft_autologin
    git pull
    cd ..
else
    echo "[1/8] 克隆仓库..."
    git clone $REPO_URL
fi

cd minecraft_autologin

# 2. 创建虚拟环境
echo "[2/8] 创建Python虚拟环境..."
python3 -m venv venv

# 3. 安装依赖
echo "[3/8] 安装依赖包..."
venv/bin/pip install -r requirements.txt

# 4. 创建必要目录
echo "[4/8] 创建目录结构..."
mkdir -p accounts/cookies
mkdir -p cookies
mkdir -p debug
mkdir -p tests/debug

# 5. 创建systemd服务
echo "[5/8] 创建systemd服务..."
cat > /etc/systemd/system/autologin.service << EOF
[Unit]
Description=Minecraft Auto Login Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/minecraft_autologin
ExecStart=/root/minecraft_autologin/venv/bin/python app.py
Restart=always
RestartSec=10
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=multi-user.target
EOF

# 6. 重载systemd
echo "[6/8] 重载systemd..."
systemctl daemon-reload

# 7. 启动服务
echo "[7/8] 启动服务..."
systemctl enable autologin
systemctl restart autologin

# 8. 检查状态
echo "[8/8] 检查服务状态..."
sleep 2
systemctl status autologin --no-pager

echo ""
echo "=========================================="
echo "部署完成！"
echo "=========================================="
echo ""
echo "服务管理命令:"
echo "  查看状态: systemctl status autologin"
echo "  查看日志: journalctl -u autologin -f"
echo "  重启服务: systemctl restart autologin"
echo "  停止服务: systemctl stop autologin"
echo ""
echo "访问地址:"
echo "  用户端: http://154.37.221.205:5001"
echo "  管理端: http://154.37.221.205:5001/admin"
echo ""
