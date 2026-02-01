#!/bin/bash

echo "=========================================="
echo "MySQL数据库设置"
echo "=========================================="

# 检查是否已有.env文件
if [ -f .env ]; then
    echo "检测到现有.env文件"
    read -p "是否覆盖? (y/n): " overwrite
    if [ "$overwrite" != "y" ]; then
        echo "保留现有配置"
        exit 0
    fi
fi

# 生成加密密钥
echo ""
echo "生成加密密钥..."
ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

# 收集配置信息
echo ""
echo "请输入数据库配置:"
read -p "数据库主机 [localhost]: " DB_HOST
DB_HOST=${DB_HOST:-localhost}

read -p "数据库端口 [3306]: " DB_PORT
DB_PORT=${DB_PORT:-3306}

read -p "数据库用户 [root]: " DB_USER
DB_USER=${DB_USER:-root}

read -sp "数据库密码: " DB_PASSWORD
echo ""

read -p "数据库名称 [minecraft_autologin]: " DB_NAME
DB_NAME=${DB_NAME:-minecraft_autologin}

echo ""
read -p "管理员用户名 [xiaomao]: " ADMIN_USERNAME
ADMIN_USERNAME=${ADMIN_USERNAME:-xiaomao}

read -sp "管理员密码: " ADMIN_PASSWORD
echo ""

# 生成随机SECRET_KEY
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# 创建.env文件
cat > .env << EOF
# 管理员账号
ADMIN_USERNAME=$ADMIN_USERNAME
ADMIN_PASSWORD=$ADMIN_PASSWORD

# Session密钥
SECRET_KEY=$SECRET_KEY

# 数据库配置
DB_HOST=$DB_HOST
DB_PORT=$DB_PORT
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_NAME=$DB_NAME

# 加密密钥
ENCRYPTION_KEY=$ENCRYPTION_KEY
EOF

echo ""
echo "✓ .env文件已创建"

# 初始化数据库
echo ""
echo "初始化数据库..."
mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASSWORD" < init_db.sql

if [ $? -eq 0 ]; then
    echo "✓ 数据库初始化成功"
else
    echo "✗ 数据库初始化失败"
    exit 1
fi

# 迁移数据
echo ""
read -p "是否迁移现有JSON数据到MySQL? (y/n): " migrate
if [ "$migrate" = "y" ]; then
    echo "开始迁移数据..."
    venv/bin/python migrate_to_mysql.py
    
    if [ $? -eq 0 ]; then
        echo "✓ 数据迁移成功"
        
        # 备份JSON文件
        echo ""
        read -p "是否备份并删除JSON文件? (y/n): " backup
        if [ "$backup" = "y" ]; then
            mkdir -p backup
            mv accounts/accounts.json backup/ 2>/dev/null
            mv accounts/cards.json backup/ 2>/dev/null
            mv accounts/cookies/*.json backup/ 2>/dev/null
            echo "✓ JSON文件已备份到 backup/ 目录"
        fi
    else
        echo "✗ 数据迁移失败"
        exit 1
    fi
fi

echo ""
echo "=========================================="
echo "设置完成！"
echo "=========================================="
echo ""
echo "下一步:"
echo "1. 安装依赖: venv/bin/pip install -r requirements.txt"
echo "2. 启动服务: venv/bin/python app.py"
echo ""
