#!/bin/bash
cd /root/minecraft_autologin/static/js

# 备份原文件
cp admin.js admin.js.bak

# 在modules对象中添加logs模块（在最后一个模块后）
sed -i '/^};$/i\    ,\n    logs: `\n        <div class="module" id="logs-module">\n            <h1 class="module-title">日志</h1>\n            <div class="table-container">\n                <table>\n                    <thead>\n                        <tr>\n                            <th>时间</th>\n                            <th>IP</th>\n                            <th>操作</th>\n                            <th>卡密</th>\n                            <th>账号</th>\n                            <th>设备代码</th>\n                            <th>状态</th>\n                            <th>信息</th>\n                            <th>操作</th>\n                        </tr>\n                    </thead>\n                    <tbody id="logsTable"></tbody>\n                </table>\n            </div>\n        </div>\n    `' admin.js

# 在loadModule函数的switch中添加logs case
sed -i "/case 'cards':/a\\        case 'logs':\\n            loadLogs();\\n            break;" admin.js

# 在文件末尾添加日志相关函数
cat >> admin.js << 'EOFJS'

async function loadLogs() {
    try {
        const response = await fetch(`${API_URL}/logs?limit=200`);
        const logs = await response.json();
        const tbody = document.getElementById('logsTable');
        tbody.innerHTML = logs.map(log => `
            <tr>
                <td>${new Date(log.created_at).toLocaleString('zh-CN')}</td>
                <td>${log.ip || '-'}</td>
                <td>${getActionText(log.action)}</td>
                <td style="font-size: 11px;">${log.card_key || '-'}</td>
                <td style="font-size: 12px;">${log.email || '-'}</td>
                <td>${log.device_code || '-'}</td>
                <td><span style="color: ${log.status === 'success' ? '#00ff00' : log.status === 'failed' ? '#ff4444' : '#ff8800'}">${getStatusText(log.status)}</span></td>
                <td>${log.message || '-'}${log.deleted ? ' <span style="color: #ff4444;">[已删除]</span>' : ''}</td>
                <td><button onclick="deleteLog(${log.id})" style="background: #ff4444; color: white; border: none; padding: 4px 12px; border-radius: 3px; cursor: pointer;">删除</button></td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('加载日志失败:', error);
    }
}

function getActionText(action) {
    const actions = {'login': '登录', 'card_verify': '卡密验证', 'cookie_get': 'Cookie获取'};
    return actions[action] || action;
}

function getStatusText(status) {
    const statuses = {'success': '成功', 'failed': '失败', 'error': '错误'};
    return statuses[status] || status;
}

async function deleteLog(id) {
    if (!confirm('确定删除此日志？')) return;
    try {
        await fetch(`${API_URL}/logs/${id}`, { method: 'DELETE' });
        loadLogs();
    } catch (error) {
        alert('删除失败');
    }
}
EOFJS

echo "admin.js已更新"
