const API_URL = 'http://localhost:5001/api';

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
            showModal(true, '登录成功');
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
