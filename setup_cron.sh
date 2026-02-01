#!/bin/bash

echo "设置每日自动更新订阅天数"
echo "=========================="

SCRIPT_DIR="/root/minecraft_autologin"

(crontab -l 2>/dev/null | grep -v "daily_update.py"; echo "0 0 * * * cd $SCRIPT_DIR && $SCRIPT_DIR/venv/bin/python $SCRIPT_DIR/daily_update.py >> $SCRIPT_DIR/cron.log 2>&1") | crontab -

echo "✓ Cron任务已设置"
echo "✓ 每天凌晨0点自动更新订阅天数"
echo ""
echo "查看cron任务:"
echo "  crontab -l"
echo ""
echo "查看执行日志:"
echo "  tail -f $SCRIPT_DIR/cron.log"
