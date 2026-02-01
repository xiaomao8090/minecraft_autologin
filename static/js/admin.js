const API_URL = window.location.origin + '/api';
const socket = io(window.location.origin);

const modules = {
    stats: `
        <div class="module active" id="stats-module">
            <h1 class="module-title">统计</h1>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">总账号数</div>
                    <div class="stat-value" id="totalAccounts">0</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">有 Cookie</div>
                    <div class="stat-value" id="withCookie">0</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">无 Cookie</div>
                    <div class="stat-value" id="withoutCookie">0</div>
                </div>
            </div>
            <div class="chart-container">
                <canvas id="loginChart"></canvas>
            </div>
        </div>
    `,
    
    import: `
        <div class="module" id="import-module">
            <h1 class="module-title">导入账号</h1>
            
            <div class="import-methods">
                <button class="btn active" id="textImportBtn">文本导入</button>
                <button class="btn btn-secondary" id="fileImportBtn">文件导入</button>
                <input type="file" id="fileInput" accept=".txt" style="display: none;">
            </div>
            
            <div class="form-group" id="textImportArea">
                <label class="form-label">账号列表 (格式: email:password)</label>
                <textarea id="importText" placeholder="example@gmail.com:password123&#10;user@outlook.com:pass456"></textarea>
            </div>
            
            <button class="btn" id="importBtn">导入</button>
            
            <div class="notification" id="importNotification" style="display: none;">
                <div class="notification-header">
                    <span class="notification-title">导入完成</span>
                    <button class="notification-close" id="closeNotification">×</button>
                </div>
                <div class="notification-body">
                    <div class="notification-stats">
                        <div class="stat-item success">
                            <span class="stat-icon">✓</span>
                            <span class="stat-label">新增账号</span>
                            <span class="stat-value" id="newCount">0</span>
                        </div>
                        <div class="stat-item duplicate">
                            <span class="stat-icon">⊙</span>
                            <span class="stat-label">重复跳过</span>
                            <span class="stat-value" id="duplicateCount">0</span>
                        </div>
                        <div class="stat-item update">
                            <span class="stat-icon">↻</span>
                            <span class="stat-label">密码更新</span>
                            <span class="stat-value" id="updateCount">0</span>
                        </div>
                        <div class="stat-item error">
                            <span class="stat-icon">✗</span>
                            <span class="stat-label">格式错误</span>
                            <span class="stat-value" id="errorCount">0</span>
                        </div>
                    </div>
                    <div class="notification-footer">
                        <span>总计处理：<strong id="totalLines">0</strong> 行</span>
                        <span>用时：<strong id="elapsedTime">0</strong> 秒</span>
                    </div>
                </div>
            </div>
            
            <div class="filter-bar">
                <input type="text" class="search-input" id="searchInput" placeholder="搜索邮箱...">
                <select class="filter-select" id="levelFilter">
                    <option value="all">全部等级</option>
                    <option value="0">0 级</option>
                    <option value="1-9">1-9 级</option>
                    <option value="10-20">10-20 级</option>
                    <option value="21+">21+ 级</option>
                </select>
                <select class="filter-select" id="cookieFilter">
                    <option value="all">全部状态</option>
                    <option value="has">有 Cookie</option>
                    <option value="none">无 Cookie</option>
                </select>
            </div>
            
            <div class="table-container" style="margin-top: 30px;">
                <table>
                    <thead>
                        <tr>
                            <th>邮箱</th>
                            <th>密码</th>
                            <th>等级</th>
                            <th>MC名</th>
                            <th>订阅信息</th>
                            <th>Cookie</th>
                            <th>状态</th>
                            <th>操作</th>
                        </tr>
                    </thead>
                    <tbody id="accountsTable"></tbody>
                </table>
            </div>
        </div>
    `,
    
    cookies: `
        <div class="module" id="cookies-module">
            <h1 class="module-title">Cookie 管理</h1>
            
            <div class="batch-actions">
                <button class="btn" id="selectAllCookiesBtn">全选</button>
                <button class="btn" id="getAllCookiesBtn">批量获取 Cookie</button>
                <button class="btn btn-secondary" id="getSelectedCookiesBtn" style="display: none;">获取选中</button>
            </div>
            
            <div class="progress-container" id="progressContainer">
                <div class="progress-text" id="progressText">准备中...</div>
                <div class="progress-bar">
                    <div class="progress-fill" id="progressFill"></div>
                </div>
                <div class="progress-log" id="progressLog"></div>
            </div>
            
            <div class="table-container" style="margin-top: 30px;">
                <table>
                    <thead>
                        <tr>
                            <th><input type="checkbox" id="selectAllCheckbox"></th>
                            <th>邮箱</th>
                            <th>状态</th>
                            <th>最后更新</th>
                            <th>操作</th>
                        </tr>
                    </thead>
                    <tbody id="cookiesTable"></tbody>
                </table>
            </div>
        </div>
    `,
    
    status: `
        <div class="module" id="status-module">
            <h1 class="module-title">使用状态</h1>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>邮箱</th>
                            <th>最后登录</th>
                            <th>状态</th>
                        </tr>
                    </thead>
                    <tbody id="statusTable"></tbody>
                </table>
            </div>
        </div>
    `
};

function renderModule(moduleName) {
    console.log('renderModule called with:', moduleName);
    const content = document.getElementById('content');
    console.log('Content element:', content);
    console.log('Module HTML length:', modules[moduleName]?.length);
    
    content.innerHTML = modules[moduleName];
    
    const moduleDiv = content.querySelector('.module');
    if (moduleDiv) {
        moduleDiv.classList.add('active');
    }
    
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    document.querySelector(`[data-module="${moduleName}"]`).classList.add('active');
    
    switch(moduleName) {
        case 'stats':
            loadStats();
            break;
        case 'import':
            loadAccounts();
            setupImport();
            break;
        case 'cookies':
            loadCookies();
            setupCookies();
            break;
        case 'status':
            loadStatus();
            break;
    }
}

async function loadStats() {
    try {
        const response = await fetch(`${API_URL}/stats`);
        const data = await response.json();
        
        document.getElementById('totalAccounts').textContent = data.total;
        document.getElementById('withCookie').textContent = data.with_cookie;
        document.getElementById('withoutCookie').textContent = data.without_cookie;
        
        const ctx = document.getElementById('loginChart').getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00'],
                datasets: [{
                    label: '登录次数',
                    data: [0, 0, 0, 0, 0, 0],
                    borderColor: '#fff',
                    backgroundColor: 'rgba(255, 255, 255, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        labels: {
                            color: '#fff'
                        }
                    }
                },
                scales: {
                    y: {
                        ticks: { color: '#888' },
                        grid: { color: '#222' }
                    },
                    x: {
                        ticks: { color: '#888' },
                        grid: { color: '#222' }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Failed to load stats:', error);
    }
}

async function loadAccounts() {
    try {
        const response = await fetch(`${API_URL}/accounts`);
        const accounts = await response.json();
        
        window.allAccounts = accounts;
        filterAndDisplayAccounts();
    } catch (error) {
        console.error('Failed to load accounts:', error);
    }
}

function filterAndDisplayAccounts() {
    const searchTerm = document.getElementById('searchInput')?.value.toLowerCase() || '';
    const levelFilter = document.getElementById('levelFilter')?.value || 'all';
    const cookieFilter = document.getElementById('cookieFilter')?.value || 'all';
    
    let filtered = window.allAccounts || [];
    
    if (searchTerm) {
        filtered = filtered.filter(acc => acc.email.toLowerCase().includes(searchTerm));
    }
    
    if (levelFilter !== 'all') {
        if (levelFilter === '0') {
            filtered = filtered.filter(acc => acc.level === 0);
        } else if (levelFilter === '1-9') {
            filtered = filtered.filter(acc => acc.level >= 1 && acc.level <= 9);
        } else if (levelFilter === '10-20') {
            filtered = filtered.filter(acc => acc.level >= 10 && acc.level <= 20);
        } else if (levelFilter === '21+') {
            filtered = filtered.filter(acc => acc.level >= 21);
        }
    }
    
    if (cookieFilter !== 'all') {
        if (cookieFilter === 'has') {
            filtered = filtered.filter(acc => acc.has_cookie);
        } else if (cookieFilter === 'none') {
            filtered = filtered.filter(acc => !acc.has_cookie);
        }
    }
    
    const tbody = document.getElementById('accountsTable');
    tbody.innerHTML = filtered.map(acc => `
        <tr class="${acc.disabled ? 'disabled-row' : ''}">
            <td>${acc.email}</td>
            <td>
                <span class="password-hidden" data-password="${acc.password}">********</span>
                <button class="action-btn" onclick="togglePassword(this)">显示</button>
            </td>
            <td>${acc.level > 0 ? 'Lv.' + acc.level : '-'}</td>
            <td>${acc.mcname !== 'Unknown' ? acc.mcname : '-'}</td>
            <td style="font-size: 12px; color: #666;">${acc.subscription || '-'}</td>
            <td><span class="status-badge ${acc.has_cookie ? 'success' : 'none'}">${acc.has_cookie ? '有' : '无'}</span></td>
            <td>
                <span class="status-badge ${acc.disabled ? 'error' : 'success'}">${acc.disabled ? '停用' : '启用'}</span>
            </td>
            <td>
                <button class="action-btn" onclick="toggleAccountStatus('${acc.email}', ${acc.disabled})">${acc.disabled ? '启用' : '停用'}</button>
                <button class="action-btn" onclick="deleteAccount('${acc.email}')">删除</button>
            </td>
        </tr>
    `).join('');
}

function togglePassword(btn) {
    const span = btn.previousElementSibling;
    const password = span.dataset.password;
    
    if (span.textContent === '********') {
        span.textContent = password;
        btn.textContent = '隐藏';
    } else {
        span.textContent = '********';
        btn.textContent = '显示';
    }
}

function setupImport() {
    const textImportBtn = document.getElementById('textImportBtn');
    const fileImportBtn = document.getElementById('fileImportBtn');
    const fileInput = document.getElementById('fileInput');
    const importBtn = document.getElementById('importBtn');
    const textArea = document.getElementById('importText');
    
    textImportBtn.addEventListener('click', () => {
        textImportBtn.classList.add('active');
        fileImportBtn.classList.remove('active');
        document.getElementById('textImportArea').style.display = 'block';
    });
    
    fileImportBtn.addEventListener('click', () => {
        fileInput.click();
    });
    
    fileInput.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        
        const formData = new FormData();
        formData.append('file', file);
        
        importBtn.disabled = true;
        importBtn.textContent = '导入中...';
        
        try {
            const response = await fetch(`${API_URL}/accounts/upload`, {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (data.success) {
                showImportNotification(data);
                fileInput.value = '';
                loadAccounts();
            } else {
                alert('导入失败: ' + data.message);
            }
        } catch (error) {
            alert('导入失败');
        } finally {
            importBtn.disabled = false;
            importBtn.textContent = '导入';
        }
    });
    
    importBtn.addEventListener('click', async () => {
        const text = textArea.value;
        if (!text.trim()) return;
        
        importBtn.disabled = true;
        importBtn.textContent = '导入中...';
        
        try {
            const response = await fetch(`${API_URL}/accounts`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text })
            });
            
            const data = await response.json();
            if (data.success) {
                showImportNotification(data);
                textArea.value = '';
                loadAccounts();
            }
        } catch (error) {
            alert('导入失败');
        } finally {
            importBtn.disabled = false;
            importBtn.textContent = '导入';
        }
    });
    
    document.getElementById('closeNotification')?.addEventListener('click', () => {
        document.getElementById('importNotification').style.display = 'none';
    });
    
    document.getElementById('searchInput')?.addEventListener('input', filterAndDisplayAccounts);
    document.getElementById('levelFilter')?.addEventListener('change', filterAndDisplayAccounts);
    document.getElementById('cookieFilter')?.addEventListener('change', filterAndDisplayAccounts);
}

function showImportNotification(data) {
    document.getElementById('newCount').textContent = data.new_count;
    document.getElementById('duplicateCount').textContent = data.duplicate_count;
    document.getElementById('updateCount').textContent = data.password_update_count;
    document.getElementById('errorCount').textContent = data.error_count;
    document.getElementById('totalLines').textContent = data.total_lines;
    document.getElementById('elapsedTime').textContent = data.elapsed_time;
    
    document.getElementById('importNotification').style.display = 'block';
}

async function toggleAccountStatus(email, currentDisabled) {
    const action = currentDisabled ? '启用' : '停用';
    if (!confirm(`确定${action} ${email}?`)) return;
    
    try {
        const response = await fetch(`${API_URL}/accounts/${encodeURIComponent(email)}/toggle`, {
            method: 'POST'
        });
        const data = await response.json();
        if (data.success) {
            loadAccounts();
        } else {
            alert(`${action}失败`);
        }
    } catch (error) {
        alert(`${action}失败`);
    }
}

async function deleteAccount(email) {
    if (!confirm(`确定删除 ${email}?\n\n此操作将同时删除账号和 Cookie 文件，无法恢复！`)) return;
    
    try {
        await fetch(`${API_URL}/accounts/${encodeURIComponent(email)}`, {
            method: 'DELETE'
        });
        loadAccounts();
    } catch (error) {
        alert('删除失败');
    }
}

async function loadCookies() {
    try {
        const response = await fetch(`${API_URL}/accounts`);
        const accounts = await response.json();
        
        const tbody = document.getElementById('cookiesTable');
        tbody.innerHTML = accounts.map(acc => `
            <tr>
                <td><input type="checkbox" class="cookie-checkbox" data-email="${acc.email}"></td>
                <td>${acc.email}</td>
                <td><span class="status-badge ${acc.has_cookie ? 'success' : 'none'}">${acc.cookie_status}</span></td>
                <td>${acc.last_login || '-'}</td>
                <td><button class="action-btn" onclick="getCookie('${acc.email}')">获取</button></td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Failed to load cookies:', error);
    }
}

function setupCookies() {
    const selectAllCheckbox = document.getElementById('selectAllCheckbox');
    const selectAllBtn = document.getElementById('selectAllCookiesBtn');
    const getAllBtn = document.getElementById('getAllCookiesBtn');
    const getSelectedBtn = document.getElementById('getSelectedCookiesBtn');
    
    selectAllCheckbox?.addEventListener('change', (e) => {
        const checkboxes = document.querySelectorAll('.cookie-checkbox');
        checkboxes.forEach(cb => cb.checked = e.target.checked);
        updateBatchButtons();
    });
    
    document.addEventListener('change', (e) => {
        if (e.target.classList.contains('cookie-checkbox')) {
            updateBatchButtons();
        }
    });
    
    selectAllBtn?.addEventListener('click', () => {
        const checkboxes = document.querySelectorAll('.cookie-checkbox');
        const allChecked = Array.from(checkboxes).every(cb => cb.checked);
        checkboxes.forEach(cb => cb.checked = !allChecked);
        selectAllCheckbox.checked = !allChecked;
        updateBatchButtons();
    });
    
    getAllBtn?.addEventListener('click', async () => {
        const response = await fetch(`${API_URL}/accounts`);
        const accounts = await response.json();
        const emails = accounts.map(acc => acc.email);
        
        document.getElementById('progressContainer').classList.add('show');
        document.getElementById('progressLog').innerHTML = '';
        
        await fetch(`${API_URL}/cookies/get`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ emails })
        });
    });
    
    getSelectedBtn?.addEventListener('click', async () => {
        const checkboxes = document.querySelectorAll('.cookie-checkbox:checked');
        const emails = Array.from(checkboxes).map(cb => cb.dataset.email);
        
        if (emails.length === 0) {
            alert('请选择账号');
            return;
        }
        
        document.getElementById('progressContainer').classList.add('show');
        document.getElementById('progressLog').innerHTML = '';
        
        await fetch(`${API_URL}/cookies/get`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ emails })
        });
    });
    
    socket.on('cookie_progress', (data) => {
        const percent = (data.current / data.total * 100).toFixed(0);
        document.getElementById('progressFill').style.width = `${percent}%`;
        document.getElementById('progressText').textContent = `${data.current}/${data.total} - ${data.email}`;
        
        const log = document.getElementById('progressLog');
        const item = document.createElement('div');
        item.className = `progress-log-item ${data.status}`;
        item.textContent = `${data.email} - ${data.message}`;
        log.appendChild(item);
        log.scrollTop = log.scrollHeight;
    });
    
    socket.on('cookie_complete', () => {
        setTimeout(() => {
            document.getElementById('progressContainer').classList.remove('show');
            loadCookies();
        }, 2000);
    });
}

function updateBatchButtons() {
    const checkboxes = document.querySelectorAll('.cookie-checkbox:checked');
    const getSelectedBtn = document.getElementById('getSelectedBtn');
    
    if (checkboxes.length > 0) {
        getSelectedBtn.style.display = 'inline-block';
        getSelectedBtn.textContent = `获取选中 (${checkboxes.length})`;
    } else {
        getSelectedBtn.style.display = 'none';
    }
}

async function getCookie(email) {
    document.getElementById('progressContainer').classList.add('show');
    document.getElementById('progressLog').innerHTML = '';
    
    await fetch(`${API_URL}/cookies/get`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ emails: [email] })
    });
}

async function loadStatus() {
    try {
        const response = await fetch(`${API_URL}/accounts`);
        const accounts = await response.json();
        
        const tbody = document.getElementById('statusTable');
        tbody.innerHTML = accounts.map(acc => `
            <tr>
                <td>${acc.email}</td>
                <td>${acc.last_login || '-'}</td>
                <td><span class="status-badge ${acc.has_cookie ? 'success' : 'none'}">${acc.has_cookie ? '可用' : '不可用'}</span></td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Failed to load status:', error);
    }
}

document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', (e) => {
        e.preventDefault();
        const module = item.dataset.module;
        console.log('Switching to module:', module);
        renderModule(module);
    });
});

console.log('Initializing admin panel...');
console.log('Modules available:', Object.keys(modules));
renderModule('stats');
