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
                    <div class="stat-label">可用账号</div>
                    <div class="stat-value" id="withCookie">0</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">已使用</div>
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
            
            <div class="batch-actions" style="margin-top: 20px;">
                <button class="btn" id="deleteUsedAccountsBtn" style="background: #dc3545;">删除已使用账号</button>
            </div>
            
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
    `,
    
    cards: `
        <div class="module" id="cards-module">
            <h1 class="module-title">卡密管理</h1>
            
            <div class="card-generator">
                <div class="form-row">
                    <div class="form-group">
                        <label>卡密类型</label>
                        <select id="cardType">
                            <option value="normal">正式卡</option>
                            <option value="test">测试卡</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>生成数量</label>
                        <input type="number" id="cardCount" value="1" min="1" max="100">
                    </div>
                    <div class="form-group">
                        <label>有效期</label>
                        <select id="cardDuration">
                            <option value="1day">1天</option>
                            <option value="2day">2天</option>
                            <option value="3day">3天</option>
                            <option value="7day">7天</option>
                            <option value="15day">15天</option>
                            <option value="30day">30天</option>
                            <option value="1month">1个月</option>
                            <option value="2month">2个月</option>
                            <option value="3month">3个月</option>
                            <option value="6month">6个月</option>
                            <option value="12month">12个月</option>
                        </select>
                    </div>
                    <button class="btn" id="generateCardsBtn">生成卡密</button>
                </div>
            </div>
            
            <div class="generated-cards" id="generatedCards" style="display: none;">
                <h3>生成的卡密</h3>
                <div class="cards-list" id="cardsList"></div>
                <button class="btn btn-secondary" id="copyAllCardsBtn">复制全部</button>
            </div>
            
            <div class="table-container" style="margin-top: 30px;">
                <table>
                    <thead>
                        <tr>
                            <th>卡密</th>
                            <th>类型</th>
                            <th>有效期</th>
                            <th>创建时间</th>
                            <th>状态</th>
                            <th>使用时间</th>
                            <th>操作</th>
                        </tr>
                    </thead>
                    <tbody id="cardsTable"></tbody>
                </table>
            </div>
        </div>
    `,
    
    logs: `
        <div class="module" id="logs-module">
            <h1 class="module-title">操作日志</h1>
            
            <div class="batch-actions">
                <button class="btn" id="deleteAllLogsBtn" style="background: #dc3545;">删除全部日志</button>
            </div>
            
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
    
    users: `
        <div class="module" id="users-module">
            <h1 class="module-title">用户管理</h1>
            
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>卡密</th>
                            <th>类型</th>
                            <th>剩余天数</th>
                            <th>成功次数</th>
                            <th>失败次数</th>
                            <th>最后IP</th>
                            <th>到期时间</th>
                            <th>状态</th>
                            <th>操作</th>
                        </tr>
                    </thead>
                    <tbody id="usersTable"></tbody>
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
        case 'cards':
            loadCards();
            setupCards();
            break;
        case 'logs':
            loadLogs();
            setupLogs();
            break;
        case 'users':
            loadUsers();
            break;
    }
}

async function loadStats() {
    try {
        const response = await fetch(`${API_URL}/stats`);
        const data = await response.json();
        
        document.getElementById('totalAccounts').textContent = data.total;
        document.getElementById('withCookie').textContent = data.available;
        document.getElementById('withoutCookie').textContent = data.used;
        
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
            <td>********</td>
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
    
    document.getElementById('deleteUsedAccountsBtn')?.addEventListener('click', deleteUsedAccounts);
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
    
    socket.off('cookie_progress');
    socket.off('cookie_complete');
    
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

async function loadCards() {
    try {
        const response = await fetch(`${API_URL}/cards`);
        const cards = await response.json();
        
        const tbody = document.getElementById('cardsTable');
        tbody.innerHTML = cards.map(card => `
            <tr>
                <td><code>${card.card_key}</code></td>
                <td><span class="status-badge ${card.type === 'test' ? 'none' : 'success'}">${card.type === 'test' ? '测试卡' : '正式卡'}</span></td>
                <td>${card.duration}</td>
                <td>${new Date(card.created_at).toLocaleString('zh-CN')}</td>
                <td><span class="status-badge ${card.used ? 'error' : 'success'}">${card.used ? '已使用' : '未使用'}</span></td>
                <td>${card.used_at ? new Date(card.used_at).toLocaleString('zh-CN') : '-'}</td>
                <td>
                    ${!card.used ? `<button class="action-btn" onclick="deleteCard('${card.card_key}')">删除</button>` : '-'}
                </td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Failed to load cards:', error);
    }
}

function setupCards() {
    const generateBtn = document.getElementById('generateCardsBtn');
    const copyAllBtn = document.getElementById('copyAllCardsBtn');
    
    generateBtn?.addEventListener('click', async () => {
        const count = parseInt(document.getElementById('cardCount').value);
        const duration = document.getElementById('cardDuration').value;
        const type = document.getElementById('cardType').value;
        
        if (count < 1 || count > 100) {
            alert('数量必须在1-100之间');
            return;
        }
        
        generateBtn.disabled = true;
        generateBtn.textContent = '生成中...';
        
        try {
            const response = await fetch(`${API_URL}/cards/generate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ count, duration, type })
            });
            
            const data = await response.json();
            
            if (data.success) {
                const cardsList = document.getElementById('cardsList');
                cardsList.innerHTML = data.cards.map(card => 
                    `<div class="card-item"><code>${card}</code></div>`
                ).join('');
                
                document.getElementById('generatedCards').style.display = 'block';
                
                window.generatedCards = data.cards;
                
                loadCards();
            }
        } catch (error) {
            alert('生成失败');
        } finally {
            generateBtn.disabled = false;
            generateBtn.textContent = '生成卡密';
        }
    });
    
    copyAllBtn?.addEventListener('click', () => {
        if (window.generatedCards) {
            const text = window.generatedCards.join('\n');
            navigator.clipboard.writeText(text).then(() => {
                alert('已复制到剪贴板');
            });
        }
    });
}

async function deleteCard(cardKey) {
    if (!confirm(`确定删除卡密 ${cardKey}?`)) return;
    
    try {
        await fetch(`${API_URL}/cards/${encodeURIComponent(cardKey)}`, {
            method: 'DELETE'
        });
        loadCards();
    } catch (error) {
        alert('删除失败');
    }
}

function setupLogs() {
    document.getElementById('deleteAllLogsBtn')?.addEventListener('click', deleteAllLogs);
}

async function loadLogs() {
    try {
        const response = await fetch(`${API_URL}/logs?limit=100`);
        const logs = await response.json();
        
        const tbody = document.getElementById('logsTable');
        tbody.innerHTML = logs.map(log => {
            const statusClass = log.status === 'success' ? 'success' : log.status === 'failed' ? 'error' : 'none';
            const hasDetail = log.detail_log && log.detail_log.trim().length > 0;
            
            return `
                <tr>
                    <td style="font-size: 12px;">${new Date(log.created_at).toLocaleString('zh-CN')}</td>
                    <td>${log.ip || '-'}</td>
                    <td>${log.action}</td>
                    <td style="font-size: 11px;">${log.card_key || '-'}</td>
                    <td style="font-size: 12px;">${log.email || '-'}</td>
                    <td>${log.device_code || '-'}</td>
                    <td><span class="status-badge ${statusClass}">${log.status}</span></td>
                    <td style="max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${log.message || '-'}${log.deleted ? ' (已删除)' : ''}</td>
                    <td>
                        ${hasDetail ? `<button class="action-btn" style="background: #28a745;" onclick="viewDetail(${log.id})">详细</button>` : '-'}
                        <button class="action-btn" onclick="deleteLog(${log.id})">删除</button>
                    </td>
                </tr>
            `;
        }).join('');
    } catch (error) {
        console.error('Failed to load logs:', error);
    }
}

async function viewDetail(logId) {
    try {
        const response = await fetch(`${API_URL}/logs/${logId}/detail`);
        const data = await response.json();
        
        if (data.success) {
            const modal = document.createElement('div');
            modal.style.cssText = 'position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.8); display: flex; align-items: center; justify-content: center; z-index: 9999;';
            
            const content = document.createElement('div');
            content.style.cssText = 'background: #1a1a1a; padding: 30px; border-radius: 8px; max-width: 90%; max-height: 90%; overflow: auto; border: 1px solid #333;';
            
            const title = document.createElement('h2');
            title.textContent = '详细日志';
            title.style.cssText = 'color: #fff; margin-bottom: 20px;';
            
            const pre = document.createElement('pre');
            pre.textContent = data.detail || '无详细日志';
            pre.style.cssText = 'color: #ccc; background: #0a0a0a; padding: 20px; border-radius: 4px; overflow: auto; max-height: 70vh; font-size: 13px; line-height: 1.6;';
            
            const closeBtn = document.createElement('button');
            closeBtn.textContent = '关闭';
            closeBtn.style.cssText = 'margin-top: 20px; padding: 10px 30px; background: #fff; color: #000; border: none; border-radius: 4px; cursor: pointer;';
            closeBtn.onclick = () => modal.remove();
            
            content.appendChild(title);
            content.appendChild(pre);
            content.appendChild(closeBtn);
            modal.appendChild(content);
            document.body.appendChild(modal);
            
            modal.onclick = (e) => {
                if (e.target === modal) modal.remove();
            };
        } else {
            alert('无法加载详细日志');
        }
    } catch (error) {
        alert('加载失败');
    }
}

async function deleteLog(logId) {
    if (!confirm('确定删除此日志?')) return;
    
    try {
        await fetch(`${API_URL}/logs/${logId}`, {
            method: 'DELETE'
        });
        loadLogs();
    } catch (error) {
        alert('删除失败');
    }
}

async function deleteUsedAccounts() {
    if (!confirm('确定删除所有已使用（停用）的账号？\n\n此操作不可恢复！')) return;
    
    try {
        const response = await fetch(`${API_URL}/accounts/delete-used`, {
            method: 'POST'
        });
        const data = await response.json();
        if (data.success) {
            alert(`已删除 ${data.deleted_count} 个账号`);
            loadAccounts();
        } else {
            alert('删除失败');
        }
    } catch (error) {
        alert('删除失败');
    }
}

async function deleteAllLogs() {
    if (!confirm('确定删除全部日志？\n\n此操作不可恢复！')) return;
    
    try {
        const response = await fetch(`${API_URL}/logs/delete-all`, {
            method: 'POST'
        });
        const data = await response.json();
        if (data.success) {
            alert(`已删除 ${data.deleted_count} 条日志`);
            loadLogs();
        } else {
            alert('删除失败');
        }
    } catch (error) {
        alert('删除失败');
    }
}

async function loadUsers() {
    try {
        const response = await fetch(`${API_URL}/users`);
        const users = await response.json();
        
        const tbody = document.getElementById('usersTable');
        tbody.innerHTML = users.map(user => {
            const expireDate = user.expire_at ? new Date(user.expire_at) : null;
            const now = new Date();
            const daysLeft = expireDate ? Math.floor((expireDate - now) / (1000 * 60 * 60 * 24)) : 0;
            const statusClass = user.banned ? 'error' : (daysLeft > 0 ? 'success' : 'none');
            const statusText = user.banned ? '已封禁' : (daysLeft > 0 ? '正常' : '已过期');
            
            const maskCardKey = (key) => {
                if (!key || key.length < 10) return key;
                const parts = key.split('-');
                if (parts.length === 4) {
                    return `${parts[0]}-${parts[1]}-***-${parts[3]}`;
                }
                return key.substring(0, 8) + '***' + key.substring(key.length - 4);
            };
            
            return `
                <tr>
                    <td><code>${maskCardKey(user.card_key)}</code></td>
                    <td><span class="status-badge ${user.type === 'test' ? 'none' : 'success'}">${user.type === 'test' ? '测试' : '正式'}</span></td>
                    <td>${daysLeft > 0 ? daysLeft + ' 天' : '-'}</td>
                    <td>${user.success_count || 0}</td>
                    <td>${user.fail_count || 0}</td>
                    <td>${user.last_ip || '-'}</td>
                    <td>${expireDate ? expireDate.toLocaleDateString('zh-CN') : '-'}</td>
                    <td><span class="status-badge ${statusClass}">${statusText}</span></td>
                    <td>
                        ${user.banned 
                            ? `<button class="action-btn" style="background: #28a745;" onclick="unbanUser('${user.card_key}')">解封</button>`
                            : `<button class="action-btn" style="background: #dc3545;" onclick="banUser('${user.card_key}')">封禁</button>`
                        }
                    </td>
                </tr>
            `;
        }).join('');
    } catch (error) {
        console.error('Failed to load users:', error);
    }
}

async function banUser(cardKey) {
    if (!confirm(`确定封禁此用户？\n\n卡密: ${cardKey}`)) return;
    
    try {
        const response = await fetch(`${API_URL}/users/${encodeURIComponent(cardKey)}/ban`, {
            method: 'POST'
        });
        const data = await response.json();
        if (data.success) {
            alert('已封禁');
            loadUsers();
        } else {
            alert('封禁失败');
        }
    } catch (error) {
        alert('封禁失败');
    }
}

async function unbanUser(cardKey) {
    if (!confirm(`确定解封此用户？\n\n卡密: ${cardKey}`)) return;
    
    try {
        const response = await fetch(`${API_URL}/users/${encodeURIComponent(cardKey)}/unban`, {
            method: 'POST'
        });
        const data = await response.json();
        if (data.success) {
            alert('已解封');
            loadUsers();
        } else {
            alert('解封失败');
        }
    } catch (error) {
        alert('解封失败');
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
