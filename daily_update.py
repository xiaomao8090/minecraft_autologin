#!/usr/bin/env python3
from database import Database
from datetime import datetime

db = Database()

print(f"[{datetime.now()}] 开始更新订阅天数...")
count = db.update_subscription_days()
print(f"[{datetime.now()}] 已更新 {count} 个账号")
