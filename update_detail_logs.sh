#!/bin/bash

echo "更新详细日志功能"
echo "=================="

cd /root/minecraft_autologin

echo "1. 拉取最新代码..."
git pull

echo ""
echo "2. 重启服务..."
pkill -f "python.*app.py"
sleep 2

source venv/bin/activate
nohup python app.py > app.log 2>&1 &

echo ""
echo "✓ 更新完成"
echo "✓ 服务已重启"
echo ""
echo "测试步骤:"
echo "1. 访问管理后台，点击'日志'菜单"
echo "2. 尝试登录一次，查看日志记录"
echo "3. 点击'详细'按钮查看完整日志"
echo ""
echo "如果还有问题，查看日志:"
echo "  tail -f app.log"
