#!/bin/bash

echo "部署智能订阅系统"
echo "=================="

cd /root/minecraft_autologin

echo "1. 拉取最新代码..."
git pull

echo ""
echo "2. 更新数据库..."
mysql -u root -p minecraft_autologin < add_subscription_system.sql

echo ""
echo "3. 设置定时任务..."
./setup_cron.sh

echo ""
echo "4. 重启服务..."
pkill -f "python.*app.py"
sleep 2

source venv/bin/activate
nohup python app.py > app.log 2>&1 &

echo ""
echo "✓ 部署完成"
echo ""
echo "新功能:"
echo "- 智能账号选择（根据订阅天数匹配）"
echo "- 优先级系统（无续费 > 有续费 > 短期）"
echo "- 记住上次使用的账号"
echo "- 每天自动更新订阅天数"
echo ""
echo "测试步骤:"
echo "1. 导入带订阅信息的账号"
echo "2. 生成并验证卡密"
echo "3. 尝试登录，系统会自动选择最合适的账号"
echo "4. 查看日志确认选择逻辑"
