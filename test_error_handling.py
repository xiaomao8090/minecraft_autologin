#!/usr/bin/env python3
import json
import os
from pathlib import Path

print("="*80)
print("错误处理测试")
print("="*80)

BASE_DIR = Path(__file__).parent
ACCOUNTS_FILE = BASE_DIR / "accounts" / "accounts.json"
COOKIES_DIR = BASE_DIR / "accounts" / "cookies"

os.makedirs(COOKIES_DIR, exist_ok=True)

def validate_cookie_file(cookie_file):
    if not cookie_file.exists():
        return False, "Cookie文件不存在"
    
    try:
        with open(cookie_file, 'r', encoding='utf-8') as f:
            cookies = json.load(f)
        
        if not isinstance(cookies, dict):
            return False, "Cookie格式错误"
        
        if len(cookies) < 10:
            return False, f"Cookie不完整（只有{len(cookies)}个）"
        
        required_cookies = ['__Host-MSAAUTH', 'WLSSC']
        missing = [c for c in required_cookies if c not in cookies]
        if missing:
            return False, f"缺少关键Cookie: {', '.join(missing)}"
        
        return True, "Cookie有效"
    except json.JSONDecodeError:
        return False, "Cookie文件格式错误"
    except Exception as e:
        return False, f"Cookie验证失败: {str(e)}"

print("\n[测试1] Cookie验证功能")
print("-"*80)

test_cookie_file = COOKIES_DIR / "test_cookie.json"

print("\n1.1 测试：文件不存在")
valid, msg = validate_cookie_file(test_cookie_file)
print(f"  结果: {msg}")
assert not valid, "应该返回False"
print("  ✓ 通过")

print("\n1.2 测试：空Cookie文件")
with open(test_cookie_file, 'w') as f:
    json.dump({}, f)
valid, msg = validate_cookie_file(test_cookie_file)
print(f"  结果: {msg}")
assert not valid, "应该返回False"
print("  ✓ 通过")

print("\n1.3 测试：Cookie数量不足")
with open(test_cookie_file, 'w') as f:
    json.dump({"cookie1": "value1", "cookie2": "value2"}, f)
valid, msg = validate_cookie_file(test_cookie_file)
print(f"  结果: {msg}")
assert not valid, "应该返回False"
print("  ✓ 通过")

print("\n1.4 测试：缺少关键Cookie")
cookies = {f"cookie{i}": f"value{i}" for i in range(15)}
with open(test_cookie_file, 'w') as f:
    json.dump(cookies, f)
valid, msg = validate_cookie_file(test_cookie_file)
print(f"  结果: {msg}")
assert not valid, "应该返回False"
print("  ✓ 通过")

print("\n1.5 测试：完整有效的Cookie")
cookies = {f"cookie{i}": f"value{i}" for i in range(15)}
cookies['__Host-MSAAUTH'] = 'auth_value'
cookies['WLSSC'] = 'wlssc_value'
with open(test_cookie_file, 'w') as f:
    json.dump(cookies, f)
valid, msg = validate_cookie_file(test_cookie_file)
print(f"  结果: {msg}")
assert valid, "应该返回True"
print("  ✓ 通过")

print("\n1.6 测试：格式错误的JSON")
with open(test_cookie_file, 'w') as f:
    f.write("{invalid json")
valid, msg = validate_cookie_file(test_cookie_file)
print(f"  结果: {msg}")
assert not valid, "应该返回False"
print("  ✓ 通过")

test_cookie_file.unlink()

print("\n[测试2] 错误检测函数")
print("-"*80)

from auto_login_http import AutoLoginHTTP

class MockResponse:
    def __init__(self, text, url):
        self.text = text
        self.url = url

auto_login = AutoLoginHTTP(debug=False)

print("\n2.1 测试：检测设备代码过期")
response = MockResponse('"sErrTxt":"The code has expired"', "https://example.com")
error_type, error_msg = auto_login.check_error_in_response(response)
print(f"  错误类型: {error_type}")
print(f"  错误消息: {error_msg}")
assert error_type == 'expired_code', "应该检测到expired_code"
print("  ✓ 通过")

print("\n2.2 测试：检测密码错误")
response = MockResponse('"sErrTxt":"Your password is incorrect"', "https://example.com")
error_type, error_msg = auto_login.check_error_in_response(response)
print(f"  错误类型: {error_type}")
print(f"  错误消息: {error_msg}")
assert error_type == 'invalid_password', "应该检测到invalid_password"
print("  ✓ 通过")

print("\n2.3 测试：无错误")
response = MockResponse('{"status": "ok"}', "https://example.com")
error_type, error_msg = auto_login.check_error_in_response(response)
print(f"  错误类型: {error_type}")
print(f"  错误消息: {error_msg}")
assert error_type is None, "应该返回None"
print("  ✓ 通过")

print("\n[测试3] 成功检测函数")
print("-"*80)

print("\n3.1 测试：检测800478C7标识")
response = MockResponse('{"code": "800478C7"}', "https://example.com")
is_success = auto_login.check_success_in_response(response)
print(f"  结果: {is_success}")
assert is_success, "应该返回True"
print("  ✓ 通过")

print("\n3.2 测试：检测res=success")
response = MockResponse('{}', "https://example.com?res=success")
is_success = auto_login.check_success_in_response(response)
print(f"  结果: {is_success}")
assert is_success, "应该返回True"
print("  ✓ 通过")

print("\n3.3 测试：检测大功告成")
response = MockResponse('大功告成！您已成功登录', "https://example.com")
is_success = auto_login.check_success_in_response(response)
print(f"  结果: {is_success}")
assert is_success, "应该返回True"
print("  ✓ 通过")

print("\n3.4 测试：无成功标识")
response = MockResponse('{"status": "pending"}', "https://example.com")
is_success = auto_login.check_success_in_response(response)
print(f"  结果: {is_success}")
assert not is_success, "应该返回False"
print("  ✓ 通过")

print("\n" + "="*80)
print("✓ 所有测试通过！")
print("="*80)
