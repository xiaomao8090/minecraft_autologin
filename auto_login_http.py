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
    def __init__(self, debug=False, max_retries=3):
        self.session = requests.Session()
        self.session.verify = False
        self.debug = debug
        self.max_retries = max_retries  # 最大重试次数
        self.start_time = time.time()
        self.step = 0
        self.stats = {
            'total_retries': 0,
            'network_errors': 0,
            'timeout_errors': 0,
            'rate_limit_errors': 0
        }
        if self.debug:
            os.makedirs('debug', exist_ok=True)
    
    def classify_error(self, response_text, response_url=""):
        """
        错误分类 - 学习自MSMC
        返回: (error_type, error_message, is_fatal)
        is_fatal: True表示致命错误，不应重试
        """
        # 1. 检查密码错误（致命错误）
        if any(keyword in response_text.lower() for keyword in [
            "password is incorrect",
            "password incorrect", 
            "incorrect password",
            "密码不正确",
            "密码错误"
        ]):
            return 'invalid_password', '密码错误', True
        
        # 2. 检查账号不存在（致命错误）
        if any(keyword in response_text.lower() for keyword in [
            "account doesn't exist",
            "account does not exist",
            "账号不存在"
        ]):
            return 'account_not_exist', '账号不存在', True
        
        # 3. 检查设备代码过期（致命错误）
        if any(keyword in response_text.lower() for keyword in [
            "code expired",
            "expired code",
            "代码已过期",
            "代码过期"
        ]):
            return 'expired_code', '设备代码已过期', True
        
        # 4. 检查2FA/安全验证（需要特殊处理）
        if any(keyword in response_url for keyword in [
            "recover?mkt",
            "identity/confirm",
            "Email/Confirm"
        ]):
            return '2fa_required', '需要双因素认证', True
        
        # 5. 检查安全信息页面（可以跳过）
        if 'cancel?mkt=' in response_url or 'cancel?mkt=' in response_text:
            return 'security_info', '安全信息页面', False
        
        # 6. 检查速率限制（应该重试）
        if '429' in str(response_text) or 'too many requests' in response_text.lower():
            return 'rate_limit', '请求过于频繁', False
        
        # 7. 检查登录成功
        if 'res=success' in response_url:
            return 'success', '登录成功', False
        
        # 8. 检查sErrTxt错误
        err_txt_match = re.search(r'"sErrTxt":"([^"]*)"', response_text)
        if err_txt_match:
            err_txt = err_txt_match.group(1)
            if err_txt:
                return 'server_error', err_txt, False
        
        # 9. 未知错误（应该重试）
        return 'unknown_error', '未知错误', False
    
    def request_with_retry(self, method, url, **kwargs):
        """
        带重试机制的请求 - 学习自MSMC
        """
        tries = 0
        last_error = None
        
        while tries < self.max_retries:
            try:
                # 设置超时
                if 'timeout' not in kwargs:
                    kwargs['timeout'] = 15
                
                # 发送请求
                if method.upper() == 'GET':
                    response = self.session.get(url, **kwargs)
                elif method.upper() == 'POST':
                    response = self.session.post(url, **kwargs)
                else:
                    raise ValueError(f"不支持的HTTP方法: {method}")
                
                # 检查速率限制
                if response.status_code == 429:
                    self.stats['rate_limit_errors'] += 1
                    wait_time = 5 * (tries + 1)  # 递增等待时间
                    if self.debug:
                        print(f"  [重试] 速率限制，等待 {wait_time} 秒...")
                    time.sleep(wait_time)
                    tries += 1
                    self.stats['total_retries'] += 1
                    continue
                
                # 请求成功
                return response, None
                
            except requests.exceptions.Timeout:
                self.stats['timeout_errors'] += 1
                last_error = 'timeout'
                if self.debug:
                    print(f"  [重试] 超时 (尝试 {tries + 1}/{self.max_retries})")
                
            except requests.exceptions.ConnectionError:
                self.stats['network_errors'] += 1
                last_error = 'connection_error'
                if self.debug:
                    print(f"  [重试] 连接错误 (尝试 {tries + 1}/{self.max_retries})")
                
            except Exception as e:
                last_error = str(e)
                if self.debug:
                    print(f"  [重试] 异常: {e} (尝试 {tries + 1}/{self.max_retries})")
            
            tries += 1
            self.stats['total_retries'] += 1
            
            # 重试前等待
            if tries < self.max_retries:
                time.sleep(2 * tries)  # 递增等待时间
        
        # 所有重试都失败
        return None, last_error
    
    def check_error_in_response(self, response):
        """保持向后兼容"""
        error_type, error_msg, is_fatal = self.classify_error(response.text, response.url)
        if error_type in ['invalid_password', 'expired_code', 'unknown_error']:
            return error_type, error_msg
        return None, None
    
    def check_success_in_response(self, response):
        if '800478C7' in response.text:
            return True
        if 'res=success' in response.url:
            return True
        if '大功告成' in response.text:
            return True
        return False
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
        
        # 使用重试机制访问设备代码页面
        response, error = self.request_with_retry('GET', "https://login.live.com/oauth20_remoteconnect.srf")
        
        if response is None:
            print(f"[错误] 访问设备代码页面失败: {error}")
            return False
        
        try:
            print(f"  状态: {response.status_code}")
            print(f"  URL: {response.url}")
            print(f"  响应长度: {len(response.text)} 字节")
            self.save_html("device_code_page", response.text, response.url)
            
            # 检查错误
            error_type, error_msg, is_fatal = self.classify_error(response.text, response.url)
            if is_fatal:
                print(f"[错误] {error_msg}")
                return False
            
            ppft_match = re.search(r'"sFT":"([^"]+)"', response.text)
            if not ppft_match:
                ppft_match = re.search(r'value="([^"]+)"[^>]*name="PPFT"', response.text)
            if not ppft_match:
                ppft_match = re.search(r'name="PPFT"[^>]*value="([^"]+)"', response.text)
            if not ppft_match:
                print("[错误] 无法提取 PPFT")
                return False
            ppft = ppft_match.group(1)
            print(f"  PPFT: {ppft[:20]}...")
            
            urlpost_match = re.search(r'"urlPost":"([^"]+)"', response.text)
            if not urlpost_match:
                print("[错误] 无法提取 urlPost")
                return False
            urlpost = urlpost_match.group(1).replace('&amp;', '&')
            print(f"  urlPost: {urlpost[:60]}...")
            
            print(f"\n[2/6] 提交设备代码...")
            data = {
                'otc': device_code,
                'PPFT': ppft
            }
            
            # 使用重试机制提交设备代码
            response, error = self.request_with_retry(
                'POST',
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
            print(f"  最终 URL: {response.url}")
            print(f"  响应长度: {len(response.text)} 字节")
            self.save_html("after_code_submit", response.text, response.url)
            
            error_type, error_msg = self.check_error_in_response(response)
            if error_type == 'expired_code':
                print(f"  ✗ 设备代码已过期: {error_msg}")
                return 'expired_code'
            
            if self.check_success_in_response(response):
                print(f"  ✓ 设备代码提交成功")
                print(f"  ✓ Microsoft 已接受授权请求")
                return True
            elif 'Sign in to your account' in response.text or 'Enter password' in response.text:
                print(f"  ⚠ 需要额外验证（密码）")
                return response
            elif 'cancel?mkt=' in response.text:
                print(f"  ⚠ 需要额外验证（安全信息）")
                return response
            else:
                print(f"  ✗ 未知响应")
                if error_type:
                    print(f"  错误信息: {error_msg}")
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
            print(f"  最终 URL: {response.url}")
            self.save_html("after_password_submit", response.text, response.url)
            
            if 'fmHF' in response.text and 'DoSubmit' in response.text:
                print(f"\n[5/6] 检测到自动提交表单...")
                action_match = re.search(r'id="fmHF"[^>]*action="([^"]+)"', response.text)
                if action_match:
                    action_url = action_match.group(1).replace('&amp;', '&')
                    print(f"  表单目标: {action_url[:80]}...")
                    
                    form_data = {}
                    for match in re.finditer(r'name="([^"]+)"[^>]*value="([^"]*)"', response.text):
                        form_data[match.group(1)] = match.group(2)
                    
                    print(f"  提交表单字段: {len(form_data)} 个")
                    
                    form_response = self.session.post(
                        action_url,
                        data=form_data,
                        headers={
                            'Content-Type': 'application/x-www-form-urlencoded',
                            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                        },
                        allow_redirects=True,
                        timeout=15
                    )
                    print(f"  状态: {form_response.status_code}")
                    print(f"  最终 URL: {form_response.url}")
                    self.save_html("after_form_submit", form_response.text, form_response.url)
                    response = form_response
            
            if self.check_success_in_response(response):
                print(f"  ✓ 验证成功")
                return True
            
            if 'cancel?mkt=' in response.text or 'cancel' in response.url.lower():
                print(f"\n[5/6] 检测到安全信息页面，点击下一步跳过...")
                self.save_html("security_cancel_page", response.text, response.url)
                
                try:
                    ru_match = re.search(r'[?&]ru=([^&"\']+)', response.url)
                    if ru_match:
                        import urllib.parse
                        return_url = urllib.parse.unquote(ru_match.group(1))
                        print(f"  提取到返回URL: {return_url[:80]}...")
                        
                        skip_response = self.session.get(
                            return_url,
                            allow_redirects=True,
                            timeout=15
                        )
                        print(f"  ✓ 已点击下一步")
                        print(f"  跳过后URL: {skip_response.url[:80]}...")
                        print(f"  响应长度: {len(skip_response.text)} 字节")
                        self.save_html("after_cancel_skip", skip_response.text, skip_response.url)
                        
                        if self.check_success_in_response(skip_response):
                            print(f"  ✓ 检测到授权成功标识")
                            return True
                        elif 'consent' in skip_response.url.lower() or 'Consent' in skip_response.url:
                            print(f"  ✓ 跳过成功，检测到同意页面")
                            response = skip_response
                        elif 'DoSubmit' in skip_response.text and 'fmHF' in skip_response.text:
                            print(f"  检测到自动提交表单，提取表单数据...")
                            action_match = re.search(r'id="fmHF"[^>]*action="([^"]+)"', skip_response.text)
                            if action_match:
                                action_url = action_match.group(1).replace('&amp;', '&')
                                print(f"  表单目标: {action_url[:80]}...")
                                
                                form_data = {}
                                for match in re.finditer(r'name="([^"]+)"[^>]*value="([^"]*)"', skip_response.text):
                                    form_data[match.group(1)] = match.group(2)
                                
                                print(f"  提交表单字段: {len(form_data)} 个")
                                
                                form_response = self.session.post(
                                    action_url,
                                    data=form_data,
                                    headers={
                                        'Content-Type': 'application/x-www-form-urlencoded',
                                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                                    },
                                    allow_redirects=True,
                                    timeout=15
                                )
                                print(f"  状态: {form_response.status_code}")
                                print(f"  最终 URL: {form_response.url[:80]}...")
                                self.save_html("after_auto_form_submit", form_response.text, form_response.url)
                                
                                if self.check_success_in_response(form_response):
                                    print(f"  ✓ 授权完成")
                                    return True
                                elif 'consent' in form_response.url.lower() or 'Consent' in form_response.url:
                                    print(f"  ✓ 进入同意页面")
                                    response = form_response
                                else:
                                    print(f"  ⚠ 表单提交后状态未知")
                                    return False
                            else:
                                print(f"  ⚠ 无法提取表单action")
                                return False
                        else:
                            print(f"  ⚠ 跳过后未检测到授权完成")
                            print(f"  可能需要手动在HMCL点击'允许'")
                            return False
                    else:
                        print(f"  ⚠ 无法从URL提取返回地址")
                        return False
                except Exception as e:
                    print(f"  ⚠ 跳过处理异常: {e}")
                    if self.debug:
                        import traceback
                        traceback.print_exc()
                    return False
            
            if 'consent' in response.url.lower() or 'Consent' in response.url:
                print(f"\n[6/6] 处理同意页面...")
                
                server_data_match = re.search(r'var ServerData=({.+?});', response.text, re.DOTALL)
                if not server_data_match:
                    print(f"  ✗ 无法提取 ServerData")
                    return False
                
                server_data_str = server_data_match.group(1)
                
                canary_match = re.search(r'"sCanary":"([^"]+)"', server_data_str)
                if not canary_match:
                    print(f"  ✗ 无法提取 Canary 令牌")
                    return False
                
                canary_raw = canary_match.group(1)
                canary = canary_raw.replace('\\u002b', '+').replace('\\u002f', '/').replace('\\u003d', '=').replace('\\u003b', ';').replace('\\u003a', ':')
                
                print(f"  Canary: {canary[:50]}...")
                
                consent_data = {
                    'ucaction': 'Yes',
                    'client_id': '000000004C794E0A',
                    'scope': '000000004C794E0A:XboxLive.signin 000000004C794E0A:int.offline_access',
                    'cscope': '',
                    'canary': canary
                }
                
                print(f"  提交同意请求...")
                consent_response = self.session.post(
                    response.url,
                    data=consent_data,
                    headers={
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                        'Referer': response.url,
                        'Origin': 'https://account.live.com'
                    },
                    allow_redirects=True,
                    timeout=15
                )
                
                print(f"  状态: {consent_response.status_code}")
                print(f"  最终 URL: {consent_response.url[:80]}...")
                self.save_html("after_consent_submit", consent_response.text, consent_response.url)
                
                if self.check_success_in_response(consent_response):
                    print(f"  ✓ 同意成功")
                    return True
                else:
                    print(f"  ⚠ 同意响应未知")
                    if self.debug:
                        print(f"  响应长度: {len(consent_response.text)} 字节")
                    return False
            
            print(f"\n[警告] 未检测到同意页面，但也未完成授权")
            print(f"  当前URL: {response.url[:80]}...")
            if self.check_success_in_response(response):
                print(f"  ✓ 检测到授权成功标识")
                return True
            else:
                print(f"  ✗ 未检测到授权成功标识")
                return False
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
        print(f"[信息] 账号: {email}")
        print(f"[信息] 开始处理...\n")
        if not self.load_cookies(cookie_file):
            return False, 'invalid_cookie', 'Cookie加载失败'
        
        result = self.submit_device_code(device_code)
        
        if result is True:
            print(f"\n[成功] Microsoft 授权完成")
            print(f"[信息] 等待 HMCL 完成登录...")
            time.sleep(3)
            print(f"[成功] 登录完成")
            print(f"[成功] 用时: {self.get_elapsed_time()}")
            print(f"[成功] HMCL 应该已经自动登录")
            return True, None, None
        elif result == 'expired_code':
            print(f"\n[失败] 设备代码已过期")
            return False, 'expired_code', '设备代码已过期'
        elif result is False:
            print(f"\n[失败] 登录失败")
            return False, 'unknown_error', '登录失败'
        else:
            print(f"\n[3/6] 处理额外验证...")
            verify_result = self.handle_additional_verification(result, password, email)
            if verify_result is True:
                print(f"\n[成功] Microsoft 授权完成")
                print(f"[信息] 等待 HMCL 完成登录...")
                time.sleep(3)
                print(f"[成功] 登录完成")
                print(f"[成功] 用时: {self.get_elapsed_time()}")
                print(f"[成功] HMCL 应该已经自动登录")
                return True, None, None
            else:
                print(f"\n[失败] 额外验证失败")
                print(f"[失败] Cookie 可能已过期或账号需要 2FA")
                return False, 'invalid_cookie', 'Cookie已失效或需要2FA'
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
    success, error_type, error_msg = auto_login.run(cookie_file, device_code, password, email)
    
    # 显示统计信息
    if auto_login.stats['total_retries'] > 0:
        print(f"\n[统计] 总重试次数: {auto_login.stats['total_retries']}")
        if auto_login.stats['network_errors'] > 0:
            print(f"[统计] 网络错误: {auto_login.stats['network_errors']}")
        if auto_login.stats['timeout_errors'] > 0:
            print(f"[统计] 超时错误: {auto_login.stats['timeout_errors']}")
        if auto_login.stats['rate_limit_errors'] > 0:
            print(f"[统计] 速率限制: {auto_login.stats['rate_limit_errors']}")
    
    if success:
        print("\n✓ 处理完成")
        print("✓ 请检查 HMCL 是否已登录成功")
    else:
        print("\n✗ 处理失败")
        if error_type:
            print(f"✗ 错误类型: {error_type}")
        if error_msg:
            print(f"✗ 错误信息: {error_msg}")
        if debug_mode:
            print("✗ 请检查 debug/ 文件夹中的 HTML 文件")
if __name__ == '__main__':
    import sys
    if len(sys.argv) == 5:
        cookie_file = sys.argv[1]
        device_code = sys.argv[2]
        password = sys.argv[3]
        email = sys.argv[4]
        
        auto_login = AutoLoginHTTP(debug=False)
        success, error_type, error_msg = auto_login.run(cookie_file, device_code, password, email)
        
        if success:
            print("\n✓ 处理完成")
            print("✓ HMCL 应该已登录成功")
            sys.exit(0)
        else:
            print("\n✗ 处理失败")
            if error_type:
                print(f"✗ 错误类型: {error_type}")
            if error_msg:
                print(f"✗ 错误信息: {error_msg}")
            sys.exit(1)
    else:
        main()
