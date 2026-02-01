#!/bin/bash

echo "=========================================="
echo "部署MySQL版本到服务器"
echo "=========================================="

SERVER="root@154.37.221.205"
PROJECT_DIR="/root/minecraft_autologin"

echo ""
echo "[1/6] 推送代码到GitHub..."
git add .
git commit -m "迁移到MySQL数据库"
git push

echo ""
echo "[2/6] 连接服务器并拉取代码..."
ssh $SERVER << 'EOF'
cd /root/minecraft_autologin
git pull
EOF

echo ""
echo "[3/6] 安装依赖..."
ssh $SERVER << 'EOF'
cd /root/minecraft_autologin
venv/bin/pip install -r requirements.txt
EOF

echo ""
echo "[4/6] 设置数据库..."
echo "请在服务器上手动运行: ./setup_mysql.sh"
echo "或者手动创建.env文件并初始化数据库"
read -p "按回车继续..."

echo ""
echo "[5/6] 测试数据库连接..."
ssh $SERVER << 'EOF'
cd /root/minecraft_autologin
venv/bin/python test_db.py
EOF

echo ""
echo "[6/6] 重启服务..."
ssh $SERVER << 'EOF'
systemctl restart autologin
systemctl status autologin --no-pager
EOF

echo ""
echo "=========================================="
echo "部署完成！"
echo "=========================================="
echo ""
echo "访问地址: http://154.37.221.205:5001"
echo "或: https://login.waka.rest"
echo ""
