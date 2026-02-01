#!/bin/bash
echo "服务器MySQL设置"
echo "================"
echo ""
read -sp "请输入MySQL root密码: " MYSQL_PASSWORD
echo ""
echo ""
echo "初始化数据库..."
mysql -u root -p"$MYSQL_PASSWORD" < init_db.sql
if [ $? -eq 0 ]; then
    echo "✓ 数据库初始化成功"
else
    echo "✗ 数据库初始化失败"
    exit 1
fi
echo ""
echo "更新.env文件..."
sed -i "s/^DB_PASSWORD=.*/DB_PASSWORD=$MYSQL_PASSWORD/" .env
echo "✓ .env已更新"
echo ""
echo "迁移数据..."
venv/bin/python migrate_to_mysql.py
echo ""
echo "测试数据库连接..."
venv/bin/python test_db.py
echo ""
echo "重启服务..."
systemctl restart autologin
systemctl status autologin --no-pager
echo ""
echo "完成！"
