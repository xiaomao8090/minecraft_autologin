#!/bin/bash
echo "宝塔MySQL设置"
echo "============="
echo ""

# 尝试从宝塔配置读取密码
if [ -f /www/server/panel/default.pl ]; then
    echo "检测到宝塔面板"
    BT_MYSQL_PASSWORD=$(grep -oP "(?<=mysql_root\s').*(?=')" /www/server/panel/default.pl 2>/dev/null)
    if [ -n "$BT_MYSQL_PASSWORD" ]; then
        echo "找到宝塔MySQL密码"
        MYSQL_PASSWORD="$BT_MYSQL_PASSWORD"
    fi
fi

# 如果没找到，手动输入
if [ -z "$MYSQL_PASSWORD" ]; then
    echo "请输入MySQL root密码（在宝塔面板-数据库中查看）："
    read -sp "密码: " MYSQL_PASSWORD
    echo ""
fi

echo ""
echo "测试MySQL连接..."
mysql -u root -p"$MYSQL_PASSWORD" -e "SELECT 1;" > /dev/null 2>&1

if [ $? -ne 0 ]; then
    echo "✗ MySQL密码错误"
    echo ""
    echo "请在宝塔面板查看MySQL root密码："
    echo "1. 登录宝塔面板"
    echo "2. 数据库 -> root密码"
    echo ""
    echo "然后重新运行此脚本"
    exit 1
fi

echo "✓ MySQL连接成功"
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

if [ $? -eq 0 ]; then
    echo ""
    echo "重启服务..."
    systemctl restart autologin
    sleep 2
    systemctl status autologin --no-pager
    echo ""
    echo "=========================================="
    echo "✓ 部署完成！"
    echo "=========================================="
    echo ""
    echo "访问地址："
    echo "- http://154.37.221.205:5001"
    echo "- https://login.waka.rest"
    echo ""
else
    echo "✗ 数据库连接测试失败"
    exit 1
fi
