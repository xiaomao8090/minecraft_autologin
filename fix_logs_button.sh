#!/bin/bash
cd /root/minecraft_autologin/static/js

# 备份
cp admin.js admin.js.bak3

# 找到loadLogs函数中的表格行生成部分，替换为包含详细按钮的版本
python3 << 'PYTHON_SCRIPT'
import re

with open('admin.js', 'r', encoding='utf-8') as f:
    content = f.read()

# 找到并替换表格行的生成部分
old_pattern = r"tbody\.innerHTML = logs\.map\(log => `[^`]*`\)\.join\(''\);"

new_code = """tbody.innerHTML = logs.map(log => `
            <tr>
                <td>\${new Date(log.created_at).toLocaleString('zh-CN')}</td>
                <td>\${log.ip || '-'}</td>
                <td>\${getActionText(log.action)}</td>
                <td style="font-size: 11px;">\${log.card_key || '-'}</td>
                <td style="font-size: 12px;">\${log.email || '-'}</td>
                <td>\${log.device_code || '-'}</td>
                <td><span style="color: \${log.status === 'success' ? '#00ff00' : log.status === 'failed' ? '#ff4444' : '#ff8800'}">\${getStatusText(log.status)}</span></td>
                <td>\${log.message || '-'}\${log.deleted ? ' <span style="color: #ff4444;">[已删除]</span>' : ''}</td>
                <td>
                    <button onclick="viewDetail(\${log.id})" style="background: #4CAF50; color: white; border: none; padding: 4px 12px; border-radius: 3px; cursor: pointer; margin-right: 5px;">详细</button>
                    <button onclick="deleteLog(\${log.id})" style="background: #ff4444; color: white; border: none; padding: 4px 12px; border-radius: 3px; cursor: pointer;">删除</button>
                </td>
            </tr>
        `).join('');"""

# 使用更宽松的匹配
if 'tbody.innerHTML = logs.map(log =>' in content:
    # 找到这个函数的开始和结束
    start = content.find('tbody.innerHTML = logs.map(log =>')
    if start != -1:
        # 找到对应的 .join('');
        end = content.find(".join('');", start)
        if end != -1:
            end += len(".join('');")
            content = content[:start] + new_code + content[end:]
            
            with open('admin.js', 'w', encoding='utf-8') as f:
                f.write(content)
            print("✓ 已更新表格行生成代码")
        else:
            print("✗ 找不到结束标记")
    else:
        print("✗ 找不到开始标记")
else:
    print("✗ 找不到目标代码")
PYTHON_SCRIPT

echo "admin.js已更新"
