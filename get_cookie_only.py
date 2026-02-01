#!/usr/bin/env python3
import requests
import re
import json
import urllib3
import warnings
import os
import time
from urllib.parse import urlparse, parse_qs
urllib3.disable_warnings()
warnings.filterwarnings("ignore")
LOGIN_URL = "https://login.live.com/oauth20_authorize.srf?client_id=00000000402B5328&redirect_uri=https://login.live.com/oauth20_desktop.srf&scope=service::user.auth.xboxlive.com::MBI_SSL&display=touch&response_type=token&locale=en"
class CookieGetter:
    def __init__(self, debug=False):
        self.session = requests.Session()
        self.session.verify = False
        self.debug = debug
        self.start_time = time.time()
        if self.debug:
            os.makedirs('debug', exist_ok=True)
        os.makedirs('cookies', exist_ok=True)
    def save_page_content(self, step_name, content, url=""):
        if not self.debug:
            return
        filename = f"debug/{step_name}.html"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"<!-- URL: {url} -->\n")
                f.write(f"<!-- Step: {step_name} -->\n")
                f.write(f"<!-- Length: {len(content)} bytes -->\n\n")
                f.write(content)
            print(f"[调试] 已保存: {filename}")
        except Exception as e:
            print(f"[错误] 保存页面失败: {e}")
    def show_page_preview(self, content, max_lines=20):
        if not self.debug:
            return
        lines = content.split('\n')
        preview_lines = lines[:max_lines]
        print(f"\n[调试] 页面预览 (前 {max_lines} 行):")
        print("-" * 70)
        for i, line in enumerate(preview_lines, 1):
            if line.strip():
                print(f"{i:3d} | {line[:100]}")
        if len(lines) > max_lines:
            print(f"... (还有 {len(lines) - max_lines} 行)")
        print("-" * 70)
    def get_login_page(self):
        if self.debug:
            print("[1/4] Fetching login page...")
        try:
            response = self.session.get(LOGIN_URL, timeout=15)
            if self.debug:
                print(f"  Status: {response.status_code}")
                print(f"  URL: {response.url}")
                print(f"  Size: {len(response.text)} bytes")
            self.save_page_content("01_login_page", response.text, response.url)
            self.show_page_preview(response.text)
            ppft_match = re.search(r'value=\\?"(.+?)\\?"', response.text, re.S) or re.search(r'value="(.+?)"', response.text, re.S)
            if not ppft_match:
                print("[错误] 无法提取 PPFT token")
                return None, None
            ppft = ppft_match.group(1)
            urlpost_match = re.search(r'"urlPost":"(.+?)"', response.text, re.S) or re.search(r"urlPost:'(.+?)'", response.text, re.S)
            if not urlpost_match:
                print("[错误] 无法提取 urlPost")
                return None, None
            urlpost = urlpost_match.group(1)
            if self.debug:
                print(f"  PPFT: {ppft[:50]}...")
                print(f"  urlPost: {urlpost}")
            return urlpost, ppft
        except Exception as e:
            print(f"[错误] 获取登录页面失败: {e}")
            return None, None
    def login(self, email, password, urlpost, ppft):
        if self.debug:
            print("[2/4] Submitting login...")
        try:
            data = {
                'login': email,
                'loginfmt': email,
                'passwd': password,
                'PPFT': ppft
            }
            response = self.session.post(
                urlpost,
                data=data,
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                },
                allow_redirects=True,
                timeout=15
            )
            if self.debug:
                print(f"  Status: {response.status_code}")
                print(f"  URL: {response.url}")
                print(f"  Size: {len(response.text)} bytes")
            self.save_page_content("02_login_response", response.text, response.url)
            self.show_page_preview(response.text)
            if '#' in response.url and 'access_token' in response.url:
                if self.debug:
                    print("  Login successful")
                return True
            elif 'cancel?mkt=' in response.text:
                if self.debug:
                    print("  Additional verification required...")
                try:
                    ipt = re.search('(?<="ipt" value=")(.+?)(?=")', response.text).group(1)
                    pprid = re.search('(?<="pprid" value=")(.+?)(?=")', response.text).group(1)
                    uaid = re.search('(?<="uaid" value=")(.+?)(?=")', response.text).group(1)
                    action_url = re.search('(?<=id="fmHF" action=")(.+?)(?=")', response.text).group(1)
                    if self.debug:
                        print(f"  ipt: {ipt[:50]}...")
                        print(f"  pprid: {pprid}")
                        print(f"  uaid: {uaid}")
                    verify_data = {
                        'ipt': ipt,
                        'pprid': pprid,
                        'uaid': uaid
                    }
                    verify_response = self.session.post(
                        action_url,
                        data=verify_data,
                        allow_redirects=True,
                        timeout=15
                    )
                    if self.debug:
                        print(f"  Verify status: {verify_response.status_code}")
                    self.save_page_content("03_verify_response", verify_response.text, verify_response.url)
                    self.show_page_preview(verify_response.text)
                    return_url_match = re.search('(?<="recoveryCancel":{"returnUrl":")(.+?)(?=")', verify_response.text)
                    if not return_url_match:
                        if self.debug:
                            print("  Cannot extract return URL")
                        return False
                    return_url = return_url_match.group(1)
                    final_response = self.session.get(
                        return_url,
                        allow_redirects=True,
                        timeout=15
                    )
                    if self.debug:
                        print(f"  Final status: {final_response.status_code}")
                    self.save_page_content("04_final_response", final_response.text, final_response.url)
                    self.show_page_preview(final_response.text)
                    if '#' in final_response.url and 'access_token' in final_response.url:
                        if self.debug:
                            print("  Verification passed, login successful")
                        return True
                except Exception as e:
                    print(f"[错误] 验证失败: {e}")
                    return False
            elif any(keyword in response.text for keyword in ["recover?mkt", "account.live.com/identity/confirm", "Email/Confirm"]):
                print("[错误] 需要双因素认证，无法自动登录")
                return False
            elif any(keyword in response.text.lower() for keyword in ["password is incorrect", "account doesn't exist", "sign in to your microsoft account"]):
                print("[错误] 密码错误或账号不存在")
                return False
            else:
                print("[错误] 未知响应，登录可能失败")
                title_match = re.search(r'<title>(.+?)</title>', response.text)
                if self.debug and title_match:
                    print(f"  页面标题: {title_match.group(1)}")
                return False
        except Exception as e:
            print(f"[错误] 登录失败: {e}")
            if self.debug:
                import traceback
                traceback.print_exc()
            return False
    def get_cookies(self):
        if self.debug:
            print("[3/4] Extracting cookies...")
        cookies = {}
        for cookie in self.session.cookies:
            cookies[cookie.name] = cookie.value
        if self.debug:
            print(f"  Found {len(cookies)} cookies")
            important_cookies = ['MSPAuth', 'MSPOK', 'WLSSC', '__Host-MSAAUTH']
            for name in important_cookies:
                if name in cookies:
                    value = cookies[name]
                    print(f"  {name}: {value[:50]}...")
        return cookies
    def save_cookies(self, cookies, email):
        if self.debug:
            print("[4/4] Saving cookies...")
        try:
            safe_email = re.sub(r'[^\w\-_\.]', '_', email)
            filename = f"cookies/{safe_email}.json"
            with open(filename, 'w') as f:
                json.dump(cookies, f, indent=2)
            return filename
        except Exception as e:
            print(f"[错误] 保存失败: {e}")
            return None
    def get_elapsed_time(self):
        elapsed = time.time() - self.start_time
        return f"{elapsed:.2f}s"
def main():
    print("="*80)
    print("Microsoft Cookie 获取工具")
    print("="*80)
    debug_input = input("调试模式? [y/N]: ").strip().lower()
    debug_mode = debug_input in ['y', 'yes']
    if debug_mode:
        print("[调试] 调试模式已启用")
        print("[调试] 页面将保存到 debug/ 文件夹\n")
    account_input = input("邮箱 或 邮箱:密码: ").strip()
    if ':' in account_input:
        parts = account_input.split(':', 1)
        email = parts[0].strip()
        password = parts[1].strip()
    else:
        email = account_input
        password = input("密码: ").strip()
    if not email or not password:
        print("[错误] 需要邮箱和密码")
        return
    print(f"\n[信息] 账号: {email}")
    print("[信息] 开始登录...\n")
    getter = CookieGetter(debug=debug_mode)
    urlpost, ppft = getter.get_login_page()
    if not urlpost or not ppft:
        print(f"\n[失败] 用时: {getter.get_elapsed_time()}")
        return
    success = getter.login(email, password, urlpost, ppft)
    if not success:
        print(f"\n[失败] 用时: {getter.get_elapsed_time()}")
        return
    cookies = getter.get_cookies()
    if not cookies:
        print(f"\n[失败] 用时: {getter.get_elapsed_time()}")
        return
    filename = getter.save_cookies(cookies, email)
    if filename:
        print(f"\n[成功] Cookie 已保存: {filename}")
        print(f"[成功] 用时: {getter.get_elapsed_time()}")
        print(f"[成功] Cookie 数量: {len(cookies)}")
    else:
        print(f"\n[失败] 用时: {getter.get_elapsed_time()}")
if __name__ == '__main__':
    main()
