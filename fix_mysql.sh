#!/bin/bash
echo "修复MySQL访问权限"
echo "=================="
echo ""

echo "尝试使用sudo登录MySQL..."
sudo mysql -u root << 'EOF'
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '';
FLUSH PRIVILEGES;
SELECT user, host, plugin FROM mysql.user WHERE user='root';
EOF

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ MySQL root密码已设置为空"
    echo ""
    echo "现在初始化数据库..."
    mysql -u root < init_db.sql
    
    if [ $? -eq 0 ]; then
        echo "✓ 数据库初始化成功"
        echo ""
        echo "迁移数据..."
        venv/bin/python migrate_to_mysql.py
        echo ""
        echo "测试连接..."
        venv/bin/python test_db.py
        echo ""
        echo "重启服务..."
        systemctl restart autologin
        systemctl status autologin --no-pager
        echo ""
        echo "✓ 完成！"
    else
        echo "✗ 数据库初始化失败"
    fi
else
    echo "✗ 无法访问MySQL"
    echo ""
    echo "请手动运行："
    echo "sudo mysql -u root"
    echo "然后执行："
    echo "ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '';"
    echo "FLUSH PRIVILEGES;"
fi
