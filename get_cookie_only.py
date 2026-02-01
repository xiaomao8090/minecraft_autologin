#!/usr/bin/env python3
import requests
import re
import json
import urllib3
import warnings
import os
import time
from pathlib import Path
urllib3.disable_warnings()
warnings.filterwarnings("ignore")

LOGIN_URL = "https://login.live.com/oauth20_authorize.srf?client_id=00000000402B5328&redirect_uri=https://login.live.com/oauth20_desktop.srf&scope=service::user.auth.xboxlive.com::MBI_SSL&display=touch&response_type=token&locale=en"

class CookieGetter:
    def __init__(self, debug=False):
        self.session = requests.Session()
        self.session.verify = False
        self.debug = debug
        self.start_time = time.time()
        self.step = 0
        os.makedirs('cookies', exist_ok=True)
        if self.debug:
            os.makedirs('debug_cookie', exist_ok=True)

    def save_html(self, step_name, content, url=""):
        if not self.debug:
            return
        self.step += 1
        filename = f"debug_cookie/{self.step:02d}_{step_name}.html"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"<!-- URL: {url} -->\n")
                f.write(f"<!-- Step: {step_name} -->\n\n")
                f.write(content)
            print(f"  [DEBUG] 已保存: {filename}")
        except Exception as e:
            print(f"  [DEBUG] 保存失败: {e}")

    def get_login_page(self):
        try:
            print("[1/4] 访问登录页面...")
            response = self.session.get(LOGIN_URL, timeout=15)
            print(f"  状态: {response.status_code}")
            print(f"  URL: {response.url}")
            print(f"  响应长度: {len(response.text)} 字节")
            self.save_html("login_page", response.text, response.url)
            
            ppft_match = re.search(r'sFTTag.*value=\\\"(.+?)\\\"', response.text, re.S)
            if not ppft_match:
                ppft_match = re.search(r'"sFT":"(.+?)"', response.text, re.S)
            if not ppft_match:
                print("  [错误] 无法提取PPFT")
                return None, None
            ppft = ppft_match.group(1)
            print(f"  PPFT: {ppft[:20]}...")
            
            urlpost_match = re.search(r'"urlPost":"(.+?)"', response.text, re.S)
            if not urlpost_match:
                print("  [错误] 无法提取urlPost")
                return None, None
            urlpost = urlpost_match.group(1)
            print(f"  urlPost: {urlpost[:60]}...")
            
            return urlpost, ppft
        except Exception as e:
            print(f"  [错误] {e}")
            return None, None

    def login(self, email, password, urlpost, ppft):
        try:
            print("\n[2/4] 提交登录凭证...")
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
            print(f"  状态: {response.status_code}")
            print(f"  最终URL: {response.url}")
            print(f"  响应长度: {len(response.text)} 字节")
            self.save_html("after_login", response.text, response.url)
            
            if '#' in response.url and 'access_token' in response.url:
                print("  ✓ 登录成功（URL包含access_token）")
                return True
            elif 'cancel?mkt=' in response.text:
                print("  ⚠ 检测到安全信息页面，尝试跳过...")
                try:
                    ipt = re.search('(?<="ipt" value=")(.+?)(?=")', response.text).group(1)
                    pprid = re.search('(?<="pprid" value=")(.+?)(?=")', response.text).group(1)
                    uaid = re.search('(?<="uaid" value=")(.+?)(?=")', response.text).group(1)
                    action_url = re.search('(?<=id="fmHF" action=")(.+?)(?=")', response.text).group(1)
                    
                    print(f"  提取字段: ipt, pprid, uaid")
                    print(f"  action_url: {action_url[:60]}...")
                    
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
                    print(f"  跳过请求状态: {verify_response.status_code}")
                    self.save_html("after_skip_security", verify_response.text, verify_response.url)
                    
                    return_url_match = re.search('(?<="recoveryCancel":{"returnUrl":")(.+?)(?=")', verify_response.text)
                    if not return_url_match:
                        print("  [错误] 无法提取返回URL")
                        return False
                    return_url = return_url_match.group(1)
                    print(f"  返回URL: {return_url[:60]}...")
                    
                    final_response = self.session.get(
                        return_url,
                        allow_redirects=True,
                        timeout=15
                    )
                    print(f"  最终状态: {final_response.status_code}")
                    print(f"  最终URL: {final_response.url}")
                    self.save_html("after_return", final_response.text, final_response.url)
                    
                    if '#' in final_response.url and 'access_token' in final_response.url:
                        print("  ✓ 跳过成功，登录完成")
                        return True
                    else:
                        print("  ✗ 跳过后未检测到access_token")
                        return False
                except Exception as e:
                    print(f"  [错误] 跳过失败: {e}")
                    return False
            else:
                print("  ✗ 登录失败（未检测到成功标志）")
                return False
        except Exception as e:
            print(f"  [错误] {e}")
            return False

    def get_complete_cookies(self):
        try:
            print("\n[3/4] 访问m365页面获取完整Cookie...")
            m365_url = "https://m365.cloud.microsoft/search/?auth=1&origindomain=Office"
            response = self.session.get(m365_url, timeout=15, allow_redirects=True)
            print(f"  状态: {response.status_code}")
            print(f"  最终URL: {response.url[:80]}...")
            print(f"  响应长度: {len(response.text)} 字节")
            self.save_html("m365_page", response.text, response.url)
            
            cookies = {}
            for cookie in self.session.cookies:
                cookies[cookie.name] = cookie.value
            
            print(f"  ✓ 提取到 {len(cookies)} 个Cookie")
            return cookies
        except Exception as e:
            print(f"  [错误] {e}")
            return None

    def save_cookies(self, cookies, email):
        try:
            print("\n[4/4] 保存Cookie...")
            safe_email = re.sub(r'[^\w\-_\.]', '_', email)
            dest_file = f"cookies/{safe_email}.json"
            
            with open(dest_file, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, indent=2)
            
            print(f"  ✓ 已保存到: {dest_file}")
            return dest_file
        except Exception as e:
            print(f"  [错误] {e}")
            return None

    def get_elapsed_time(self):
        elapsed = time.time() - self.start_time
        return f"{elapsed:.2f}s"

def main():
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
    
    debug_input = input("调试模式? [y/N]: ").strip().lower()
    debug_mode = debug_input in ['y', 'yes']
    
    print("\n" + "="*80)
    print("Cookie 获取工具")
    print("="*80 + "\n")
    
    getter = CookieGetter(debug=debug_mode)
    
    urlpost, ppft = getter.get_login_page()
    if not urlpost or not ppft:
        print("\n[失败] 无法获取登录页面")
        return
    
    success = getter.login(email, password, urlpost, ppft)
    if not success:
        print("\n[失败] 登录失败")
        return
    
    cookies = getter.get_complete_cookies()
    if not cookies:
        print("\n[失败] 获取 Cookie 失败")
        return
    
    filepath = getter.save_cookies(cookies, email)
    if filepath:
        print(f"\n" + "="*80)
        print(f"[成功] Cookie 已保存: {filepath}")
        print(f"[成功] 用时: {getter.get_elapsed_time()}")
        print(f"[成功] Cookie 数量: {len(cookies)}")
        print("="*80)
    else:
        print("\n[失败] 保存失败")

if __name__ == '__main__':
    main()
