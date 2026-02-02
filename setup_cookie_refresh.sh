#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

chmod +x "$SCRIPT_DIR/refresh_cookies.py"

(crontab -l 2>/dev/null | grep -v "refresh_cookies.py"; echo "0 2 * * * cd $SCRIPT_DIR && $SCRIPT_DIR/venv/bin/python $SCRIPT_DIR/refresh_cookies.py >> $SCRIPT_DIR/cookie_refresh.log 2>&1") | crontab -

echo "Cookie自动刷新任务已设置"
echo "每天凌晨2点执行"
echo "日志文件: $SCRIPT_DIR/cookie_refresh.log"
echo ""
echo "查看当前cron任务:"
crontab -l | grep refresh_cookies.py
