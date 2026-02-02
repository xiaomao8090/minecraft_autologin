#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

chmod +x "$SCRIPT_DIR/monitor.py"

(crontab -l 2>/dev/null | grep -v "monitor.py"; echo "0 */6 * * * cd $SCRIPT_DIR && $SCRIPT_DIR/venv/bin/python $SCRIPT_DIR/monitor.py >> $SCRIPT_DIR/monitor.log 2>&1") | crontab -

echo "监控任务已设置"
echo "每6小时执行一次"
echo "日志文件: $SCRIPT_DIR/monitor.log"
echo ""
echo "查看当前cron任务:"
crontab -l | grep monitor.py
echo ""
echo "立即执行一次监控:"
cd "$SCRIPT_DIR" && "$SCRIPT_DIR/venv/bin/python" "$SCRIPT_DIR/monitor.py"
