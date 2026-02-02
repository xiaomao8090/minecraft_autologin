#!/usr/bin/env python3
import os
import sys
from datetime import datetime, timedelta
from database import Database

db = Database()

try:
    from email_alert import EmailAlert
    email_alert = EmailAlert()
    EMAIL_ENABLED = True
except Exception as e:
    print(f"[警告] 邮件告警未配置: {e}")
    EMAIL_ENABLED = False

def check_account_health():
    accounts = db.get_all_accounts()
    total = len(accounts)
    available = sum(1 for acc in accounts if not acc.get('disabled'))
    used = total - available
    
    no_cookie = sum(1 for acc in accounts if not db.get_cookie(acc['email']))
    failed_cookie = sum(1 for acc in accounts if acc.get('cookie_status') == 'failed')
    
    return {
        'total': total,
        'available': available,
        'used': used,
        'no_cookie': no_cookie,
        'failed_cookie': failed_cookie,
        'available_rate': (available / total * 100) if total > 0 else 0
    }

def check_login_stats():
    logs = db.get_logs(1000)
    
    recent_logs = [log for log in logs if log['action'] == 'login']
    
    if not recent_logs:
        return {'total': 0, 'success': 0, 'failed': 0, 'success_rate': 0}
    
    total = len(recent_logs)
    success = sum(1 for log in recent_logs if log['status'] == 'success')
    failed = total - success
    
    return {
        'total': total,
        'success': success,
        'failed': failed,
        'success_rate': (success / total * 100) if total > 0 else 0
    }

def check_card_stats():
    cards = db.get_all_cards()
    total = len(cards)
    used = sum(1 for card in cards if card.get('used'))
    unused = total - used
    banned = sum(1 for card in cards if card.get('banned'))
    
    return {
        'total': total,
        'used': used,
        'unused': unused,
        'banned': banned,
        'usage_rate': (used / total * 100) if total > 0 else 0
    }

def send_alert(title, message, level='warning'):
    print(f"\n{'='*60}")
    print(f"[{level.upper()}] {title}")
    print(f"时间: {datetime.now()}")
    print(f"消息: {message}")
    print(f"{'='*60}\n")
    
    if EMAIL_ENABLED:
        try:
            email_alert.send_alert(title, message, level)
        except Exception as e:
            print(f"[错误] 发送邮件失败: {e}")

def monitor():
    print(f"[{datetime.now()}] 开始监控检查...\n")
    
    account_health = check_account_health()
    print(f"账号健康状态:")
    print(f"  总账号: {account_health['total']}")
    print(f"  可用: {account_health['available']} ({account_health['available_rate']:.1f}%)")
    print(f"  已用: {account_health['used']}")
    print(f"  无Cookie: {account_health['no_cookie']}")
    print(f"  Cookie失效: {account_health['failed_cookie']}")
    
    if account_health['available_rate'] < 20:
        send_alert(
            "可用账号不足",
            f"可用账号仅剩 {account_health['available']} 个 ({account_health['available_rate']:.1f}%)",
            'critical'
        )
    elif account_health['available_rate'] < 50:
        send_alert(
            "可用账号偏低",
            f"可用账号 {account_health['available']} 个 ({account_health['available_rate']:.1f}%)",
            'warning'
        )
    
    if account_health['no_cookie'] > 0:
        send_alert(
            "账号缺少Cookie",
            f"{account_health['no_cookie']} 个账号没有Cookie",
            'warning'
        )
    
    if account_health['failed_cookie'] > account_health['total'] * 0.3:
        send_alert(
            "Cookie失效率过高",
            f"{account_health['failed_cookie']} 个账号Cookie失效",
            'critical'
        )
    
    print(f"\n登录统计:")
    login_stats = check_login_stats()
    print(f"  总登录: {login_stats['total']}")
    print(f"  成功: {login_stats['success']} ({login_stats['success_rate']:.1f}%)")
    print(f"  失败: {login_stats['failed']}")
    
    if login_stats['total'] > 10 and login_stats['success_rate'] < 50:
        send_alert(
            "登录成功率过低",
            f"成功率仅 {login_stats['success_rate']:.1f}%",
            'critical'
        )
    
    print(f"\n卡密统计:")
    card_stats = check_card_stats()
    print(f"  总卡密: {card_stats['total']}")
    print(f"  已使用: {card_stats['used']} ({card_stats['usage_rate']:.1f}%)")
    print(f"  未使用: {card_stats['unused']}")
    print(f"  已封禁: {card_stats['banned']}")
    
    if card_stats['unused'] < 10:
        send_alert(
            "卡密库存不足",
            f"未使用卡密仅剩 {card_stats['unused']} 个",
            'warning'
        )
    
    print(f"\n[{datetime.now()}] 监控检查完成")
    
    if EMAIL_ENABLED and datetime.now().hour == 8:
        try:
            stats = {
                'account': account_health,
                'login': login_stats,
                'card': card_stats
            }
            email_alert.send_daily_report(stats)
            print("已发送每日报告邮件")
        except Exception as e:
            print(f"发送每日报告失败: {e}")

if __name__ == '__main__':
    monitor()
