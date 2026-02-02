const API_URL = window.location.origin + '/api';

const elements = {
    cardKeyInput: document.getElementById('cardKeyInput'),
    verifyBtn: document.getElementById('verifyBtn'),
    errorMsg: document.getElementById('errorMsg')
};

async function verifyCard() {
    const cardKey = elements.cardKeyInput.value.trim();
    
    if (!cardKey) {
        showError('请输入卡密');
        return;
    }
    
    elements.verifyBtn.disabled = true;
    elements.verifyBtn.textContent = '验证中...';
    elements.errorMsg.style.display = 'none';
    
    try {
        const response = await fetch(`${API_URL}/cards/verify`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ card_key: cardKey })
        });
        
        const data = await response.json();
        
        if (data.success) {
            window.location.href = '/';
        } else {
            showError(data.message || '验证失败');
            elements.verifyBtn.disabled = false;
            elements.verifyBtn.textContent = '验证并继续';
        }
    } catch (error) {
        showError('网络错误，请重试');
        elements.verifyBtn.disabled = false;
        elements.verifyBtn.textContent = '验证并继续';
    }
}

function showError(message) {
    elements.errorMsg.textContent = message;
    elements.errorMsg.style.display = 'block';
}

elements.verifyBtn.addEventListener('click', verifyCard);

elements.cardKeyInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        verifyCard();
    }
});

elements.cardKeyInput.addEventListener('input', () => {
    elements.errorMsg.style.display = 'none';
});
