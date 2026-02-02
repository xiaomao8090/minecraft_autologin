#!/usr/bin/env python3
import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
from database import Database

script_dir = Path(__file__).parent.absolute()
db = Database()

def refresh_cookie(email, password):
    try:
        result = subprocess.run(
            [str(script_dir / 'venv/bin/python'), str(script_dir / 'get_cookie_only.py'), f"{email}:{password}"],
            capture_output=True,
            text=True,
            cwd=str(script_dir),
            timeout=60
        )
        
        import re
        safe_email = re.sub(r'[^\w\-_\.]', '_', email)
        source_cookie = script_dir / "cookies" / f"{safe_email}.json"
        
        if source_cookie.exists():
            with open(source_cookie, 'r', encoding='utf-8') as f:
                cookie_data = json.load(f)
            db.save_cookie(email, cookie_data)
            db.update_account(email, cookie_status='valid')
            source_cookie.unlink()
            return True, '成功'
        else:
            error_msg = '获取失败'
            if '密码错误' in result.stdout or '登录失败' in result.stdout:
                error_msg = '密码错误'
                db.delete_account(email)
                db.delete_cookie(email)
            else:
                db.update_account(email, cookie_status='failed')
            return False, error_msg
    except Exception as e:
        return False, str(e)

def main():
    print(f"[{datetime.now()}] 开始批量刷新Cookie...")
    
    accounts = db.get_all_accounts()
    total = len(accounts)
    success_count = 0
    fail_count = 0
    deleted_count = 0
    
    print(f"总共 {total} 个账号需要刷新\n")
    
    for i, acc in enumerate(accounts, 1):
        email = acc['email']
        password = acc['password']
        
        print(f"[{i}/{total}] {email}...", end=' ')
        
        success, msg = refresh_cookie(email, password)
        
        if success:
            print(f"✓ {msg}")
            success_count += 1
        else:
            print(f"✗ {msg}")
            if '密码错误' in msg:
                deleted_count += 1
            fail_count += 1
    
    print(f"\n[{datetime.now()}] 刷新完成")
    print(f"成功: {success_count}")
    print(f"失败: {fail_count}")
    print(f"删除: {deleted_count}")
    print(f"总计: {total}")

if __name__ == '__main__':
    main()
