logs: `
    <div class="module" id="logs-module">
        <h1 class="module-title">日志</h1>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>时间</th>
                        <th>IP</th>
                        <th>操作</th>
                        <th>卡密</th>
                        <th>账号</th>
                        <th>设备代码</th>
                        <th>状态</th>
                        <th>信息</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody id="logsTable"></tbody>
            </table>
        </div>
    </div>
`,

async function loadLogs() {
    try {
        const response = await fetch(`${API_URL}/logs?limit=200`);
        const logs = await response.json();
        const tbody = document.getElementById('logsTable');
        tbody.innerHTML = logs.map(log => `
            <tr class="log-${log.status}">
                <td>${new Date(log.created_at).toLocaleString('zh-CN')}</td>
                <td>${log.ip || '-'}</td>
                <td>${getActionText(log.action)}</td>
                <td>${log.card_key || '-'}</td>
                <td>${log.email || '-'}</td>
                <td>${log.device_code || '-'}</td>
                <td><span class="status-${log.status}">${getStatusText(log.status)}</span></td>
                <td class="log-message">${log.message || '-'}${log.deleted ? ' <span class="deleted-tag">已删除</span>' : ''}</td>
                <td><button class="btn-delete" onclick="deleteLog(${log.id})">删除</button></td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('加载日志失败:', error);
    }
}

function getActionText(action) {
    const actions = {
        'login': '登录',
        'card_verify': '卡密验证',
        'cookie_get': 'Cookie获取'
    };
    return actions[action] || action;
}

function getStatusText(status) {
    const statuses = {
        'success': '成功',
        'failed': '失败',
        'error': '错误'
    };
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
