#!/bin/bash

echo "部署用户管理功能"
echo "=================="

cd /root/minecraft_autologin

echo "1. 拉取最新代码..."
git pull

echo ""
echo "2. 更新数据库..."
mysql -u root -p minecraft_autologin < add_user_management.sql

echo ""
echo "3. 重启服务..."
pkill -f "python.*app.py"
sleep 2

source venv/bin/activate
nohup python app.py > app.log 2>&1 &

echo ""
echo "✓ 部署完成"
echo ""
echo "新功能:"
echo "- 用户管理页面（查看卡密使用情况）"
echo "- 显示剩余天数、成功/失败次数、IP地址"
echo "- 封禁/解封用户功能"
echo "- 自动统计使用次数"
