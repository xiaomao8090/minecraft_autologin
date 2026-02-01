#!/bin/bash
cd /root/minecraft_autologin

# 添加detail_log字段到logs表
mysql -u minecraft_autologin -p45004879 minecraft_autologin -e "ALTER TABLE logs ADD COLUMN IF NOT EXISTS detail_log LONGTEXT AFTER message;"

# 更新admin.js中的loadLogs函数
cd static/js
cp admin.js admin.js.bak2

# 替换loadLogs函数中的表格行生成部分
cat > /tmp/new_logs_row.txt << 'EOF'
            <tr>
                <td>${new Date(log.created_at).toLocaleString('zh-CN')}</td>
                <td>${log.ip || '-'}</td>
                <td>${getActionText(log.action)}</td>
                <td style="font-size: 11px;">${log.card_key || '-'}</td>
                <td style="font-size: 12px;">${log.email || '-'}</td>
                <td>${log.device_code || '-'}</td>
                <td><span style="color: ${log.status === 'success' ? '#00ff00' : log.status === 'failed' ? '#ff4444' : '#ff8800'}">${getStatusText(log.status)}</span></td>
                <td>${log.message || '-'}${log.deleted ? ' <span style="color: #ff4444;">[已删除]</span>' : ''}</td>
                <td>
                    ${log.detail_log ? '<button onclick="viewDetail(' + log.id + ')" style="background: #4CAF50; color: white; border: none; padding: 4px 12px; border-radius: 3px; cursor: pointer; margin-right: 5px;">详细</button>' : ''}
                    <button onclick="deleteLog(' + log.id + ')" style="background: #ff4444; color: white; border: none; padding: 4px 12px; border-radius: 3px; cursor: pointer;">删除</button>
                </td>
            </tr>
EOF

# 添加viewDetail函数
cat >> admin.js << 'EOFJS'

async function viewDetail(id) {
    try {
        const response = await fetch(`${API_URL}/logs/${id}/detail`);
        const data = await response.json();
        if (data.success) {
            const modal = document.createElement('div');
            modal.style.cssText = 'position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.8); display: flex; align-items: center; justify-content: center; z-index: 10000;';
            modal.innerHTML = `
                <div style="background: #111; border: 1px solid #333; border-radius: 8px; max-width: 90%; max-height: 90%; overflow: auto; padding: 20px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                        <h2 style="color: #fff; margin: 0;">详细日志</h2>
                        <button onclick="this.closest('div').parentElement.remove()" style="background: #ff4444; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">关闭</button>
                    </div>
                    <pre style="background: #000; color: #0f0; padding: 15px; border-radius: 4px; overflow: auto; max-height: 70vh; font-family: monospace; font-size: 12px; line-height: 1.5;">${data.detail.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</pre>
                </div>
            `;
            document.body.appendChild(modal);
            modal.onclick = (e) => { if (e.target === modal) modal.remove(); };
        } else {
            alert('无法获取详细日志');
        }
    } catch (error) {
        alert('获取详细日志失败');
    }
}
EOFJS

echo "admin.js已更新，添加了详细日志查看功能"
