#!/usr/bin/env python3
"""迁移JSON数据到MySQL数据库"""

import json
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from database import Database

# 加载环境变量
load_dotenv()

BASE_DIR = Path(__file__).parent
ACCOUNTS_FILE = BASE_DIR / "accounts" / "accounts.json"
COOKIES_DIR = BASE_DIR / "accounts" / "cookies"
CARDS_FILE = BASE_DIR / "accounts" / "cards.json"

def migrate():
    db = Database()
    
    print("开始迁移数据...")
    
    # 1. 迁移账号
    if ACCOUNTS_FILE.exists():
        with open(ACCOUNTS_FILE, 'r', encoding='utf-8') as f:
            accounts = json.load(f)
        
        print(f"\n迁移 {len(accounts)} 个账号...")
        for email, data in accounts.items():
            try:
                db.add_account(
                    email=email,
                    password=data.get('password', ''),
                    level=data.get('level', 0),
                    mcname=data.get('mcname', 'Unknown'),
                    subscription=data.get('subscription', ''),
                    hypixel=data.get('hypixel', {}),
                    capes=data.get('capes', [])
                )
                
                # 更新状态
                if data.get('cookie_status'):
                    db.update_account(email, cookie_status=data['cookie_status'])
                if data.get('last_login'):
                    db.update_account(email, last_login=data['last_login'])
                if data.get('disabled'):
                    db.update_account(email, disabled=data['disabled'])
                
                print(f"  ✓ {email}")
            except Exception as e:
                print(f"  ✗ {email}: {e}")
    
    # 2. 迁移Cookie
    if COOKIES_DIR.exists():
        cookie_files = list(COOKIES_DIR.glob("*.json"))
        print(f"\n迁移 {len(cookie_files)} 个Cookie...")
        
        for cookie_file in cookie_files:
            email = cookie_file.stem
            try:
                with open(cookie_file, 'r', encoding='utf-8') as f:
                    cookie_data = json.load(f)
                
                db.save_cookie(email, cookie_data)
                print(f"  ✓ {email}")
            except Exception as e:
                print(f"  ✗ {email}: {e}")
    
    # 3. 迁移卡密
    if CARDS_FILE.exists():
        with open(CARDS_FILE, 'r', encoding='utf-8') as f:
            cards = json.load(f)
        
        print(f"\n迁移 {len(cards)} 个卡密...")
        for card_key, data in cards.items():
            try:
                db.add_card(
                    card_key=card_key,
                    duration=data.get('duration', '1day'),
                    duration_days=data.get('duration_days', 1),
                    card_type=data.get('type', 'normal')
                )
                
                # 如果已使用，更新状态
                if data.get('used'):
                    expire_at = data.get('expire_at')
                    if expire_at:
                        db.use_card(card_key, expire_at)
                
                print(f"  ✓ {card_key}")
            except Exception as e:
                print(f"  ✗ {card_key}: {e}")
    
    # 4. 创建管理员账号
    print("\n创建管理员账号...")
    admin_username = os.environ.get('ADMIN_USERNAME', 'xiaomao')
    admin_password = os.environ.get('ADMIN_PASSWORD', '45004879te')
    
    try:
        conn = db.get_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO admin_users (username, password, created_at)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE password = %s
            """, (
                admin_username,
                db.encrypt(admin_password),
                datetime.now(),
                db.encrypt(admin_password)
            ))
        conn.commit()
        conn.close()
        print(f"  ✓ 管理员: {admin_username}")
    except Exception as e:
        print(f"  ✗ 管理员创建失败: {e}")
    
    print("\n迁移完成！")

if __name__ == '__main__':
    migrate()
