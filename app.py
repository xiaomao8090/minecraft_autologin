from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import json
import os
import re
from datetime import datetime
from pathlib import Path
import threading
import time

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

BASE_DIR = Path(__file__).parent
ACCOUNTS_FILE = BASE_DIR / "accounts" / "accounts.json"
COOKIES_DIR = BASE_DIR / "accounts" / "cookies"

def load_accounts():
    if ACCOUNTS_FILE.exists():
        with open(ACCOUNTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

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

def save_accounts(accounts):
    with open(ACCOUNTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(accounts, f, indent=2, ensure_ascii=False)

def get_available_accounts():
    accounts = load_accounts()
    available = []
    for email, data in accounts.items():
        if data.get('disabled', False):
            continue
        cookie_file = COOKIES_DIR / f"{email}.json"
        if cookie_file.exists():
            available.append({
                'email': email,
                'created_at': data.get('created_at', ''),
                'last_login': data.get('last_login')
            })
    available.sort(key=lambda x: x['created_at'])
    return available

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/admin')
def admin():
    return send_from_directory('static', 'admin.html')

@app.route('/api/available-count', methods=['GET'])
def available_count():
    available = get_available_accounts()
    return jsonify({'count': len(available)})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    device_code = data.get('device_code', '').strip().upper()
    
    if len(device_code) != 8:
        return jsonify({'success': False, 'message': '设备代码必须是8位'}), 400
    
    available = get_available_accounts()
    if not available:
        return jsonify({'success': False, 'message': '没有可用账号'}), 400
    
    account = available[0]
    email = account['email']
    
    accounts = load_accounts()
    password = accounts[email]['password']
    
    script_dir = Path(__file__).parent
    source_cookie = COOKIES_DIR / f"{email}.json"
    
    try:
        valid, msg = validate_cookie_file(source_cookie)
        if not valid:
            return jsonify({'success': False, 'message': msg}), 400
        
        import sys
        sys.path.insert(0, str(script_dir))
        from auto_login_http import AutoLoginHTTP
        
        auto_login = AutoLoginHTTP(debug=True)
        success, error_type, error_msg = auto_login.run(str(source_cookie), device_code, password, email)
        
        if success:
            accounts[email]['last_login'] = datetime.now().isoformat()
            accounts[email]['disabled'] = True
            save_accounts(accounts)
            return jsonify({'success': True, 'message': '登录成功', 'email': email})
        else:
            if error_type == 'expired_code':
                return jsonify({
                    'success': False,
                    'message': '设备代码已过期，请重新获取',
                    'email': email
                })
            elif error_type == 'invalid_cookie':
                if source_cookie.exists():
                    source_cookie.unlink()
                    print(f"[清理] 已删除失效的Cookie: {source_cookie}")
                
                accounts[email]['disabled'] = True
                accounts[email]['cookie_status'] = 'failed'
                save_accounts(accounts)
                print(f"[清理] 已停用账号: {email}")
                
                return jsonify({
                    'success': False,
                    'message': 'Cookie已失效，已自动删除并停用账号',
                    'email': email
                })
            else:
                return jsonify({
                    'success': False,
                    'message': error_msg or '登录失败',
                    'email': email
                })
    except Exception as e:
        return jsonify({'success': False, 'message': f'系统错误: {str(e)}'}), 500

@app.route('/api/accounts', methods=['GET'])
def get_accounts():
    accounts = load_accounts()
    result = []
    for email, data in accounts.items():
        cookie_file = COOKIES_DIR / f"{email}.json"
        result.append({
            'email': email,
            'password': data.get('password'),
            'level': data.get('level', 0),
            'mcname': data.get('mcname', 'Unknown'),
            'subscription': data.get('subscription', ''),
            'has_cookie': cookie_file.exists(),
            'cookie_status': data.get('cookie_status', 'none'),
            'last_login': data.get('last_login'),
            'created_at': data.get('created_at'),
            'disabled': data.get('disabled', False)
        })
    return jsonify(result)

@app.route('/api/accounts/upload', methods=['POST'])
def upload_accounts():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '没有文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': '没有选择文件'}), 400
    
    if not file.filename.endswith('.txt'):
        return jsonify({'success': False, 'message': '只支持 .txt 文件'}), 400
    
    try:
        text = file.read().decode('utf-8')
        
        import re
        accounts = load_accounts()
        
        new_count = 0
        duplicate_count = 0
        password_update_count = 0
        error_count = 0
        total_lines = 0
        
        start_time = time.time()
        
        pattern_full = r'\[(\d+)\]([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9_-]+):([^\s\|]+)\s*\|McName:([^\s\[]+)(?:\s*\[Hypixel:([^\]]+)\])?(?:\s*\[Capes:([^\]]+)\])?'
        pattern_subscription = r'([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9_-]+):([^\s\|]+)\s*\|?\s*\[?([^\]]*)\]?'
        pattern_simple = r'([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9_-]+):([^\s\|]+)'
        
        lines = text.strip().split('\n')
        processed_emails = {}
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            total_lines += 1
            
            match_full = re.search(pattern_full, line)
            if match_full:
                level, email, password, mcname, hypixel, capes = match_full.groups()
                email = email.strip()
                password = password.strip()
                
                hypixel_data = {}
                if hypixel:
                    for item in hypixel.split():
                        if ':' in item:
                            key, value = item.split(':', 1)
                            hypixel_data[key] = value.replace('-Coins', '')
                
                cape_list = [c.strip() for c in capes.split(',')] if capes else []
                
                key = f"{email}:{password}"
                if key in processed_emails:
                    duplicate_count += 1
                    continue
                
                processed_emails[key] = True
                
                if email in accounts and accounts[email]['password'] == password:
                    duplicate_count += 1
                elif email in accounts and accounts[email]['password'] != password:
                    accounts[email]['password'] = password
                    accounts[email]['level'] = int(level)
                    accounts[email]['mcname'] = mcname.strip()
                    accounts[email]['hypixel'] = hypixel_data
                    accounts[email]['capes'] = cape_list
                    password_update_count += 1
                else:
                    accounts[email] = {
                        'password': password,
                        'level': int(level),
                        'mcname': mcname.strip(),
                        'hypixel': hypixel_data,
                        'capes': cape_list,
                        'created_at': datetime.now().isoformat(),
                        'cookie_status': 'none',
                        'last_login': None
                    }
                    new_count += 1
                continue
            
            match_subscription = re.search(pattern_subscription, line)
            if match_subscription and '|' in line:
                email, password, subscription_info = match_subscription.groups()
                email = email.strip()
                password = password.strip()
                subscription_info = subscription_info.strip() if subscription_info else ''
                
                if not email or not password:
                    error_count += 1
                    continue
                
                key = f"{email}:{password}"
                if key in processed_emails:
                    duplicate_count += 1
                    continue
                
                processed_emails[key] = True
                
                if email in accounts and accounts[email]['password'] == password:
                    duplicate_count += 1
                elif email in accounts and accounts[email]['password'] != password:
                    accounts[email]['password'] = password
                    if subscription_info:
                        accounts[email]['subscription'] = subscription_info
                    password_update_count += 1
                else:
                    accounts[email] = {
                        'password': password,
                        'level': 0,
                        'mcname': 'Unknown',
                        'subscription': subscription_info if subscription_info else '',
                        'created_at': datetime.now().isoformat(),
                        'cookie_status': 'none',
                        'last_login': None
                    }
                    new_count += 1
                continue
            
            match_simple = re.search(pattern_simple, line)
            if match_simple:
                email, password = match_simple.groups()
                email = email.strip()
                password = password.strip()
                
                if not email or not password:
                    error_count += 1
                    continue
                
                key = f"{email}:{password}"
                if key in processed_emails:
                    duplicate_count += 1
                    continue
                
                processed_emails[key] = True
                
                if email in accounts and accounts[email]['password'] == password:
                    duplicate_count += 1
                elif email in accounts and accounts[email]['password'] != password:
                    accounts[email]['password'] = password
                    password_update_count += 1
                else:
                    accounts[email] = {
                        'password': password,
                        'level': 0,
                        'mcname': 'Unknown',
                        'hypixel': {},
                        'capes': [],
                        'created_at': datetime.now().isoformat(),
                        'cookie_status': 'none',
                        'last_login': None
                    }
                    new_count += 1
            else:
                error_count += 1
        
        save_accounts(accounts)
        
        elapsed_time = time.time() - start_time
        
        return jsonify({
            'success': True,
            'new_count': new_count,
            'duplicate_count': duplicate_count,
            'password_update_count': password_update_count,
            'error_count': error_count,
            'total_lines': total_lines,
            'elapsed_time': round(elapsed_time, 2)
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/accounts', methods=['POST'])
def add_accounts():
    data = request.json
    text = data.get('text', '')
    
    import re
    accounts = load_accounts()
    
    new_count = 0
    duplicate_count = 0
    password_update_count = 0
    error_count = 0
    total_lines = 0
    
    start_time = time.time()
    
    pattern_full = r'\[(\d+)\]([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9_-]+):([^\s\|]+)\s*\|McName:([^\s\[]+)(?:\s*\[Hypixel:([^\]]+)\])?(?:\s*\[Capes:([^\]]+)\])?'
    pattern_simple = r'([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9_-]+):([^\s\|]+)'
    
    lines = text.strip().split('\n')
    processed_emails = {}
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        total_lines += 1
        
        match_full = re.search(pattern_full, line)
        if match_full:
            level, email, password, mcname, hypixel, capes = match_full.groups()
            email = email.strip()
            password = password.strip()
            
            hypixel_data = {}
            if hypixel:
                for item in hypixel.split():
                    if ':' in item:
                        key, value = item.split(':', 1)
                        hypixel_data[key] = value.replace('-Coins', '')
            
            cape_list = [c.strip() for c in capes.split(',')] if capes else []
            
            key = f"{email}:{password}"
            if key in processed_emails:
                duplicate_count += 1
                continue
            
            processed_emails[key] = True
            
            if email in accounts and accounts[email]['password'] == password:
                duplicate_count += 1
            elif email in accounts and accounts[email]['password'] != password:
                accounts[email]['password'] = password
                accounts[email]['level'] = int(level)
                accounts[email]['mcname'] = mcname.strip()
                accounts[email]['hypixel'] = hypixel_data
                accounts[email]['capes'] = cape_list
                password_update_count += 1
            else:
                accounts[email] = {
                    'password': password,
                    'level': int(level),
                    'mcname': mcname.strip(),
                    'hypixel': hypixel_data,
                    'capes': cape_list,
                    'created_at': datetime.now().isoformat(),
                    'cookie_status': 'none',
                    'last_login': None
                }
                new_count += 1
            continue
        
        match_simple = re.search(pattern_simple, line)
        if match_simple:
            email, password = match_simple.groups()
            email = email.strip()
            password = password.strip()
            
            if not email or not password:
                error_count += 1
                continue
            
            key = f"{email}:{password}"
            if key in processed_emails:
                duplicate_count += 1
                continue
            
            processed_emails[key] = True
            
            if email in accounts and accounts[email]['password'] == password:
                duplicate_count += 1
            elif email in accounts and accounts[email]['password'] != password:
                accounts[email]['password'] = password
                password_update_count += 1
            else:
                accounts[email] = {
                    'password': password,
                    'level': 0,
                    'mcname': 'Unknown',
                    'hypixel': {},
                    'capes': [],
                    'created_at': datetime.now().isoformat(),
                    'cookie_status': 'none',
                    'last_login': None
                }
                new_count += 1
        else:
            error_count += 1
    
    save_accounts(accounts)
    
    elapsed_time = time.time() - start_time
    
    return jsonify({
        'success': True,
        'new_count': new_count,
        'duplicate_count': duplicate_count,
        'password_update_count': password_update_count,
        'error_count': error_count,
        'total_lines': total_lines,
        'elapsed_time': round(elapsed_time, 2)
    })

@app.route('/api/accounts/<email>', methods=['DELETE'])
def delete_account(email):
    accounts = load_accounts()
    if email in accounts:
        del accounts[email]
        save_accounts(accounts)
        
        cookie_file = COOKIES_DIR / f"{email}.json"
        if cookie_file.exists():
            cookie_file.unlink()
        
        return jsonify({'success': True})
    return jsonify({'success': False}), 404

@app.route('/api/accounts/<email>/toggle', methods=['POST'])
def toggle_account(email):
    accounts = load_accounts()
    if email in accounts:
        current_status = accounts[email].get('disabled', False)
        accounts[email]['disabled'] = not current_status
        save_accounts(accounts)
        return jsonify({'success': True, 'disabled': accounts[email]['disabled']})
    return jsonify({'success': False}), 404

@app.route('/api/cookies/get', methods=['POST'])
def get_cookies():
    data = request.json
    emails = data.get('emails', [])
    
    def process():
        accounts = load_accounts()
        total = len(emails)
        
        for i, email in enumerate(emails):
            if email not in accounts:
                socketio.emit('cookie_progress', {
                    'current': i + 1,
                    'total': total,
                    'email': email,
                    'status': 'skip',
                    'message': '账号不存在'
                })
                continue
            
            password = accounts[email]['password']
            
            socketio.emit('cookie_progress', {
                'current': i + 1,
                'total': total,
                'email': email,
                'status': 'processing',
                'message': '正在获取...'
            })
            
            import subprocess
            script_dir = Path(__file__).parent
            
            try:
                result = subprocess.run(
                    [str(script_dir / 'venv/bin/python'), str(script_dir / 'get_cookie_only.py'), f"{email}:{password}"],
                    capture_output=True,
                    text=True,
                    cwd=str(script_dir),
                    timeout=30
                )
                
                safe_email = re.sub(r'[^\w\-_\.]', '_', email)
                source_cookie = script_dir / "cookies" / f"{safe_email}.json"
                target_cookie = COOKIES_DIR / f"{email}.json"
                
                if source_cookie.exists():
                    import shutil
                    shutil.move(str(source_cookie), str(target_cookie))
                    
                    accounts[email]['cookie_status'] = 'valid'
                    accounts[email]['cookie_updated'] = datetime.now().isoformat()
                    save_accounts(accounts)
                    
                    socketio.emit('cookie_progress', {
                        'current': i + 1,
                        'total': total,
                        'email': email,
                        'status': 'success',
                        'message': '成功'
                    })
                else:
                    accounts[email]['cookie_status'] = 'failed'
                    save_accounts(accounts)
                    
                    # 提取详细错误信息
                    error_msg = '获取失败'
                    if result.returncode != 0:
                        # 从stdout中提取失败原因
                        if '登录失败' in result.stdout:
                            error_msg = '密码错误或账号异常'
                        elif '无法获取登录页面' in result.stdout:
                            error_msg = '网络错误'
                        elif '获取 Cookie 失败' in result.stdout:
                            error_msg = 'Cookie获取失败'
                        elif result.stderr:
                            error_msg = f'错误: {result.stderr[:100]}'
                        else:
                            # 显示完整输出的最后几行
                            lines = result.stdout.strip().split('\n')
                            last_lines = [l for l in lines[-5:] if l.strip()]
                            if last_lines:
                                error_msg = ' | '.join(last_lines)[:150]
                            else:
                                error_msg = f'脚本错误 (code {result.returncode})'
                    
                    socketio.emit('cookie_progress', {
                        'current': i + 1,
                        'total': total,
                        'email': email,
                        'status': 'failed',
                        'message': error_msg
                    })
            except Exception as e:
                socketio.emit('cookie_progress', {
                    'current': i + 1,
                    'total': total,
                    'email': email,
                    'status': 'failed',
                    'message': str(e)
                })
        
        socketio.emit('cookie_complete', {'success': True})
    
    thread = threading.Thread(target=process)
    thread.start()
    
    return jsonify({'success': True})

@app.route('/api/stats', methods=['GET'])
def get_stats():
    accounts = load_accounts()
    total = len(accounts)
    with_cookie = 0
    without_cookie = 0
    
    for email in accounts.keys():
        cookie_file = COOKIES_DIR / f"{email}.json"
        if cookie_file.exists():
            with_cookie += 1
        else:
            without_cookie += 1
    
    return jsonify({
        'total': total,
        'with_cookie': with_cookie,
        'without_cookie': without_cookie
    })

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5001, debug=False, allow_unsafe_werkzeug=True)
