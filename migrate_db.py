#!/usr/bin/env python3
from database import Database
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

host = os.environ.get('DB_HOST', 'localhost')
port = int(os.environ.get('DB_PORT', 3306))
user = os.environ.get('DB_USER', 'root')
password = os.environ.get('DB_PASSWORD', '')
database = os.environ.get('DB_NAME', 'minecraft_autologin')

print("连接数据库...")
conn = pymysql.connect(host=host, port=port, user=user, password=password, database=database)

try:
    with conn.cursor() as cursor:
        print("添加用户管理字段...")
        cursor.execute("ALTER TABLE cards ADD COLUMN IF NOT EXISTS banned BOOLEAN DEFAULT FALSE")
        cursor.execute("ALTER TABLE cards ADD COLUMN IF NOT EXISTS last_ip VARCHAR(50)")
        cursor.execute("ALTER TABLE cards ADD COLUMN IF NOT EXISTS success_count INT DEFAULT 0")
        cursor.execute("ALTER TABLE cards ADD COLUMN IF NOT EXISTS fail_count INT DEFAULT 0")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_banned ON cards(banned)")
        
        print("添加订阅系统字段...")
        cursor.execute("ALTER TABLE accounts ADD COLUMN IF NOT EXISTS subscription_days INT DEFAULT 0")
        cursor.execute("ALTER TABLE accounts ADD COLUMN IF NOT EXISTS auto_renew BOOLEAN DEFAULT FALSE")
        cursor.execute("ALTER TABLE accounts ADD COLUMN IF NOT EXISTS subscription_updated_at DATE")
        cursor.execute("ALTER TABLE cards ADD COLUMN IF NOT EXISTS last_used_email VARCHAR(255)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_subscription_days ON accounts(subscription_days)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_auto_renew ON accounts(auto_renew)")
        
    conn.commit()
    print("✓ 数据库迁移完成")
except Exception as e:
    print(f"✗ 错误: {e}")
finally:
    conn.close()
