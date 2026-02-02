#!/usr/bin/env python3
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

class EmailAlert:
    def __init__(self):
        self.smtp_server = 'smtp.gmail.com'
        self.smtp_port = 587
        self.sender_email = os.environ.get('ALERT_EMAIL')
        self.sender_password = os.environ.get('ALERT_EMAIL_PASSWORD')
        receiver_emails = os.environ.get('ALERT_RECEIVER_EMAIL', self.sender_email)
        
        if receiver_emails:
            self.receiver_emails = [email.strip() for email in receiver_emails.split(',')]
        else:
            self.receiver_emails = [self.sender_email]
        
        if not self.sender_email or not self.sender_password:
            raise ValueError("请设置 ALERT_EMAIL 和 ALERT_EMAIL_PASSWORD 环境变量")
    
    def send_alert(self, subject, message, level='warning'):
        try:
            for receiver_email in self.receiver_emails:
                msg = MIMEMultipart('alternative')
                msg['From'] = self.sender_email
                msg['To'] = receiver_email
                msg['Subject'] = f"[{level.upper()}] {subject}"
            
            level_colors = {
                'info': '#3b82f6',
                'warning': '#f59e0b',
                'critical': '#ef4444'
            }
            color = level_colors.get(level, '#6b7280')
            
            html_content = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: {color}; color: white; padding: 20px; border-radius: 5px 5px 0 0; }}
                    .content {{ background: #f9fafb; padding: 20px; border: 1px solid #e5e7eb; border-top: none; }}
                    .footer {{ background: #f3f4f6; padding: 15px; text-align: center; font-size: 12px; color: #6b7280; border-radius: 0 0 5px 5px; }}
                    .info {{ background: white; padding: 15px; margin: 10px 0; border-left: 4px solid {color}; }}
                    h1 {{ margin: 0; font-size: 24px; }}
                    .time {{ font-size: 14px; opacity: 0.9; margin-top: 5px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>{subject}</h1>
                        <div class="time">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
                    </div>
                    <div class="content">
                        <div class="info">
                            {message.replace(chr(10), '<br>')}
                        </div>
                    </div>
                    <div class="footer">
                        Minecraft Auto Login 监控系统
                    </div>
                </div>
            </body>
            </html>
            """
            
            text_content = f"""
{subject}
{'='*60}
时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
级别: {level.upper()}

{message}

---
Minecraft Auto Login 监控系统
            """
            
            part1 = MIMEText(text_content, 'plain')
            part2 = MIMEText(html_content, 'html')
            
            msg.attach(part1)
            msg.attach(part2)
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            print(f"[邮件] 已发送告警邮件到 {receiver_email}: {subject}")
            return True
        except Exception as e:
            print(f"[错误] 发送邮件失败: {e}")
            return False
    
    def send_daily_report(self, stats):
        subject = "每日系统报告"
        
        message = f"""
账号状态:
  总账号: {stats['account']['total']}
  可用: {stats['account']['available']} ({stats['account']['available_rate']:.1f}%)
  已用: {stats['account']['used']}
  无Cookie: {stats['account']['no_cookie']}
  Cookie失效: {stats['account']['failed_cookie']}

登录统计:
  总登录: {stats['login']['total']}
  成功: {stats['login']['success']} ({stats['login']['success_rate']:.1f}%)
  失败: {stats['login']['failed']}

卡密统计:
  总卡密: {stats['card']['total']}
  已使用: {stats['card']['used']} ({stats['card']['usage_rate']:.1f}%)
  未使用: {stats['card']['unused']}
  已封禁: {stats['card']['banned']}
        """
        
        return self.send_alert(subject, message, 'info')
    
    def send_login_success(self, card_key, email, device_code, ip):
        subject = "用户登录成功"
        message = f"""有用户成功登录

卡密: {card_key}
使用账号: {email}
设备代码: {device_code}
IP地址: {ip}
时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        return self.send_alert(subject, message, 'info')
    
    def send_accounts_imported(self, new_count, duplicate_count, password_update_count, error_count, total_lines):
        subject = "账号导入完成"
        message = f"""账号导入操作完成

总行数: {total_lines}
新增账号: {new_count}
重复账号: {duplicate_count}
密码更新: {password_update_count}
错误行数: {error_count}

成功率: {((new_count + password_update_count) / total_lines * 100):.1f}%
        """
        level = 'info' if error_count == 0 else 'warning'
        return self.send_alert(subject, message, level)

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 3:
        print("用法: python email_alert.py <subject> <message> [level]")
        sys.exit(1)
    
    subject = sys.argv[1]
    message = sys.argv[2]
    level = sys.argv[3] if len(sys.argv) > 3 else 'warning'
    
    alert = EmailAlert()
    alert.send_alert(subject, message, level)
