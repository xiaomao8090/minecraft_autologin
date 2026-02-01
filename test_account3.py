#!/usr/bin/env python3
"""测试账号3的脚本"""

import sys
import os

# 设置账号信息
EMAIL = "fabiula.pacheco@yahoo.com.br"
PASSWORD = "124471Br"
DEVICE_CODE = "QAKRVR5H"

print(f"=== 测试账号3 ===")
print(f"邮箱: {EMAIL}")
print(f"密码: {PASSWORD}")
print(f"设备代码: {DEVICE_CODE}")
print()

# 步骤1: 获取Cookie
print("步骤1: 获取Cookie...")
print(f"运行命令: echo '{EMAIL}:{PASSWORD}' | python get_cookie_only.py")
print()

# 使用subprocess运行
import subprocess

# 获取Cookie
try:
    result = subprocess.run(
        ["python", "get_cookie_only.py"],
        input=f"{EMAIL}:{PASSWORD}\ny\n",  # 添加 y 启用调试模式
        capture_output=True,
        text=True,
        cwd=os.path.dirname(os.path.abspath(__file__)),
        timeout=120
    )
    print("=== 获取Cookie输出 ===")
    print(result.stdout)
    if result.stderr:
        print("=== 错误输出 ===")
        print(result.stderr)
    print()
except Exception as e:
    print(f"获取Cookie失败: {e}")
    print()

# 步骤2: 自动登录
print("步骤2: 自动登录...")
print(f"运行命令: echo '{DEVICE_CODE}' | echo '{EMAIL}:{PASSWORD}' | python auto_login_http.py")
print()

try:
    result = subprocess.run(
        ["python", "auto_login_http.py"],
        input=f"{DEVICE_CODE}\n{EMAIL}:{PASSWORD}\ny\n",  # 添加 y 启用调试模式
        capture_output=True,
        text=True,
        cwd=os.path.dirname(os.path.abspath(__file__)),
        timeout=120
    )
    print("=== 自动登录输出 ===")
    print(result.stdout)
    if result.stderr:
        print("=== 错误输出 ===")
        print(result.stderr)
except Exception as e:
    print(f"自动登录失败: {e}")

print()
print("=== 测试完成 ===")
