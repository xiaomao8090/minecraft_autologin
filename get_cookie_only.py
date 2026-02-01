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
        os.makedirs('cookies', exist_ok=True)

    def get_login_page(self):
        try:
            response = self.session.get(LOGIN_URL, timeout=15)
            
            ppft_match = re.search(r'sFTTag.*value=\\\"(.+?)\\\"', response.text, re.S)
            if not ppft_match:
                ppft_match = re.search(r'"sFT":"(.+?)"', response.text, re.S)
            if not ppft_match:
                return None, None
            ppft = ppft_match.group(1)
            
            urlpost_match = re.search(r'"urlPost":"(.+?)"', response.text, re.S)
            if not urlpost_match:
                return None, None
            urlpost = urlpost_match.group(1)
            
            return urlpost, ppft
        except Exception as e:
            return None, None

    def login(self, email, password, urlpost, ppft):
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
            
            if '#' in response.url and 'access_token' in response.url:
                return True
            elif 'cancel?mkt=' in response.text:
                try:
                    ipt = re.search('(?<="ipt" value=")(.+?)(?=")', response.text).group(1)
                    pprid = re.search('(?<="pprid" value=")(.+?)(?=")', response.text).group(1)
                    uaid = re.search('(?<="uaid" value=")(.+?)(?=")', response.text).group(1)
                    action_url = re.search('(?<=id="fmHF" action=")(.+?)(?=")', response.text).group(1)
                    
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
                    
                    return_url_match = re.search('(?<="recoveryCancel":{"returnUrl":")(.+?)(?=")', verify_response.text)
                    if not return_url_match:
                        return False
                    return_url = return_url_match.group(1)
                    
                    final_response = self.session.get(
                        return_url,
                        allow_redirects=True,
                        timeout=15
                    )
                    
                    if '#' in final_response.url and 'access_token' in final_response.url:
                        return True
                except Exception:
                    return False
            return False
        except Exception:
            return False

    def get_complete_cookies(self):
        try:
            m365_url = "https://m365.cloud.microsoft/search/?auth=1&origindomain=Office"
            response = self.session.get(m365_url, timeout=15, allow_redirects=True)
            
            cookies = {}
            for cookie in self.session.cookies:
                cookies[cookie.name] = cookie.value
            
            return cookies
        except Exception:
            return None

    def save_cookies(self, cookies, email):
        try:
            safe_email = re.sub(r'[^\w\-_\.]', '_', email)
            dest_file = f"cookies/{safe_email}.json"
            
            with open(dest_file, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, indent=2)
            
            return dest_file
        except Exception:
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
    
    getter = CookieGetter(debug=False)
    
    urlpost, ppft = getter.get_login_page()
    if not urlpost or not ppft:
        print("[失败] 无法获取登录页面")
        return
    
    success = getter.login(email, password, urlpost, ppft)
    if not success:
        print("[失败] 登录失败")
        return
    
    cookies = getter.get_complete_cookies()
    if not cookies:
        print("[失败] 获取 Cookie 失败")
        return
    
    filepath = getter.save_cookies(cookies, email)
    if filepath:
        print(f"[成功] Cookie 已保存: {filepath}")
        print(f"[成功] 用时: {getter.get_elapsed_time()}")
        print(f"[成功] Cookie 数量: {len(cookies)}")
    else:
        print("[失败] 保存失败")

if __name__ == '__main__':
    main()
