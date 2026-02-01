#!/bin/bash
cd /root/minecraft_autologin/static/js

# 恢复备份
cp admin.js.bak2 admin.js

# 找到loadLogs函数并在其后添加正确的代码
cat >> admin.js << 'EOFJS'

async function loadLogs() {
    try {
        const response = await fetch(`${API_URL}/logs?limit=200`);
        const logs = await response.json();
        const tbody = document.getElementById('logsTable');
        tbody.innerHTML = logs.map(log => {
            const time = new Date(log.created_at).toLocaleString('zh-CN');
            const ip = log.ip || '-';
            const action = getActionText(log.action);
            const cardKey = log.card_key || '-';
            const email = log.email || '-';
            const deviceCode = log.device_code || '-';
            const statusColor = log.status === 'success' ? '#00ff00' : log.status === 'failed' ? '#ff4444' : '#ff8800';
            const statusText = getStatusText(log.status);
            const message = log.message || '-';
            const deletedTag = log.deleted ? ' <span style="color: #ff4444;">[已删除]</span>' : '';
            
            return `
                <tr>
                    <td>${time}</td>
                    <td>${ip}</td>
                    <td>${action}</td>
                    <td style="font-size: 11px;">${cardKey}</td>
                    <td style="font-size: 12px;">${email}</td>
                    <td>${deviceCode}</td>
                    <td><span style="color: ${statusColor}">${statusText}</span></td>
                    <td>${message}${deletedTag}</td>
                    <td>
                        <button onclick="viewDetail(${log.id})" style="background: #4CAF50; color: white; border: none; padding: 4px 12px; border-radius: 3px; cursor: pointer; margin-right: 5px;">详细</button>
                        <button onclick="deleteLog(${log.id})" style="background: #ff4444; color: white; border: none; padding: 4px 12px; border-radius: 3px; cursor: pointer;">删除</button>
                    </td>
                </tr>
            `;
        }).join('');
    } catch (error) {
        console.error('加载日志失败:', error);
    }
}
EOFJS

echo "✓ admin.js已修复"
