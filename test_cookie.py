#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')

from get_cookie_only import CookieGetter

email = "105480339@qq.com"
password = "Mother0418"

print(f"测试账号: {email}")
print("="*50)

getter = CookieGetter(debug=False)

print("[1/4] 获取登录页面...")
urlpost, ppft = getter.get_login_page()
if not urlpost or not ppft:
    print("✗ 失败")
    sys.exit(1)
print(f"✓ 成功")
print(f"  PPFT: {ppft[:50]}...")
print(f"  urlPost: {urlpost[:80]}...")

print("\n[2/4] 登录...")
success = getter.login(email, password, urlpost, ppft)
if not success:
    print("✗ 失败")
    sys.exit(1)
print("✓ 成功")

print("\n[3/4] 获取完整 Cookie...")
cookies = getter.get_complete_cookies()
if not cookies:
    print("✗ 失败")
    sys.exit(1)
print(f"✓ 成功 ({len(cookies)} 个)")

print("\n[4/4] 保存 Cookie...")
filepath = getter.save_cookies(cookies, email)
if not filepath:
    print("✗ 失败")
    sys.exit(1)
print(f"✓ 成功: {filepath}")

print("\n" + "="*50)
print(f"总用时: {getter.get_elapsed_time()}")
