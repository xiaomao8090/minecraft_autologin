#!/usr/bin/env python3
"""测试数据库连接"""

from dotenv import load_dotenv
from database import Database

load_dotenv()

try:
    print("测试数据库连接...")
    db = Database()
    
    print("✓ 数据库连接成功")
    
    # 测试查询
    accounts = db.get_all_accounts()
    print(f"✓ 账号数量: {len(accounts)}")
    
    cards = db.get_all_cards()
    print(f"✓ 卡密数量: {len(cards)}")
    
    print("\n数据库测试通过！")
    
except Exception as e:
    print(f"✗ 数据库连接失败: {e}")
    exit(1)
