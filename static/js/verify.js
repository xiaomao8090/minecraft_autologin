const API_URL = window.location.origin + '/api';

const elements = {
    cardKeyInput: document.getElementById('cardKeyInput'),
    verifyBtn: document.getElementById('verifyBtn'),
    errorMsg: document.getElementById('errorMsg'),
    btnText: document.querySelector('.btn-text'),
    btnLoader: document.querySelector('.btn-loader')
};

window.addEventListener('load', () => {
    setTimeout(() => {
        document.querySelector('.page-loader').classList.add('hidden');
    }, 500);
});

elements.cardKeyInput.addEventListener('input', (e) => {
    let value = e.target.value.toUpperCase().replace(/[^A-Z0-9-]/g, '');
    
    if (value.startsWith('AUTO-LOGIN-')) {
        const parts = value.substring(11).split('-');
        const formatted = parts.map(part => part.substring(0, 4)).join('-');
        value = 'AUTO-LOGIN-' + formatted;
    }
    
    e.target.value = value;
    elements.errorMsg.style.display = 'none';
});

async function verifyCard() {
    const cardKey = elements.cardKeyInput.value.trim();
    
    if (!cardKey) {
        showError('请输入卡密');
        return;
    }
    
    elements.verifyBtn.disabled = true;
    elements.btnText.style.display = 'none';
    elements.btnLoader.style.display = 'inline-block';
    elements.errorMsg.style.display = 'none';
    
    try {
        const response = await fetch(`${API_URL}/cards/verify`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ card_key: cardKey })
        });
        
        const data = await response.json();
        
        if (data.success) {
            elements.verifyBtn.style.background = '#4ade80';
            elements.btnText.textContent = '验证成功';
            elements.btnText.style.display = 'inline';
            elements.btnLoader.style.display = 'none';
            
            setTimeout(() => {
                document.querySelector('.container').style.opacity = '0';
                document.querySelector('.container').style.transform = 'translateY(-20px)';
                setTimeout(() => {
                    window.location.href = '/';
                }, 300);
            }, 500);
        } else {
            showError(data.message || '验证失败');
            resetButton();
        }
    } catch (error) {
        showError('网络错误，请重试');
        resetButton();
    }
}

function showError(message) {
    elements.errorMsg.textContent = message;
    elements.errorMsg.style.display = 'block';
}

function resetButton() {
    elements.verifyBtn.disabled = false;
    elements.btnText.style.display = 'inline';
    elements.btnText.textContent = '验证并继续';
    elements.btnLoader.style.display = 'none';
}

elements.verifyBtn.addEventListener('click', verifyCard);

elements.cardKeyInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        verifyCard();
    }
});
