#!/usr/bin/env python3
import requests
import re
import json
import time
import os
import urllib3
import warnings
urllib3.disable_warnings()
warnings.filterwarnings("ignore")
class AutoLoginHTTP:
    def __init__(self, debug=False):
        self.session = requests.Session()
        self.session.verify = False
        self.debug = debug
        self.start_time = time.time()
        self.step = 0
        if self.debug:
            os.makedirs('debug', exist_ok=True)
    def save_html(self, step_name, content, url=""):
        if not self.debug:
            return
        self.step += 1
        filename = f"debug/{self.step:02d}_{step_name}.html"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"<!-- URL: {url} -->\n")
                f.write(f"<!-- Step: {step_name} -->\n\n")
                f.write(content)
            print(f"  已保存: {filename}")
        except Exception as e:
            print(f"[错误] 保存失败: {e}")
    def load_cookies(self, cookie_file):
        try:
            with open(cookie_file, 'r') as f:
                cookies_dict = json.load(f)
            for name, value in cookies_dict.items():
                self.session.cookies.set(name, value, domain='.login.live.com')
            print(f"[信息] 已加载 {len(cookies_dict)} 个 Cookie\n")
            return True
        except Exception as e:
            print(f"[错误] 加载 Cookie 失败: {e}")
            return False
    def submit_device_code(self, device_code):
        print(f"[1/6] 访问设备代码页面...")
        try:
            url = "https://login.live.com/oauth20_remoteconnect.srf"
            response = self.session.get(url, timeout=15)
            print(f"  状态: {response.status_code}")
            self.save_html("device_code_page", response.text, response.url)
            ppft_match = re.search(r'"sFT":"([^"]+)"', response.text)
            if not ppft_match:
                ppft_match = re.search(r'value="([^"]+)"[^>]*name="PPFT"', response.text)
            if not ppft_match:
                ppft_match = re.search(r'name="PPFT"[^>]*value="([^"]+)"', response.text)
            if not ppft_match:
                print("[错误] 无法提取 PPFT")
                return False
            ppft = ppft_match.group(1)
            urlpost_match = re.search(r'"urlPost":"([^"]+)"', response.text)
            if not urlpost_match:
                print("[错误] 无法提取 urlPost")
                return False
            urlpost = urlpost_match.group(1).replace('&amp;', '&')
            print(f"\n[2/6] 提交设备代码...")
            data = {
                'otc': device_code,
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
            self.save_html("after_code_submit", response.text, response.url)
            if '800478C7' in response.text:
                print(f"  设备代码提交成功")
                return True
            else:
                print(f"  需要额外验证")
                return response
        except Exception as e:
            print(f"[错误] 提交失败: {e}")
            if self.debug:
                import traceback
                traceback.print_exc()
            return False
    def handle_additional_verification(self, response, password, email):
        print(f"\n[3/6] 获取账号信息...")
        try:
            server_data_match = re.search(r'var ServerData = ({.+?});', response.text, re.DOTALL)
            if not server_data_match:
                print("[错误] 无法提取 ServerData")
                return False
            server_data_str = server_data_match.group(1)
            urlpost_match = re.search(r'"urlPost":"([^"]+)"', server_data_str)
            if not urlpost_match:
                print("[错误] 无法提取 urlPost")
                return False
            urlpost = urlpost_match.group(1).replace('\\u0026', '&')
            ppft_match = re.search(r'"sFTTag":"<input[^>]*value=\\"([^"]+)\\"', server_data_str)
            if not ppft_match:
                ppft_match = re.search(r'"sFT":"([^"]+)"', server_data_str)
            if not ppft_match:
                print("[错误] 无法提取 PPFT")
                return False
            ppft = ppft_match.group(1).replace('\\u0026', '&')
            print(f"\n[4/6] 提交密码...")
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
            self.save_html("after_password_submit", response.text, response.url)
            if 'cancel?mkt=' in response.text or 'cancel' in response.url.lower():
                print(f"\n[5/6] 跳过安全信息更新...")
                try:
                    ipt = re.search(r'(?<="ipt" value=")(.+?)(?=")', response.text).group(1)
                    pprid = re.search(r'(?<="pprid" value=")(.+?)(?=")', response.text).group(1)
                    uaid = re.search(r'(?<="uaid" value=")(.+?)(?=")', response.text).group(1)
                    action_url = re.search(r'(?<=id="fmHF" action=")(.+?)(?=")', response.text).group(1)
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
                    self.save_html("verify_response", verify_response.text, verify_response.url)
                    return_url_match = re.search(r'(?<="recoveryCancel":\{"returnUrl":")(.+?)(?=")', verify_response.text)
                    if return_url_match:
                        return_url = return_url_match.group(1)
                        response = self.session.get(
                            return_url,
                            allow_redirects=True,
                            timeout=15
                        )
                        print(f"  已跳过")
                        self.save_html("after_security_skip", response.text, response.url)
                    else:
                        print(f"  无法提取返回 URL")
                except Exception as e:
                    print(f"  跳过失败: {e}")
                    if self.debug:
                        import traceback
                        traceback.print_exc()
            if 'consent' in response.url.lower() or '是否允许' in response.text or 'Accept' in response.text:
                print(f"\n[6/6] 接受权限请求...")
                ppft_match = re.search(r'name="PPFT"[^>]*value="([^"]+)"', response.text)
                if not ppft_match:
                    ppft_match = re.search(r'"sFT":"([^"]+)"', response.text)
                urlpost_match = re.search(r'"urlPost":"([^"]+)"', response.text)
                if not urlpost_match:
                    urlpost_match = re.search(r'action="([^"]+)"', response.text)
                if ppft_match and urlpost_match:
                    ppft = ppft_match.group(1)
                    urlpost = urlpost_match.group(1).replace('&amp;', '&').replace('\\u0026', '&')
                    data = {
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
                    print(f"  已接受")
                    self.save_html("after_consent_accept", response.text, response.url)
                else:
                    print(f"  无法提取表单数据")
            return True
        except Exception as e:
            print(f"[错误] 额外验证失败: {e}")
            if self.debug:
                import traceback
                traceback.print_exc()
            return False
    def run(self, cookie_file, device_code, password, email):
        print("="*80)
        print("HTTP API 自动登录")
        print("="*80)
        print(f"\n[信息] Cookie 文件: {cookie_file}")
        print(f"[信息] 设备代码: {device_code}")
        print(f"[信息] 开始处理...\n")
        if not self.load_cookies(cookie_file):
            return False
        result = self.submit_device_code(device_code)
        if result is True:
            print(f"\n[成功] 登录完成")
            print(f"[成功] 用时: {self.get_elapsed_time()}")
            return True
        elif result is False:
            print(f"\n[失败] 登录失败")
            return False
        else:
            if self.handle_additional_verification(result, password, email):
                print(f"\n[成功] 登录完成")
                print(f"[成功] 用时: {self.get_elapsed_time()}")
                return True
            else:
                print(f"\n[失败] 额外验证失败")
                return False
    def get_elapsed_time(self):
        elapsed = time.time() - self.start_time
        return f"{elapsed:.2f}s"
def list_cookie_files():
    cookie_dir = "cookies"
    if not os.path.exists(cookie_dir):
        return []
    files = []
    for filename in os.listdir(cookie_dir):
        if filename.endswith('.json'):
            filepath = os.path.join(cookie_dir, filename)
            files.append(filepath)
    return sorted(files)
def main():
    cookie_files = list_cookie_files()
    if not cookie_files:
        print("[错误] 没有找到 Cookie 文件")
        print("请先运行 get_cookie_only.py 获取 Cookie")
        return
    if len(cookie_files) == 1:
        cookie_file = cookie_files[0]
        print(f"使用 Cookie: {os.path.basename(cookie_file)}")
    else:
        print(f"\n找到 {len(cookie_files)} 个 Cookie 文件:\n")
        for i, filepath in enumerate(cookie_files, 1):
            print(f"{i}. {os.path.basename(filepath)}")
        try:
            choice = int(input(f"\n选择 Cookie 文件 [1-{len(cookie_files)}]: ").strip())
            if choice < 1 or choice > len(cookie_files):
                print("[错误] 无效的选择")
                return
            cookie_file = cookie_files[choice - 1]
        except (ValueError, KeyboardInterrupt):
            print("\n[错误] 无效的输入")
            return
    device_code = input("\n请输入设备代码 (8位): ").strip().upper()
    if len(device_code) != 8:
        print("[错误] 设备代码必须是 8 位")
        return
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
    print()
    auto_login = AutoLoginHTTP(debug=debug_mode)
    success = auto_login.run(cookie_file, device_code, password, email)
    if success:
        print("\n✓ 处理完成")
        print("✓ 请检查 HMCL 是否已登录成功")
    else:
        print("\n✗ 处理失败")
        if debug_mode:
            print("✗ 请检查 debug/ 文件夹中的 HTML 文件")
if __name__ == '__main__':
    main()
