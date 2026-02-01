#!/usr/bin/env python3
import os
import json
import re
import time
from datetime import datetime
from pathlib import Path
import threading
from queue import Queue

class AccountManager:
    def __init__(self):
        self.base_dir = Path("accounts")
        self.cookie_dir = self.base_dir / "cookies"
        self.accounts_file = self.base_dir / "accounts.json"
        
        self.base_dir.mkdir(exist_ok=True)
        self.cookie_dir.mkdir(exist_ok=True)
        
        self.accounts = self.load_accounts()
    
    def load_accounts(self):
        if self.accounts_file.exists():
            with open(self.accounts_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def save_accounts(self):
        with open(self.accounts_file, 'w', encoding='utf-8') as f:
            json.dump(self.accounts, f, indent=2, ensure_ascii=False)
    
    def extract_credentials(self, text):
        results = []
        
        pattern_full = r'\[(\d+)\]([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9_-]+):([^\s\|]+)\s*\|McName:([^\s\[]+)(?:\s*\[Hypixel:([^\]]+)\])?(?:\s*\[Capes:([^\]]+)\])?'
        matches_full = re.findall(pattern_full, text)
        
        for match in matches_full:
            level, email, password, mcname, hypixel, capes = match
            
            hypixel_data = {}
            if hypixel:
                for item in hypixel.split():
                    if ':' in item:
                        key, value = item.split(':', 1)
                        hypixel_data[key] = value.replace('-Coins', '')
            
            cape_list = [c.strip() for c in capes.split(',')] if capes else []
            
            results.append({
                'email': email.strip(),
                'password': password.strip(),
                'level': int(level),
                'mcname': mcname.strip(),
                'hypixel': hypixel_data,
                'capes': cape_list
            })
        
        pattern_simple = r'([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9_-]+):([^\s\|]+)'
        matches_simple = re.findall(pattern_simple, text)
        
        existing_emails = {r['email'] for r in results}
        
        for email, password in matches_simple:
            email = email.strip()
            password = password.strip()
            
            if email not in existing_emails:
                results.append({
                    'email': email,
                    'password': password,
                    'level': 0,
                    'mcname': 'Unknown',
                    'hypixel': {},
                    'capes': []
                })
        
        return results
    
    def import_accounts(self, text):
        credentials = self.extract_credentials(text)
        
        new_count = 0
        duplicate_count = 0
        
        for data in credentials:
            email = data['email']
            
            if email in self.accounts:
                duplicate_count += 1
                print(f"[跳过] {email} (已存在)")
            else:
                self.accounts[email] = {
                    'password': data['password'],
                    'level': data['level'],
                    'mcname': data['mcname'],
                    'hypixel': data['hypixel'],
                    'capes': data['capes'],
                    'created_at': datetime.now().isoformat(),
                    'cookie_status': 'none',
                    'last_login': None
                }
                new_count += 1
                
                if data['level'] > 0:
                    print(f"[添加] Lv.{data['level']} {email} ({data['mcname']})")
                else:
                    print(f"[添加] {email}")
        
        self.save_accounts()
        
        print(f"\n导入完成:")
        print(f"  新增: {new_count}")
        print(f"  重复: {duplicate_count}")
        print(f"  总计: {len(self.accounts)}")
    
    def list_accounts(self, detailed=False):
        if not self.accounts:
            print("没有账号")
            return
        
        if detailed:
            for i, (email, data) in enumerate(self.accounts.items(), 1):
                cookie_file = self.cookie_dir / f"{email}.json"
                cookie_status = "✓" if cookie_file.exists() else "✗"
                
                print(f"\n[{i}] {email}")
                
                level = data.get('level', 0)
                if level > 0:
                    print(f"  等级: Lv.{level}")
                
                mcname = data.get('mcname', 'Unknown')
                if mcname != 'Unknown':
                    print(f"  MC名: {mcname}")
                
                print(f"  Cookie: {cookie_status}")
                
                hypixel = data.get('hypixel', {})
                if hypixel:
                    hypixel_str = ' '.join([f"{k}:{v}" for k, v in hypixel.items()])
                    print(f"  Hypixel: {hypixel_str}")
                
                capes = data.get('capes', [])
                if capes:
                    print(f"  Capes: {', '.join(capes[:3])}{'...' if len(capes) > 3 else ''}")
                
                print(f"  创建: {data.get('created_at', 'N/A')[:19]}")
        else:
            print(f"\n{'序号':<4} {'等级':<6} {'MC名':<20} {'邮箱':<30} {'Cookie':<8}")
            print("=" * 80)
            
            for i, (email, data) in enumerate(self.accounts.items(), 1):
                cookie_file = self.cookie_dir / f"{email}.json"
                cookie_status = "✓" if cookie_file.exists() else "✗"
                
                level = data.get('level', 0)
                level_str = f"Lv.{level}" if level > 0 else "-"
                
                mcname = data.get('mcname', 'Unknown')[:18]
                if mcname == 'Unknown':
                    mcname = '-'
                
                email_short = email[:28]
                
                print(f"{i:<4} {level_str:<6} {mcname:<20} {email_short:<30} {cookie_status:<8}")
    
    def get_cookies_batch(self, emails=None):
        if emails is None:
            emails = list(self.accounts.keys())
        
        print(f"\n开始批量获取 Cookie ({len(emails)} 个账号)...")
        
        success_count = 0
        fail_count = 0
        
        for i, email in enumerate(emails, 1):
            if email not in self.accounts:
                print(f"[{i}/{len(emails)}] {email} - 账号不存在")
                continue
            
            password = self.accounts[email]['password']
            
            print(f"\n[{i}/{len(emails)}] {email}")
            
            import subprocess
            script_dir = Path(__file__).parent
            
            try:
                result = subprocess.run(
                    [str(script_dir / 'venv/bin/python3'), str(script_dir / 'get_cookie_only.py')],
                    input=f"n\n{email}:{password}\n",
                    capture_output=True,
                    text=True,
                    cwd=str(script_dir),
                    timeout=30
                )
                
                safe_email = re.sub(r'[^\w\-_\.]', '_', email)
                source_cookie = script_dir / "cookies" / f"{safe_email}.json"
                target_cookie = self.cookie_dir / f"{email}.json"
                
                if source_cookie.exists():
                    import shutil
                    shutil.move(str(source_cookie), str(target_cookie))
                    
                    self.accounts[email]['cookie_status'] = 'valid'
                    self.accounts[email]['cookie_updated'] = datetime.now().isoformat()
                    success_count += 1
                    print(f"  ✓ 成功")
                else:
                    self.accounts[email]['cookie_status'] = 'failed'
                    fail_count += 1
                    
                    if '成功' in result.stdout:
                        print(f"  ✗ 失败 (Cookie 文件未找到)")
                        print(f"  查找: {source_cookie}")
                    elif result.stderr:
                        print(f"  ✗ 失败 (错误: {result.stderr[:100]})")
                    else:
                        print(f"  ✗ 失败")
                        
            except subprocess.TimeoutExpired:
                print(f"  ✗ 超时")
                fail_count += 1
            except Exception as e:
                print(f"  ✗ 异常: {e}")
                fail_count += 1
        
        self.save_accounts()
        
        print(f"\n批量获取完成:")
        print(f"  成功: {success_count}")
        print(f"  失败: {fail_count}")
    
    def auto_login_batch(self, device_code, emails=None):
        if emails is None:
            emails = [e for e in self.accounts.keys() 
                     if (self.cookie_dir / f"{e}.json").exists()]
        
        if not emails:
            print("没有可用的账号（需要先获取 Cookie）")
            return
        
        print(f"\n开始批量登录 ({len(emails)} 个账号)...")
        print(f"设备代码: {device_code}\n")
        
        for i, email in enumerate(emails, 1):
            if email not in self.accounts:
                continue
            
            cookie_file = self.cookie_dir / f"{email}.json"
            if not cookie_file.exists():
                print(f"[{i}/{len(emails)}] {email} - Cookie 不存在")
                continue
            
            password = self.accounts[email]['password']
            
            print(f"[{i}/{len(emails)}] {email}")
            
            import subprocess
            script_dir = Path(__file__).parent
            
            source_cookie = self.cookie_dir / f"{email}.json"
            target_cookie = script_dir / "accounts" / "cookies" / f"{email}.json"
            temp_cookie = script_dir / "cookies" / f"{email}.json"
            
            import shutil
            script_dir.joinpath("cookies").mkdir(exist_ok=True)
            shutil.copy(str(source_cookie), str(temp_cookie))
            
            result = subprocess.run(
                [str(script_dir / 'venv/bin/python3'), str(script_dir / 'auto_login_http.py')],
                input=f"{device_code}\n{email}:{password}\nn\n",
                capture_output=True,
                text=True,
                cwd=str(script_dir)
            )
            
            if temp_cookie.exists():
                temp_cookie.unlink()
            
            if '成功' in result.stdout:
                self.accounts[email]['last_login'] = datetime.now().isoformat()
                print(f"  ✓ 登录成功")
                break
            else:
                print(f"  ✗ 登录失败")
        
        self.save_accounts()
    
    def delete_account(self, email):
        if email in self.accounts:
            del self.accounts[email]
            self.save_accounts()
            
            cookie_file = self.cookie_dir / f"{email}.json"
            if cookie_file.exists():
                cookie_file.unlink()
            
            print(f"已删除: {email}")
        else:
            print(f"账号不存在: {email}")
    
    def export_accounts(self, filename="accounts_export.txt"):
        with open(filename, 'w', encoding='utf-8') as f:
            for email, data in self.accounts.items():
                f.write(f"{email}:{data['password']}\n")
        
        print(f"已导出到: {filename}")
        print(f"总计: {len(self.accounts)} 个账号")


def show_menu():
    print("\n" + "="*60)
    print("Microsoft 账号管理系统")
    print("="*60)
    print("1. 导入账号（粘贴文本）")
    print("2. 从文件导入账号")
    print("3. 查看所有账号")
    print("4. 查看账号详情")
    print("5. 批量获取 Cookie")
    print("6. 批量登录 HMCL")
    print("7. 单个账号登录")
    print("8. 删除账号")
    print("9. 导出账号")
    print("10. Cookie 管理")
    print("0. 退出")
    print("="*60)


def cookie_management_menu(manager):
    while True:
        print("\n" + "="*60)
        print("Cookie 管理")
        print("="*60)
        print("1. 查看所有 Cookie")
        print("2. 删除 Cookie")
        print("3. 刷新 Cookie")
        print("0. 返回")
        print("="*60)
        
        choice = input("\n选择: ").strip()
        
        if choice == '1':
            print(f"\n{'邮箱':<35} {'状态':<8} {'更新时间':<20}")
            print("=" * 70)
            
            for email in manager.accounts.keys():
                cookie_file = manager.cookie_dir / f"{email}.json"
                if cookie_file.exists():
                    stat = cookie_file.stat()
                    mtime = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                    print(f"{email:<35} {'有效':<8} {mtime:<20}")
                else:
                    print(f"{email:<35} {'无':<8} {'-':<20}")
        
        elif choice == '2':
            email = input("输入邮箱: ").strip()
            cookie_file = manager.cookie_dir / f"{email}.json"
            if cookie_file.exists():
                cookie_file.unlink()
                print(f"已删除 Cookie: {email}")
            else:
                print("Cookie 不存在")
        
        elif choice == '3':
            email = input("输入邮箱（留空=全部）: ").strip()
            if email:
                if email in manager.accounts:
                    manager.get_cookies_batch([email])
                else:
                    print("账号不存在")
            else:
                manager.get_cookies_batch()
        
        elif choice == '0':
            break


def main():
    manager = AccountManager()
    
    while True:
        show_menu()
        choice = input("\n选择: ").strip()
        
        if choice == '1':
            print("\n粘贴账号文本（输入 END 结束）:")
            lines = []
            while True:
                line = input()
                if line.strip().upper() == 'END':
                    break
                lines.append(line)
            
            text = '\n'.join(lines)
            manager.import_accounts(text)
        
        elif choice == '2':
            filename = input("文件路径: ").strip()
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    text = f.read()
                manager.import_accounts(text)
            except Exception as e:
                print(f"读取文件失败: {e}")
        
        elif choice == '3':
            manager.list_accounts()
        
        elif choice == '4':
            manager.list_accounts(detailed=True)
        
        elif choice == '5':
            manager.list_accounts()
            choice = input("\n输入序号（留空=全部，多个用逗号分隔）: ").strip()
            
            if choice:
                indices = [int(x.strip()) for x in choice.split(',')]
                emails = [list(manager.accounts.keys())[i-1] for i in indices]
                manager.get_cookies_batch(emails)
            else:
                manager.get_cookies_batch()
        
        elif choice == '6':
            device_code = input("输入设备代码 (8位): ").strip().upper()
            if len(device_code) != 8:
                print("设备代码必须是 8 位")
                continue
            
            manager.list_accounts()
            choice = input("\n输入序号（留空=第一个有 Cookie 的）: ").strip()
            
            if choice:
                indices = [int(x.strip()) for x in choice.split(',')]
                emails = [list(manager.accounts.keys())[i-1] for i in indices]
                manager.auto_login_batch(device_code, emails)
            else:
                manager.auto_login_batch(device_code)
        
        elif choice == '7':
            device_code = input("输入设备代码 (8位): ").strip().upper()
            if len(device_code) != 8:
                print("设备代码必须是 8 位")
                continue
            
            manager.list_accounts()
            try:
                idx = int(input("输入序号: ").strip())
                if idx < 1 or idx > len(manager.accounts):
                    print("无效的序号")
                    continue
                
                email = list(manager.accounts.keys())[idx-1]
                manager.auto_login_batch(device_code, [email])
            except (ValueError, IndexError):
                print("无效的输入")
        
        elif choice == '8':
            manager.list_accounts()
            try:
                idx = int(input("输入序号: ").strip())
                if idx < 1 or idx > len(manager.accounts):
                    print("无效的序号")
                    continue
                
                email = list(manager.accounts.keys())[idx-1]
                
                confirm = input(f"确认删除 {email}? (y/N): ").strip().lower()
                if confirm == 'y':
                    manager.delete_account(email)
            except (ValueError, IndexError):
                print("无效的输入")
        
        elif choice == '9':
            filename = input("导出文件名 (默认: accounts_export.txt): ").strip()
            if not filename:
                filename = "accounts_export.txt"
            manager.export_accounts(filename)
        
        elif choice == '10':
            cookie_management_menu(manager)
        
        elif choice == '0':
            print("再见！")
            break
        
        else:
            print("无效选择")


if __name__ == '__main__':
    main()
