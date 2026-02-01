const API_URL = window.location.origin + '/api';

// 检查卡密验证状态
async function checkCardVerification() {
    try {
        const response = await fetch(`${API_URL}/cards/check`);
        const data = await response.json();
        
        if (data.verified) {
            document.getElementById('cardVerifyModal').style.display = 'none';
            document.getElementById('mainContent').style.display = 'block';
            
            // 显示卡密信息
            const expireDate = new Date(data.expire_at);
            document.getElementById('cardInfo').innerHTML = `
                <div class="card-info-badge">
                    <span>卡密: ${data.card_key}</span>
                    <span>到期: ${expireDate.toLocaleDateString('zh-CN')}</span>
                </div>
            `;
        } else {
            document.getElementById('cardVerifyModal').style.display = 'flex';
            document.getElementById('mainContent').style.display = 'none';
        }
    } catch (error) {
        document.getElementById('cardVerifyModal').style.display = 'flex';
        document.getElementById('mainContent').style.display = 'none';
    }
}

// 验证卡密
async function verifyCard() {
    const cardKey = document.getElementById('cardKeyInput').value.trim();
    const errorMsg = document.getElementById('cardErrorMsg');
    const verifyBtn = document.getElementById('verifyCardBtn');
    
    if (!cardKey) {
        errorMsg.textContent = '请输入卡密';
        errorMsg.style.display = 'block';
        return;
    }
    
    verifyBtn.disabled = true;
    verifyBtn.textContent = '验证中...';
    errorMsg.style.display = 'none';
    
    try {
        const response = await fetch(`${API_URL}/cards/verify`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ card_key: cardKey })
        });
        
        const data = await response.json();
        
        if (data.success) {
            checkCardVerification();
        } else {
            errorMsg.textContent = data.message || '验证失败';
            errorMsg.style.display = 'block';
        }
    } catch (error) {
        errorMsg.textContent = '网络错误，请重试';
        errorMsg.style.display = 'block';
    } finally {
        verifyBtn.disabled = false;
        verifyBtn.textContent = '验证';
    }
}

// 页面加载时检查
checkCardVerification();

const elements = {
    accountCount: document.getElementById('accountCount'),
    deviceCode: document.getElementById('deviceCode'),
    loginBtn: document.getElementById('loginBtn'),
    modal: document.getElementById('modal'),
    modalIcon: document.getElementById('modalIcon'),
    modalMessage: document.getElementById('modalMessage'),
    closeBtn: document.getElementById('closeBtn')
};

async function loadAvailableCount() {
    try {
        const response = await fetch(`${API_URL}/available-count`);
        const data = await response.json();
        elements.accountCount.textContent = data.count;
    } catch (error) {
        elements.accountCount.textContent = '0';
    }
}

function showModal(success, message) {
    elements.modal.classList.add('show');
    elements.modalMessage.textContent = message;
    
    if (success) {
        elements.modalIcon.classList.add('success');
        elements.modalIcon.classList.remove('error');
        elements.modalIcon.innerHTML = '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline>';
    } else {
        elements.modalIcon.classList.add('error');
        elements.modalIcon.classList.remove('success');
        elements.modalIcon.innerHTML = '<circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line>';
    }
}

function hideModal() {
    elements.modal.classList.remove('show');
}

async function handleLogin() {
    const deviceCode = elements.deviceCode.value.trim().toUpperCase();
    
    if (deviceCode.length !== 8) {
        showModal(false, '设备代码必须是8位');
        return;
    }
    
    elements.loginBtn.disabled = true;
    elements.loginBtn.textContent = '登录中...';
    
    try {
        const response = await fetch(`${API_URL}/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ device_code: deviceCode })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showModal(true, '授权完成，请检查 HMCL 是否已登录');
            elements.deviceCode.value = '';
            loadAvailableCount();
        } else {
            showModal(false, data.message || '登录失败');
        }
    } catch (error) {
        showModal(false, '网络错误');
    } finally {
        elements.loginBtn.disabled = false;
        elements.loginBtn.textContent = '登录';
    }
}

elements.loginBtn.addEventListener('click', handleLogin);
elements.closeBtn.addEventListener('click', hideModal);

elements.deviceCode.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        handleLogin();
    }
});

elements.deviceCode.addEventListener('input', (e) => {
    e.target.value = e.target.value.toUpperCase();
});

loadAvailableCount();
setInterval(loadAvailableCount, 30000);
