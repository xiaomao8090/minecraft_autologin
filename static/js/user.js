const API_URL = window.location.origin + '/api';

window.addEventListener('load', () => {
    setTimeout(() => {
        document.querySelector('.page-loader').classList.add('hidden');
    }, 500);
});

async function checkCardVerification() {
    try {
        const response = await fetch(`${API_URL}/cards/check`);
        const data = await response.json();
        
        if (!data.verified) {
            window.location.href = '/verify.html';
            return;
        }
        
        const maskCardKey = (key) => {
            if (!key || key.length < 10) return key;
            const parts = key.split('-');
            if (parts.length === 4) {
                return `${parts[0]}-${parts[1]}-***-${parts[3]}`;
            }
            return key.substring(0, 8) + '***' + key.substring(key.length - 4);
        };
        
        const expireDate = new Date(data.expire_at);
        const now = new Date();
        const daysLeft = Math.floor((expireDate - now) / (1000 * 60 * 60 * 24));
        
        document.getElementById('cardInfo').innerHTML = `
            <div class="card-info-badge">
                <span>卡密: ${maskCardKey(data.card_key)}</span>
                <span class="days-left">剩余 ${daysLeft} 天</span>
                <span>到期: ${expireDate.toLocaleDateString('zh-CN')}</span>
            </div>
        `;
    } catch (error) {
        window.location.href = '/verify.html';
    }
}

checkCardVerification();

const elements = {
    accountCount: document.getElementById('accountCount'),
    deviceCode: document.getElementById('deviceCode'),
    loginBtn: document.getElementById('loginBtn'),
    modal: document.getElementById('modal'),
    modalIcon: document.getElementById('modalIcon'),
    modalMessage: document.getElementById('modalMessage'),
    subMessage: document.getElementById('subMessage'),
    closeBtn: document.getElementById('closeBtn'),
    btnText: document.querySelector('.btn-text'),
    btnLoader: document.querySelector('.btn-loader'),
    progressBar: document.getElementById('progressBar')
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

function showModal(success, message, subMsg = '') {
    elements.modal.classList.add('show');
    elements.modalMessage.textContent = message;
    elements.subMessage.textContent = subMsg;
    
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
        showModal(false, '设备代码必须是8位', '请检查输入的设备代码');
        return;
    }
    
    elements.loginBtn.disabled = true;
    elements.btnText.style.display = 'none';
    elements.btnLoader.style.display = 'inline-block';
    
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
            showModal(true, '授权完成', `使用账号: ${data.email}`);
            elements.deviceCode.value = '';
            loadAvailableCount();
        } else {
            showModal(false, data.message || '登录失败', '请重试或联系客服');
        }
    } catch (error) {
        showModal(false, '网络错误', '请检查网络连接后重试');
    } finally {
        elements.loginBtn.disabled = false;
        elements.btnText.style.display = 'inline';
        elements.btnLoader.style.display = 'none';
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
    const progress = (e.target.value.length / 8) * 100;
    elements.progressBar.style.width = progress + '%';
    
    if (e.target.value.length === 8) {
        elements.loginBtn.focus();
    }
});

loadAvailableCount();
setInterval(loadAvailableCount, 30000);
