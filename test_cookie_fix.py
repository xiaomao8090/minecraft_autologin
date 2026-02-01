#!/usr/bin/env python3
"""测试Cookie获取的修复方案"""

import requests
import time
import json
import re
from bs4 import BeautifulSoup

# 测试账号2
EMAIL = "332316690@qq.com"
PASSWORD = "xl15830532317"

print("=" * 80)
print("测试Cookie获取修复方案")
print("=" * 80)
print()

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})

def save_html(filename, content, url):
    """保存HTML用于调试"""
    with open(f"debug_test/{filename}.html", 'w', encoding='utf-8') as f:
        f.write(f"<!-- URL: {url} -->\n")
        f.write(f"<!-- Step: {filename} -->\n\n")
        f.write(content)

# 步骤1: 登录
print("[1] 登录Microsoft账号...")
login_url = "https://login.live.com/oauth20_authorize.srf?client_id=00000000402B5328&redirect_uri=https://login.live.com/oauth20_desktop.srf&scope=service::user.auth.xboxlive.com::MBI_SSL&display=touch&response_type=token&locale=en"
response = session.get(login_url, timeout=15)
save_html("01_login_page", response.text, response.url)

# 提取PPFT和urlPost
soup = BeautifulSoup(response.text, 'html.parser')
ppft_input = soup.find('input', {'name': 'PPFT'})
ppft = ppft_input['value'] if ppft_input else None
url_post_input = soup.find('input', {'name': 'urlPost'})
url_post = url_post_input['value'] if url_post_input else None

if ppft and url_post:
    print(f"  PPFT: {ppft[:20]}...")
    print(f"  urlPost: {url_post[:60]}...")
else:
    print(f"  ⚠️ 未找到PPFT或urlPost")
    print(f"  PPFT: {ppft}")
    print(f"  urlPost: {url_post}")
print()

# 步骤2: 提交登录
if not ppft or not url_post:
    print("[错误] 无法获取登录表单信息")
    exit(1)

print("[2] 提交登录凭证...")
login_data = {
    'login': EMAIL,
    'passwd': PASSWORD,
    'PPFT': ppft
}
response = session.post(url_post, data=login_data, timeout=15, allow_redirects=True)
save_html("02_after_login", response.text, response.url)
print(f"  最终URL: {response.url[:80]}...")
print(f"  是否包含access_token: {'access_token' in response.url}")
print()

# 步骤3: 访问m365页面（当前方法）
print("[3] 方法1: 直接访问m365页面（当前方法）...")
m365_url = "https://m365.cloud.microsoft/search/?auth=1&origindomain=Office"
response = session.get(m365_url, timeout=15, allow_redirects=True)
save_html("03_m365_direct", response.text, response.url)
print(f"  最终URL: {response.url[:80]}...")
print(f"  响应长度: {len(response.text)} 字节")

# 检查是否是自动提交表单
soup = BeautifulSoup(response.text, 'html.parser')
form = soup.find('form')
if form:
    action = form.get('action', '')
    print(f"  检测到表单，目标: {action[:80]}...")
    if '/ar/cancel?' in action:
        print("  ⚠️ 警告：表单会跳转到安全信息页面！")
    else:
        print("  ✓ 表单目标正常")
else:
    print("  ✓ 没有自动提交表单")

cookies_method1 = len(session.cookies)
print(f"  Cookie数量: {cookies_method1}")
print()

# 步骤4: 访问m365页面（改进方法）
print("[4] 方法2: 访问m365页面并等待跳转完成...")

# 重新创建session来测试
session2 = requests.Session()
session2.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})

# 复制登录后的cookies
for cookie in session.cookies:
    session2.cookies.set_cookie(cookie)

# 访问m365，但设置allow_redirects=False，手动处理跳转
response = session2.get(m365_url, timeout=15, allow_redirects=False)
print(f"  第1次请求: {response.status_code}")
print(f"  URL: {response.url[:80]}...")

redirect_count = 0
max_redirects = 10

while response.status_code in [301, 302, 303, 307, 308] and redirect_count < max_redirects:
    redirect_count += 1
    location = response.headers.get('Location')
    if not location:
        break
    
    print(f"  第{redirect_count + 1}次请求（跳转）: {location[:80]}...")
    
    # 检查是否是安全信息页面
    if '/ar/cancel?' in location:
        print(f"  ⚠️ 警告：检测到安全信息页面跳转！")
        print(f"  停止跟踪跳转")
        break
    
    response = session2.get(location, timeout=15, allow_redirects=False)
    print(f"    状态: {response.status_code}")

save_html("04_m365_with_redirects", response.text, response.url)
cookies_method2 = len(session2.cookies)
print(f"  Cookie数量: {cookies_method2}")
print()

# 步骤5: 对比结果
print("=" * 80)
print("对比结果")
print("=" * 80)
print(f"方法1（直接访问）: {cookies_method1} 个Cookie")
print(f"方法2（处理跳转）: {cookies_method2} 个Cookie")
print()

if cookies_method1 == cookies_method2:
    print("✓ Cookie数量相同")
else:
    print(f"⚠️ Cookie数量不同，差异: {abs(cookies_method1 - cookies_method2)} 个")

print()
print("详细Cookie列表:")
print()
print("方法1的Cookie:")
for cookie in session.cookies:
    print(f"  - {cookie.name}: {cookie.domain}")

print()
print("方法2的Cookie:")
for cookie in session2.cookies:
    print(f"  - {cookie.name}: {cookie.domain}")

print()
print("=" * 80)
print("测试完成")
print("=" * 80)
